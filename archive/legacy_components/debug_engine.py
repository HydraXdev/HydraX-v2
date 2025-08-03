#!/usr/bin/env python3
"""
Debug signal engine to see what's happening
"""

import sqlite3

def debug_market_data():
    print("🔍 DEBUGGING MARKET DATA...")
    
    db_path = "/root/HydraX-v2/data/live_market.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tick data
    cursor.execute("SELECT COUNT(*) FROM live_ticks")
    tick_count = cursor.fetchone()[0]
    print(f"📊 Total ticks: {tick_count}")
    
    # Check recent ticks per pair
    pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY"]
    
    print("\n📈 Recent data per pair:")
    for pair in pairs:
        cursor.execute("""
        SELECT COUNT(*) FROM live_ticks WHERE symbol = ?
        """, (pair,))
        count = cursor.fetchone()[0]
        
        cursor.execute("""
        SELECT bid, ask, timestamp FROM live_ticks 
        WHERE symbol = ? 
        ORDER BY timestamp DESC LIMIT 1
        """, (pair,))
        latest = cursor.fetchone()
        
        if latest:
            print(f"  {pair}: {count} ticks, latest: {latest[0]}/{latest[1]} at {latest[2]}")
        else:
            print(f"  {pair}: {count} ticks, no data")
    
    conn.close()

def calculate_tcs_debug(symbol):
    """Debug TCS calculation"""
    print(f"\n🔧 TCS DEBUG for {symbol}:")
    
    db_path = "/root/HydraX-v2/data/live_market.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT bid, ask, timestamp
    FROM live_ticks 
    WHERE symbol = ?
    ORDER BY timestamp DESC 
    LIMIT 20
    ''', (symbol,))
    
    history = cursor.fetchall()
    conn.close()
    
    print(f"  History records: {len(history)}")
    
    if len(history) < 10:
        print(f"  ❌ Insufficient data ({len(history)} < 10)")
        return 0
        
    # Calculate components
    prices = [(row[0] + row[1]) / 2 for row in history]
    current = prices[0]
    
    print(f"  Current price: {current}")
    
    # Trend analysis
    short_avg = sum(prices[:5]) / 5
    medium_avg = sum(prices[5:15]) / 10 if len(prices) >= 15 else short_avg
    
    trend = abs(short_avg - medium_avg) / medium_avg if medium_avg > 0 else 0
    
    print(f"  Short avg: {short_avg}")
    print(f"  Medium avg: {medium_avg}")
    print(f"  Trend: {trend}")
    
    # Volatility
    moves = [abs(prices[i] - prices[i+1]) for i in range(min(10, len(prices)-1))]
    volatility = sum(moves) / len(moves) if moves else 0
    
    print(f"  Volatility: {volatility}")
    
    # TCS components
    base = 70
    trend_points = min(15, trend * 5000)
    vol_points = min(10, volatility * 100000)
    time_bonus = 8  # Assume good time
    session_bonus = 5 if symbol in ["EURUSD", "GBPUSD", "USDJPY"] else 2
    
    tcs = int(base + trend_points + vol_points + time_bonus + session_bonus)
    
    print(f"  Base: {base}")
    print(f"  Trend points: {trend_points}")
    print(f"  Vol points: {vol_points}")
    print(f"  Time bonus: {time_bonus}")
    print(f"  Session bonus: {session_bonus}")
    print(f"  FINAL TCS: {tcs}")
    
    return tcs

def test_with_lower_threshold():
    """Test with very low threshold"""
    print("\n🎯 TESTING WITH LOW THRESHOLD...")
    
    from simple_live_engine import SimpleLiveEngine
    
    engine = SimpleLiveEngine()
    # Force low threshold
    engine.tcs_optimizer.current_threshold = 65.0
    
    signals = engine.run_signal_cycle()
    print(f"Signals with 65% threshold: {signals}")

if __name__ == "__main__":
    debug_market_data()
    calculate_tcs_debug("EURUSD")
    calculate_tcs_debug("GBPUSD")
    test_with_lower_threshold()