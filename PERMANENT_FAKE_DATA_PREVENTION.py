#!/usr/bin/env python3
"""
PERMANENT FAKE DATA PREVENTION SYSTEM
Prevents fake data from being reintroduced into the codebase
"""

import os
import re
import sys
from datetime import datetime

# Patterns that indicate fake data generation
FAKE_DATA_PATTERNS = [
    r'random\.(random|uniform|randint|choice|sample|shuffle)',
    r'generate_realistic_.*data',
    r'simulate.*trade.*result',
    r'fake.*data',
    r'mock.*balance',
    r'synthetic.*signal',
]

# Critical production files that must NEVER contain fake data
CRITICAL_FILES = [
    'apex_venom_v7_unfiltered.py',
    'webapp_server_optimized.py',
    'src/bitten_core/bitten_core.py',
    'src/bitten_core/fire_router.py',
    'bitten_production_bot.py',
    'working_signal_generator.py',
]

def scan_file(filepath):
    """Scan a file for fake data patterns"""
    violations = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        for i, line in enumerate(lines):
            for pattern in FAKE_DATA_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip comments and imports
                    if line.strip().startswith('#') or 'import random' in line:
                        continue
                    violations.append({
                        'line': i + 1,
                        'content': line.strip(),
                        'pattern': pattern
                    })
                    
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
        
    return violations

def scan_directory(directory):
    """Scan entire directory for fake data"""
    all_violations = {}
    
    for root, dirs, files in os.walk(directory):
        # Skip git and test directories
        if '.git' in root or 'test' in root or 'archive' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                violations = scan_file(filepath)
                
                if violations:
                    relative_path = os.path.relpath(filepath, directory)
                    all_violations[relative_path] = violations
                    
    return all_violations

def generate_report(violations):
    """Generate detailed violation report"""
    report = []
    report.append("# FAKE DATA VIOLATION REPORT")
    report.append(f"Generated: {datetime.now()}")
    report.append(f"Total files with violations: {len(violations)}")
    report.append("")
    
    critical_violations = 0
    
    for filepath, file_violations in violations.items():
        is_critical = any(critical in filepath for critical in CRITICAL_FILES)
        
        if is_critical:
            critical_violations += 1
            report.append(f"## 🚨 CRITICAL: {filepath}")
        else:
            report.append(f"## {filepath}")
            
        report.append(f"Violations: {len(file_violations)}")
        
        for v in file_violations:
            report.append(f"- Line {v['line']}: `{v['content'][:80]}...`")
            
        report.append("")
        
    report.append(f"\n🚨 CRITICAL VIOLATIONS: {critical_violations}")
    
    return "\n".join(report)

def create_git_hook():
    """Create pre-commit hook to prevent fake data"""
    hook_content = """#!/bin/bash
# Pre-commit hook to prevent fake data

echo "🔍 Scanning for fake data violations..."

# Run the prevention script
python3 /root/HydraX-v2/PERMANENT_FAKE_DATA_PREVENTION.py

# Check exit code
if [ $? -ne 0 ]; then
    echo "❌ Commit blocked: Fake data detected!"
    echo "Please remove all fake data before committing."
    exit 1
fi

echo "✅ No fake data detected - commit allowed"
"""
    
    git_hooks_dir = "/root/HydraX-v2/.git/hooks"
    if os.path.exists(git_hooks_dir):
        hook_path = os.path.join(git_hooks_dir, "pre-commit")
        with open(hook_path, 'w') as f:
            f.write(hook_content)
        os.chmod(hook_path, 0o755)
        print("✅ Git pre-commit hook installed")

def main():
    print("🔍 PERMANENT FAKE DATA PREVENTION SYSTEM")
    print("=" * 50)
    
    # Scan the codebase
    violations = scan_directory("/root/HydraX-v2")
    
    if violations:
        # Generate report
        report = generate_report(violations)
        
        # Save report
        with open("/root/HydraX-v2/FAKE_DATA_VIOLATIONS.md", 'w') as f:
            f.write(report)
            
        print(f"❌ Found fake data in {len(violations)} files!")
        print("Report saved to: FAKE_DATA_VIOLATIONS.md")
        
        # Check for critical violations
        critical_count = sum(1 for f in violations if any(c in f for c in CRITICAL_FILES))
        if critical_count > 0:
            print(f"\n🚨 CRITICAL: {critical_count} production files contain fake data!")
            sys.exit(1)
    else:
        print("✅ No fake data violations found!")
        
    # Install git hook
    create_git_hook()
    
    print("\n📋 Prevention measures installed:")
    print("- Git pre-commit hook active")
    print("- Run this script anytime to scan")
    print("- Critical files are monitored")

if __name__ == "__main__":
    main()