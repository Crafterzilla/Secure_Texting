import asyncio
import json
from json_msg import CODES, msg

BUFFER = 256
MAX_WAIT_TIME = 60

"""
Reads a json message from the server with a limit of 256
Once read, it returns it as a string to user
"""
async def read_messages(reader: asyncio.StreamReader) -> msg:
    json_message = msg(CODES.EXIT.value, "No Message")

    try:
        # Attemtps to read data from server
        data = await reader.read(BUFFER)

        # If nothing is data, raise exception
        if not data:
            raise asyncio.exceptions.IncompleteReadError(bytes(0), 256)
        
        # Decode data
        data_str = data.decode()
        
        print(data)
        # Turn data into dict then to two strs
        json_message = json.loads(data_str)
        json_message = msg.from_json_dict(json_message)


    except asyncio.exceptions.IncompleteReadError:
        print("Server Sent Incomplete Data\n")
        raise ConnectionError()

    except json.JSONDecodeError:
        print("Error when attempting to decode json")
        print("Likey an issue with your network or the server")
    
    # Return String without newline
    return json_message

"""
Send a message to the server. No need for validation here
as the server with validate rather than the client
"""
async def write_messages(writer):
    message = input("> ")
    writer.write(f"{message}".encode())
    await writer.drain()

async def preauth(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    while True:
        # Get message from server. Wait a sec before getting new message
        await asyncio.sleep(0.5)
        message = await read_messages(reader)
        
        # Print message
        print(f"{message.msg}")

        # Write back to server if nothing else requested
        if message.code == CODES.WRITE_BACK.value:
            await write_messages(writer)
        elif message.code == CODES.EXIT.value:
            raise asyncio.CancelledError
        elif message.code == CODES.AUTHENTICATED.value:
            break


async def main():
    # Open and connect to server. Get back reader and writer
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    print(f"Connected to {writer.get_extra_info('peername')}")
    

    # Run Client indefendiently. If it received something from the server,
    # by default send back something. However, it a CODE is sent from the
    # server to the client, skip the send back, and handle the code
    try:
        # Pre authentication loop
        await preauth(reader, writer)
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except asyncio.CancelledError:
        print("Disconnecting from server...")
        writer.close()
        await writer.wait_closed()
        print("Disconnected")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program Ended")
