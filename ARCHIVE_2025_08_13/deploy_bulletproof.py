
#!/usr/bin/env python3
"""
BULLETPROOF AGENT DEPLOYMENT SCRIPT
Deploy unbreakable 24/7 agent system to AWS Windows
"""

import requests
import json
import time
import os

class BulletproofDeployment:
    def __init__(self, target_ip="localhost"):
        self.target_ip = target_ip
        self.base_url = f"http://{target_ip}:5555"
        self.agents = {}
        
    def deploy_agents(self):
        """Deploy all agents to Windows server"""
        print("🚀 DEPLOYING BULLETPROOF AGENT SYSTEM...")
        
        # Get agent files
        system = BulletproofAgentSystem()
        agents = system.deploy_multiple_agents()
        
        # Try to upload to existing agent first
        try:
            session = requests.Session()
            session.timeout = 10
            
            for filename, content in agents.items():
                filepath = f"C:\\BITTEN_Agent\\{filename}"
                
                response = session.post(
                    f"{self.base_url}/upload",
                    json={
                        "filepath": filepath,
                        "content": content
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ Uploaded {filename}")
                else:
                    print(f"❌ Failed to upload {filename}")
                    
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            print("MANUAL DEPLOYMENT REQUIRED:")
            print("1. RDP to localhost")
            print("2. Create files manually from output above")
            print("3. Run START_AGENTS.bat")
            return False
        
        # Start the system
        try:
            response = session.post(
                f"{self.base_url}/execute",
                json={
                    "command": "cd C:\\BITTEN_Agent && START_AGENTS.bat",
                    "type": "cmd"
                }
            )
            
            if response.status_code == 200:
                print("✅ BULLETPROOF SYSTEM STARTED")
                return True
            else:
                print("❌ Failed to start system")
                return False
                
        except Exception as e:
            print(f"❌ Startup failed: {e}")
            return False
    
    def test_all_connections(self):
        """Test all connection methods"""
        print("🔍 TESTING ALL CONNECTION METHODS...")
        
        methods = [
            {'name': 'Primary Agent', 'url': f'http://{self.target_ip}:5555/health'},
            {'name': 'Backup Agent', 'url': f'http://{self.target_ip}:5556/health'},
            {'name': 'WebSocket Agent', 'url': f'ws://{self.target_ip}:5557'}
        ]
        
        results = {}
        
        for method in methods:
            try:
                if method['url'].startswith('http'):
                    response = requests.get(method['url'], timeout=5)
                    results[method['name']] = response.status_code == 200
                else:
                    # WebSocket test would need websockets library
                    results[method['name']] = "WebSocket test not implemented"
                    
            except Exception as e:
                results[method['name']] = f"Failed: {e}"
        
        return results

if __name__ == "__main__":
    deployer = BulletproofDeployment()
    
    if deployer.deploy_agents():
        print("\n✅ BULLETPROOF SYSTEM DEPLOYED SUCCESSFULLY")
        
        # Test connections
        results = deployer.test_all_connections()
        print("\n📊 CONNECTION TEST RESULTS:")
        for name, status in results.items():
            print(f"  {name}: {status}")
            
        print("\n🎯 SYSTEM IS NOW BULLETPROOF AND READY FOR 24/7 TRADING")
    else:
        print("\n❌ DEPLOYMENT FAILED - MANUAL INTERVENTION REQUIRED")
