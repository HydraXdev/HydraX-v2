-- 📧 BITTEN Email Capture & Press Pass Claims Database Migration
-- Version: 1.0
-- Created: 2025-01-11
-- Description: Tables for email capture, Press Pass claims, and conversion tracking

-- ==========================================
-- PRESS PASS CLAIMS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS press_pass_claims (
    id BIGSERIAL PRIMARY KEY,
    
    -- Contact information
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    claim_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Claim tracking
    claimed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    activated BOOLEAN DEFAULT FALSE,
    activated_at TIMESTAMP WITH TIME ZONE,
    
    -- Conversion tracking
    converted BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMP WITH TIME ZONE,
    conversion_tier VARCHAR(50),
    
    -- Analytics attribution
    source VARCHAR(100),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    referral_code VARCHAR(50),
    
    -- Email engagement metrics
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    last_email_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- A/B testing
    ab_variant VARCHAR(50),
    
    -- Technical tracking
    user_agent VARCHAR(500),
    ip_address VARCHAR(50),
    
    -- Indexes
    INDEX idx_claims_email (email),
    INDEX idx_claims_token (claim_token),
    INDEX idx_claims_activated (activated),
    INDEX idx_claims_converted (converted),
    INDEX idx_claims_expires_at (expires_at),
    INDEX idx_claims_source (source),
    INDEX idx_claims_campaign (utm_campaign)
);

-- ==========================================
-- EMAIL CAMPAIGNS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS email_campaigns (
    id BIGSERIAL PRIMARY KEY,
    press_pass_claim_id BIGINT NOT NULL REFERENCES press_pass_claims(id) ON DELETE CASCADE,
    
    -- Campaign details
    campaign_type VARCHAR(50) NOT NULL, -- welcome, day1, day3, day6, day7
    content_variant VARCHAR(50), -- For A/B testing email content
    
    -- Tracking
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    -- Performance
    cta_clicked VARCHAR(100), -- Which CTA was clicked
    
    -- Indexes
    INDEX idx_campaigns_claim_id (press_pass_claim_id),
    INDEX idx_campaigns_type (campaign_type),
    INDEX idx_campaigns_sent_at (sent_at)
);

-- ==========================================
-- CONVERSION EVENTS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS conversion_events (
    id BIGSERIAL PRIMARY KEY,
    press_pass_claim_id BIGINT REFERENCES press_pass_claims(id) ON DELETE CASCADE,
    
    -- Event details
    event_type VARCHAR(100) NOT NULL, -- page_view, cta_click, signup_start, etc.
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Session tracking
    session_id VARCHAR(255),
    page_url VARCHAR(500),
    
    -- Indexes
    INDEX idx_events_claim_id (press_pass_claim_id),
    INDEX idx_events_type (event_type),
    INDEX idx_events_created_at (created_at DESC),
    INDEX idx_events_session (session_id)
);

-- ==========================================
-- A/B TEST RESULTS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS ab_test_results (
    id BIGSERIAL PRIMARY KEY,
    
    -- Test identification
    test_name VARCHAR(100) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    user_identifier VARCHAR(255) NOT NULL, -- email or session_id
    
    -- Assignment
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metrics
    exposures INTEGER DEFAULT 1,
    conversions JSONB DEFAULT '{}', -- {metric_name: count}
    
    -- Unique constraint
    UNIQUE(test_name, user_identifier),
    
    -- Indexes
    INDEX idx_ab_test_name (test_name),
    INDEX idx_ab_variant (variant),
    INDEX idx_ab_assigned_at (assigned_at)
);

-- ==========================================
-- ANALYTICS AGGREGATES TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS analytics_daily_aggregates (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    
    -- Metrics
    page_views INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    press_pass_claims INTEGER DEFAULT 0,
    press_pass_activations INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(15,2) DEFAULT 0,
    
    -- Funnel metrics
    email_form_views INTEGER DEFAULT 0,
    email_form_submits INTEGER DEFAULT 0,
    telegram_clicks INTEGER DEFAULT 0,
    
    -- Email metrics
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    
    -- A/B test performance
    ab_test_metrics JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    UNIQUE(date),
    
    -- Indexes
    INDEX idx_aggregates_date (date DESC)
);

-- ==========================================
-- FUNCTIONS & TRIGGERS
-- ==========================================

