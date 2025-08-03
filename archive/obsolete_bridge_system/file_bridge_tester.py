#!/usr/bin/env python3
"""
📂 FILE-BASED BRIDGE TESTER
Test the correct file-based communication protocol with MT5 bridge
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FileBridgeTester')

class FileBridgeTester:
    """Test file-based bridge communication protocol"""
    
    def __init__(self):
        # Bridge file paths (from config)
        self.instruction_file = "bitten_instructions.txt"
        self.result_file = "bitten_results.txt"
        self.status_file = "bitten_status.txt"
        
        # Bridge working directory
        self.bridge_dir = "/root/HydraX-v2"
        
        # Full file paths
        self.instruction_path = os.path.join(self.bridge_dir, self.instruction_file)
        self.result_path = os.path.join(self.bridge_dir, self.result_file)
        self.status_path = os.path.join(self.bridge_dir, self.status_file)
        
        logger.info(f"File Bridge Tester initialized")
        logger.info(f"Instruction file: {self.instruction_path}")
        logger.info(f"Result file: {self.result_path}")
        logger.info(f"Status file: {self.status_path}")
    
    def check_bridge_files_exist(self) -> Dict[str, bool]:
        """Check if bridge communication files exist"""
        files_status = {
            "instruction_file": os.path.exists(self.instruction_path),
            "result_file": os.path.exists(self.result_path),
            "status_file": os.path.exists(self.status_path)
        }
        
        logger.info("📂 BRIDGE FILES STATUS:")
        for file_type, exists in files_status.items():
            status = "✅ EXISTS" if exists else "❌ MISSING"
            logger.info(f"  {file_type}: {status}")
        
        return files_status
    
    def read_bridge_status(self) -> Optional[Dict[str, Any]]:
        """Read current bridge status from status file"""
        try:
            if os.path.exists(self.status_path):
                with open(self.status_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        status_data = json.loads(content)
                        logger.info(f"📊 Bridge Status: {json.dumps(status_data, indent=2)}")
                        return status_data
                    else:
                        logger.warning("⚠️ Status file exists but is empty")
                        return None
            else:
                logger.warning("⚠️ Status file does not exist")
                return None
        except Exception as e:
            logger.error(f"❌ Error reading status file: {e}")
            return None
    
    def read_bridge_results(self) -> Optional[Dict[str, Any]]:
        """Read latest results from result file"""
        try:
            if os.path.exists(self.result_path):
                with open(self.result_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        # Result file may contain multiple results, get the latest
                        lines = content.strip().split('\n')
                        latest_result = lines[-1]
                        result_data = json.loads(latest_result)
                        logger.info(f"📥 Latest Result: {json.dumps(result_data, indent=2)}")
                        return result_data
                    else:
                        logger.warning("⚠️ Result file exists but is empty")
                        return None
            else:
                logger.warning("⚠️ Result file does not exist")
                return None
        except Exception as e:
            logger.error(f"❌ Error reading result file: {e}")
            return None
    
    def write_trade_instruction(self, trade_data: Dict[str, Any]) -> bool:
        """Write trade instruction to instruction file"""
        try:
            # Add instruction metadata
            instruction = {
                "timestamp": datetime.now().isoformat(),
                "instruction_id": f"INST_{int(time.time())}",
                "type": "trade_request",
                "data": trade_data
            }
            
            # Write to instruction file
            with open(self.instruction_path, 'w') as f:
                json.dump(instruction, f, indent=2)
            
            logger.info(f"📤 Trade instruction written:")
            logger.info(f"  File: {self.instruction_path}")
            logger.info(f"  Instruction: {json.dumps(instruction, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing instruction file: {e}")
            return False
    
    def wait_for_result(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Wait for bridge to process instruction and write result"""
        logger.info(f"⏳ Waiting for bridge result (timeout: {timeout}s)...")
        
        start_time = time.time()
        last_result_size = 0
        
        # Get initial result file size
        if os.path.exists(self.result_path):
            last_result_size = os.path.getsize(self.result_path)
        
        while time.time() - start_time < timeout:
            try:
                if os.path.exists(self.result_path):
                    current_size = os.path.getsize(self.result_path)
                    
                    # Check if file has been modified (new content)
                    if current_size > last_result_size:
                        logger.info("📥 New result detected!")
                        time.sleep(0.5)  # Give time for write to complete
                        return self.read_bridge_results()
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.warning(f"⚠️ Error checking result file: {e}")
                time.sleep(1)
        
        logger.warning(f"⏰ Timeout waiting for bridge result after {timeout}s")
        return None
    
    def test_eurusd_trade(self) -> Dict[str, Any]:
        """Test EURUSD trade through file bridge"""
        logger.info("\n🎯 TESTING EURUSD TRADE VIA FILE BRIDGE")
        logger.info("-" * 50)
        
        # Create EURUSD trade instruction
        trade_data = {
            "symbol": "EURUSD",
            "type": "buy",
            "lot": 0.01,
            "sl": 1.088,
            "tp": 1.094,
            "comment": "BITTEN_FILE_TEST",
            "mission_id": f"FILE_TEST_{int(time.time())}",
            "user_id": "7176191872"
        }
        
        # Write instruction
        if not self.write_trade_instruction(trade_data):
            return {"success": False, "error": "Failed to write instruction"}
        
        # Wait for result
        result = self.wait_for_result(timeout=30)
        
        if result:
            return {"success": True, "result": result}
        else:
            return {"success": False, "error": "No result received within timeout"}
    
    def run_file_bridge_diagnostic(self):
        """Run complete file bridge diagnostic"""
        logger.info("📂 FILE-BASED BRIDGE DIAGNOSTIC")
        logger.info("Testing correct file-based MT5 bridge protocol")
        logger.info("=" * 60)
        
        # Step 1: Check if bridge files exist
        files_status = self.check_bridge_files_exist()
        
        # Step 2: Read current bridge status
        bridge_status = self.read_bridge_status()
        
        # Step 3: Read any existing results
        existing_results = self.read_bridge_results()
        
        # Step 4: Test EURUSD trade
        trade_result = self.test_eurusd_trade()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 FILE BRIDGE DIAGNOSTIC SUMMARY")
        logger.info("=" * 60)
        
        # File availability
        files_available = sum(files_status.values())
        logger.info(f"📂 Bridge files available: {files_available}/3")
        
        # Bridge status
        if bridge_status:
            logger.info(f"📊 Bridge status: {bridge_status.get('status', 'Unknown')}")
            if bridge_status.get('mt5_connected'):
                logger.info("✅ MT5 connection: Connected")
            else:
                logger.info("❌ MT5 connection: Disconnected")
        else:
            logger.info("❌ Bridge status: Unknown (no status file)")
        
        # Trade test result
        if trade_result["success"]:
            logger.info("✅ EURUSD trade test: SUCCESS")
            if trade_result.get("result"):
                result_data = trade_result["result"]
                if result_data.get("success"):
                    logger.info(f"  ✅ Trade executed: {result_data.get('message', 'No message')}")
                    if result_data.get("ticket"):
                        logger.info(f"  🎫 Ticket: {result_data['ticket']}")
                else:
                    logger.info(f"  ❌ Trade failed: {result_data.get('error', 'Unknown error')}")
        else:
            logger.info(f"❌ EURUSD trade test: FAILED - {trade_result.get('error')}")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        if files_available == 0:
            logger.info("  ❌ Bridge files missing - Bridge may not be running")
            logger.info("  💡 Start the file-based bridge service")
        elif not bridge_status:
            logger.info("  ❌ No bridge status available")
            logger.info("  💡 Check if bridge process is running")
        elif not bridge_status.get('mt5_connected'):
            logger.info("  ❌ Bridge not connected to MT5")
            logger.info("  💡 Check MT5 terminal and credentials")
        elif trade_result["success"]:
            logger.info("  ✅ File bridge communication working!")
            logger.info("  🎯 Ready for live trading")
        
        return {
            "files_available": files_available,
            "bridge_status": bridge_status,
            "trade_test_success": trade_result["success"],
            "summary": "File bridge diagnostic completed"
        }

def main():
    """Run file bridge diagnostic"""
    tester = FileBridgeTester()
    results = tester.run_file_bridge_diagnostic()
    
    # Exit with appropriate code
    if results["trade_test_success"]:
        exit(0)  # Success
    elif results["files_available"] == 0:
        exit(2)  # Bridge not running
    else:
        exit(1)  # Other failure

if __name__ == "__main__":
    main()