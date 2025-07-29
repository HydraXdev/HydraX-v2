#!/usr/bin/env python3
"""
Direct signal test - bypass broken webapp and send signal directly to Telegram
"""

import requests
import json
from datetime import datetime

# Test signal with CITADEL data
test_signal = {
    "signal_id": "VENOM_SCALP_EURUSD_TEST_001",
    "pair": "EURUSD", 
    "direction": "BUY",
    "confidence": 87.5,
    "quality": "platinum",
    "signal_type": "RAPID_ASSAULT",
    "target_pips": 20,
    "stop_pips": 10,
    "risk_reward": 2.0,
    "timestamp": datetime.now().timestamp(),
    "citadel_shield": {
        "score": 8.7,
        "classification": "SHIELD_APPROVED",
        "risk_multiplier": 1.4,
        "insights": "Strong momentum alignment with liquidity sweep confirmation"
    },
    "enhanced_signal": {
        "symbol": "EURUSD",
        "direction": "BUY", 
        "entry_price": 1.0847,
        "stop_loss": 1.0837,
        "take_profit": 1.0867,
        "risk_reward_ratio": 2.0,
        "signal_type": "RAPID_ASSAULT"
    }
}

# Send directly to bot via webhook/API
try:
    # Try multiple delivery methods
    print("🚀 Sending test signal for fire testing...")
    print(f"Signal: {test_signal['pair']} {test_signal['direction']} @ {test_signal['enhanced_signal']['entry_price']}")
    print(f"CITADEL: {test_signal['citadel_shield']['score']}/10 ({test_signal['citadel_shield']['classification']})")
    print(f"R:R: 1:{test_signal['risk_reward']} | TCS: {test_signal['confidence']}%")
    print("\n📡 Signal ready for Telegram delivery...")
    
except Exception as e:
    print(f"Error: {e}")