-- BITTEN v2.0 Positions Table
-- Active and closed MT5 position tracking with P&L

CREATE TABLE IF NOT EXISTS positions (
    position_id TEXT PRIMARY KEY,
    fire_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    ticket INTEGER NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED_TP', 'CLOSED_SL', 'CLOSED_MANUAL', 'CLOSED_PARTIAL')),
    open_price REAL NOT NULL,
    close_price REAL,
    lot_size REAL NOT NULL,
    profit_loss REAL,
    pips_result REAL,
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    FOREIGN KEY (fire_id) REFERENCES fires(fire_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_positions_user_status ON positions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_positions_ticket ON positions(ticket);
CREATE INDEX IF NOT EXISTS idx_positions_fire_id ON positions(fire_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_opened_at ON positions(opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_positions_closed_at ON positions(closed_at DESC) WHERE closed_at IS NOT NULL;

-- Comments
COMMENT ON TABLE positions IS 'MT5 position tracking with real-time P&L updates';
COMMENT ON COLUMN positions.status IS 'OPEN (active trade), CLOSED_TP (hit take profit), CLOSED_SL (hit stop loss), CLOSED_MANUAL (user closed), CLOSED_PARTIAL (BITMODE partial close)';
COMMENT ON COLUMN positions.ticket IS 'MT5 order ticket number (unique)';
COMMENT ON COLUMN positions.profit_loss IS 'Final profit/loss in account currency';
COMMENT ON COLUMN positions.pips_result IS 'Final pip result (+/-)';
