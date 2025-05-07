# server_interclient_comms.py - Updated for secure messaging
import asyncio
from server_utils import get_user_input, client, send_user_msg, BUFFER, MAX_WAIT_TIME
from json_msg import CODES
from enum import Enum
from queue import LifoQueue
from datetime import datetime
from database import get_user_data, get_public_key, store_public_key, get_user_salt

# Valid chars only ascii chars from A to Z, a to z, 0 to 9, space ' ', and quotaions "
valid_chars = {chr(i) for i in range(65, 91)} | {chr(j) for j in range(97, 123)}
valid_chars |= {' ', '"'} | {chr(i) for i in range(48, 58)}
valid_message_chars = valid_chars |  {'.', '!', "'", "?", ",", "{", "}", ":", "\"", "_", "-", "+", "=", "/", "\\", "*", "&", "^", "%", "$", "#", "@", "!", "~", "`", "|", ";", "<", ">", "[", "]", "(", ")"}

class CLIENT_CMDS(Enum):
    SEND = "SEND"
    TO = "TO"
    EXIT = "EXIT"
    GET_USER = "GETUSERS"
    HELP = "HELP"
    PUBKEY = "PUBKEY"     # For uploading public key
    GETKEY = "GETKEY"     # For getting public key
    GET_SALT = "GET_SALT"  # For getting salt during authentication

"""
Client can type any of these commands to the server to communicate directly with server
or to send message to another user on server. Once the CODES.AUTH is sent to client,
this will handle the client until the connection is terminated
"""
async def client_to_client_comms(client: client, clients: dict[str, client]):
    while True:
        try:
            # Await User Command and timeout if too long
            user_cmd = await asyncio.wait_for(client.reader.read(BUFFER), timeout=MAX_WAIT_TIME)

            # If user connection breaks or something
            if not user_cmd:  
                raise asyncio.IncompleteReadError(bytes(0), 256) 
            
            # Convert bytes into list[str] of args
            user_cmd_str = user_cmd.decode().strip()
            
            # Special handling for JSON messages (encrypted content)
            if user_cmd_str.startswith("SEND ") and "{" in user_cmd_str and "}" in user_cmd_str:
                # Find the "TO" part
                to_index = user_cmd_str.rfind(" TO ")
                if to_index > 0:
                    # Extract recipient
                    recipient = user_cmd_str[to_index + 4:]
                    # Extract the encrypted message (everything between SEND and TO)
                    encrypted_message = user_cmd_str[5:to_index]
                    # Create args list
                    user_args = ["SEND", encrypted_message, "TO", recipient]
                else:
                    user_args = godly_parser(user_cmd_str)
            else:
                user_args = godly_parser(user_cmd_str)
            
            # Ensure list has 1 arg or more
            if len(user_args) == 0:
                await send_user_msg(f"No cmd sent. Invalid Input!", CODES.ERROR, client.writer)
                continue
           
            print(f"Command from {client.username}: {user_args[0]}")

            # Check the first arg cmd
            arg = user_args[0].upper()
            
            if arg == CLIENT_CMDS.EXIT.value:
                break
            elif arg == CLIENT_CMDS.GET_USER.value:
                users = [client for client in clients] 
                await send_user_msg(f"Active Users: {users}", CODES.SUCCESS, client.writer)
            elif arg == CLIENT_CMDS.SEND.value:
                await check_send(user_args, client, clients)
            elif arg == CLIENT_CMDS.TO.value:
                await send_user_msg("Invalid command format. Use: SEND message TO username", CODES.ERROR, client.writer)
            elif arg == CLIENT_CMDS.HELP.value:
                help_msg = "Commands:\n- GETUSERS: List all active users\n- SEND message TO username: Send a message\n- PUBKEY key: Upload your public key\n- GETKEY username: Get a user's public key\n- HELP: Show this help message\n- EXIT: Disconnect from server"
                await send_user_msg(help_msg, CODES.SUCCESS, client.writer)
            elif arg == CLIENT_CMDS.PUBKEY.value:
                if len(user_args) > 1:
                    public_key = user_args[1]
                    if await store_public_key(client.username, public_key):
                        await send_user_msg("Public key stored", CODES.SUCCESS, client.writer)
                    else:
                        await send_user_msg("Failed to store public key", CODES.ERROR, client.writer)
                else:
                    await send_user_msg("PUBKEY command requires a key", CODES.ERROR, client.writer)
            elif arg == CLIENT_CMDS.GETKEY.value:
                if len(user_args) > 1:
                    target_username = user_args[1]
                    public_key = await get_public_key(target_username)
                    if public_key:
                        await send_user_msg(f"KEY {target_username} {public_key}", CODES.SUCCESS, client.writer)
                    else:
                        await send_user_msg(f"No public key found for {target_username}", CODES.ERROR, client.writer)
                else:
                    await send_user_msg("GETKEY command requires a username", CODES.ERROR, client.writer)
            elif arg == CLIENT_CMDS.GET_SALT.value:
                # Get user's salt for authentication
                salt = await get_user_salt(client.username)
                if salt:
                    await send_user_msg(salt, CODES.SALT, client.writer)
                else:
                    await send_user_msg("Error retrieving salt", CODES.ERROR, client.writer)
            else:
                await send_user_msg(f"Unknown command: {arg}. Type HELP for available commands.", CODES.ERROR, client.writer)
        except asyncio.IncompleteReadError:
            # Client disconnected
            print(f"Client {client.username} disconnected unexpectedly")
            break
        except asyncio.TimeoutError:
            # Timeout waiting for command
            await send_user_msg("Timeout waiting for command", CODES.ERROR, client.writer)
            continue
        except ValueError as e:
            await send_user_msg(f"Command error: {str(e)}", CODES.ERROR, client.writer)
        except Exception as e:
            print(f"Error handling command: {str(e)}")
            await send_user_msg(f"Server error processing command", CODES.ERROR, client.writer)
            continue

