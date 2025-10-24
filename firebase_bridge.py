#!/usr/bin/env python3
"""
Firebase Bridge - Connects BITTEN ZMQ system to Firebase/Firestore
Mirrors signals and exec states for real-time web app updates

Architecture:
- Layer 1: Firestore = real-time operational store (app/EA needs)
- Layer 2: BigQuery = analytics (heavy metrics, long history) - future
- Rollups: /metrics/* for fast dashboard queries (no heavy aggregations)
"""
import os
import sys
import json
import time
from datetime import datetime, timezone
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client(project="bitten-0420")

# Data model constants (from /root/hydrax/src/config/datamodel.ts)
DATA = {
    "collections": {
        "signals": "signals",
        "exec_for_user": lambda uid: f"exec/{uid}/items"
    },
    "fields": {
        "signal": {
            "id": "id",
            "pair": "pair",
            "side": "side",
            "price": "price",
            "sl": "sl",
            "tp": "tp",
            "confidence": "confidence"
        },
        "exec": {
            "id": "id",
            "signalId": "signalId",
            "state": "state",
            "createdAt": "createdAt",
            "updatedAt": "updatedAt",
            "uid": "uid"
        }
    },
    "enums": {
        "execStates": {
            "pending": "PENDING",
            "sent": "SENT",
            "acked": "ACKED",
            "filled": "FILLED",
            "rejected": "REJECTED",
            "timeout": "TIMEOUT"
        }
    }
}

# Auto-fire configuration from environment
AUTO_FIRE_ENABLED = os.getenv('AUTO_FIRE', 'false').lower() == 'true'
AUTO_FIRE_UID = os.getenv('AUTO_FIRE_UID', '')
AUTO_FIRE_MIN_CONF = float(os.getenv('AUTO_FIRE_MIN_CONF', '80'))

print("🔥 Firebase Bridge Initialized")
print("=" * 60)
print(f"Project: bitten-0420")
print(f"Firestore: Connected")
print(f"Auto-Fire: {'ENABLED' if AUTO_FIRE_ENABLED else 'DISABLED'}")
if AUTO_FIRE_ENABLED:
    print(f"Auto-Fire UID: {AUTO_FIRE_UID}")
    print(f"Auto-Fire Min Confidence: {AUTO_FIRE_MIN_CONF}%")
print("=" * 60)

