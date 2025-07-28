#!/usr/bin/env python3
"""
Start REAL Signal Engine
This uses the ACTUAL signal analysis, not random numbers!
"""

import os
import sys

# Add paths
sys.path.insert(0, '/root/HydraX-v2')

print("=" * 50)
print("STARTING REAL SIGNAL ENGINE")
print("This is the AUTHORIZED engine with actual analysis")
print("NOT a synthetic/fake generator!")
print("=" * 50)

try:
    from AUTHORIZED_SIGNAL_ENGINE import AuthorizedSignalEngine
    
    # Create and start the engine
    engine = AuthorizedSignalEngine()
    
    print("\n✅ REAL Signal Engine initialized")
    print(f"Threshold: {engine.current_threshold}%")
    print(f"Pairs: {len(engine.pairs)}")
    print("\nStarting signal generation from REAL market data...")
    
    # Start the engine
    while True:
        signals = engine.generate_signals()
        if signals:
            print(f"\n🎯 Generated {len(signals)} REAL signals from market analysis")
            for signal in signals:
                print(f"  - {signal}")
        
        # Wait before next check
        import time
        time.sleep(60)
        
except KeyboardInterrupt:
    print("\n🛑 Engine stopped by user")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()