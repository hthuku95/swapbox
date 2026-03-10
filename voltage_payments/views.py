import json
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from payments.models import Order
from profiles.models import UserProfile

from .models import VoltagePayment, VoltageWallet, VoltageWebhookConfig, VoltageWebhookLog
from .voltage_client import VoltageAPIException, voltage_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_active_wallet():
    """Return the active VoltageWallet for the current network, or None."""
    network = getattr(settings, 'VOLTAGE_NETWORK', 'mutinynet')
    return VoltageWallet.objects.filter(
        network=network, is_active=True
    ).first()


def handle_completed_payment(payment):
    """
    Called when Voltage confirms a payment is completed.

    Transfers account ownership from seller to buyer and sends a
    confirmation e-mail.  Idempotent — safe to call more than once.
    """
    if payment.order.payment_complete:
        logger.info(f"Payment {payment.id} already processed — skipping.")
        return

    try:
        order = payment.order
        cart  = order.cart

        order.payment_complete = True
        order.save()

        transferred = []
        for account in cart.accounts_to_be_purchased.all():
            old_owner = account.current_owner
            account.current_owner = cart.user
            account.status = 'S'   # Sold
            account.save()
            cart.accounts_to_be_purchased.remove(account)
            transferred.append(account)
            logger.info(
                f"Transferred account {account.id} "
                f"from {old_owner} to {cart.user}"
            )

        logger.info(
            f"Payment {payment.id} processed — "
            f"{len(transferred)} account(s) transferred."
        )

        if transferred and payment.user.user.email:
            _send_confirmation_email(payment, transferred)

    except Exception as e:
        logger.error(f"Error handling completed payment {payment.id}: {e}")
        # Do not re-raise — we never want a webhook to return 500
        # because Voltage would keep retrying.