def mirror_signal_to_firestore(signal_data):
    """
    Mirror a signal from BITTEN to Firestore /signals collection

    Schema designed for:
    - Real-time operational queries (app/EA needs)
    - Analytics rollups (counters, win rates)
    - BigQuery export readiness (immutable after creation)

    Args:
        signal_data (dict): Signal data from Elite Guard

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        signal_id = signal_data.get('signal_id') or signal_data.get('id')
        if not signal_id:
            print(f"⚠️  No signal_id found in data")
            return False

        # Build comprehensive Firestore document (immutable core + mutable status)
        firestore_doc = {
            # Core signal data (immutable)
            'pair': signal_data.get('symbol') or signal_data.get('pair'),
            'symbol': signal_data.get('symbol'),
            'direction': signal_data.get('direction'),  # "BUY" or "SELL"
            'entry': float(signal_data.get('entry_price', 0) or signal_data.get('entry', 0)),
            'sl': float(signal_data.get('stop_loss') or signal_data.get('sl') or 0) if signal_data.get('stop_loss') or signal_data.get('sl') else None,
            'tp': float(signal_data.get('take_profit') or signal_data.get('tp') or 0) if signal_data.get('take_profit') or signal_data.get('tp') else None,
            'confidence': float(signal_data.get('confidence', 0)),
            'pattern_type': signal_data.get('pattern_type') or signal_data.get('pattern'),
            'strategy': signal_data.get('signal_type') or signal_data.get('signal_class', 'UNKNOWN'),
            'session': signal_data.get('session'),
            'timeframe': signal_data.get('timeframe', 'M5'),

            # Risk/Reward metrics
            'stopPips': float(signal_data.get('stop_pips', 0)) if signal_data.get('stop_pips') else None,
            'targetPips': float(signal_data.get('target_pips', 0)) if signal_data.get('target_pips') else None,
            'riskReward': float(signal_data.get('risk_reward', 0)) if signal_data.get('risk_reward') else None,

            # Timestamps
            'createdAt': firestore.SERVER_TIMESTAMP,
            'expiresAt': int(signal_data.get('expires_at', 0)) if signal_data.get('expires_at') else None,

            # Mutable tracking fields (updated later)
            'status': 'ACTIVE',  # ACTIVE, EXPIRED, HIT_TP, HIT_SL
            'outcome': None,  # null, "WIN", "LOSS"
            'exitPrice': None,
            'exitTime': None,
            'pnlPips': None,
            'durationSeconds': None,

            # Metadata
            'proOnly': signal_data.get('pro_only', True),
            'qualityTier': signal_data.get('quality_tier'),
            'citadelScore': float(signal_data.get('citadel_score', 0)) if signal_data.get('citadel_score') else None,
        }

        # Remove None values for cleaner storage
        firestore_doc = {k: v for k, v in firestore_doc.items() if v is not None}

        # Write to Firestore (merge=False for first write, ensures immutability of core fields)
        db.collection('signals').document(signal_id).set(firestore_doc, merge=False)

        print(f"✅ Mirrored signal: {signal_id} ({signal_data.get('symbol')} {signal_data.get('direction')})")

        # Trigger metrics rollup increment (async)
        _increment_signal_metrics(firestore_doc)

        return True

    except Exception as e:
        print(f"❌ Firebase mirror failed: {e}")
        return False


def update_exec_state(user_id, fire_id, state_update):
    """
    Update execution state in Firestore /exec/{uid}/{execId}

    Args:
        user_id (str): User ID
        fire_id (str): Fire command ID
        state_update (dict): State update data

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not user_id or not fire_id:
            print(f"⚠️  Missing user_id or fire_id")
            return False

        # Path: /exec/{uid}/{execId}
        doc_ref = db.collection('exec').document(user_id).collection(user_id).document(fire_id)

        # Build update
        update_data = {
            'state': state_update.get('state'),
            'lastUpdated': firestore.SERVER_TIMESTAMP,
        }

        # Add optional fields
        if state_update.get('sentAt'):
            update_data['sentAt'] = firestore.SERVER_TIMESTAMP
        if state_update.get('ackAt'):
            update_data['ackAt'] = firestore.SERVER_TIMESTAMP
        if state_update.get('finalAt'):
            update_data['finalAt'] = firestore.SERVER_TIMESTAMP
        if state_update.get('ticket'):
            update_data['ticket'] = int(state_update['ticket'])
        if state_update.get('price'):
            update_data['price'] = float(state_update['price'])
        if state_update.get('error'):
            update_data['error'] = state_update['error']
        if state_update.get('reason'):
            update_data['reason'] = state_update['reason']

        # Write to Firestore
        doc_ref.set(update_data, merge=True)

        print(f"✅ Updated exec state: {fire_id} → {state_update.get('state')}")
        return True

    except Exception as e:
        print(f"❌ Exec state update failed: {e}")
        return False


