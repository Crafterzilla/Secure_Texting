import asyncio
from server_utils import get_user_input, client, send_user_msg, BUFFER, MAX_WAIT_TIME
from json_msg import CODES
from enum import Enum
from queue import LifoQueue
from datetime import datetime

# Valid chars only ascii chars from A to Z, a to z, 0 to 9, space ' ', and quotaions "
valid_chars = {chr(i) for i in range(65, 91)} | {chr(j) for j in range(97, 123)}
valid_chars |= {' ', '"'} | {chr(i) for i in range(48, 58)}
valid_message_chars = valid_chars |  {'.', '!', "'", "?", ","}

class CLIENT_CMDS(Enum):
    SEND = "SEND"
    TO = "TO"
    EXIT = "EXIT"
    GET_USER = "GETUSERS"
    HELP = "HELP"

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
            user_args = godly_parser(user_cmd.decode().strip())
            

            # Ensure list has 1 arg or more
            if len(user_args) == 0:
                await send_user_msg(f"No cmd sent. Invalid Input!", CODES.ERROR, client.writer)
                continue
           
            print(user_args)

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
                pass
            elif arg == CLIENT_CMDS.HELP.value:
                pass
            else:
                await send_user_msg(f"CMD ({arg}) is invalid!", CODES.ERROR, client.writer)


        except ValueError:
            await send_user_msg("Message contains invalid chars!", CODES.ERROR, client.writer)


async def check_send(user_args: list[str], client: client, clients: dict[str, client]):
    # Must contain 4 args
    if len(user_args) != 4:
        await send_user_msg(f"Your cmd has too many or too few args (len: {len(user_args)})", CODES.ERROR, client.writer)
        return
    
    # If cmd is "SEND ... ... ..."
    if user_args[0].upper() == CLIENT_CMDS.SEND.value and user_args[2].upper() == CLIENT_CMDS.TO.value:
        user_to_recieve_msg = user_args[3]
        if user_to_recieve_msg not in clients:
            await send_user_msg(f"User ({user_to_recieve_msg} does not exist or is inactive)", CODES.ERROR, client.writer)
        else:
            send_msg = f"[{datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}] {client.username}: {user_args[1]}"

            # SEND THE MSG TO USER HOORAYYY!!!
            await send_user_msg(send_msg, CODES.SUCCESS, clients[user_to_recieve_msg].writer)
    else:
        await send_user_msg(f"Third arg must be TO", CODES.ERROR, client.writer)
        return

"""
Parse input and give it out as a list of strings
"""
def godly_parser(cmd: str) -> list[str]:
    print(cmd)
    # Stack to check if quotations are closed
    stack = LifoQueue()
    str_list = []
    
    tmp_str = ""
    for char in cmd:
        # If char is invalid, raise an exception to be handled later
        if char not in valid_chars and stack.empty():
            raise ValueError
        elif char not in valid_message_chars and not stack.empty():
            raise ValueError
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
        raise ValueError

    str_list.append(tmp_str)
    return str_list


if __name__ == "__main__":
    print(godly_parser('SEND "HELLO THEREsdfa asdfaf 123!!" TO JESSICA'))
    print()
