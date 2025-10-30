-- Create the users table
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY, -- Unique identifier for each user
    email VARCHAR(255) NOT NULL UNIQUE,           -- User's email address
    password_hash TEXT NOT NULL,                  -- Hashed password for security
    full_name VARCHAR(255),                       -- Optional full name of the user
    created_at TIMESTAMP DEFAULT NOW(),           -- Timestamp of account creation
    updated_at TIMESTAMP DEFAULT NOW()            -- Timestamp of last update
);

-- Create a trigger to update the updated_at field on modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create an index on the email column for faster lookups
CREATE INDEX idx_users_email ON users(email);
