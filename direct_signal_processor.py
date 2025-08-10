#!/usr/bin/env python3
"""
Direct Signal Processor - Bypasses broken webapp
Receives Elite Guard signals and creates missions directly
"""

import zmq
import json
import time
import os
import telebot
from datetime import datetime

# Bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7854827710:AAE9kCptktGxwXP5cqOF4A_zqQdYSHSxXx0')
bot = telebot.TeleBot(BOT_TOKEN)

# User data (would normally come from database)
USER_DATA = {
    '7176191872': {
        'tier': 'COMMANDER',
        'balance': 10000,
        'risk_per_trade': 2.0,
        'position_multiplier': 2.0,
        'xp_multiplier': 1.5,
        'max_positions': 5
    }
}

def process_signal(signal_data):
    """Process Elite Guard signal and create mission"""
    print(f"📡 Processing signal: {signal_data['signal_id']}")
    
    # Create mission file
    mission_file = f"/root/HydraX-v2/missions/{signal_data['signal_id']}.json"
    mission = {
        **signal_data,
        'mission_id': signal_data['signal_id'],
        'base_lot_size': 0.01,
        'expiry_time': int(time.time()) + 7200,
        'status': 'pending'
    }
    
    with open(mission_file, 'w') as f:
        json.dump(mission, f, indent=2)
    
    print(f"✅ Mission created: {mission_file}")
    
    # Send Telegram notifications
    for user_id, user_info in USER_DATA.items():
        send_notification(user_id, user_info, signal_data)

def send_notification(user_id, user_info, signal):
    """Send personalized Telegram notification"""
    
    # Calculate user-specific values
    base_lot = 0.01
    user_lot = base_lot * user_info['position_multiplier']
    risk_amount = user_info['balance'] * (user_info['risk_per_trade'] / 100)
    pips_to_sl = abs(signal['entry_price'] - signal['sl']) * 10000
    pips_to_tp = abs(signal['tp'] - signal['entry_price']) * 10000
    actual_xp = int(signal.get('xp_reward', 100) * user_info['xp_multiplier'])
    
    message = f"""🚨 ELITE GUARD SIGNAL 🚨

Signal: {signal['signal_id']}

📊 {signal['symbol']} {signal['direction']}
━━━━━━━━━━━━━━━━━━━━━━

📍 Entry: {signal['entry_price']}
🛡️ SL: {signal['sl']} (-{pips_to_sl:.1f} pips)
🎯 TP: {signal['tp']} (+{pips_to_tp:.1f} pips)

💪 Confidence: {signal['confidence']}%
🛡️ CITADEL: {signal.get('citadel_score', 0)}/10
📈 Pattern: {signal.get('pattern_type', 'UNKNOWN')}

━━━━━━━━━━━━━━━━━━━━━━
👤 YOUR DATA ({user_info['tier']})

💰 Position: {user_lot:.2f} lots
⚠️ Risk: ${risk_amount:.0f} ({user_info['risk_per_trade']}%)
🎯 Win: ${risk_amount * signal.get('risk_reward', 2):.0f}
✨ XP: {actual_xp}

━━━━━━━━━━━━━━━━━━━━━━

🔥 FIRE: /fire {signal['signal_id']}

🌐 HUD: http://134.199.204.67:8888/hud?signal={signal['signal_id']}

━━━━━━━━━━━━━━━━━━━━━━
⏰ Expires: 2 hours
━━━━━━━━━━━━━━━━━━━━━━"""
    
    try:
        bot.send_message(int(user_id), message)
        print(f"✅ Notification sent to {user_id}")
    except Exception as e:
        print(f"❌ Failed to send to {user_id}: {e}")

def main():
    """Main loop - listen for Elite Guard signals"""
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5557")
    subscriber.subscribe(b'')
    
    print("🚀 Direct Signal Processor started")
    print("📡 Listening for Elite Guard signals on port 5557...")
    
    while True:
        try:
            message = subscriber.recv_string(zmq.NOBLOCK)
            
            if message.startswith("ELITE_GUARD_SIGNAL "):
                json_str = message[19:]
                signal = json.loads(json_str)
                process_signal(signal)
            else:
                try:
                    signal = json.loads(message)
                    process_signal(signal)
                except:
                    pass
                    
        except zmq.Again:
            time.sleep(0.1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()