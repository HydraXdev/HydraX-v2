#!/usr/bin/env python3
"""
Send a test Telegram alert with proper mission HUD link
"""
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
pips_to_tp = abs(mission['tp'] - mission['entry_price']) * 10000
actual_xp = int(mission['xp_reward'] * user_data['xp_multiplier'])

# Generate CORRECT webapp URLs
hud_url = f"https://joinbitten.com/hud?signal={signal_id}&user_id={user_data['user_id']}"
warroom_url = f"https://joinbitten.com/me?signal={signal_id}&user_id={user_data['user_id']}"

telegram_message = f'''
🚨 **ELITE GUARD SIGNAL ALERT** 🚨

**Mission ID:** `{signal_id}`

📊 **{mission['symbol']} {mission['direction']}**
━━━━━━━━━━━━━━━━━━━━━━

📍 **Entry:** {mission['entry_price']}
🛡️ **Stop Loss:** {mission['sl']} (-{pips_to_sl:.1f} pips)
🎯 **Take Profit:** {mission['tp']} (+{pips_to_tp:.1f} pips)

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
⚡ **ACTION BUTTONS**

🎯 [Open Mission HUD]({hud_url})
🏠 [Open War Room]({warroom_url})

**Quick Fire via Telegram:**
`/fire {signal_id}`

⏰ **Expires in:** 2 hours
━━━━━━━━━━━━━━━━━━━━━━

*Elite Guard v6.0 | CITADEL Shield Active*
*Pattern: {mission['pattern_type']}*
*Session: Market Testing Mode*
'''

print(telegram_message)
print('')
print('=' * 60)
print('📱 TELEGRAM ALERT SIMULATION')
print('=' * 60)
print('')
print('📊 TEST LINKS:')
print(f'Mission HUD: {hud_url}')
print(f'War Room: {warroom_url}')
print('')
print('🔥 FIRE COMMAND:')
print(f'/fire {signal_id}')
print('')
print('📝 MISSION DATA:')
print(f'Signal ID: {signal_id}')
print(f'Symbol: {mission["symbol"]} {mission["direction"]}')
print(f'Entry: {mission["entry_price"]} | SL: {mission["sl"]} | TP: {mission["tp"]}')
print('')
print('👤 USER OVERLAY:')
print(f'User ID: {user_data["user_id"]}')
print(f'Tier: {user_data["tier"]}')
print(f'Position: {user_lot} lots (base: {base_lot}, multiplier: {user_data["position_multiplier"]}x)')
print(f'Risk: ${risk_amount} ({user_data["risk_per_trade"]}%)')
print(f'XP: {actual_xp} (base: {mission["xp_reward"]}, multiplier: {user_data["xp_multiplier"]}x)')
print('')
print('✅ This demonstrates:')
print('1. Base mission data from Elite Guard')
print('2. User-specific overlay calculations')
print('3. Personalized position sizing by tier')
print('4. XP multipliers for higher tiers')
print('5. Proper WebApp links (HUD vs War Room)')