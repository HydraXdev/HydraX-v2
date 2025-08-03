
#!/usr/bin/env python3
"""BITTEN Live Trading Dashboard"""
import sqlite3
import time
import os
from datetime import datetime

def show_dashboard():
    db_path = "/root/HydraX-v2/data/live_market.db"
    
    while True:
        os.system('clear')
        print("=== BITTEN LIVE TRADING DASHBOARD ===")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*40)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Recent ticks
            cursor.execute("""
                SELECT symbol, bid, ask, spread, timestamp 
                FROM live_ticks 
                ORDER BY timestamp DESC 
                LIMIT 8
            """)
            
            print("\n📊 RECENT MARKET DATA:")
            print(f"{'Symbol':<10} {'Bid':<10} {'Ask':<10} {'Spread':<8} {'Time':<20}")
            print("-"*60)
            
            for row in cursor.fetchall():
                symbol, bid, ask, spread, timestamp = row
                print(f"{symbol:<10} {bid:<10.5f} {ask:<10.5f} {spread:<8.5f} {timestamp[-8:]}")
            
            # Recent signals
            cursor.execute("""
                SELECT symbol, direction, entry_price, confidence, timestamp
                FROM live_signals
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            print("\n🎯 RECENT SIGNALS:")
            print(f"{'Symbol':<10} {'Dir':<5} {'Entry':<10} {'Conf':<6} {'Time':<20}")
            print("-"*60)
            
            for row in cursor.fetchall():
                symbol, direction, entry, conf, timestamp = row
                dir_icon = "🟢" if direction == "BUY" else "🔴"
                print(f"{symbol:<10} {dir_icon} {direction:<4} {entry:<10.5f} {conf:<6.1%} {timestamp[-8:]}")
            
            # Stats
            cursor.execute("SELECT COUNT(*) FROM live_ticks WHERE timestamp > datetime('now', '-1 hour')")
            hourly_ticks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM live_signals WHERE timestamp > datetime('now', '-24 hours')")
            daily_signals = cursor.fetchone()[0]
            
            print(f"\n📈 STATS:")
            print(f"Ticks/hour: {hourly_ticks}")
            print(f"Signals today: {daily_signals}")
            
            conn.close()
            
        except Exception as e:
            print(f"\nError: {e}")
        
        time.sleep(5)

if __name__ == "__main__":
    show_dashboard()
