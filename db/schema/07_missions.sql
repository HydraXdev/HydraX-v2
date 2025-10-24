-- BITTEN v2.0 Missions Table
-- User-specific mission briefings with Telegram message tracking

CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    signal_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    tg_message_id BIGINT,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACTIVE', 'COMPLETED', 'EXPIRED')),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    target_uuid TEXT,
    FOREIGN KEY (signal_id) REFERENCES signals(signal_id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_missions_signal ON missions(signal_id);
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
CREATE INDEX IF NOT EXISTS idx_missions_tg_message_id ON missions(tg_message_id) WHERE tg_message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_missions_target_uuid ON missions(target_uuid);
CREATE INDEX IF NOT EXISTS idx_missions_expires_at ON missions(expires_at) WHERE status = 'PENDING';

-- Comments
COMMENT ON TABLE missions IS 'User-specific mission briefings with Telegram integration';
COMMENT ON COLUMN missions.payload_json IS 'Complete mission HUD data (risk, reward, pattern details)';
COMMENT ON COLUMN missions.tg_message_id IS 'Telegram message ID for mission briefing';
COMMENT ON COLUMN missions.status IS 'PENDING (awaiting fire), ACTIVE (fired), COMPLETED (closed), EXPIRED (timed out)';
