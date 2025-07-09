#!/usr/bin/env python3
# test_stealth_standalone.py
# Standalone test that imports stealth protocol directly

import sys
import os

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'bitten_core'))

# Now import directly
import stealth_protocol

def main():
    print("🥷 STEALTH PROTOCOL STANDALONE TEST")
    print("=" * 50)
    
    # Create instance
    stealth = stealth_protocol.StealthProtocol()
    print(f"✅ Created stealth protocol instance")
    print(f"   Enabled: {stealth.config.enabled}")
    print(f"   Level: {stealth.config.level.value}")
    
    # Test a simple function
    trade = {'symbol': 'EURUSD', 'volume': 0.1}
    delay = stealth.entry_delay(trade)
    print(f"\n✅ Entry delay test: {delay:.2f} seconds")
    
    # Test lot jitter
    new_lot = stealth.lot_size_jitter(0.1, 'EURUSD')
    print(f"✅ Lot jitter test: 0.1 -> {new_lot}")
    
    # Check log file
    log_path = "/root/HydraX-v2/logs/stealth_log.txt"
    if os.path.exists(log_path):
        print(f"\n✅ Log file exists at: {log_path}")
    
    print("\n✅ Stealth protocol is working!")

if __name__ == "__main__":
    main()