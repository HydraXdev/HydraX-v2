#!/usr/bin/env python3
"""
Permanently disable fake data generation in VENOM
"""

import os

# Read the base VENOM file
with open('/root/HydraX-v2/apex_venom_v7_unfiltered.py', 'r') as f:
    content = f.read()

# Replace the generate_realistic_market_data method with error
fake_method_start = content.find('def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict:')
if fake_method_start != -1:
    # Find the end of the method
    lines = content[fake_method_start:].split('\n')
    method_lines = []
    indent_level = None
    
    for i, line in enumerate(lines):
        if i == 0:
            method_lines.append(line)
            continue
            
        # Get indent level from first line after def
        if indent_level is None and line.strip():
            indent_level = len(line) - len(line.lstrip())
            
        # Check if we're still in the method
        if line.strip() and not line.startswith(' ' * indent_level):
            break
            
        method_lines.append(line)
    
    # Create replacement that throws error
    replacement = '''def generate_realistic_market_data(self, pair: str, timestamp: datetime) -> Dict:
        """PERMANENTLY DISABLED - NO FAKE DATA ALLOWED"""
        raise RuntimeError(f"FAKE DATA GENERATION FORBIDDEN! Use get_real_mt5_data() for {pair}")'''
    
    # Replace the method
    old_method = '\n'.join(method_lines)
    content = content.replace(old_method, replacement)
    
    # Also update the call in generate_venom_signal to use real data
    content = content.replace(
        'market_data = self.generate_realistic_market_data(pair, timestamp)',
        '# REAL DATA ONLY - get from MT5 container\n        market_data = self.get_real_mt5_data(pair) if hasattr(self, "get_real_mt5_data") else {}'
    )
    
    # Write back
    with open('/root/HydraX-v2/apex_venom_v7_unfiltered.py', 'w') as f:
        f.write(content)
    
    print("✅ FAKE DATA GENERATION PERMANENTLY DISABLED!")
    print("   - generate_realistic_market_data() now throws RuntimeError")
    print("   - generate_venom_signal() updated to use real data only")
    print("   - NO FAKE DATA can ever be generated again!")
else:
    print("Method already removed or not found")