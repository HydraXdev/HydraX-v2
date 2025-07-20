#!/usr/bin/env python3
"""
Test the /GHOSTED command functionality
"""

import sys
sys.path.append('/root/HydraX-v2/src')

try:
    from bitten_core.performance_commands import handle_ghosted_command
    print("✅ Successfully imported handle_ghosted_command")
    
    # Test the command
    print("\n🧪 Testing /GHOSTED command:")
    print("=" * 50)
    
    result = handle_ghosted_command()
    print(result)
    
    print("=" * 50)
    print("✅ /GHOSTED command test completed successfully!")
    
except Exception as e:
    print(f"❌ Error testing /GHOSTED command: {e}")
    import traceback
    traceback.print_exc()