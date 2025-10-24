#!/usr/bin/env python3
"""
BITTEN Firestore Initialization Script
Creates collections, sets up TTL, and verifies structure
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter


def init_firebase():
    """Initialize Firebase Admin SDK"""
    cred_path = "/root/bitten-firebase-sa.json"

    if not os.path.exists(cred_path):
        print(f"❌ Firebase credentials not found: {cred_path}")
        sys.exit(1)

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized")
        return firestore.client()
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        sys.exit(1)


def create_sample_user(db, user_id="7176191872"):
    """Create sample user document"""
    try:
        user_ref = db.collection('users').document(user_id)
        user_data = {
            'user_id': user_id,
            'balance': 850.45,
            'equity': 862.30,
            'tier': 'COMMANDER',
            'fire_mode': 'AUTO',
            'bitmode_enabled': True,
            'auto_fire_slots': 3,
            'last_updated': firestore.SERVER_TIMESTAMP
        }
        user_ref.set(user_data)
        print(f"✅ Created sample user: {user_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        return False


def create_sample_signal(db):
    """Create sample signal with TTL"""
    try:
        signal_id = f"ELITE_GUARD_EURUSD_{int(time.time())}"
        signal_ref = db.collection('signals').document(signal_id)

        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=24)

        signal_data = {
            'signal_id': signal_id,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.10500,
            'sl_pips': 20,
            'tp_pips': 30,
            'confidence': 85.5,
            'pattern_type': 'LIQUIDITY_SWEEP_REVERSAL',
            'signal_type': 'PRECISION_STRIKE',
            'citadel_score': 8.5,
            'status': 'ACTIVE',
            'created_at': created_at,
            'expires_at': expires_at,
            'ttl': expires_at  # For TTL policy
        }
        signal_ref.set(signal_data)
        print(f"✅ Created sample signal: {signal_id} (expires in 24h)")
        return signal_id
    except Exception as e:
        print(f"❌ Failed to create signal: {e}")
        return None


def create_sample_position(db, user_id="7176191872"):
    """Create sample position"""
    try:
        position_id = f"POS_{user_id}_{int(time.time())}"
        position_ref = db.collection('positions').document(position_id)

        position_data = {
            'position_id': position_id,
            'user_id': user_id,
            'ticket': 19059064,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'volume': 0.50,
            'open_price': 1.10500,
            'sl': 1.10300,
            'tp': 1.10800,
            'status': 'OPEN',
            'profit': 25.50,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        position_ref.set(position_data)
        print(f"✅ Created sample position: {position_id}")
        return position_id
    except Exception as e:
        print(f"❌ Failed to create position: {e}")
        return None


def create_sample_fire_history(db, user_id="7176191872", signal_id=None):
    """Create sample fire history entry"""
    try:
        fire_id = f"FIRE_{user_id}_{int(time.time())}"
        fire_ref = db.collection('fire_history').document(fire_id)

        fire_data = {
            'fire_id': fire_id,
            'user_id': user_id,
            'signal_id': signal_id or f"ELITE_GUARD_EURUSD_{int(time.time())}",
            'mission_id': f"MISSION_{int(time.time())}",
            'status': 'FILLED',
            'ticket': 19059064,
            'fill_price': 1.10500,
            'volume': 0.50,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        fire_ref.set(fire_data)
        print(f"✅ Created sample fire history: {fire_id}")
        return fire_id
    except Exception as e:
        print(f"❌ Failed to create fire history: {e}")
        return None


def create_system_stats(db):
    """Create system statistics document"""
    try:
        stats_ref = db.collection('system').document('stats')
        stats_data = {
            'total_signals': 0,
            'active_signals': 0,
            'total_fires': 0,
            'active_positions': 0,
            'total_users': 0,
            'last_updated': firestore.SERVER_TIMESTAMP
        }
        stats_ref.set(stats_data)
        print("✅ Created system stats document")
        return True
    except Exception as e:
        print(f"❌ Failed to create system stats: {e}")
        return False


def verify_collections(db):
    """Verify all collections were created"""
    print("\n🔍 Verifying collections...")

    collections = {
        'users': 0,
        'signals': 0,
        'positions': 0,
        'fire_history': 0,
        'system': 0
    }

    for collection_name in collections.keys():
        try:
            docs = db.collection(collection_name).limit(10).stream()
            count = sum(1 for _ in docs)
            collections[collection_name] = count
            print(f"  ✅ {collection_name}: {count} documents")
        except Exception as e:
            print(f"  ❌ {collection_name}: Error - {e}")

    return collections


def test_query_performance(db):
    """Test indexed queries"""
    print("\n🔍 Testing indexed queries...")

    try:
        # Test 1: Query signals by status and created_at
        start = time.time()
        signals = db.collection('signals')\
            .where(filter=FieldFilter('status', '==', 'ACTIVE'))\
            .order_by('created_at', direction=firestore.Query.DESCENDING)\
            .limit(10)\
            .stream()
        count = sum(1 for _ in signals)
        elapsed = time.time() - start
        print(f"  ✅ Query 1 (status + created_at): {count} results in {elapsed*1000:.2f}ms")

        # Test 2: Query signals by symbol and confidence
        start = time.time()
        signals = db.collection('signals')\
            .where(filter=FieldFilter('symbol', '==', 'EURUSD'))\
            .order_by('confidence', direction=firestore.Query.DESCENDING)\
            .limit(10)\
            .stream()
        count = sum(1 for _ in signals)
        elapsed = time.time() - start
        print(f"  ✅ Query 2 (symbol + confidence): {count} results in {elapsed*1000:.2f}ms")

        # Test 3: Query positions by user_id and status
        start = time.time()
        positions = db.collection('positions')\
            .where(filter=FieldFilter('user_id', '==', '7176191872'))\
            .where(filter=FieldFilter('status', '==', 'OPEN'))\
            .stream()
        count = sum(1 for _ in positions)
        elapsed = time.time() - start
        print(f"  ✅ Query 3 (user_id + status): {count} results in {elapsed*1000:.2f}ms")

        return True
    except Exception as e:
        print(f"  ❌ Query test failed: {e}")
        return False


def main():
    """Main initialization routine"""
    print("=" * 70)
    print("🔥 BITTEN FIRESTORE INITIALIZATION")
    print("=" * 70)

    # Initialize Firebase
    db = init_firebase()

    # Create sample documents
    print("\n📝 Creating sample documents...")
    user_created = create_sample_user(db)
    signal_id = create_sample_signal(db)
    position_created = create_sample_position(db)
    fire_created = create_sample_fire_history(db, signal_id=signal_id)
    stats_created = create_system_stats(db)

    # Verify collections
    collections = verify_collections(db)

    # Test queries
    test_query_performance(db)

    # Summary
    print("\n" + "=" * 70)
    print("📊 INITIALIZATION SUMMARY")
    print("=" * 70)
    print(f"Users: {collections['users']} documents")
    print(f"Signals: {collections['signals']} documents (24h TTL)")
    print(f"Positions: {collections['positions']} documents")
    print(f"Fire History: {collections['fire_history']} documents")
    print(f"System: {collections['system']} documents")
    print("\n✅ Firestore initialization complete!")
    print("\n📝 Next steps:")
    print("  1. Deploy security rules: firebase deploy --only firestore:rules")
    print("  2. Deploy indexes: firebase deploy --only firestore:indexes")
    print("  3. Run test script: python3 firestore/test_firestore.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
