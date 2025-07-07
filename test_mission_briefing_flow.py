#!/usr/bin/env python3
"""Test the complete mission briefing flow with existing components"""

import asyncio
import json
from src.bitten_core.mission_briefing_generator import MissionBriefingGenerator, MissionType, UrgencyLevel
from src.bitten_core.signal_alerts import SignalAlertSystem, SignalAlert

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861
WEBAPP_URL = 'https://joinbitten.com/mission'

async def test_full_flow():
    """Test complete flow from signal to mission briefing"""
    
    # 1. Generate Mission Briefing
    generator = MissionBriefingGenerator()
    
    # Create signal data
    signal_data = {
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'stop_loss': 1.0830,
        'take_profit': 1.0880,
        'tcs_score': 87,
        'active_traders': 12
    }
    
    # Generate full mission briefing
    mission = generator.generate_mission_briefing(
        signal_data=signal_data,
        mission_type=MissionType.ARCADE_SCALP,
        user_tier='FANG'
    )
    
    print("📋 Generated Mission Briefing:")
    print(f"Callsign: {mission.callsign}")
    print(f"TCS Score: {mission.tcs_score}%")
    print(f"Risk/Reward: 1:{mission.risk_reward_ratio}")
    print(f"Active Operators: {mission.active_operators}")
    
    # 2. Send Brief Telegram Alert
    alert_system = SignalAlertSystem(
        bot_token=BOT_TOKEN,
        hud_webapp_url=WEBAPP_URL
    )
    
    # Create brief alert
    signal_alert = SignalAlert(
        signal_id=mission.mission_id,
        symbol=mission.symbol,
        direction=mission.direction,
        confidence=mission.tcs_score / 100,
        urgency=mission.urgency.value,
        timestamp=mission.created_at,
        expires_at=mission.expires_at
    )
    
    print("\n📱 Telegram Alert Preview:")
    print(f"⚡ SIGNAL DETECTED")
    print(f"{signal_alert.symbol} | {signal_alert.direction} | {int(signal_alert.confidence * 100)}% confidence")
    print(f"⏰ Expires in {(signal_alert.expires_at - signal_alert.timestamp) // 60} minutes")
    print("[🎯 VIEW INTEL]")
    
    # 3. Mission Briefing Data for WebApp
    webapp_data = {
        'mission': mission.__dict__,
        'user_stats': {
            'last_7d_pnl': 127.50,
            'win_rate': 73,
            'trades_today': 3,
            'rank': 'WARRIOR'
        },
        'live_stats': {
            'fire_count': 12,
            'time_remaining': mission.time_remaining
        }
    }
    
    print("\n🌐 WebApp Mission Briefing will show:")
    print("- User stats header with link to /me")
    print("- Full tactical briefing with tier-specific intel")
    print("- Live countdown and fire count")
    print("- Single FIRE button for execution")
    print("- Education tabs based on tier")

if __name__ == "__main__":
    asyncio.run(test_full_flow())