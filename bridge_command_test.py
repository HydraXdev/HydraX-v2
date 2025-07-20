#!/usr/bin/env python3
"""
🔍 PRODUCTION BRIDGE COMMAND FORMAT TESTER
Test different command formats with the production bridge
"""

import socket
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BridgeCommandTest')

class BridgeCommandTester:
    """Test different command formats with production bridge"""
    
    def __init__(self):
        self.bridge_host = "localhost"
        self.bridge_port = 5555
        
    def send_command(self, command: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        """Send command to bridge and return response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # Connect
            sock.connect((self.bridge_host, self.bridge_port))
            logger.info(f"✅ Connected to {self.bridge_host}:{self.bridge_port}")
            
            # Send command
            message = json.dumps(command).encode('utf-8')
            sock.send(message)
            logger.info(f"📤 Sent: {json.dumps(command, indent=2)}")
            
            # Wait for response
            try:
                response = sock.recv(4096)
                if response:
                    response_data = json.loads(response.decode('utf-8'))
                    logger.info(f"📥 Response: {json.dumps(response_data, indent=2)}")
                    return {"success": True, "response": response_data}
                else:
                    logger.warning("⚠️ No response received")
                    return {"success": False, "error": "No response"}
                    
            except socket.timeout:
                logger.error(f"❌ Response timeout after {timeout} seconds")
                return {"success": False, "error": "Timeout"}
            
            except Exception as e:
                logger.error(f"❌ Response error: {e}")
                return {"success": False, "error": str(e)}
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            try:
                sock.close()
            except:
                pass
    
    def test_ping_command(self):
        """Test simple ping command"""
        logger.info("\n🏓 TESTING PING COMMAND")
        logger.info("-" * 30)
        
        ping_command = {"command": "ping"}
        return self.send_command(ping_command)
    
    def test_status_command(self):
        """Test status command"""
        logger.info("\n📊 TESTING STATUS COMMAND")
        logger.info("-" * 30)
        
        status_command = {"command": "status"}
        return self.send_command(status_command)
    
    def test_account_info_command(self):
        """Test account info command"""
        logger.info("\n💳 TESTING ACCOUNT INFO COMMAND")
        logger.info("-" * 30)
        
        account_command = {"command": "account_info"}
        return self.send_command(account_command)
    
    def test_symbol_info_command(self):
        """Test symbol info command"""
        logger.info("\n📈 TESTING SYMBOL INFO COMMAND")
        logger.info("-" * 30)
        
        symbol_command = {
            "command": "symbol_info",
            "symbol": "EURUSD"
        }
        return self.send_command(symbol_command)
    
    def test_fire_command_formats(self):
        """Test different fire command formats"""
        logger.info("\n🔥 TESTING FIRE COMMAND FORMATS")
        logger.info("-" * 40)
        
        # Format 1: Current BITTEN format
        format1 = {
            "symbol": "EURUSD",
            "type": "buy",
            "lot": 0.01,
            "tp": 1.094,
            "sl": 1.088,
            "comment": "BITTEN_TEST",
            "mission_id": "TEST_001",
            "user_id": "7176191872",
            "timestamp": "2025-07-17T02:50:00.000Z"
        }
        
        logger.info("🧪 Testing Format 1 (Current BITTEN):")
        result1 = self.send_command(format1)
        
        # Format 2: With fire command
        format2 = {
            "command": "fire",
            "symbol": "EURUSD",
            "type": "buy",
            "lot": 0.01,
            "tp": 1.094,
            "sl": 1.088,
            "comment": "BITTEN_TEST_CMD"
        }
        
        logger.info("\n🧪 Testing Format 2 (With fire command):")
        result2 = self.send_command(format2)
        
        # Format 3: MT5 style order_send
        format3 = {
            "command": "order_send",
            "request": {
                "action": "TRADE_ACTION_DEAL",
                "symbol": "EURUSD",
                "volume": 0.01,
                "type": "ORDER_TYPE_BUY",
                "price": 1.09,
                "sl": 1.088,
                "tp": 1.094,
                "comment": "BITTEN_MT5_STYLE",
                "type_time": "ORDER_TIME_GTC",
                "type_filling": "ORDER_FILLING_IOC"
            }
        }
        
        logger.info("\n🧪 Testing Format 3 (MT5 order_send style):")
        result3 = self.send_command(format3)
        
        # Format 4: Simple trade command
        format4 = {
            "action": "trade",
            "symbol": "EURUSD",
            "operation": "buy",
            "volume": 0.01,
            "sl": 1.088,
            "tp": 1.094
        }
        
        logger.info("\n🧪 Testing Format 4 (Simple trade):")
        result4 = self.send_command(format4)
        
        return [result1, result2, result3, result4]
    
    def test_heartbeat_check(self):
        """Test if bridge is alive with heartbeat"""
        logger.info("\n💓 TESTING HEARTBEAT/ALIVE CHECK")
        logger.info("-" * 35)
        
        heartbeat_command = {"heartbeat": True}
        return self.send_command(heartbeat_command, timeout=5)
    
    def run_comprehensive_test(self):
        """Run all bridge command tests"""
        logger.info("🔍 PRODUCTION BRIDGE COMMAND TESTING")
        logger.info("Host: localhost:5555")
        logger.info("=" * 50)
        
        results = []
        
        # Test basic connectivity commands
        results.append(("PING", self.test_ping_command()))
        results.append(("STATUS", self.test_status_command()))
        results.append(("ACCOUNT_INFO", self.test_account_info_command()))
        results.append(("SYMBOL_INFO", self.test_symbol_info_command()))
        results.append(("HEARTBEAT", self.test_heartbeat_check()))
        
        # Test fire command formats
        fire_results = self.test_fire_command_formats()
        for i, result in enumerate(fire_results, 1):
            results.append((f"FIRE_FORMAT_{i}", result))
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 COMMAND TEST SUMMARY")
        logger.info("=" * 50)
        
        success_count = 0
        for test_name, result in results:
            status = "✅" if result.get("success") else "❌"
            logger.info(f"{status} {test_name}: {'SUCCESS' if result.get('success') else 'FAILED'}")
            if result.get("success"):
                success_count += 1
            elif result.get("error"):
                logger.info(f"    Error: {result['error']}")
        
        logger.info(f"\n✅ Successful commands: {success_count}/{len(results)}")
        
        if success_count == 0:
            logger.error("❌ CRITICAL: Bridge not responding to ANY commands")
            logger.error("   Bridge may be:")
            logger.error("   - Running different protocol")
            logger.error("   - Expecting authentication")
            logger.error("   - Using binary protocol instead of JSON")
            logger.error("   - Crashed/stuck but port still open")
        
        return results

def main():
    """Run bridge command testing"""
    tester = BridgeCommandTester()
    results = tester.run_comprehensive_test()
    
    # Exit with status based on results
    success_count = sum(1 for _, result in results if result.get("success"))
    if success_count == 0:
        exit(1)  # Complete failure
    elif success_count < len(results) // 2:
        exit(2)  # Partial failure
    else:
        exit(0)  # Success

if __name__ == "__main__":
    main()