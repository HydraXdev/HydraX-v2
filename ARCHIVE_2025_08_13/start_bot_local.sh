#!/bin/bash
# BITTEN Bot Launcher with Local Webapp

# Load environment
source /root/HydraX-v2/.env.bitten

# Kill existing bot processes
pkill -f "bitten_bot.py" || true

# Start bot with new configuration
cd /root/HydraX-v2
python3 WEBAPP_SIGNAL_BOT.py 2>&1 | tee -a webapp_signal_bot.log &

echo "✅ BITTEN bot started with local webapp configuration"
echo "📍 Webapp URL: $BITTEN_WEBAPP_URL"
echo "🎯 HUD URL: $BITTEN_HUD_URL"
