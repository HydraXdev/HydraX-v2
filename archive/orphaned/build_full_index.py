#!/usr/bin/env python3
"""
Build comprehensive SHEPHERD index for all critical BITTEN files
"""
import os
import sys
import json
import ast
from datetime import datetime

sys.path.append('/root/HydraX-v2')

# Load existing quick index
quick_index_path = '/root/HydraX-v2/bitten/data/shepherd/quick_index.json'
with open(quick_index_path, 'r') as f:
    quick_data = json.load(f)

# Extract components list
if isinstance(quick_data, dict) and 'components' in quick_data:
    components = quick_data['components']
else:
    components = []

print(f"Starting with {len(components)} components from quick index")

# Key files to add to index
critical_files = [
    'BULLETPROOF_INFRASTRUCTURE.py',
    'AUTHORIZED_SIGNAL_ENGINE.py',
    'aws_mt5_bridge.py',
    'core/tcs_engine.py',
    'webapp_server.py',
    'simple_mt5_allocator.py',
    'mt5_instance_tracker.py',
    'broker_education_menu.py'
]

def extract_basic_info(filepath):
    """Extract basic function and class info from a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        file_components = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                component = {
                    "id": node.name,
                    "type": "function",
                    "file": filepath,
                    "tier": "tier_general",
                    "trigger": ["direct_call"],
                    "connects_to": [],
                    "flags": [],
                    "purpose": ast.get_docstring(node) or "No description",
                    "last_modified": datetime.now().isoformat()
                }
                
                # Add flags based on function name
                if 'trade' in node.name.lower() or 'signal' in node.name.lower():
                    component["flags"].append("trading")
                if 'critical' in node.name.lower() or 'emergency' in node.name.lower():
                    component["flags"].append("critical")
                    
                file_components.append(component)
                
            elif isinstance(node, ast.ClassDef):
                component = {
                    "id": node.name,
                    "type": "class",
                    "file": filepath,
                    "tier": "tier_general",
                    "trigger": ["direct_call"],
                    "connects_to": [],
                    "flags": [],
                    "purpose": ast.get_docstring(node) or "No description",
                    "last_modified": datetime.now().isoformat()
                }
                
                # Add flags based on class name
                if 'Bridge' in node.name or 'Infrastructure' in node.name:
                    component["flags"].append("infrastructure")
                if 'Signal' in node.name or 'Engine' in node.name:
                    component["flags"].append("critical")
                    
                file_components.append(component)
                
        return file_components
        
    except Exception as e:
        print(f"  Error processing {filepath}: {e}")
        return []

# Process critical files
for filepath in critical_files:
    if os.path.exists(filepath):
        print(f"Indexing: {filepath}")
        new_components = extract_basic_info(filepath)
        components.extend(new_components)
        print(f"  Added {len(new_components)} components")

# Save comprehensive index
output_path = '/root/HydraX-v2/bitten/data/shepherd/shepherd_index.json'
with open(output_path, 'w') as f:
    json.dump(components, f, indent=2)

print(f"\n✅ Comprehensive index built!")
print(f"Total components: {len(components)}")
print(f"Saved to: {output_path}")

# Show summary
functions = [c for c in components if c['type'] == 'function']
classes = [c for c in components if c['type'] == 'class']
critical = [c for c in components if 'critical' in c.get('flags', [])]

print(f"\n📊 Index Summary:")
print(f"  Functions: {len(functions)}")
print(f"  Classes: {len(classes)}")
print(f"  Critical components: {len(critical)}")