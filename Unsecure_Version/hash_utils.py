import hashlib # for sha256
import base64 # for encoding4

'''
As a brief explanation, hashing is a 1-way function so its 'impossible' to decrypt if intercepted. The salt is a randomly generated string prepended to the password, making even
two identical passwords hash differently. We store the salt with the hash.

In the future we can implement work factor, which slows down the process of encryption to make it more computationally infeasible to crack.
'''

def hash_password(password: str) -> str:
    """Simple password hashing using SHA-256 - no salt for initial implementation"""
    return hashlib.sha256(password.encode()).hexdigest()
