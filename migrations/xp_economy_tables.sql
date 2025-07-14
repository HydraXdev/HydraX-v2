-- 💰 XP Economy Database Migration
-- Version: 1.0
-- Created: 2025-01-11
-- Description: Tables for XP economy system with full database integration,
--              transaction tracking, and Press Pass reset support

-- ==========================================
-- XP BALANCES TABLE
-- ==========================================

-- Core XP balance tracking for all users
CREATE TABLE IF NOT EXISTS xp_balances (
    user_id BIGINT PRIMARY KEY,
    current_balance INTEGER NOT NULL DEFAULT 0 CHECK (current_balance >= 0),
    lifetime_earned INTEGER NOT NULL DEFAULT 0 CHECK (lifetime_earned >= 0),
    lifetime_spent INTEGER NOT NULL DEFAULT 0 CHECK (lifetime_spent >= 0),
    prestige_level INTEGER NOT NULL DEFAULT 0 CHECK (prestige_level >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure data integrity
    CONSTRAINT balance_integrity CHECK (lifetime_earned >= lifetime_spent),
    CONSTRAINT balance_calculation CHECK (current_balance = lifetime_earned - lifetime_spent)
);

-- ==========================================
-- XP TRANSACTIONS TABLE
-- ==========================================

-- Complete transaction history for audit and analytics
CREATE TABLE IF NOT EXISTS xp_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- 'earn', 'spend', 'reset', 'bonus', 'refund'
    amount INTEGER NOT NULL, -- Positive for earning, negative for spending
    balance_before INTEGER NOT NULL CHECK (balance_before >= 0),
    balance_after INTEGER NOT NULL CHECK (balance_after >= 0),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES xp_balances(user_id)
        ON DELETE CASCADE,
    
    -- Data integrity checks
    CONSTRAINT transaction_balance_check CHECK (
        (transaction_type IN ('earn', 'bonus') AND amount > 0 AND balance_after = balance_before + amount) OR
        (transaction_type IN ('spend', 'reset') AND amount < 0 AND balance_after = balance_before + amount) OR
        (transaction_type = 'refund' AND amount > 0 AND balance_after = balance_before + amount)
    )
);

-- ==========================================
-- PRESS PASS RESET HISTORY
-- ==========================================

-- Track all Press Pass XP resets
CREATE TABLE IF NOT EXISTS press_pass_resets (
    reset_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    xp_wiped INTEGER NOT NULL CHECK (xp_wiped >= 0),
    reset_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE,
    
    INDEX idx_press_pass_resets_user (user_id),
    INDEX idx_press_pass_resets_date (reset_at DESC)
);

-- ==========================================
-- XP SHOP PURCHASES
-- ==========================================

-- Track active XP shop purchases
CREATE TABLE IF NOT EXISTS xp_shop_purchases (
    purchase_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id VARCHAR(100) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    purchase_type VARCHAR(50) NOT NULL,
    cost INTEGER NOT NULL CHECK (cost > 0),
    purchase_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    uses_remaining INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    
    -- Foreign key
    CONSTRAINT fk_user_purchase
        FOREIGN KEY(user_id)
        REFERENCES xp_balances(user_id)
        ON DELETE CASCADE,
    
    INDEX idx_shop_purchases_user (user_id),
    INDEX idx_shop_purchases_active (user_id, is_active),
    INDEX idx_shop_purchases_expires (expires_at)
);

-- ==========================================
-- JOB EXECUTION LOG
-- ==========================================

-- Track scheduled job executions
CREATE TABLE IF NOT EXISTS job_execution_log (
    log_id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_job_log_name (job_name),
    INDEX idx_job_log_time (execution_time DESC)
);

-- ==========================================
-- PERFORMANCE INDEXES
-- ==========================================

