#!/usr/bin/env python3
"""
Test script to verify integration with mission flow
This simulates what happens when generates a real signal
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add paths for imports
sys.path.append('/root/HydraX-v2')

# Test the integration
async def test_apex_integration():
    """Test that signals properly trigger the integrated flow"""
    
    print("🧪 Testing Integration with Mission Flow")
    print("=" * 50)
    
    # Import the integrated flow
    from apex_mission_integrated_flow import process_apex_signal_direct
    
    # Create a realistic signal (matching apex_v5_lean.py format)
    apex_signal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs': 82,
        'signal_type': 'SNIPER OPS',
        'entry_price': 1.09045,
        'bid': 1.09040,
        'ask': 1.09050,
        'spread': 1.0,
        'timestamp': datetime.now().isoformat(),
        'signal_number': 999
    }
    
    print(f"📊 Testing with signal: {apex_signal['signal_type']} - {apex_signal['symbol']} {apex_signal['direction']}")
    print(f"🎯 TCS Score: {apex_signal['tcs']}%")
    print(f"💰 Entry Price: {apex_signal['entry_price']}")
    print()
    
    # Process through integrated flow
    result = await process_apex_signal_direct(apex_signal)
    
    if result['success']:
        print("✅ COMPLETE INTEGRATION SUCCESS!")
        print(f"📋 Mission ID: {result['mission_id']}")
        print(f"📱 Telegram Sent: {result['telegram_sent']}")
        print(f"🌐 WebApp URL: {result['webapp_url']}")
        
        # Check enhanced signal data
        enhanced = result['enhanced_signal']
        print(f"📈 RR Ratio: 1:{enhanced.get('risk_reward_ratio', 'N/A')}")
        print(f"🛑 Stop Loss: {enhanced.get('stop_loss', 'N/A')}")
        print(f"🎯 Take Profit: {enhanced.get('take_profit', 'N/A')}")
        
        # Verify mission file was created
        missions_dir = "/root/HydraX-v2/missions"
        mission_file = f"{missions_dir}/{result['mission_id']}.json"
        
        if os.path.exists(mission_file):
            print(f"💾 Mission file created: {mission_file}")
            
            # Load and verify mission data
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
            
            print(f"🎮 Mission Title: {mission_data['mission']['title']}")
            print(f"⏰ Expires: {mission_data['timing']['expires_at']}")
            print(f"👤 User Tier: {mission_data['user']['tier']}")
            
            print("\n🚀 FLOW VERIFICATION COMPLETE!")
            print("→ Mission → TOC → Telegram → WebApp ✅")
            
        else:
            print("❌ Mission file not found")
            
    else:
        print("❌ INTEGRATION FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(test_apex_integration())