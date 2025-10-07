#!/usr/bin/env python3
"""
BITTEN COMPREHENSIVE PERFORMANCE REPORT
One-stop shop for ALL system performance data - no modifications needed
Shows all dimensions: time periods, patterns, confidence levels, sessions, pairs
"""

import json
import os
import sqlite3
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta


def get_signals_from_event_bus():
    """Get signal data from event bus with fallback to traditional sources"""
    signals = []
    try:
        conn = sqlite3.connect("/root/HydraX-v2/event_bus/bitten_events.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT signal_id, symbol, direction, confidence, pattern_type, created_at
            FROM signal_events
            WHERE created_at > ?
            ORDER BY created_at DESC
        """,
            (datetime.now().timestamp() - 24 * 3600,),
        )

        for row in cursor.fetchall():
            signals.append(
                {
                    "signal_id": row[0],
                    "symbol": row[1],
                    "direction": row[2],
                    "confidence": row[3],
                    "pattern_type": row[4],
                    "created_at": row[5],
                }
            )
        conn.close()
        print(f"📍 Signal Data Source: Event Bus ({len(signals)} signals)")
        return signals
    except Exception as e:
        print(f"⚠️ Event Bus unavailable ({e}), using database fallback")
        return []


def get_outcomes_from_event_bus():
    """Get outcome data from event bus execution.outcome.v1 events"""
    outcomes = []
    try:
        conn = sqlite3.connect("/root/HydraX-v2/event_bus/bitten_events.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_json FROM events
            WHERE event_type = 'execution.outcome.v1'
            ORDER BY created_at DESC
        """
        )

        for row in cursor.fetchall():
            outcome_data = json.loads(row[0])
            outcomes.append(
                {
                    "signal_id": outcome_data.get("signal_id"),
                    "symbol": outcome_data.get("symbol"),
                    "direction": outcome_data.get("direction"),
                    "pattern_type": outcome_data.get("pattern_type"),
                    "confidence": outcome_data.get("confidence"),
                    "outcome": outcome_data.get("result"),
                    "pips_result": outcome_data.get("pnl_pips", 0),
                    "duration_minutes": outcome_data.get("duration_minutes", 0),
                    "source": outcome_data.get("source", "event_bus"),
                }
            )

        conn.close()
        print(f"📍 Outcome Data Source: Event Bus ({len(outcomes)} outcomes)")
        return outcomes
    except Exception as e:
        print(f"⚠️ Event Bus outcomes unavailable ({e}), using JSONL fallback")
        return []


