#!/usr/bin/env python3
"""
Link legacy Telegram account data to new Firebase Auth user
Usage: python3 link_legacy_account.py <firebase_auth_uid> <telegram_id>
"""
import sys
import sqlite3
from google.cloud import firestore

if len(sys.argv) != 3:
    print("Usage: python3 link_legacy_account.py <firebase_auth_uid> <telegram_id>")
    sys.exit(1)

new_uid = sys.argv[1]
telegram_id = sys.argv[2]

# Connect to database
conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
cursor = conn.cursor()

# Connect to Firebase
db = firestore.Client(project="bitten-0420")

print("=" * 70)
print("🔗 LINKING LEGACY ACCOUNT TO NEW FIREBASE AUTH USER")
print("=" * 70)

# Get legacy UUID
cursor.execute("SELECT firebase_uid FROM user_uuid_mapping WHERE telegram_id = ?", (telegram_id,))
row = cursor.fetchone()

if not row:
    print(f"\n❌ No mapping found for Telegram ID {telegram_id}")
    sys.exit(1)

legacy_uid = row[0]
print(f"\n📋 Found legacy account:")
print(f"   Telegram ID: {telegram_id}")
print(f"   Legacy UUID: {legacy_uid}")
print(f"   New Auth UID: {new_uid}")

# Get legacy account data
legacy_ref = db.collection('users').document(legacy_uid)
legacy_doc = legacy_ref.get()

if not legacy_doc.exists:
    print(f"\n❌ No data found at /users/{legacy_uid}")
    sys.exit(1)

legacy_data = legacy_doc.to_dict()
print(f"\n📊 Legacy account data:")
print(f"   Balance: ${legacy_data.get('balance', 0):.2f}")
print(f"   Equity: ${legacy_data.get('equity', 0):.2f}")
print(f"   Tier: {legacy_data.get('tier', 'N/A')}")
print(f"   Display Name: {legacy_data.get('displayName', 'N/A')}")

# Copy data to new UID
new_ref = db.collection('users').document(new_uid)
new_doc = new_ref.get()

if new_doc.exists:
    # Merge with existing data
    print(f"\n✅ Merging with existing account at /users/{new_uid}")
    new_ref.set({
        'balance': legacy_data.get('balance', 0),
        'equity': legacy_data.get('equity', 0),
        'tier': legacy_data.get('tier', 'RECRUIT'),
        'account_login': legacy_data.get('account_login'),
        'broker': legacy_data.get('broker'),
        'leverage': legacy_data.get('leverage'),
        'target_uuid': legacy_data.get('target_uuid'),
        'telegram_id': telegram_id,
        'legacy_uid': legacy_uid,
    }, merge=True)
else:
    # Create new document
    print(f"\n✅ Creating new account at /users/{new_uid}")
    legacy_data['uid'] = new_uid
    legacy_data['telegram_id'] = telegram_id
    legacy_data['legacy_uid'] = legacy_uid
    new_ref.set(legacy_data)

# Update UUID mapping
cursor.execute(
    "UPDATE user_uuid_mapping SET firebase_uid = ? WHERE telegram_id = ?",
    (new_uid, telegram_id)
)
conn.commit()

print(f"\n✅ Account data migrated successfully!")
print(f"   Old UUID: {legacy_uid}")
print(f"   New UUID: {new_uid}")
print(f"   Database mapping updated")

print("\n" + "=" * 70)
