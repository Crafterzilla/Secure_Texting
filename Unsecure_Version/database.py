import sqlite3
import asyncio

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

async def check_credentials(username: str, password: str):
    """
    Check if the given username and password exist in the database.
    Returns True if the credentials are valid, False otherwise.
    """

    # Connect to the SQLite database
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    try:
        # Execute the query to check for the username/password combination
        cursor.execute("""
            SELECT * FROM members
            WHERE username = ? AND password = ?
        """, (username, password))

        # Fetch the result
        result = cursor.fetchone()

        # If a row is returned, the credentials are valid
        return result is not None

    finally:
        # Close the connection
        conn.close()
