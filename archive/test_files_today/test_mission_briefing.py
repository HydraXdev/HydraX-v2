#!/usr/bin/env python3
"""
Test mission briefing generation with APEX signals
"""

import sys
import os
sys.path.append('/root/HydraX-v2/src/bitten_core')

from mission_briefing_generator_active import APEXv5MissionBriefingGenerator
import json
from datetime import datetime

def test_mission_briefing():
    """Test mission briefing generation with APEX signal format"""
    
    print("🎯 TESTING MISSION BRIEFING GENERATION")
    print("=" * 50)
    print()
    
    # Initialize generator
    generator = APEXv5MissionBriefingGenerator()
    
    # Test signals matching APEX output format
    test_signals = [
        {
            # RAPID_ASSAULT signal from APEX
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.0900,
            'signal_type': 'RAPID_ASSAULT',
            'tcs': 75,
            'pattern': 'APEX Pattern',
            'timeframe': 'M5',
            'session': 'LONDON',
            'confluence_count': 1,
            'bid': 1.08995,
            'ask': 1.09005,
            'spread': 1.0
        },
        {
            # SNIPER_OPS signal from APEX
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'entry_price': 1.2500,
            'signal_type': 'SNIPER_OPS',
            'tcs': 85,
            'pattern': 'APEX Pattern',
            'timeframe': 'M15',
            'session': 'OVERLAP',
            'confluence_count': 2,
            'bid': 1.24995,
            'ask': 1.25005,
            'spread': 1.0
        }
    ]
    
    user_data = {
        'tier': 'FANG',
        'daily_signals': 12,
        'daily_pips': 45.3,
        'win_rate': 72.5
    }
    
    account_data = {
        'balance': 10000.0
    }
    
    for i, signal_data in enumerate(test_signals, 1):
        print(f"🔥 Test {i}: {signal_data['signal_type']} - {signal_data['symbol']}")
        print(f"   Entry: {signal_data['entry_price']}")
        print(f"   TCS: {signal_data['tcs']}%")
        print(f"   Session: {signal_data['session']}")
        print()
        
        try:
            # Generate mission briefing
            briefing = generator.generate_v5_mission_briefing(
                signal_data, user_data, account_data
            )
            
            print(f"✅ Mission Generated:")
            print(f"   ID: {briefing.mission_id}")
            print(f"   Title: {briefing.mission_title}")
            print(f"   Signal Class: {briefing.signal_class.value}")
            print(f"   Mission Type: {briefing.mission_type.value}")
            print(f"   Urgency: {briefing.urgency_level.value}")
            print(f"   Description: {briefing.mission_description}")
            print()
            
            # Test webapp formatting
            webapp_format = generator.format_for_webapp(briefing)
            
            print(f"📱 WebApp Format:")
            print(f"   Pair: {webapp_format['pair']} {webapp_format['pair_icon']}")
            print(f"   Direction: {webapp_format['direction']}")
            print(f"   Entry: {webapp_format['entry_price']}")
            print(f"   Risk: {webapp_format['risk_amount']} ({webapp_format['risk_percentage']})")
            print(f"   Expected Profit: {webapp_format['dollar_amount']}")
            print(f"   Session Boost: {webapp_format['session_boost']} ({webapp_format['session_multiplier']})")
            print()
            
            # Show tactical notes
            print(f"📋 Tactical Notes:")
            for note in briefing.tactical_notes[:3]:  # Show first 3
                print(f"   • {note}")
            print()
            
        except Exception as e:
            print(f"❌ Error generating mission: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
        print()
    
    print("🎯 Mission briefing generation test complete!")
    print("✅ Missions can convert APEX signals to user-friendly format")
    print("🔥 Ready to connect to TOC firing system")

if __name__ == "__main__":
    test_mission_briefing()