#!/usr/bin/env python3
"""
Modified realistic signal bot with higher chance for testing
"""

import sys
import os

# Monkey patch the signal config before importing
import SIGNALS_REALISTIC
SIGNALS_REALISTIC.SIGNAL_CONFIG['signal_chance'] = 0.8  # 80% chance
SIGNALS_REALISTIC.SIGNAL_CONFIG['check_interval'] = 5   # Check every 5 seconds

print("🚀 Starting high-frequency realistic signals for testing...")
print("Signal chance: 80% (vs 12% normal)")
print("Check interval: 5s (vs 30s normal)")
print("\nExpect signals within 10-15 seconds...")

# Run the main function
SIGNALS_REALISTIC.main()
