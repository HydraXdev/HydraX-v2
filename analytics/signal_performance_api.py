#!/usr/bin/env python3
"""
Signal Performance Analytics API
Reads unified_tracking.jsonl and exposes performance metrics via REST endpoints
"""

import json
import logging
from collections import defaultdict
from datetime import datetime

import redis
from flask import Flask, jsonify, request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
LOG = logging.getLogger("ANALYTICS_API")

app = Flask(__name__)
CORS(app)

# Redis for caching (5min TTL)
try:
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    LOG.info("✅ Redis connected for caching")
except:
    REDIS_AVAILABLE = False
    LOG.warning("⚠️ Redis not available, caching disabled")

TRACKING_FILE = "/root/HydraX-v2/unified_tracking.jsonl"
CACHE_TTL = 300  # 5 minutes


def load_signals():
    """Load all signals from tracking file"""
    signals = []
    try:
        with open(TRACKING_FILE, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    signals.append(data)
                except json.JSONDecodeError:
                    continue
        LOG.info(f"📊 Loaded {len(signals)} signals from tracking file")
    except FileNotFoundError:
        LOG.warning(f"⚠️ Tracking file not found: {TRACKING_FILE}")
    return signals


def get_cached_or_compute(cache_key, compute_func):
    """Get from cache or compute and cache"""
    if REDIS_AVAILABLE:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    result = compute_func()

    if REDIS_AVAILABLE:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))

    return result


@app.route("/api/performance/by_pattern", methods=["GET"])
def performance_by_pattern():
    """Win rates per pattern type"""

    def compute():
        signals = load_signals()
        pattern_stats = defaultdict(
            lambda: {"total": 0, "wins": 0, "losses": 0, "pending": 0, "total_pips": 0, "total_lifespan": 0}
        )

        for sig in signals:
            pattern = sig.get("pattern_type", "UNKNOWN")
            outcome = sig.get("outcome", "PENDING")
            pips = sig.get("pips_result", 0)
            lifespan = sig.get("lifespan", 0)

            pattern_stats[pattern]["total"] += 1
            if outcome == "WIN":
                pattern_stats[pattern]["wins"] += 1
                pattern_stats[pattern]["total_pips"] += pips
                pattern_stats[pattern]["total_lifespan"] += lifespan
            elif outcome == "LOSS":
                pattern_stats[pattern]["losses"] += 1
                pattern_stats[pattern]["total_pips"] += pips
                pattern_stats[pattern]["total_lifespan"] += lifespan
            else:
                pattern_stats[pattern]["pending"] += 1

        # Calculate percentages
        results = []
        for pattern, stats in pattern_stats.items():
            completed = stats["wins"] + stats["losses"]
            win_rate = (stats["wins"] / completed * 100) if completed > 0 else 0
            avg_pips = (stats["total_pips"] / completed) if completed > 0 else 0
            avg_lifespan = (stats["total_lifespan"] / completed) if completed > 0 else 0

            results.append(
                {
                    "pattern": pattern,
                    "total": stats["total"],
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "pending": stats["pending"],
                    "win_rate": round(win_rate, 1),
                    "avg_pips": round(avg_pips, 1),
                    "avg_lifespan_min": round(avg_lifespan / 60, 1) if avg_lifespan > 0 else 0,
                }
            )

        return sorted(results, key=lambda x: x["total"], reverse=True)

    return jsonify(get_cached_or_compute("perf_by_pattern", compute))


@app.route("/api/performance/by_confidence", methods=["GET"])
def performance_by_confidence():
    """Win rates by confidence buckets"""

    def compute():
        signals = load_signals()
        conf_stats = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "pending": 0, "total_pips": 0})

        for sig in signals:
            conf = sig.get("confidence", 0)
            outcome = sig.get("outcome", "PENDING")
            pips = sig.get("pips_result", 0)

            # Determine bucket
            if conf < 70:
                bucket = "60-70"
            elif conf < 75:
                bucket = "70-75"
            elif conf < 80:
                bucket = "75-80"
            elif conf < 85:
                bucket = "80-85"
            elif conf < 90:
                bucket = "85-90"
            else:
                bucket = "90+"

            conf_stats[bucket]["total"] += 1
            if outcome == "WIN":
                conf_stats[bucket]["wins"] += 1
                conf_stats[bucket]["total_pips"] += pips
            elif outcome == "LOSS":
                conf_stats[bucket]["losses"] += 1
                conf_stats[bucket]["total_pips"] += pips
            else:
                conf_stats[bucket]["pending"] += 1

        results = []
        for bucket in ["60-70", "70-75", "75-80", "80-85", "85-90", "90+"]:
            if bucket in conf_stats:
                stats = conf_stats[bucket]
                completed = stats["wins"] + stats["losses"]
                win_rate = (stats["wins"] / completed * 100) if completed > 0 else 0
                avg_pips = (stats["total_pips"] / completed) if completed > 0 else 0

                results.append(
                    {
                        "confidence_range": bucket + "%",
                        "total": stats["total"],
                        "wins": stats["wins"],
                        "losses": stats["losses"],
                        "pending": stats["pending"],
                        "win_rate": round(win_rate, 1),
                        "avg_pips": round(avg_pips, 1),
                    }
                )

        return results

    return jsonify(get_cached_or_compute("perf_by_confidence", compute))


