import sqlite3
import asyncio

# We remove the import of hash_password since passwords will already be hashed by the client
# from hash_utils import hash_password

async def init_database():
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    
    with open("init_database.sql") as file:
         sql_file = file.read()

    # Execute sql script
    cur.executescript(sql_file)
    
    # Close data connection
    cur.close()
    conn.close()

async def check_credentials(username: str, hashed_password: str):
    """
    Check if the given username and password exist in the database.
    Password is expected to be already hashed by the client.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    try:
        # Execute the query to check for the username/hashed_password combination
        cursor.execute("""
            SELECT * FROM members
            WHERE username = ? AND password = ?
        """, (username, hashed_password))

        # Fetch the result
        result = cursor.fetchone()

        # If a row is returned, the credentials are valid
        return result is not None

    finally:
        # Close the connection
        conn.close()