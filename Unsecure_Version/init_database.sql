BEGIN;

-- Create the members table
CREATE TABLE IF NOT EXISTS members (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
);

-- Insert sample data (optional, can be done in reset_database.py)
-- Will use hashed passwords here

COMMIT;