import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

def sign_message(message, private_key_pem):
    """Sign a message using a private key."""
    # Load the private key
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None
    )
    
    # Create a signature
    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Return base64 encoded signature
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(message, signature, public_key_pem):
    """Verify a message signature using a public key."""
    # Load the public key
    public_key = serialization.load_pem_public_key(public_key_pem)
    
    # Decode the signature
    signature_bytes = base64.b64decode(signature)
    
    try:
        # Verify the signature
        public_key.verify(
            signature_bytes,
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False