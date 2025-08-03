#!/usr/bin/env python3
"""
Direct test of VENOM signal generation
"""

import sys
sys.path.insert(0, '/root/HydraX-v2')
from apex_venom_v7_unfiltered import ApexVenomV7Unfiltered
from datetime import datetime

# Create VENOM instance
venom = ApexVenomV7Unfiltered()

# Set market data manually
venom.last_market_data = {
    'EURUSD': {
        'close': 1.0850,
        'spread': 2.0,
        'volume': 1000,
        'timestamp': datetime.now()
    }
}

# Try to generate a signal
try:
    signal = venom.generate_venom_signal('EURUSD', datetime.now())
    if signal:
        print(f"✅ Signal generated: {signal['signal_id']}")
        print(f"   Direction: {signal['direction']}")
        print(f"   Confidence: {signal['confidence']}%")
        print(f"   Signal Type: {signal['signal_type']}")
    else:
        print("❌ No signal generated")
except Exception as e:
    print(f"❌ Error generating signal: {e}")
    import traceback
    traceback.print_exc()