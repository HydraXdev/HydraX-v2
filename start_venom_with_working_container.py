#!/usr/bin/env python3
"""
Start VENOM v7 with the working MT5 container
"""

import sys
import os

# Add src to path
sys.path.insert(0, '/root/HydraX-v2/src')
sys.path.insert(0, '/root/HydraX-v2')

from apex_venom_v7_with_smart_timer import ApexVenomV7WithTimer
from start_venom_live import LiveDataVenomEngine

if __name__ == "__main__":
    print("🐍 Starting VENOM v7 with local-mt5-test-deprecated container")
    
    # Create engine with the working container
    engine = LiveDataVenomEngine()
    engine.mt5_container = "local-mt5-test-deprecated"  # Override to use working container
    engine.venom_engine.mt5_container = "local-mt5-test-deprecated"
    
    print(f"📊 Using container: {engine.mt5_container}")
    
    # Run the engine
    engine.run_live_engine()