#!/usr/bin/env python3
"""
EMERGENCY SIGNAL GENERATOR
Generates signals immediately without Elite Guard complexity
"""
import json
import time
from datetime import datetime

def generate_emergency_signal():
    """Generate a basic signal to test system"""
    signal_id = f"EMERGENCY_EURUSD_{int(time.time())}"
    
    signal = {
        "signal_id": signal_id,
        "symbol": "EURUSD", 
        "direction": "BUY",
        "entry_price": 1.0900,
        "sl": 1.0850,
        "tp": 1.0950,
        "confidence": 75.0,
        "pattern_type": "EMERGENCY_TEST",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "citadel_score": 0,
        "risk_reward": 1.0,
        "target_pips": 50,
        "status": "pending",
        "completed": False,
        "signal_type": "RAPID_ASSAULT",
        "session": "EMERGENCY",
        "xp_reward": 100
    }
    
    # Write directly to truth log
    with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
        f.write(json.dumps(signal) + '\n')
    
    print(f"✅ EMERGENCY SIGNAL GENERATED: {signal_id}")
    return signal

if __name__ == "__main__":
    generate_emergency_signal()