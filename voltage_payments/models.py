import uuid
from django.db import models
from django.utils import timezone
from payments.models import Order
from profiles.models import UserProfile


PAYMENT_KIND_CHOICES = [
    ('bolt11', 'Lightning (BOLT11)'),
    ('onchain', 'On-chain Bitcoin'),
    ('bip21', 'Unified BIP21 (Lightning + On-chain)'),
]

PAYMENT_STATUS_CHOICES = [
    ('generating', 'Generating'),
    ('receiving',  'Receiving (Awaiting Payment)'),
    ('completed',  'Completed'),
    ('expired',    'Expired'),
    ('failed',     'Failed'),
]

NETWORK_CHOICES = [
    ('mainnet',   'Bitcoin Mainnet'),
    ('mutinynet', 'Mutinynet (Staging / Testnet)'),
]


class VoltageWallet(models.Model):
    """
    A Voltage.cloud wallet saved to the database.
    Manageable from the Django Admin — the admin can add wallets, sync
    balances, and designate which wallet is active for payments.
    """
    wallet_id       = models.CharField(max_length=100, unique=True)
    organization_id = models.CharField(max_length=100)
    environment_id  = models.CharField(max_length=100)
    name            = models.CharField(max_length=100)
    network         = models.CharField(max_length=20, choices=NETWORK_CHOICES)
    is_active       = models.BooleanField(
        default=True,
        help_text='Only one wallet should be active per network.',
    )
    is_staging      = models.BooleanField(
        default=True,
        help_text='True = staging / testnet wallet.',
    )
    balance_msats   = models.BigIntegerField(
        default=0,
        help_text='Cached balance in millisatoshis. Use Admin action to sync.',
    )
    last_synced     = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', 'network']
        verbose_name = 'Voltage Wallet'
        verbose_name_plural = 'Voltage Wallets'

    def __str__(self):
        env = 'Staging' if self.is_staging else 'Production'
        return f"{self.name} [{self.network}] — {env}"

    @property
    def balance_sats(self):
        return self.balance_msats // 1000

    @property
    def balance_btc(self):
        return round(self.balance_msats / 100_000_000_000, 8)


class VoltageWebhookConfig(models.Model):
    """
    Stores the Voltage webhook registration details, including the
    shared_secret (which Voltage shows only once at creation time).
    """
    webhook_id     = models.CharField(max_length=100, blank=True)
    webhook_url    = models.URLField()
    shared_secret  = models.CharField(
        max_length=512,
        blank=True,
        help_text='Voltage shared_secret — shown once at webhook creation. Store immediately.',
    )
    environment_id = models.CharField(max_length=100)
    is_active      = models.BooleanField(default=True)
    events         = models.JSONField(default=list, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Voltage Webhook Config'
        verbose_name_plural = 'Voltage Webhook Configs'

    def __str__(self):
        status = 'Active' if self.is_active else 'Inactive'
        return f"Webhook {self.webhook_id or '(unsaved)'} — {status}"


class VoltagePayment(models.Model):
    """
    One Bitcoin payment per Order.

    The UUID primary key (id) is also sent to the Voltage API as the
    payment id, which acts as an idempotency key on their side.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order        = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='voltage_payment'
    )
    user         = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name='voltage_payments'
    )
    wallet       = models.ForeignKey(
        VoltageWallet, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Amounts
    amount_usd   = models.DecimalField(max_digits=10, decimal_places=2)
    amount_msats = models.BigIntegerField(default=0)
    btc_price_at_creation = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='BTC/USD price at the moment the payment was created.',
    )

    # Payment method
    payment_kind = models.CharField(
        max_length=10, choices=PAYMENT_KIND_CHOICES, default='bip21'
    )
    status       = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='generating'
    )
    network      = models.CharField(
        max_length=20, choices=NETWORK_CHOICES, default='mutinynet'
    )

    # Payment address / invoice (populated once Voltage confirms generation)
    btc_address       = models.CharField(max_length=200, blank=True)
    lightning_invoice = models.TextField(blank=True)
    bip21_uri         = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Raw data from Voltage (for debugging and reconciliation)
    voltage_response = models.JSONField(default=dict, blank=True)
    webhook_data     = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Voltage Payment'
        verbose_name_plural = 'Voltage Payments'

    def __str__(self):
        return f"Payment {self.id} — ${self.amount_usd} ({self.get_status_display()})"

    @property
    def is_paid(self):
        return self.status == 'completed'

    @property
    def is_expired(self):
        return self.status == 'expired' or (
            self.expires_at and timezone.now() > self.expires_at
        )

    @property
    def amount_sats(self):
        return self.amount_msats // 1000

    def get_status_badge_class(self):
        return {
            'generating': 'secondary',
            'receiving':  'warning',
            'completed':  'success',
            'expired':    'dark',
            'failed':     'danger',
        }.get(self.status, 'secondary')

    def get_primary_payment_string(self):
        """Return the best payment string to display / encode in QR code."""
        if self.bip21_uri:
            return self.bip21_uri
        if self.lightning_invoice:
            return self.lightning_invoice
        return self.btc_address


class VoltageWebhookLog(models.Model):
    """Audit trail — every Voltage webhook event is logged here."""
    payment            = models.ForeignKey(
        VoltagePayment,
        on_delete=models.CASCADE,
        related_name='webhook_logs',
        null=True,
        blank=True,
    )
    voltage_payment_id = models.CharField(max_length=100, blank=True)
    event_type         = models.CharField(max_length=50)
    payload            = models.JSONField()
    processed_ok       = models.BooleanField(default=False)
    error_message      = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Webhook Log'
        verbose_name_plural = 'Webhook Logs'

    def __str__(self):
        return f"[{self.event_type}] {self.voltage_payment_id} @ {self.created_at:%Y-%m-%d %H:%M}"
