#!/usr/bin/env python3
"""
BITTEN Admin API Server
Provides SQLite data endpoints for the Throne admin dashboard
"""

import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

DB_PATH = "/root/HydraX-v2/bitten.db"


def get_db_connection():
    """Create database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    """Convert sqlite3.Row to dict"""
    return dict(zip(row.keys(), row))


@app.route("/api/admin/stats", methods=["GET"])
def get_trading_stats():
    """Get trading statistics for the last 24 hours"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate 24 hours ago timestamp
        now = int(datetime.now().timestamp())
        day_ago = now - 86400

        # Total signals in last 24h
        cursor.execute(
            "SELECT COUNT(*) as count FROM signals WHERE created_at > ?",
            (day_ago,)
        )
        signals_24h = cursor.fetchone()["count"]

        # Total fires executed in last 24h
        cursor.execute(
            "SELECT COUNT(*) as count FROM fires WHERE created_at > ? AND status = 'FILLED'",
            (day_ago,)
        )
        fires_executed = cursor.fetchone()["count"]

        # Win rate calculation
        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses
            FROM signals
            WHERE created_at > ? AND outcome IS NOT NULL
            """,
            (day_ago,)
        )
        win_loss = cursor.fetchone()
        wins = win_loss["wins"] or 0
        losses = win_loss["losses"] or 0
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0.0

        # Total P&L from fires
        cursor.execute(
            """
            SELECT COALESCE(SUM(pnl), 0) as total_pnl
            FROM fires
            WHERE created_at > ? AND pnl IS NOT NULL
            """,
            (day_ago,)
        )
        total_pnl = cursor.fetchone()["total_pnl"] or 0.0

        # Average confidence
        cursor.execute(
            "SELECT COALESCE(AVG(confidence), 0) as avg_conf FROM signals WHERE created_at > ?",
            (day_ago,)
        )
        avg_confidence = cursor.fetchone()["avg_conf"] or 0.0

        conn.close()

        return jsonify({
            "signals_24h": signals_24h,
            "fires_executed": fires_executed,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_confidence": round(avg_confidence, 2),
        })

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/signals/recent", methods=["GET"])
def get_recent_signals():
    """Get recent signals with optional limit"""
    try:
        limit = request.args.get("limit", default=20, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                signal_id,
                symbol,
                direction,
                entry_price,
                stop_pips,
                target_pips,
                confidence,
                pattern_type,
                created_at,
                outcome,
                pips_result,
                session,
                risk_reward
            FROM signals
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        signals = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(signals)

    except Exception as e:
        print(f"Error fetching recent signals: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/patterns/performance", methods=["GET"])
def get_pattern_performance():
    """Get performance breakdown by pattern type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate 7 days ago for more data
        now = int(datetime.now().timestamp())
        week_ago = now - (7 * 86400)

        cursor.execute(
            """
            SELECT
                pattern_type,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                ROUND(AVG(confidence), 2) as avg_confidence,
                COALESCE(SUM(pips_result), 0) as total_pips
            FROM signals
            WHERE created_at > ? AND pattern_type IS NOT NULL
            GROUP BY pattern_type
            ORDER BY total_signals DESC
            """,
            (week_ago,)
        )

        patterns = []
        for row in cursor.fetchall():
            wins = row["wins"] or 0
            losses = row["losses"] or 0
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0.0

            patterns.append({
                "pattern_type": row["pattern_type"],
                "total_signals": row["total_signals"],
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 2),
                "avg_confidence": row["avg_confidence"] or 0.0,
                "total_pips": round(row["total_pips"] or 0.0, 2),
            })

        conn.close()

        return jsonify(patterns)

    except Exception as e:
        print(f"Error fetching pattern performance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/symbols/performance", methods=["GET"])
def get_symbol_performance():
    """Get performance breakdown by symbol"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Calculate 7 days ago for more data
        now = int(datetime.now().timestamp())
        week_ago = now - (7 * 86400)

        cursor.execute(
            """
            SELECT
                symbol,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                COALESCE(SUM(pips_result), 0) as total_pips
            FROM signals
            WHERE created_at > ? AND symbol IS NOT NULL
            GROUP BY symbol
            ORDER BY total_pips DESC
            LIMIT 10
            """,
            (week_ago,)
        )

        symbols = []
        for row in cursor.fetchall():
            wins = row["wins"] or 0
            losses = row["losses"] or 0
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0.0

            symbols.append({
                "symbol": row["symbol"],
                "total_signals": row["total_signals"],
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 2),
                "total_pips": round(row["total_pips"] or 0.0, 2),
            })

        conn.close()

        return jsonify(symbols)

    except Exception as e:
        print(f"Error fetching symbol performance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/fires/recent", methods=["GET"])
def get_recent_fires():
    """Get recent fire executions"""
    try:
        limit = request.args.get("limit", default=20, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                fire_id,
                mission_id,
                user_id,
                status,
                ticket,
                price,
                created_at,
                closed_at,
                pnl,
                symbol,
                direction,
                profit
            FROM fires
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )

        fires = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(fires)

    except Exception as e:
        print(f"Error fetching recent fires: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        conn.close()

        return jsonify({
            "status": "healthy",
            "database": "connected",
            "total_signals": count,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
        }), 500


if __name__ == "__main__":
    print("=" * 70)
    print("BITTEN ADMIN API SERVER")
    print("=" * 70)
    print(f"Database: {DB_PATH}")
    print(f"Port: 8893")
    print("Endpoints:")
    print("  GET /api/admin/stats - Trading statistics (24h)")
    print("  GET /api/admin/signals/recent?limit=20 - Recent signals")
    print("  GET /api/admin/patterns/performance - Pattern breakdown")
    print("  GET /api/admin/symbols/performance - Symbol breakdown")
    print("  GET /api/admin/fires/recent?limit=20 - Recent fires")
    print("  GET /api/admin/health - Health check")
    print("=" * 70)

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"⚠️  WARNING: Database not found at {DB_PATH}")
    else:
        print(f"✅ Database found at {DB_PATH}")

    app.run(host="0.0.0.0", port=8893, debug=True)
