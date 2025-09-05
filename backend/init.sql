-- Initialize the customer_health database with required tables
-- This script runs automatically when the PostgreSQL container starts

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    segment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_metadata JSONB
);

-- Seed 10 customers
INSERT INTO customers (name, segment) VALUES
    ('Acme Corp', 'enterprise'),
    ('TechStart Inc', 'startup'), 
    ('Global Solutions', 'enterprise'),
    ('Local Business', 'smb'),
    ('Innovation Labs', 'startup'),
    ('Corporate Giant', 'enterprise'),
    ('Small Shop', 'smb'),
    ('Mid-size Co', 'mid-market'),
    ('Digital Agency', 'smb'),
    ('Enterprise Plus', 'enterprise')
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_events_customer_id ON events(customer_id);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