-- Function to update email engagement metrics
CREATE OR REPLACE FUNCTION update_email_engagement()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.opened_at IS NOT NULL AND OLD.opened_at IS NULL THEN
        UPDATE press_pass_claims
        SET emails_opened = emails_opened + 1
        WHERE id = NEW.press_pass_claim_id;
    END IF;
    
    IF NEW.clicked_at IS NOT NULL AND OLD.clicked_at IS NULL THEN
        UPDATE press_pass_claims
        SET emails_clicked = emails_clicked + 1
        WHERE id = NEW.press_pass_claim_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_email_engagement_trigger
AFTER UPDATE ON email_campaigns
FOR EACH ROW EXECUTE FUNCTION update_email_engagement();

-- Function to track conversion
CREATE OR REPLACE FUNCTION track_press_pass_conversion()
RETURNS TRIGGER AS $$
BEGIN
    -- If user tier changes from press_pass to paid tier
    IF OLD.tier = 'press_pass' AND NEW.tier IN ('NIBBLER', 'FANG', 'COMMANDER', 'APEX') THEN
        -- Update press pass claim if exists
        UPDATE press_pass_claims
        SET converted = TRUE,
            converted_at = CURRENT_TIMESTAMP,
            conversion_tier = NEW.tier
        WHERE email = NEW.email
          AND activated = TRUE
          AND converted = FALSE;
        
        -- Track conversion event
        INSERT INTO conversion_events (
            press_pass_claim_id,
            event_type,
            event_data
        )
        SELECT 
            id,
            'tier_upgrade',
            jsonb_build_object(
                'from_tier', OLD.tier,
                'to_tier', NEW.tier,
                'user_id', NEW.user_id
            )
        FROM press_pass_claims
        WHERE email = NEW.email
        LIMIT 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: This trigger should be created on the users table
-- CREATE TRIGGER track_press_pass_conversion_trigger
-- AFTER UPDATE OF tier ON users
-- FOR EACH ROW EXECUTE FUNCTION track_press_pass_conversion();

-- Function to aggregate daily analytics
CREATE OR REPLACE FUNCTION aggregate_daily_analytics(target_date DATE)
RETURNS void AS $$
BEGIN
    INSERT INTO analytics_daily_aggregates (
        date,
        press_pass_claims,
        press_pass_activations,
        conversions,
        emails_sent,
        emails_opened,
        emails_clicked
    )
    SELECT
        target_date,
        COUNT(DISTINCT ppc.id) FILTER (WHERE DATE(ppc.claimed_at) = target_date),
        COUNT(DISTINCT ppc.id) FILTER (WHERE DATE(ppc.activated_at) = target_date),
        COUNT(DISTINCT ppc.id) FILTER (WHERE DATE(ppc.converted_at) = target_date),
        COUNT(DISTINCT ec.id) FILTER (WHERE DATE(ec.sent_at) = target_date),
        COUNT(DISTINCT ec.id) FILTER (WHERE DATE(ec.opened_at) = target_date),
        COUNT(DISTINCT ec.id) FILTER (WHERE DATE(ec.clicked_at) = target_date)
    FROM press_pass_claims ppc
    LEFT JOIN email_campaigns ec ON ec.press_pass_claim_id = ppc.id
    ON CONFLICT (date) DO UPDATE SET
        press_pass_claims = EXCLUDED.press_pass_claims,
        press_pass_activations = EXCLUDED.press_pass_activations,
        conversions = EXCLUDED.conversions,
        emails_sent = EXCLUDED.emails_sent,
        emails_opened = EXCLUDED.emails_opened,
        emails_clicked = EXCLUDED.emails_clicked,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- INDEXES FOR PERFORMANCE
-- ==========================================

-- Composite indexes for common queries
CREATE INDEX idx_claims_active_not_converted ON press_pass_claims(activated, converted) 
WHERE activated = TRUE AND converted = FALSE;

CREATE INDEX idx_claims_expiring_soon ON press_pass_claims(expires_at) 
WHERE activated = TRUE AND converted = FALSE AND expires_at > CURRENT_TIMESTAMP;

CREATE INDEX idx_campaigns_performance ON email_campaigns(campaign_type, opened_at, clicked_at);

CREATE INDEX idx_events_funnel ON conversion_events(session_id, event_type, created_at);

-- ==========================================
-- INITIAL DATA
-- ==========================================

-- Create initial A/B tests
INSERT INTO ab_test_results (test_name, variant, user_identifier)
VALUES 
    ('press_pass_cta', 'control', 'system'),
    ('urgency_messaging', 'control', 'system'),
    ('email_subject_lines', 'control', 'system')
ON CONFLICT DO NOTHING;

-- ==========================================
-- PERMISSIONS
-- ==========================================

-- Grant permissions to application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bitten_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bitten_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bitten_app;