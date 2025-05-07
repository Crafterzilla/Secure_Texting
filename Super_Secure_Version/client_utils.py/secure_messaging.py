import asyncio
import json
import sys
import os

# Add parent directory to path so we can import crypto modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto.key_management import generate_key_pair, save_keys_to_file, load_private_key, load_public_key
from crypto.encryption import encrypt_message, decrypt_message

class SecureMessaging:
    def __init__(self, username, reader, writer):
        self.username = username
        self.reader = reader
        self.writer = writer
        self.private_key = None
        self.public_key = None
        self.public_keys_cache = {}  # Cache for other users' public keys
    
    async def initialize_keys(self):
        """Initialize encryption keys for this client."""
        # Check if keys already exist
        private_key = load_private_key(self.username)
        public_key = load_public_key(self.username)
        
        # If keys don't exist, generate them
        if not private_key or not public_key:
            private_key, public_key = generate_key_pair()
            save_keys_to_file(self.username, private_key, public_key)
            
            # Upload public key to server
            await self.upload_public_key(public_key)
        
        self.private_key = private_key
        self.public_key = public_key
    
    async def upload_public_key(self, public_key):
        """Upload the public key to the server."""
        # Format: "PUBKEY <base64-encoded-key>"
        encoded_key = public_key.decode('utf-8')
        self.writer.write(f"PUBKEY {encoded_key}".encode())
        await self.writer.drain()
    
    async def get_recipient_public_key(self, recipient_username):
        """Get a recipient's public key from the server."""
        # Check cache first
        if recipient_username in self.public_keys_cache:
            return self.public_keys_cache[recipient_username]
        
        # Request public key from server
        self.writer.write(f"GETKEY {recipient_username}".encode())
        await self.writer.drain()
        
        # Wait for response
        data = await self.reader.read(4096)  # Public keys can be large
        response = data.decode()
        
        # Parse response (format: "KEY <username> <base64-encoded-key>")
        if response.startswith("KEY "):
            parts = response.split(" ", 2)
            if len(parts) == 3 and parts[1] == recipient_username:
                # Store in cache
                public_key = parts[2].encode('utf-8')
                self.public_keys_cache[recipient_username] = public_key
                return public_key
        
        return None
    
    async def send_encrypted_message(self, message, recipient_username):
        """Encrypt and send a message to another user."""
        # Get recipient's public key
        recipient_public_key = await self.get_recipient_public_key(recipient_username)
        
        if not recipient_public_key:
            return False, "Could not get recipient's public key"
        
        # Encrypt the message
        encrypted_message = encrypt_message(message, recipient_public_key)
        
        # Send the encrypted message
        self.writer.write(f"SEND {encrypted_message} TO {recipient_username}".encode())
        await self.writer.drain()
        
        return True, "Message sent"
    
    def decrypt_received_message(self, encrypted_message):
        """Decrypt a received message."""
        try:
            return decrypt_message(encrypted_message, self.private_key)
        except Exception as e:
            return f"Error decrypting message: {e}"