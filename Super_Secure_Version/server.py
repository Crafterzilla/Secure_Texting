import asyncio
import json
import os
import base64
import sqlite3
import hashlib
import hmac
from crypto.encryption import encrypt_message
from hash_utils import generate_salt, hash_password, compute_challenge_response

# Constants
HOST = '127.0.0.1'
PORT = 8888

# Active clients
clients = {}

def init_database():
    """Initialize the database"""
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    
    # Create tables
    cur.execute('''
    CREATE TABLE IF NOT EXISTS members (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL
    )
    ''')
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS public_keys (
        username TEXT PRIMARY KEY,
        public_key TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES members(username)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized.")

def user_exists(username):
    """Check if a user exists"""
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    cur.execute("SELECT username FROM members WHERE username = ?", (username,))
    result = cur.fetchone() is not None
    conn.close()
    return result

def create_user(username, password_hash, salt, public_key):
    """Create a new user"""
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    
    try:
        # Insert into members table
        cur.execute(
            "INSERT INTO members (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt)
        )
        
        # Insert into public_keys table
        cur.execute(
            "INSERT INTO public_keys (username, public_key) VALUES (?, ?)",
            (username, public_key)
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()

def get_user_data(username):
    """Get user data"""
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT password_hash, salt FROM members WHERE username = ?", (username,))
        result = cur.fetchone()
        
        if result:
            cur.execute("SELECT public_key FROM public_keys WHERE username = ?", (username,))
            public_key = cur.fetchone()
            
            return {
                "password_hash": result[0],
                "salt": result[1],
                "public_key": public_key[0] if public_key else None
            }
        return None
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None
    finally:
        conn.close()

async def handle_client(reader, writer):
    """Handle a client connection"""
    addr = writer.get_extra_info('peername')
    print(f"New connection from {addr}")
    
    try:
        # Send welcome message
        writer.write("Enter '1' to login or '2' to register:".encode())
        await writer.drain()
        
        # Get choice
        choice_data = await reader.read(1024)
        if not choice_data:
            return
        
        choice = choice_data.decode().strip()
        
        if choice == "2":  # REGISTER
            # Send username prompt
            writer.write("Enter username:".encode())
            await writer.drain()
            
            # Get username
            username_data = await reader.read(1024)
            if not username_data:
                return
            
            username = username_data.decode().strip()
            
            # Check if username exists
            if user_exists(username):
                writer.write(f"Username {username} already exists".encode())
                await writer.drain()
                return
            
            # Send password prompt
            writer.write("Enter password:".encode())
            await writer.drain()
            
            # Get password
            password_data = await reader.read(1024)
            if not password_data:
                return
            
            password = password_data.decode().strip()
            
            # Generate salt
            salt = generate_salt()
            
            # Hash password
            password_hash = hash_password(password, salt)
            
            # Prompt for public key
            writer.write("Send public key:".encode())
            await writer.drain()
            
            # Get public key
            public_key_data = await reader.read(2048)
            if not public_key_data:
                return
            
            public_key = public_key_data.decode().strip()
            
            # Create user
            if create_user(username, password_hash, salt, public_key):
                writer.write(f"User {username} created successfully!".encode())
                await writer.drain()
            else:
                writer.write("Error creating user".encode())
                await writer.drain()
        
        elif choice == "1":  # LOGIN
            # Send username prompt
            writer.write("Enter username:".encode())
            await writer.drain()
            
            # Get username
            username_data = await reader.read(1024)
            if not username_data:
                return
            
            username = username_data.decode().strip()
            print(f"Login attempt: {username}")
            
            # Check if user exists
            if not user_exists(username):
                writer.write(f"Username {username} not found".encode())
                await writer.drain()
                return
            
            # Get user data
            user_data = get_user_data(username)
            if not user_data or not user_data["public_key"]:
                writer.write("Error retrieving user data".encode())
                await writer.drain()
                return
            
            # Generate challenge
            challenge = os.urandom(32)
            challenge_b64 = base64.b64encode(challenge).decode()
            
            # Encrypt challenge
            try:
                encrypted_challenge = encrypt_message(challenge_b64, user_data["public_key"].encode())
                
                # Send challenge
                writer.write(f"CHALLENGE {encrypted_challenge}".encode())
                await writer.drain()
                
                # Wait for salt request
                salt_request = await reader.read(1024)
                if not salt_request or salt_request.decode().strip() != "GET_SALT":
                    writer.write("Invalid salt request".encode())
                    await writer.drain()
                    return
                
                # Send salt
                salt_msg = json.dumps({"code": "SALT", "msg": user_data["salt"]})
                writer.write(salt_msg.encode())
                await writer.drain()
                
                # Get response
                response_data = await reader.read(1024)
                if not response_data:
                    return
                
                response = response_data.decode().strip()
                
                # Compute expected response
                expected = compute_challenge_response(user_data["password_hash"], challenge_b64)
                
                # Verify
                if hmac.compare_digest(expected, response):
                    # Authentication successful
                    writer.write(f"Hello {username}! Login successful.".encode())
                    await writer.drain()
                    
                    # Chat loop
                    clients[username] = writer
                    
                    try:
                        while True:
                            cmd_data = await reader.read(1024)
                            if not cmd_data:
                                break
                            
                            cmd = cmd_data.decode().strip()
                            
                            print(cmd, cmd.upper())

                            if cmd.upper() == "EXIT":
                                break
                            elif cmd.upper() == "GETUSERS":
                                writer.write(f"Active users: {list(clients.keys())}".encode())
                                await writer.drain()
                            elif cmd.upper() == "HELP":
                                help_text = "Commands: GETUSERS, HELP, SEND message TO username, EXIT"
                                writer.write(help_text.encode())
                                await writer.drain()
                            elif cmd.upper().startswith("SEND ") and " TO " in cmd:
                                parts = cmd.split(" TO ", 1)
                                message = parts[0][5:]  # Skip "SEND "
                                recipient = parts[1]
                                
                                if recipient in clients:
                                    clients[recipient].write(f"[{username}]: {message}".encode())
                                    await clients[recipient].drain()
                                    writer.write(f"Message sent to {recipient}".encode())
                                    await writer.drain()
                                else:
                                    writer.write(f"User {recipient} not online".encode())
                                    await writer.drain()
                            else:
                                writer.write("Unknown command. Type HELP for commands.".encode())
                                await writer.drain()
                    finally:
                        if username in clients:
                            del clients[username]
                else:
                    writer.write("Authentication failed".encode())
                    await writer.drain()
            except Exception as e:
                print(f"Error during login: {e}")
                writer.write(f"Login error: {str(e)}".encode())
                await writer.drain()
        else:
            writer.write("Invalid choice".encode())
            await writer.drain()
    
    except Exception as e:
        print(f"Error handling client: {e}")
    
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection closed with {addr}")

async def main():
    # Initialize database
    init_database()
    
    # Start server
    server = await asyncio.start_server(handle_client, HOST, PORT)
    
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shutdown by user")