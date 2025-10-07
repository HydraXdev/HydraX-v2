#!/usr/bin/env python3
"""
Enhanced position tracking module for webapp v2.07H
Consumes position_snapshots, hybrid_events, and position_closures
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
import logging
from flask import jsonify, request

logger = logging.getLogger(__name__)

DB = "/root/HydraX-v2/bitten.db"

def get_latest_positions(uuid):
    """Get latest position snapshot for a user"""
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

        # Get latest snapshot
        cur.execute("""
            SELECT positions_json, balance, equity, margin, margin_level,
                   free_margin, open_positions, hybrid_positions, timestamp
            FROM position_snapshots
            WHERE uuid = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (uuid,))

        result = cur.fetchone()
        if not result:
            return None

        positions = json.loads(result[0]) if result[0] else []

        # Enrich with hybrid events
        for pos in positions:
            ticket = pos.get('ticket')
            if ticket:
                # Get hybrid events for this position
                cur.execute("""
                    SELECT event_type, volume, pips, timestamp
                    FROM hybrid_events
                    WHERE ticket = ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                """, (ticket,))

                pos['hybrid_events'] = [
                    {
                        'type': row[0],
                        'volume': row[1],
                        'pips': row[2],
                        'time': row[3]
                    }
                    for row in cur.fetchall()
                ]

        con.close()

        return {
            'positions': positions,
            'balance': result[1],
            'equity': result[2],
            'margin': result[3],
            'margin_level': result[4],
            'free_margin': result[5],
            'open_positions': result[6],
            'hybrid_positions': result[7],
            'timestamp': result[8],
            'age_seconds': int(time.time() - result[8]) if result[8] else None
        }

    except Exception as e:
        logger.error(f"Error getting position snapshot: {e}")
        return None

