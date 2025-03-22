import asyncio
import sqlite3
import server_utils as utils
import server_auth
import signal

# Default Port and IP for server. Server runs on localhost.
# Please open firewall at Port 8888 for server to accept connections
PORT = 8888
IP = '127.0.0.1'

# Global set of clients for server to keep track of
clients: set[utils.client] = set()

"""
Close Connection to Client
"""
async def close_connection(writer: asyncio.StreamWriter) -> None:
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

    # Attempt to Authentiate User. If success add to client list
    try:
        client = await server_auth.authenticate_user(reader, writer)
        clients.add(client)
    except server_auth.FailedAuth:
        # Tell user to fuck off since he failed 
        await utils.send_user_msg("3 Failed Attemps!!! Closing connection", utils.CODES.EXIT, writer)
        await close_connection(writer)
        return


    # Write data to client
    await close_connection(writer)


"""
Overall very high level function. Starts the server and then runs handle_client for each
connection. The rest of the implementation is dealt with later.
"""
async def init_server():
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
        server.close()
        await server.wait_closed()
        print("Server stopped.")


def main():
    asyncio.run(init_server())

if __name__ == "__main__":
    main()