def update_ea_presence(uuid, online=True, metadata=None):
    """
    Update EA presence in Firestore /presence/{uuid}

    Args:
        uuid (str): EA UUID
        online (bool): Online status
        metadata (dict): Optional metadata (version, balance, etc.)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not uuid:
            print(f"⚠️  Missing UUID")
            return False

        # Build presence doc
        presence_data = {
            'online': online,
            'lastSeen': firestore.SERVER_TIMESTAMP,
        }

        if metadata:
            if metadata.get('version'):
                presence_data['eaVersion'] = metadata['version']
            if metadata.get('balance'):
                presence_data['balance'] = float(metadata['balance'])
            if metadata.get('equity'):
                presence_data['equity'] = float(metadata['equity'])
            if metadata.get('latency'):
                presence_data['latencyMs'] = int(metadata['latency'])

        # Write to Firestore
        db.collection('presence').document(uuid).set(presence_data, merge=True)

        status = "online" if online else "offline"
        print(f"✅ Updated presence: {uuid} → {status}")
        return True

    except Exception as e:
        print(f"❌ Presence update failed: {e}")
        return False


def _increment_signal_metrics(signal_doc):
    """
    Increment metrics rollups for fast dashboard queries

    Rollup structure:
    /metrics/global/daily/{YYYYMMDD} - Global daily stats
    /metrics/pair/{PAIR}/daily/{YYYYMMDD} - Per-pair daily stats
    /metrics/strategy/{STRAT}/daily/{YYYYMMDD} - Per-strategy stats (optional)

    This is called on signal creation. Updates counters atomically using Firestore increment.
    """
    try:
        # Get today's date key
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        pair = signal_doc.get('pair', 'UNKNOWN')
        strategy = signal_doc.get('strategy', 'UNKNOWN')

        # Atomic increment operations (all async, non-blocking)
        increment = firestore.Increment(1)

        # Global daily metrics
        global_ref = db.collection('metrics').document('global').collection('daily').document(today)
        global_ref.set({
            'signals': increment,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }, merge=True)

        # Per-pair daily metrics
        pair_ref = db.collection('metrics').document('pair').collection(pair).document('daily').document(today)
        pair_ref.set({
            'signals': increment,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }, merge=True)

        # Per-strategy daily metrics (optional, if strategy exists)
        if strategy and strategy != 'UNKNOWN':
            strategy_ref = db.collection('metrics').document('strategy').collection(strategy).document('daily').document(today)
            strategy_ref.set({
                'signals': increment,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }, merge=True)

        print(f"📊 Incremented metrics: global, {pair}, {strategy}")

    except Exception as e:
        # Non-critical - don't crash if metrics fail
        print(f"⚠️  Metrics increment failed (non-critical): {e}")


def update_signal_outcome(signal_id, outcome, exit_price, pnl_pips):
    """
    Update signal outcome when TP/SL is hit

    Args:
        signal_id (str): Signal ID
        outcome (str): "WIN" or "LOSS"
        exit_price (float): Actual exit price
        pnl_pips (float): Profit/loss in pips

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not signal_id:
            print(f"⚠️  No signal_id provided for outcome update")
            return False

        # Get signal document first (to read original data for metrics)
        signal_ref = db.collection('signals').document(signal_id)
        signal_doc = signal_ref.get()

        if not signal_doc.exists:
            print(f"⚠️  Signal {signal_id} not found in Firestore")
            return False

        signal_data = signal_doc.to_dict()

        # Update signal document with outcome
        update_data = {
            'status': 'HIT_TP' if outcome == 'WIN' else 'HIT_SL',
            'outcome': outcome,
            'exitPrice': float(exit_price),
            'exitTime': firestore.SERVER_TIMESTAMP,
            'pnlPips': float(pnl_pips),
            'durationSeconds': int(time.time() - signal_data.get('createdAt', 0).timestamp()) if signal_data.get('createdAt') else None
        }

        signal_ref.update(update_data)

        print(f"✅ Updated outcome: {signal_id} → {outcome} ({pnl_pips:+.1f} pips)")

        # Update metrics rollups with win/loss data
        _increment_outcome_metrics(signal_data, outcome, pnl_pips)

        return True

    except Exception as e:
        print(f"❌ Outcome update failed: {e}")
        return False


def _increment_outcome_metrics(signal_data, outcome, pnl_pips):
    """
    Update metrics rollups with win/loss data

    Uses incremental formulas to update:
    - fills count
    - win rate (using incremental average)
    - average R:R
    """
    try:
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        pair = signal_data.get('pair', 'UNKNOWN')
        strategy = signal_data.get('strategy', 'UNKNOWN')

        increment = firestore.Increment(1)
        wins_increment = firestore.Increment(1 if outcome == 'WIN' else 0)

        # Batch update all metrics documents
        batch = db.batch()

        # Global metrics
        global_ref = db.collection('metrics').document('global').collection('daily').document(today)
        batch.set(global_ref, {
            'fills': increment,
            'wins': wins_increment,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }, merge=True)

        # Per-pair metrics
        pair_ref = db.collection('metrics').document('pair').collection(pair).document('daily').document(today)
        batch.set(pair_ref, {
            'fills': increment,
            'wins': wins_increment,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }, merge=True)

        # Per-strategy metrics
        if strategy and strategy != 'UNKNOWN':
            strategy_ref = db.collection('metrics').document('strategy').collection(strategy).document('daily').document(today)
            batch.set(strategy_ref, {
                'fills': increment,
                'wins': wins_increment,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }, merge=True)

        # Commit batch
        batch.commit()

        print(f"📊 Updated outcome metrics: {outcome} for {pair}")

    except Exception as e:
        print(f"⚠️  Outcome metrics update failed (non-critical): {e}")


