#!/usr/bin/env python3
"""
BITMODE Diagnostic Tool - Monitor and debug hybrid positions
# [DISABLED BITMODE] Shows real-time status of BITMODE positions and their milestones
"""

import json
import time
import sqlite3
from datetime import datetime
from src.bitten_core.hybrid_manager import hybrid_manager
from src.bitten_core.fire_mode_database import fire_mode_db

def check_bitmode_status():
# [DISABLED BITMODE]     """Check which users have BITMODE enabled"""
    conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, bitmode_enabled, current_mode, auto_slots_in_use
        FROM user_fire_modes
        WHERE bitmode_enabled = 1
    """)
    results = cursor.fetchall()
    conn.close()
    
# [DISABLED BITMODE]     print("\n🎯 BITMODE ENABLED USERS:")
    print("-" * 60)
    if results:
        for user_id, enabled, mode, slots in results:
            print(f"User: {user_id} | Mode: {mode} | Active Slots: {slots}")
    else:
# [DISABLED BITMODE]         print("No users have BITMODE enabled")
    print("-" * 60)
    return results

def check_active_positions():
    """Check active positions from database"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.fire_id, f.user_id, s.symbol, s.direction, 
               f.status, f.ticket, f.price, f.created_at
        FROM fires f
        JOIN missions m ON f.mission_id = m.mission_id
        JOIN signals s ON m.signal_id = s.signal_id
        WHERE f.status = 'FILLED'
        AND (f.closed_at IS NULL OR f.closed_at = 0)
        ORDER BY f.created_at DESC
        LIMIT 10
    """)
    results = cursor.fetchall()
    conn.close()
    
    print("\n📊 ACTIVE POSITIONS:")
    print("-" * 80)
    if results:
        for fire_id, user_id, symbol, direction, status, ticket, price, created_at in results:
            age_minutes = (time.time() - created_at) / 60 if created_at else 0
            print(f"Fire: {fire_id[:20]}... | {symbol} {direction} | Ticket: {ticket} | Age: {age_minutes:.1f}m")
            
            # Check if this position is being tracked by hybrid manager
            diagnostic = hybrid_manager.get_diagnostic_info(fire_id)
            if "error" not in diagnostic:
                print(f"  → State: {diagnostic['state']} | Partials: {diagnostic['partials_done']}")
                print(f"  → TP1: {diagnostic['tp1_price']:.5f} | TP2: {diagnostic['tp2_price']:.5f}")
                print(f"  → BE: {diagnostic['be_price']:.5f} | Trail: {diagnostic['trail_pips']:.1f} pips")
    else:
        print("No active positions found")
    print("-" * 80)

def test_pip_calculations():
    """Test pip calculation for different symbols"""
    print("\n🔧 PIP CALCULATION TEST:")
    print("-" * 60)
    
    test_cases = [
        ("EURUSD", 1.1000, 1.0980, "BUY"),
        ("GBPUSD", 1.3000, 1.2980, "SELL"),
        ("USDJPY", 150.00, 149.80, "BUY"),
        ("XAUUSD", 2650.00, 2648.00, "SELL"),
        ("XAGUSD", 31.500, 31.490, "BUY"),
    ]
    
    for symbol, entry, sl, direction in test_cases:
        config = hybrid_manager.get_symbol_config(symbol)
        risk_pips = hybrid_manager.price_to_pips(symbol, entry, sl)
        
        # Calculate levels
        levels = hybrid_manager.calculate_hybrid_levels(symbol, entry, sl, direction)
        
        print(f"\n{symbol} {direction} @ {entry:.5f}:")
        print(f"  Pip size: {config.pip_size} | Points/pip: {config.points_per_pip}")
        print(f"  Risk: {risk_pips:.1f} pips")
        print(f"  TP1 (1.5R): {levels['tp1_price']:.5f} (+{levels['tp1_pips']:.1f} pips)")
        print(f"  TP2 (2.0R): {levels['tp2_price']:.5f} (+{levels['tp2_pips']:.1f} pips)")
        print(f"  BE offset: {levels['be_offset_pips']:.1f} pips")
        print(f"  Trail: {levels['trail_distance_pips']:.1f} pips")
    
    print("-" * 60)

def monitor_loop():
    """Continuous monitoring loop"""
# [DISABLED BITMODE]     print("\n🔄 STARTING BITMODE MONITOR (Press Ctrl+C to stop)")
    print("=" * 80)
    
    while True:
        try:
            # Clear screen (optional)
            print("\033[H\033[J", end="")  # ANSI escape to clear screen
            
# [DISABLED BITMODE]             print(f"📅 BITMODE DIAGNOSTIC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
# [DISABLED BITMODE]             # Check BITMODE users
            bitmode_users = check_bitmode_status()
            
            # Check active positions
            check_active_positions()
            
            # Show pip calculations
            test_pip_calculations()
            
            print("\n" + "=" * 80)
            print("Refreshing in 30 seconds...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\n✋ Monitor stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error in monitor loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
# [DISABLED BITMODE] ║           BITMODE DIAGNOSTIC & MONITORING TOOL            ║
╠══════════════════════════════════════════════════════════╣
# [DISABLED BITMODE] ║  This tool monitors BITMODE positions and verifies the    ║
║  correct pip calculations for partial closes and BE moves ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run one-time check first
    check_bitmode_status()
    check_active_positions()
    test_pip_calculations()
    
    # Ask if user wants continuous monitoring
    print("\n" + "=" * 80)
    response = input("Start continuous monitoring? (y/n): ")
    if response.lower() == 'y':
        monitor_loop()
    else:
        print("✅ Diagnostic complete")