@app.route("/api/performance/by_session", methods=["GET"])
def performance_by_session():
    """Performance by trading session"""

    def compute():
        signals = load_signals()
        session_stats = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "pending": 0, "total_pips": 0})

        for sig in signals:
            session = sig.get("session", "UNKNOWN")
            outcome = sig.get("outcome", "PENDING")
            pips = sig.get("pips_result", 0)

            session_stats[session]["total"] += 1
            if outcome == "WIN":
                session_stats[session]["wins"] += 1
                session_stats[session]["total_pips"] += pips
            elif outcome == "LOSS":
                session_stats[session]["losses"] += 1
                session_stats[session]["total_pips"] += pips
            else:
                session_stats[session]["pending"] += 1

        results = []
        for session, stats in session_stats.items():
            completed = stats["wins"] + stats["losses"]
            win_rate = (stats["wins"] / completed * 100) if completed > 0 else 0
            avg_pips = (stats["total_pips"] / completed) if completed > 0 else 0

            results.append(
                {
                    "session": session,
                    "total": stats["total"],
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "pending": stats["pending"],
                    "win_rate": round(win_rate, 1),
                    "avg_pips": round(avg_pips, 1),
                }
            )

        return sorted(results, key=lambda x: x["total"], reverse=True)

    return jsonify(get_cached_or_compute("perf_by_session", compute))


@app.route("/api/performance/by_pair", methods=["GET"])
def performance_by_pair():
    """Performance by currency pair"""

    def compute():
        signals = load_signals()
        pair_stats = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "pending": 0, "total_pips": 0})

        for sig in signals:
            symbol = sig.get("symbol", "UNKNOWN")
            outcome = sig.get("outcome", "PENDING")
            pips = sig.get("pips_result", 0)

            pair_stats[symbol]["total"] += 1
            if outcome == "WIN":
                pair_stats[symbol]["wins"] += 1
                pair_stats[symbol]["total_pips"] += pips
            elif outcome == "LOSS":
                pair_stats[symbol]["losses"] += 1
                pair_stats[symbol]["total_pips"] += pips
            else:
                pair_stats[symbol]["pending"] += 1

        results = []
        for symbol, stats in pair_stats.items():
            completed = stats["wins"] + stats["losses"]
            win_rate = (stats["wins"] / completed * 100) if completed > 0 else 0
            avg_pips = (stats["total_pips"] / completed) if completed > 0 else 0

            results.append(
                {
                    "symbol": symbol,
                    "total": stats["total"],
                    "wins": stats["wins"],
                    "losses": stats["losses"],
                    "pending": stats["pending"],
                    "win_rate": round(win_rate, 1),
                    "avg_pips": round(avg_pips, 1),
                }
            )

        return sorted(results, key=lambda x: x["total"], reverse=True)

    return jsonify(get_cached_or_compute("perf_by_pair", compute))


@app.route("/api/performance/time_analysis", methods=["GET"])
def time_analysis():
    """Average lifespan for wins vs losses"""

    def compute():
        signals = load_signals()
        win_lifespans = []
        loss_lifespans = []

        for sig in signals:
            outcome = sig.get("outcome", "PENDING")
            lifespan = sig.get("lifespan", 0)

            if outcome == "WIN" and lifespan > 0:
                win_lifespans.append(lifespan)
            elif outcome == "LOSS" and lifespan > 0:
                loss_lifespans.append(lifespan)

        avg_win_lifespan = (sum(win_lifespans) / len(win_lifespans)) if win_lifespans else 0
        avg_loss_lifespan = (sum(loss_lifespans) / len(loss_lifespans)) if loss_lifespans else 0

        return {
            "avg_win_lifespan_min": round(avg_win_lifespan / 60, 1),
            "avg_loss_lifespan_min": round(avg_loss_lifespan / 60, 1),
            "total_wins": len(win_lifespans),
            "total_losses": len(loss_lifespans),
        }

    return jsonify(get_cached_or_compute("time_analysis", compute))


@app.route("/api/performance/recent", methods=["GET"])
def recent_signals():
    """Last 100 signals with full details"""
    limit = request.args.get("limit", 100, type=int)

    signals = load_signals()
    recent = signals[-limit:] if len(signals) > limit else signals
    recent.reverse()  # Most recent first

    return jsonify(recent)


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    signals = load_signals()
    return jsonify(
        {
            "status": "healthy",
            "total_signals": len(signals),
            "redis_available": REDIS_AVAILABLE,
            "tracking_file": TRACKING_FILE,
        }
    )


if __name__ == "__main__":
    LOG.info("🚀 Starting Signal Performance Analytics API on port 8892")
    app.run(host="0.0.0.0", port=8892, debug=False)
