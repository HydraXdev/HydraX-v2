-- BITTEN v2.0 Signal Outcomes Table
-- Real-time signal tracking to TP/SL for ML training and performance analytics
-- Uses TimescaleDB for time-series optimization and automatic data retention

CREATE TABLE IF NOT EXISTS signal_outcomes (
    outcome_id SERIAL PRIMARY KEY,
    signal_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('WIN', 'LOSS', 'TIMEOUT')),
    pips_result REAL,
    duration_seconds INTEGER,
    tracked_at TIMESTAMP DEFAULT NOW(),
    pattern_type TEXT,
    confidence REAL,
    session TEXT,
    FOREIGN KEY (signal_id) REFERENCES signals(signal_id) ON DELETE CASCADE
);

-- Convert to TimescaleDB hypertable for time-series optimization
SELECT create_hypertable('signal_outcomes', 'tracked_at', if_not_exists => TRUE);

-- Automatic 90-day data retention policy
SELECT add_retention_policy('signal_outcomes', INTERVAL '90 days', if_not_exists => TRUE);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_signal_outcomes_signal ON signal_outcomes(signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_outcomes_outcome ON signal_outcomes(outcome);
CREATE INDEX IF NOT EXISTS idx_signal_outcomes_pattern ON signal_outcomes(pattern_type);
CREATE INDEX IF NOT EXISTS idx_signal_outcomes_tracked_at ON signal_outcomes(tracked_at DESC);

-- Composite indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_signal_outcomes_pattern_outcome ON signal_outcomes(pattern_type, outcome);
CREATE INDEX IF NOT EXISTS idx_signal_outcomes_confidence_outcome ON signal_outcomes(confidence, outcome);

-- Comments
COMMENT ON TABLE signal_outcomes IS 'Real-time signal outcome tracking for ML training and performance analytics';
COMMENT ON COLUMN signal_outcomes.outcome IS 'WIN (hit TP), LOSS (hit SL), TIMEOUT (neither hit within 4 hours)';
COMMENT ON COLUMN signal_outcomes.pips_result IS 'Final pip result (+TP or -SL)';
COMMENT ON COLUMN signal_outcomes.duration_seconds IS 'Time from signal creation to outcome';
COMMENT ON COLUMN signal_outcomes.pattern_type IS 'Denormalized for fast analytics queries';
COMMENT ON COLUMN signal_outcomes.confidence IS 'Denormalized TCS for confidence range analysis';
