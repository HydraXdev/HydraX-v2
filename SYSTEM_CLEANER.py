#!/usr/bin/env python3
"""
🧹 SYSTEM CLEANER - Remove contaminated restart mechanisms
Systematically clean the system of auto-restart threats
"""

import os
import re
import shutil
from typing import List

class SystemCleaner:
    
    def __init__(self):
        self.cleaned_files = []
        self.quarantined_files = []
        self.errors = []
        
    def clean_bot_tokens(self):
        """Replace bot tokens with disabled versions"""
        print("🔐 Cleaning bot tokens...")
        
        files_to_clean = []
        for root, dirs, files in os.walk('/root/HydraX-v2'):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        if '7854827710' in content:
                            files_to_clean.append(filepath)
                    except:
                        pass
        
        for filepath in files_to_clean:
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Replace bot token with disabled version
                new_content = content.replace(
                    'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")',
                    'DISABLED_BOT_TOKEN_FOR_SECURITY'
                )
                
                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    self.cleaned_files.append(filepath)
                    print(f"  ✅ Cleaned: {filepath}")
                    
            except Exception as e:
                self.errors.append(f"Error cleaning {filepath}: {e}")
    
    def quarantine_dangerous_files(self):
        """Move dangerous files to quarantine"""
        print("🚫 Quarantining dangerous files...")
        
        dangerous_files = [
            '/root/HydraX-v2/scripts/webapp-watchdog.py',
            '/root/HydraX-v2/intelligent_controller.py',
            '/root/HydraX-v2/scripts/webapp-monitor.sh',
            '/root/HydraX-v2/bulletproof_agents/',
        ]
        
        quarantine_dir = '/root/HydraX-v2/QUARANTINE'
        os.makedirs(quarantine_dir, exist_ok=True)
        
        for item in dangerous_files:
            if os.path.exists(item):
                try:
                    basename = os.path.basename(item)
                    if os.path.isdir(item):
                        shutil.move(item, os.path.join(quarantine_dir, basename))
                    else:
                        shutil.move(item, os.path.join(quarantine_dir, basename))
                    self.quarantined_files.append(item)
                    print(f"  🚫 Quarantined: {item}")
                except Exception as e:
                    self.errors.append(f"Error quarantining {item}: {e}")
    
    def clean_infinite_loops(self):
        """Comment out dangerous infinite loops"""
        print("🔄 Neutralizing infinite loops...")
        
        patterns_to_disable = [
            (r'(\s*)(while\s+True\s*:)', r'\1# SECURITY: Disabled infinite loop\n\1if False:  # \2'),
            (r'(\s*)(while\s+self\.running\s*:)', r'\1# SECURITY: Disabled monitoring loop\n\1if False:  # \2'),
            (r'(\s*)(autorestart:\s*true)', r'\1# SECURITY: Disabled auto-restart\n\1autorestart: false  # \2'),
            (r'(\s*)(Restart=always)', r'\1# SECURITY: Disabled SystemD restart\n\1Restart=no  # \2'),
        ]
        
        for root, dirs, files in os.walk('/root/HydraX-v2'):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'QUARANTINE']
            for file in files:
                if file.endswith(('.py', '.sh', '.service', '.js', '.yml')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        
                        new_content = content
                        changed = False
                        
                        for pattern, replacement in patterns_to_disable:
                            if re.search(pattern, new_content, re.IGNORECASE):
                                new_content = re.sub(pattern, replacement, new_content, flags=re.IGNORECASE)
                                changed = True
                        
                        if changed:
                            with open(filepath, 'w') as f:
                                f.write(new_content)
                            self.cleaned_files.append(filepath)
                            print(f"  ✅ Neutralized loops: {filepath}")
                            
                    except Exception as e:
                        self.errors.append(f"Error cleaning loops in {filepath}: {e}")
    
    def create_monitoring_system(self):
        """Create a clean monitoring system"""
        print("👁️ Creating clean monitoring system...")
        
        monitor_content = '''#!/usr/bin/env python3
"""
🛡️ CLEAN MONITOR - Restart-free system monitoring
Only monitors, never restarts anything automatically
"""

import time
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_system_health():
    """Check system health without restarting anything"""
    health = {
        'timestamp': datetime.now().isoformat(),
        'processes': {},
        'threats': []
    }
    
    # Check for unauthorized processes
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\\n'):
            if any(pattern in line.lower() for pattern in ['telegram', 'signals', 'bot']):
                if 'grep' not in line and line.strip():
                    health['threats'].append(f"Unauthorized process: {line.strip()}")
    except:
        pass
    
    # Log health status
    if health['threats']:
        logger.warning(f"THREATS DETECTED: {len(health['threats'])}")
        for threat in health['threats']:
            logger.warning(f"  {threat}")
    else:
        logger.info("System clean - no unauthorized processes")
    
    return health

def main():
    """Main monitoring loop - SAFE VERSION"""
    logger.info("🛡️ Clean monitor starting - NO AUTO-RESTART CAPABILITY")
    
    while True:
        try:
            health = check_system_health()
            # Only log, never restart
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
'''
        
        with open('/root/HydraX-v2/CLEAN_MONITOR.py', 'w') as f:
            f.write(monitor_content)
        print("  ✅ Created clean monitoring system")
    
    def run_full_clean(self):
        """Run complete system cleaning"""
        print("🧹 SYSTEM CLEANER - Starting comprehensive cleanup")
        print("="*60)
        
        self.clean_bot_tokens()
        self.quarantine_dangerous_files()
        self.clean_infinite_loops()
        self.create_monitoring_system()
        
        print("="*60)
        print("🎯 CLEANUP SUMMARY:")
        print(f"  Files cleaned: {len(self.cleaned_files)}")
        print(f"  Files quarantined: {len(self.quarantined_files)}")
        print(f"  Errors: {len(self.errors)}")
        
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  {error}")
        
        print("✅ System cleanup completed")

if __name__ == "__main__":
    cleaner = SystemCleaner()
    cleaner.run_full_clean()