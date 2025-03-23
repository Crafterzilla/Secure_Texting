import asyncio
from json_msg import CODES, msg

BUFFER = 256
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
Send Client a json object prompt and receive in the end a beaultuiful string
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
               raise asyncio.exceptions.IncompleteReadError(bytes(0), 256) 
            
           # If success break from the loop
            break
        except asyncio.exceptions.IncompleteReadError:
            print("Client Sent Incomplete Data\n")

    # Return the decoded data str
    return data.decode().strip()

"""
Send the user a message with a code prompting the user what to do.
"""
async def send_user_msg(prompt: str, code: CODES, writer: asyncio.StreamWriter) -> None:
    json_to_send = msg(code.value, prompt)
    writer.write(json_to_send.to_json_str().encode())
    await writer.drain()
    await asyncio.sleep(0.5)
