from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from .models import VoltageWallet, VoltagePayment, VoltageWebhookLog, VoltageWebhookConfig
from .voltage_client import voltage_client, VoltageAPIException


@admin.register(VoltageWallet)
class VoltageWalletAdmin(admin.ModelAdmin):
    list_display   = ['name', 'network', 'environment_badge', 'balance_display', 'is_active', 'last_synced']
    list_filter    = ['network', 'is_staging', 'is_active']
    readonly_fields = ['balance_msats', 'last_synced', 'created_at', 'updated_at']
    actions        = ['sync_balance']

    fieldsets = (
        ('Wallet Identity', {
            'fields': ('name', 'wallet_id', 'organization_id', 'environment_id'),
        }),
        ('Configuration', {
            'fields': ('network', 'is_staging', 'is_active'),
        }),
        ('Balance (synced from Voltage)', {
            'fields': ('balance_msats', 'last_synced'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def environment_badge(self, obj):
        color = '#fd7e14' if obj.is_staging else '#28a745'
        label = 'Staging' if obj.is_staging else 'Production'
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:3px;font-size:11px;">{}</span>',
            color, label,
        )
    environment_badge.short_description = 'Environment'

    def balance_display(self, obj):
        sats = obj.balance_sats
        btc  = obj.balance_btc
        return format_html('<b>{:,}</b> sats &nbsp;({} BTC)', sats, btc)
    balance_display.short_description = 'Balance'

    def sync_balance(self, request, queryset):
        updated = 0
        for wallet in queryset:
            try:
                data = voltage_client.get_wallet(wallet.wallet_id)
                balances = data.get('balances', [])
                wallet.balance_msats = balances[0].get('available', 0) if balances else 0
                wallet.last_synced   = timezone.now()
                wallet.save(update_fields=['balance_msats', 'last_synced'])
                updated += 1
            except VoltageAPIException as e:
                self.message_user(
                    request,
                    f"Error syncing wallet {wallet.name}: {e}",
                    level=messages.ERROR,
                )
        if updated:
            self.message_user(request, f"Synced balance for {updated} wallet(s).")
    sync_balance.short_description = 'Sync balance from Voltage API'


@admin.register(VoltageWebhookConfig)
class VoltageWebhookConfigAdmin(admin.ModelAdmin):
    list_display  = ['webhook_id', 'webhook_url', 'environment_id', 'is_active', 'created_at']
    list_filter   = ['is_active']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Webhook Details', {
            'fields': ('webhook_id', 'webhook_url', 'environment_id', 'is_active'),
        }),
        ('Secret (sensitive)', {
            'fields': ('shared_secret',),
            'description': (
                'The shared_secret is used to verify webhook signatures. '
                'It is shown only once by Voltage at creation time. '
                'Also set VOLTAGE_WEBHOOK_SECRET in your .env file.'
            ),
        }),
        ('Events', {
            'fields': ('events',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


@admin.register(VoltagePayment)
class VoltagePaymentAdmin(admin.ModelAdmin):
    list_display   = [
        'short_id', 'user', 'amount_usd', 'amount_sats_display',
        'status_badge', 'payment_kind', 'network', 'created_at', 'order_link',
    ]
    list_filter    = ['status', 'payment_kind', 'network', 'created_at']
    search_fields  = ['user__user__username', 'user__user__email', 'id', 'order__reference_code']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'voltage_response', 'webhook_data',
        'btc_address', 'lightning_invoice', 'bip21_uri', 'amount_msats',
        'btc_price_at_creation',
    ]
    ordering       = ['-created_at']
    actions        = ['sync_from_voltage', 'mark_expired']

    fieldsets = (
        ('Payment Identity', {
            'fields': ('id', 'user', 'order', 'wallet'),
        }),
        ('Amounts', {
            'fields': ('amount_usd', 'amount_msats', 'btc_price_at_creation'),
        }),
        ('Status', {
            'fields': ('status', 'payment_kind', 'network', 'expires_at'),
        }),
        ('Payment Details', {
            'fields': ('btc_address', 'lightning_invoice', 'bip21_uri'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        ('Raw Voltage Data', {
            'fields': ('voltage_response', 'webhook_data'),
            'classes': ('collapse',),
        }),
    )

    def short_id(self, obj):
        return str(obj.id)[:8] + '…'
    short_id.short_description = 'ID'

    def status_badge(self, obj):
        colours = {
            'generating': '#6c757d',
            'receiving':  '#ffc107',
            'completed':  '#28a745',
            'expired':    '#343a40',
            'failed':     '#dc3545',
        }
        colour = colours.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;'
            'border-radius:3px;font-size:12px;">{}</span>',
            colour, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def amount_sats_display(self, obj):
        return f"{obj.amount_sats:,} sats"
    amount_sats_display.short_description = 'Amount (sats)'

    def order_link(self, obj):
        if obj.order:
            from django.urls import reverse
            url = reverse('admin:payments_order_change', args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', url, obj.order.reference_code)
        return '—'
    order_link.short_description = 'Order'

    def has_add_permission(self, request):
        return False  # Payments are created programmatically only

    def sync_from_voltage(self, request, queryset):
        """Pull current status from Voltage API and update DB records."""
        from .views import handle_completed_payment
        updated = 0
        for payment in queryset.exclude(status__in=['completed', 'failed']):
            try:
                data   = voltage_client.get_payment(str(payment.id))
                new_st = data.get('status', '')

                status_map = {
                    'generating': 'generating',
                    'receiving':  'receiving',
                    'completed':  'completed',
                    'expired':    'expired',
                    'failed':     'failed',
                }
                mapped = status_map.get(new_st)
                if mapped and mapped != payment.status:
                    payment.status = mapped
                    payment.voltage_response = data
                    payment.save()
                    if mapped == 'completed':
                        handle_completed_payment(payment)
                    updated += 1
            except VoltageAPIException as e:
                self.message_user(
                    request,
                    f"Error syncing payment {payment.id}: {e}",
                    level=messages.ERROR,
                )
        self.message_user(request, f"Synced {updated} payment(s) from Voltage.")
    sync_from_voltage.short_description = 'Sync status from Voltage API'

    def mark_expired(self, request, queryset):
        updated = queryset.filter(
            status__in=['generating', 'receiving']
        ).update(status='expired')
        self.message_user(request, f"Marked {updated} payment(s) as expired.")
    mark_expired.short_description = 'Mark selected payments as expired'


@admin.register(VoltageWebhookLog)
class VoltageWebhookLogAdmin(admin.ModelAdmin):
    list_display   = ['event_type', 'voltage_payment_id', 'payment', 'processed_ok', 'created_at']
    list_filter    = ['event_type', 'processed_ok', 'created_at']
    search_fields  = ['voltage_payment_id', 'payment__id']
    readonly_fields = ['event_type', 'voltage_payment_id', 'payment', 'payload', 'processed_ok', 'error_message', 'created_at']
    ordering       = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
