#!/usr/bin/env python3
"""
🎯 APEX ENGINE SUPERVISOR AGENT
Monitors, diagnoses, and optimizes the APEX v5.0 engine in real-time
Knows everything about engine performance, signals, and troubleshooting
"""

import time
import logging
import requests
import json
import subprocess
import os
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import psutil

class APEXEngineSupervisor:
    def __init__(self):
        self.logger = self.setup_logging()
        self.engine_pid = None
        self.last_signal_time = None
        self.signal_count = 0
        self.bridge_status = "UNKNOWN"
        self.engine_health = "UNKNOWN"
        self.session_performance = {}
        
        # Performance thresholds
        self.max_scan_time = 15  # seconds
        self.min_signals_per_hour = 2
        self.max_memory_mb = 200
        
        self.logger.info("🎯 APEX ENGINE SUPERVISOR INITIALIZED")
    
    def setup_logging(self) -> logging.Logger:
        """Setup supervisor logging"""
        logger = logging.getLogger("APEX_SUPERVISOR")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('/root/HydraX-v2/apex_supervisor.log')
        formatter = logging.Formatter('%(asctime)s - SUPERVISOR - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def check_engine_process(self) -> Dict:
        """Check if APEX engine process is running"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                if 'apex_v5_live_real.py' in str(proc.info.get('cmdline', [])):
                    processes.append({
                        'pid': proc.info['pid'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cpu_percent': proc.info['cpu_percent'],
                        'status': 'RUNNING'
                    })
            
            if processes:
                self.engine_pid = processes[0]['pid']
                return {
                    'status': 'RUNNING',
                    'processes': processes,
                    'health': 'HEALTHY' if processes[0]['memory_mb'] < self.max_memory_mb else 'HIGH_MEMORY'
                }
            else:
                return {'status': 'STOPPED', 'processes': [], 'health': 'DEAD'}
                
        except Exception as e:
            self.logger.error(f"❌ Error checking engine process: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def check_bridge_connection(self) -> Dict:
        """Test bridge connection and file availability"""
        try:
            response = requests.post(
                "http://3.145.84.187:5555/execute",
                json={
                    "command": "Get-ChildItem -Path C:\\\\MT5_Farm\\\\Bridge\\\\Incoming\\\\ | Measure-Object | Select-Object Count",
                    "type": "powershell"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'status': 'CONNECTED',
                        'bridge_health': 'HEALTHY',
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    }
            
            return {'status': 'FAILED', 'bridge_health': 'UNHEALTHY'}
            
        except Exception as e:
            return {'status': 'ERROR', 'bridge_health': 'DEAD', 'error': str(e)}
    
    def analyze_engine_logs(self) -> Dict:
        """Analyze APEX engine logs for performance and issues"""
        try:
            if not os.path.exists('/root/HydraX-v2/apex_v5_live_real.log'):
                return {'status': 'NO_LOGS', 'signals_found': 0}
            
            with open('/root/HydraX-v2/apex_v5_live_real.log', 'r') as f:
                logs = f.readlines()
            
            # Analyze log patterns
            scan_cycles = 0
            signals_generated = 0
            errors = 0
            last_activity = None
            
            for line in logs:
                if '🔄 Starting scan cycle' in line:
                    scan_cycles += 1
                    last_activity = line.split(' - ')[0]
                elif '🎯 SIGNAL #' in line:
                    signals_generated += 1
                    self.last_signal_time = line.split(' - ')[0]
                elif 'ERROR' in line or '❌' in line:
                    errors += 1
            
            return {
                'status': 'ANALYZED',
                'scan_cycles': scan_cycles,
                'signals_generated': signals_generated,
                'errors': errors,
                'last_activity': last_activity,
                'last_signal': self.last_signal_time,
                'performance': 'GOOD' if errors == 0 and scan_cycles > 0 else 'ISSUES'
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    def get_current_session_info(self) -> Dict:
        """Get current trading session and expected performance"""
        hour = datetime.utcnow().hour
        
        if 12 <= hour < 16:
            session = 'OVERLAP'
            expected_signals = 8  # per hour
            boost = 20
        elif 7 <= hour < 16:
            session = 'LONDON'
            expected_signals = 6
            boost = 15
        elif 13 <= hour < 22:
            session = 'NY'
            expected_signals = 5
            boost = 12
        elif 22 <= hour or hour < 7:
            session = 'ASIAN'
            expected_signals = 2
            boost = 8
        else:
            session = 'NORMAL'
            expected_signals = 3
            boost = 5
        
        return {
            'session': session,
            'hour_utc': hour,
            'expected_signals_per_hour': expected_signals,
            'tcs_boost': boost,
            'activity_level': 'HIGH' if session in ['OVERLAP', 'LONDON'] else 'MEDIUM' if session == 'NY' else 'LOW'
        }
    
    def diagnose_no_signals(self) -> Dict:
        """Diagnose why no signals are being generated"""
        diagnosis = {
            'issues': [],
            'recommendations': [],
            'severity': 'INFO'
        }
        
        # Check session
        session_info = self.get_current_session_info()
        if session_info['activity_level'] == 'LOW':
            diagnosis['issues'].append(f"Currently in {session_info['session']} session (low activity)")
            diagnosis['recommendations'].append("Wait for LONDON session (7-16 UTC) for higher signal volume")
        
        # Check bridge connection
        bridge_status = self.check_bridge_connection()
        if bridge_status['status'] != 'CONNECTED':
            diagnosis['issues'].append("Bridge connection issues")
            diagnosis['recommendations'].append("Check bridge server at 3.145.84.187:5555")
            diagnosis['severity'] = 'HIGH'
        
        # Check engine health
        engine_status = self.check_engine_process()
        if engine_status['status'] != 'RUNNING':
            diagnosis['issues'].append("APEX engine not running")
            diagnosis['recommendations'].append("Restart APEX engine immediately")
            diagnosis['severity'] = 'CRITICAL'
        
        return diagnosis
    
    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'components': {},
            'recommendations': []
        }
        
        # Check all components
        report['components']['engine'] = self.check_engine_process()
        report['components']['bridge'] = self.check_bridge_connection()
        report['components']['logs'] = self.analyze_engine_logs()
        report['components']['session'] = self.get_current_session_info()
        
        # Determine overall status
        if report['components']['engine']['status'] != 'RUNNING':
            report['overall_status'] = 'CRITICAL'
            report['recommendations'].append("🚨 RESTART APEX ENGINE IMMEDIATELY")
        elif report['components']['bridge']['status'] != 'CONNECTED':
            report['overall_status'] = 'DEGRADED'
            report['recommendations'].append("🔧 Check bridge connection")
        elif report['components']['logs']['signals_generated'] == 0:
            report['overall_status'] = 'WARNING'
            report['recommendations'].append("⚠️ No signals generated - check TCS thresholds")
        else:
            report['overall_status'] = 'HEALTHY'
            report['recommendations'].append("✅ All systems operational")
        
        return report
    
    def auto_restart_engine(self) -> bool:
        """Automatically restart APEX engine if needed"""
        try:
            self.logger.info("🔄 Auto-restarting APEX engine")
            
            # Check if singleton lock exists
            lock_file = Path('/root/HydraX-v2/.apex_engine.lock')
            pid_file = Path('/root/HydraX-v2/.apex_engine.pid')
            
            # Kill existing processes PROPERLY
            if pid_file.exists():
                try:
                    old_pid = int(pid_file.read_text().strip())
                    self.logger.info(f"🔫 Killing old APEX process PID={old_pid}")
                    os.kill(old_pid, signal.SIGTERM)
                    time.sleep(2)
                except:
                    pass
            
            # Clean up lock files
            if lock_file.exists():
                lock_file.unlink()
            if pid_file.exists():
                pid_file.unlink()
            
            # Start new process (singleton will handle duplicate prevention)
            subprocess.Popen([
                'python3', '/root/HydraX-v2/apex_v5_live_real.py'
            ], stdout=open('/root/HydraX-v2/apex_v5_live_real.log', 'a'),  # append, don't overwrite!
               stderr=subprocess.STDOUT)
            
            time.sleep(5)
            
            # Verify restart
            engine_status = self.check_engine_process()
            if engine_status['status'] == 'RUNNING':
                self.logger.info("✅ APEX engine restarted successfully")
                return True
            else:
                self.logger.error("❌ APEX engine restart failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Auto-restart failed: {e}")
            return False
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("🎯 Starting APEX Engine Supervision")
        
        while True:
            try:
                # Generate health report
                report = self.generate_health_report()
                
                # Log status
                self.logger.info(f"📊 System Status: {report['overall_status']}")
                self.logger.info(f"🔧 Engine: {report['components']['engine']['status']}")
                self.logger.info(f"🌉 Bridge: {report['components']['bridge']['status']}")
                self.logger.info(f"📈 Signals: {report['components']['logs']['signals_generated']}")
                
                # Auto-healing actions
                if report['overall_status'] == 'CRITICAL':
                    self.logger.warning("🚨 CRITICAL STATUS - Attempting auto-restart")
                    self.auto_restart_engine()
                
                # Print recommendations
                for rec in report['recommendations']:
                    self.logger.info(f"💡 {rec}")
                
                # Wait before next check
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Supervisor stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Supervisor error: {e}")
                time.sleep(30)

def main():
    supervisor = APEXEngineSupervisor()
    supervisor.monitor_loop()

if __name__ == "__main__":
    main()