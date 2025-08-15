#!/usr/bin/env python3
"""
One-time backfill script to populate signals and template missions from last 24h
Parses relay logs for ELITE_GUARD_* signals and inserts into database
"""

import sqlite3
import json
import time
import subprocess
import re
import os

def main():
    # Database connection
    DB = os.environ.get("BITTEN_DB", "/root/HydraX-v2/bitten.db")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    now = int(time.time())
    since = now - 24*3600
    
    # Get relay logs from last 24h
    result = subprocess.run(
        ["pm2", "logs", "relay_to_telegram", "--lines", "2000", "--nostream"],
        capture_output=True, text=True
    )
    
    lines = result.stdout.split('\n')
    
    # Parse signals from logs
    signals_found = {}
    pattern = r"Signal relayed: (ELITE_GUARD_\w+_\d+) \((\w+) (\w+)\)"
    
    for line in lines:
        if "Signal relayed:" in line:
            match = re.search(pattern, line)
            if match:
                signal_id = match.group(1)
                symbol = match.group(2)
                direction = match.group(3)
                
                if signal_id not in signals_found:
                    signals_found[signal_id] = {
                        'signal_id': signal_id,
                        'symbol': symbol,
                        'direction': direction,
                        'entry_price': 0,
                        'stop_pips': 10,  # default
                        'target_pips': 15,  # default
                        'confidence': 70,  # default
                        'pattern_type': 'LIQUIDITY_SWEEP_REVERSAL'
                    }
    
    # Also check for existing mission files
    missions_dir = "/root/HydraX-v2/missions"
    if os.path.exists(missions_dir):
        for filename in os.listdir(missions_dir):
            if filename.startswith("ELITE_GUARD_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(missions_dir, filename), 'r') as f:
                        data = json.load(f)
                        signal_id = data.get('signal_id', filename.replace('.json', ''))
                        
                        if signal_id not in signals_found:
                            signals_found[signal_id] = {
                                'signal_id': signal_id,
                                'symbol': data.get('symbol', data.get('pair', '')),
                                'direction': data.get('direction', ''),
                                'entry_price': float(data.get('entry_price', 0) or 0),
                                'stop_pips': float(data.get('stop_pips', 10) or 10),
                                'target_pips': float(data.get('target_pips', 15) or 15),
                                'confidence': float(data.get('confidence', 70) or 70),
                                'pattern_type': data.get('pattern_type', 'UNKNOWN')
                            }
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
    
    # Insert signals and create template missions
    signals_added = 0
    missions_added = 0
    
    for signal_id, signal in signals_found.items():
        # Check if signal already exists
        exists = cur.execute("SELECT 1 FROM signals WHERE signal_id=?", (signal_id,)).fetchone()
        
        if not exists:
            # Insert signal (note: sl/tp stored as absolute values, not pips)
            cur.execute("""
                INSERT OR IGNORE INTO signals
                (signal_id, symbol, direction, entry, sl, tp, confidence, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_id,
                signal['symbol'],
                signal['direction'],
                signal['entry_price'],
                0,  # sl will be computed at fire time from stop_pips
                0,  # tp will be computed at fire time from target_pips
                signal['confidence'],
                json.dumps(signal),  # payload has stop_pips/target_pips
                now - 3600  # Assume 1 hour ago
            ))
            signals_added += cur.rowcount
        
        # Check if template mission exists
        mission_exists = cur.execute("SELECT 1 FROM missions WHERE mission_id=?", (signal_id,)).fetchone()
        
        if not mission_exists:
            # Create template mission
            cur.execute("""
                INSERT OR IGNORE INTO missions
                (mission_id, signal_id, payload_json, status, expires_at, created_at)
                VALUES (?, ?, ?, 'PENDING', ?, ?)
            """, (
                signal_id,
                signal_id,
                json.dumps(signal),
                now + 30*60,  # 30 minutes from now
                now - 3600  # Assume 1 hour ago
            ))
            missions_added += cur.rowcount
    
    conn.commit()
    
    # Print summary
    print(f"Backfill complete:")
    print(f"  Signals found in logs/files: {len(signals_found)}")
    print(f"  Signals added to DB: {signals_added}")
    print(f"  Template missions created: {missions_added}")
    
    # Show current counts
    signal_count = cur.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    mission_count = cur.execute("SELECT COUNT(*) FROM missions").fetchone()[0]
    
    print(f"\nCurrent totals:")
    print(f"  Total signals in DB: {signal_count}")
    print(f"  Total missions in DB: {mission_count}")
    
    conn.close()

if __name__ == "__main__":
    main()