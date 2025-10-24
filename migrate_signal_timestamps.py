#!/usr/bin/env python3
"""
Migrate existing Firestore signals from 'timestamp' to 'created_at'

This script adds the 'created_at' field to all existing signal documents
that only have 'timestamp', so AlertFeed queries work correctly.
"""

import sys
sys.path.insert(0, '/root/HydraX-v2')

from firebase_backend import get_firestore_client

def migrate_signal_timestamps():
    """Add created_at field to signals that only have timestamp"""
    db = get_firestore_client()
    if not db:
        print("❌ Failed to connect to Firestore")
        return False

    try:
        # Get all signals
        signals_ref = db.collection('signals')
        signals = signals_ref.stream()

        migrated = 0
        skipped = 0

        for doc in signals:
            data = doc.to_dict()

            # Check if it has timestamp but not created_at
            if 'timestamp' in data and 'created_at' not in data:
                # Add created_at with the same value as timestamp
                doc.reference.update({
                    'created_at': data['timestamp']
                })
                migrated += 1
                print(f"✅ Migrated {doc.id}")
            else:
                skipped += 1

        print(f"\n📊 Migration Complete:")
        print(f"   Migrated: {migrated} signals")
        print(f"   Skipped: {skipped} signals (already have created_at)")
        return True

    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == '__main__':
    print("🔄 Starting Firestore signal timestamp migration...")
    migrate_signal_timestamps()
