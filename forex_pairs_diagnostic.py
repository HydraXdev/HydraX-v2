#!/usr/bin/env python3
"""
🔍 FOREX PAIRS DIAGNOSTIC - Focus on Major Pairs Only
Test trade execution with US-compliant major forex pairs
"""

import sys
import os
import json
import time
import socket
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add paths
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/forex_diagnostic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ForexDiagnostic')

class ForexPairsDiagnostic:
    """Diagnostic focused on major forex pairs only"""
    
    def __init__(self):
        # US-compliant safe pairs (no metals, no exotics)
        self.SAFE_PAIRS = ["EURUSD", "USDJPY", "GBPJPY", "USDCAD", "GBPUSD", "AUDUSD"]
        self.BLOCKED_PAIRS = ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD"]  # Known problematic
        
        self.production_bridge_host = "3.145.84.187"
        self.production_bridge_port = 5555
        self.emergency_bridge_host = "127.0.0.1"
        self.emergency_bridge_port = 9000
        
        self.test_results = []
    
    def log_test(self, symbol: str, status: str, details: Dict[str, Any]):
        """Log test result with symbol tracking"""
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        
        status_symbol = "✅" if status == "SUCCESS" else "❌" if status == "FAILURE" else "⚠️"
        logger.info(f"{status_symbol} {symbol}: {status}")
        if details:
            for key, value in details.items():
                logger.info(f"    {key}: {value}")
    
    def create_safe_trade_payload(self, symbol: str) -> Dict[str, Any]:
        """Create trade payload for safe forex pairs with realistic levels"""
        
        # Define realistic pip distances for each pair
        pip_configs = {
            "EURUSD": {"pip_value": 0.0001, "sl_pips": 20, "tp_pips": 40},
            "USDJPY": {"pip_value": 0.01, "sl_pips": 20, "tp_pips": 40},
            "GBPJPY": {"pip_value": 0.01, "sl_pips": 25, "tp_pips": 50},
            "USDCAD": {"pip_value": 0.0001, "sl_pips": 20, "tp_pips": 40},
            "GBPUSD": {"pip_value": 0.0001, "sl_pips": 20, "tp_pips": 40},
            "AUDUSD": {"pip_value": 0.0001, "sl_pips": 20, "tp_pips": 40}
        }
        
        config = pip_configs.get(symbol, {"pip_value": 0.0001, "sl_pips": 20, "tp_pips": 40})
        
        # Mock current price (would be fetched from MT5 in production)
        mock_prices = {
            "EURUSD": 1.0900,
            "USDJPY": 150.00,
            "GBPJPY": 185.00,
            "USDCAD": 1.3500,
            "GBPUSD": 1.2700,
            "AUDUSD": 0.6800
        }
        
        current_price = mock_prices.get(symbol, 1.0000)
        pip_value = config["pip_value"]
        
        # Calculate SL/TP levels for BUY order
        sl_price = current_price - (config["sl_pips"] * pip_value)
        tp_price = current_price + (config["tp_pips"] * pip_value)
        
        return {
            "symbol": symbol,
            "type": "buy",
            "lot": 0.01,  # Minimum safe lot size
            "sl": round(sl_price, 5),
            "tp": round(tp_price, 5),
            "comment": f"BITTEN_FOREX_TEST {symbol}",
            "mission_id": f"FOREX_TEST_{symbol}_{int(time.time())}",
            "user_id": "7176191872",
            "timestamp": datetime.now().isoformat(),
            "price": current_price,  # For logging
            "sl_pips": config["sl_pips"],
            "tp_pips": config["tp_pips"]
        }
    
    def test_symbol_tradability(self, symbol: str) -> Dict[str, Any]:
        """Test if symbol is tradable (simulate MT5 symbol_info check)"""
        
        # Simulate symbol info check
        if symbol in self.BLOCKED_PAIRS:
            return {
                "tradable": False,
                "trade_mode": "BLOCKED",
                "reason": "US account restriction",
                "visible": True
            }
        elif symbol in self.SAFE_PAIRS:
            return {
                "tradable": True,
                "trade_mode": "TRADE_MODE_FULL",
                "reason": "Major forex pair",
                "visible": True,
                "spread": 2  # Mock spread
            }
        else:
            return {
                "tradable": False,
                "trade_mode": "UNKNOWN",
                "reason": "Untested pair",
                "visible": False
            }
    
    def send_to_bridge(self, payload: Dict[str, Any], host: str, port: int, bridge_type: str):
        """Send payload to bridge with enhanced logging"""
        symbol = payload.get("symbol", "UNKNOWN")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            # Connect
            sock.connect((host, port))
            self.log_test(symbol, "BRIDGE_CONNECTED", {
                "bridge": bridge_type,
                "host": host,
                "port": port
            })
            
            # Send payload
            message = json.dumps(payload).encode('utf-8')
            sock.send(message)
            self.log_test(symbol, "PAYLOAD_SENT", {
                "bridge": bridge_type,
                "lot_size": payload.get("lot"),
                "sl_pips": payload.get("sl_pips"),
                "tp_pips": payload.get("tp_pips")
            })
            
            # Wait for response
            try:
                sock.settimeout(8.0)  # Longer timeout for forex execution
                response = sock.recv(4096)
                if response:
                    bridge_response = json.loads(response.decode('utf-8'))
                    self.log_test(symbol, "RESPONSE_RECEIVED", {
                        "bridge": bridge_type,
                        "success": bridge_response.get("success"),
                        "retcode": bridge_response.get("retcode"),
                        "comment": bridge_response.get("comment"),
                        "trade_id": bridge_response.get("trade_id")
                    })
                    
                    # Analyze MT5 response codes
                    retcode = bridge_response.get("retcode")
                    if retcode in [10009, 10008]:  # TRADE_RETCODE_DONE, TRADE_RETCODE_PLACED
                        self.log_test(symbol, "EXECUTION_SUCCESS", {
                            "bridge": bridge_type,
                            "retcode": retcode,
                            "trade_id": bridge_response.get("trade_id")
                        })
                    elif retcode:
                        # Map common MT5 error codes
                        error_meanings = {
                            10004: "TRADE_RETCODE_REJECT - Request rejected",
                            10006: "TRADE_RETCODE_INVALID - Invalid request",
                            10013: "TRADE_RETCODE_INVALID_VOLUME - Invalid volume",
                            10014: "TRADE_RETCODE_INVALID_PRICE - Invalid price",
                            10015: "TRADE_RETCODE_INVALID_STOPS - Invalid stops",
                            10016: "TRADE_RETCODE_TRADE_DISABLED - Trade disabled",
                            10017: "TRADE_RETCODE_MARKET_CLOSED - Market closed",
                            10018: "TRADE_RETCODE_NO_MONEY - Insufficient funds",
                            10019: "TRADE_RETCODE_PRICE_CHANGED - Price changed",
                            10020: "TRADE_RETCODE_PRICE_OFF - Off quotes",
                            10027: "TRADE_RETCODE_INVALID_FILL - Invalid fill type"
                        }
                        
                        error_desc = error_meanings.get(retcode, f"Unknown error code: {retcode}")
                        self.log_test(symbol, "EXECUTION_FAILURE", {
                            "bridge": bridge_type,
                            "retcode": retcode,
                            "error": error_desc,
                            "comment": bridge_response.get("comment")
                        })
                    else:
                        self.log_test(symbol, "EXECUTION_UNKNOWN", {
                            "bridge": bridge_type,
                            "response": bridge_response
                        })
                else:
                    self.log_test(symbol, "NO_RESPONSE", {"bridge": bridge_type})
                    
            except socket.timeout:
                self.log_test(symbol, "RESPONSE_TIMEOUT", {
                    "bridge": bridge_type,
                    "timeout_seconds": 8
                })
            except Exception as e:
                self.log_test(symbol, "RESPONSE_ERROR", {
                    "bridge": bridge_type,
                    "error": str(e)
                })
            
            sock.close()
            
        except Exception as e:
            self.log_test(symbol, "CONNECTION_FAILED", {
                "bridge": bridge_type,
                "host": host,
                "port": port,
                "error": str(e)
            })
    
    def test_safe_forex_pairs(self):
        """Test all safe forex pairs"""
        logger.info("🔍 TESTING SAFE FOREX PAIRS ONLY")
        logger.info("=" * 60)
        
        for symbol in self.SAFE_PAIRS:
            logger.info(f"\n🎯 TESTING {symbol}")
            logger.info("-" * 30)
            
            # Check symbol tradability
            symbol_info = self.test_symbol_tradability(symbol)
            self.log_test(symbol, "SYMBOL_CHECK", symbol_info)
            
            if not symbol_info["tradable"]:
                self.log_test(symbol, "SKIPPED", {"reason": symbol_info["reason"]})
                continue
            
            # Create trade payload
            payload = self.create_safe_trade_payload(symbol)
            self.log_test(symbol, "PAYLOAD_CREATED", {
                "entry_price": payload["price"],
                "sl_price": payload["sl"],
                "tp_price": payload["tp"],
                "sl_pips": payload["sl_pips"],
                "tp_pips": payload["tp_pips"]
            })
            
            # Test with production bridge
            self.send_to_bridge(payload, self.production_bridge_host, self.production_bridge_port, "PRODUCTION")
            
            # Small delay between tests
            time.sleep(1)
    
    def test_blocked_pairs_detection(self):
        """Test that blocked pairs are properly detected"""
        logger.info("\n🚫 TESTING BLOCKED PAIRS DETECTION")
        logger.info("-" * 40)
        
        for symbol in self.BLOCKED_PAIRS:
            symbol_info = self.test_symbol_tradability(symbol)
            self.log_test(symbol, "BLOCKED_CHECK", symbol_info)
            
            if symbol_info["tradable"]:
                self.log_test(symbol, "WARNING", {"message": f"{symbol} should be blocked but appears tradable"})
    
    def run_forex_diagnostic(self):
        """Run complete forex pairs diagnostic"""
        start_time = time.time()
        
        logger.info("🚀 STARTING FOREX PAIRS DIAGNOSTIC")
        logger.info("Focus: US-compliant major forex pairs only")
        logger.info("=" * 60)
        
        # Test blocked pairs detection
        self.test_blocked_pairs_detection()
        
        # Test safe forex pairs
        self.test_safe_forex_pairs()
        
        # Generate summary
        end_time = time.time()
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 FOREX DIAGNOSTIC SUMMARY")
        logger.info("=" * 60)
        
        # Count results by status
        success_count = len([r for r in self.test_results if r["status"] == "EXECUTION_SUCCESS"])
        failure_count = len([r for r in self.test_results if r["status"] == "EXECUTION_FAILURE"])
        connection_failures = len([r for r in self.test_results if r["status"] == "CONNECTION_FAILED"])
        
        logger.info(f"✅ Successful executions: {success_count}")
        logger.info(f"❌ Execution failures: {failure_count}")
        logger.info(f"🔌 Connection failures: {connection_failures}")
        logger.info(f"⏱️  Total execution time: {end_time - start_time:.2f} seconds")
        
        # Show per-symbol results
        logger.info("\n📈 PER-SYMBOL RESULTS:")
        for symbol in self.SAFE_PAIRS:
            symbol_results = [r for r in self.test_results if r["symbol"] == symbol]
            execution_results = [r for r in symbol_results if "EXECUTION" in r["status"]]
            
            if execution_results:
                latest = execution_results[-1]
                status_emoji = "✅" if latest["status"] == "EXECUTION_SUCCESS" else "❌"
                logger.info(f"    {status_emoji} {symbol}: {latest['status']}")
                if latest["details"].get("retcode"):
                    logger.info(f"        RetCode: {latest['details']['retcode']}")
        
        # Save detailed results
        results_file = f"/root/HydraX-v2/forex_diagnostic_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved: {results_file}")
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "connection_failures": connection_failures,
            "total_tests": len(self.test_results),
            "execution_time": end_time - start_time,
            "results_file": results_file
        }

def main():
    """Run the forex pairs diagnostic"""
    diagnostic = ForexPairsDiagnostic()
    result = diagnostic.run_forex_diagnostic()
    
    # Exit with appropriate code
    if result["connection_failures"] > 0:
        logger.error("❌ Connection failures detected - check bridge connectivity")
        sys.exit(2)
    elif result["success_count"] == 0:
        logger.error("❌ No successful executions - check account and symbol permissions")
        sys.exit(1)
    else:
        logger.info("✅ Diagnostic completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()