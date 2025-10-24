#!/usr/bin/env python3
"""Check user data in Firebase for debugging"""
import sqlite3
from google.cloud import firestore

# Connect to database
db_path = '/root/HydraX-v2/bitten.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Connect to Firebase
firebase_db = firestore.Client(project="bitten-0420")

print("=" * 70)
print("🔍 USER DATA CHECK - Firebase vs SQLite")
print("=" * 70)

# Get UUID mapping
cursor.execute("SELECT telegram_id, firebase_uid FROM user_uuid_mapping WHERE telegram_id = '7176191872';")
row = cursor.fetchone()

if row:
    telegram_id, firebase_uid = row
    print(f"\n📋 UUID Mapping:")
    print(f"   Telegram ID: {telegram_id}")
    print(f"   Firebase UUID: {firebase_uid}")

    # Get account data from SQLite
    cursor.execute("""
        SELECT account_login, last_balance, last_equity, broker, leverage, target_uuid
        FROM ea_instances
        WHERE user_id = ?
    """, (telegram_id,))

    ea_row = cursor.fetchone()
    if ea_row:
        account_login, balance, equity, broker, leverage, target_uuid = ea_row
        print(f"\n📊 SQLite Account Data:")
        print(f"   Account: {account_login}")
        print(f"   Balance: ${balance:.2f}")
        print(f"   Equity: ${equity:.2f}")
        print(f"   Broker: {broker}")
        print(f"   Leverage: {leverage}")
        print(f"   Target UUID: {target_uuid}")

    # Get data from Firebase
    print(f"\n🔥 Firebase User Data:")
    user_ref = firebase_db.collection('users').document(firebase_uid)
    user_doc = user_ref.get()

    if user_doc.exists:
        data = user_doc.to_dict()
        print(f"   ✅ Document exists!")
        print(f"   Balance: ${data.get('balance', 0):.2f}")
        print(f"   Equity: ${data.get('equity', 0):.2f}")
        print(f"   Display Name: {data.get('displayName', 'N/A')}")
        print(f"   Tier: {data.get('tier', 'N/A')}")
        print(f"   Email: {data.get('email', 'N/A')}")
    else:
        print(f"   ❌ Document does not exist at /users/{firebase_uid}")

    print(f"\n💡 Login Instructions:")
    print(f"   1. User should create account with email at /login")
    print(f"   2. After signup, their account balance should sync automatically")
    print(f"   3. Or, link existing Firebase UID {firebase_uid} to this account data")

else:
    print(f"\n❌ No UUID mapping found for Telegram ID 7176191872")

print("\n" + "=" * 70)
