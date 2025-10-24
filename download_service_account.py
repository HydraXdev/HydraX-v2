#!/usr/bin/env python3
"""
Download Firebase service account key
This uses your existing Firebase CLI authentication
"""
import subprocess
import json
import sys

print("🔥 Downloading Firebase Service Account Key...")
print("=" * 60)

# Get the current Firebase token
try:
    result = subprocess.run(
        ['firebase', 'login:ci'],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        print("⚠️  You need to be logged in to Firebase CLI")
        print("\nRun: firebase login")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n📋 Service Account Instructions:")
print("=" * 60)
print("\nSince automated key generation requires additional permissions,")
print("please manually download the service account key:\n")
print("1. Visit:")
print("   https://console.firebase.google.com/project/bitten-0420/settings/serviceaccounts/adminsdk")
print("\n2. Click 'Generate New Private Key'")
print("\n3. Save the downloaded JSON file as:")
print("   /root/bitten-firebase-sa.json")
print("\n4. Then run:")
print("   export GOOGLE_APPLICATION_CREDENTIALS=/root/bitten-firebase-sa.json")
print("\n5. Verify with:")
print("   python3 /root/HydraX-v2/firebase_bridge_setup.sh")
print("\n" + "=" * 60)
