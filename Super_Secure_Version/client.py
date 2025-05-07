# client.py - Final clean version
import asyncio
from asyncio.exceptions import IncompleteReadError
import json
import os
import getpass
import sys
import signal
import traceback

from json_msg import CODES, msg

HOST_IP = '127.0.0.1'
PORT = 8888

BUFFER = 1024  # Increased buffer size
MAX_WAIT_TIME = 60

"""
Reads a json message from the server
"""
async def read_messages(reader: asyncio.StreamReader) -> msg:
    default_message = msg(CODES.SUCCESS.value, "No Message")

    try:
        # Attempts to read data from server
        data = await reader.read(BUFFER)

        # If nothing is data, raise exception
        if not data:
            raise asyncio.exceptions.IncompleteReadError(bytes(0), BUFFER)
        
        # Decode data
        data_str = data.decode()
        
        try:
            # Try to parse the JSON
            json_data = json.loads(data_str)
            json_message = msg.from_json_dict(json_data)
            return json_message
        except json.JSONDecodeError:
            # Handle non-JSON data
            print(f"Server: {data_str}")
            return default_message

    except asyncio.exceptions.IncompleteReadError:
        print("Connection to server lost")
        raise ConnectionError()
    except Exception as e:
        print(f"Error reading message: {str(e)}")
        return default_message

"""
Send a message to the server
"""
async def write_messages(writer, message) -> str:
    writer.write(f"{message}".encode())
    await writer.drain()
    return message

async def preauth(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    username = ""
    
    while True:
        # Get message from server
        await asyncio.sleep(0.5)
        message = await read_messages(reader)
        
        # Print message
        print(f"{message.msg}")

        # Write back to server if required
        if message.code == CODES.WRITE_BACK.value:
            # If asking about login/register
            if "login or register" in message.msg.lower():
                choice = input("> ")
                await write_messages(writer, choice)
            # If requesting username, save it
            elif "username" in message.msg.lower():
                username = input("> ")
                await write_messages(writer, username)
            # Handle password input
            elif "password" in message.msg.lower():
                password = getpass.getpass("> ")
                await write_messages(writer, password)
            else:
                user_input = input("> ")
                await write_messages(writer, user_input)
        elif message.code == CODES.EXIT.value:
            raise asyncio.CancelledError
        elif message.code == CODES.AUTHENTICATED.value:
            break
    
    return username

async def postauth(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, username: str):
    print(f"Authenticated as {username}")
    print("Type HELP for available commands")
    
    # Create event for clean shutdown
    shutdown_event = asyncio.Event()
    
    # Create tasks for reading and writing
    async def reader_task():
        try:
            while not shutdown_event.is_set():
                try:
                    # Read messages from server
                    data = await reader.read(BUFFER)
                    if not data:
                        print("Server connection closed")
                        shutdown_event.set()
                        break
                    
                    # Decode and process the data
                    data_str = data.decode()
                    
                    # Try to parse as JSON
                    try:
                        json_data = json.loads(data_str)
                        if 'msg' in json_data:
                            message = json_data['msg']
                            print(f"\n{message}")
                        else:
                            print(f"\nServer: {data_str}")
                    except json.JSONDecodeError:
                        # If not JSON, print raw message
                        print(f"\nServer: {data_str}")
                    
                    print("> ", end="", flush=True)
                    
                    # Small delay between reads
                    await asyncio.sleep(0.1)
                        
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Error processing server message: {str(e)}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\nReader error: {str(e)}")
            shutdown_event.set()
    
    async def writer_task():
        try:
            while not shutdown_event.is_set():
                try:
                    message = input("> ")
                    
                    if not message.strip():  # Skip empty messages
                        continue
                    
                    await write_messages(writer, message)
                    
                    # Small delay to allow response to arrive
                    await asyncio.sleep(0.2)
                    
                    # Handle exit command
                    if message.upper() == "EXIT":
                        print("Exiting chat...")
                        shutdown_event.set()
                        break
                except EOFError:
                    # End of input (Ctrl+D)
                    print("\nInput closed")
                    shutdown_event.set()
                    break
                        
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            print("\nExiting...")
            shutdown_event.set()
        except Exception as e:
            print(f"\nWriter error: {str(e)}")
            shutdown_event.set()
    
    # Run both tasks
    reader_future = asyncio.create_task(reader_task())
    writer_future = asyncio.create_task(writer_task())
    
    # Wait for shutdown event
    await shutdown_event.wait()
    
    # Cancel both tasks
    reader_future.cancel()
    writer_future.cancel()
    
    # Wait for tasks to complete
    await asyncio.gather(reader_future, writer_future, return_exceptions=True)

async def main():
    try:
        # Connect to server
        reader, writer = await asyncio.open_connection(HOST_IP, PORT)
        print(f"Connected to {writer.get_extra_info('peername')}")
        
        # Run Client
        try:
            # Pre authentication loop - returns username if successful
            username = await preauth(reader, writer)
            
            # Post authentication loop
            await postauth(reader, writer, username)

        except ConnectionError as e:
            print(f"Connection error: {e}")
        except asyncio.CancelledError:
            print("Disconnecting from server...")
        finally:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            print("Disconnected")
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print(f"Make sure server is running at {HOST_IP}:{PORT}")

def handle_signal(signal, frame):
    print("\nProgram terminated")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_signal)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram Ended")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()