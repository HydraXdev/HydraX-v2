#!/bin/bash
# Firebase Bridge Setup Script
# Run this once to set up Firebase integration

echo "🔥 Firebase Bridge Setup"
echo "========================"
echo ""

# Check if service account exists
if [ ! -f "/root/bitten-firebase-sa.json" ]; then
    echo "⚠️  Service Account Key Missing"
    echo ""
    echo "Please download the service account key:"
    echo "1. Visit: https://console.firebase.google.com/project/bitten-0420/settings/serviceaccounts/adminsdk"
    echo "2. Click 'Generate New Private Key'"
    echo "3. Download and save as: /root/bitten-firebase-sa.json"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/root/bitten-firebase-sa.json"

# Add to bashrc if not already there
if ! grep -q "GOOGLE_APPLICATION_CREDENTIALS" ~/.bashrc; then
    echo 'export GOOGLE_APPLICATION_CREDENTIALS="/root/bitten-firebase-sa.json"' >> ~/.bashrc
    echo "✅ Added GOOGLE_APPLICATION_CREDENTIALS to ~/.bashrc"
fi

# Test connection
echo ""
echo "Testing Firebase connection..."
python3 << 'PYEOF'
from google.cloud import firestore
try:
    db = firestore.Client(project="bitten-0420")
    # Test write
    doc_ref = db.collection('_test').document('connection_test')
    doc_ref.set({'status': 'connected', 'timestamp': firestore.SERVER_TIMESTAMP})
    print("✅ Firebase connection successful!")
    # Cleanup test doc
    doc_ref.delete()
except Exception as e:
    print(f"❌ Firebase connection failed: {e}")
    exit(1)
PYEOF

echo ""
echo "✅ Setup complete! Firebase bridge is ready."
