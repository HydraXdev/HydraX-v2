#!/usr/bin/env python3
"""
Press Pass System Monitor
Monitors the health and performance of Press Pass integration
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from collections import defaultdict

class PressPassMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.error_counts = defaultdict(int)
        self.health_checks = []
        
    def check_nginx_errors(self):
        """Check Nginx error logs for Press Pass related errors"""
        try:
            # Get last 100 lines of nginx error log
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/nginx/error.log"],
                capture_output=True,
                text=True
            )
            
            errors = []
            for line in result.stdout.split('\n'):
                if any(keyword in line.lower() for keyword in ['press', 'pass', 'pp_', 'telegram']):
                    errors.append(line)
                    
            return len(errors) == 0, errors
        except Exception as e:
            return False, [str(e)]
    
    def check_bot_status(self):
        """Check if Telegram bot is running"""
        try:
            # Check if bot process is running
            result = subprocess.run(
                ["pgrep", "-f", "telegram.*bot|hydrax.*bot"],
                capture_output=True
            )
            
            if result.returncode == 0:
                return True, "Bot process found"
            else:
                # Check systemd service
                result = subprocess.run(
                    ["systemctl", "is-active", "hydrax-bot"],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout.strip() == "active":
                    return True, "Bot service active"
                else:
                    return False, "Bot not running"
                    
        except Exception as e:
            return False, str(e)
    
    def check_web_endpoints(self):
        """Check web endpoints are accessible"""
        import requests
        
        endpoints = [
            ("http://localhost/", "Landing page"),
            ("http://localhost/index.html", "Index page")
        ]
        
        results = []
        for url, name in endpoints:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    # Check for Press Pass content
                    if "press pass" in response.text.lower():
                        results.append((True, f"{name}: OK (Press Pass content found)"))
                    else:
                        results.append((False, f"{name}: No Press Pass content"))
                else:
                    results.append((False, f"{name}: HTTP {response.status_code}"))
            except Exception as e:
                results.append((False, f"{name}: {str(e)}"))
        
        all_ok = all(r[0] for r in results)
        return all_ok, results
    
    def check_component_health(self):
        """Check if Press Pass components are healthy"""
        components = [
            "src/bitten_core/press_pass_manager.py",
            "src/bitten_core/press_pass_scheduler.py",
            "src/bitten_core/press_pass_commands.py",
            "src/bitten_core/telegram_router.py"
        ]
        
        results = []
        for component in components:
            if os.path.exists(component):
                # Check file modification time
                mtime = os.path.getmtime(component)
                mod_time = datetime.fromtimestamp(mtime)
                
                # Check if recently modified (within last hour)
                if (datetime.now() - mod_time).seconds < 3600:
                    results.append((True, f"{os.path.basename(component)}: Recently updated"))
                else:
                    results.append((True, f"{os.path.basename(component)}: OK"))
            else:
                results.append((False, f"{os.path.basename(component)}: Missing"))
        
        all_ok = all(r[0] for r in results)
        return all_ok, results
    
    def generate_health_report(self):
        """Generate comprehensive health report"""
        print("\n" + "="*60)
        print("PRESS PASS SYSTEM HEALTH REPORT")
        print("="*60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Uptime: {datetime.now() - self.start_time}")
        print("\n")
        
        # Run all health checks
        checks = [
            ("Nginx Errors", self.check_nginx_errors()),
            ("Bot Status", self.check_bot_status()),
            ("Web Endpoints", self.check_web_endpoints()),
            ("Component Health", self.check_component_health())
        ]
        
        overall_health = True
        
        for check_name, (status, details) in checks:
            icon = "✅" if status else "❌"
            print(f"{icon} {check_name}: {'HEALTHY' if status else 'ISSUES DETECTED'}")
            
            if not status:
                overall_health = False
            
            if isinstance(details, list):
                for detail in details:
                    if isinstance(detail, tuple):
                        detail_icon = "✓" if detail[0] else "✗"
                        print(f"   {detail_icon} {detail[1]}")
                    else:
                        print(f"   - {detail}")
            else:
                print(f"   {details}")
            print()
        
        # Summary
        print("\n" + "-"*60)
        if overall_health:
            print("✅ SYSTEM STATUS: HEALTHY")
            print("All Press Pass components are functioning normally.")
        else:
            print("⚠️  SYSTEM STATUS: ISSUES DETECTED")
            print("Some components require attention. Check details above.")
        
        return overall_health
    
    def continuous_monitor(self, interval=60):
        """Run continuous monitoring"""
        print("Starting Press Pass continuous monitoring...")
        print(f"Checking every {interval} seconds. Press Ctrl+C to stop.")
        
        try:
            while True:
                self.generate_health_report()
                
                # Save report to file
                report_file = f"deployment/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(report_file, 'w') as f:
                    # Redirect stdout to file temporarily
                    old_stdout = sys.stdout
                    sys.stdout = f
                    self.generate_health_report()
                    sys.stdout = old_stdout
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
            return

def main():
    monitor = PressPassMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        monitor.continuous_monitor(interval)
    else:
        # Single health check
        monitor.generate_health_report()

if __name__ == "__main__":
    main()