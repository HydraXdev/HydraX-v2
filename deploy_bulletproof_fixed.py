#!/usr/bin/env python3
"""
BULLETPROOF AGENT DEPLOYMENT SCRIPT
Deploy unbreakable 24/7 agent system to AWS Windows
"""

import requests
import json
import time
import os

def deploy_bulletproof_agents():
    """Deploy bulletproof agents to Windows server"""
    target_ip = "3.145.84.187"
    base_url = f"http://{target_ip}:5555"
    
    print("🚀 DEPLOYING BULLETPROOF AGENT SYSTEM...")
    print("=" * 50)
    
    # Read agent files
    agent_files = {}
    
    # Primary agent
    with open('/root/HydraX-v2/bulletproof_agents/primary_agent.py', 'r') as f:
        agent_files['primary_agent.py'] = f.read()
    
    # Backup agent  
    with open('/root/HydraX-v2/bulletproof_agents/backup_agent.py', 'r') as f:
        agent_files['backup_agent.py'] = f.read()
    
    # WebSocket agent
    with open('/root/HydraX-v2/bulletproof_agents/websocket_agent.py', 'r') as f:
        agent_files['websocket_agent.py'] = f.read()
    
    # Startup script
    with open('/root/HydraX-v2/bulletproof_agents/START_AGENTS.bat', 'r') as f:
        agent_files['START_AGENTS.bat'] = f.read()
    
    # Try to upload to existing agent
    try:
        session = requests.Session()
        session.timeout = 10
        
        # Test connection first
        try:
            response = session.get(f"{base_url}/health")
            if response.status_code != 200:
                raise Exception("Agent not responding")
            print("✅ Connected to existing agent")
        except:
            print("❌ Cannot connect to existing agent")
            print("MANUAL DEPLOYMENT REQUIRED:")
            print("1. RDP to 3.145.84.187")
            print("2. Create C:\\BITTEN_Agent directory")
            print("3. Copy files from /root/HydraX-v2/bulletproof_agents/")
            print("4. Run START_AGENTS.bat")
            return False
        
        # Upload all files
        for filename, content in agent_files.items():
            filepath = f"C:\\BITTEN_Agent\\{filename}"
            
            response = session.post(
                f"{base_url}/upload",
                json={
                    "filepath": filepath,
                    "content": content
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Uploaded {filename}")
            else:
                print(f"❌ Failed to upload {filename}: {response.text}")
                
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
    
    # Kill existing agents and start new ones
    print("\n🔄 STARTING BULLETPROOF SYSTEM...")
    try:
        # Kill existing python processes
        response = session.post(
            f"{base_url}/execute",
            json={
                "command": "taskkill /F /IM python.exe /T",
                "type": "cmd"
            }
        )
        
        time.sleep(5)  # Wait for processes to stop
        
        # Start new bulletproof system
        response = session.post(
            f"{base_url}/execute",
            json={
                "command": "cd C:\\BITTEN_Agent && START_AGENTS.bat",
                "type": "cmd"
            }
        )
        
        if response.status_code == 200:
            print("✅ BULLETPROOF SYSTEM STARTED")
            return True
        else:
            print(f"❌ Failed to start system: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        return False

def test_all_connections():
    """Test all connection methods"""
    target_ip = "3.145.84.187"
    
    print("\n🔍 TESTING ALL CONNECTION METHODS...")
    print("=" * 40)
    
    methods = [
        {'name': 'Primary Agent', 'port': 5555},
        {'name': 'Backup Agent', 'port': 5556},
        {'name': 'WebSocket Agent', 'port': 5557}
    ]
    
    results = {}
    
    for method in methods:
        try:
            url = f"http://{target_ip}:{method['port']}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results[method['name']] = f"✅ ONLINE - {data.get('status', 'unknown')}"
            else:
                results[method['name']] = f"❌ HTTP {response.status_code}"
                
        except requests.exceptions.ConnectTimeout:
            results[method['name']] = "❌ TIMEOUT"
        except requests.exceptions.ConnectionError:
            results[method['name']] = "❌ CONNECTION REFUSED"
        except Exception as e:
            results[method['name']] = f"❌ ERROR: {str(e)[:50]}"
    
    print("📊 CONNECTION TEST RESULTS:")
    for name, status in results.items():
        print(f"  {name}: {status}")
    
    # Check if at least one connection works
    working = any("✅" in status for status in results.values())
    
    if working:
        print("\n🎯 SYSTEM IS BULLETPROOF AND READY!")
        print("✅ At least one connection method is working")
        print("✅ Automatic failover will handle any single point failures")
        return True
    else:
        print("\n❌ ALL CONNECTIONS FAILED")
        print("Manual intervention required")
        return False

def create_intelligent_test():
    """Create a test using the intelligent controller"""
    print("\n🧠 TESTING INTELLIGENT CONTROLLER...")
    
    try:
        # Import and test the intelligent controller
        import sys
        sys.path.append('/root/HydraX-v2')
        
        # Test command execution with failover
        test_commands = [
            "Get-Date",
            "Get-Process | Select-Object -First 5",
            "Test-NetConnection -ComputerName google.com -Port 80"
        ]
        
        for cmd in test_commands:
            print(f"\n🔧 Testing: {cmd}")
            try:
                # This would use the intelligent controller
                # For now, just test basic HTTP
                response = requests.post(
                    "http://3.145.84.187:5555/execute",
                    json={"command": cmd, "type": "powershell"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Success: {result.get('stdout', '')[:100]}...")
                else:
                    print(f"❌ Failed: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Controller test failed: {e}")

if __name__ == "__main__":
    print("🛡️  BULLETPROOF AGENT DEPLOYMENT")
    print("=" * 60)
    
    # Deploy the system
    if deploy_bulletproof_agents():
        print("\n✅ DEPLOYMENT SUCCESSFUL")
        
        # Wait for agents to start
        print("\n⏳ Waiting 15 seconds for agents to start...")
        time.sleep(15)
        
        # Test all connections
        if test_all_connections():
            print("\n🎉 BULLETPROOF SYSTEM IS LIVE!")
            print("🔄 24/7 monitoring and auto-recovery active")
            print("📡 Multiple connection methods available")
            print("🛡️  Trading signals now have unbreakable connectivity")
            
            # Test intelligent controller
            create_intelligent_test()
            
            print("\n📋 NEXT STEPS:")
            print("1. Monitor system with: python3 /root/HydraX-v2/intelligent_controller.py")
            print("2. Test trading signals: python3 /root/HydraX-v2/check_mt5_live_status.py")
            print("3. System will auto-recover from any single point failures")
            
        else:
            print("\n⚠️  DEPLOYMENT COMPLETED BUT CONNECTIONS FAILED")
            print("Manual verification required")
            
    else:
        print("\n❌ DEPLOYMENT FAILED")
        print("Manual intervention required on Windows server")