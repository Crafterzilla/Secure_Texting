# crypto/__init__.py

# Import key functions from submodules to make them available directly from the crypto package
from .key_management import generate_key_pair, save_keys_to_file, load_private_key, load_public_key
from .encryption import encrypt_message, decrypt_message
from .password import secure_password_hash, verify_password
from .signatures import sign_message, verify_signature

# You can define what gets exported when using "from crypto import *"
__all__ = [
    'generate_key_pair',
    'save_keys_to_file',
    'load_private_key',
    'load_public_key',
    'encrypt_message',
    'decrypt_message',
    'secure_password_hash',
    'verify_password',
    'sign_message',
    'verify_signature'
]