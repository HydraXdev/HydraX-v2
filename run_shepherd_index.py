#!/usr/bin/env python3
"""
Quick SHEPHERD index builder - focuses on core BITTEN files only
"""
import sys
import os
sys.path.append('/root/HydraX-v2')

from bitten.core.shepherd.indexer import ShepherdIndexer

def run_quick_index():
    """Run a quick index of core BITTEN files"""
    indexer = ShepherdIndexer('/root/HydraX-v2')
    
    # Focus on core BITTEN directories only
    core_dirs = [
        'bitten/core',
        'core',
        'webapp',
        'telegram',
        'agents'
    ]
    
    print("🧠 SHEPHERD Quick Index Starting...")
    
    components = []
    for dir_path in core_dirs:
        full_path = os.path.join('/root/HydraX-v2', dir_path)
        if os.path.exists(full_path):
            print(f"📁 Scanning {dir_path}...")
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        try:
                            result = indexer.scan_file(filepath)
                            components.extend(result)
                            print(f"  ✓ {file}: {len(result)} components")
                        except Exception as e:
                            print(f"  ✗ {file}: {str(e)}")
    
    # Save index
    output_path = '/root/HydraX-v2/bitten/data/shepherd/shepherd_index.json'
    indexer._save_index(components, output_path)
    
    print(f"\n✅ Index complete: {len(components)} components indexed")
    print(f"📄 Saved to: {output_path}")
    
    # Show summary
    function_count = len([c for c in components if c['type'] == 'function'])
    class_count = len([c for c in components if c['type'] == 'class'])
    print(f"\n📊 Summary:")
    print(f"   Functions: {function_count}")
    print(f"   Classes: {class_count}")
    print(f"   Total: {len(components)}")

if __name__ == "__main__":
    run_quick_index()