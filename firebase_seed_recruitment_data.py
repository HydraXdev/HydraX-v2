#!/usr/bin/env python3
"""
BITTEN Recruitment System - Firebase Seed Data Script
Creates realistic test data for /system page analytics
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import random

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        cred = credentials.Certificate('/root/bitten-firebase-sa.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase Admin SDK initialized")
        return db
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return None

def seed_signal_generators(db):
    """Seed signal_generators collection"""
    generators = [
        {
            'id': 'ELITE_GUARD',
            'name': 'Elite Guard',
            'win_rate': 73.5,
            'total_signals': 120,
            'total_pips': 892,
            'active': True
        },
        {
            'id': 'RAPIDPULSE',
            'name': 'RapidPulse',
            'win_rate': 78.2,
            'total_signals': 45,
            'total_pips': 351,
            'active': True
        },
        {
            'id': 'CITADEL',
            'name': 'Citadel Shield',
            'win_rate': 71.8,
            'total_signals': 89,
            'total_pips': 624,
            'active': True
        }
    ]

    count = 0
    for gen in generators:
        doc_id = gen.pop('id')
        gen['updated_at'] = firestore.SERVER_TIMESTAMP
        db.collection('signal_generators').document(doc_id).set(gen)
        count += 1
        print(f"  → Created signal_generator: {doc_id}")

    return count

def seed_system_stats(db):
    """Seed system_stats collection"""
    stats = {
        'win_rate': 73.8,
        'total_fires': 3429,
        'total_pips': 12547,
        'total_profit': 47293,
        'top_pair': 'GBPJPY',
        'top_session': 'LONDON',
        'avg_hold_hours': 2.4,
        'best_pattern': 'Liq Sweep',
        'active_users': 247,
        'total_users': 1834,
        'uptime_days': 287,
        'updated_at': firestore.SERVER_TIMESTAMP
    }

    db.collection('system_stats').document('global').set(stats)
    print("  → Created system_stats: global")
    return 1

def seed_squad_stats(db):
    """Seed squad_stats collection (Top 10 users)"""
    users = [
        {'user_id': '7176191872', 'callsign': 'ALPHA_7', 'xp': 1247, 'recruits': 5, 'active': 5},
        {'user_id': '8923456789', 'callsign': 'DELTA_9', 'xp': 892, 'recruits': 3, 'active': 3},
        {'user_id': '9034567890', 'callsign': 'BRAVO_3', 'xp': 674, 'recruits': 2, 'active': 2},
        {'user_id': '8145678901', 'callsign': 'ECHO_12', 'xp': 521, 'recruits': 2, 'active': 1},
        {'user_id': '7256789012', 'callsign': 'FOXTROT_6', 'xp': 418, 'recruits': 1, 'active': 1},
        {'user_id': '6367890123', 'callsign': 'CHARLIE_4', 'xp': 387, 'recruits': 1, 'active': 1},
        {'user_id': '5478901234', 'callsign': 'GHOST_2', 'xp': 312, 'recruits': 1, 'active': 0},
        {'user_id': '4589012345', 'callsign': 'VIPER_8', 'xp': 289, 'recruits': 1, 'active': 1},
        {'user_id': '3690123456', 'callsign': 'NOMAD_5', 'xp': 254, 'recruits': 0, 'active': 0},
        {'user_id': '2701234567', 'callsign': 'SHADOW_11', 'xp': 198, 'recruits': 0, 'active': 0}
    ]

    def calculate_rank(recruits):
        """Calculate squad rank based on recruits"""
        if recruits >= 5: return 'COLONEL'
        elif recruits >= 3: return 'CAPTAIN'
        elif recruits >= 2: return 'SERGEANT'
        elif recruits >= 1: return 'CORPORAL'
        else: return 'PRIVATE'

    count = 0
    for user in users:
        doc_data = {
            'user_id': user['user_id'],
            'callsign': user['callsign'],
            'referral_code': user['callsign'],
            'total_recruits': user['recruits'],
            'active_recruits': user['active'],
            'total_xp_from_recruits': user['xp'],
            'squad_rank': calculate_rank(user['recruits']),
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        db.collection('squad_stats').document(user['user_id']).set(doc_data)
        count += 1
        print(f"  → Created squad_stats: {user['callsign']} ({user['recruits']} recruits)")

    return count

def seed_activity_feed(db):
    """Seed activity_feed collection (Last 10 events)"""
    now = datetime.utcnow()

    events = [
        {'type': 'signal', 'text': 'ELITE_GUARD: GBPJPY SELL @ 85%', 'minutes_ago': 5},
        {'type': 'fire', 'text': 'DELTA_9 fired EURUSD BUY', 'minutes_ago': 12},
        {'type': 'win', 'text': 'ALPHA_7 +12.5 pips on GBPJPY', 'minutes_ago': 18},
        {'type': 'signal', 'text': 'RAPIDPULSE: XAUUSD BUY @ 82%', 'minutes_ago': 23},
        {'type': 'recruit', 'text': 'BRAVO_3 recruited new operative', 'minutes_ago': 35},
        {'type': 'win', 'text': 'FOXTROT_6 +8.3 pips on EURUSD', 'minutes_ago': 42},
        {'type': 'fire', 'text': 'ECHO_12 fired GBPJPY SELL', 'minutes_ago': 58},
        {'type': 'signal', 'text': 'ELITE_GUARD: EURUSD BUY @ 79%', 'minutes_ago': 67},
        {'type': 'win', 'text': 'CHARLIE_4 +15.2 pips on XAUUSD', 'minutes_ago': 78},
        {'type': 'fire', 'text': 'VIPER_8 fired GBPUSD BUY', 'minutes_ago': 92}
    ]

    count = 0
    for i, event in enumerate(events):
        timestamp = now - timedelta(minutes=event['minutes_ago'])
        doc_data = {
            'type': event['type'],
            'text': event['text'],
            'timestamp': timestamp,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        # Use timestamp as document ID for ordering
        doc_id = f"event_{int(timestamp.timestamp())}_{i}"
        db.collection('activity_feed').document(doc_id).set(doc_data)
        count += 1
        print(f"  → Created activity_feed: {event['text'][:40]}...")

    return count

def seed_performance_stats(db):
    """Seed performance_stats collection"""

    # By session
    by_session = {
        'LONDON': {'win_rate': 78.5, 'signal_count': 450, 'avg_pips': 12.8},
        'NY': {'win_rate': 73.2, 'signal_count': 320, 'avg_pips': 11.3},
        'OVERLAP': {'win_rate': 71.9, 'signal_count': 180, 'avg_pips': 10.7},
        'ASIAN': {'win_rate': 65.4, 'signal_count': 120, 'avg_pips': 9.2}
    }
    db.collection('performance_stats').document('by_session').set(by_session)
    print("  → Created performance_stats: by_session")

    # By symbol
    by_symbol = {
        'GBPJPY': {'win_rate': 78.3, 'signal_count': 280, 'avg_pips': 15.4},
        'EURUSD': {'win_rate': 74.1, 'signal_count': 350, 'avg_pips': 11.2},
        'XAUUSD': {'win_rate': 72.6, 'signal_count': 190, 'avg_pips': 13.8},
        'GBPUSD': {'win_rate': 71.2, 'signal_count': 240, 'avg_pips': 12.5},
        'USDJPY': {'win_rate': 69.8, 'signal_count': 210, 'avg_pips': 10.9}
    }
    db.collection('performance_stats').document('by_symbol').set(by_symbol)
    print("  → Created performance_stats: by_symbol")

    # By pattern
    by_pattern = {
        'LIQUIDITY_SWEEP': {'win_rate': 76.5, 'signal_count': 340, 'avg_pips': 14.2},
        'ORDER_BLOCK': {'win_rate': 73.8, 'signal_count': 280, 'avg_pips': 12.6},
        'FAIR_VALUE_GAP': {'win_rate': 71.2, 'signal_count': 190, 'avg_pips': 11.8},
        'VCB_BREAKOUT': {'win_rate': 69.4, 'signal_count': 150, 'avg_pips': 10.4},
        'SWEEP_RETURN': {'win_rate': 68.1, 'signal_count': 110, 'avg_pips': 9.7}
    }
    db.collection('performance_stats').document('by_pattern').set(by_pattern)
    print("  → Created performance_stats: by_pattern")

    return 3

def seed_hourly_signal_volume(db):
    """Seed hourly signal volume data for chart"""
    now = datetime.utcnow()

    # Create 24 hours of data
    hourly_data = {}
    for hour in range(24):
        # Simulate realistic volume patterns (higher during trading sessions)
        base_volume = 10
        if 7 <= hour <= 16:  # London/NY sessions
            base_volume = 25
        elif 0 <= hour <= 3:  # Asian session
            base_volume = 15

        volume = base_volume + random.randint(-5, 10)
        hourly_data[f"hour_{hour:02d}"] = {
            'hour': hour,
            'signal_count': max(0, volume),
            'win_count': int(volume * 0.74)  # 74% win rate
        }

    db.collection('performance_stats').document('hourly_volume').set(hourly_data)
    print("  → Created performance_stats: hourly_volume (24 hours)")
    return 1

def main():
    """Main seed data execution"""
    print("\n" + "="*60)
    print("🌱 BITTEN RECRUITMENT SYSTEM - SEED DATA")
    print("="*60 + "\n")

    # Initialize Firebase
    db = initialize_firebase()
    if not db:
        print("\n❌ Failed to initialize Firebase. Exiting.")
        return

    total_docs = 0

    # Seed all collections
    print("\n📊 Seeding signal_generators collection...")
    total_docs += seed_signal_generators(db)

    print("\n📈 Seeding system_stats collection...")
    total_docs += seed_system_stats(db)

    print("\n👥 Seeding squad_stats collection...")
    total_docs += seed_squad_stats(db)

    print("\n📡 Seeding activity_feed collection...")
    total_docs += seed_activity_feed(db)

    print("\n📊 Seeding performance_stats collection...")
    total_docs += seed_performance_stats(db)

    print("\n📈 Seeding hourly signal volume...")
    total_docs += seed_hourly_signal_volume(db)

    # Summary
    print("\n" + "="*60)
    print("✅ SEED DATA COMPLETE")
    print("="*60)
    print(f"\n📦 Total documents created: {total_docs}")
    print("\n📋 Collection Summary:")
    print("  • signal_generators: 3 documents")
    print("  • system_stats: 1 document")
    print("  • squad_stats: 10 documents")
    print("  • activity_feed: 10 documents")
    print("  • performance_stats: 5 documents (by_session, by_symbol, by_pattern, hourly_volume)")
    print("\n🔗 View in Firebase Console:")
    print("  https://console.firebase.google.com/project/bitten-0420/firestore/data")
    print("\n✅ Data ready for /system page testing!")
    print("\n")

if __name__ == "__main__":
    main()
