import asyncio
from asyncio.exceptions import IncompleteReadError
import json
from json_msg import CODES, msg

HOST_IP = '127.0.0.1'
PORT = 8888

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
        
        # print(data)
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
async def write_messages(writer) -> str:
    message = input("> ")
    writer.write(f"{message}".encode())
    await writer.drain()
    return message

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


async def postauth(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    async def postauth_reader(reader: asyncio.StreamReader):
        while True:
            # Get message from server. Wait a sec before getting new message
            await asyncio.sleep(0.5)
            message = await read_messages(reader)
            
            # Print message
            print(f"{message.msg}", flush=True)
            print("> ", end="", flush=True)

            # Write back to server if nothing else requested
            if message.code == CODES.EXIT.value:
                break

    async def postauth_writer(writer: asyncio.StreamWriter):
        print("Console for Writing. Type HELP for available commands")

        message = ""
        while message != "EXIT":
            message = await asyncio.to_thread(input, "> ")
            writer.write(f"{message}".encode())
            await writer.drain()

    # Create tasks for the reader and writer
    reader_task = asyncio.create_task(postauth_reader(reader))
    writer_task = asyncio.create_task(postauth_writer(writer))

    # Wait for both tasks to complete
    await asyncio.wait([reader_task, writer_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel the other task if one completes
    if not reader_task.done():
        reader_task.cancel()
    if not writer_task.done():
        writer_task.cancel()

    # Wait for tasks to be cancelled
    await asyncio.gather(reader_task, writer_task, return_exceptions=True)

    print("Post-auth session ended.")


async def main():
    # Open and connect to server. Get back reader and writer
    reader, writer = await asyncio.open_connection(HOST_IP, PORT)
    print(f"Connected to {writer.get_extra_info('peername')}")
    

    # Run Client indefendiently. If it received something from the server,
    # by default send back something. However, it a CODE is sent from the
    # server to the client, skip the send back, and handle the code
    try:
        # Pre authentication loop
        await preauth(reader, writer)
        
        # Post authentication loop
        await postauth(reader, writer)    

        raise asyncio.CancelledError
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
