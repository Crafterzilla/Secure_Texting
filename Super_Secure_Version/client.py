# minimal_client.py - Simplified secure client
import asyncio
import json
import os
import getpass
import sys
from crypto.key_management import generate_key_pair
from crypto.encryption import encrypt_message, decrypt_message
from hash_utils import hash_password, compute_challenge_response

# Constants
HOST = '127.0.0.1'
PORT = 8888

async def main():
    # Connect to server
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        print(f"Connected to {HOST}:{PORT}")
    except Exception as e:
        print(f"Connection error: {e}")
        return
    
    try:
        # Get welcome message
        data = await reader.read(1024)
        print(data.decode())
        
        # Choose login or register
        choice = input("> ")
        writer.write(choice.encode())
        await writer.drain()
        
        if choice == "2":  # REGISTER
            # Get username prompt
            data = await reader.read(1024)
            print(data.decode())
            
            # Enter username
            username = input("> ")
            writer.write(username.encode())
            await writer.drain()
            
            # Get result or password prompt
            data = await reader.read(1024)
            response = data.decode()
            print(response)
            
            if "exists" in response:
                return
            
            # Enter password
            password = getpass.getpass("> ")
            writer.write(password.encode())
            await writer.drain()
            
            # Get public key prompt
            data = await reader.read(1024)
            print(data.decode())
            
            # Generate key pair
            print("Generating key pair...")
            private_key, public_key = generate_key_pair()
            
            # Save keys
            os.makedirs("keys", exist_ok=True)
            with open(f"keys/{username}_private.pem", "wb") as f:
                f.write(private_key)
            with open(f"keys/{username}_public.pem", "wb") as f:
                f.write(public_key)
            
            print(f"Keys saved to keys/{username}_private.pem and keys/{username}_public.pem")
            
            # Send public key
            writer.write(public_key.decode().encode())
            await writer.drain()
            
            # Get result
            data = await reader.read(1024)
            print(data.decode())
            print("Registration complete. Restart client to login.")
        
        elif choice == "1":  # LOGIN
            # Get username prompt
            data = await reader.read(1024)
            print(data.decode())
            
            # Enter username
            username = input("> ")
            writer.write(username.encode())
            await writer.drain()
            
            # Get result or challenge
            data = await reader.read(1024)
            response = data.decode()
            
            if "not found" in response:
                print(response)
                return
            
            if "CHALLENGE" in response:
                print("Received authentication challenge")
                
                # Extract challenge
                challenge_parts = response.split("CHALLENGE ", 1)
                if len(challenge_parts) < 2:
                    print("Invalid challenge format")
                    return
                
                encrypted_challenge = challenge_parts[1]
                
                try:
                    # Load private key
                    with open(f"keys/{username}_private.pem", "rb") as f:
                        private_key = f.read()
                except FileNotFoundError:
                    print(f"Private key for {username} not found")
                    return
                
                try:
                    # Decrypt challenge
                    decrypted_challenge = decrypt_message(encrypted_challenge, private_key)
                    print("Challenge decrypted")
                except Exception as e:
                    print(f"Failed to decrypt challenge: {e}")
                    return
                
                # Get password
                password = getpass.getpass("Password: ")
                
                # Request salt
                writer.write("GET_SALT".encode())
                await writer.drain()
                
                # Get salt
                data = await reader.read(1024)
                try:
                    salt_json = json.loads(data.decode())
                    salt = salt_json["msg"]
                    print("Received salt")
                except Exception as e:
                    print(f"Error parsing salt: {e}")
                    print(f"Raw: {data.decode()}")
                    return
                
                # Hash password
                password_hash = hash_password(password, salt)
                
                # Compute response
                response = compute_challenge_response(password_hash, decrypted_challenge)
                
                # Send response
                writer.write(response.encode())
                await writer.drain()
                
                # Get result
                data = await reader.read(1024)
                result = data.decode()
                print(result)
                
                if "Login successful" in result:
                    # Chat loop
                    print("\nCommands: GETUSERS, HELP, SEND message TO username, EXIT")
                    
                    # Start reader task
                    async def read_messages():
                        while True:
                            try:
                                data = await reader.read(1024)
                                if not data:
                                    print("\nServer disconnected")
                                    break
                                print(f"\n{data.decode()}")
                                print("> ", end="", flush=True)
                            except Exception as e:
                                print(f"\nError: {e}")
                                break
                    
                    # Start the task
                    task = asyncio.create_task(read_messages())
                    
                    try:
                        while True:
                            message = input("> ")
                            
                            if not message.strip():
                                continue
                            
                            if message.upper() == "EXIT":
                                break
                            
                            # Send message
                            writer.write(message.encode())
                            await writer.drain()
                    except KeyboardInterrupt:
                        print("\nExiting...")
                    finally:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        writer.close()
        await writer.wait_closed()
        print("Disconnected")

if __name__ == "__main__":
    # Make sure keys directory exists
    os.makedirs("keys", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")