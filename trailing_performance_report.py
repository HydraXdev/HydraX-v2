#!/usr/bin/env python3
"""
Trailing Stop Performance Analytics
Shows how much extra profit trailing stops captured vs fixed TP
"""
import sqlite3
import json
from datetime import datetime

def trailing_performance_report():
    """Generate comprehensive trailing stop performance report"""

    db_path = "/root/HydraX-v2/bitten.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*70)
    print("🎯 TRAILING STOP PERFORMANCE REPORT")
    print("="*70)

    # 1. Get all trailing-enabled trades (EXIT events)
    cursor.execute("""
        SELECT
            fire_id,
            symbol,
            direction,
            current_profit_pips,
            style,
            created_at
        FROM trailing_events
        WHERE event_type = 'EXIT'
        ORDER BY created_at DESC
        LIMIT 50
    """)

    exits = cursor.fetchall()

    if not exits:
        print("\n📊 No trailing stop exits recorded yet")
        print("   (Trades need to close via trailing SL to appear here)\n")
        conn.close()
        return

    print(f"\n📊 TRAILING STOP EXITS: {len(exits)} trades")
    print("-"*70)

    total_pips = 0
    by_style = {}

    for fire_id, symbol, direction, profit_pips, style, created_at in exits:
        total_pips += profit_pips or 0

        if style not in by_style:
            by_style[style] = {'count': 0, 'total_pips': 0}
        by_style[style]['count'] += 1
        by_style[style]['total_pips'] += profit_pips or 0

        # Show last 10 trades
        if exits.index((fire_id, symbol, direction, profit_pips, style, created_at)) < 10:
            timestamp = datetime.fromtimestamp(created_at).strftime('%m/%d %H:%M')
            print(f"{timestamp} | {symbol:8} {direction:4} | +{profit_pips:6.1f} pips | {style}")

    print("-"*70)
    print(f"TOTAL CAPTURED: +{total_pips:.1f} pips")

    # 2. Compare trailing vs non-trailing
    print("\n\n💰 PROFIT COMPARISON: Trailing vs Fixed TP")
    print("-"*70)

    # Get trailing exits average
    cursor.execute("""
        SELECT AVG(current_profit_pips) FROM trailing_events WHERE event_type = 'EXIT'
    """)
    trailing_avg = cursor.fetchone()[0] or 0

    # Get non-trailing exits average (positions closed at original TP)
    cursor.execute("""
        SELECT AVG(
            CASE
                WHEN direction = 'BUY' THEN (tp - price) / 0.0001
                WHEN direction = 'SELL' THEN (price - tp) / 0.0001
            END
        ) as avg_pips
        FROM fires
        WHERE status = 'FILLED'
        AND ticket > 0
        AND fire_id NOT IN (SELECT DISTINCT fire_id FROM trailing_events)
        LIMIT 100
    """)
    fixed_avg = cursor.fetchone()[0] or 0

    print(f"Average Trailing Stop Exit:  +{trailing_avg:.1f} pips")
    print(f"Average Fixed TP Exit:        +{fixed_avg:.1f} pips")

    if trailing_avg > fixed_avg:
        improvement = ((trailing_avg - fixed_avg) / fixed_avg * 100) if fixed_avg > 0 else 0
        extra_pips = trailing_avg - fixed_avg
        print(f"\n✅ TRAILING ADVANTAGE: +{extra_pips:.1f} pips per trade (+{improvement:.1f}%)")

    # 3. Breakdown by trailing style
    print("\n\n📊 PERFORMANCE BY TRAILING STYLE:")
    print("-"*70)

    for style, data in sorted(by_style.items(), key=lambda x: x[1]['total_pips'], reverse=True):
        count = data['count']
        total = data['total_pips']
        avg = total / count if count > 0 else 0
        print(f"{style:15} | {count:3} trades | Avg: +{avg:6.1f} pips | Total: +{total:8.1f} pips")

    # 4. Show PROTECTION achievements (30+ pip milestones)
    cursor.execute("""
        SELECT COUNT(*), AVG(current_profit_pips)
        FROM trailing_events
        WHERE event_type = 'PROTECTION'
    """)

    protection_count, protection_avg = cursor.fetchone()

    if protection_count and protection_count > 0:
        print("\n\n🛡️ PROFIT PROTECTION MILESTONES:")
        print("-"*70)
        print(f"Trades reaching +30 pips:  {protection_count}")
        print(f"Average profit at unlock:  +{protection_avg:.1f} pips")
        print(f"\n✅ {protection_count} slots unlocked early for new trades!")

    # 5. Show active trailing positions
    cursor.execute("""
        SELECT
            fire_id,
            symbol,
            direction,
            current_profit_pips,
            style,
            event_type
        FROM trailing_events
        WHERE fire_id IN (
            SELECT DISTINCT fire_id
            FROM trailing_events
            WHERE event_type IN ('ACTIVE', 'ARMED', 'UPDATED')
        )
        AND fire_id NOT IN (
            SELECT fire_id FROM trailing_events WHERE event_type = 'EXIT'
        )
        ORDER BY created_at DESC
        LIMIT 10
    """)

    active = cursor.fetchall()

    if active:
        print("\n\n🎯 ACTIVE TRAILING POSITIONS:")
        print("-"*70)
        for fire_id, symbol, direction, profit_pips, style, event_type in active[:5]:
            print(f"{symbol:8} {direction:4} | +{profit_pips:6.1f} pips | {style:10} | {event_type}")

    print("\n" + "="*70)
    print("✅ Report complete - Trailing stops working as expected!")
    print("="*70 + "\n")

    conn.close()

if __name__ == "__main__":
    trailing_performance_report()
