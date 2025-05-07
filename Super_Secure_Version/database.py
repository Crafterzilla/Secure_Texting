# database.py - Simplified and cleaned up
import sqlite3
import asyncio
import os
import hashlib

async def init_database():
    """Initialize the database and create necessary tables"""
    # Remove existing database if it exists
    if os.path.exists("chat.db"):
        os.remove("chat.db")
    
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    
    # Create members table if it doesn't exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS members (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create public_keys table if it doesn't exist
    cur.execute('''
    CREATE TABLE IF NOT EXISTS public_keys (
        username TEXT PRIMARY KEY,
        public_key TEXT NOT NULL,
        key_creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES members(username)
    )
    ''')
    
    # Create table for auth challenges
    cur.execute('''
    CREATE TABLE IF NOT EXISTS auth_challenges (
        username TEXT NOT NULL,
        challenge TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (username),
        FOREIGN KEY (username) REFERENCES members(username)
    )
    ''')
    
    # Commit and close
    conn.commit()
    cur.close()
    conn.close()
    
    print("Database initialized successfully.")

async def create_user(username, password_hash, salt):
    """Create a new user with the given username and password_hash"""
    # Check if username already exists
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT username FROM members WHERE username = ?", (username,))
        if cursor.fetchone():
            return False  # Username already exists
        
        # Insert the new user
        cursor.execute(
            "INSERT INTO members (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
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

async def get_user_data(username):
    """Get user data including password hash and salt"""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT password_hash, salt FROM members WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            return {"password_hash": result[0], "salt": result[1]}
        return None
    except Exception as e:
        print(f"Error retrieving user data: {e}")
        return None
    finally:
        conn.close()

async def get_user_salt(username):
    """Get a user's salt"""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT salt FROM members WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error retrieving salt: {e}")
        return None
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

async def store_challenge(username, challenge):
    """Store an authentication challenge for a user"""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO auth_challenges (username, challenge)
            VALUES (?, ?)
        """, (username, challenge))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error storing challenge: {e}")
        return False
    finally:
        conn.close()

async def get_challenge(username):
    """Get stored authentication challenge for a user"""
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT challenge FROM auth_challenges
            WHERE username = ?
        """, (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error retrieving challenge: {e}")
        return None
    finally:
        conn.close()