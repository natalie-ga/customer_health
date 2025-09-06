-- Initialize the customer_health database with required tables
-- This script runs automatically when the PostgreSQL container starts

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    segment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_metadata JSONB
);


-- Import CSV data directly
COPY customers FROM '/app/customers.csv' DELIMITER ',' CSV HEADER;
COPY events FROM '/app/events.csv' DELIMITER ',' CSV HEADER;




CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_events_customer_id_ts ON events(customer_id, ts); 
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_metadata_gin ON events USING GIN (event_metadata);