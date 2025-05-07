# server_auth.py - Improved username validation
import asyncio
from database import check_credentials, create_user, user_exists
from server_utils import get_user_input, client, send_user_msg
from json_msg import CODES
from datetime import datetime
import hashlib

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
            password = await get_user_input("Create a password: ", reader, writer)
            
            # Create the user
            if await create_user(username, password):
                send_str = f"User {username} created successfully! Please login now."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                # Continue to login flow
            else:
                send_str = f"Username {username} already exists. Please try again."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                raise FailedAuth()
        
        # Login flow
        while attempts < 3:
            # Try getting username
            username = await get_user_input("Type in your username: ", reader, writer)
            print(f"Username: {username}")
            
            # First, check if the username exists
            if not await user_exists(username):
                send_str = f"Username '{username}' not found. Please try again."
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
                continue  # Skip password prompt and let them try username again
                
            # Username exists, so prompt for password
            password = await get_user_input("Type in your password: ", reader, writer)
            print(f"Received password")  # Don't print actual password
            
            # Attempt to authenticate
            if await check_credentials(username, password):
                send_str = f"Hello {username}!!! Log on Successful on {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}"
                await send_user_msg(send_str, CODES.AUTHENTICATED, writer)
                break
            else:
                send_str = f"Incorrect password for {username}. Attempt {attempts + 1}!"
                attempts += 1
                await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)

        # If credentials could not be authenticated, raise exception
        if attempts == 3:
            raise FailedAuth()

    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise FailedAuth()

    return client(reader, writer, username)