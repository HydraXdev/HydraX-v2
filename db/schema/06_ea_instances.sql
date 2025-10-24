-- BITTEN v2.0 EA Instances Table
-- MT5 Expert Advisor connection tracking and heartbeat monitoring

CREATE TABLE IF NOT EXISTS ea_instances (
    target_uuid TEXT PRIMARY KEY,
    user_id TEXT,
    account_login TEXT,
    broker TEXT,
    currency TEXT,
    leverage INTEGER,
    last_balance REAL,
    last_equity REAL,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_ea_instances_user ON ea_instances(user_id);
CREATE INDEX IF NOT EXISTS idx_ea_instances_last_seen ON ea_instances(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_ea_instances_version ON ea_instances(version);

-- Auto-update timestamp trigger
CREATE TRIGGER update_ea_instances_updated_at BEFORE UPDATE ON ea_instances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for active EAs (heartbeat within last 2 minutes)
CREATE OR REPLACE VIEW active_ea_instances AS
SELECT *
FROM ea_instances
WHERE last_seen >= NOW() - INTERVAL '2 minutes';

-- Comments
COMMENT ON TABLE ea_instances IS 'MT5 EA connection tracking with heartbeat monitoring';
COMMENT ON COLUMN ea_instances.target_uuid IS 'Unique EA identifier (e.g., COMMANDER_DEV_001)';
COMMENT ON COLUMN ea_instances.last_seen IS 'Last heartbeat timestamp for connection freshness';
COMMENT ON COLUMN ea_instances.version IS 'EA version (e.g., v2.07)';
COMMENT ON VIEW active_ea_instances IS 'EAs with heartbeat within last 120 seconds';
