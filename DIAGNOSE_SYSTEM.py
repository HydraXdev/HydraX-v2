#!/usr/bin/env python3
"""
BITTEN System Diagnostic Tool
Identifies and reports all configuration and routing issues
"""

import os
import sys
import json
import asyncio
import requests
from datetime import datetime
import telegram
from colorama import init, Fore, Style

init(autoreset=True)

class SystemDiagnostic:
    """Comprehensive system diagnostic"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.config = {
            'bot_token': 'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")',
            'chat_id': 'int(os.getenv("CHAT_ID", "-1002581996861"))',
            'webapp_url': 'http://134.199.204.67:8888',
            'webapp_port': 8888
        }
    
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{text.center(60)}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def check_file_exists(self, filepath: str, description: str) -> bool:
        """Check if a file exists"""
        if os.path.exists(filepath):
            print(f"{Fore.GREEN}✅ {description}: Found{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ {description}: Missing{Style.RESET_ALL}")
            self.issues.append(f"Missing file: {filepath}")
            return False
    
    def check_process_running(self, process_name: str) -> bool:
        """Check if a process is running"""
        import subprocess
        result = subprocess.run(['pgrep', '-f', process_name], capture_output=True)
        if result.returncode == 0:
            print(f"{Fore.GREEN}✅ {process_name}: Running{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ {process_name}: Not running{Style.RESET_ALL}")
            self.issues.append(f"Process not running: {process_name}")
            return False
    
    def check_port_open(self, port: int) -> bool:
        """Check if a port is open"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"{Fore.GREEN}✅ Port {port}: Open{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Port {port}: Closed{Style.RESET_ALL}")
            self.issues.append(f"Port {port} is not open")
            return False
    
    def check_webapp_health(self) -> bool:
        """Check webapp health"""
        try:
            response = requests.get(f"{self.config['webapp_url']}/test", timeout=5)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ WebApp: Healthy{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠️ WebApp: Status {response.status_code}{Style.RESET_ALL}")
                self.warnings.append(f"WebApp returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ WebApp: Not responding - {e}{Style.RESET_ALL}")
            self.issues.append(f"WebApp not responding: {e}")
            return False
    
    async def check_telegram_bot(self) -> bool:
        """Check Telegram bot connectivity"""
        try:
            bot = telegram.Bot(token=self.config['bot_token'])
            me = await bot.get_me()
            print(f"{Fore.GREEN}✅ Telegram Bot: Connected (@{me.username}){Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Telegram Bot: Failed - {e}{Style.RESET_ALL}")
            self.issues.append(f"Telegram bot error: {e}")
            return False
    
    def check_core_files(self):
        """Check all core files exist"""
        self.print_header("CORE FILES CHECK")
        
        core_files = {
            'src/bitten_core/bitten_core.py': 'BITTEN Core',
            'src/bitten_core/fire_modes.py': 'Fire Modes',
            'src/bitten_core/signal_alerts.py': 'Signal Alerts',
            'src/bitten_core/telegram_router.py': 'Telegram Router',
            'config/telegram.py': 'Telegram Config',
            'config/webapp.py': 'WebApp Config'
        }
        
        for filepath, description in core_files.items():
            self.check_file_exists(filepath, description)
    
    def check_processes(self):
        """Check running processes"""
        self.print_header("PROCESS CHECK")
        
        processes = {
            'webapp_server.py': 'WebApp Server',
            'SIGNAL': 'Signal Bot'
        }
        
        for process, description in processes.items():
            self.check_process_running(process)
    
    def check_network(self):
        """Check network services"""
        self.print_header("NETWORK CHECK")
        
        self.check_port_open(self.config['webapp_port'])
        self.check_webapp_health()
    
    def check_configuration(self):
        """Check configuration consistency"""
        self.print_header("CONFIGURATION CHECK")
        
        # Check webapp config
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from config.webapp import WebAppConfig
            
            if 'joinbitten.com' in WebAppConfig.PRODUCTION_BASE_URL:
                print(f"{Fore.YELLOW}⚠️ WebApp config points to production but running locally{Style.RESET_ALL}")
                self.warnings.append("WebApp configuration mismatch")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Cannot load webapp config: {e}{Style.RESET_ALL}")
            self.issues.append(f"WebApp config error: {e}")
    
    def check_logs(self):
        """Check log files"""
        self.print_header("LOG FILES CHECK")
        
        log_dir = 'logs'
        if os.path.exists(log_dir):
            log_files = os.listdir(log_dir)
            if log_files:
                print(f"{Fore.GREEN}✅ Log directory: {len(log_files)} files found{Style.RESET_ALL}")
                for log in log_files[:5]:  # Show first 5
                    print(f"   - {log}")
            else:
                print(f"{Fore.YELLOW}⚠️ Log directory empty{Style.RESET_ALL}")
                self.warnings.append("No log files found")
        else:
            print(f"{Fore.RED}❌ Log directory missing{Style.RESET_ALL}")
            self.issues.append("Log directory does not exist")
    
    def generate_report(self):
        """Generate diagnostic report"""
        self.print_header("DIAGNOSTIC REPORT")
        
        print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
        print(f"Issues Found: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\n{Fore.RED}Critical Issues:{Style.RESET_ALL}")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
        
        if self.warnings:
            print(f"\n{Fore.YELLOW}Warnings:{Style.RESET_ALL}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")
        
        if not self.issues:
            print(f"\n{Fore.GREEN}✅ System is healthy!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ System needs attention!{Style.RESET_ALL}")
        
        # Generate fix script
        self.generate_fix_script()
    
    def generate_fix_script(self):
        """Generate a script to fix found issues"""
        if not self.issues:
            return
        
        print(f"\n{Fore.CYAN}Generating fix script...{Style.RESET_ALL}")
        
        fix_commands = []
        
        for issue in self.issues:
            if "Process not running: webapp_server.py" in issue:
                fix_commands.append("# Start WebApp server")
                fix_commands.append("cd /root/HydraX-v2 && python3 webapp_server.py &")
            
            elif "Process not running: SIGNAL" in issue:
                fix_commands.append("# Start Signal bot")
                fix_commands.append("cd /root/HydraX-v2 && python3 SIGNALS_REALISTIC.py &")
            
            elif "Log directory does not exist" in issue:
                fix_commands.append("# Create log directory")
                fix_commands.append("mkdir -p /root/HydraX-v2/logs")
            
            elif "Port 8888 is not open" in issue:
                fix_commands.append("# Check if port is blocked by firewall")
                fix_commands.append("sudo ufw allow 8888/tcp")
        
        if fix_commands:
            with open('FIX_ISSUES.sh', 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Auto-generated fix script\n\n")
                for cmd in fix_commands:
                    f.write(f"{cmd}\n")
            
            os.chmod('FIX_ISSUES.sh', 0o755)
            print(f"{Fore.GREEN}✅ Fix script created: ./FIX_ISSUES.sh{Style.RESET_ALL}")

async def main():
    """Run diagnostic"""
    diag = SystemDiagnostic()
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{'BITTEN SYSTEM DIAGNOSTIC'.center(60)}")
    print(f"{Fore.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(60)}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # Run checks
    diag.check_core_files()
    diag.check_processes()
    diag.check_network()
    diag.check_configuration()
    diag.check_logs()
    
    # Async checks
    await diag.check_telegram_bot()
    
    # Generate report
    diag.generate_report()

if __name__ == '__main__':
    asyncio.run(main())