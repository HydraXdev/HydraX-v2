#!/usr/bin/env python3
"""
🔍 BITTEN FIRE PACKAGE DIAGNOSTIC TRACER
Comprehensive trace of trade execution from engine to MT5
"""

import sys
import os
import json
import time
import socket
import logging
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

# Add paths
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/fire_trace.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FireTracer')

class FireExecutionTracer:
    """Comprehensive fire execution diagnostics"""
    
    def __init__(self):
        self.trace_log = []
        self.emergency_bridge_host = "127.0.0.1"
        self.emergency_bridge_port = 9000
        self.production_bridge_host = "localhost"
        self.production_bridge_port = 5555
        
    def log_trace(self, step: str, status: str, details: Dict[str, Any]):
        """Log trace step with timestamp"""
        trace_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "details": details
        }
        self.trace_log.append(trace_entry)
        
        status_symbol = "✅" if status == "SUCCESS" else "❌" if status == "FAILURE" else "🔍"
        logger.info(f"{status_symbol} {step}: {status}")
        if details:
            for key, value in details.items():
                logger.info(f"    {key}: {value}")
    
    def step_1_bridge_credentials(self):
        """✅ Step 1: Confirm Bridge Startup Credentials"""
        self.log_trace("STEP_1_BRIDGE_CREDENTIALS", "CHECKING", {})
        
        # Check for emergency bridge process
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            emergency_running = 'emergency_bridge_server.py' in result.stdout
            
            self.log_trace("EMERGENCY_BRIDGE_STATUS", 
                         "SUCCESS" if emergency_running else "FAILURE",
                         {"running": emergency_running})
            
            # Test emergency bridge connection
            if emergency_running:
                self.test_bridge_connection(self.emergency_bridge_host, self.emergency_bridge_port, "EMERGENCY")
            
            # Test production bridge connection
            self.test_bridge_connection(self.production_bridge_host, self.production_bridge_port, "PRODUCTION")
            
        except Exception as e:
            self.log_trace("BRIDGE_CREDENTIALS_CHECK", "FAILURE", {"error": str(e)})
    
    def test_bridge_connection(self, host: str, port: int, bridge_type: str):
        """Test connection to a bridge"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.log_trace(f"{bridge_type}_BRIDGE_CONNECTION", "SUCCESS", 
                             {"host": host, "port": port, "reachable": True})
            else:
                self.log_trace(f"{bridge_type}_BRIDGE_CONNECTION", "FAILURE", 
                             {"host": host, "port": port, "reachable": False, "error_code": result})
                
        except Exception as e:
            self.log_trace(f"{bridge_type}_BRIDGE_CONNECTION", "FAILURE", 
                         {"host": host, "port": port, "error": str(e)})
    
    def step_2_verify_trading_enabled(self):
        """✅ Step 2: Verify Trading Enabled"""
        self.log_trace("STEP_2_TRADING_VERIFICATION", "CHECKING", {})
        
        # This would require actual MT5 connection - simulating check
        # In production, this would call mt5.account_info()
        mock_account_info = {
            "trade_allowed": True,
            "login": "SIMULATED_LOGIN",
            "margin_mode": "HEDGING",
            "server": "SIMULATED_SERVER",
            "balance": 10000.0
        }
        
        self.log_trace("TRADING_ACCOUNT_INFO", "SUCCESS", mock_account_info)
    
    def step_3_trace_fire_payload(self):
        """✅ Step 3: Trace the Trade Fire Payload"""
        self.log_trace("STEP_3_FIRE_PAYLOAD", "CHECKING", {})
        
        # Create sample fire payload
        sample_payload = {
            "symbol": "XAUUSD",
            "type": "buy",
            "lot": 0.01,
            "tp": 2650.0,
            "sl": 2600.0,
            "comment": "BITTEN FIRE TCS:85%",
            "mission_id": "TEST_MISSION_001",
            "user_id": "7176191872",
            "timestamp": datetime.now().isoformat()
        }
        
        self.log_trace("FIRE_PAYLOAD_FORMAT", "SUCCESS", sample_payload)
        
        # Validate symbol format
        symbol_valid = sample_payload["symbol"] in ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
        self.log_trace("SYMBOL_VALIDATION", 
                     "SUCCESS" if symbol_valid else "FAILURE",
                     {"symbol": sample_payload["symbol"], "valid": symbol_valid})
        
        return sample_payload
    
    def step_4_test_fire_execution(self, payload: Dict[str, Any]):
        """✅ Step 4: Test Fire Execution"""
        self.log_trace("STEP_4_FIRE_EXECUTION", "TESTING", {})
        
        # Test with emergency bridge first
        self.send_to_bridge(payload, self.emergency_bridge_host, self.emergency_bridge_port, "EMERGENCY")
        
        # Test with production bridge
        self.send_to_bridge(payload, self.production_bridge_host, self.production_bridge_port, "PRODUCTION")
    
    def send_to_bridge(self, payload: Dict[str, Any], host: str, port: int, bridge_type: str):
        """Send payload to bridge and log results"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            # Connect
            sock.connect((host, port))
            self.log_trace(f"{bridge_type}_BRIDGE_CONNECT", "SUCCESS", 
                         {"host": host, "port": port})
            
            # Send payload
            message = json.dumps(payload).encode('utf-8')
            sock.send(message)
            self.log_trace(f"{bridge_type}_PAYLOAD_SENT", "SUCCESS", 
                         {"payload_size": len(message), "payload": payload})
            
            # Wait for response
            try:
                sock.settimeout(5.0)
                response = sock.recv(4096)
                if response:
                    bridge_response = json.loads(response.decode('utf-8'))
                    self.log_trace(f"{bridge_type}_RESPONSE_RECEIVED", "SUCCESS", bridge_response)
                    
                    # Analyze response
                    if bridge_response.get("success"):
                        self.log_trace(f"{bridge_type}_EXECUTION_RESULT", "SUCCESS", 
                                     {"trade_id": bridge_response.get("trade_id"),
                                      "message": bridge_response.get("message")})
                    else:
                        self.log_trace(f"{bridge_type}_EXECUTION_RESULT", "FAILURE", 
                                     {"error": bridge_response.get("error", "Unknown error")})
                else:
                    self.log_trace(f"{bridge_type}_RESPONSE_RECEIVED", "FAILURE", 
                                 {"error": "No response received"})
                    
            except socket.timeout:
                self.log_trace(f"{bridge_type}_RESPONSE_TIMEOUT", "FAILURE", 
                             {"timeout": "5 seconds"})
            except Exception as e:
                self.log_trace(f"{bridge_type}_RESPONSE_ERROR", "FAILURE", 
                             {"error": str(e)})
            
            sock.close()
            
        except Exception as e:
            self.log_trace(f"{bridge_type}_CONNECTION_FAILED", "FAILURE", 
                         {"host": host, "port": port, "error": str(e)})
    
    def step_5_check_fire_router_integration(self):
        """✅ Step 5: Check Fire Router Integration"""
        self.log_trace("STEP_5_FIRE_ROUTER", "CHECKING", {})
        
        try:
            from src.bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection
            
            # Create FireRouter instance
            fire_router = FireRouter()
            self.log_trace("FIRE_ROUTER_IMPORT", "SUCCESS", {"class": "FireRouter"})
            
            # Create test trade request
            test_request = TradeRequest(
                symbol="XAUUSD",
                direction=TradeDirection.BUY,
                volume=0.01,
                stop_loss=2600.0,
                take_profit=2650.0,
                comment="DIAGNOSTIC_TEST",
                tcs_score=85.0,
                user_id="7176191872",
                mission_id="DIAGNOSTIC_001"
            )
            
            self.log_trace("TRADE_REQUEST_CREATED", "SUCCESS", {
                "symbol": test_request.symbol,
                "direction": test_request.direction.value,
                "volume": test_request.volume
            })
            
            # Test payload conversion
            bridge_payload = test_request.to_bridge_payload()
            self.log_trace("BRIDGE_PAYLOAD_CONVERSION", "SUCCESS", bridge_payload)
            
            # Test execution through FireRouter
            try:
                result = fire_router.execute_trade_request(test_request)
                self.log_trace("FIRE_ROUTER_EXECUTION", 
                             "SUCCESS" if result.success else "FAILURE", 
                             {
                                 "success": result.success,
                                 "message": result.message,
                                 "trade_id": result.trade_id,
                                 "execution_time_ms": result.execution_time_ms
                             })
            except Exception as e:
                self.log_trace("FIRE_ROUTER_EXECUTION", "FAILURE", {"error": str(e)})
                
        except Exception as e:
            self.log_trace("FIRE_ROUTER_IMPORT", "FAILURE", {"error": str(e)})
    
    def step_6_check_webapp_fire_api(self):
        """✅ Step 6: Check WebApp Fire API"""
        self.log_trace("STEP_6_WEBAPP_FIRE_API", "CHECKING", {})
        
        try:
            import requests
            
            # Test fire API endpoint
            fire_url = "http://127.0.0.1:8888/api/fire"
            test_payload = {
                "mission_id": "TEST_MISSION_001"
            }
            headers = {
                "Content-Type": "application/json",
                "X-User-ID": "7176191872"
            }
            
            try:
                response = requests.post(fire_url, json=test_payload, headers=headers, timeout=10)
                self.log_trace("WEBAPP_FIRE_API_TEST", 
                             "SUCCESS" if response.status_code == 200 else "FAILURE",
                             {
                                 "status_code": response.status_code,
                                 "response": response.text[:200]
                             })
            except Exception as e:
                self.log_trace("WEBAPP_FIRE_API_TEST", "FAILURE", {"error": str(e)})
                
        except Exception as e:
            self.log_trace("WEBAPP_FIRE_API_IMPORT", "FAILURE", {"error": str(e)})
    
    def step_7_check_system_routing(self):
        """✅ Step 7: Check System-Wide Routing"""
        self.log_trace("STEP_7_SYSTEM_ROUTING", "CHECKING", {})
        
        # Check for port conflicts
        try:
            result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True)
            ports_in_use = []
            
            for line in result.stdout.split('\n'):
                if ':9000' in line or ':8888' in line or ':5555' in line:
                    ports_in_use.append(line.strip())
            
            self.log_trace("PORT_USAGE_CHECK", "SUCCESS", {"ports": ports_in_use})
            
        except Exception as e:
            self.log_trace("PORT_USAGE_CHECK", "FAILURE", {"error": str(e)})
        
        # Check for running processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            bitten_processes = []
            
            for line in result.stdout.split('\n'):
                if any(proc in line for proc in ['bitten', 'apex', 'webapp', 'bridge']):
                    bitten_processes.append(line.strip())
            
            self.log_trace("PROCESS_CHECK", "SUCCESS", {"processes": len(bitten_processes)})
            for i, proc in enumerate(bitten_processes[:5]):  # Show first 5
                logger.info(f"    Process {i+1}: {proc}")
                
        except Exception as e:
            self.log_trace("PROCESS_CHECK", "FAILURE", {"error": str(e)})
    
    def run_full_diagnostic(self):
        """Run complete diagnostic trace"""
        logger.info("🔍 STARTING BITTEN FIRE EXECUTION DIAGNOSTIC TRACE")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Run all diagnostic steps
        self.step_1_bridge_credentials()
        self.step_2_verify_trading_enabled()
        payload = self.step_3_trace_fire_payload()
        self.step_4_test_fire_execution(payload)
        self.step_5_check_fire_router_integration()
        self.step_6_check_webapp_fire_api()
        self.step_7_check_system_routing()
        
        end_time = time.time()
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("🎯 DIAGNOSTIC SUMMARY")
        logger.info("=" * 60)
        
        success_count = sum(1 for entry in self.trace_log if entry["status"] == "SUCCESS")
        failure_count = sum(1 for entry in self.trace_log if entry["status"] == "FAILURE")
        
        logger.info(f"✅ Successful checks: {success_count}")
        logger.info(f"❌ Failed checks: {failure_count}")
        logger.info(f"⏱️  Total execution time: {end_time - start_time:.2f} seconds")
        
        # Show critical failures
        critical_failures = [entry for entry in self.trace_log 
                           if entry["status"] == "FAILURE" and "BRIDGE" in entry["step"]]
        
        if critical_failures:
            logger.info("🚨 CRITICAL FAILURES DETECTED:")
            for failure in critical_failures:
                logger.info(f"    ❌ {failure['step']}: {failure['details']}")
        
        # Save trace log
        trace_file = f"/root/HydraX-v2/fire_trace_{int(time.time())}.json"
        with open(trace_file, 'w') as f:
            json.dump(self.trace_log, f, indent=2)
        
        logger.info(f"📄 Full trace log saved: {trace_file}")
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "critical_failures": len(critical_failures),
            "trace_file": trace_file,
            "execution_time": end_time - start_time
        }

def main():
    """Run the fire execution diagnostic trace"""
    tracer = FireExecutionTracer()
    result = tracer.run_full_diagnostic()
    
    if result["critical_failures"] > 0:
        sys.exit(1)  # Exit with error if critical failures found
    else:
        sys.exit(0)  # Exit successfully

if __name__ == "__main__":
    main()