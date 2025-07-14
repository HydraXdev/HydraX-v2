#!/usr/bin/env python3
"""
🛡️ SECURITY SCANNER - Detect Auto-Restart Mechanisms
Scans for dangerous patterns before git pulls
"""

import os
import re
import subprocess
import json
from typing import List, Dict, Tuple

class SecurityScanner:
    
    DANGEROUS_PATTERNS = [
        # Auto-restart patterns
        r'autorestart.*[=:].*true',
        r'Restart.*[=:].*always',
        r'daemon.*[=:].*True',
        
        # Infinite loops
        r'while\s+True\s*:',
        r'while\s+self\.running\s*:',
        r'while\s+.*running.*:',
        
        # Process spawning
        r'subprocess\.Popen.*restart',
        r'threading\.Thread.*daemon.*True',
        r'os\.system.*restart',
        
        # Scheduled tasks
        r'schtasks.*create',
        r'crontab.*restart',
        r'systemctl.*enable',
        
        # Port chasing patterns  
        r'port.*\+.*1',
        r'find.*available.*port',
        r'port.*range.*\d+.*\d+',
        
        # Monitoring patterns
        r'psutil\.process_iter',
        r'pkill.*restart',
        r'killall.*python',
        
        # Network restart triggers
        r'ssh.*restart',
        r'remote.*execute.*restart',
        
        # Bot token usage
        r'7854827710',  # The specific bot token
        r'telegram.*bot.*start',
    ]
    
    DANGEROUS_FILES = [
        'webapp-watchdog.py',
        'intelligent_controller.py', 
        'webapp-monitor.sh',
        'NUCLEAR_STOP_ALL.py',  # Ironically, this is also dangerous if misused
        'BULLETPROOF_BOT_MANAGER.py',
    ]
    
    def scan_file(self, filepath: str) -> List[Dict]:
        """Scan a single file for dangerous patterns"""
        threats = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in self.DANGEROUS_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        threats.append({
                            'file': filepath,
                            'line': i,
                            'pattern': pattern,
                            'content': line.strip(),
                            'severity': 'HIGH'
                        })
                        
        except Exception as e:
            threats.append({
                'file': filepath,
                'line': 0,
                'pattern': 'SCAN_ERROR',
                'content': str(e),
                'severity': 'ERROR'
            })
            
        return threats
    
    def scan_directory(self, directory: str) -> Dict:
        """Scan entire directory for threats"""
        all_threats = []
        
        for root, dirs, files in os.walk(directory):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith(('.py', '.sh', '.service', '.js', '.yml', '.yaml')):
                    filepath = os.path.join(root, file)
                    threats = self.scan_file(filepath)
                    all_threats.extend(threats)
                    
                # Flag dangerous files by name
                if file in self.DANGEROUS_FILES:
                    all_threats.append({
                        'file': filepath,
                        'line': 0,
                        'pattern': 'DANGEROUS_FILENAME',
                        'content': f'File {file} is known to contain restart mechanisms',
                        'severity': 'CRITICAL'
                    })
        
        return {
            'total_threats': len(all_threats),
            'threats': all_threats,
            'summary': self._generate_summary(all_threats)
        }
    
    def _generate_summary(self, threats: List[Dict]) -> Dict:
        """Generate threat summary"""
        by_severity = {}
        by_file = {}
        
        for threat in threats:
            severity = threat['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            file = threat['file']
            by_file[file] = by_file.get(file, 0) + 1
            
        return {
            'by_severity': by_severity,
            'by_file': by_file,
            'most_dangerous_files': sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def scan_git_diff(self, commit_range: str = "HEAD~1..HEAD") -> Dict:
        """Scan git diff for dangerous additions"""
        try:
            result = subprocess.run(
                ['git', 'diff', commit_range], 
                capture_output=True, text=True, cwd='/root/HydraX-v2'
            )
            
            if result.returncode != 0:
                return {'error': f'Git diff failed: {result.stderr}'}
                
            diff_content = result.stdout
            threats = []
            
            for i, line in enumerate(diff_content.split('\n'), 1):
                if line.startswith('+'):  # Only check additions
                    for pattern in self.DANGEROUS_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            threats.append({
                                'line': i,
                                'pattern': pattern,
                                'content': line.strip(),
                                'severity': 'HIGH',
                                'type': 'GIT_ADDITION'
                            })
                            
            return {
                'total_threats': len(threats),
                'threats': threats
            }
            
        except Exception as e:
            return {'error': str(e)}

def main():
    scanner = SecurityScanner()
    
    print("🛡️ SECURITY SCANNER - Scanning for auto-restart mechanisms...")
    
    # Scan current directory
    results = scanner.scan_directory('/root/HydraX-v2')
    
    print(f"\n📊 SCAN RESULTS:")
    print(f"Total threats found: {results['total_threats']}")
    
    if results['threats']:
        print(f"\n🚨 THREATS DETECTED:")
        for threat in results['threats'][:20]:  # Show first 20
            print(f"  {threat['severity']} | {threat['file']}:{threat['line']}")
            print(f"    Pattern: {threat['pattern']}")
            print(f"    Content: {threat['content'][:100]}...")
            print()
            
        print(f"\n📈 SUMMARY:")
        for severity, count in results['summary']['by_severity'].items():
            print(f"  {severity}: {count}")
            
        print(f"\n🎯 MOST DANGEROUS FILES:")
        for file, count in results['summary']['most_dangerous_files']:
            print(f"  {file}: {count} threats")
    else:
        print("✅ No threats detected")
    
    return results['total_threats']

if __name__ == "__main__":
    threat_count = main()
    exit(1 if threat_count > 0 else 0)