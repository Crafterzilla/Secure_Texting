import os
import json
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_key_pair():
    """Generate a new RSA key pair for a user."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    public_key = private_key.public_key()
    
    # Serialize keys to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem

def save_keys_to_file(username, private_key, public_key, path="."):
    """Save a user's key pair to files (client-side)."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.join(path, "keys"), exist_ok=True)
    
    # Save private key
    with open(os.path.join(path, "keys", f"{username}_private.pem"), "wb") as f:
        f.write(private_key)
    
    # Save public key
    with open(os.path.join(path, "keys", f"{username}_public.pem"), "wb") as f:
        f.write(public_key)

def load_private_key(username, path="."):
    """Load a user's private key from a file (client-side)."""
    try:
        with open(os.path.join(path, "keys", f"{username}_private.pem"), "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None

def load_public_key(username, path="."):
    """Load a user's public key from a file (client-side)."""
    try:
        with open(os.path.join(path, "keys", f"{username}_public.pem"), "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None
        
# Server-side key operations will use database functions