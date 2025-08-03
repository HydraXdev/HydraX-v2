#!/usr/bin/env python3
"""
Legacy Purge Analyzer - Identifies all legacy components to remove
Dry run mode to show what will be deleted
"""

import os
import glob
import re
from pathlib import Path
from typing import List, Dict, Set

class LegacyPurgeAnalyzer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.legacy_components = {
            'file_based_execution': [],
            'wine_containers': [],
            'http_endpoints': [],
            'obsolete_eas': [],
            'old_configs': [],
            'temp_files': [],
            'legacy_logs': []
        }
        
    def analyze(self):
        """Run complete legacy analysis"""
        print("🔍 Legacy System Analysis")
        print("="*60)
        
        # 1. Find file-based execution code
        self._find_fire_txt_code()
        
        # 2. Find Wine containers
        self._find_wine_containers()
        
        # 3. Find HTTP endpoints
        self._find_http_endpoints()
        
        # 4. Find obsolete EAs
        self._find_obsolete_eas()
        
        # 5. Find old configs
        self._find_old_configs()
        
        # 6. Find temp files
        self._find_temp_files()
        
        # Report findings
        self._report_findings()
        
    def _find_fire_txt_code(self):
        """Find all file-based execution references"""
        print("\n📁 Searching for file-based execution code...")
        
        # Search patterns
        patterns = [
            ('fire.txt', r'fire\.txt'),
            ('fire_txt', r'fire_txt'),
            ('trade_result.txt', r'trade_result\.txt'),
            ('write_fire', r'write_fire'),
            ('fire_path', r'fire_path'),
            ('uuid.txt', r'uuid\.txt')
        ]
        
        # Search Python files
        for root, dirs, files in os.walk('.'):
            # Skip archive and critical dirs
            if any(skip in root for skip in ['archive', '.git', '__pycache__', 'venv', 'lockbox']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for name, pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                # Check if it's actual code, not just documentation
                                lines = content.split('\n')
                                for i, line in enumerate(lines):
                                    if re.search(pattern, line) and not line.strip().startswith('#'):
                                        self.legacy_components['file_based_execution'].append({
                                            'file': filepath,
                                            'type': name,
                                            'line': i + 1,
                                            'content': line.strip()
                                        })
                                        break
                    except:
                        pass
                        
    def _find_wine_containers(self):
        """Find Wine-related files and directories"""
        print("\n🍷 Searching for Wine containers...")
        
        wine_patterns = [
            'wine_*',
            '*wine*',
            '*.wine',
            'winetricks*',
            'mt5_wine*'
        ]
        
        for pattern in wine_patterns:
            matches = glob.glob(pattern, recursive=False)
            for match in matches:
                if os.path.exists(match):
                    self.legacy_components['wine_containers'].append(match)
                    
        # Check for Wine processes
        wine_procs = os.popen("ps aux | grep -i wine | grep -v grep").read()
        if wine_procs:
            self.legacy_components['wine_containers'].append("RUNNING_PROCESSES:\n" + wine_procs)
            
    def _find_http_endpoints(self):
        """Find HTTP/POST trade endpoints"""
        print("\n🌐 Searching for HTTP endpoints...")
        
        http_patterns = [
            (r'@app\.route.*\/fire', 'Flask /fire endpoint'),
            (r'@app\.route.*\/execute_trade', 'Flask /execute_trade endpoint'),
            (r'requests\.post.*fire', 'HTTP POST to fire'),
            (r'WebRequest\(', 'EA WebRequest call'),
            (r'http.*\/market-data', 'Market data HTTP endpoint')
        ]
        
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ['archive', '.git']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            
                        for pattern, desc in http_patterns:
                            if re.search(pattern, content):
                                self.legacy_components['http_endpoints'].append({
                                    'file': filepath,
                                    'type': desc
                                })
                                break
                    except:
                        pass
                        
    def _find_obsolete_eas(self):
        """Find obsolete EA files"""
        print("\n🤖 Searching for obsolete EAs...")
        
        # EA file patterns
        ea_patterns = [
            'mq5/BITTENBridge_TradeExecutor_PRODUCTION.mq5',
            'mq5/BITTENBridge_TradeExecutor_DEBUG.mq5',
            'mq5/BITTENBridge_TradeExecutor_FIXED*.mq5',
            'mq5/BITTENBridge_TradeExecutor_LEAN.mq5',
            'mq5/*fire*.mq5',
            'mq5/*HTTP*.mq5'
        ]
        
        for pattern in ea_patterns:
            matches = glob.glob(pattern)
            for match in matches:
                # Skip the v7 ZMQ EA
                if 'ZMQ_v7' not in match:
                    self.legacy_components['obsolete_eas'].append(match)
                    
        # Also check for .ex5 binaries
        ex5_files = glob.glob('mq5/*.ex5')
        for ex5 in ex5_files:
            if 'ZMQ' not in ex5:
                self.legacy_components['obsolete_eas'].append(ex5)
                
    def _find_old_configs(self):
        """Find old configuration files"""
        print("\n⚙️ Searching for old configs...")
        
        config_patterns = [
            '.env.backup*',
            '.env.old*',
            '*fire_mode_config*',
            'USE_ZMQ=false',
            'ZMQ_DUAL_WRITE=true'
        ]
        
        # Check .env files
        env_files = glob.glob('.env*')
        for env_file in env_files:
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                if 'USE_ZMQ=false' in content:
                    self.legacy_components['old_configs'].append({
                        'file': env_file,
                        'issue': 'Contains USE_ZMQ=false'
                    })
                if 'ZMQ_DUAL_WRITE=true' in content:
                    self.legacy_components['old_configs'].append({
                        'file': env_file,
                        'issue': 'Contains ZMQ_DUAL_WRITE=true'
                    })
            except:
                pass
                
    def _find_temp_files(self):
        """Find temporary files and logs"""
        print("\n📄 Searching for temp files...")
        
        temp_patterns = [
            'fire.txt',
            'trade_result.txt',
            'uuid.txt',
            'temp_fire_*',
            'logs/fire*.log',
            'logs/*bridge*.log',
            '*.bak',
            '*.old'
        ]
        
        for pattern in temp_patterns:
            matches = glob.glob(pattern, recursive=True)
            self.legacy_components['temp_files'].extend(matches)
            
        # Check /tmp directory
        tmp_files = glob.glob('/tmp/*bitten*') + glob.glob('/tmp/*fire*') + glob.glob('/tmp/*mt5*')
        self.legacy_components['temp_files'].extend(tmp_files)
        
    def _report_findings(self):
        """Report all findings"""
        print("\n" + "="*60)
        print("📊 LEGACY COMPONENTS FOUND")
        print("="*60)
        
        total_items = 0
        
        # File-based execution
        if self.legacy_components['file_based_execution']:
            print(f"\n🔥 File-based Execution ({len(self.legacy_components['file_based_execution'])} references):")
            for item in self.legacy_components['file_based_execution'][:5]:  # Show first 5
                print(f"   {item['file']}:{item['line']} - {item['type']}")
            if len(self.legacy_components['file_based_execution']) > 5:
                print(f"   ... and {len(self.legacy_components['file_based_execution']) - 5} more")
            total_items += len(self.legacy_components['file_based_execution'])
            
        # Wine containers
        if self.legacy_components['wine_containers']:
            print(f"\n🍷 Wine Containers ({len(self.legacy_components['wine_containers'])} found):")
            for item in self.legacy_components['wine_containers']:
                print(f"   {item}")
            total_items += len(self.legacy_components['wine_containers'])
            
        # HTTP endpoints
        if self.legacy_components['http_endpoints']:
            print(f"\n🌐 HTTP Endpoints ({len(self.legacy_components['http_endpoints'])} found):")
            for item in self.legacy_components['http_endpoints']:
                print(f"   {item['file']} - {item['type']}")
            total_items += len(self.legacy_components['http_endpoints'])
            
        # Obsolete EAs
        if self.legacy_components['obsolete_eas']:
            print(f"\n🤖 Obsolete EAs ({len(self.legacy_components['obsolete_eas'])} found):")
            for item in self.legacy_components['obsolete_eas']:
                print(f"   {item}")
            total_items += len(self.legacy_components['obsolete_eas'])
            
        # Old configs
        if self.legacy_components['old_configs']:
            print(f"\n⚙️ Old Configs ({len(self.legacy_components['old_configs'])} found):")
            for item in self.legacy_components['old_configs']:
                if isinstance(item, dict):
                    print(f"   {item['file']} - {item['issue']}")
                else:
                    print(f"   {item}")
            total_items += len(self.legacy_components['old_configs'])
            
        # Temp files
        if self.legacy_components['temp_files']:
            print(f"\n📄 Temp Files ({len(self.legacy_components['temp_files'])} found):")
            for item in self.legacy_components['temp_files'][:10]:  # Show first 10
                print(f"   {item}")
            if len(self.legacy_components['temp_files']) > 10:
                print(f"   ... and {len(self.legacy_components['temp_files']) - 10} more")
            total_items += len(self.legacy_components['temp_files'])
            
        print(f"\n📊 Total legacy items found: {total_items}")
        
        if self.dry_run:
            print("\n⚠️ DRY RUN MODE - No files deleted")
            print("Run with --execute to perform actual deletion")
        
        return total_items

if __name__ == "__main__":
    import sys
    
    dry_run = '--execute' not in sys.argv
    analyzer = LegacyPurgeAnalyzer(dry_run=dry_run)
    analyzer.analyze()