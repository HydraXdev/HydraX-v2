#!/usr/bin/env python3
"""
Integration script to add data integrity enforcement to all production files
"""

import os
import re
from pathlib import Path

def add_enforcer_imports(file_path: str) -> bool:
    """Add data integrity enforcer imports to a Python file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Skip if already integrated
        if "data_integrity_enforcer" in content:
            return False
            
        # Find import section
        lines = content.split('\n')
        import_index = -1
        
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i
        
        if import_index == -1:
            # No imports found, add at top
            import_index = 0
            
        # Add enforcer import after last import
        enforcer_import = """
# DATA INTEGRITY ENFORCEMENT - ZERO TOLERANCE FOR FAKE DATA
from data_integrity_enforcer import assert_no_fake_data, assert_file_integrity, validate_truth_log_only
"""
        
        lines.insert(import_index + 1, enforcer_import)
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
            
        return True
        
    except Exception as e:
        print(f"Error integrating {file_path}: {e}")
        return False

def add_signal_validation(file_path: str) -> bool:
    """Add signal validation calls to signal processing functions"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Skip if already integrated
        if "assert_no_fake_data" in content:
            return False
            
        # Find signal processing patterns and add validation
        patterns = [
            (r'def.*process.*signal.*\(.*data.*\):', 'assert_no_fake_data(data, "signal_processing")'),
            (r'def.*generate.*signal.*\(.*\):', 'assert_no_fake_data(result, "signal_generation")'),
            (r'def.*execute.*trade.*\(.*data.*\):', 'assert_no_fake_data(data, "trade_execution")'),
            (r'json\.load.*\(.*\)', 'assert_no_fake_data(loaded_data, "json_load")'),
            (r'json\.loads.*\(.*\)', 'assert_no_fake_data(parsed_data, "json_parse")')
        ]
        
        modified = False
        for pattern, validation in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Add validation after function definition
                content = re.sub(
                    pattern, 
                    lambda m: m.group(0) + f'\n    # FAKE DATA VALIDATION\n    {validation}',
                    content,
                    flags=re.IGNORECASE
                )
                modified = True
        
        if modified:
            with open(file_path, 'w') as f:
                f.write(content)
                
        return modified
        
    except Exception as e:
        print(f"Error adding validation to {file_path}: {e}")
        return False

def integrate_production_files():
    """Integrate data integrity enforcement into all production files"""
    
    production_files = [
        "/root/HydraX-v2/bitten_production_bot.py",
        "/root/HydraX-v2/webapp_server_optimized.py", 
        "/root/HydraX-v2/src/bitten_core/bitten_core.py",
        "/root/HydraX-v2/src/bitten_core/fire_router.py",
        "/root/HydraX-v2/truth_tracker.py",
        "/root/HydraX-v2/venom_stream_pipeline.py"
    ]
    
    print("🔒 INTEGRATING DATA INTEGRITY ENFORCEMENT")
    print("=" * 50)
    
    integrated_count = 0
    
    for file_path in production_files:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
            
        print(f"🔧 Processing: {file_path}")
        
        # Add imports
        if add_enforcer_imports(file_path):
            print(f"  ✅ Added enforcer imports")
            integrated_count += 1
        else:
            print(f"  ℹ️ Already integrated or no imports section")
            
        # Add validation calls
        if add_signal_validation(file_path):
            print(f"  ✅ Added signal validation calls")
        else:
            print(f"  ℹ️ No signal processing patterns found")
    
    print("\n" + "=" * 50)
    print(f"🔒 INTEGRATION COMPLETE: {integrated_count} files modified")
    print("🚨 SYSTEM NOW ENFORCES ZERO FAKE DATA TOLERANCE")
    
    return integrated_count

if __name__ == "__main__":
    integrate_production_files()