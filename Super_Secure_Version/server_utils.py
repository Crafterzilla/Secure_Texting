# server_utils.py - Updated for secure messaging
import asyncio
from json_msg import CODES, msg

BUFFER = 2048  # Increased buffer size
MAX_WAIT_TIME = 240

"""
Representation of a User. Easier to pass around for args rather than all three things
"""
class client:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, username: str) -> None:
        self.reader = reader
        self.writer = writer
        self.username = username
        self.message_history = None
    def __str__(self) -> str:
        return self.username

"""
Send Client a json object prompt and receive in the end a beautiful string
"""
async def get_user_input(prompt: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> str:
    # Function to get and handle user input
    while True:
        try:
            # Send user prompt requesting user input with CODE
            await send_user_msg(prompt, CODES.WRITE_BACK, writer)

            # Read User Response
            data = await asyncio.wait_for(reader.read(BUFFER), timeout=MAX_WAIT_TIME)

            # If nothing is data, raise exception
            if not data:
               raise asyncio.exceptions.IncompleteReadError(bytes(0), BUFFER) 
            
           # If success break from the loop
            break
        except asyncio.exceptions.IncompleteReadError:
            print("Client Sent Incomplete Data\n")
            raise  # Re-raise to allow caller to handle

    # Return the decoded data str
    return data.decode().strip()

"""
Send the user a message with a code prompting the user what to do.
Ensures proper JSON formatting of messages.
"""
async def send_user_msg(prompt: str, code: CODES, writer: asyncio.StreamWriter) -> None:
    try:
        # Create a properly formatted JSON message
        json_to_send = msg(code.value, prompt)
        # Convert to JSON string and encode
        json_str = json_to_send.to_json_str()
        # Send the message
        writer.write(json_str.encode())
        await writer.drain()
        # Small delay to ensure message is sent completely
        await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        # Don't raise so server can continue operating