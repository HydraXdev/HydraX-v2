#!/usr/bin/env python3
"""
SE-1 Single-EA Monitor
Detects multiple EAs on port 5555 and suggests iptables drops
"""
import subprocess
import sys
import re
from datetime import datetime

def get_port_5555_connections():
    """Get all ESTABLISHED connections on port 5555"""
    try:
        result = subprocess.run(['ss', '-tnp'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        connections = []
        for line in lines:
            if ':5555' in line and 'ESTAB' in line:
                # Parse the connection line
                # Format: ESTAB 0 0 134.199.204.67:5555 185.244.67.11:65369 users:(("python3",pid=1085740,fd=16))
                parts = line.split()
                if len(parts) >= 5:
                    local_addr = parts[3]  # 134.199.204.67:5555
                    remote_addr = parts[4]  # 185.244.67.11:65369

                    # Extract remote IP
                    remote_ip = remote_addr.split(':')[0]
                    connections.append({
                        'local': local_addr,
                        'remote': remote_addr,
                        'remote_ip': remote_ip,
                        'full_line': line.strip()
                    })

        return connections
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to run ss command: {e}")
        return []

def generate_iptables_drops(unauthorized_ips):
    """Generate iptables DROP commands for unauthorized IPs"""
    commands = []
    for ip in unauthorized_ips:
        # Block incoming connections from this IP to port 5555
        commands.append(f"iptables -I INPUT -s {ip} -p tcp --dport 5555 -j DROP")
        # Block outgoing connections to this IP from port 5555
        commands.append(f"iptables -I OUTPUT -d {ip} -p tcp --sport 5555 -j DROP")
    return commands

def mock_mode_test():
    """Test with mock data showing multiple EAs"""
    print("=== MOCK MODE TEST ===")

    # Simulate ss output with multiple connections (1 authorized + 2 unauthorized = 3 total)
    mock_connections = [
        {
            'local': '134.199.204.67:5555',
            'remote': '185.244.67.11:65369',
            'remote_ip': '185.244.67.11',
            'full_line': 'ESTAB 0      0      134.199.204.67:5555   185.244.67.11:65369 users:(("python3",pid=1085740,fd=16))'
        },
        {
            'local': '134.199.204.67:5555',
            'remote': '192.168.1.100:54321',
            'remote_ip': '192.168.1.100',
            'full_line': 'ESTAB 0      0      134.199.204.67:5555   192.168.1.100:54321 users:(("python3",pid=1085740,fd=17))'
        },
        {
            'local': '134.199.204.67:5555',
            'remote': '10.0.0.50:43210',
            'remote_ip': '10.0.0.50',
            'full_line': 'ESTAB 0      0      134.199.204.67:5555   10.0.0.50:43210 users:(("python3",pid=1085740,fd=18))'
        }
    ]

    print(f"🚨 ALERT: Multiple EAs detected on port 5555! ({len(mock_connections)} connections)")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 Connected EAs:")

    for i, conn in enumerate(mock_connections, 1):
        print(f"  {i}. {conn['remote_ip']} → {conn['remote']}")

    # Assume first IP is authorized (the real one we saw)
    authorized_ip = '185.244.67.11'
    unauthorized_ips = [conn['remote_ip'] for conn in mock_connections if conn['remote_ip'] != authorized_ip]

    if unauthorized_ips:
        print(f"\n🔒 Suggested iptables DROP commands for unauthorized EAs:")
        drop_commands = generate_iptables_drops(unauthorized_ips)
        for cmd in drop_commands:
            print(f"  {cmd}")

    return mock_connections

def live_mode_test():
    """Test with live system data"""
    print("=== LIVE MODE TEST ===")

    connections = get_port_5555_connections()

    if len(connections) == 0:
        print("⚠️  WARNING: No EAs connected to port 5555")
        return connections
    elif len(connections) == 1:
        conn = connections[0]
        print(f"✅ HEALTHY: Single EA connected from {conn['remote_ip']} ({conn['remote']})")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return connections
    else:
        print(f"🚨 ALERT: Multiple EAs detected on port 5555! ({len(connections)} connections)")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📋 Connected EAs:")

        for i, conn in enumerate(connections, 1):
            print(f"  {i}. {conn['remote_ip']} → {conn['remote']}")

        # For this test, assume first detected IP is authorized
        authorized_ip = connections[0]['remote_ip']
        unauthorized_ips = [conn['remote_ip'] for conn in connections if conn['remote_ip'] != authorized_ip]

        if unauthorized_ips:
            print(f"\n🔒 Suggested iptables DROP commands for unauthorized EAs:")
            drop_commands = generate_iptables_drops(unauthorized_ips)
            for cmd in drop_commands:
                print(f"  {cmd}")

        return connections

def main():
    print("🔍 SE-1 Single-EA Monitor - Port 5555 Security Check")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "--mock":
        mock_mode_test()
    else:
        live_mode_test()

if __name__ == "__main__":
    main()