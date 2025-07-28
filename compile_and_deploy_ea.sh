#!/bin/bash

# Script to compile and deploy the new BITTENBridge_Close_Enabled EA

echo "🔧 BITTENBridge EA Deployment Script"
echo "====================================="

# Check if container is running
if ! docker ps | grep -q "hydrax-mt5-ea_test"; then
    echo "❌ Container hydrax-mt5-ea_test is not running!"
    exit 1
fi

echo "📝 Step 1: Copying new EA to container..."
docker cp /root/HydraX-v2/mq5/BITTENBridge_Close_Enabled.mq5 hydrax-mt5-ea_test:/wine/drive_c/MetaTrader5/MQL5/Experts/

echo "📝 Step 2: Renaming as BITTENBridge_TradeExecutor.mq5 (keeping compatibility)..."
docker exec hydrax-mt5-ea_test bash -c "cd /wine/drive_c/MetaTrader5/MQL5/Experts && cp BITTENBridge_Close_Enabled.mq5 BITTENBridge_TradeExecutor.mq5"

echo "📝 Step 3: Setting permissions..."
docker exec hydrax-mt5-ea_test chmod 777 /wine/drive_c/MetaTrader5/MQL5/Experts/BITTENBridge_TradeExecutor.mq5

echo "📝 Step 4: Creating uuid.txt file..."
docker exec hydrax-mt5-ea_test bash -c "echo 'hydrax-mt5-ea_test' > /wine/drive_c/MetaTrader5/MQL5/Files/uuid.txt"

echo "📝 Step 5: Verifying files..."
docker exec hydrax-mt5-ea_test ls -la /wine/drive_c/MetaTrader5/MQL5/Experts/BITTENBridge_TradeExecutor.*

echo ""
echo "✅ EA deployment complete!"
echo ""
echo "📌 New features in BITTENBridge_Close_Enabled:"
echo "   - Close position support via action='close'"
echo "   - UUID tracking from uuid.txt"
echo "   - Trade reporting to https://terminus.joinbitten.com/report"
echo "   - Enhanced error messages with emojis"
echo ""
echo "⚠️  Note: The EA needs to be compiled within MT5 Terminal."
echo "    It will auto-compile on first load or you can manually"
echo "    compile in MetaEditor inside the container."