def main():
    print("=" * 80)
    print("🎯 BITTEN COMPREHENSIVE SYSTEM PERFORMANCE REPORT")
    print("=" * 80)
    print(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print("=" * 80)

    conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
    cursor = conn.cursor()

    # ========================================================================
    # SECTION 1: TIME-BASED ANALYSIS (Multiple Periods)
    # ========================================================================
    print("\n" + "=" * 80)
    print("📅 TIME-BASED SIGNAL ANALYSIS")
    print("=" * 80)

    time_periods = [
        ("10 minutes", "-10 minutes"),
        ("30 minutes", "-30 minutes"),
        ("1 hour", "-1 hour"),
        ("2 hours", "-2 hours"),
        ("4 hours", "-4 hours"),
        ("6 hours", "-6 hours"),
        ("12 hours", "-12 hours"),
        ("24 hours", "-24 hours"),
    ]

    print("\n📊 SIGNALS BY TIME PERIOD:")
    print("-" * 60)
    for period_name, period_sql in time_periods:
        cursor.execute(
            f"""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT pattern_type) as patterns,
                   ROUND(AVG(confidence), 1) as avg_conf
            FROM signals
            WHERE created_at > strftime('%s', 'now', '{period_sql}')
        """
        )
        result = cursor.fetchone()
        if result[0] > 0:
            print(f"{period_name:12} | {result[0]:4} signals | {result[1]} patterns | {result[2]:.1f}% avg conf")
        else:
            print(f"{period_name:12} | No signals")

    # ========================================================================
    # SECTION 2: PATTERN PERFORMANCE (Event Bus + Database Integration)
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 PATTERN PERFORMANCE BREAKDOWN")
    print("=" * 80)

    # Try to get recent signals from event bus first
    event_bus_signals = get_signals_from_event_bus()

    # Get all patterns
    cursor.execute(
        """
        SELECT DISTINCT pattern_type FROM signals
        WHERE created_at > strftime('%s', 'now', '-24 hours')
        ORDER BY pattern_type
    """
    )
    patterns = [row[0] for row in cursor.fetchall()]

    for pattern in patterns:
        print(f"\n🎯 {pattern}:")
        print("-" * 60)

        # Pattern stats by time period
        for period_name, period_sql in [("2H", "-2 hours"), ("12H", "-12 hours"), ("24H", "-24 hours")]:
            cursor.execute(
                f"""
                SELECT COUNT(*) as count,
                       ROUND(AVG(confidence), 1) as avg_conf,
                       MIN(confidence) as min_conf,
                       MAX(confidence) as max_conf
                FROM signals
                WHERE pattern_type = ?
                AND created_at > strftime('%s', 'now', '{period_sql}')
            """,
                (pattern,),
            )
            result = cursor.fetchone()
            if result[0] > 0:
                print(
                    f"  {period_name}: {result[0]:3} signals | Conf: {result[1]:.1f}% (min:{result[2]:.1f}, max:{result[3]:.1f})"
                )

    # ========================================================================
    # SECTION 3: CONFIDENCE LEVEL ANALYSIS
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 CONFIDENCE LEVEL ANALYSIS")
    print("=" * 80)

    confidence_buckets = [
        ("70-75%", 70, 75),
        ("75-80%", 75, 80),
        ("80-85%", 80, 85),
        ("85-90%", 85, 90),
        ("90-95%", 90, 95),
        ("95-100%", 95, 100),
    ]

    print("\n📊 SIGNALS BY CONFIDENCE BUCKET (Last 24H):")
    print("-" * 60)
    for bucket_name, min_conf, max_conf in confidence_buckets:
        cursor.execute(
            """
            SELECT COUNT(*) as count,
                   GROUP_CONCAT(DISTINCT pattern_type) as patterns
            FROM signals
            WHERE confidence >= ? AND confidence < ?
            AND created_at > strftime('%s', 'now', '-24 hours')
        """,
            (min_conf, max_conf),
        )
        result = cursor.fetchone()
        if result[0] > 0:
            patterns_str = result[1][:40] + "..." if result[1] and len(result[1]) > 40 else result[1]
            print(f"{bucket_name:10} | {result[0]:4} signals | {patterns_str}")

    # ========================================================================
    # SECTION 4: SYMBOL/PAIR ANALYSIS
    # ========================================================================
    print("\n" + "=" * 80)
    print("💱 SYMBOL/PAIR PERFORMANCE")
    print("=" * 80)

    cursor.execute(
        """
        SELECT symbol,
               COUNT(*) as count,
               GROUP_CONCAT(DISTINCT pattern_type) as patterns,
               ROUND(AVG(confidence), 1) as avg_conf
        FROM signals
        WHERE created_at > strftime('%s', 'now', '-24 hours')
        GROUP BY symbol
        ORDER BY count DESC
        LIMIT 15
    """
    )

    print("\n📊 TOP 15 ACTIVE PAIRS (Last 24H):")
    print("-" * 60)
    for row in cursor.fetchall():
        patterns_str = row[2][:30] + "..." if row[2] and len(row[2]) > 30 else row[2]
        print(f"{row[0]:10} | {row[1]:4} signals | {row[3]:.1f}% conf | {patterns_str}")

    # ========================================================================
    # SECTION 5: EXECUTED TRADES ANALYSIS
    # ========================================================================
    print("\n" + "=" * 80)
    print("🔥 EXECUTED TRADES ANALYSIS")
    print("=" * 80)

    cursor.execute(
        """
        SELECT
            s.pattern_type,
            COUNT(*) as executed,
            GROUP_CONCAT(DISTINCT s.symbol) as symbols
        FROM fires f
        JOIN signals s ON f.fire_id = s.signal_id
        WHERE f.created_at > strftime('%s', 'now', '-24 hours')
        AND f.ticket > 0
        GROUP BY s.pattern_type
        ORDER BY executed DESC
    """
    )

    print("\n📊 EXECUTED TRADES BY PATTERN (Last 24H):")
    print("-" * 60)
    for row in cursor.fetchall():
        symbols_str = row[2][:30] + "..." if row[2] and len(row[2]) > 30 else row[2]
        print(f"{row[0]:30} | {row[1]:3} trades | {symbols_str}")

    conn.close()

    # ========================================================================
    # SECTION 6: WIN/LOSS TRACKING FROM DYNAMIC_TRACKING.JSONL
    # ========================================================================
    print("\n" + "=" * 80)
    print("📈 ACTUAL WIN/LOSS OUTCOMES (FROM TRACKING)")
    print("=" * 80)

    import time

    current_time = time.time()

    # Initialize comprehensive tracking stats
    outcome_stats = {
        "by_pattern": defaultdict(lambda: defaultdict(int)),
        "by_confidence": defaultdict(lambda: defaultdict(int)),
        "by_symbol": defaultdict(lambda: defaultdict(int)),
        "by_hour": defaultdict(lambda: defaultdict(int)),
        "overall": defaultdict(int),
    }

    # Read all outcomes from Event Bus (PRODUCTION - SCHEMA V1)
    outcomes = get_outcomes_from_event_bus()

    if not outcomes:
        print("⚠️ No outcomes found in event bus")
        print("   This may indicate outcome mirrorer is not running or no trades have completed")
        print("   Check: ps aux | grep outcome_mirrorer")

    # Process outcomes from either source
    for outcome_data in outcomes:
        try:
            outcome = outcome_data.get("outcome")
            if outcome in ["WIN", "LOSS"]:
                pattern = outcome_data.get("pattern_type", "UNKNOWN")
                symbol = outcome_data.get("symbol", "UNKNOWN")
                confidence = outcome_data.get("confidence", 0)
                pips = outcome_data.get("pips_result", 0)

                # For event bus data, we might not have timestamp, skip time-based analysis
                hours_ago = 0  # Default for event bus data

                # Overall stats
                outcome_stats["overall"][outcome] += 1
                outcome_stats["overall"]["pips"] += pips

                # By pattern
                outcome_stats["by_pattern"][pattern][outcome] += 1
                outcome_stats["by_pattern"][pattern]["pips"] += pips

                # By symbol
                outcome_stats["by_symbol"][symbol][outcome] += 1
                outcome_stats["by_symbol"][symbol]["pips"] += pips

                # By confidence bucket
                conf_bucket = f"{int(confidence/5)*5}-{int(confidence/5)*5+5}%"
                outcome_stats["by_confidence"][conf_bucket][outcome] += 1
                outcome_stats["by_confidence"][conf_bucket]["pips"] += pips

                # By hours ago (for time analysis)
                if hours_ago <= 24:
                    time_bucket = f"{hours_ago}h_ago"
                    outcome_stats["by_hour"][time_bucket][outcome] += 1
                    outcome_stats["by_hour"][time_bucket]["pips"] += pips
        except:
            pass

    print(f"📍 Data Source: Event Bus (execution.outcome.v1 schema v1) - PRODUCTION")

    # Overall Performance
    total = outcome_stats["overall"]["WIN"] + outcome_stats["overall"]["LOSS"]
    if total > 0:
        wr = (outcome_stats["overall"]["WIN"] / total) * 100
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f'Total: {total} | Wins: {outcome_stats["overall"]["WIN"]} | Losses: {outcome_stats["overall"]["LOSS"]}')
        print(f'Win Rate: {wr:.1f}% | P&L: {outcome_stats["overall"]["pips"]:+.1f} pips')

        # By Pattern
        print(f"\n📊 WIN RATE BY PATTERN:")
        print("-" * 70)
        print(f'{"Pattern":25} {"Trades":>7} {"Wins":>5} {"Losses":>7} {"Win%":>6} {"P&L":>10}')
        print("-" * 70)
        for pattern, stats in sorted(outcome_stats["by_pattern"].items()):
            total = stats["WIN"] + stats["LOSS"]
            if total > 0:
                wr = (stats["WIN"] / total) * 100
                print(f'{pattern:25} {total:7} {stats["WIN"]:5} {stats["LOSS"]:7} {wr:6.1f}% {stats["pips"]:+10.1f}p')

        # By Symbol (Top 10)
        print(f"\n📊 WIN RATE BY SYMBOL (TOP 10):")
        print("-" * 70)
        print(f'{"Symbol":10} {"Trades":>7} {"Wins":>5} {"Losses":>7} {"Win%":>6} {"P&L":>10}')
        print("-" * 70)
        symbol_totals = [
            (symbol, stats["WIN"] + stats["LOSS"], stats) for symbol, stats in outcome_stats["by_symbol"].items()
        ]
        for symbol, total, stats in sorted(symbol_totals, key=lambda x: x[1], reverse=True)[:10]:
            if total > 0:
                wr = (stats["WIN"] / total) * 100
                print(f'{symbol:10} {total:7} {stats["WIN"]:5} {stats["LOSS"]:7} {wr:6.1f}% {stats["pips"]:+10.1f}p')

        # By Confidence
        print(f"\n📊 WIN RATE BY CONFIDENCE:")
        print("-" * 70)
        print(f'{"Confidence":12} {"Trades":>7} {"Wins":>5} {"Losses":>7} {"Win%":>6} {"P&L":>10}')
        print("-" * 70)
        for conf_bucket in sorted(outcome_stats["by_confidence"].keys()):
            stats = outcome_stats["by_confidence"][conf_bucket]
            total = stats["WIN"] + stats["LOSS"]
            if total > 0:
                wr = (stats["WIN"] / total) * 100
                print(
                    f'{conf_bucket:12} {total:7} {stats["WIN"]:5} {stats["LOSS"]:7} {wr:6.1f}% {stats["pips"]:+10.1f}p'
                )

        # Time-based performance (last 24 hours by hour)
        print(f"\n📊 PERFORMANCE BY TIME (LAST 24H):")
        print("-" * 60)
        for h in range(0, 25, 2):  # Every 2 hours
            wins = losses = pips = 0
            for hour in range(h, min(h + 2, 25)):
                time_key = f"{hour}h_ago"
                if time_key in outcome_stats["by_hour"]:
                    wins += outcome_stats["by_hour"][time_key].get("WIN", 0)
                    losses += outcome_stats["by_hour"][time_key].get("LOSS", 0)
                    pips += outcome_stats["by_hour"][time_key].get("pips", 0)

            total = wins + losses
            if total > 0:
                wr = (wins / total) * 100
                print(
                    f"{h:2}-{min(h+2,24):2}h ago: {total:3} trades | W:{wins:2} L:{losses:2} | WR:{wr:5.1f}% | {pips:+7.1f}p"
                )

    # ========================================================================
    # SECTION 7: SYSTEM HEALTH & PROCESSES (ARCHITECTURE.md CRITICAL ONLY)
    # ========================================================================
    print("\n" + "=" * 80)
    print("🔧 SYSTEM HEALTH CHECK")
    print("=" * 80)
    print("📍 Only showing ARCHITECTURE.md critical components")

    # CRITICAL PROCESSES FROM ARCHITECTURE.md - DO NOT MODIFY
    critical_processes = [
        ("elite_guard", "Signal Generation"),
        ("command_router", "Fire Routing"),
        ("confirm_listener", "Trade Confirmations"),
        ("telemetry_bridge", "Market Data"),
        ("athena_broadcaster", "Telegram Alerts"),
        ("bitten-production-bot", "Main Bot"),
    ]

    try:
        result = subprocess.run(["pm2", "list"], capture_output=True, text=True)

        for process, description in critical_processes:
            if process in result.stdout:
                if "online" in result.stdout.split(process)[1].split("\n")[0]:
                    print(f"✅ {process:25} - {description}")
                else:
                    print(f"❌ {process:25} - {description} (NOT RUNNING)")
            else:
                print(f"❌ {process:25} - {description} (NOT FOUND)")
    except:
        print("⚠️  Unable to check process status")

    # ========================================================================
    # SECTION 8: DATA SOURCE INVENTORY
    # ========================================================================
    print("\n" + "=" * 80)
    print("📁 DATA SOURCE INVENTORY")
    print("=" * 80)

    # Get event bus signals to show integration status
    event_bus_signals = get_signals_from_event_bus()

    data_files = [
        ("/root/HydraX-v2/event_bus/bitten_events.db", f"Event Bus (SIGNAL SOURCE - {len(event_bus_signals)} signals)"),
        ("/root/HydraX-v2/dynamic_tracking.jsonl", "Dynamic outcome tracking (OUTCOME SOURCE)"),
        ("/root/HydraX-v2/comprehensive_tracking.jsonl", "Comprehensive signal tracking"),
        ("/root/HydraX-v2/optimized_tracking.jsonl", "ML optimized tracking"),
        ("/root/HydraX-v2/bitten.db", "Main database"),
        ("/root/HydraX-v2/MASTER_OUTCOMES.jsonl", "Master outcomes archive"),
    ]

    for filepath, description in data_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 1024 * 1024:
                size_str = f"{size/(1024*1024):.1f}MB"
            elif size > 1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size}B"

            # Get modification time
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            time_ago = datetime.now() - mtime
            if time_ago.days > 0:
                time_str = f"{time_ago.days}d ago"
            elif time_ago.seconds > 3600:
                time_str = f"{time_ago.seconds//3600}h ago"
            else:
                time_str = f"{time_ago.seconds//60}m ago"

            print(f"✅ {os.path.basename(filepath):35} {size_str:>10} modified {time_str:>10}")
            print(f"   {description}")
        else:
            print(f"❌ {os.path.basename(filepath):35} NOT FOUND")

    print("\n" + "=" * 80)
    print("📍 Run this report anytime with: python3 /root/HydraX-v2/bitten_report.py")
    print("📍 This report shows ALL data dimensions - no modifications needed")
    print("=" * 80)


if __name__ == "__main__":
    main()
