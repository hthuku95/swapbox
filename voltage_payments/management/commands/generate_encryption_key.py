"""
python manage.py generate_encryption_key

Generates a fresh Fernet symmetric encryption key for the
CREDENTIAL_ENCRYPTION_KEY setting used to encrypt Credential model fields.

Run this once and add the output to your .env file:
  CREDENTIAL_ENCRYPTION_KEY=<key>

WARNING: If you change this key after credentials have been stored, you will
lose the ability to decrypt existing records.  Back up your data before
rotating keys.
"""
from django.core.management.base import BaseCommand
from cryptography.fernet import Fernet


class Command(BaseCommand):
    help = 'Generate a Fernet encryption key for CREDENTIAL_ENCRYPTION_KEY.'

    def handle(self, *args, **options):
        key = Fernet.generate_key().decode()
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('New encryption key generated:'))
        self.stdout.write('')
        self.stdout.write(f'  CREDENTIAL_ENCRYPTION_KEY={key}')
        self.stdout.write('')
        self.stdout.write(
            'Add the line above to your .env file, then restart the server.'
        )
        self.stdout.write(
            self.style.WARNING(
                'WARNING: Never change this key once credentials are stored '
                '— doing so will make all existing encrypted fields unreadable.'
            )
        )