-- Optimize query performance
CREATE INDEX IF NOT EXISTS idx_xp_balances_current ON xp_balances(current_balance DESC);
CREATE INDEX IF NOT EXISTS idx_xp_balances_updated ON xp_balances(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_user_id ON xp_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_created_at ON xp_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_type ON xp_transactions(transaction_type);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_xp_transactions_user_date ON xp_transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_xp_balances_prestige ON xp_balances(prestige_level DESC, current_balance DESC);

-- ==========================================
-- TRIGGERS FOR AUTOMATED UPDATES
-- ==========================================

-- Update last_updated timestamp on balance changes
CREATE OR REPLACE FUNCTION update_xp_balance_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_xp_balance_timestamp_trigger
BEFORE UPDATE ON xp_balances
FOR EACH ROW EXECUTE FUNCTION update_xp_balance_timestamp();

-- Automatically expire shop purchases
CREATE OR REPLACE FUNCTION expire_shop_purchases()
RETURNS void AS $$
BEGIN
    UPDATE xp_shop_purchases
    SET is_active = FALSE
    WHERE is_active = TRUE
    AND (
        (expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP) OR
        (uses_remaining IS NOT NULL AND uses_remaining <= 0)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get user's active purchases
CREATE OR REPLACE FUNCTION get_active_purchases(p_user_id BIGINT)
RETURNS TABLE(
    item_id VARCHAR(100),
    item_name VARCHAR(200),
    purchase_type VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE,
    uses_remaining INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sp.item_id,
        sp.item_name,
        sp.purchase_type,
        sp.expires_at,
        sp.uses_remaining
    FROM xp_shop_purchases sp
    WHERE sp.user_id = p_user_id
    AND sp.is_active = TRUE
    AND (sp.expires_at IS NULL OR sp.expires_at > CURRENT_TIMESTAMP)
    AND (sp.uses_remaining IS NULL OR sp.uses_remaining > 0)
    ORDER BY sp.purchase_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate XP statistics
CREATE OR REPLACE FUNCTION get_xp_economy_stats()
RETURNS TABLE(
    total_circulation BIGINT,
    total_users INTEGER,
    average_balance NUMERIC,
    median_balance INTEGER,
    top_holder_balance INTEGER,
    transactions_today INTEGER,
    xp_earned_today BIGINT,
    xp_spent_today BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH stats AS (
        SELECT 
            SUM(current_balance) as total_circ,
            COUNT(*) as user_count,
            AVG(current_balance) as avg_bal,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY current_balance) as med_bal,
            MAX(current_balance) as max_bal
        FROM xp_balances
        WHERE current_balance > 0
    ),
    daily_tx AS (
        SELECT 
            COUNT(*) as tx_today,
            SUM(CASE WHEN transaction_type IN ('earn', 'bonus') THEN amount ELSE 0 END) as earned,
            SUM(CASE WHEN transaction_type IN ('spend', 'reset') THEN ABS(amount) ELSE 0 END) as spent
        FROM xp_transactions
        WHERE created_at >= CURRENT_DATE
    )
    SELECT 
        COALESCE(stats.total_circ, 0),
        COALESCE(stats.user_count, 0),
        COALESCE(stats.avg_bal, 0),
        COALESCE(stats.med_bal, 0)::INTEGER,
        COALESCE(stats.max_bal, 0),
        COALESCE(daily_tx.tx_today, 0)::INTEGER,
        COALESCE(daily_tx.earned, 0),
        COALESCE(daily_tx.spent, 0)
    FROM stats, daily_tx;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- SCHEDULED JOBS (via pg_cron or external)
-- ==========================================

-- Note: Schedule these functions to run:
-- 1. expire_shop_purchases() - Every hour
-- 2. Press Pass reset - Daily at 00:00 UTC
-- 3. Warning notifications - 23:00 and 23:45 UTC

-- Example pg_cron setup (requires pg_cron extension):
-- SELECT cron.schedule('expire-xp-purchases', '0 * * * *', 'SELECT expire_shop_purchases();');
-- SELECT cron.schedule('press-pass-warn-60', '0 23 * * *', $$CALL system('/path/to/press_pass_reset_job.py warn_60');$$);
-- SELECT cron.schedule('press-pass-warn-15', '45 23 * * *', $$CALL system('/path/to/press_pass_reset_job.py warn_15');$$);
-- SELECT cron.schedule('press-pass-reset', '0 0 * * *', $$CALL system('/path/to/press_pass_reset_job.py reset');$$);

-- ==========================================
-- PERMISSIONS
-- ==========================================

-- Grant permissions to application user (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bitten_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bitten_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bitten_app;

-- ==========================================
-- MIGRATION COMPLETE
-- ==========================================

-- Insert migration record
INSERT INTO migration_history (filename, applied_at) 
VALUES ('xp_economy_tables.sql', CURRENT_TIMESTAMP)
ON CONFLICT (filename) DO NOTHING;