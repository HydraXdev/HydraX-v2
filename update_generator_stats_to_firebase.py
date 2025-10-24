#!/usr/bin/env python3
"""
Update generator performance stats to Firebase Firestore
Reads from unified_tracking.jsonl and updates signal_generators collection
"""

import json
import time
import sqlite3
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
try:
    cred = credentials.Certificate('/root/bitten-firebase-sa.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialized")
except Exception as e:
    print(f"❌ Firebase init failed: {e}")
    exit(1)

def get_generator_stats(signal_prefix, name):
    """Get stats for a generator from database"""
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()

        # Get 24h signal count and avg confidence
        cursor.execute("""
            SELECT
                COUNT(*) as signals_24h,
                AVG(confidence) as avg_confidence,
                MAX(created_at) as last_signal_time
            FROM signals
            WHERE signal_id LIKE ? || '%'
            AND created_at > strftime('%s', 'now', '-24 hours')
        """, (signal_prefix,))

        result = cursor.fetchone()
        signals_24h = result[0] if result else 0
        avg_confidence = round(result[1], 1) if result and result[1] else 0.0
        last_signal_time = result[2] if result and result[2] else None

        # Get win rate from signals with outcomes
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses
            FROM signals
            WHERE signal_id LIKE ? || '%'
            AND outcome IN ('WIN', 'LOSS')
            AND created_at > strftime('%s', 'now', '-7 days')
        """, (signal_prefix,))

        result = cursor.fetchone()
        wins = result[0] if result else 0
        losses = result[1] if result else 0
        win_rate = round((wins / (wins + losses)) * 100, 1) if (wins + losses) > 0 else 0.0

        conn.close()

        # Determine status
        if last_signal_time:
            age_seconds = int(time.time()) - last_signal_time
            if age_seconds < 3600:  # Last signal < 1 hour
                status = 'online'
            elif age_seconds < 7200:  # Last signal < 2 hours
                status = 'degraded'
            else:
                status = 'offline'
        else:
            status = 'offline'

        return {
            'signals_24h': signals_24h,
            'win_rate': win_rate,
            'avg_confidence': avg_confidence,
            'status': status,
            'last_signal_time': last_signal_time,
            'last_updated': firestore.SERVER_TIMESTAMP
        }

    except Exception as e:
        print(f"❌ Error getting stats for {name}: {e}")
        return None

def update_firestore():
    """Update Firestore with generator stats"""

    # Elite Guard stats
    elite_stats = get_generator_stats('ELITE', 'Elite Guard')
    if elite_stats:
        db.collection('signal_generators').document('ELITE_GUARD').set(elite_stats, merge=True)
        print(f"✅ Updated ELITE_GUARD: {elite_stats['signals_24h']} signals, {elite_stats['win_rate']}% WR, status={elite_stats['status']}")

    # PULSE/RapidPulse stats (note: UI looks for RAPIDPULSE document)
    pulse_stats = get_generator_stats('PULSE', 'PULSE Scalper')
    if pulse_stats:
        db.collection('signal_generators').document('RAPIDPULSE').set(pulse_stats, merge=True)
        print(f"✅ Updated RAPIDPULSE: {pulse_stats['signals_24h']} signals, {pulse_stats['win_rate']}% WR, status={pulse_stats['status']}")

    # APEX Sentinel stats (note: UI looks for APEX_SENTINEL document)
    apex_stats = get_generator_stats('APEX', 'APEX Sentinel')
    if apex_stats:
        db.collection('signal_generators').document('APEX_SENTINEL').set(apex_stats, merge=True)
        print(f"✅ Updated APEX_SENTINEL: {apex_stats['signals_24h']} signals, {apex_stats['win_rate']}% WR, status={apex_stats['status']}")

if __name__ == '__main__':
    import sys

    # Support running as daemon with --loop flag
    if '--loop' in sys.argv:
        print("🔄 Starting generator stats updater daemon (60s interval)...")
        while True:
            try:
                update_firestore()
                time.sleep(60)  # Update every 60 seconds
            except KeyboardInterrupt:
                print("\n⚠️ Shutdown signal received")
                break
            except Exception as e:
                print(f"❌ Error in update loop: {e}")
                time.sleep(60)
    else:
        print("🔄 Updating generator stats to Firebase...")
        update_firestore()
        print("✅ Firebase update complete")