def _send_confirmation_email(payment, accounts):
    try:
        account_lines = "\n".join(
            f"  • {a.title} ({a.platform}) — ${a.selling_price}"
            for a in accounts
        )
        buyer_name = (
            payment.user.user.get_full_name() or payment.user.user.username
        )
        subject = "Bitcoin Payment Confirmed — Swapbox"
        body = (
            f"Hi {buyer_name},\n\n"
            f"Your Bitcoin payment has been confirmed!\n\n"
            f"Payment ID : {payment.id}\n"
            f"Amount     : ${payment.amount_usd} USD "
            f"({payment.amount_sats:,} sats)\n"
            f"Network    : {payment.get_network_display()}\n\n"
            f"Purchased accounts:\n{account_lines}\n\n"
            f"You can view them from your Swapbox dashboard.\n\n"
            f"Thank you for using Swapbox!\n"
        )
        send_mail(
            subject,
            body,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@swapbox.com'),
            [payment.user.user.email],
            fail_silently=True,
        )
        logger.info(f"Confirmation email sent to {payment.user.user.email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@login_required
def create_payment(request, order_id):
    """
    Entry point from the checkout flow (payment_method == 'BTC').

    1. Validates the order belongs to the current user.
    2. Converts the USD order value to msats via CoinGecko.
    3. Creates a VoltagePayment record in the DB.
    4. Calls the Voltage API to create a BIP21 receive payment.
    5. Saves the returned address / invoice.
    6. Redirects to the payment_info page.
    """
    userprofile = get_object_or_404(UserProfile, user=request.user)
    order       = get_object_or_404(Order, id=order_id)

    # Ownership check
    if order.cart.user != userprofile:
        messages.error(request, "You don't have permission to access this order.")
        return redirect('profiles:dashboard')

    # Already paid?
    if order.payment_complete:
        messages.info(request, "This order has already been paid.")
        return redirect('payments:payment-details', slug=order.reference_code)

    # Existing active payment for this order?
    if hasattr(order, 'voltage_payment'):
        existing = order.voltage_payment
        if existing.status in ('generating', 'receiving'):
            messages.info(request, "Resuming your existing Bitcoin payment.")
            return redirect('voltage_payments:payment_info', payment_id=existing.id)
        elif existing.status == 'completed':
            messages.info(request, "This order has already been paid.")
            return redirect('payments:payment-details', slug=order.reference_code)

    # Which wallet to use?
    wallet = _get_active_wallet()

    # Convert USD → msats
    try:
        amount_msats, btc_price = voltage_client.usd_to_msats(order.value)
    except VoltageAPIException as e:
        logger.error(f"USD→msats conversion failed: {e}")
        messages.error(request, "Could not fetch the current BTC price. Please try again.")
        return redirect('payments:checkout-view')

    # Create the DB record (using our UUID as the Voltage payment id)
    network = getattr(settings, 'VOLTAGE_NETWORK', 'mutinynet')
    payment = VoltagePayment.objects.create(
        order=order,
        user=userprofile,
        wallet=wallet,
        amount_usd=order.value,
        amount_msats=amount_msats,
        btc_price_at_creation=btc_price,
        payment_kind='bip21',
        network=network,
        expires_at=timezone.now() + timedelta(hours=1),
    )

    # Call Voltage API
    try:
        response = voltage_client.create_receive_payment(
            payment_id=payment.id,          # Our UUID → Voltage idempotency key
            amount_msats=amount_msats,
            payment_kind='bip21',
            description=f"Swapbox order {order.reference_code}",
            expiration=3600,
        )
    except VoltageAPIException as e:
        logger.error(f"Voltage API error creating payment {payment.id}: {e}")
        payment.status = 'failed'
        payment.save()
        messages.error(request, f"Bitcoin payment service error: {e}")
        return redirect('payments:checkout-view')

    # Persist the Voltage response and extract payment data
    payment.voltage_response = response
    payment.status = response.get('status', 'generating')

    extracted = voltage_client.extract_payment_data(response)
    payment.btc_address       = extracted['btc_address']
    payment.lightning_invoice = extracted['lightning_invoice']
    payment.bip21_uri         = extracted['bip21_uri']
    payment.save()

    logger.info(
        f"VoltagePayment {payment.id} created — "
        f"status: {payment.status}, network: {network}"
    )

    return redirect('voltage_payments:payment_info', payment_id=payment.id)


@login_required
def payment_info(request, payment_id):
    """
    Display the Bitcoin payment details page.

    Shows a QR code, the BIP21 URI / Lightning invoice / on-chain address,
    the amount in sats and USD, and a countdown timer.
    JavaScript polls payment_status_api every 10 seconds to auto-redirect
    when the payment completes.
    """
    userprofile = get_object_or_404(UserProfile, user=request.user)
    payment     = get_object_or_404(
        VoltagePayment, id=payment_id, user=userprofile
    )

    # If the payment is still generating, try a fresh fetch from Voltage
    if payment.status == 'generating' and voltage_client.is_configured():
        try:
            response = voltage_client.get_payment(str(payment.id))
            new_status = response.get('status', payment.status)
            if new_status != payment.status:
                payment.status = new_status
                extracted = voltage_client.extract_payment_data(response)
                payment.btc_address       = extracted['btc_address']
                payment.lightning_invoice = extracted['lightning_invoice']
                payment.bip21_uri         = extracted['bip21_uri']
                payment.voltage_response  = response
                payment.save()
        except VoltageAPIException as e:
            logger.warning(f"Could not refresh payment {payment.id}: {e}")

    return render(request, 'voltage_payments/payment_info.html', {
        'payment':    payment,
        'order':      payment.order,
        'is_testnet': payment.network == 'mutinynet',
    })


@csrf_exempt
@require_POST
def voltage_webhook(request):
    """
    Receive and process webhook events from Voltage.cloud.

    Expected headers:
      x-voltage-signature  — Base64 HMAC-SHA256 of (body + '.' + timestamp)
      x-voltage-timestamp  — Unix timestamp string
      x-voltage-event      — e.g. 'receive.completed'

    Payload envelope:
      { "type": "receive", "detail": { "event": "completed", "data": {...} } }
    """
    log_entry = None
    try:
        # --- Signature verification ---
        signature = request.META.get('HTTP_X_VOLTAGE_SIGNATURE', '')
        timestamp  = request.META.get('HTTP_X_VOLTAGE_TIMESTAMP', '')

        if not voltage_client.verify_webhook_signature(
            request.body, signature, timestamp
        ):
            logger.warning("Voltage webhook: invalid signature")
            return HttpResponse('Invalid signature', status=400)

        # --- Parse payload ---
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Voltage webhook: invalid JSON payload")
            return HttpResponse('Invalid JSON', status=400)

        event_type = request.META.get('HTTP_X_VOLTAGE_EVENT', '')
        detail     = payload.get('detail', {})
        data       = detail.get('data', {})
        payment_id = data.get('id', '')

        if not payment_id:
            logger.warning("Voltage webhook: no payment id in payload")
            return HttpResponse('Missing payment id', status=400)

        # --- Find our payment record ---
        try:
            payment = VoltagePayment.objects.get(id=payment_id)
        except VoltagePayment.DoesNotExist:
            logger.warning(f"Voltage webhook: no payment found for id {payment_id}")
            return HttpResponse('Payment not found', status=404)

        # --- Create audit log ---
        log_entry = VoltageWebhookLog.objects.create(
            payment=payment,
            voltage_payment_id=payment_id,
            event_type=event_type,
            payload=payload,
        )

        # --- Update payment status ---
        event_name = detail.get('event', '')

        if event_name == 'completed':
            payment.status       = 'completed'
            payment.webhook_data = payload
            payment.save()
            handle_completed_payment(payment)
            logger.info(f"Payment {payment_id} completed via webhook")

        elif event_name == 'expired':
            payment.status       = 'expired'
            payment.webhook_data = payload
            payment.save()
            logger.info(f"Payment {payment_id} expired")

        elif event_name == 'failed':
            payment.status       = 'failed'
            payment.webhook_data = payload
            payment.save()
            logger.warning(f"Payment {payment_id} failed")

        elif event_name in ('generated', 'refreshed'):
            # Address / invoice is now ready — extract and save it
            extracted = voltage_client.extract_payment_data(data)
            payment.btc_address       = extracted['btc_address']
            payment.lightning_invoice = extracted['lightning_invoice']
            payment.bip21_uri         = extracted['bip21_uri']
            payment.status            = 'receiving'
            payment.webhook_data      = payload
            payment.save()
            logger.info(f"Payment {payment_id} generated (now receiving)")

        else:
            logger.info(f"Voltage webhook: unhandled event '{event_name}'")

        log_entry.processed_ok = True
        log_entry.save()
        return HttpResponse('OK')

    except Exception as e:
        error_msg = f"Voltage webhook error: {e}"
        logger.error(error_msg)
        if log_entry:
            log_entry.error_message = error_msg
            log_entry.save()
        return HttpResponse(f"Error: {e}", status=500)


@login_required
def payment_status_api(request, payment_id):
    """
    JSON polling endpoint called by the payment_info page every 10 seconds.
    Optionally syncs with Voltage for real-time status.
    """
    userprofile = get_object_or_404(UserProfile, user=request.user)
    try:
        payment = VoltagePayment.objects.get(id=payment_id, user=userprofile)
    except VoltagePayment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)

    # Sync with Voltage if still pending
    if payment.status in ('generating', 'receiving') and voltage_client.is_configured():
        try:
            response   = voltage_client.get_payment(str(payment.id))
            new_status = response.get('status', payment.status)
            if new_status != payment.status:
                payment.status          = new_status
                extracted = voltage_client.extract_payment_data(response)
                payment.btc_address       = extracted['btc_address']
                payment.lightning_invoice = extracted['lightning_invoice']
                payment.bip21_uri         = extracted['bip21_uri']
                payment.voltage_response  = response
                payment.save()
                if new_status == 'completed':
                    handle_completed_payment(payment)
        except VoltageAPIException as e:
            logger.warning(f"Status poll for {payment.id} failed: {e}")

    return JsonResponse({
        'status':           payment.status,
        'status_display':   payment.get_status_display(),
        'is_paid':          payment.is_paid,
        'is_expired':       payment.is_expired,
        'amount_usd':       str(payment.amount_usd),
        'amount_sats':      payment.amount_sats,
        'btc_address':      payment.btc_address,
        'lightning_invoice': payment.lightning_invoice,
        'bip21_uri':        payment.bip21_uri,
        'network':          payment.network,
        'expires_at':       payment.expires_at.isoformat() if payment.expires_at else None,
        'created_at':       payment.created_at.isoformat(),
    })


@login_required
def payment_list(request):
    """List the current user's Bitcoin payments."""
    userprofile = get_object_or_404(UserProfile, user=request.user)
    payments    = VoltagePayment.objects.filter(
        user=userprofile
    ).select_related('order').order_by('-created_at')

    return render(request, 'voltage_payments/payment_list.html', {
        'payments': payments,
    })
