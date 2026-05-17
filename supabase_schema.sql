-- Supabase (PostgreSQL) Table Definitions
-- Execute this in Supabase SQL Editor to create tables

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    hashed_password TEXT,
    full_name TEXT,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    provider TEXT,
    provider_id TEXT,
    points NUMERIC(10,2) DEFAULT 1000.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quantity NUMERIC(10,2) NOT NULL,
    price NUMERIC(10,4) NOT NULL,
    total_price NUMERIC(10,2),
    fee NUMERIC(10,2),
    type TEXT NOT NULL CHECK (type IN ('buy', 'sell')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);

-- Enable Row Level Security (optional, recommended)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Example RLS policy for users (only allow users to see their own data)
-- CREATE POLICY "Users can view their own data"
--     ON users FOR SELECT
--     USING (auth.uid()::text = id::text);
