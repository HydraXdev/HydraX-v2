-- BITTEN v2.0 Fires Table
-- Fire command execution tracking with risk management

CREATE TABLE IF NOT EXISTS fires (
    fire_id TEXT PRIMARY KEY,
    mission_id TEXT,
    user_id TEXT NOT NULL,
    signal_id TEXT NOT NULL,
    target_uuid TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED' CHECK (status IN ('QUEUED', 'SENT', 'FILLED', 'REJECTED', 'FAILED')),
    ticket INTEGER,
    fill_price REAL,
    lot_size REAL NOT NULL,
    sl_price REAL,
    tp_price REAL,
    equity_used REAL,
    risk_pct_used REAL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    filled_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (signal_id) REFERENCES signals(signal_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_fires_user_created ON fires(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fires_signal ON fires(signal_id);
CREATE INDEX IF NOT EXISTS idx_fires_status ON fires(status);
CREATE INDEX IF NOT EXISTS idx_fires_target_uuid ON fires(target_uuid);
CREATE INDEX IF NOT EXISTS idx_fires_ticket ON fires(ticket) WHERE ticket IS NOT NULL;

-- Auto-update timestamp trigger
CREATE TRIGGER update_fires_updated_at BEFORE UPDATE ON fires
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE fires IS 'Fire command execution tracking from signal to MT5 execution';
COMMENT ON COLUMN fires.status IS 'QUEUED (in IPC queue), SENT (to EA), FILLED (confirmed), REJECTED (EA error), FAILED (system error)';
COMMENT ON COLUMN fires.ticket IS 'MT5 order ticket number from EA confirmation';
COMMENT ON COLUMN fires.equity_used IS 'Account equity at time of fire execution';
COMMENT ON COLUMN fires.risk_pct_used IS 'Risk percentage applied (2% or 5% based on mode)';
