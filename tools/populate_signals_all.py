#!/usr/bin/env python3
"""
Populate signals_all table from existing signals data for winloss report
Maps old outcome format (WIN/LOSS) to new format (TP/SL)
"""

import sqlite3
from datetime import datetime

DB_PATH = "/root/HydraX-v2/bitten.db"

def migrate_signals():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting signal migration to signals_all table...")
    
    # Get existing signals
    cursor.execute("""
        SELECT 
            signal_id,
            created_at,
            symbol,
            direction,
            pattern_type,
            confidence,
            entry_price,
            sl,
            tp,
            stop_pips,
            target_pips,
            outcome
        FROM signals
        WHERE created_at IS NOT NULL
    """)
    
    signals = cursor.fetchall()
    print(f"Found {len(signals)} signals to migrate")
    
    # Migrate each signal
    migrated = 0
    for signal in signals:
        signal_id, created_at, symbol, direction, pattern_type, confidence, entry_price, sl, tp, stop_pips, target_pips, outcome = signal
        
        # Determine decision based on outcome
        decision = 'FIRED' if outcome else 'DROPPED'
        
        # Calculate risk reward
        risk_reward = None
        if stop_pips and target_pips and stop_pips > 0:
            risk_reward = target_pips / stop_pips
            
        # Determine session based on time
        if created_at:
            hour = datetime.fromtimestamp(created_at).hour
            if 22 <= hour or hour < 8:
                session = 'ASIAN'
            elif 8 <= hour < 12:
                session = 'LONDON'
            elif 12 <= hour < 17:
                session = 'NY'
            else:
                session = 'OVERLAP'
        else:
            session = 'UNKNOWN'
            
        # Insert into signals_all
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO signals_all (
                    signal_id, ts_fire, symbol, side, pattern, session,
                    raw_confidence, calibrated_confidence, decision,
                    entry_price, stop_loss, take_profit,
                    stop_pips, target_pips, risk_reward
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_id, created_at, symbol, direction, pattern_type, session,
                confidence, confidence, decision,  # Use same confidence for both
                entry_price, sl, tp,
                stop_pips, target_pips, risk_reward
            ))
            
            # Map outcome to shadow table if it exists
            if outcome:
                outcome_mapped = 'TP' if outcome == 'WIN' else 'SL' if outcome == 'LOSS' else 'TIMEOUT'
                achieved_r = 1.0 if outcome == 'WIN' else -1.0 if outcome == 'LOSS' else 0
                
                cursor.execute("""
                    INSERT OR IGNORE INTO signal_outcomes_shadow (
                        signal_id, outcome_shadow, achieved_r_shadow,
                        duration_min_shadow, resolved_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    signal_id, outcome_mapped, achieved_r,
                    60,  # Default 60 minutes duration
                    created_at + 3600 if created_at else None
                ))
                
            migrated += 1
            
        except sqlite3.IntegrityError:
            # Already exists, skip
            continue
            
    conn.commit()
    print(f"Migrated {migrated} signals to signals_all table")
    
    # Verify migration
    cursor.execute("SELECT COUNT(*) FROM signals_all")
    total = cursor.fetchone()[0]
    print(f"Total signals in signals_all: {total}")
    
    cursor.execute("SELECT COUNT(*) FROM signal_outcomes_shadow")
    shadow_total = cursor.fetchone()[0]
    print(f"Total shadow outcomes: {shadow_total}")
    
    conn.close()

if __name__ == "__main__":
    migrate_signals()