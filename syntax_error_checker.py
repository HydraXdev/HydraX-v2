#!/usr/bin/env python3
"""
Check syntax errors and identify why files are broken
"""

import ast
import os
from pathlib import Path

def check_syntax_errors():
    """Check specific files for syntax errors"""
    
    error_files = [
        'BITTEN_InitSync_Module.py',
        'setup_stripe_products.py', 
        'venom_vs_apex_validator.py',
        'bitten_alerts_actual.py',
        'setup_persistent_menu.py',
        'apex_v5_lean.py',
        'user_mission_system.py',
        'AUTONOMOUS_OPERATION_VALIDATOR.py',
        'webapp_server.py',
        'commander_throne.py'
    ]
    
    print("🔍 CHECKING SYNTAX ERRORS IN DETAIL")
    print("="*60)
    
    for filename in error_files:
        filepath = Path(f"/root/HydraX-v2/{filename}")
        if not filepath.exists():
            print(f"❌ {filename}: FILE NOT FOUND")
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse
            try:
                ast.parse(content)
                print(f"✅ {filename}: SYNTAX OK")
            except SyntaxError as e:
                print(f"❌ {filename}: {e}")
                print(f"   Line {e.lineno}: {e.text}")
                
        except Exception as e:
            print(f"❌ {filename}: READ ERROR - {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_syntax_errors()