def get_position_closures(uuid, hours=24):
    """Get recent position closures for a user"""
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

        since = int(time.time() - (hours * 3600))

        cur.execute("""
            SELECT ticket, fire_id, symbol, volume, open_price, close_price,
                   profit, reason, timestamp, duration_seconds, pips_gained
            FROM position_closures
            WHERE uuid = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (uuid, since))

        closures = []
        for row in cur.fetchall():
            closures.append({
                'ticket': row[0],
                'fire_id': row[1],
                'symbol': row[2],
                'volume': row[3],
                'open_price': row[4],
                'close_price': row[5],
                'profit': row[6],
                'reason': row[7],  # TP_HIT, SL_HIT, MANUAL, STOP_OUT
                'timestamp': row[8],
                'duration_seconds': row[9],
                'pips_gained': row[10],
                'time_ago': format_time_ago(row[8])
            })

        con.close()
        return closures

    except Exception as e:
        logger.error(f"Error getting position closures: {e}")
        return []

def get_hybrid_statistics(uuid, hours=24):
    """Get hybrid position management statistics"""
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

        since = int(time.time() - (hours * 3600))

        # Count hybrid events by type
        cur.execute("""
            SELECT event_type, COUNT(*) as count, SUM(volume) as total_volume,
                   AVG(pips) as avg_pips
            FROM hybrid_events
            WHERE uuid = ? AND timestamp > ?
            GROUP BY event_type
        """, (uuid, since))

        stats = {}
        for row in cur.fetchall():
            stats[row[0]] = {
                'count': row[1],
                'total_volume': row[2],
                'avg_pips': row[3]
            }

        # Count closure reasons
        cur.execute("""
            SELECT reason, COUNT(*) as count, SUM(profit) as total_profit,
                   AVG(profit) as avg_profit
            FROM position_closures
            WHERE uuid = ? AND timestamp > ?
            GROUP BY reason
        """, (uuid, since))

        closure_stats = {}
        for row in cur.fetchall():
            closure_stats[row[0]] = {
                'count': row[1],
                'total_profit': row[2],
                'avg_profit': row[3]
            }

        con.close()

        return {
            'hybrid_events': stats,
            'closure_reasons': closure_stats,
            'period_hours': hours
        }

    except Exception as e:
        logger.error(f"Error getting hybrid statistics: {e}")
        return {'hybrid_events': {}, 'closure_reasons': {}}

def get_trade_analytics(uuid, date=None):
    """Get trade analytics for a specific date"""
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        cur.execute("""
            SELECT total_trades, winning_trades, losing_trades, total_volume,
                   total_profit, total_pips, best_trade, worst_trade,
                   avg_win, avg_loss, win_rate, expectancy,
                   hybrid_partials, trail_updates
            FROM trade_analytics
            WHERE uuid = ? AND date = ?
        """, (uuid, date))

        result = cur.fetchone()
        if not result:
            return None

        con.close()

        return {
            'date': date,
            'total_trades': result[0],
            'winning_trades': result[1],
            'losing_trades': result[2],
            'total_volume': result[3],
            'total_profit': result[4],
            'total_pips': result[5],
            'best_trade': result[6],
            'worst_trade': result[7],
            'avg_win': result[8],
            'avg_loss': result[9],
            'win_rate': result[10],
            'expectancy': result[11],
            'hybrid_partials': result[12],
            'trail_updates': result[13]
        }

    except Exception as e:
        logger.error(f"Error getting trade analytics: {e}")
        return None

def get_ea_telemetry(uuid):
    """Get EA telemetry and health status"""
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()

        cur.execute("""
            SELECT node_id, account, broker, server, currency,
                   symbols_monitored, ticks_processed, hybrid_positions,
                   version, hybrid_enabled, socket_type,
                   last_heartbeat, last_handshake, last_metrics
            FROM ea_telemetry
            WHERE uuid = ?
        """, (uuid,))

        result = cur.fetchone()
        if not result:
            return None

        con.close()

        now = int(time.time())
        return {
            'node_id': result[0],
            'account': result[1],
            'broker': result[2],
            'server': result[3],
            'currency': result[4],
            'symbols_monitored': result[5],
            'ticks_processed': result[6],
            'hybrid_positions': result[7],
            'version': result[8],
            'hybrid_enabled': result[9],
            'socket_type': result[10],
            'last_heartbeat': result[11],
            'last_handshake': result[12],
            'last_metrics': result[13],
            'heartbeat_age': now - result[11] if result[11] else None,
            'metrics_age': now - result[13] if result[13] else None,
            'is_connected': (now - result[11] < 120) if result[11] else False
        }

    except Exception as e:
        logger.error(f"Error getting EA telemetry: {e}")
        return None

def format_time_ago(timestamp):
    """Format timestamp as human-readable time ago"""
    if not timestamp:
        return "Never"

    now = int(time.time())
    diff = now - timestamp

    if diff < 60:
        return f"{diff}s ago"
    elif diff < 3600:
        return f"{diff // 60}m ago"
    elif diff < 86400:
        return f"{diff // 3600}h ago"
    else:
        return f"{diff // 86400}d ago"

def register_v207_routes(app):
    """Register v2.07H position tracking routes with Flask app"""

    @app.route('/api/v207/positions/<uuid>')
    def api_v207_positions(uuid):
        """Get latest position snapshot"""
        data = get_latest_positions(uuid)
        if data:
            return jsonify(data)
        return jsonify({'error': 'No position data found'}), 404

    @app.route('/api/v207/closures/<uuid>')
    def api_v207_closures(uuid):
        """Get recent position closures"""
        hours = request.args.get('hours', 24, type=int)
        data = get_position_closures(uuid, hours)
        return jsonify({'closures': data, 'hours': hours})

    @app.route('/api/v207/hybrid/<uuid>')
    def api_v207_hybrid(uuid):
        """Get hybrid position statistics"""
        hours = request.args.get('hours', 24, type=int)
        data = get_hybrid_statistics(uuid, hours)
        return jsonify(data)

    @app.route('/api/v207/analytics/<uuid>')
    def api_v207_analytics(uuid):
        """Get trade analytics"""
        date = request.args.get('date')
        data = get_trade_analytics(uuid, date)
        if data:
            return jsonify(data)
        return jsonify({'error': 'No analytics data found'}), 404

    @app.route('/api/v207/telemetry/<uuid>')
    def api_v207_telemetry(uuid):
        """Get EA telemetry"""
        data = get_ea_telemetry(uuid)
        if data:
            return jsonify(data)
        return jsonify({'error': 'No telemetry data found'}), 404

    @app.route('/api/v207/dashboard/<uuid>')
    def api_v207_dashboard(uuid):
        """Combined dashboard data for v2.07H"""
        positions = get_latest_positions(uuid)
        closures = get_position_closures(uuid, 24)
        hybrid = get_hybrid_statistics(uuid, 24)
        analytics = get_trade_analytics(uuid)
        telemetry = get_ea_telemetry(uuid)

        return jsonify({
            'positions': positions,
            'recent_closures': closures[:10],  # Last 10 closures
            'hybrid_stats': hybrid,
            'today_analytics': analytics,
            'ea_telemetry': telemetry,
            'timestamp': int(time.time())
        })

    logger.info("✅ v2.07H position tracking routes registered")

if __name__ == "__main__":
    # Test the functions
    test_uuid = "COMMANDER_DEV_001"

    print("\n📊 Testing v2.07H Position Tracking")
    print("=" * 50)

    # Test position snapshot
    positions = get_latest_positions(test_uuid)
    if positions:
        print(f"✅ Position Snapshot: {positions['open_positions']} open, "
              f"{positions['hybrid_positions']} hybrid")
        print(f"   Balance: ${positions['balance']:.2f}")
        print(f"   Equity: ${positions['equity']:.2f}")
    else:
        print("❌ No position snapshot found")

    # Test closures
    closures = get_position_closures(test_uuid)
    print(f"\n✅ Recent Closures: {len(closures)} found")
    for c in closures[:3]:
        print(f"   {c['symbol']} - {c['reason']} - P&L: ${c['profit']:.2f}")

    # Test hybrid stats
    stats = get_hybrid_statistics(test_uuid)
    print(f"\n✅ Hybrid Statistics:")
    for event_type, data in stats['hybrid_events'].items():
        print(f"   {event_type}: {data['count']} events")

    # Test analytics
    analytics = get_trade_analytics(test_uuid)
    if analytics:
        print(f"\n✅ Today's Analytics:")
        print(f"   Win Rate: {analytics['win_rate']:.1f}%")
        print(f"   Total P&L: ${analytics['total_profit']:.2f}")

    # Test telemetry
    telemetry = get_ea_telemetry(test_uuid)
    if telemetry:
        print(f"\n✅ EA Telemetry:")
        print(f"   Version: {telemetry['version']}")
        print(f"   Connected: {telemetry['is_connected']}")
        print(f"   Hybrid Enabled: {telemetry['hybrid_enabled']}")