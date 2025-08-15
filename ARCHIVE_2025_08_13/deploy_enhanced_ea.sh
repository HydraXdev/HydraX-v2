#!/bin/bash
# Deploy Enhanced EA to MT5 Farm

echo "🚀 Deploying Enhanced BITTEN EA v3"
echo "=================================="

# Copy enhanced EA to farm
echo "📦 Copying enhanced EA to farm server..."
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no \
    /root/HydraX-v2/src/bridge/BITTENBridge_v3_ENHANCED.mq5 \
    root@129.212.185.102:/opt/bitten/

# Copy enhanced adapter
echo "🐍 Copying enhanced Python adapter..."
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no \
    /root/HydraX-v2/src/bitten_core/mt5_enhanced_adapter.py \
    root@129.212.185.102:/opt/bitten/

# Update the enhanced signal flow
echo "📊 Copying enhanced signal flow..."
sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no \
    /root/HydraX-v2/src/bitten_core/complete_signal_flow_v2.py \
    root@129.212.185.102:/opt/bitten/

# Create setup instructions
cat << 'INSTRUCTIONS' > /tmp/enhanced_setup.txt
BITTEN Enhanced EA v3 Setup
===========================

For each MT5 terminal (broker1, broker2, broker3):

1. Copy EA to Experts folder:
   - From: /opt/bitten/BITTENBridge_v3_ENHANCED.mq5
   - To: [MT5]/MQL5/Experts/

2. Compile in MetaEditor (F7)

3. Attach to EURUSD chart with these settings:
   - InstructionFile: bitten_instructions_secure.txt
   - CommandFile: bitten_commands_secure.txt
   - ResultFile: bitten_results_secure.txt
   - StatusFile: bitten_status_secure.txt
   - PositionsFile: bitten_positions_secure.txt
   - AccountFile: bitten_account_secure.txt
   - MarketFile: bitten_market_secure.txt
   - CheckIntervalMs: 100
   - MagicNumber: 20250626
   - EnableTrailing: true
   - EnablePartialClose: true
   - EnableBreakEven: true
   - EnableMultiTP: true

4. Enable AutoTrading

5. Verify EA shows: "BITTEN Enhanced Bridge v3 ready"

New Features:
- Two-way account data communication
- Risk-based automatic lot calculation
- Break-even management
- Partial close (50% default)
- Multi-step TP (3 levels)
- Trailing stop
- Live market data feed

Testing:
1. Check account data: cat bitten_account_secure.txt
2. Check positions: cat bitten_positions_secure.txt
3. Check market data: cat bitten_market_secure.txt
INSTRUCTIONS

sshpass -p 'bNL9SqfNXhWL4#y' scp -o StrictHostKeyChecking=no \
    /tmp/enhanced_setup.txt \
    root@129.212.185.102:/opt/bitten/

echo ""
echo "✅ Enhanced EA deployed!"
echo ""
echo "📋 Summary of Enhancements:"
echo "- Account balance/equity/margin reporting"
echo "- Automatic lot sizing from risk percentage"
echo "- Break-even management (20 points profit)"
echo "- Partial close capability (take 50% profit)"
echo "- Multi-step TP (30%/30%/40% at 3 levels)"
echo "- Trailing stop management"
echo "- Live position P&L tracking"
echo "- Daily P&L calculation"
echo ""
echo "🎯 Next Steps:"
echo "1. Install EA in each MT5 terminal"
echo "2. Configure with enhanced settings"
echo "3. Test account data: curl http://129.212.185.102:8001/live_data"
echo "4. Test position management features"
echo ""
echo "The system now has full two-way communication!"