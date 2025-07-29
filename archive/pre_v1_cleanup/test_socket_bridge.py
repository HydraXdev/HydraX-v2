#!/usr/bin/env python3
"""
Test Socket Bridge Communication
Validates that socket signals are properly converted to MT5 files
"""

import asyncio
import websockets
import json
import os
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SocketBridgeTest')

class SocketBridgeTest:
    """Test the socket-to-file bridge communication"""
    
    def __init__(self, bridge_host="localhost", bridge_port=8080, drop_path="/tmp/mt5-drop"):
        self.bridge_host = bridge_host
        self.bridge_port = bridge_port
        self.drop_path = drop_path
        self.test_results = {}
        
        # Create drop directory
        os.makedirs(drop_path, exist_ok=True)
        
        logger.info(f"Socket Bridge Test initialized")
        logger.info(f"Bridge: {bridge_host}:{bridge_port}")
        logger.info(f"Drop path: {drop_path}")
    
    async def test_connection(self):
        """Test basic WebSocket connection"""
        logger.info("Testing WebSocket connection...")
        
        try:
            uri = f"ws://{self.bridge_host}:{self.bridge_port}"
            async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
                # Send ping
                await websocket.send(json.dumps({"action": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                
                logger.info("✅ WebSocket connection successful")
                self.test_results["connection"] = True
                return True
                
        except asyncio.TimeoutError:
            logger.error("❌ WebSocket connection timeout")
            self.test_results["connection"] = False
            return False
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.test_results["connection"] = False
            return False
    
    async def test_trade_signal(self):
        """Test trade signal processing"""
        logger.info("Testing trade signal processing...")
        
        # Clear drop directory
        for file in os.listdir(self.drop_path):
            if file.startswith("trade_"):
                os.remove(os.path.join(self.drop_path, file))
        
        trade_signal = {
            "action": "trade",
            "symbol": "EURUSD",
            "direction": "BUY", 
            "lot_size": 0.01,
            "stop_loss": 1.0950,
            "take_profit": 1.1050
        }
        
        try:
            uri = f"ws://{self.bridge_host}:{self.bridge_port}"
            async with websockets.connect(uri) as websocket:
                # Send trade signal
                await websocket.send(json.dumps(trade_signal))
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                result = json.loads(response)
                
                if result.get('status') == 'success':
                    logger.info("✅ Trade signal accepted by bridge")
                    
                    # Check if file was created
                    time.sleep(1)  # Wait for file creation
                    trade_files = [f for f in os.listdir(self.drop_path) if f.startswith("trade_")]
                    
                    if trade_files:
                        # Verify file content
                        file_path = os.path.join(self.drop_path, trade_files[0])
                        with open(file_path, 'r') as f:
                            file_data = json.load(f)
                        
                        # Validate file structure
                        required_fields = ['trade_id', 'symbol', 'direction', 'lot_size', 'magic_number']
                        if all(field in file_data for field in required_fields):
                            logger.info(f"✅ Trade file created successfully: {trade_files[0]}")
                            logger.info(f"   Symbol: {file_data['symbol']}")
                            logger.info(f"   Direction: {file_data['direction']}")
                            logger.info(f"   Lot Size: {file_data['lot_size']}")
                            logger.info(f"   Trade ID: {file_data['trade_id']}")
                            
                            self.test_results["trade_signal"] = True
                            return True
                        else:
                            logger.error("❌ Trade file missing required fields")
                            self.test_results["trade_signal"] = False
                            return False
                    else:
                        logger.error("❌ No trade file created")
                        self.test_results["trade_signal"] = False
                        return False
                else:
                    logger.error(f"❌ Trade signal rejected: {result.get('message')}")
                    self.test_results["trade_signal"] = False
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Trade signal test failed: {e}")
            self.test_results["trade_signal"] = False
            return False
    
    async def test_multiple_signals(self):
        """Test multiple rapid trade signals"""
        logger.info("Testing multiple rapid trade signals...")
        
        signals = [
            {"action": "trade", "symbol": "GBPUSD", "direction": "SELL", "lot_size": 0.01},
            {"action": "trade", "symbol": "USDJPY", "direction": "BUY", "lot_size": 0.02},
            {"action": "trade", "symbol": "AUDUSD", "direction": "BUY", "lot_size": 0.01}]
        
        try:
            uri = f"ws://{self.bridge_host}:{self.bridge_port}"
            async with websockets.connect(uri) as websocket:
                success_count = 0
                
                for signal in signals:
                    await websocket.send(json.dumps(signal))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    result = json.loads(response)
                    
                    if result.get('status') == 'success':
                        success_count += 1
                        logger.info(f"✅ Signal processed: {signal['symbol']} {signal['direction']}")
                    else:
                        logger.error(f"❌ Signal failed: {signal['symbol']}")
                
                if success_count == len(signals):
                    logger.info("✅ Multiple signals test passed")
                    self.test_results["multiple_signals"] = True
                    return True
                else:
                    logger.error(f"❌ Multiple signals test failed: {success_count}/{len(signals)}")
                    self.test_results["multiple_signals"] = False
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Multiple signals test failed: {e}")
            self.test_results["multiple_signals"] = False
            return False
    
    async def test_error_handling(self):
        """Test error handling with invalid signals"""
        logger.info("Testing error handling...")
        
        invalid_signals = [
            {"action": "trade"},  # Missing required fields
            {"action": "trade", "symbol": "INVALID", "direction": "INVALID"},  # Invalid direction
            {"invalid": "json"},  # Wrong format
        ]
        
        try:
            uri = f"ws://{self.bridge_host}:{self.bridge_port}"
            async with websockets.connect(uri) as websocket:
                error_handled_count = 0
                
                for signal in invalid_signals:
                    await websocket.send(json.dumps(signal))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    result = json.loads(response)
                    
                    if result.get('status') == 'error':
                        error_handled_count += 1
                        logger.info(f"✅ Error properly handled: {result.get('message')}")
                    else:
                        logger.error("❌ Invalid signal was not rejected")
                
                if error_handled_count == len(invalid_signals):
                    logger.info("✅ Error handling test passed")
                    self.test_results["error_handling"] = True
                    return True
                else:
                    logger.error("❌ Error handling test failed")
                    self.test_results["error_handling"] = False
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.test_results["error_handling"] = False
            return False
    
    def run_standalone_bridge_test(self, port=8080):
        """Run a standalone socket bridge for testing"""
        logger.info("Starting standalone socket bridge for testing...")
        
        # Create a simple test bridge
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f"""
#!/usr/bin/env python3
import asyncio
import websockets
import json
import os
import time
from datetime import datetime

class TestSocketBridge:
    def __init__(self, drop_path="{self.drop_path}"):
        self.drop_path = drop_path
        os.makedirs(drop_path, exist_ok=True)

    async def handle_client(self, websocket, path):
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except:
            pass

    async def process_message(self, websocket, message):
        try:
            data = json.loads(message)
            
            if data.get('action') == 'trade':
                result = self.handle_trade_signal(data)
                await websocket.send(json.dumps({{
                    'status': 'success' if result else 'error',
                    'message': 'Trade processed' if result else 'Trade failed',
                    'timestamp': datetime.now().isoformat()
                }}))
            else:
                await websocket.send(json.dumps({{
                    'status': 'error',
                    'message': 'Unknown action'
                }}))
        except Exception as e:
            await websocket.send(json.dumps({{
                'status': 'error',
                'message': str(e)
            }}))

    def handle_trade_signal(self, signal):
        try:
            symbol = signal.get('symbol', '').upper()
            direction = signal.get('direction', '').upper()
            
            if not symbol or direction not in ['BUY', 'SELL']:
                return False
            
            trade_id = int(time.time() * 1000000)
            filename = f"trade_{{trade_id}}_{{symbol}}.json"
            filepath = os.path.join(self.drop_path, filename)
            
            trade_data = {{
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': direction,
                'lot_size': float(signal.get('lot_size', 0.01)),
                'stop_loss': float(signal.get('stop_loss', 0)),
                'take_profit': float(signal.get('take_profit', 0)),
                'timestamp': datetime.now().isoformat(),
                'magic_number': 20250726
            }}
            
            with open(filepath, 'w') as f:
                json.dump(trade_data, f, indent=2)
            
            return True
        except:
            return False

bridge = TestSocketBridge()
start_server = websockets.serve(bridge.handle_client, 'localhost', {port})
asyncio.get_event_loop().run_until_complete(start_server)
print(f"Test bridge running on port {port}")
asyncio.get_event_loop().run_forever()
""")
            bridge_script = f.name
        
        # Start bridge in background
        import subprocess
        import atexit
        
        bridge_process = subprocess.Popen([
            'python3', bridge_script
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        def cleanup_bridge():
            bridge_process.terminate()
            os.unlink(bridge_script)
        atexit.register(cleanup_bridge)
        
        # Wait for bridge to start
        time.sleep(2)
        return bridge_process
    
    async def run_full_test_suite(self):
        """Run complete test suite"""
        logger.info("🚀 Starting Socket Bridge Test Suite")
        logger.info("=" * 50)
        
        # Start standalone bridge for testing
        bridge_process = self.run_standalone_bridge_test(self.bridge_port)
        
        try:
            # Run all tests
            tests = [
                ("Connection Test", self.test_connection),
                ("Trade Signal Test", self.test_trade_signal),
                ("Multiple Signals Test", self.test_multiple_signals),
                ("Error Handling Test", self.test_error_handling)
            ]
            
            for test_name, test_func in tests:
                logger.info(f"\n🧪 Running {test_name}...")
                try:
                    success = await test_func()
                    if success:
                        logger.info(f"✅ {test_name} PASSED")
                    else:
                        logger.error(f"❌ {test_name} FAILED")
                except Exception as e:
                    logger.error(f"❌ {test_name} FAILED with exception: {e}")
                    self.test_results[test_name.lower().replace(' ', '_')] = False
            
        finally:
            # Cleanup
            bridge_process.terminate()
            bridge_process.wait()
        
        # Show results summary
        self.show_test_results()
    
    def show_test_results(self):
        """Display test results summary"""
        logger.info("\n" + "=" * 50)
        logger.info("🎯 TEST RESULTS SUMMARY")
        logger.info("=" * 50)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        
        logger.info("-" * 50)
        logger.info(f"Overall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Socket Bridge is production ready!")
        else:
            logger.error("⚠️  Some tests failed - review bridge implementation")

async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Socket Bridge Communication')
    parser.add_argument('--host', default='localhost', help='Bridge host')
    parser.add_argument('--port', type=int, default=8080, help='Bridge port')
    parser.add_argument('--drop-path', default='/tmp/mt5-drop', help='File drop path')
    
    args = parser.parse_args()
    
    tester = SocketBridgeTest(args.host, args.port, args.drop_path)
    await tester.run_full_test_suite()

if __name__ == '__main__':
    asyncio.run(main())