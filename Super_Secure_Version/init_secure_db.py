# init_secure_db.py - Script to initialize the secure chat database
import asyncio
import os
from database import init_database, migrate_to_salted_passwords

async def setup_database():
    """
    Initialize the database with proper schema and migrate if needed.
    
    This script can be run to:
    1. Create a fresh database if none exists
    2. Migrate existing database to support secure authentication
    """
    # Check if database already exists
    db_exists = os.path.exists("chat.db")
    
    if db_exists:
        print("Existing database found.")
        choice = input("Do you want to (1) upgrade the existing database or (2) reset to a clean state? [1/2]: ")
        
        if choice == "2":
            confirm = input("WARNING: This will delete all existing data. Are you sure? [y/N]: ")
            if confirm.lower() == "y":
                await init_database(reset=True)
                print("Database has been reset to a clean state.")
            else:
                print("Reset cancelled. Proceeding with upgrade...")
                await init_database(reset=False)
                
                # Migrate existing users to use salted passwords
                migrated = await migrate_to_salted_passwords()
                print(f"Migrated {migrated} existing user(s) to use salted passwords.")
        else:
            # Default to upgrade
            await init_database(reset=False)
            
            # Migrate existing users to use salted passwords
            migrated = await migrate_to_salted_passwords()
            print(f"Migrated {migrated} existing user(s) to use salted passwords.")
    else:
        print("No existing database found. Creating new database...")
        await init_database(reset=False)
        print("Database created successfully with default users.")
    
    print("Database setup complete. Ready to start the server.")

if __name__ == "__main__":
    asyncio.run(setup_database())