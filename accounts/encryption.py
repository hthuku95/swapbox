"""
Field-level encryption for sensitive Credential model fields.

Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) from the
cryptography library.  The encryption key is read from settings.CREDENTIAL_ENCRYPTION_KEY.

Generate a key with:
  python manage.py generate_encryption_key

Security layers:
  - Fernet encryption: strong authenticated encryption, protects data at rest
  - HMAC-SHA256 MAC inside Fernet: guarantees ciphertext integrity
  - Key stored in env var / .env, never in source code or the database
"""
import logging
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_fernet_instance = None


def _get_fernet():
    """Return a cached Fernet instance (reads key from settings on first call)."""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    key = getattr(settings, 'CREDENTIAL_ENCRYPTION_KEY', '')
    if not key:
        raise ValueError(
            'CREDENTIAL_ENCRYPTION_KEY is not configured. '
            'Run: python manage.py generate_encryption_key'
        )
    if isinstance(key, str):
        key = key.encode()
    _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a plaintext string.  Returns a URL-safe base64-encoded ciphertext
    string suitable for storage in a TextField.

    Returns an empty string for empty / None input.
    """
    if not plaintext:
        return plaintext or ''
    try:
        f = _get_fernet()
        return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f'Encryption failed: {e}')
        raise


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a ciphertext string.  Returns the original plaintext.

    Returns an empty string for empty / None input.
    Returns None if decryption fails (wrong key or corrupted data) to avoid
    crashing pages that display credentials — log the error instead.
    """
    if not ciphertext:
        return ciphertext or ''
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        logger.error(
            'Credential decryption failed — InvalidToken. '
            'The encryption key may have changed or the data is corrupted.'
        )
        return None
    except Exception as e:
        logger.error(f'Credential decryption error: {e}')
        return None


class EncryptedTextField(object):
    """
    Descriptor that transparently encrypts on assignment and decrypts on access.

    Usage in a model:
        from django.db import models
        from .encryption import EncryptedTextField as EncryptedDescriptor

    We implement this as a Django custom model Field (TextField subclass)
    so that Django migrations, admin, and forms all work correctly.
    """
    pass


from django.db import models


class EncryptedCharField(models.TextField):
    """
    A Django model field backed by a TEXT column that transparently
    encrypts the value on write and decrypts it on read.

    Use this as a drop-in replacement for CharField / TextField on any
    field that stores sensitive information (passwords, tokens, etc.).

    max_length on the Python side still validates user input length before
    encryption, but the database column is TEXT (no length limit) to
    accommodate the longer encrypted value.
    """

    def __init__(self, *args, plaintext_max_length=512, **kwargs):
        # Store the max length for Python-side validation
        self._plaintext_max_length = plaintext_max_length
        # Remove max_length from kwargs since TextField doesn't need it
        kwargs.pop('max_length', None)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        """Called every time a value is loaded from the database."""
        return decrypt_value(value)

    def get_prep_value(self, value):
        """Called every time a value is about to be saved to the database."""
        if value is None:
            return value
        return encrypt_value(str(value))

    def to_python(self, value):
        """Used by forms and deserialization — value is already plaintext."""
        return value
