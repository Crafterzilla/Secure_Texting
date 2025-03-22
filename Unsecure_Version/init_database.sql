BEGIN;

-- Create the members table
CREATE TABLE IF NOT EXISTS members (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
);


-- Insert records into the members table (only if they don't already exist)
INSERT OR IGNORE INTO members (username, password) VALUES ("Bobzilla", "123456");
INSERT OR IGNORE INTO members (username, password) VALUES ("OzTheWiz", "cool_password_123");
INSERT OR IGNORE INTO members (username, password) VALUES ("Jessica551", "qwerty");

COMMIT;
