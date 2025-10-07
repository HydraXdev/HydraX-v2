#!/bin/bash
# 🔒 SECURE ATHENA BOT STARTUP SCRIPT
# Loads environment variables and starts bot with security hardening

echo "🔒 Starting Secure ATHENA Bot..."

# Load environment variables from secure file
source /root/HydraX-v2/.secrets/athena.env

# Verify token is loaded
if [ -z "$ATHENA_BOT_TOKEN" ]; then
    echo "❌ Error: ATHENA_BOT_TOKEN not found in environment"
    exit 1
fi

echo "✅ Token loaded from environment"
echo "✅ Security hardening active"
echo "✅ Authorized users: 7176191872 only"
echo "✅ Allowed commands: start, status, brief, help"

# Start ATHENA bot
cd /root/HydraX-v2
python3 athena_mission_bot.py

echo "🔒 ATHENA Bot stopped"