def auto_fire_if_enabled(signal_doc):
    """
    Auto-fire logic: Creates exec document if conditions are met

    Args:
        signal_doc (dict): Signal document from Firestore mirror

    Returns:
        bool: True if auto-fire was triggered, False otherwise
    """
    try:
        # Check if auto-fire is enabled
        if not AUTO_FIRE_ENABLED:
            return False

        if not AUTO_FIRE_UID:
            print("⚠️  AUTO_FIRE enabled but AUTO_FIRE_UID not set")
            return False

        # Get signal ID and confidence
        signal_id = signal_doc.get('signal_id') or signal_doc.get('id')
        if not signal_id:
            print("⚠️  No signal_id in signal_doc for auto-fire")
            return False

        # Check confidence threshold
        confidence = signal_doc.get(DATA['fields']['signal']['confidence'], 0)
        if confidence < AUTO_FIRE_MIN_CONF:
            print(f"ℹ️  Signal {signal_id} confidence {confidence}% < {AUTO_FIRE_MIN_CONF}% threshold, skipping auto-fire")
            return False

        # Build deterministic exec ID: auto_<signalId>_<uid>
        exec_id = f"auto_{signal_id}_{AUTO_FIRE_UID}"

        # Build exec document
        exec_doc = {
            DATA['fields']['exec']['id']: exec_id,
            DATA['fields']['exec']['uid']: AUTO_FIRE_UID,
            DATA['fields']['exec']['signalId']: signal_id,
            DATA['fields']['exec']['state']: DATA['enums']['execStates']['pending'],
            DATA['fields']['exec']['createdAt']: firestore.SERVER_TIMESTAMP,
            DATA['fields']['exec']['updatedAt']: firestore.SERVER_TIMESTAMP,

            # Copy-through fields EA needs
            'pair': signal_doc.get(DATA['fields']['signal']['pair']),
            'side': signal_doc.get(DATA['fields']['signal']['side']),
            'price': signal_doc.get(DATA['fields']['signal']['price']),
            'sl': signal_doc.get(DATA['fields']['signal']['sl']),
            'tp': signal_doc.get(DATA['fields']['signal']['tp']),

            # Metadata
            'source': 'AUTO',
            'confidence': confidence
        }

        # Remove None values
        exec_doc = {k: v for k, v in exec_doc.items() if v is not None}

        # Get collection path: /exec/{uid}/items
        exec_collection_path = DATA['collections']['exec_for_user'](AUTO_FIRE_UID)

        # Write to Firestore with merge=True for idempotency
        # (create if not exists, or update timestamps if exists)
        db.collection(exec_collection_path).document(exec_id).set(exec_doc, merge=True)

        print(f"🔥 AUTO-FIRE: Created exec {exec_id} for signal {signal_id} ({confidence}% confidence)")
        return True

    except Exception as e:
        # Log error but don't crash
        print(f"⚠️  Auto-fire error (non-critical): {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 Testing Firebase Bridge Functions...")
    print("=" * 60)

    # Test signal mirror
    test_signal = {
        'signal_id': 'TEST_SIGNAL_123',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.10000,
        'sl': 1.09800,
        'tp': 1.10300,
        'confidence': 0.85,
        'pattern_type': 'VCB_BREAKOUT',
        'session': 'LONDON',
        'expires_at': int(time.time()) + 1800,
        'pro_only': True
    }

    print("\n1. Testing signal mirror...")
    mirror_signal_to_firestore(test_signal)

    # Test exec state update
    print("\n2. Testing exec state update...")
    update_exec_state('test_user_123', 'TEST_FIRE_456', {
        'state': 'PENDING',
        'sentAt': True
    })

    # Test presence update
    print("\n3. Testing presence update...")
    update_ea_presence('COMMANDER_DEV_001', True, {
        'version': '2.07',
        'balance': 1000.00,
        'equity': 1012.50
    })

    print("\n✅ All tests complete! Check Firestore Console:")
    print("   https://console.firebase.google.com/project/bitten-0420/firestore")
    print("=" * 60)
