#!/usr/bin/env python3
# start_bitten.py
# BITTEN System Startup Script

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bitten_core.webhook_server import main

if __name__ == '__main__':
    print("🚀 Starting BITTEN Trading Operations Center...")
    print("=" * 50)
    main()