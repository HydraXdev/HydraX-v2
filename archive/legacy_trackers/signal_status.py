#!/usr/bin/env python3
"""
Quick VENOM Signal Status Check
Shows current win/loss status at a glance
"""

import sqlite3
import json
import os
from datetime import datetime

def get_current_prices():
    """Get current market prices"""
    try:
        with open('/tmp/ea_raw_data.json', 'r') as f:
            content = f.read().strip()
            if not content.endswith('}'):
                if content.endswith(']'):
                    content += '}'
                elif content.endswith(','):
                    content = content.rstrip(',') + ']}'
            return json.loads(content)
    except:
        return {"ticks": []}

def check_signal_status():
    """Check current signal status"""
    db_path = "/root/HydraX-v2/signal_tracker.db"
    
    if not os.path.exists(db_path):
        print("❌ No tracking database found. Start realtime_signal_tracker.py first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get overall stats
    cursor.execute("SELECT COUNT(*) FROM signals")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signals WHERE outcome = 'WIN'")
    wins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signals WHERE outcome = 'LOSS'")
    losses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signals WHERE outcome = 'PENDING'")
    pending = cursor.fetchone()[0]
    
    # Get current prices for pending analysis
    current_prices = get_current_prices()
    price_map = {}
    for tick in current_prices.get('ticks', []):
        price_map[tick['symbol']] = {'bid': tick['bid'], 'ask': tick['ask']}
    
    # Get recent signals with current analysis
    cursor.execute('''
        SELECT signal_id, symbol, direction, confidence, quality,
               entry_price, stop_loss, take_profit, outcome, timestamp
        FROM signals 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''')
    
    print("🐍⚡ VENOM SIGNAL STATUS")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Overall stats
    closed = wins + losses  
    win_rate = (wins / closed * 100) if closed > 0 else 0
    
    print("📊 PERFORMANCE SUMMARY")
    print(f"📈 Total: {total} | ✅ Wins: {wins} | ❌ Losses: {losses} | ⏳ Pending: {pending}")
    print(f"🎯 Win Rate: {win_rate:.1f}% ({wins}/{closed})")
    print()
    
    print("🔄 RECENT SIGNALS")
    print("-" * 30)
    
    for row in cursor.fetchall():
        signal_id, symbol, direction, confidence, quality, entry, sl, tp, outcome, timestamp = row
        
        # Get current market analysis for pending signals
        status_info = ""
        if outcome == 'PENDING' and symbol in price_map:
            current = price_map[symbol]['bid'] if direction == 'SELL' else price_map[symbol]['ask']
            
            if direction == 'BUY':
                sl_dist = current - sl
                tp_dist = tp - current
                if current >= tp:
                    status_info = f"✅ Hit TP ({current:.5f})"
                elif current <= sl:
                    status_info = f"❌ Hit SL ({current:.5f})"
                else:
                    status_info = f"⏳ {current:.5f} (SL:{sl_dist:+.1f}p, TP:{tp_dist:+.1f}p)"
            else:  # SELL
                sl_dist = sl - current
                tp_dist = current - tp
                if current <= tp:
                    status_info = f"✅ Hit TP ({current:.5f})"
                elif current >= sl:
                    status_info = f"❌ Hit SL ({current:.5f})"
                else:
                    status_info = f"⏳ {current:.5f} (SL:{sl_dist:+.1f}p, TP:{tp_dist:+.1f}p)"
        
        # Format output
        if outcome == 'WIN':
            emoji = "✅"
        elif outcome == 'LOSS':
            emoji = "❌"
        else:
            emoji = "⏳"
        
        quality_emoji = "💎" if quality == "platinum" else "🥇"
        short_id = signal_id.split('_')[-1] if '_' in signal_id else signal_id[-4:]
        
        print(f"{emoji} {symbol} {direction} @{confidence}% {quality_emoji} ({short_id})")
        if status_info:
            print(f"   {status_info}")
    
    conn.close()

if __name__ == "__main__":
    check_signal_status()