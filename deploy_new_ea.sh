#!/bin/bash

# Comprehensive EA deployment script for BITTENBridge_Close_Enabled

echo "🚀 Deploying BITTENBridge_Close_Enabled EA"
echo "========================================="

# Step 1: Update all source locations
echo "📝 Step 1: Updating source files..."
cp /root/HydraX-v2/mq5/BITTENBridge_Close_Enabled.mq5 /root/HydraX-v2/mq5/BITTENBridge_TradeExecutor.mq5
cp /root/HydraX-v2/mq5/BITTENBridge_Close_Enabled.mq5 /root/HydraX-MT5-Terminal-Automation/MQL5/Experts/BITTENBridge_TradeExecutor.mq5

# Step 2: Update container files
echo "📝 Step 2: Deploying to container..."
if docker ps | grep -q "hydrax-mt5-ea_test"; then
    # Copy to both locations in container
    docker cp /root/HydraX-v2/mq5/BITTENBridge_Close_Enabled.mq5 hydrax-mt5-ea_test:/wine/drive_c/Program\ Files/MetaTrader\ 5/MQL5/Experts/BITTENBridge_TradeExecutor.mq5
    docker cp /root/HydraX-v2/mq5/BITTENBridge_Close_Enabled.mq5 hydrax-mt5-ea_test:/wine/drive_c/MetaTrader5/MQL5/Experts/BITTENBridge_TradeExecutor.mq5
    
    # Create uuid.txt file
    echo "📝 Step 3: Creating uuid.txt..."
    docker exec hydrax-mt5-ea_test bash -c "echo 'hydrax-mt5-ea_test' > '/wine/drive_c/Program Files/MetaTrader 5/MQL5/Files/uuid.txt'"
    docker exec hydrax-mt5-ea_test bash -c "echo 'hydrax-mt5-ea_test' > /wine/drive_c/MetaTrader5/MQL5/Files/uuid.txt"
    
    # Set permissions
    echo "📝 Step 4: Setting permissions..."
    docker exec hydrax-mt5-ea_test chmod -R 777 "/wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts/"
    docker exec hydrax-mt5-ea_test chmod -R 777 /wine/drive_c/MetaTrader5/MQL5/Experts/
    docker exec hydrax-mt5-ea_test chmod -R 777 "/wine/drive_c/Program Files/MetaTrader 5/MQL5/Files/"
    docker exec hydrax-mt5-ea_test chmod -R 777 /wine/drive_c/MetaTrader5/MQL5/Files/
else
    echo "❌ Container hydrax-mt5-ea_test is not running!"
fi

# Step 5: Update Docker build files
echo "📝 Step 5: Updating Docker build files..."
cp /root/HydraX-v2/mq5/BITTENBridge_Close_Enabled.mq5 /root/HydraX-v2/src/bridge/BITTENBridge_v3_ENHANCED.mq5
cp /root/HydraX-v2/mq5/BITTENBridge_Close_Enabled.mq5 /root/HydraX-v2/webapp/static/BITTENBridge_v3_ENHANCED.mq5

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📌 New features in BITTENBridge_Close_Enabled:"
echo "   - Close position support: {\"action\":\"close\",\"symbol\":\"EURUSD\"}"
echo "   - UUID tracking from uuid.txt file"
echo "   - Trade reporting to https://terminus.joinbitten.com/report"
echo "   - Enhanced error messages with emojis"
echo "   - WebRequest support for trade reporting"
echo ""
echo "⚠️  Important notes:"
echo "   1. The EA will auto-compile when MT5 loads it"
echo "   2. Make sure to allow WebRequests to https://terminus.joinbitten.com in MT5"
echo "   3. The uuid.txt file has been created in MQL5/Files/"
echo "   4. Test with: {\"action\":\"close\",\"symbol\":\"EURUSD\"} in fire.txt"