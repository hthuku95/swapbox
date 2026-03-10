"""
python manage.py setup_voltage

Validates Voltage.cloud connectivity, fetches wallet info, saves it to the
database, and optionally registers a webhook.

Usage:
  python manage.py setup_voltage
  python manage.py setup_voltage --create-webhook --webhook-url https://yourdomain.com/bitcoin/webhook/
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from voltage_payments.voltage_client import voltage_client, VoltageAPIException
from voltage_payments.models import VoltageWallet, VoltageWebhookConfig


class Command(BaseCommand):
    help = 'Validate Voltage.cloud connection, sync wallet to DB, optionally create webhook.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-webhook',
            action='store_true',
            help='Register a new webhook with Voltage (requires --webhook-url)',
        )
        parser.add_argument(
            '--webhook-url',
            type=str,
            default='',
            help='Full public HTTPS URL of the webhook endpoint.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Voltage.cloud Setup'))
        self.stdout.write('')

        # ---- Config check ----
        if not voltage_client.is_configured():
            self.stderr.write(self.style.ERROR(
                'Voltage is not configured. Check your .env file for:\n'
                '  SWAPBOX_VOLTAGE_API_KEY\n'
                '  VOLTAGE_ORGANIZATION_ID\n'
                '  VOLTAGE_STAGING_ENVIRONMENT_ID (or PRODUCTION)\n'
                '  SWAPBOX_STAGING_WALLET_ID (or PRODUCTION)'
            ))
            return

        network = getattr(settings, 'VOLTAGE_NETWORK', 'mutinynet')
        self.stdout.write(f"  Network : {network}")
        self.stdout.write(f"  Env ID  : {getattr(settings, 'VOLTAGE_ENVIRONMENT_ID', '—')}")
        self.stdout.write(f"  Org ID  : {getattr(settings, 'VOLTAGE_ORGANIZATION_ID', '—')}")
        self.stdout.write(f"  Wallet  : {getattr(settings, 'VOLTAGE_WALLET_ID', '—')}")
        self.stdout.write('')

        # ---- Fetch wallet ----
        self.stdout.write('Fetching wallet info from Voltage API…')
        try:
            wallet_data = voltage_client.get_wallet()
        except VoltageAPIException as e:
            self.stderr.write(self.style.ERROR(f'API error: {e}'))
            return

        name    = wallet_data.get('name', 'Swapbox Wallet')
        wid     = wallet_data.get('id', '')
        org_id  = wallet_data.get('organization_id', '')
        env_id  = wallet_data.get('environment_id', '')
        balances = wallet_data.get('balances', [])
        balance_msats = balances[0].get('available', 0) if balances else 0

        self.stdout.write(self.style.SUCCESS(f"  Connected  : {name}"))
        self.stdout.write(f"  Wallet ID  : {wid}")
        self.stdout.write(f"  Org ID     : {org_id}")
        self.stdout.write(f"  Env ID     : {env_id}")
        self.stdout.write(f"  Balance    : {balance_msats:,} msats ({balance_msats // 1000:,} sats)")
        self.stdout.write('')

        # ---- Save to DB ----
        wallet, created = VoltageWallet.objects.update_or_create(
            wallet_id=wid,
            defaults={
                'organization_id': org_id,
                'environment_id':  env_id,
                'name':            name,
                'network':         network,
                'is_staging':      settings.DEBUG,
                'is_active':       True,
                'balance_msats':   balance_msats,
                'last_synced':     timezone.now(),
            },
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f"  {action} VoltageWallet in database."))

        # ---- Webhook ----
        if options['create_webhook']:
            webhook_url = options['webhook_url']
            if not webhook_url:
                self.stderr.write(self.style.ERROR(
                    '--webhook-url is required when using --create-webhook'
                ))
                return

            self.stdout.write(f"\nRegistering webhook at: {webhook_url}")
            try:
                wh_result = voltage_client.create_webhook(webhook_url)
            except VoltageAPIException as e:
                self.stderr.write(self.style.ERROR(f'Webhook registration failed: {e}'))
                return

            wh_id     = wh_result.get('id', '')
            wh_secret = wh_result.get('shared_secret', '')

            VoltageWebhookConfig.objects.update_or_create(
                environment_id=env_id,
                defaults={
                    'webhook_id':    wh_id,
                    'webhook_url':   webhook_url,
                    'shared_secret': wh_secret,
                    'is_active':     True,
                    'events':        wh_result.get('events', []),
                },
            )

            self.stdout.write(self.style.SUCCESS(f"  Webhook ID     : {wh_id}"))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                '  *** ACTION REQUIRED ***\n'
                f'  shared_secret = {wh_secret}\n\n'
                '  Add this to your .env file NOW (it will not be shown again):\n'
                f'  VOLTAGE_WEBHOOK_SECRET={wh_secret}'
            ))
        else:
            self.stdout.write(
                'Tip: run with --create-webhook --webhook-url <URL> to register a webhook.'
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Setup complete.'))
