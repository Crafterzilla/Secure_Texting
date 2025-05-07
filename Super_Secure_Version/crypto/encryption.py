import os
import json
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization

# Maximum bytes that can be encrypted with RSA-2048 using OAEP padding with SHA-256
RSA_MAX_BYTES = 190

def encrypt_message(message, recipient_public_key_pem):
    """
    Encrypt a message for a recipient using their public key.
    Automatically chooses between direct RSA or hybrid encryption based on message size.
    """
    # Convert message to bytes
    message_bytes = message.encode('utf-8')
    
    # For small messages, use RSA directly
    if len(message_bytes) <= RSA_MAX_BYTES:
        return encrypt_with_rsa(message_bytes, recipient_public_key_pem)
    
    # For larger messages, use hybrid encryption
    return encrypt_with_hybrid(message_bytes, recipient_public_key_pem)

def encrypt_with_rsa(message_bytes, recipient_public_key_pem):
    """Encrypt small messages directly with RSA."""
    # Load recipient's public key
    recipient_key = serialization.load_pem_public_key(recipient_public_key_pem)
    
    # Encrypt the message
    encrypted = recipient_key.encrypt(
        message_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Return as JSON with method indicator
    return json.dumps({
        "method": "rsa",
        "data": base64.b64encode(encrypted).decode('utf-8')
    })

def encrypt_with_hybrid(message_bytes, recipient_public_key_pem):
    """Encrypt larger messages with AES + RSA."""
    # Generate a random AES key
    aes_key = os.urandom(32)  # 256-bit key
    
    # Generate random IV
    iv = os.urandom(16)
    
    # Encrypt the message with AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
    encryptor = cipher.encryptor()
    encrypted_message = encryptor.update(message_bytes) + encryptor.finalize()
    
    # Encrypt the AES key with RSA
    recipient_key = serialization.load_pem_public_key(recipient_public_key_pem)
    encrypted_key = recipient_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Return everything as a JSON object
    return json.dumps({
        "method": "hybrid",
        "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8'),
        "iv": base64.b64encode(iv).decode('utf-8'),
        "data": base64.b64encode(encrypted_message).decode('utf-8')
    })

def decrypt_message(encrypted_data_json, private_key_pem):
    """Decrypt a message using the recipient's private key."""
    # Parse the JSON data
    encrypted_data = json.loads(encrypted_data_json)
    method = encrypted_data["method"]
    
    # Load private key
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None
    )
    
    # If RSA was used directly
    if method == "rsa":
        encrypted = base64.b64decode(encrypted_data["data"])
        decrypted = private_key.decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode('utf-8')
    
    # If hybrid encryption was used
    elif method == "hybrid":
        # Decrypt the AES key
        encrypted_key = base64.b64decode(encrypted_data["encrypted_key"])
        aes_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Decrypt the message with the AES key
        iv = base64.b64decode(encrypted_data["iv"])
        encrypted_message = base64.b64decode(encrypted_data["data"])
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_message) + decryptor.finalize()
        
        return decrypted.decode('utf-8')