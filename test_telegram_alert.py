#!/usr/bin/env python3
import json
import sys
sys.path.append('/root/HydraX-v2')

# Load the test signal
signal_id = 'ELITE_GUARD_EURUSD_1754828514'
mission_file = f'/root/HydraX-v2/missions/{signal_id}.json'

with open(mission_file, 'r') as f:
    mission = json.load(f)

# Simulate user-specific overlay data for Commander tier
user_data = {
    'user_id': '7176191872',
    'tier': 'COMMANDER',
    'balance': 10000,
    'risk_per_trade': 2.0,  # 2% risk
    'max_positions': 5,
    'position_multiplier': 2.0,  # Commander gets 2x position size
    'xp_multiplier': 1.5,  # Commander gets 1.5x XP
    'fire_mode': 'manual',
    'active_positions': 2
}

# Calculate user-specific values
base_lot = mission['base_lot_size']
user_lot = base_lot * user_data['position_multiplier']
risk_amount = user_data['balance'] * (user_data['risk_per_trade'] / 100)
pips_to_sl = abs(mission['entry_price'] - mission['sl']) * 10000
potential_loss = user_lot * pips_to_sl * 10  # $10 per pip for 0.01 lot
actual_xp = int(mission['xp_reward'] * user_data['xp_multiplier'])

# Generate personalized mission briefing
webapp_url = f"https://joinbitten.com/me?signal={signal_id}&user={user_data['user_id']}"

telegram_message = f'''
🚨 **ELITE GUARD SIGNAL ALERT** 🚨

**Mission ID:** `{signal_id}`

📊 **{mission['symbol']} {mission['direction']}**
━━━━━━━━━━━━━━━━━━━━━━

📍 **Entry:** {mission['entry_price']}
🛡️ **Stop Loss:** {mission['sl']} (-{pips_to_sl:.1f} pips)
🎯 **Take Profit:** {mission['tp']} (+{abs(mission['tp'] - mission['entry_price']) * 10000:.1f} pips)

💪 **Confidence:** {mission['confidence']}%
🛡️ **CITADEL Score:** {mission['citadel_score']}/10
📈 **Pattern:** {mission['pattern_type']}
⚡ **Risk/Reward:** 1:{mission['risk_reward']}

━━━━━━━━━━━━━━━━━━━━━━
👤 **YOUR PERSONALIZED DATA**

🎖️ **Tier:** {user_data['tier']}
💰 **Your Position:** {user_lot:.2f} lots
⚠️ **Risk:** ${risk_amount:.2f} ({user_data['risk_per_trade']}%)
🎯 **Potential Win:** ${risk_amount * mission['risk_reward']:.2f}
✨ **XP Reward:** {actual_xp} XP

📊 **Active Positions:** {user_data['active_positions']}/{user_data['max_positions']}
🔫 **Fire Mode:** {user_data['fire_mode'].upper()}

━━━━━━━━━━━━━━━━━━━━━━
⚡ **ACTION REQUIRED**

[🌐 Open Mission HUD]({webapp_url})

To execute via Telegram:
`/fire {signal_id}`

Or press the 🔫 FIRE button in your War Room

⏰ **Expires in:** 2 hours
━━━━━━━━━━━━━━━━━━━━━━

*Elite Guard v6.0 | CITADEL Shield Active*
'''

print(telegram_message)
print('')
print('=' * 50)
print('📱 This is what would be sent to your Telegram')
print('=' * 50)
print('')
print(f'WebApp URL: {webapp_url}')
print(f'Fire Command: /fire {signal_id}')
print('')
print('📝 Mission data saved to:')
print(f'   - Truth Log: /root/HydraX-v2/truth_log.jsonl')
print(f'   - Mission File: {mission_file}')
print('')
print('To test the fire command:')
print(f'1. Copy this command: /fire {signal_id}')
print('2. Send it to the BITTEN bot on Telegram')
print('3. The system will process it through the ZMQ pipeline to the EA')