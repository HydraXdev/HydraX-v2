#!/usr/bin/env python3
"""
Audit script to find all fire.txt references in the codebase
This helps identify all places that need migration to ZMQ
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

def find_fire_txt_references(root_dir: str = "/root/HydraX-v2") -> Dict[str, List[Tuple[int, str]]]:
    """
    Find all references to fire.txt in the codebase
    
    Returns:
        Dict mapping file paths to list of (line_number, line_content) tuples
    """
    fire_references = {}
    
    # Patterns to search for
    patterns = [
        r'fire\.txt',
        r'fire_txt',
        r'FIRE\.TXT',
        r'fire_path',
        r'fire_file',
        r'/fire\.',
        r'\\fire\.',
        r'"fire\.',
        r"'fire\."
    ]
    
    # Compile regex patterns
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    # Walk through directory
    for root, dirs, files in os.walk(root_dir):
        # Skip archive and .git directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'archive', '__pycache__', 'venv']]
        
        for file in files:
            if file.endswith(('.py', '.md', '.txt', '.sh')):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    matches = []
                    for line_num, line in enumerate(lines, 1):
                        for pattern in compiled_patterns:
                            if pattern.search(line):
                                matches.append((line_num, line.strip()))
                                break
                    
                    if matches:
                        fire_references[file_path] = matches
                        
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return fire_references

def categorize_references(references: Dict[str, List[Tuple[int, str]]]) -> Dict[str, Dict]:
    """
    Categorize references by type of usage
    """
    categories = {
        'write_operations': [],
        'read_operations': [],
        'path_references': [],
        'documentation': [],
        'comments': [],
        'other': []
    }
    
    for file_path, matches in references.items():
        for line_num, line in matches:
            # Categorize based on content
            if 'open(' in line and 'w' in line:
                categories['write_operations'].append({
                    'file': file_path,
                    'line': line_num,
                    'content': line
                })
            elif 'open(' in line and 'r' in line:
                categories['read_operations'].append({
                    'file': file_path,
                    'line': line_num,
                    'content': line
                })
            elif file_path.endswith('.md') or file_path.endswith('.txt'):
                categories['documentation'].append({
                    'file': file_path,
                    'line': line_num,
                    'content': line
                })
            elif line.strip().startswith('#') or line.strip().startswith('//'):
                categories['comments'].append({
                    'file': file_path,
                    'line': line_num,
                    'content': line
                })
            elif 'path' in line.lower() or '=' in line:
                categories['path_references'].append({
                    'file': file_path,
                    'line': line_num,
                    'content': line
                })
            else:
                categories['other'].append({
                    'file': file_path,
                    'line': line_num,
                    'content': line
                })
    
    return categories

def generate_migration_report(categories: Dict[str, Dict]) -> str:
    """
    Generate a migration report with recommendations
    """
    report = []
    report.append("# Fire.txt Migration Report\n")
    report.append(f"Generated: {datetime.now().isoformat()}\n")
    
    # Summary
    total_refs = sum(len(refs) for refs in categories.values())
    report.append(f"## Summary\n")
    report.append(f"Total references found: {total_refs}\n")
    report.append(f"- Write operations: {len(categories['write_operations'])}\n")
    report.append(f"- Read operations: {len(categories['read_operations'])}\n")
    report.append(f"- Path references: {len(categories['path_references'])}\n")
    report.append(f"- Documentation: {len(categories['documentation'])}\n")
    report.append(f"- Comments: {len(categories['comments'])}\n")
    report.append(f"- Other: {len(categories['other'])}\n")
    
    # Critical migrations needed
    report.append(f"\n## Critical Migrations Required\n")
    report.append("These write operations need immediate migration to ZMQ:\n")
    
    for ref in categories['write_operations']:
        report.append(f"\n### {ref['file']}:{ref['line']}")
        report.append(f"```python")
        report.append(ref['content'])
        report.append("```")
        report.append("**Migration**: Replace with `execute_bitten_trade()` from zmq_bitten_controller\n")
    
    # Read operations
    report.append(f"\n## Read Operations to Remove\n")
    report.append("These read operations should be replaced with telemetry monitoring:\n")
    
    for ref in categories['read_operations'][:5]:  # Show first 5
        report.append(f"- {ref['file']}:{ref['line']}")
    
    if len(categories['read_operations']) > 5:
        report.append(f"- ... and {len(categories['read_operations']) - 5} more\n")
    
    # Migration strategy
    report.append("\n## Migration Strategy\n")
    report.append("1. **Phase 1**: Add ZMQ alongside fire.txt (dual-write)\n")
    report.append("2. **Phase 2**: Verify ZMQ working, monitor both channels\n")
    report.append("3. **Phase 3**: Stop reading fire.txt, only write for compatibility\n")
    report.append("4. **Phase 4**: Remove all fire.txt writes\n")
    
    # Feature flag recommendation
    report.append("\n## Feature Flag Implementation\n")
    report.append("```python\n")
    report.append("USE_ZMQ = os.getenv('USE_ZMQ', 'false').lower() == 'true'\n")
    report.append("\n")
    report.append("if USE_ZMQ:\n")
    report.append("    from zmq_bitten_controller import execute_bitten_trade\n")
    report.append("    result = execute_bitten_trade(signal_data)\n")
    report.append("else:\n")
    report.append("    # Legacy fire.txt method\n")
    report.append("    with open(fire_path, 'w') as f:\n")
    report.append("        json.dump(signal_data, f)\n")
    report.append("```\n")
    
    return '\n'.join(report)

def main():
    """
    Run the audit and generate report
    """
    print("🔍 Auditing fire.txt references...")
    
    # Find all references
    references = find_fire_txt_references()
    
    if not references:
        print("✅ No fire.txt references found!")
        return
    
    # Categorize
    categories = categorize_references(references)
    
    # Generate report
    report = generate_migration_report(categories)
    
    # Save report
    report_path = "/root/HydraX-v2/FIRE_TXT_MIGRATION_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Audit complete!")
    print(f"Total files with references: {len(references)}")
    print(f"Report saved to: {report_path}")
    
    # Show critical files
    print("\n🚨 Critical files needing migration:")
    for ref in categories['write_operations'][:5]:
        print(f"  - {ref['file']}:{ref['line']}")
    
    if len(categories['write_operations']) > 5:
        print(f"  - ... and {len(categories['write_operations']) - 5} more")

if __name__ == "__main__":
    main()