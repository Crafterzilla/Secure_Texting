# server_auth.py - Updated for secure authentication
import asyncio
import os
import base64
import json
import hashlib
import hmac

from database import get_user_data, create_user, user_exists, store_public_key, get_public_key, store_challenge, get_user_salt
from server_utils import get_user_input, client, send_user_msg
from json_msg import CODES, msg
from datetime import datetime
from hash_utils import generate_salt, hash_password, compute_challenge_response

from crypto.encryption import encrypt_message
from crypto.key_management import load_public_key

class FailedAuth(Exception):
    pass

"""
Attempts to gather input from connected client. It then attempts to authenticate 3
times for the client. If it fails, the connection is ended. It sends the user json msg
objects and returns a client to the server
"""
async def authenticate_user(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> client:
    # Init vars
    attempts = 0
    username = ""

    try:
        # First ask if user wants to login or register
        auth_option = await get_user_input("Enter '1' to login or '2' to register: ", reader, writer)
        
        if auth_option == "2":
            # Registration flow
            username = await get_user_input("Create a username: ", reader, writer)
            
            # Check if username already exists
            if await user_exists(username):
                send_str = f"Username {username} already exists. Please try again."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                raise FailedAuth()
            
            # Get password
            password = await get_user_input("Create a password: ", reader, writer)
            
            # Generate salt for the user
            salt = generate_salt()
            
            # Hash the password server-side
            password_hash = hash_password(password, salt)
            
            # Now prompt client to generate and send their public key
            public_key_pem = await get_user_input("Please generate and send your public key: ", reader, writer)
            
            # Store public key
            if not await store_public_key(username, public_key_pem):
                await send_user_msg("Failed to store public key", CODES.ERROR, writer)
                raise FailedAuth()
            
            # Create the user
            if await create_user(username, password_hash, salt):
                send_str = f"User {username} created successfully! Please login now."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                # Set username to empty to force re-entering username for login
                username = ""
                # Continue to login flow
            else:
                send_str = f"Error creating user {username}. Please try again."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                raise FailedAuth()
        
        # Login flow
        while attempts < 3:
            # Try getting username
            if username == "":  # If we're not continuing from registration
                username = await get_user_input("Type in your username: ", reader, writer)
            
            print(f"Login attempt: {username}")
            
            # First, check if the username exists
            if not await user_exists(username):
                send_str = f"Username '{username}' not found. Please try again."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                username = ""  # Reset username for next attempt
                attempts += 1
                continue
            
            # Get user data including password hash and salt
            user_data = await get_user_data(username)
            if not user_data:
                send_str = f"Error retrieving user data. Please try again."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                username = ""  # Reset username for next attempt
                attempts += 1
                continue
            
            # Get user's public key
            public_key_pem = await get_public_key(username)
            if not public_key_pem:
                send_str = f"No public key found for user. Please register again."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                username = ""  # Reset username for next attempt
                attempts += 1
                continue
            
            # Generate random challenge
            challenge = os.urandom(32)
            challenge_b64 = base64.b64encode(challenge).decode()
            
            # Store challenge for verification
            await store_challenge(username, challenge_b64)
            
            # Encrypt challenge using user's public key
            encrypted_challenge = encrypt_message(challenge_b64, public_key_pem.encode())
            
            # Send encrypted challenge to client
            await send_user_msg(f"CHALLENGE {encrypted_challenge}", CODES.WRITE_BACK, writer)
            
            # Wait for GET_SALT request
            try:
                salt_request = await reader.read(1024)
                salt_request_str = salt_request.decode().strip()
                
                if salt_request_str == "GET_SALT":
                    # Send salt to client
                    user_salt = user_data["salt"]
                    salt_msg = msg(CODES.SALT.value, user_salt)
                    writer.write(salt_msg.to_json_str().encode())
                    await writer.drain()
                elif salt_request_str.startswith("ERROR_"):
                    # Client reported an error
                    send_str = f"Authentication error: {salt_request_str}"
                    await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                    username = ""  # Reset username for next attempt
                    attempts += 1
                    continue
                
                # Receive response from client
                response_data = await reader.read(1024)
                response = response_data.decode().strip()
                
                # Compute expected response
                expected_response = compute_challenge_response(user_data["password_hash"], challenge_b64)
                
                # Verify response
                if hmac.compare_digest(expected_response, response):
                    send_str = f"Hello {username}!!! Login Successful on {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}"
                    await send_user_msg(send_str, CODES.AUTHENTICATED, writer)
                    break
                else:
                    send_str = f"Authentication failed for {username}. Attempt {attempts + 1}!"
                    await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                    attempts += 1
                    username = ""  # Reset username for next attempt
            except Exception as e:
                print(f"Error during authentication: {e}")
                attempts += 1
                continue

        # If credentials could not be authenticated, raise exception
        if attempts == 3:
            raise FailedAuth()

    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise FailedAuth()

    return client(reader, writer, username)