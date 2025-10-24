#!/usr/bin/env python3
"""Sync account data from BITTEN database to Firebase"""
import sqlite3
from google.cloud import firestore

# Connect to BITTEN database
bitten_db = sqlite3.connect('/root/HydraX-v2/bitten.db')
cursor = bitten_db.cursor()

# Connect to Firebase
db = firestore.Client(project="bitten-0420")

print("🔄 Syncing account data to Firebase...")
print("=" * 60)

# Get EA instances with account data
cursor.execute("""
    SELECT target_uuid, user_id, account_login, last_balance, last_equity, broker, leverage
    FROM ea_instances
    WHERE user_id IS NOT NULL
""")

for row in cursor.fetchall():
    target_uuid, telegram_id, account_login, balance, equity, broker, leverage = row
    
    if not telegram_id:
        continue
    
    print(f"\n📊 Account: {account_login}")
    print(f"   Telegram ID: {telegram_id}")
    print(f"   Balance: ${balance:.2f}")
    print(f"   Equity: ${equity:.2f}")
    
    # Create/update user document in Firebase
    # Use telegram_id as the user document ID for now
    user_ref = db.collection('users').document(str(telegram_id))
    
    user_data = {
        'telegram_id': telegram_id,
        'account_login': account_login,
        'balance': float(balance) if balance else 0.0,
        'equity': float(equity) if equity else 0.0,
        'broker': broker or 'Unknown',
        'leverage': leverage or 100,
        'target_uuid': target_uuid,
        'displayName': f'Commander {telegram_id[-4:]}',
        'tier': 'COMMANDER',  # Set based on your actual tier system
    }
    
    user_ref.set(user_data, merge=True)
    print(f"   ✅ Synced to Firebase /users/{telegram_id}")

print("\n" + "=" * 60)
print("✅ Account sync complete!")
print("\nNext: Sign in with Telegram ID as your Firebase user ID")
