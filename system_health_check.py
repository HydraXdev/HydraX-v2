#!/usr/bin/env python3
"""
Complete System Health Check and Debug Analysis
Checks all components, connections, and potential issues
"""

import subprocess
import json
import time
import psutil
import os
import socket
import requests
from datetime import datetime, timedelta
from pathlib import Path

class SystemHealthCheck:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []
        self.processes = {}
        self.ports = {}
        self.connections = {}
        
    def run_command(self, cmd):
        """Run shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return None
    
    def check_process(self, name, pattern):
        """Check if a process is running"""
        output = self.run_command(f"ps aux | grep '{pattern}' | grep -v grep")
        if output:
            lines = output.split('\n')
            for line in lines:
                if pattern in line:
                    parts = line.split()
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    self.processes[name] = {
                        'pid': pid,
                        'cpu': cpu,
                        'mem': mem,
                        'running': True,
                        'command': ' '.join(parts[10:])
                    }
                    return True
        self.processes[name] = {'running': False}
        return False
    
    def check_port(self, port, description):
        """Check if a port is listening"""
        output = self.run_command(f"netstat -tuln | grep ':{port}'")
        if output and 'LISTEN' in output:
            self.ports[port] = {'status': 'LISTENING', 'description': description}
            return True
        self.ports[port] = {'status': 'CLOSED', 'description': description}
        return False
    
    def check_zmq_connection(self, port):
        """Check ZMQ connections on a port"""
        output = self.run_command(f"lsof -i :{port}")
        connections = []
        if output:
            lines = output.split('\n')[1:]  # Skip header
            for line in lines:
                if 'ESTABLISHED' in line:
                    connections.append(line.strip())
        return connections
    
    def check_file_exists(self, filepath, description):
        """Check if critical file exists"""
        if Path(filepath).exists():
            self.successes.append(f"✅ {description}: {filepath}")
            return True
        else:
            self.warnings.append(f"⚠️ Missing {description}: {filepath}")
            return False
    
    def check_log_errors(self, logfile, max_age_minutes=60):
        """Check for recent errors in log files"""
        if not Path(logfile).exists():
            return []
        
        errors = []
        try:
            with open(logfile, 'r') as f:
                lines = f.readlines()
                for line in lines[-100:]:  # Last 100 lines
                    if 'ERROR' in line or 'CRITICAL' in line or 'Exception' in line:
                        errors.append(line.strip())
        except:
            pass
        return errors
    
    def test_http_endpoint(self, url, description):
        """Test HTTP endpoint availability"""
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                self.successes.append(f"✅ {description} responding at {url}")
                return True
            else:
                self.warnings.append(f"⚠️ {description} returned {response.status_code}")
                return False
        except:
            self.issues.append(f"❌ {description} not responding at {url}")
            return False
    
    def run_full_check(self):
        """Run complete system health check"""
        print("=" * 60)
        print("🔍 BITTEN SYSTEM HEALTH CHECK")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 60)
        
        # 1. CHECK CORE PROCESSES
        print("\n📊 CHECKING CORE PROCESSES...")
        print("-" * 40)
        
        critical_processes = [
            ('Elite Guard', 'elite_guard_with_citadel.py'),
            ('Fire Publisher', 'safe_fire_publisher_fix.py'),
            ('Production Bot', 'bitten_production_bot.py'),
            ('WebApp Server', 'webapp_server_optimized.py'),
            ('Telemetry Bridge', 'zmq_telemetry_bridge'),
            ('Market Watchdog', 'market_data_watchdog.py'),
            ('Venom Watchdog', 'venom_stream_watchdog'),
        ]
        
        for name, pattern in critical_processes:
            if self.check_process(name, pattern):
                proc = self.processes[name]
                print(f"✅ {name}: PID {proc['pid']} (CPU: {proc['cpu']}%, MEM: {proc['mem']}%)")
            else:
                print(f"❌ {name}: NOT RUNNING")
                self.issues.append(f"{name} is not running")
        
        # 2. CHECK ZMQ PORTS
        print("\n🔌 CHECKING ZMQ PORTS...")
        print("-" * 40)
        
        zmq_ports = [
            (5555, 'Fire Commands to EA'),
            (5556, 'Market Data from EA'),
            (5557, 'Elite Guard Signals'),
            (5560, 'Telemetry Relay'),
        ]
        
        for port, desc in zmq_ports:
            if self.check_port(port, desc):
                print(f"✅ Port {port}: LISTENING ({desc})")
                connections = self.check_zmq_connection(port)
                if connections:
                    print(f"   → {len(connections)} active connections")
            else:
                print(f"❌ Port {port}: NOT LISTENING ({desc})")
                self.issues.append(f"Port {port} not listening")
        
        # 3. CHECK WEB SERVICES
        print("\n🌐 CHECKING WEB SERVICES...")
        print("-" * 40)
        
        self.test_http_endpoint('http://localhost:8888/health', 'WebApp Health')
        self.test_http_endpoint('http://localhost:8001/market-data/health', 'Market Data Receiver')
        
        # 4. CHECK CRITICAL FILES
        print("\n📁 CHECKING CRITICAL FILES...")
        print("-" * 40)
        
        critical_files = [
            ('/root/HydraX-v2/user_registry.json', 'User Registry'),
            ('/root/HydraX-v2/citadel_state.json', 'CITADEL State'),
            ('/root/HydraX-v2/truth_log.jsonl', 'Truth Log'),
        ]
        
        for filepath, desc in critical_files:
            self.check_file_exists(filepath, desc)
        
        # 5. CHECK FOR ERRORS IN LOGS
        print("\n📋 CHECKING RECENT LOG ERRORS...")
        print("-" * 40)
        
        log_files = [
            '/tmp/final_fire_publisher.log',
            '/root/HydraX-v2/elite_guard.log',
            '/root/HydraX-v2/bitten_production_bot.log',
            '/root/HydraX-v2/webapp.log',
        ]
        
        total_errors = 0
        for logfile in log_files:
            errors = self.check_log_errors(logfile)
            if errors:
                print(f"⚠️ {Path(logfile).name}: {len(errors)} recent errors")
                total_errors += len(errors)
                for error in errors[-3:]:  # Show last 3 errors
                    print(f"   → {error[:100]}...")
        
        if total_errors == 0:
            print("✅ No recent errors in log files")
        
        # 6. CHECK SIGNAL GENERATION
        print("\n📡 CHECKING SIGNAL GENERATION...")
        print("-" * 40)
        
        # Check Elite Guard threshold
        try:
            with open('/root/HydraX-v2/citadel_state.json', 'r') as f:
                citadel = json.load(f)
                threshold = citadel.get('global', {}).get('adaptive_throttle', {}).get('tcs_threshold', 0)
                print(f"📊 CITADEL Threshold: {threshold}%")
                if threshold > 60:
                    self.warnings.append(f"Threshold too high: {threshold}% (should be ~50%)")
                    print(f"⚠️ Threshold may be too high for signal generation")
        except:
            self.issues.append("Cannot read CITADEL state")
        
        # Check last signal time
        output = self.run_command("tail -1 /root/HydraX-v2/truth_log.jsonl")
        if output:
            try:
                last_signal = json.loads(output)
                signal_time = datetime.fromisoformat(last_signal['generated_at'].replace('Z', '+00:00'))
                age = datetime.now() - signal_time.replace(tzinfo=None)
                print(f"📅 Last signal: {age.total_seconds()/3600:.1f} hours ago")
                if age.total_seconds() > 86400:  # More than 24 hours
                    self.warnings.append("No signals in 24+ hours")
            except:
                pass
        
        # 7. CHECK ORPHANED PROCESSES
        print("\n🧹 CHECKING FOR ORPHANED PROCESSES...")
        print("-" * 40)
        
        orphan_patterns = [
            'venom_v7',
            'apex_venom',
            'signal_generator',
            'market_receiver',
            'bridge_troll',
        ]
        
        orphans_found = 0
        for pattern in orphan_patterns:
            output = self.run_command(f"ps aux | grep '{pattern}' | grep -v grep")
            if output:
                orphans_found += 1
                print(f"⚠️ Found orphaned process: {pattern}")
                self.warnings.append(f"Orphaned process: {pattern}")
        
        if orphans_found == 0:
            print("✅ No orphaned processes found")
        
        # 8. CHECK DISK SPACE
        print("\n💾 CHECKING DISK SPACE...")
        print("-" * 40)
        
        output = self.run_command("df -h / | tail -1")
        if output:
            parts = output.split()
            used_percent = parts[4].strip('%')
            available = parts[3]
            print(f"📊 Disk usage: {used_percent}% used, {available} available")
            if int(used_percent) > 90:
                self.issues.append(f"Disk space critical: {used_percent}% used")
        
        # 9. CHECK EA CONNECTION
        print("\n🤖 CHECKING EA CONNECTION...")
        print("-" * 40)
        
        ea_connections = self.run_command("lsof -i :5555 | grep ESTABLISHED | wc -l")
        if ea_connections and int(ea_connections) > 0:
            print(f"✅ EA has {ea_connections} active connections to port 5555")
        else:
            self.issues.append("EA not connected to port 5555")
            print("❌ EA not connected to port 5555")
        
        # FINAL SUMMARY
        print("\n" + "=" * 60)
        print("📊 SYSTEM HEALTH SUMMARY")
        print("=" * 60)
        
        if not self.issues:
            print("✅ SYSTEM STATUS: HEALTHY")
            print("All critical components are running properly")
        else:
            print("❌ SYSTEM STATUS: ISSUES DETECTED")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        print("\n🚀 MARKET OPEN READINESS:")
        market_ready = len(self.issues) == 0
        if market_ready:
            print("✅ System is READY for market open")
            if threshold > 60:
                print("⚠️ BUT: Consider lowering Elite Guard threshold to ~50")
        else:
            print("❌ System needs attention before market open")
            print("   Fix the issues listed above")
        
        return {
            'healthy': len(self.issues) == 0,
            'issues': self.issues,
            'warnings': self.warnings,
            'processes': self.processes,
            'ports': self.ports
        }

if __name__ == "__main__":
    checker = SystemHealthCheck()
    result = checker.run_full_check()
    
    # Save report
    with open('/root/HydraX-v2/system_health_report.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n📄 Full report saved to: /root/HydraX-v2/system_health_report.json")