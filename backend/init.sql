-- Initialize the customer_health database with required tables
-- This script runs automatically when the PostgreSQL container starts

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    segment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_metadata JSONB
);

-- Seed 10 customers with 8-character UUIDs
INSERT INTO customers (id, name, segment) VALUES
    ('a1b2c3d4', 'Acme Corp', 'enterprise'),
    ('e5f6g7h8', 'TechStart Inc', 'startup'), 
    ('i9j0k1l2', 'Global Solutions', 'enterprise'),
    ('m3n4o5p6', 'Local Business', 'smb'),
    ('q7r8s9t0', 'Innovation Labs', 'startup'),
    ('u1v2w3x4', 'Corporate Giant', 'enterprise'),
    ('y5z6a7b8', 'Small Shop', 'smb'),
    ('c9d0e1f2', 'Mid-size Co', 'mid-market'),
    ('g3h4i5j6', 'Digital Agency', 'smb'),
    ('k7l8m9n0', 'Enterprise Plus', 'enterprise')
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

-- Seed support ticket events for realistic support load scoring
-- This creates varied support patterns per customer for M5

DO $$
DECLARE
    customer_record RECORD;
    ticket_severity TEXT[] := ARRAY['low', 'medium', 'high', 'critical'];
    ticket_categories TEXT[] := ARRAY['technical', 'billing', 'feature_request', 'bug', 'integration', 'training'];
    days_back INTEGER;
    ticket_date DATE;
    ticket_count_per_month INTEGER;
    monthly_ticket_rate FLOAT;
    severity TEXT;
    category TEXT;
    ticket_open_time TIMESTAMP;
    ticket_close_time TIMESTAMP;
    resolution_hours INTEGER;
    should_close_ticket BOOLEAN;
BEGIN
    -- Loop through each customer
    FOR customer_record IN SELECT id, name, segment FROM customers LOOP
        
        -- Set support ticket patterns based on customer segment and health
        CASE customer_record.segment
            WHEN 'enterprise' THEN 
                -- Enterprise: More tickets but better support, mix of severities
                monthly_ticket_rate := 0.3 + (random() * 0.4);  -- 0.3-0.7 tickets per day on average
            WHEN 'mid-market' THEN 
                -- Mid-market: Moderate ticket volume
                monthly_ticket_rate := 0.2 + (random() * 0.3);  -- 0.2-0.5 tickets per day
            WHEN 'startup' THEN 
                -- Startup: Variable, sometimes high due to rapid development
                monthly_ticket_rate := 0.1 + (random() * 0.5);  -- 0.1-0.6 tickets per day
            WHEN 'smb' THEN 
                -- SMB: Lower ticket volume but might indicate issues when they do occur
                monthly_ticket_rate := 0.1 + (random() * 0.2);  -- 0.1-0.3 tickets per day
            ELSE 
                monthly_ticket_rate := 0.2;
        END CASE;
        
        -- Generate support ticket events for past 30 days
        FOR days_back IN 0..29 LOOP
            ticket_date := CURRENT_DATE - days_back;
            
            -- Random chance of creating tickets on this day
            IF random() < monthly_ticket_rate THEN
                
                -- Determine ticket severity (weighted toward lower severity)
                severity := CASE 
                    WHEN random() < 0.5 THEN 'low'
                    WHEN random() < 0.8 THEN 'medium'  
                    WHEN random() < 0.95 THEN 'high'
                    ELSE 'critical'
                END;
                
                -- Random category
                category := ticket_categories[1 + (random() * array_length(ticket_categories, 1))::integer];
                
                -- Create ticket open event
                ticket_open_time := ticket_date + INTERVAL '8 hours' + (random() * INTERVAL '12 hours');
                
                INSERT INTO events (customer_id, event_type, ts, event_metadata) VALUES (
                    customer_record.id,
                    'ticket_open',
                    ticket_open_time,
                    jsonb_build_object(
                        'severity', severity,
                        'category', category,
                        'ticket_id', 'TIX_' || generate_random_uuid(),
                        'source', CASE WHEN random() < 0.7 THEN 'web' WHEN random() < 0.9 THEN 'email' ELSE 'phone' END,
                        'assignee', 'support_agent_' || (1 + random() * 10)::integer
                    )
                );
                
                -- Determine if ticket should be closed (most tickets get closed)
                should_close_ticket := CASE
                    WHEN severity = 'critical' THEN random() < 0.9  -- 90% of critical tickets closed quickly
                    WHEN severity = 'high' THEN random() < 0.85     -- 85% of high tickets closed
                    WHEN severity = 'medium' THEN random() < 0.8    -- 80% of medium tickets closed
                    ELSE random() < 0.75                            -- 75% of low tickets closed
                END;
                
                -- Create ticket close event if applicable
                IF should_close_ticket THEN
                    -- Resolution time varies by severity
                    resolution_hours := CASE
                        WHEN severity = 'critical' THEN 1 + (random() * 8)::integer    -- 1-8 hours
                        WHEN severity = 'high' THEN 4 + (random() * 20)::integer       -- 4-24 hours  
                        WHEN severity = 'medium' THEN 8 + (random() * 40)::integer     -- 8-48 hours
                        ELSE 12 + (random() * 120)::integer                           -- 12-132 hours (up to 5.5 days)
                    END;
                    
                    ticket_close_time := ticket_open_time + (resolution_hours || ' hours')::interval;
                    
                    -- Only close if within our 30-day window
                    IF ticket_close_time <= CURRENT_DATE + INTERVAL '1 day' THEN
                        INSERT INTO events (customer_id, event_type, ts, event_metadata) VALUES (
                            customer_record.id,
                            'ticket_close',
                            ticket_close_time,
                            jsonb_build_object(
                                'severity', severity,
                                'category', category,
                                'ticket_id', (SELECT event_metadata->>'ticket_id' FROM events 
                                             WHERE customer_id = customer_record.id 
                                             AND event_type = 'ticket_open' 
                                             AND ts = ticket_open_time),
                                'resolution_time_hours', resolution_hours,
                                'satisfaction_rating', CASE 
                                    WHEN resolution_hours <= 24 THEN 4 + (random())::integer  -- 4-5 stars for quick resolution
                                    WHEN resolution_hours <= 72 THEN 3 + (random() * 2)::integer  -- 3-4 stars
                                    ELSE 1 + (random() * 3)::integer  -- 1-3 stars for slow resolution
                                END
                            )
                        );
                    END IF;
                END IF;
                
            END IF;
        END LOOP;
        
    END LOOP;
END $$;

-- Create indexes for better performance (including the required M3 index)
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_events_customer_id_ts ON events(customer_id, ts);  -- M3 requirement
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_metadata_gin ON events USING GIN (event_metadata);
