#!/usr/bin/env python3
"""
Test MT5 Socket Bridge Functionality
Tests both ping and fire commands to verify the enhanced bridge is working
"""

import socket
import json
import time
from datetime import datetime

class MT5SocketTester:
    def __init__(self, host="3.145.84.187", port=9000):
        self.host = host
        self.port = port
        
    def send_command(self, command_data: dict, timeout=10):
        """Send command to MT5 socket bridge"""
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # Connect to bridge
            sock.connect((self.host, self.port))
            
            # Send command
            message = json.dumps(command_data)
            sock.send(message.encode('utf-8'))
            
            # Receive response
            response = sock.recv(4096)
            result = json.loads(response.decode('utf-8'))
            
            sock.close()
            return result
            
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return None
    
    def test_ping(self):
        """Test ping command"""
        print("🏓 Testing PING command...")
        
        ping_command = {"command": "ping"}
        result = self.send_command(ping_command)
        
        if result:
            print(f"✅ PING successful!")
            print(f"   Status: {result.get('status', 'Unknown')}")
            print(f"   Account: {result.get('account', 'N/A')}")
            print(f"   Broker: {result.get('broker', 'N/A')}")
            print(f"   Balance: {result.get('balance', 'N/A')}")
            print(f"   Symbols: {len(result.get('symbols', []))} available")
            return True
        else:
            print("❌ PING failed")
            return False
    
    def test_fire(self):
        """Test fire command"""
        print("🔥 Testing FIRE command...")
        
        fire_command = {
            "command": "fire",
            "symbol": "EURUSD",
            "type": "buy",
            "lot": 0.01,
            "sl": 1.0800,
            "tp": 1.0950,
            "comment": "Test fire from socket"
        }
        
        result = self.send_command(fire_command)
        
        if result:
            print(f"✅ FIRE successful!")
            print(f"   Retcode: {result.get('retcode', 'Unknown')}")
            print(f"   Ticket: {result.get('ticket', 'N/A')}")
            print(f"   Symbol: {result.get('symbol', 'N/A')}")
            print(f"   Volume: {result.get('volume', 'N/A')}")
            print(f"   Price: {result.get('price', 'N/A')}")
            
            # Check if successful
            if result.get('retcode') == 10009:  # TRADE_RETCODE_DONE
                print("🎯 Trade executed successfully!")
                return True
            else:
                print(f"⚠️ Trade result: {result.get('comment', 'No comment')}")
                return False
        else:
            print("❌ FIRE failed")
            return False
    
    def test_fire_router_compatibility(self):
        """Test compatibility with existing FireRouter"""
        print("🔗 Testing FireRouter compatibility...")
        
        try:
            # Import and test FireRouter
            import sys
            sys.path.append('/root/HydraX-v2/src/bitten_core')
            from fire_router import FireRouter, TradeRequest, TradeDirection
            
            # Create FireRouter instance
            router = FireRouter(
                bridge_host=self.host,
                bridge_port=self.port
            )
            
            # Create test trade request
            trade_request = TradeRequest(
                symbol="EURUSD",
                direction=TradeDirection.BUY,
                volume=0.01,
                stop_loss=1.0800,
                take_profit=1.0950,
                comment="FireRouter compatibility test",
                user_id="test_user",
                mission_id="test_mission_001",
                tcs_score=85.0
            )
            
            # Execute trade
            result = router.execute_trade_request(trade_request)
            
            if result.success:
                print("✅ FireRouter compatibility successful!")
                print(f"   Message: {result.message}")
                print(f"   Ticket: {result.ticket}")
                print(f"   Execution time: {result.execution_time_ms}ms")
                return True
            else:
                print(f"❌ FireRouter test failed: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ FireRouter compatibility error: {e}")
            return False
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🧪 MT5 SOCKET BRIDGE TEST SUITE")
        print("=" * 40)
        print(f"Target: {self.host}:{self.port}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Ping
        if self.test_ping():
            tests_passed += 1
        print()
        
        # Test 2: Fire
        if self.test_fire():
            tests_passed += 1
        print()
        
        # Test 3: FireRouter compatibility
        if self.test_fire_router_compatibility():
            tests_passed += 1
        print()
        
        # Summary
        print("📊 TEST RESULTS")
        print("=" * 20)
        print(f"✅ Passed: {tests_passed}/{total_tests}")
        print(f"❌ Failed: {total_tests - tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("The MT5 socket bridge is fully functional")
        else:
            print(f"\n⚠️ {total_tests - tests_passed} TESTS FAILED")
            print("Check the bridge configuration and try again")
        
        return tests_passed == total_tests

def main():
    """Main test function"""
    tester = MT5SocketTester()
    
    print("🎯 MT5 Socket Bridge Test Tool")
    print("=" * 30)
    
    # Run the full test suite
    success = tester.run_full_test_suite()
    
    if success:
        print("\n✅ Bridge is ready for production use!")
    else:
        print("\n❌ Bridge needs attention before production use")

if __name__ == "__main__":
    main()