async def check_send(user_args: list[str], client: client, clients: dict[str, client]):
    # Must contain at least 4 args: SEND "message" TO username
    if len(user_args) < 4:
        await send_user_msg(f"Invalid command format. Use: SEND message TO username", CODES.ERROR, client.writer)
        return
    
    # If cmd is "SEND ... ... ..."
    if user_args[0].upper() == CLIENT_CMDS.SEND.value and user_args[2].upper() == CLIENT_CMDS.TO.value:
        user_to_receive_msg = user_args[3]
        if user_to_receive_msg not in clients:
            await send_user_msg(f"User ({user_to_receive_msg}) does not exist or is offline", CODES.ERROR, client.writer)
        else:
            timestamp = datetime.now().strftime('%m/%d/%Y, %H:%M:%S')
            
            # Process the message content
            message_content = user_args[1]
            
            # Always treat messages as potentially encrypted
            # Include metadata (timestamp and sender) but don't modify the content
            send_msg = f"[{timestamp}] {client.username}: {message_content}"
            
            # Send message to recipient
            await send_user_msg(send_msg, CODES.SUCCESS, clients[user_to_receive_msg].writer)
            # Confirm to sender
            await send_user_msg(f"Message sent to {user_to_receive_msg}", CODES.SUCCESS, client.writer)
    else:
        await send_user_msg(f"Invalid command format. Use: SEND message TO username", CODES.ERROR, client.writer)
        return

"""
Parse input and give it out as a list of strings
"""
def godly_parser(cmd: str) -> list[str]:
    # Stack to check if quotations are closed
    stack = LifoQueue()
    str_list = []
    
    # Special case: if the command contains JSON (for encrypted messages)
    if cmd.startswith("SEND ") and "{" in cmd and "}" in cmd:
        # Find the TO part
        to_index = cmd.rfind(" TO ")
        if to_index > 0:
            # Extract the message parts
            send_part = "SEND"
            encrypted_part = cmd[5:to_index].strip()
            to_part = "TO"
            recipient_part = cmd[to_index + 4:].strip()
            
            return [send_part, encrypted_part, to_part, recipient_part]
    
    # Regular parsing
    tmp_str = ""
    json_mode = False
    brace_count = 0
    
    for char in cmd:
        # If entering JSON mode
        if char == '{':
            if not json_mode and stack.empty():
                if tmp_str:
                    str_list.append(tmp_str)
                    tmp_str = ""
                json_mode = True
                brace_count = 1
                tmp_str += char
                continue
            elif json_mode:
                brace_count += 1
        
        # If exiting JSON mode
        elif char == '}' and json_mode:
            brace_count -= 1
            tmp_str += char
            if brace_count == 0:
                str_list.append(tmp_str)
                tmp_str = ""
                json_mode = False
                continue
        
        # If in JSON mode, accept all characters
        elif json_mode:
            tmp_str += char
            continue
        
        # If char is invalid outside of JSON, raise an exception
        elif char not in valid_chars and stack.empty():
            raise ValueError(f"Invalid character: '{char}'")
        elif char not in valid_message_chars and not stack.empty():
            raise ValueError(f"Invalid character in message: '{char}'")
        # If char space, skip
        elif char == ' ' and stack.empty():
            if tmp_str != "":
                str_list.append(tmp_str)
                tmp_str = ""
        elif char == '"':
            # If stack empty fill stack, else
            if stack.empty():
                stack.put(char)
            else:
                stack.get()
                str_list.append(tmp_str)
                tmp_str = ""
        else:
            tmp_str += char
    
    # If quotations are not closed, raise exception
    if not stack.empty():
        raise ValueError("Unclosed quotation mark")
    
    # If JSON is not closed, raise exception
    if json_mode:
        raise ValueError("Unclosed JSON object")

    if tmp_str:  # Add the last part if it exists
        str_list.append(tmp_str)
    
    return str_list