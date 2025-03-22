# Purpose:
# Take client input and attempt and see if user is valid and 
# validate the user authenticate attmept. If failure, after
# three attempts, kill the connection

import asyncio
from server_utils import get_user_input, client, send_user_msg
from json_msg import CODES, msg


class FailedAuth(Exception):
    pass
"""
Function to authenticate credentials
TODO: Make it read from database instead of test
"""
def authenticate(username: str, password: str) -> bool:
    # For debug purposes
    test_user = "user"
    test_password = "password"

    return (username == test_user and password == test_password)

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
            
        # Try getting password
        password = await get_user_input("Type in your password: ", reader, writer)
        print(f"Password: {password}")
        
        # Attempt to authenticate. If successsful, store msg in send_str
        if authenticate(username, password):
            send_str = f"Hello {username}!!"
            break
        else:
            send_str = f"Invalid credentials. Attempt {attempts}!"
            attempts += 1
        
        # Send msg to user about authenticaton attempt
        await send_user_msg(send_str, CODES.NO_WRITE_BACK, writer)
        await asyncio.sleep(1)

    # If credentials could not be authenticated, raise exception
    if attempts == 3:
        raise FailedAuth()

    return client(reader, writer, username)
