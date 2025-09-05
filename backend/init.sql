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

-- Seed 30 days of login events with varied patterns per customer
-- This creates realistic login frequency data for health scoring

-- Helper function to generate random login events
DO $$
DECLARE
    customer_record RECORD;
    login_date DATE;
    days_back INTEGER;
    login_probability FLOAT;
    customer_login_pattern FLOAT;
BEGIN
    -- Loop through each customer
    FOR customer_record IN SELECT id, name, segment FROM customers LOOP
        
        -- Set different login patterns based on segment
        CASE customer_record.segment
            WHEN 'enterprise' THEN customer_login_pattern := 0.8;  -- High activity
            WHEN 'mid-market' THEN customer_login_pattern := 0.6;  -- Medium activity  
            WHEN 'smb' THEN customer_login_pattern := 0.4;         -- Lower activity
            WHEN 'startup' THEN customer_login_pattern := 0.7;     -- Variable but high
            ELSE customer_login_pattern := 0.5;
        END CASE;
        
        -- Generate login events for past 30 days
        FOR days_back IN 0..29 LOOP
            login_date := CURRENT_DATE - days_back;
            
            -- Adjust probability based on day of week (weekends less likely)
            login_probability := customer_login_pattern;
            IF EXTRACT(DOW FROM login_date) IN (0, 6) THEN  -- Sunday = 0, Saturday = 6
                login_probability := login_probability * 0.3;  -- Much less likely on weekends
            END IF;
            
            -- Random chance of login based on customer pattern
            IF random() < login_probability THEN
                INSERT INTO events (customer_id, event_type, ts, event_metadata) VALUES (
                    customer_record.id,
                    'login',
                    login_date + INTERVAL '8 hours' + (random() * INTERVAL '12 hours'),  -- Random time during work day
                    jsonb_build_object(
                        'device', CASE WHEN random() < 0.7 THEN 'desktop' ELSE 'mobile' END,
                        'session_duration', (300 + random() * 3600)::integer,  -- 5 min to 1 hour
                        'ip_address', '192.168.' || (1 + random() * 254)::integer || '.' || (1 + random() * 254)::integer
                    )
                );
            END IF;
        END LOOP;
        
    END LOOP;
END $$;

-- Seed feature usage events for realistic feature adoption scoring
-- This creates varied feature usage patterns per customer for M4

DO $$
DECLARE
    customer_record RECORD;
    feature_list TEXT[] := ARRAY[
        'dashboard', 'reports', 'analytics', 'user_management', 'api_access',
        'integrations', 'notifications', 'export', 'billing', 'support_chat',
        'mobile_app', 'advanced_filters', 'custom_fields', 'automation', 'calendar'
    ];
    total_features INTEGER := 15;
    feature_name TEXT;
    days_back INTEGER;
    use_date DATE;
    features_to_use INTEGER;
    customer_adoption_rate FLOAT;
BEGIN
    -- Loop through each customer
    FOR customer_record IN SELECT id, name, segment FROM customers LOOP
        
        -- Set feature adoption rates based on customer segment
        CASE customer_record.segment
            WHEN 'enterprise' THEN 
                customer_adoption_rate := 0.7 + (random() * 0.2);  -- 70-90% features
                features_to_use := (customer_adoption_rate * total_features)::INTEGER;
            WHEN 'mid-market' THEN 
                customer_adoption_rate := 0.5 + (random() * 0.2);  -- 50-70% features
                features_to_use := (customer_adoption_rate * total_features)::INTEGER;
            WHEN 'startup' THEN 
                customer_adoption_rate := 0.4 + (random() * 0.3);  -- 40-70% features
                features_to_use := (customer_adoption_rate * total_features)::INTEGER;
            WHEN 'smb' THEN 
                customer_adoption_rate := 0.2 + (random() * 0.3);  -- 20-50% features
                features_to_use := (customer_adoption_rate * total_features)::INTEGER;
            ELSE 
                features_to_use := 5;  -- Default
        END CASE;
        
        -- Ensure at least 1 feature used
        IF features_to_use < 1 THEN
            features_to_use := 1;
        END IF;
        
        -- Generate feature usage events for past 30 days
        FOR i IN 1..features_to_use LOOP
            feature_name := feature_list[i];
            
            -- Generate multiple usage events for each feature over 30 days
            FOR days_back IN 0..29 LOOP
                use_date := CURRENT_DATE - days_back;
                
                -- Random chance of using this feature on this day (varies by feature popularity)
                IF random() < CASE 
                    WHEN feature_name IN ('dashboard', 'reports') THEN 0.8  -- Core features used often
                    WHEN feature_name IN ('analytics', 'notifications') THEN 0.6  -- Regular features
                    WHEN feature_name IN ('api_access', 'integrations') THEN 0.3  -- Advanced features
                    ELSE 0.4  -- Other features
                END THEN
                    INSERT INTO events (customer_id, event_type, ts, event_metadata) VALUES (
                        customer_record.id,
                        'feature_use',
                        use_date + INTERVAL '9 hours' + (random() * INTERVAL '10 hours'),  -- Random time during work day
                        jsonb_build_object(
                            'feature', feature_name,
                            'duration_seconds', (60 + random() * 1800)::integer,  -- 1 min to 30 min
                            'user_agent', CASE WHEN random() < 0.8 THEN 'web' ELSE 'mobile' END,
                            'session_id', 'sess_' || generate_random_uuid()
                        )
                    );
                END IF;
            END LOOP;
        END LOOP;
        
    END LOOP;
END $$;

-- Create indexes for better performance (including the required M3 index)
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_events_customer_id_ts ON events(customer_id, ts);  -- M3 requirement
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_metadata_gin ON events USING GIN (event_metadata);
