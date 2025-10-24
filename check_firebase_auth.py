#!/usr/bin/env python3
"""Check Firebase Auth users"""
from firebase_admin import auth, credentials, initialize_app

# Initialize Firebase Admin
cred = credentials.Certificate('/root/HydraX-v2/bitten-firebase-sa.json')
initialize_app(cred)

print('🔍 Checking Firebase Auth users...')
print('=' * 70)

# List all users
page = auth.list_users()
count = 0
for user in page.users:
    count += 1
    print(f'\n👤 Auth User {count}:')
    print(f'   UID: {user.uid}')
    print(f'   Email: {user.email or "N/A"}')
    print(f'   Display Name: {user.display_name or "N/A"}')
    print(f'   Email Verified: {user.email_verified}')
    print(f'   Created: {user.user_metadata.creation_timestamp}')
    print(f'   Last Sign In: {user.user_metadata.last_sign_in_timestamp or "Never"}')

if count == 0:
    print('\n❌ No Firebase Auth users found!')
    print('   You need to create an account at /login')
else:
    print(f'\n✅ Total Firebase Auth users: {count}')

print('=' * 70)
