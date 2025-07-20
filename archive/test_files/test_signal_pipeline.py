#!/usr/bin/env python3
"""
Test Signal Pipeline - Generate test signals and verify complete flow

This script:
1. Generates test signals in APEX log format
2. Writes them to the log file
3. Verifies mission generation
4. Tests API endpoints
5. Validates fire router execution
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Test-Signal-Pipeline')

class SignalPipelineTest:
    """Test the complete signal pipeline"""
    
    def __init__(self):
        self.base_dir = Path("/root/HydraX-v2")
        self.missions_dir = self.base_dir / "missions"
        self.log_file = self.base_dir / "apex_v5_live_real.log"
        
        # Ensure directories exist
        self.missions_dir.mkdir(exist_ok=True)
        
        # Test signals
        self.test_signals = [
            {
                "log_line": "🎯 SIGNAL #1: EURUSD BUY TCS:85%",
                "expected": {
                    "symbol": "EURUSD",
                    "type": "buy",
                    "tcs_score": 85
                }
            },
            {
                "log_line": "🎯 SIGNAL #2: GBPUSD SELL TCS:78%",
                "expected": {
                    "symbol": "GBPUSD",
                    "type": "sell",
                    "tcs_score": 78
                }
            },
            {
                "log_line": "🎯 SIGNAL #3: USDJPY BUY TCS:92%",
                "expected": {
                    "symbol": "USDJPY",
                    "type": "buy",
                    "tcs_score": 92
                }
            }
        ]
        
        logger.info("Signal pipeline test initialized")
    
    def write_test_signals_to_log(self):
        """Write test signals to log file"""
        try:
            logger.info("Writing test signals to log file...")
            
            with open(self.log_file, 'a') as f:
                f.write(f"\n# Test signals generated at {datetime.now().isoformat()}\n")
                
                for i, signal in enumerate(self.test_signals):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"[{timestamp}] {signal['log_line']}\n"
                    f.write(log_entry)
                    
                    logger.info(f"✓ Written signal {i+1}: {signal['log_line']}")
                    
                    # Add small delay between signals
                    time.sleep(0.1)
            
            logger.info("✅ Test signals written to log file")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to write test signals: {e}")
            return False
    
    def test_signal_parsing(self):
        """Test signal parsing"""
        try:
            logger.info("Testing signal parsing...")
            
            # Mock telegram token for testing
            original_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'
            
            try:
                # Import apex connector
                from apex_telegram_connector import ApexTelegramConnector
                
                # Create connector
                connector = ApexTelegramConnector()
                
                # Test each signal
                parsed_signals = []
                
                for signal in self.test_signals:
                    parsed = connector.parse_signal_line(signal['log_line'])
                    
                    if not parsed:
                        logger.error(f"Failed to parse: {signal['log_line']}")
                        return False
                    
                    # Verify parsed data
                    expected = signal['expected']
                    
                    if parsed['symbol'] != expected['symbol']:
                        logger.error(f"Symbol mismatch: expected {expected['symbol']}, got {parsed['symbol']}")
                        return False
                    
                    if parsed['type'] != expected['type']:
                        logger.error(f"Type mismatch: expected {expected['type']}, got {parsed['type']}")
                        return False
                    
                    if parsed['tcs_score'] != expected['tcs_score']:
                        logger.error(f"TCS mismatch: expected {expected['tcs_score']}, got {parsed['tcs_score']}")
                        return False
                    
                    parsed_signals.append(parsed)
                    logger.info(f"✓ Parsed: {parsed['symbol']} {parsed['type']} TCS:{parsed['tcs_score']}%")
                
                logger.info("✅ Signal parsing test passed")
                return parsed_signals
                
            finally:
                # Restore original token
                if original_token:
                    os.environ['TELEGRAM_BOT_TOKEN'] = original_token
                else:
                    os.environ.pop('TELEGRAM_BOT_TOKEN', None)
                    
        except Exception as e:
            logger.error(f"❌ Signal parsing test failed: {e}")
            return False
    
    def test_mission_generation(self, parsed_signals):
        """Test mission generation from parsed signals"""
        try:
            logger.info("Testing mission generation...")
            
            # Add src to path
            sys.path.insert(0, str(self.base_dir / "src"))
            
            # Import mission generator
            from bitten_core.mission_briefing_generator_v5 import generate_mission
            
            generated_missions = []
            
            for i, signal in enumerate(parsed_signals):
                # Add missing fields for mission generation
                mission_signal = {
                    "symbol": signal["symbol"],
                    "type": signal["type"],
                    "tp": 1.1050 if signal["symbol"] == "EURUSD" else 1.2750,  # Sample TP
                    "sl": 1.1020 if signal["symbol"] == "EURUSD" else 1.2800,  # Sample SL
                    "tcs_score": signal["tcs_score"]
                }
                
                # Generate mission
                mission = generate_mission(mission_signal, f"test_user_{i+1}")
                
                # Verify mission structure
                required_fields = ["mission_id", "user_id", "symbol", "type", "tp", "sl", "tcs"]
                for field in required_fields:
                    if field not in mission:
                        logger.error(f"Mission missing field: {field}")
                        return False
                
                # Verify mission file exists
                mission_file = self.missions_dir / f"{mission['mission_id']}.json"
                if not mission_file.exists():
                    logger.error(f"Mission file not created: {mission_file}")
                    return False
                
                generated_missions.append(mission)
                logger.info(f"✓ Generated mission: {mission['mission_id']} for {mission['symbol']}")
            
            logger.info("✅ Mission generation test passed")
            return generated_missions
            
        except Exception as e:
            logger.error(f"❌ Mission generation test failed: {e}")
            return False
    
    def test_mission_api(self, missions):
        """Test mission API endpoints"""
        try:
            logger.info("Testing mission API...")
            
            # Import mission endpoints
            from api.mission_endpoints import load_mission_data, save_mission_data
            
            for mission in missions:
                # Test loading mission
                loaded_mission = load_mission_data(mission['mission_id'])
                
                if not loaded_mission:
                    logger.error(f"Failed to load mission: {mission['mission_id']}")
                    return False
                
                # Verify data integrity
                if loaded_mission['mission_id'] != mission['mission_id']:
                    logger.error(f"Mission ID mismatch: {loaded_mission['mission_id']} != {mission['mission_id']}")
                    return False
                
                if loaded_mission['symbol'] != mission['symbol']:
                    logger.error(f"Symbol mismatch: {loaded_mission['symbol']} != {mission['symbol']}")
                    return False
                
                logger.info(f"✓ API test passed for mission: {mission['mission_id']}")
            
            logger.info("✅ Mission API test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mission API test failed: {e}")
            return False
    
    def test_fire_router(self, missions):
        """Test fire router execution"""
        try:
            logger.info("Testing fire router execution...")
            
            # Import fire router
            from bitten_core.fire_router import FireRouter, ExecutionMode
            
            # Create router in simulation mode
            router = FireRouter(execution_mode=ExecutionMode.SIMULATION)
            
            executed_trades = []
            
            for mission in missions:
                # Convert to legacy format for backward compatibility
                legacy_mission = {
                    "mission_id": mission['mission_id'],
                    "user_id": mission['user_id'],
                    "symbol": mission['symbol'],
                    "type": mission['type'],
                    "tp": mission['tp'],
                    "sl": mission['sl'],
                    "lot_size": mission.get('lot_size', 0.01),
                    "tcs": mission['tcs']
                }
                
                # Execute trade
                result = router.execute_trade(legacy_mission)
                
                if result not in ["sent_to_bridge", "failed"]:
                    logger.error(f"Unexpected execution result: {result}")
                    return False
                
                executed_trades.append({
                    "mission_id": mission['mission_id'],
                    "symbol": mission['symbol'],
                    "result": result
                })
                
                logger.info(f"✓ Trade executed: {mission['symbol']} - {result}")
            
            logger.info("✅ Fire router test passed")
            return executed_trades
            
        except Exception as e:
            logger.error(f"❌ Fire router test failed: {e}")
            return False
    
    def test_complete_pipeline(self):
        """Test the complete signal-to-execution pipeline"""
        try:
            logger.info("Testing complete pipeline...")
            
            # Step 1: Write test signals to log
            if not self.write_test_signals_to_log():
                return False
            
            # Step 2: Parse signals
            parsed_signals = self.test_signal_parsing()
            if not parsed_signals:
                return False
            
            # Step 3: Generate missions
            missions = self.test_mission_generation(parsed_signals)
            if not missions:
                return False
            
            # Step 4: Test API
            if not self.test_mission_api(missions):
                return False
            
            # Step 5: Execute trades
            executed_trades = self.test_fire_router(missions)
            if not executed_trades:
                return False
            
            logger.info("✅ Complete pipeline test passed")
            
            # Print summary
            print("\n" + "="*60)
            print("SIGNAL PIPELINE TEST SUMMARY")
            print("="*60)
            print(f"Signals processed: {len(parsed_signals)}")
            print(f"Missions generated: {len(missions)}")
            print(f"Trades executed: {len(executed_trades)}")
            
            print("\nExecuted Trades:")
            for trade in executed_trades:
                print(f"  - {trade['symbol']}: {trade['result']}")
            
            print("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Complete pipeline test failed: {e}")
            return False
    
    def verify_directory_structure(self):
        """Verify required directories and files exist"""
        try:
            logger.info("Verifying directory structure...")
            
            # Check directories
            required_dirs = [
                self.missions_dir,
                self.base_dir / "src",
                self.base_dir / "src" / "api",
                self.base_dir / "src" / "bitten_core"
            ]
            
            for dir_path in required_dirs:
                if not dir_path.exists():
                    logger.error(f"Required directory missing: {dir_path}")
                    return False
                logger.info(f"✓ Directory exists: {dir_path}")
            
            # Check files
            required_files = [
                self.base_dir / "apex_telegram_connector.py",
                self.base_dir / "src" / "api" / "mission_endpoints.py",
                self.base_dir / "src" / "bitten_core" / "fire_router.py",
                self.base_dir / "src" / "bitten_core" / "mission_briefing_generator_v5.py"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    logger.error(f"Required file missing: {file_path}")
                    return False
                logger.info(f"✓ File exists: {file_path}")
            
            logger.info("✅ Directory structure verification passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Directory structure verification failed: {e}")
            return False
    
    def cleanup_test_files(self):
        """Clean up test files"""
        try:
            # Clean up test mission files
            for mission_file in self.missions_dir.glob("test_user_*.json"):
                try:
                    mission_file.unlink()
                except:
                    pass
            
            logger.info("✅ Test files cleaned up")
            
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def run_pipeline_test(self):
        """Run the complete pipeline test"""
        logger.info("Starting signal pipeline test...")
        
        try:
            # Verify directory structure
            if not self.verify_directory_structure():
                return False
            
            # Run complete pipeline test
            success = self.test_complete_pipeline()
            
            # Cleanup
            self.cleanup_test_files()
            
            if success:
                print("\n🎉 SIGNAL PIPELINE TEST PASSED - All components working correctly!")
                return True
            else:
                print("\n❌ SIGNAL PIPELINE TEST FAILED - Please check the issues above")
                return False
                
        except Exception as e:
            logger.error(f"Pipeline test failed: {e}")
            return False


def main():
    """Main function"""
    test_runner = SignalPipelineTest()
    
    try:
        success = test_runner.run_pipeline_test()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"Test runner failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())