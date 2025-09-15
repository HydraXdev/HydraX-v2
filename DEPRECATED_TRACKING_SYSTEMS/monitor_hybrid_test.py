#!/usr/bin/env python3
"""
Real-time monitor for USDJPY hybrid position management test
Tracks partial closes, BE modifications, and trail behavior
"""

import json
import time
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = "/root/HydraX-v2/bitten.db"
LOG_FILE = "/root/HydraX-v2/hybrid_test_events.jsonl"

def get_active_positions():
    """Get active USDJPY positions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        ticket,
        symbol,
        direction,
        entry_price,
        sl_price,
        tp_price,
        lot_size,
        opened_at,
        status
    FROM positions
    WHERE symbol = 'USDJPY' 
    AND status IN ('OPEN', 'PARTIAL')
    ORDER BY opened_at DESC
    LIMIT 1
    """
    
    result = cursor.fetchone()
    conn.close()
    return result

def get_position_events(ticket):
    """Get all events for a position"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        event_type,
        event_data,
        created_at
    FROM position_events
    WHERE ticket = ?
    ORDER BY created_at ASC
    """
    
    results = cursor.execute(query, (ticket,)).fetchall()
    conn.close()
    return results

def log_event(event_type, data):
    """Log event to JSONL file"""
    with open(LOG_FILE, 'a') as f:
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        f.write(json.dumps(event) + '\n')
        print(f"[{event['timestamp']}] {event_type}: {data}")

def monitor_position():
    """Monitor USDJPY position for hybrid events"""
    print("🔍 Monitoring for USDJPY hybrid position test...")
    print("=" * 60)
    
    position_found = False
    tracked_ticket = None
    tp1_hit = False
    be_modified = False
    trail_started = False
    
    while True:
        try:
            position = get_active_positions()
            
            if position and not position_found:
                ticket, symbol, direction, entry, sl, tp, lot, opened, status = position
                tracked_ticket = ticket
                position_found = True
                
                log_event("POSITION_OPENED", {
                    'ticket': ticket,
                    'symbol': symbol,
                    'direction': direction,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp if tp else 'None (hybrid mode)',
                    'lot': lot,
                    'opened': opened
                })
                
                # Calculate expected TP1
                if direction == 'BUY':
                    tp1_target = entry + 0.30  # 30 pips for USDJPY
                else:
                    tp1_target = entry - 0.30
                    
                log_event("TP1_TARGET", {
                    'entry': entry,
                    'tp1_target': tp1_target,
                    'pips_to_tp1': 30
                })
            
            if tracked_ticket:
                events = get_position_events(tracked_ticket)
                
                for event_type, event_data, created_at in events:
                    data = json.loads(event_data) if event_data else {}
                    
                    # Check for TP1 partial close
                    if event_type == 'PARTIAL_CLOSE' and not tp1_hit:
                        tp1_hit = True
                        log_event("TP1_PARTIAL", {
                            'percent_closed': data.get('percent', 'unknown'),
                            'price': data.get('price', 'unknown'),
                            'pips_profit': data.get('pips', 'unknown')
                        })
                    
                    # Check for BE modification
                    if event_type == 'MODIFY_SL' and tp1_hit and not be_modified:
                        be_modified = True
                        log_event("BE_MODIFICATION", {
                            'new_sl': data.get('new_sl', 'unknown'),
                            'offset_pips': data.get('offset', 'unknown')
                        })
                    
                    # Check for trail start
                    if event_type == 'TRAIL_START' and not trail_started:
                        trail_started = True
                        log_event("TRAIL_STARTED", {
                            'trail_distance': data.get('distance', 'unknown'),
                            'current_price': data.get('price', 'unknown')
                        })
                    
                    # Check for position closure
                    if event_type in ['CLOSED', 'STOPPED_OUT', 'TRAIL_HIT']:
                        log_event("POSITION_CLOSED", {
                            'exit_type': event_type,
                            'exit_price': data.get('price', 'unknown'),
                            'total_pips': data.get('pips', 'unknown'),
                            'total_r': data.get('r_multiple', 'unknown')
                        })
                        
                        print("\n" + "="*60)
                        print("✅ Test complete! Check hybrid_test_events.jsonl for full log")
                        return
            
            time.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_position()