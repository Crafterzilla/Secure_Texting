import asyncio
import server_utils as utils
import server_auth
from server_interclient_comms import client_to_client_comms
import database

# Default Port and IP for server. Server runs on localhost.
# Please open firewall at Port 8888 for server to accept connections
PORT = 8888
IP = '127.0.0.1'

# Global set of clients for server to keep track of
clients: dict[str, utils.client] = dict()

"""
Close Connection to Client
"""
async def close_connection(writer: asyncio.StreamWriter) -> None:
    # Close connection
    print(f"Closing connection with {writer.get_extra_info('peername')}")
    await utils.send_user_msg("Server is closing connection with you", utils.CODES.EXIT, writer)
    writer.close()
    await writer.wait_closed()

"""
This Function will handle the client at a high level. By that, it will first authenticate the user.
After authentication is done, it will allow the user to send messages to OTHER ACTIVE USERS.
"""
async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # Print out to the logs client connection
    addr = writer.get_extra_info('peername')
    print(f"New connection from {addr}")
    
    # For use when closing connection
    client_username = ""

    # Attempt to Authentiate User. If success add to client list
    try:
        client = await server_auth.authenticate_user(reader, writer)
        client_username = client.username
        
        # Wait a sec so client can change from sync to async execution
        await asyncio.sleep(1)
        
        # Check if client already exists
        if client.username not in clients:
            clients[client.username] = client
            await client_to_client_comms(client, clients)
        else:
            send_str = f"User {client.username} already logged in. Closing connection"
            await utils.send_user_msg(send_str, utils.CODES.NO_WRITE_BACK, writer)

        # Write data to client
        await close_connection(writer)

    except server_auth.FailedAuth:
        # Tell user to fuck off since he failed 
        await utils.send_user_msg("3 Failed Attemps!!! Closing connection", utils.CODES.NO_WRITE_BACK, writer)
        await close_connection(writer)
        return
    except asyncio.IncompleteReadError:
        # Close Connection due to invalid read
        mesg = f"Incomplete Read Error: likely client disconnected suddenly ({addr})"
        await utils.send_user_msg(mesg, utils.CODES.NO_WRITE_BACK, writer)
        await close_connection(writer)
        return
    except asyncio.TimeoutError:
        # Close Connection due to timeout error
        mesg = f"Timeout error: No data received by client ({addr})"
        await utils.send_user_msg(mesg, utils.CODES.NO_WRITE_BACK, writer)
        await close_connection(writer)
        return
    except ConnectionResetError as e:
        print(f"Connection was reset by {addr}")
        return
    except ConnectionError as e:
        print(f"{addr} | Connection error: {e}")
        return
    finally:
        # Remove client from dict
        clients.pop(client_username, None)


"""
Overall very high level function. Starts the server and then runs handle_client for each
connection. The rest of the implementation is dealt with later.
"""
async def init_server():
    # Init Database - use the sync version for simplicity
    await database.init_database()
    print("Database init at ./chat.db")

    # Start Server coroutine
    server = await asyncio.start_server(handle_client, IP, PORT)
    
    # Print stuff to console
    print(f"Starting Server on {IP}:{PORT}")
    print(f"To close server, type Ctrl+C")

    # Start serving
    try:
        await server.start_serving()  
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        print("Shutting down gracefully...")
        server.close_clients()
        server.close()
        await server.wait_closed()
        print("Server stopped.")


def main():
    asyncio.run(init_server())

if __name__ == "__main__":
    main()