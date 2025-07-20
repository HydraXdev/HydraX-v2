#!/usr/bin/env python3
"""
Configure Live Fire Router - Disable Emergency Fallback for Production
CRITICAL: Ensure live trades NEVER use local simulation bridge
"""

import sys
import os
sys.path.append('/root/HydraX-v2/src/bitten_core')

from fire_router import FireRouter, TradeRequest, TradeDirection, ExecutionMode

def test_aws_agent_ports():
    """Test all possible AWS agent ports to find the active one"""
    import socket
    import requests
    
    print("🔍 Scanning AWS agent ports...")
    agent_ports = [5555, 5556, 5557]
    active_agents = []
    
    for port in agent_ports:
        try:
            # Test socket first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port}: Socket connection successful")
                
                # Test HTTP health
                try:
                    response = requests.get(f'http://localhost:{port}/health', timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        active_agents.append({
                            'port': port,
                            'agent_id': data.get('agent_id', 'Unknown'),
                            'status': data.get('status', 'Unknown'),
                            'enhanced': 'socket_running' in data
                        })
                        print(f"   ✅ Agent active: {data.get('agent_id', 'Unknown')}")
                        print(f"   Enhanced: {'Yes' if 'socket_running' in data else 'No'}")
                except Exception as e:
                    print(f"   ❌ HTTP failed: {e}")
            else:
                print(f"❌ Port {port}: No connection")
                
        except Exception as e:
            print(f"❌ Port {port}: Error - {e}")
    
    return active_agents

def create_production_fire_router(bridge_port=5555):
    """Create a production FireRouter with NO emergency fallback"""
    
    # CRITICAL: Disable emergency fallback completely for live trades
    class ProductionFireRouter(FireRouter):
        def __init__(self, bridge_host: str = "localhost", bridge_port: int = 5555):
            super().__init__(
                bridge_host=bridge_host,
                bridge_port=bridge_port,
                execution_mode=ExecutionMode.LIVE,
                emergency_bridge_host=None,  # DISABLE emergency bridge
                emergency_bridge_port=None
            )
            
            # Override emergency bridge manager to None
            self.emergency_bridge_manager = None
            print(f"🔒 PRODUCTION ROUTER: Emergency fallback DISABLED")
            print(f"🎯 Bridge: {bridge_host}:{bridge_port} (LIVE ONLY)")
        
        def _execute_emergency_fallback(self, request, payload, primary_error):
            """OVERRIDE: Never use emergency fallback in production"""
            print("🚨 CRITICAL: Primary bridge failed - REFUSING emergency fallback")
            print("🛑 Trade execution BLOCKED to prevent simulation trades")
            
            return {
                "success": False,
                "message": f"🚨 PRODUCTION SAFETY: Primary bridge failed - Trade blocked to prevent simulation",
                "error_code": "PRODUCTION_SAFETY_BLOCK",
                "primary_error": primary_error,
                "safety_message": "Emergency fallback disabled in production mode"
            }
    
    return ProductionFireRouter(bridge_port=bridge_port)

def test_production_router(bridge_port=5555):
    """Test the production router with live bridge"""
    print(f"🧪 Testing Production Router on port {bridge_port}...")
    
    try:
        # Create production router
        router = create_production_fire_router(bridge_port)
        
        # Create test trade request
        test_request = TradeRequest(
            symbol="EURUSD",
            direction=TradeDirection.BUY,
            volume=0.01,
            stop_loss=1.0800,
            take_profit=1.0950,
            comment="Production router test",
            user_id="test_user",
            mission_id="prod_test_001",
            tcs_score=85.0
        )
        
        # Execute test trade
        result = router.execute_trade_request(test_request)
        
        if result.success:
            print("✅ Production router test SUCCESSFUL")
            print(f"   Message: {result.message}")
            print(f"   Execution time: {result.execution_time_ms}ms")
            return True
        else:
            print("❌ Production router test FAILED")
            print(f"   Error: {result.message}")
            print(f"   Error code: {result.error_code}")
            return False
            
    except Exception as e:
        print(f"❌ Production router error: {e}")
        return False

def main():
    """Main configuration function"""
    print("🔒 PRODUCTION FIRE ROUTER CONFIGURATION")
    print("=" * 50)
    print("🚨 CRITICAL: Emergency fallback will be DISABLED")
    print("🎯 Only live AWS bridge will be used for trades")
    print()
    
    # Step 1: Find active AWS agents
    active_agents = test_aws_agent_ports()
    
    if not active_agents:
        print("❌ NO ACTIVE AGENTS FOUND!")
        print("Cannot configure production router without active AWS agents")
        return False
    
    print(f"\n✅ Found {len(active_agents)} active agent(s):")
    for agent in active_agents:
        print(f"   Port {agent['port']}: {agent['agent_id']} ({'Enhanced' if agent['enhanced'] else 'Standard'})")
    
    # Step 2: Test production router with each active agent
    successful_ports = []
    for agent in active_agents:
        port = agent['port']
        print(f"\n🧪 Testing production router on port {port}...")
        
        if test_production_router(port):
            successful_ports.append(port)
            print(f"✅ Port {port} - Production router working!")
        else:
            print(f"❌ Port {port} - Production router failed")
    
    # Step 3: Report results
    if successful_ports:
        print(f"\n🎉 PRODUCTION ROUTER READY!")
        print(f"✅ Working ports: {successful_ports}")
        print(f"🔒 Emergency fallback: DISABLED")
        print(f"🎯 Live trades will use: localhost:{successful_ports[0]}")
        
        # Save configuration
        config_info = f"""
# PRODUCTION FIRE ROUTER CONFIGURATION
# Generated: {__import__('datetime').datetime.now()}

LIVE_BRIDGE_HOST = "localhost"
LIVE_BRIDGE_PORT = {successful_ports[0]}
EMERGENCY_FALLBACK_DISABLED = True

# Usage:
# router = create_production_fire_router({successful_ports[0]})
"""
        
        with open('/root/HydraX-v2/PRODUCTION_ROUTER_CONFIG.py', 'w') as f:
            f.write(config_info)
        
        print(f"📝 Configuration saved to: PRODUCTION_ROUTER_CONFIG.py")
        return True
    else:
        print(f"\n❌ PRODUCTION ROUTER FAILED!")
        print("No working AWS bridge connections found")
        print("Check AWS server connectivity and agent status")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🔒 Production router configured successfully!")
        print("🚨 Emergency fallback is DISABLED for user safety")
    else:
        print("\n❌ Production router configuration failed!")
        print("Manual intervention required")