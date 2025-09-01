#!/usr/bin/env python3
"""
BITTEN Monitoring Dashboard - Real-time system health monitoring
"""
import subprocess
import json
import time
import os
from datetime import datetime, timedelta

def get_status():
    status = {
        'timestamp': datetime.now().isoformat(),
        'services': {},
        'signals': {},
        'health': {}
    }
    
    # Check services
    services = [
        'bitten_production_bot',
        'elite_guard_with_citadel', 
        'elite_guard_zmq_relay',
        'core_engine_zmq_relay',
        'black_box_complete_truth_system',
        'core_crypto_engine'
    ]
    
    for service in services:
        try:
            result = subprocess.run(['pgrep', '-f', service], capture_output=True, text=True)
            status['services'][service] = 'RUNNING' if result.returncode == 0 else 'DEAD'
        except:
            status['services'][service] = 'ERROR'
    
    # Check recent signals with enhanced tracking
    try:
        truth_log = '/root/HydraX-v2/truth_log.jsonl'
        if os.path.exists(truth_log):
            with open(truth_log, 'r') as f:
                lines = f.readlines()
                last_hour = 0
                last_day = 0
                wins = 0
                losses = 0
                sent_to_users = 0
                user_executions = 0
                completed_signals = 0
                
                for line in lines[-200:]:  # Check last 200 entries
                    try:
                        entry = json.loads(line)
                        if 'generated_at' in entry:
                            gen_time = datetime.fromisoformat(entry['generated_at'].replace('Z', ''))
                            if gen_time > datetime.now() - timedelta(hours=1):
                                last_hour += 1
                            if gen_time > datetime.now() - timedelta(hours=24):
                                last_day += 1
                                if entry.get('outcome') == 'win':
                                    wins += 1
                                elif entry.get('outcome') == 'loss':
                                    losses += 1
                                if entry.get('sent_to_users', False):
                                    sent_to_users += 1
                                if entry.get('execution_count', 0) > 0:
                                    user_executions += 1
                                if entry.get('completed', False):
                                    completed_signals += 1
                    except:
                        continue
                
                status['signals']['last_hour'] = last_hour
                status['signals']['last_24h'] = last_day
                status['signals']['win_rate'] = f"{(wins/(wins+losses)*100):.1f}%" if (wins+losses) > 0 else "N/A"
                status['signals']['completed'] = completed_signals
                status['signals']['sent_to_users'] = sent_to_users
                status['signals']['user_executions'] = user_executions
                status['signals']['delivery_rate'] = f"{(sent_to_users/last_day*100):.1f}%" if last_day > 0 else "N/A"
    except Exception as e:
        status['signals']['error'] = str(e)
    
    # Check ports
    try:
        ports = ['5555', '5556', '5557', '5558', '5559', '5560', '8888']
        result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True)
        for port in ports:
            status['health'][f'port_{port}'] = 'LISTENING' if f':{port}' in result.stdout else 'CLOSED'
    except:
        pass
    
    # Check system resources
    try:
        # Memory
        mem_result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        if mem_result.returncode == 0:
            lines = mem_result.stdout.split('\n')
            if len(lines) > 1:
                mem_line = lines[1].split()
                if len(mem_line) > 2:
                    status['health']['memory'] = f"{mem_line[2]}/{mem_line[1]}"
        
        # Disk
        disk_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        if disk_result.returncode == 0:
            lines = disk_result.stdout.split('\n')
            if len(lines) > 1:
                disk_line = lines[1].split()
                if len(disk_line) > 3:
                    status['health']['disk'] = f"{disk_line[2]}/{disk_line[1]} ({disk_line[4]})"
    except:
        pass
    
    return status

def main():
    print("🚀 BITTEN Monitoring Dashboard Starting...")
    
    while True:
        try:
            status = get_status()
            
            # Clear screen and display
            print("\033[2J\033[H")  # Clear screen
            print("=" * 60)
            print("🎯 BITTEN MONITORING DASHBOARD")
            print("=" * 60)
            print(f"🕐 Time: {status['timestamp']}")
            print("-" * 60)
            
            print("\n🔧 SERVICES:")
            for service, state in status['services'].items():
                emoji = "✅" if state == "RUNNING" else "❌"
                print(f"  {emoji} {service}: {state}")
            
            print("\n📊 SIGNALS:")
            for key, value in status['signals'].items():
                if key == 'delivery_rate':
                    emoji = "🚨" if value != "N/A" and float(value.replace('%', '')) < 50 else "✅"
                    print(f"  {emoji} {key}: {value}")
                elif key == 'user_executions':
                    emoji = "🔧" if value == 0 else "✅"
                    print(f"  {emoji} {key}: {value}")
                elif key == 'sent_to_users':
                    emoji = "📡" if value > 0 else "❌"
                    print(f"  {emoji} {key}: {value}")
                else:
                    print(f"  • {key}: {value}")
            
            print("\n🌐 PORTS:")
            for port, state in status['health'].items():
                if 'port' in port:
                    emoji = "✅" if state == "LISTENING" else "❌"
                    port_num = port.replace('port_', '')
                    print(f"  {emoji} {port_num}: {state}")
            
            print("\n💻 SYSTEM:")
            if 'memory' in status['health']:
                print(f"  📱 Memory: {status['health']['memory']}")
            if 'disk' in status['health']:
                print(f"  💾 Disk: {status['health']['disk']}")
            
            # Alert if issues
            dead_services = [s for s, state in status['services'].items() if state == 'DEAD']
            signal_issues = []
            
            if 'sent_to_users' in status['signals'] and status['signals']['sent_to_users'] == 0:
                signal_issues.append("No signals sent to users")
            if 'user_executions' in status['signals'] and status['signals']['user_executions'] == 0:
                signal_issues.append("No user executions")
            if 'delivery_rate' in status['signals'] and status['signals']['delivery_rate'] != "N/A":
                try:
                    rate = float(status['signals']['delivery_rate'].replace('%', ''))
                    if rate < 50:
                        signal_issues.append("Low delivery rate")
                except:
                    pass
            
            if dead_services:
                print(f"\n🚨 SERVICE ALERT: Dead services detected: {', '.join(dead_services)}")
                print("   Systemd should auto-restart these services...")
            
            if signal_issues:
                print(f"\n🚨 SIGNAL FLOW ALERT: {', '.join(signal_issues)}")
                print("   Check: Elite Guard → ZMQ Relay → WebApp → Telegram Bot pipeline")
            
            print(f"\n🔄 Refreshing in 30 seconds... (Ctrl+C to exit)")
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()