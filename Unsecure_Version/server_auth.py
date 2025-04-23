# Purpose:
# Take client input and attempt and see if user is valid and 
# validate the user authenticate attempt. If failure, after
# three attempts, kill the connection

import asyncio
from database import check_credentials
from server_utils import get_user_input, client, send_user_msg
from json_msg import CODES
from datetime import datetime

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

    # Authenticate User
    # Get username and password
    while attempts < 3:
        # Try getting username
        username = await get_user_input("Type in your username: ", reader, writer)
        print(f"Username: {username}")
            
        # Try getting password (which is now pre-hashed by client)
        hashed_password = await get_user_input("Type in your password: ", reader, writer)
        print(f"Received hashed password") # Don't print actual hash
        
        # Attempt to authenticate. 
        # Since password already hashed by client, pass directly to check_credentials
        if await check_credentials(username, hashed_password):
            send_str = f"Hello {username}!!! Log on Successful on {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}"
            await send_user_msg(send_str, CODES.AUTHENTICATED, writer)
            break
        else:
            send_str = f"Invalid credentials. Attempt {attempts + 1}!"
            attempts += 1
        
        # Send msg to user about authentication attempt
        await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)

    # If credentials could not be authenticated, raise exception
    if attempts == 3:
        raise FailedAuth()

    return client(reader, writer, username)