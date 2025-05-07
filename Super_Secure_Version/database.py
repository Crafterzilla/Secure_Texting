# database.py - Simplified version
import sqlite3
import asyncio
import os
import hashlib

async def init_database():
    """Initialize the database and create necessary tables"""
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    
    # Create members table if it doesn't exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS members (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
    ''')
    
    # Create public_keys table if it doesn't exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS public_keys (
        username TEXT PRIMARY KEY,
        public_key TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES members(username)
    )
    ''')
    
    # Add some test users if the table is empty
    cur.execute("SELECT COUNT(*) FROM members")
    count = cur.fetchone()[0]
    
    if count == 0:
        # Add some default users
        users = [
            ("Bobzilla", hash_password("123456")),
            ("OzTheWiz", hash_password("cool_password_123")),
            ("Jessica551", hash_password("qwerty"))
        ]
        
        for username, password_hash in users:
            cur.execute(
                "INSERT INTO members (username, password) VALUES (?, ?)",
                (username, password_hash)
            )
    
    # Execute any additional SQL from file if it exists
    if os.path.exists("init_database.sql"):
        with open("init_database.sql") as file:
            sql_file = file.read()
        cur.executescript(sql_file)
    
    # Commit and close
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password):
    """Simple password hashing function"""
    return hashlib.sha256(password.encode()).hexdigest()

async def check_credentials(username: str, password: str):
    """
    Check if the given username and password are valid.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()

    try:
        # Get the stored password hash
        cursor.execute("SELECT password FROM members WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if not result:
            return False
        
        stored_hash = result[0]
        # Hash the provided password and compare
        password_hash = hash_password(password)
        
        return password_hash == stored_hash

    finally:
        # Close the connection
        conn.close()

async def create_user(username, password):
    """Create a new user with the given username and password"""
    # Check if username already exists
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT username FROM members WHERE username = ?", (username,))
        if cursor.fetchone():
            return False  # Username already exists
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Insert the new user
        cursor.execute(
            "INSERT INTO members (username, password) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()

async def store_public_key(username, public_key_pem):
    """Store a user's public key in the database."""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO public_keys (username, public_key)
            VALUES (?, ?)
        """, (username, public_key_pem))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error storing public key: {e}")
        return False
    finally:
        conn.close()

async def get_public_key(username):
    """Retrieve a user's public key from the database."""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT public_key FROM public_keys
            WHERE username = ?
        """, (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error retrieving public key: {e}")
        return None
    finally:
        conn.close()
        

async def user_exists(username):
    """Check if a username exists in the database"""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT username FROM members WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()