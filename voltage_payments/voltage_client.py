"""
Voltage.cloud API client for Swapbox.

Docs: https://docs.voltageapi.com/developer-guide
Base URL: https://voltageapi.com/v1

Authentication: x-api-key header
Amounts: all BTC amounts in millisatoshis (msats). 1 sat = 1000 msats.

Webhook signature:
  message = raw_body_str + '.' + timestamp_str
  signature = base64( HMAC-SHA256(shared_secret, message) )
  header: x-voltage-signature
"""
import hmac
import hashlib
import base64
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class VoltageAPIException(Exception):
    """Raised for any Voltage.cloud API error."""
    pass


class VoltageClient:
    """
    Lazy-initialised singleton client for the Voltage.cloud Payments API.
    Does not crash on startup if env vars are missing — only raises when
    an API method is actually called.
    """
    BASE_URL = 'https://voltageapi.com/v1'

    def __init__(self):
        self._ready = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init(self):
        """Load config from Django settings (called lazily on first use)."""
        if self._ready:
            return
        self._api_key = getattr(settings, 'VOLTAGE_API_KEY', '')
        self._org_id = getattr(settings, 'VOLTAGE_ORGANIZATION_ID', '')
        self._env_id = getattr(settings, 'VOLTAGE_ENVIRONMENT_ID', '')
        self._wallet_id = getattr(settings, 'VOLTAGE_WALLET_ID', '')
        self._webhook_secret = getattr(settings, 'VOLTAGE_WEBHOOK_SECRET', '')
        self._ready = True

    def _require_config(self):
        self._init()
        missing = [k for k, v in {
            'VOLTAGE_API_KEY': self._api_key,
            'VOLTAGE_ORGANIZATION_ID': self._org_id,
            'VOLTAGE_ENVIRONMENT_ID': self._env_id,
            'VOLTAGE_WALLET_ID': self._wallet_id,
        }.items() if not v]
        if missing:
            raise VoltageAPIException(
                f"Voltage.cloud configuration incomplete. "
                f"Missing settings/env vars: {', '.join(missing)}"
            )

    def _headers(self):
        return {
            'x-api-key': self._api_key,
            'Content-Type': 'application/json',
        }

    def _get(self, path):
        self._require_config()
        url = f"{self.BASE_URL}{path}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise VoltageAPIException("Voltage API request timed out")
        except requests.exceptions.ConnectionError:
            raise VoltageAPIException("Unable to connect to Voltage API")
        except requests.exceptions.HTTPError:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise VoltageAPIException(f"Voltage API {resp.status_code}: {detail}")

    def _post(self, path, data):
        self._require_config()
        url = f"{self.BASE_URL}{path}"
        try:
            resp = requests.post(url, headers=self._headers(), json=data, timeout=30)
            resp.raise_for_status()
            if resp.content:
                return resp.json()
            return {}
        except requests.exceptions.Timeout:
            raise VoltageAPIException("Voltage API request timed out")
        except requests.exceptions.ConnectionError:
            raise VoltageAPIException("Unable to connect to Voltage API")
        except requests.exceptions.HTTPError:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise VoltageAPIException(f"Voltage API {resp.status_code}: {detail}")

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def is_configured(self):
        """Return True if all required settings are present (non-raising)."""
        try:
            self._require_config()
            return True
        except VoltageAPIException:
            return False

    def usd_to_msats(self, usd_amount):
        """
        Convert a USD amount to millisatoshis using the live BTC/USD price
        from CoinGecko (free, no auth required).
        """
        try:
            resp = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': 'bitcoin', 'vs_currencies': 'usd'},
                timeout=10,
            )
            resp.raise_for_status()
            btc_price_usd = resp.json()['bitcoin']['usd']
            btc_amount = float(usd_amount) / btc_price_usd
            sats = btc_amount * 100_000_000
            msats = int(sats * 1000)
            logger.info(
                f"Converted ${usd_amount} USD → {msats} msats "
                f"(BTC price: ${btc_price_usd:,.0f})"
            )
            return msats, btc_price_usd
        except Exception as e:
            logger.error(f"CoinGecko price fetch failed: {e}")
            raise VoltageAPIException(f"Unable to fetch BTC price for conversion: {e}")

    def create_receive_payment(
        self,
        payment_id,
        amount_msats,
        payment_kind='bip21',
        description='Swapbox Payment',
        expiration=3600,
    ):
        """
        Create a receive payment (invoice / address) via the Voltage API.

        payment_id   — UUID you generate; used as idempotency key by Voltage.
        amount_msats — Amount in millisatoshis.
        payment_kind — 'bolt11' | 'onchain' | 'bip21' (default: bip21).
        expiration   — Seconds until expiry (Lightning only). Default 3600 (1 hr).

        Returns the full Voltage API response dict.
        """
        self._require_config()

        payload = {
            'id': str(payment_id),
            'wallet_id': self._wallet_id,
            'currency': 'btc',
            'payment_kind': payment_kind,
            'description': description,
        }

        if amount_msats:
            payload['amount'] = {
                'amount': int(amount_msats),
                'currency': 'btc',
                'unit': 'msats',
            }

        # expiration only applies to Lightning (bolt11 / bip21)
        if payment_kind in ('bolt11', 'bip21'):
            payload['expiration'] = expiration

        path = (
            f"/organizations/{self._org_id}"
            f"/environments/{self._env_id}/payments"
        )
        logger.info(
            f"Creating Voltage receive payment {payment_id} "
            f"({payment_kind}) for {amount_msats} msats"
        )
        result = self._post(path, payload)
        logger.info(
            f"Voltage payment {payment_id} created — status: {result.get('status')}"
        )
        return result

    def get_payment(self, payment_id):
        """Fetch current status / details of a payment from Voltage."""
        self._require_config()
        path = (
            f"/organizations/{self._org_id}"
            f"/environments/{self._env_id}/payments/{payment_id}"
        )
        return self._get(path)

    def get_wallet(self, wallet_id=None):
        """
        Fetch wallet details (including balance) from Voltage.
        Uses the configured VOLTAGE_WALLET_ID if no wallet_id is provided.
        """
        self._require_config()
        wid = wallet_id or self._wallet_id
        path = f"/organizations/{self._org_id}/wallets/{wid}"
        return self._get(path)

    def create_webhook(self, webhook_url, events=None):
        """
        Register a webhook with Voltage.

        Returns the response dict which includes 'id' and 'shared_secret'.
        IMPORTANT: shared_secret is shown only once — save it immediately.
        """
        self._require_config()
        if events is None:
            events = [
                {'type': 'receive', 'event': 'generated'},
                {'type': 'receive', 'event': 'completed'},
                {'type': 'receive', 'event': 'expired'},
                {'type': 'receive', 'event': 'failed'},
            ]
        payload = {
            'organization_id': self._org_id,
            'environment_id': self._env_id,
            'url': webhook_url,
            'name': 'Swapbox Webhook',
            'events': events,
        }
        path = (
            f"/organizations/{self._org_id}"
            f"/environments/{self._env_id}/webhooks"
        )
        logger.info(f"Registering Voltage webhook at {webhook_url}")
        result = self._post(path, payload)
        logger.info(f"Voltage webhook created — id: {result.get('id')}")
        return result

    def verify_webhook_signature(
        self, raw_body: bytes, signature: str, timestamp: str
    ) -> bool:
        """
        Verify the signature on an incoming Voltage webhook request.

        Algorithm:
          message   = raw_body_str + '.' + timestamp_str
          expected  = base64( HMAC-SHA256(shared_secret, message) )
          compare   = constant-time compare with x-voltage-signature header
        """
        self._init()
        if not self._webhook_secret:
            logger.warning(
                "VOLTAGE_WEBHOOK_SECRET not set — skipping signature verification"
            )
            return True  # Allow in dev; tighten in production

        try:
            message = raw_body.decode('utf-8') + '.' + timestamp
            expected = base64.b64encode(
                hmac.new(
                    self._webhook_secret.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256,
                ).digest()
            ).decode('utf-8')
            valid = hmac.compare_digest(expected, signature)
            if not valid:
                logger.warning("Voltage webhook signature mismatch")
            return valid
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False

    def extract_payment_data(self, response):
        """
        Extract BTC address, Lightning invoice, and BIP21 URI from a Voltage
        payment API response (works for bolt11, onchain, and bip21 kinds).

        Returns a dict with keys: btc_address, lightning_invoice, bip21_uri
        """
        data = response.get('data') or {}
        payment_type = response.get('type', '')

        btc_address = ''
        lightning_invoice = ''
        bip21_uri = ''

        if payment_type == 'onchain':
            btc_address = data.get('address', '')

        elif payment_type == 'bolt11':
            lightning_invoice = data.get('payment_request', '')

        elif payment_type == 'bip21':
            # bip21 contains both on-chain and Lightning
            lightning_invoice = data.get('payment_request', '')
            btc_address = data.get('address', '')
            # Build BIP21 URI if we have an address
            if btc_address and lightning_invoice:
                bip21_uri = f"bitcoin:{btc_address}?lightning={lightning_invoice}"
            elif btc_address:
                bip21_uri = f"bitcoin:{btc_address}"

        return {
            'btc_address': btc_address,
            'lightning_invoice': lightning_invoice,
            'bip21_uri': bip21_uri,
        }


# Module-level singleton — lazy, never crashes on import/startup
voltage_client = VoltageClient()
