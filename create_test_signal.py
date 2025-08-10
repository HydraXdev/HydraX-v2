#!/usr/bin/env python3
"""
Create a test signal for manual execution verification
"""

import json
import time
from datetime import datetime, timedelta

# Create a test Elite Guard signal
test_signal = {
    "signal_id": f"ELITE_GUARD_TEST_{int(time.time())}",
    "symbol": "EURUSD", 
    "direction": "BUY",
    "entry_price": 1.0950,
    "sl": 1.0940,
    "tp": 1.0970,
    "confidence": 95.0,
    "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
    "generated_at": datetime.now().isoformat(),
    "citadel_score": 8.5,
    "risk_reward": 2.0,
    "status": "pending",
    "completed": False,
    "signal_type": "PRECISION_STRIKE",
    "session": "OVERLAP",
    "xp_reward": 190
}

# Add to truth log
with open('truth_log.jsonl', 'a') as f:
    f.write(json.dumps(test_signal) + '\n')

# Create mission file
mission_data = {
    "mission_id": test_signal["signal_id"],
    "signal_id": test_signal["signal_id"],
    "signal": {
        "symbol": test_signal["symbol"],
        "direction": test_signal["direction"],
        "signal_type": test_signal["signal_type"],
        "entry_price": test_signal["entry_price"],
        "stop_loss": test_signal["sl"],
        "take_profit": test_signal["tp"],
        "stop_pips": 10,
        "target_pips": 20,
        "risk_reward": test_signal["risk_reward"],
        "confidence": test_signal["confidence"],
        "tcs_score": test_signal["confidence"],
        "pattern": test_signal["pattern_type"],
        "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
        "session": test_signal["session"],
        "timeframe": "M1"
    },
    "symbol": test_signal["symbol"],
    "direction": test_signal["direction"],
    "signal_type": test_signal["signal_type"],
    "entry_price": test_signal["entry_price"],
    "stop_loss": test_signal["sl"],
    "take_profit": test_signal["tp"],
    "stop_pips": 10,
    "target_pips": 20,
    "risk_reward": test_signal["risk_reward"],
    "confidence": test_signal["confidence"],
    "tcs_score": test_signal["confidence"],
    "pattern": test_signal["pattern_type"],
    "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
    "session": test_signal["session"],
    "timeframe": "M1",
    "shield_score": 8.5,
    "shield_classification": "SHIELD_APPROVED",
    "shield_label": "SHIELD APPROVED",
    "shield_emoji": "🛡️",
    "shield_explanation": "High confidence signal with strong pattern detection",
    "shield_recommendation": "Excellent setup - Full position recommended",
    "position_multiplier": 1.5,
    "created_at": datetime.now().isoformat(),
    "expires_at": (datetime.now() + timedelta(hours=2)).isoformat(),
    "hard_close_at": (datetime.now() + timedelta(hours=2, minutes=5)).isoformat(),
    "countdown_seconds": 7200,
    "xp_reward": 190,
    "status": "pending",
    "fire_count": 0,
    "user_fired": False,
    "source": "ELITE_GUARD_v6_TEST",
    "created_timestamp": int(time.time()),
    "processed_at": datetime.now().isoformat()
}

# Save mission file
mission_file = f"missions/{test_signal['signal_id']}.json"
with open(mission_file, 'w') as f:
    json.dump(mission_data, f, indent=2)

print(f"✅ Test signal created: {test_signal['signal_id']}")
print(f"📁 Mission file: {mission_file}")
print(f"🎯 Symbol: {test_signal['symbol']} {test_signal['direction']}")
print(f"💎 Confidence: {test_signal['confidence']}%")
print(f"🛡️ Shield Score: 8.5/10 (APPROVED)")
print(f"\n🔥 Ready for manual execution test!")
print(f"1. Go to webapp: http://134.199.204.67:8888/me")
print(f"2. Find mission: {test_signal['signal_id']}")
print(f"3. Click EXECUTE button")
print(f"4. Observe complete execution flow")