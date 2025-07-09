#!/usr/bin/env python3
"""
Validate that all test files are properly structured and can be imported
"""

import os
import sys
import ast
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def validate_test_file(file_path):
    """Validate a single test file"""
    print(f"\nValidating: {file_path.name}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Parse the AST
        tree = ast.parse(content)
        
        # Count test classes and functions
        test_classes = 0
        test_functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith('Test'):
                    test_classes += 1
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_functions += 1
                    
        print(f"  ✓ Valid Python syntax")
        print(f"  ✓ Test classes: {test_classes}")
        print(f"  ✓ Test functions: {test_functions}")
        
        # Check for required imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                    
        if 'pytest' in imports:
            print(f"  ✓ Uses pytest framework")
        else:
            print(f"  ⚠ No pytest import found")
            
        return True
        
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Main validation function"""
    test_dir = Path(__file__).parent
    
    print("TCS++ and Stealth Protocol Test Validation")
    print("=" * 60)
    
    test_files = [
        'test_tcs_plus_engine.py',
        'test_stealth_protocol_comprehensive.py',
        'integration/test_tcs_stealth_integration.py',
        'test_performance_benchmarks.py'
    ]
    
    all_valid = True
    
    for test_file in test_files:
        file_path = test_dir / test_file
        if file_path.exists():
            if not validate_test_file(file_path):
                all_valid = False
        else:
            print(f"\n✗ Missing file: {test_file}")
            all_valid = False
            
    print("\n" + "=" * 60)
    if all_valid:
        print("✓ All test files are valid!")
        
        # Try importing the main modules
        print("\nValidating module imports...")
        try:
            from core.tcs_engine import score_tcs, classify_trade
            print("  ✓ TCS engine imports successfully")
        except ImportError as e:
            print(f"  ✗ Failed to import TCS engine: {e}")
            all_valid = False
            
        try:
            from src.bitten_core.stealth_protocol import StealthProtocol, StealthConfig, StealthLevel
            print("  ✓ Stealth protocol imports successfully")
        except ImportError as e:
            print(f"  ✗ Failed to import stealth protocol: {e}")
            all_valid = False
            
    else:
        print("✗ Some test files have issues!")
        
    return 0 if all_valid else 1


if __name__ == '__main__':
    sys.exit(main())