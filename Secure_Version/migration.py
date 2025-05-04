import sqlite3
import os
from hash_utils import hash_password  # Using the original hash function

def reset_database():
    # Delete existing database 
    if os.path.exists('chat.db'):
        os.remove('chat.db')
    
    # Create new database
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    # Create table - keep original schema for now
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
    ''')
    
    # Add users with hashed passwords
    users = [
        ("Bobzilla", hash_password("123456")),
        ("OzTheWiz", hash_password("cool_password_123")),
        ("Jessica551", hash_password("qwerty"))
    ]
    
    for username, hashed_password in users:
        cursor.execute(
            "INSERT INTO members (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
    
    conn.commit()
    conn.close()
    print("Database has been reset with hashed passwords (no salt)")

if __name__ == "__main__":
    reset_database()