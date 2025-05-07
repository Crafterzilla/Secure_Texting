# hash_utils.py - Improved version
import hashlib
import os
import base64

def generate_salt():
    """Generate a random salt for password hashing"""
    return os.urandom(16).hex()

def hash_password(password, salt):
    """
    Create a secure password hash using scrypt with the provided salt.
    Returns the hash as a hex string.
    """
    password_hash = hashlib.scrypt(
        password.encode(), 
        salt=bytes.fromhex(salt), 
        n=16384,  # CPU/memory cost parameter
        r=8,      # Block size parameter
        p=1,      # Parallelization parameter
        dklen=32  # Output length
    )
    
    # Return the hash as hex string
    return password_hash.hex()

def compute_challenge_response(password_hash, challenge):
    """
    Compute a response to a challenge using the password hash.
    This function is used by the client during authentication.
    
    Args:
        password_hash: The locally stored password hash (hex string)
        challenge: The base64-encoded challenge from the server
        
    Returns:
        A challenge response as a hex string
    """
    # Decode the challenge
    challenge_bytes = base64.b64decode(challenge.encode('utf-8'))
    
    # Combine password hash and challenge, then hash again
    combined = bytes.fromhex(password_hash) + challenge_bytes
    response = hashlib.sha256(combined).hexdigest()
    
    return response