#!/usr/bin/env python3
"""
Monitor ZMQ System Status
Shows real-time stats for the migration
"""

import time
import os
from zmq_migration_helpers import check_migration_status

def monitor_system():
    """Monitor ZMQ system status"""
    print("📊 ZMQ System Monitor")
    print("="*50)
    print(f"USE_ZMQ: {os.getenv('USE_ZMQ', 'false')}")
    print(f"ZMQ_DUAL_WRITE: {os.getenv('ZMQ_DUAL_WRITE', 'false')}")
    print("="*50)
    
    while True:
        try:
            # Get migration status
            status = check_migration_status()
            
            # Clear screen and show header
            print("\033[H\033[J")  # Clear screen
            print("📊 ZMQ System Monitor - Real-time Status")
            print("="*50)
            
            # Show configuration
            print(f"🔧 Configuration:")
            print(f"   Migration Mode: {status['mode']}")
            print(f"   ZMQ Available: {status['zmq_available']}")
            print(f"   ZMQ Status: {status['zmq_status']}")
            
            # Show stats
            stats = status['stats']
            print(f"\n📈 Execution Statistics:")
            print(f"   Fire.txt writes: {stats['fire_txt_writes']}")
            print(f"   ZMQ writes: {stats['zmq_writes']}")
            print(f"   Dual writes: {stats['dual_writes']}")
            print(f"   Failures: {stats['failures']}")
            print(f"   Total executions: {stats['total_executions']}")
            if stats['total_executions'] > 0:
                print(f"   ZMQ percentage: {stats['zmq_percentage']:.1f}%")
            
            # Check running processes
            print(f"\n🔄 Running Processes:")
            
            # Check fire publisher
            fire_pub_status = os.system("pgrep -f zmq_fire_publisher_daemon > /dev/null") == 0
            print(f"   Fire Publisher: {'✅ Running' if fire_pub_status else '❌ Not running'}")
            
            # Check telemetry service
            telemetry_status = os.system("pgrep -f zmq_telemetry_daemon > /dev/null") == 0
            print(f"   Telemetry Service: {'✅ Running' if telemetry_status else '❌ Not running'}")
            
            # Show recent logs
            print(f"\n📝 Recent Activity:")
            try:
                with open('zmq_fire_publisher.log', 'r') as f:
                    lines = f.readlines()
                    recent = [l.strip() for l in lines[-5:]]
                    for line in recent:
                        if 'Stats:' in line:
                            print(f"   {line.split('INFO - ')[-1]}")
            except:
                print("   No recent activity")
            
            print(f"\n⏰ Last update: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("Press Ctrl+C to exit")
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Set environment variables if not set
    if not os.getenv('USE_ZMQ'):
        os.environ['USE_ZMQ'] = 'true'
        os.environ['ZMQ_DUAL_WRITE'] = 'true'
    
    monitor_system()