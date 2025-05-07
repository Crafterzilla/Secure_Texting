import os
import hashlib
import base64

def secure_password_hash(password):
    """
    Create a secure password hash using scrypt with a random salt.
    Much stronger than the previous SHA-256 implementation.
    """
    # Generate a random salt (16 bytes)
    salt = os.urandom(16)
    
    # Hash the password with scrypt
    password_hash = hashlib.scrypt(
        password.encode(), 
        salt=salt, 
        n=16384,  # CPU/memory cost parameter
        r=8,      # Block size parameter
        p=1,      # Parallelization parameter
        dklen=32  # Output length
    )
    
    # Combine salt and hash for storage
    combined = salt + password_hash
    
    # Base64 encode for storage as text
    return base64.b64encode(combined).decode('utf-8')

def verify_password(stored_hash, provided_password):
    """
    Verify a password against a stored hash.
    """
    # Decode the stored hash
    decoded = base64.b64decode(stored_hash.encode('utf-8'))
    
    # Extract salt (first 16 bytes)
    salt = decoded[:16]
    stored_password_hash = decoded[16:]
    
    # Hash the provided password with the same salt
    calculated_hash = hashlib.scrypt(
        provided_password.encode(),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=32
    )
    
    # Compare in constant time to prevent timing attacks
    return calculated_hash == stored_password_hash