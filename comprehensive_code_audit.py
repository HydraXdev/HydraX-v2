#!/usr/bin/env python3
"""
Comprehensive BITTEN System Code Audit
Identifies orphaned files, duplicates, broken imports, and bloat
"""

import os
import ast
import sys
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
import subprocess

class BittenCodeAuditor:
    def __init__(self, root_dir="/root/HydraX-v2"):
        self.root_dir = Path(root_dir)
        self.python_files = []
        self.imports_map = defaultdict(set)
        self.imported_by = defaultdict(set)
        self.entry_points = []
        self.orphaned_files = []
        self.duplicates = []
        self.broken_imports = []
        self.production_files = set()
        self.running_processes = []
        
    def scan_files(self):
        """Scan all Python files in the system"""
        print("🔍 Scanning Python files...")
        
        # Skip archive directories
        skip_patterns = ['/archive/', '/backups/', '/__pycache__/', '/.git/']
        
        for py_file in self.root_dir.rglob("*.py"):
            # Skip archived files
            if any(pattern in str(py_file) for pattern in skip_patterns):
                continue
                
            self.python_files.append(py_file)
            
        print(f"✅ Found {len(self.python_files)} Python files")
        
    def identify_running_processes(self):
        """Identify currently running Python processes"""
        print("🔍 Checking running processes...")
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'python' in line and '/root/HydraX-v2' in line:
                    # Extract the script name
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.endswith('.py') and '/root/HydraX-v2' in part:
                            script_name = Path(part).name
                            self.running_processes.append(script_name)
                            self.production_files.add(script_name)
                            
        except Exception as e:
            print(f"⚠️ Could not check running processes: {e}")
            
        print(f"✅ Found {len(self.running_processes)} running Python scripts")
        for script in self.running_processes:
            print(f"   🔥 {script}")
    
    def parse_imports(self):
        """Parse imports from all Python files"""
        print("🔍 Parsing imports and dependencies...")
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse AST
                try:
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self.imports_map[py_file].add(alias.name)
                                self.imported_by[alias.name].add(py_file)
                                
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                self.imports_map[py_file].add(node.module)
                                self.imported_by[node.module].add(py_file)
                                
                except SyntaxError:
                    print(f"⚠️ Syntax error in {py_file}")
                    
            except Exception as e:
                print(f"⚠️ Could not read {py_file}: {e}")
                
        print(f"✅ Parsed imports from {len(self.imports_map)} files")
    
    def identify_entry_points(self):
        """Identify files with main entry points"""
        print("🔍 Identifying entry points...")
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for main entry point
                if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
                    self.entry_points.append(py_file)
                    
            except Exception as e:
                continue
                
        print(f"✅ Found {len(self.entry_points)} entry point files")
    
    def find_duplicates(self):
        """Find duplicate implementations with different names"""
        print("🔍 Searching for duplicate implementations...")
        
        # Group by similar content patterns
        content_hashes = defaultdict(list)
        name_patterns = defaultdict(list)
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Remove comments and whitespace for comparison
                cleaned = re.sub(r'#.*', '', content)
                cleaned = re.sub(r'\s+', ' ', cleaned)
                
                # Simple hash of cleaned content
                content_hash = hash(cleaned[:1000])  # First 1000 chars
                content_hashes[content_hash].append(py_file)
                
                # Group by similar names
                base_name = py_file.stem.lower()
                # Remove version numbers and suffixes
                base_name = re.sub(r'_v\d+|_\d+|_backup|_old|_copy|_new|_fixed|_enhanced|_updated', '', base_name)
                name_patterns[base_name].append(py_file)
                
            except Exception as e:
                continue
        
        # Find actual duplicates
        for files in content_hashes.values():
            if len(files) > 1:
                self.duplicates.append(files)
                
        for files in name_patterns.values():
            if len(files) > 1:
                # Check if they're not already in content duplicates
                already_found = any(set(files).intersection(set(dup)) for dup in self.duplicates)
                if not already_found:
                    self.duplicates.append(files)
        
        print(f"✅ Found {len(self.duplicates)} groups of potential duplicates")
    
    def find_orphaned_files(self):
        """Find files that are not imported or used anywhere"""
        print("🔍 Finding orphaned files...")
        
        # Files that are imported by others
        imported_files = set()
        
        for py_file in self.python_files:
            file_module = self.get_module_name(py_file)
            
            # Check if this file is imported
            for imported_module in self.imported_by.keys():
                if file_module in imported_module or imported_module in file_module:
                    imported_files.add(py_file)
                    break
        
        # Files that are potential orphans
        for py_file in self.python_files:
            # Skip if it's an entry point
            if py_file in self.entry_points:
                continue
                
            # Skip if it's imported
            if py_file in imported_files:
                continue
                
            # Skip if it's currently running
            if py_file.name in self.production_files:
                continue
                
            # Check if it's a test file (tests are okay to be "orphaned")
            if 'test_' in py_file.name or '/tests/' in str(py_file):
                continue
                
            # Check if it's a script or utility
            if any(pattern in py_file.name for pattern in ['start_', 'deploy_', 'setup_', 'fix_', 'debug_']):
                continue
                
            self.orphaned_files.append(py_file)
            
        print(f"✅ Found {len(self.orphaned_files)} potentially orphaned files")
    
    def find_broken_imports(self):
        """Find broken import statements"""
        print("🔍 Checking for broken imports...")
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Try to compile to find import errors
                try:
                    compile(content, str(py_file), 'exec')
                except SyntaxError as e:
                    if 'import' in str(e).lower():
                        self.broken_imports.append((py_file, str(e)))
                except Exception:
                    pass
                    
            except Exception:
                continue
                
        print(f"✅ Found {len(self.broken_imports)} files with potential import issues")
    
    def get_module_name(self, py_file):
        """Convert file path to module name"""
        relative_path = py_file.relative_to(self.root_dir)
        module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        return '.'.join(module_parts)
    
    def analyze_production_architecture(self):
        """Analyze the actual production architecture"""
        print("🔍 Analyzing production architecture...")
        
        # Core production files
        core_files = [
            'bitten_production_bot.py',
            'webapp_server_optimized.py', 
            'commander_throne.py',
            'bridge_fortress_daemon.py',
            'apex_venom_v7_unfiltered.py'
        ]
        
        production_analysis = {
            'core_files': [],
            'supporting_files': [],
            'utility_scripts': [],
            'test_files': [],
            'orphaned_files': []
        }
        
        for py_file in self.python_files:
            filename = py_file.name
            
            if filename in core_files:
                production_analysis['core_files'].append(filename)
            elif filename.startswith('test_'):
                production_analysis['test_files'].append(filename)
            elif any(prefix in filename for prefix in ['start_', 'deploy_', 'setup_', 'fix_', 'debug_']):
                production_analysis['utility_scripts'].append(filename)
            elif py_file in self.orphaned_files:
                production_analysis['orphaned_files'].append(filename)
            else:
                production_analysis['supporting_files'].append(filename)
        
        return production_analysis
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*80)
        print("📊 BITTEN SYSTEM CODE AUDIT REPORT")
        print("="*80)
        
        # Production architecture
        arch = self.analyze_production_architecture()
        
        print(f"\n🏗️ PRODUCTION ARCHITECTURE:")
        print(f"   Core files: {len(arch['core_files'])}")
        print(f"   Supporting files: {len(arch['supporting_files'])}")
        print(f"   Utility scripts: {len(arch['utility_scripts'])}")
        print(f"   Test files: {len(arch['test_files'])}")
        print(f"   Orphaned files: {len(arch['orphaned_files'])}")
        
        print(f"\n🔥 CURRENTLY RUNNING ({len(self.running_processes)}):")
        for script in self.running_processes:
            print(f"   ✅ {script}")
        
        print(f"\n🚪 ENTRY POINTS ({len(self.entry_points)}):")
        for ep in self.entry_points[:20]:  # Show first 20
            print(f"   📝 {ep.name}")
        if len(self.entry_points) > 20:
            print(f"   ... and {len(self.entry_points) - 20} more")
        
        print(f"\n🔄 POTENTIAL DUPLICATES ({len(self.duplicates)}):")
        for i, dup_group in enumerate(self.duplicates[:10]):  # Show first 10 groups
            print(f"   Group {i+1}:")
            for file in dup_group:
                print(f"     - {file.name}")
        if len(self.duplicates) > 10:
            print(f"   ... and {len(self.duplicates) - 10} more groups")
            
        print(f"\n🏝️ ORPHANED FILES ({len(self.orphaned_files)}):")
        for orphan in self.orphaned_files[:20]:  # Show first 20
            print(f"   ❓ {orphan.name}")
        if len(self.orphaned_files) > 20:
            print(f"   ... and {len(self.orphaned_files) - 20} more")
            
        print(f"\n❌ POTENTIAL BROKEN IMPORTS ({len(self.broken_imports)}):")
        for file, error in self.broken_imports[:10]:  # Show first 10
            print(f"   🚫 {file.name}: {error[:50]}...")
        if len(self.broken_imports) > 10:
            print(f"   ... and {len(self.broken_imports) - 10} more")
        
        print(f"\n📈 STATISTICS:")
        print(f"   Total Python files: {len(self.python_files)}")
        print(f"   Entry points: {len(self.entry_points)}")
        print(f"   Production files: {len(self.production_files)}")
        print(f"   Duplicate groups: {len(self.duplicates)}")
        print(f"   Orphaned files: {len(self.orphaned_files)}")
        print(f"   Import issues: {len(self.broken_imports)}")
        
        # Calculate bloat percentage
        active_files = len(arch['core_files']) + len(arch['supporting_files'])
        bloat_files = len(arch['orphaned_files']) + len(self.duplicates) * 2  # Approximate
        bloat_percentage = (bloat_files / len(self.python_files)) * 100
        
        print(f"\n🎯 BLOAT ANALYSIS:")
        print(f"   Active files: {active_files}")
        print(f"   Potential bloat: {bloat_files}")
        print(f"   Bloat percentage: {bloat_percentage:.1f}%")
        
        if bloat_percentage > 30:
            print("   ⚠️ HIGH BLOAT DETECTED - Cleanup recommended")
        elif bloat_percentage > 15:
            print("   ⚠️ MODERATE BLOAT - Some cleanup beneficial")
        else:
            print("   ✅ ACCEPTABLE BLOAT LEVEL")
        
        return {
            'architecture': arch,
            'statistics': {
                'total_files': len(self.python_files),
                'entry_points': len(self.entry_points),
                'duplicates': len(self.duplicates),
                'orphaned': len(self.orphaned_files),
                'broken_imports': len(self.broken_imports),
                'bloat_percentage': bloat_percentage
            }
        }
    
    def generate_cleanup_recommendations(self):
        """Generate specific cleanup recommendations"""
        print(f"\n🧹 CLEANUP RECOMMENDATIONS:")
        print("="*50)
        
        if self.orphaned_files:
            print(f"\n1. ORPHANED FILES ({len(self.orphaned_files)} files):")
            print("   Consider moving to /archive/ or deleting if unused:")
            for orphan in self.orphaned_files[:10]:
                print(f"   rm {orphan}")
            if len(self.orphaned_files) > 10:
                print(f"   ... and {len(self.orphaned_files) - 10} more")
        
        if self.duplicates:
            print(f"\n2. DUPLICATE FILES ({len(self.duplicates)} groups):")
            print("   Review and keep only the latest/best version:")
            for i, dup_group in enumerate(self.duplicates[:5]):
                print(f"   Group {i+1}: Choose one from:")
                for file in dup_group:
                    print(f"     - {file}")
        
        if self.broken_imports:
            print(f"\n3. BROKEN IMPORTS ({len(self.broken_imports)} files):")
            print("   Fix import statements in:")
            for file, error in self.broken_imports[:5]:
                print(f"   - {file.name}")
        
        print(f"\n4. ARCHIVE SUGGESTIONS:")
        print("   Move old/backup files to /archive/:")
        for py_file in self.python_files:
            if any(pattern in py_file.name for pattern in ['_backup', '_old', '_copy', '_v1', '_v2', '_v3', '_v4', '_v5']):
                print(f"   mv {py_file} /root/HydraX-v2/archive/")
    
    def run_full_audit(self):
        """Run complete audit"""
        print("🔍 STARTING COMPREHENSIVE BITTEN CODE AUDIT")
        print("="*80)
        
        self.scan_files()
        self.identify_running_processes()
        self.parse_imports()
        self.identify_entry_points()
        self.find_duplicates()
        self.find_orphaned_files()
        self.find_broken_imports()
        
        report = self.generate_report()
        self.generate_cleanup_recommendations()
        
        return report

def main():
    auditor = BittenCodeAuditor()
    report = auditor.run_full_audit()
    
    # Save report to file
    with open('/root/HydraX-v2/code_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved to: /root/HydraX-v2/code_audit_report.json")
    print(f"\n🎯 AUDIT COMPLETE!")

if __name__ == "__main__":
    main()