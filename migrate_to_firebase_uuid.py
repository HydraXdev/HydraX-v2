#!/usr/bin/env python3
"""
Migrate BITTEN system from Telegram IDs to Firebase UUIDs
This script creates a mapping table and updates all user references
"""
import sqlite3
from google.cloud import firestore
import uuid

# Connect to databases
bitten_db = sqlite3.connect('/root/HydraX-v2/bitten.db')
cursor = bitten_db.cursor()

# Connect to Firebase
db = firestore.Client(project="bitten-0420")

print("=" * 70)
print("🔄 MIGRATING BITTEN SYSTEM TO FIREBASE UUID")
print("=" * 70)

# Step 1: Create UUID mapping table in SQLite
print("\n📋 Step 1: Creating UUID mapping table...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_uuid_mapping (
        telegram_id TEXT PRIMARY KEY,
        firebase_uid TEXT NOT NULL UNIQUE,
        created_at INTEGER DEFAULT (strftime('%s', 'now'))
    )
""")
bitten_db.commit()
print("✅ Mapping table created")

# Step 2: Get all unique telegram IDs from ea_instances
print("\n📊 Step 2: Finding all users...")
cursor.execute("SELECT DISTINCT user_id FROM ea_instances WHERE user_id IS NOT NULL")
telegram_ids = [row[0] for row in cursor.fetchall()]
print(f"✅ Found {len(telegram_ids)} users")

# Step 3: For each telegram ID, create/get Firebase UUID
print("\n🔑 Step 3: Generating Firebase UUIDs...")
mapping_count = 0

for telegram_id in telegram_ids:
    # Check if mapping already exists
    cursor.execute("SELECT firebase_uid FROM user_uuid_mapping WHERE telegram_id = ?", (telegram_id,))
    existing = cursor.fetchone()

    if existing:
        firebase_uid = existing[0]
        print(f"   ℹ️  Telegram {telegram_id} already mapped to {firebase_uid}")
    else:
        # Generate new Firebase-compatible UUID
        firebase_uid = str(uuid.uuid4()).replace('-', '')[:28]  # Firebase UID format

        # Insert mapping
        cursor.execute(
            "INSERT INTO user_uuid_mapping (telegram_id, firebase_uid) VALUES (?, ?)",
            (telegram_id, firebase_uid)
        )
        bitten_db.commit()

        print(f"   ✅ Telegram {telegram_id} → Firebase UUID {firebase_uid}")
        mapping_count += 1

print(f"\n✅ Created {mapping_count} new UUID mappings")

# Step 4: Migrate user data to Firebase with new UUIDs
print("\n🔥 Step 4: Migrating user data to Firebase...")

cursor.execute("""
    SELECT
        m.firebase_uid,
        m.telegram_id,
        e.account_login,
        e.last_balance,
        e.last_equity,
        e.broker,
        e.leverage,
        e.target_uuid
    FROM user_uuid_mapping m
    JOIN ea_instances e ON m.telegram_id = e.user_id
""")

for row in cursor.fetchall():
    firebase_uid, telegram_id, account_login, balance, equity, broker, leverage, target_uuid = row

    user_data = {
        'uid': firebase_uid,
        'telegram_id': telegram_id,  # Keep for legacy reference
        'account_login': account_login,
        'balance': float(balance) if balance else 0.0,
        'equity': float(equity) if equity else 0.0,
        'broker': broker or 'Unknown',
        'leverage': leverage or 100,
        'target_uuid': target_uuid,
        'displayName': f'Commander {telegram_id[-4:]}',
        'tier': 'COMMANDER',
    }

    # Write to Firebase with UUID as document ID
    db.collection('users').document(firebase_uid).set(user_data, merge=True)
    print(f"   ✅ Firebase /users/{firebase_uid} (Telegram: {telegram_id})")

print("\n=" * 70)
print("✅ MIGRATION COMPLETE!")
print("=" * 70)
print("\n📌 Next Steps:")
print("1. Users can now sign up/login with email to get Firebase UUID")
print("2. System will use Firebase UUID for all operations")
print("3. Telegram ID kept in mapping table for legacy reference")
print("\n💡 UUID Mapping Query:")
print("   SELECT * FROM user_uuid_mapping WHERE telegram_id = 'YOUR_TELEGRAM_ID';")
print("\n")
