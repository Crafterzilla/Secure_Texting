# migration.py - Updated version for secure authentication
import sqlite3
import os
from hash_utils import hash_password, generate_salt

def reset_database():
    # Delete existing database 
    if os.path.exists('chat.db'):
        os.remove('chat.db')
    
    # Create new database
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    # Create table with salt column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,  -- renamed for clarity
        salt TEXT NOT NULL,           -- new field for storing the salt
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create table for public keys
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS public_keys (
        username TEXT PRIMARY KEY,
        public_key TEXT NOT NULL,
        key_creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES members(username)
    )
    ''')

    # Create table for auth challenges
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auth_challenges (
        username TEXT NOT NULL,
        challenge TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (username),
        FOREIGN KEY (username) REFERENCES members(username)
    )
    ''')

    
    # Add users with properly hashed passwords
    users = [
        ("Bobzilla", "123456"),
        ("OzTheWiz", "cool_password_123"),
        ("Jessica551", "qwerty")
    ]
    
    for username, plaintext_password in users:
        # Generate a unique salt for each user
        salt = generate_salt()
        
        # Hash the password with the salt
        hashed_password = hash_password(plaintext_password, salt)
        
        # Store username, hashed password, and salt
        cursor.execute(
            "INSERT INTO members (username, password, salt) VALUES (?, ?, ?)",
            (username, hashed_password, salt)
        )
    
    conn.commit()
    conn.close()
    print("Database has been reset with securely hashed passwords")

if __name__ == "__main__":
    reset_database()