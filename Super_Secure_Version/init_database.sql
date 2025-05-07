-- Add to init_database.sql
CREATE TABLE IF NOT EXISTS public_keys (
    username TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES members(username)
);