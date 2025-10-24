#!/usr/bin/env python3
"""
Quick verification script to confirm Firestore deployment is ready
Run this to verify all components are working
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter


def verify_firestore_setup():
    """Comprehensive Firestore setup verification"""

    print("=" * 70)
    print("🔥 BITTEN FIRESTORE DEPLOYMENT VERIFICATION")
    print("=" * 70)

    checks_passed = 0
    checks_failed = 0

    # Check 1: Credentials file exists
    print("\n🔍 Check 1: Firebase Credentials")
    cred_path = "/root/bitten-firebase-sa.json"
    if os.path.exists(cred_path):
        print(f"  ✅ PASS: Credentials found at {cred_path}")
        checks_passed += 1
    else:
        print(f"  ❌ FAIL: Credentials not found at {cred_path}")
        checks_failed += 1
        return checks_passed, checks_failed

    # Check 2: Initialize Firebase
    print("\n🔍 Check 2: Firebase Admin SDK Initialization")
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("  ✅ PASS: Firebase Admin SDK initialized")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: Initialization failed - {e}")
        checks_failed += 1
        return checks_passed, checks_failed

    # Check 3: Collections exist
    print("\n🔍 Check 3: Required Collections")
    required_collections = ['users', 'signals', 'positions', 'fire_history', 'system']
    all_collections_exist = True

    for coll in required_collections:
        try:
            docs = list(db.collection(coll).limit(1).stream())
            if len(docs) > 0:
                print(f"  ✅ {coll}: Collection exists with data")
            else:
                print(f"  ⚠️  {coll}: Collection exists but empty")
        except Exception as e:
            print(f"  ❌ {coll}: Failed to access - {e}")
            all_collections_exist = False

    if all_collections_exist:
        checks_passed += 1
    else:
        checks_failed += 1

    # Check 4: Write operation
    print("\n🔍 Check 4: Write Operation")
    try:
        test_ref = db.collection('signals').document('verification_test')
        test_ref.set({
            'signal_id': 'verification_test',
            'symbol': 'TEST',
            'status': 'TEST',
            'created_at': firestore.SERVER_TIMESTAMP
        })
        print("  ✅ PASS: Write operation successful")
        checks_passed += 1

        # Cleanup
        test_ref.delete()
    except Exception as e:
        print(f"  ❌ FAIL: Write operation failed - {e}")
        checks_failed += 1

    # Check 5: Read operation
    print("\n🔍 Check 5: Read Operation")
    try:
        docs = list(db.collection('signals').limit(5).stream())
        print(f"  ✅ PASS: Read operation successful ({len(docs)} documents)")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: Read operation failed - {e}")
        checks_failed += 1

    # Check 6: Batch operation
    print("\n🔍 Check 6: Batch Operation")
    try:
        batch = db.batch()
        for i in range(3):
            ref = db.collection('signals').document(f'batch_verify_{i}')
            batch.set(ref, {
                'signal_id': f'batch_verify_{i}',
                'status': 'TEST',
                'created_at': firestore.SERVER_TIMESTAMP
            })
        batch.commit()
        print("  ✅ PASS: Batch write successful (3 documents)")
        checks_passed += 1

        # Cleanup
        batch = db.batch()
        for i in range(3):
            ref = db.collection('signals').document(f'batch_verify_{i}')
            batch.delete(ref)
        batch.commit()
    except Exception as e:
        print(f"  ❌ FAIL: Batch operation failed - {e}")
        checks_failed += 1

    # Check 7: Transaction
    print("\n🔍 Check 7: Transaction")
    try:
        @firestore.transactional
        def test_transaction(transaction, ref):
            snapshot = ref.get(transaction=transaction)
            if snapshot.exists:
                current = snapshot.get('total_signals') or 0
            else:
                current = 0
            transaction.set(ref, {'total_signals': current + 1}, merge=True)
            return current + 1

        stats_ref = db.collection('system').document('stats')
        transaction = db.transaction()
        result = test_transaction(transaction, stats_ref)
        print(f"  ✅ PASS: Transaction successful (count: {result})")
        checks_passed += 1
    except Exception as e:
        print(f"  ❌ FAIL: Transaction failed - {e}")
        checks_failed += 1

    # Check 8: TTL field presence
    print("\n🔍 Check 8: Signal TTL Configuration")
    try:
        signals = db.collection('signals').limit(5).stream()
        ttl_found = False
        for signal in signals:
            data = signal.to_dict()
            if 'ttl' in data and data['ttl'] is not None:
                ttl_found = True
                break

        if ttl_found:
            print("  ✅ PASS: TTL field found in signals")
            checks_passed += 1
        else:
            print("  ⚠️  WARN: TTL field not found (may need to run init_firestore.py)")
            checks_failed += 1
    except Exception as e:
        print(f"  ❌ FAIL: TTL check failed - {e}")
        checks_failed += 1

    # Check 9: Files exist
    print("\n🔍 Check 9: Required Files")
    firestore_dir = Path(__file__).parent
    required_files = [
        'firestore.rules',
        'firestore.indexes.json',
        'init_firestore.py',
        'test_firestore.py',
        'README.md'
    ]

    all_files_exist = True
    for filename in required_files:
        filepath = firestore_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✅ {filename}: {size:,} bytes")
        else:
            print(f"  ❌ {filename}: NOT FOUND")
            all_files_exist = False

    if all_files_exist:
        checks_passed += 1
    else:
        checks_failed += 1

    # Final summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    total_checks = checks_passed + checks_failed
    success_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0

    print(f"Total Checks: {total_checks}")
    print(f"Passed: {checks_passed} ✅")
    print(f"Failed: {checks_failed} ❌")
    print(f"Success Rate: {success_rate:.1f}%")

    if checks_failed == 0:
        print("\n✅ DEPLOYMENT VERIFIED - Ready for production!")
        print("\nNext steps:")
        print("  1. Deploy security rules: firebase deploy --only firestore:rules")
        print("  2. Deploy indexes: firebase deploy --only firestore:indexes")
        print("  3. Configure TTL policy in Firebase Console")
    else:
        print(f"\n⚠️  {checks_failed} check(s) failed - review errors above")

    print("=" * 70)

    return checks_passed, checks_failed


if __name__ == "__main__":
    passed, failed = verify_firestore_setup()
    sys.exit(0 if failed == 0 else 1)
