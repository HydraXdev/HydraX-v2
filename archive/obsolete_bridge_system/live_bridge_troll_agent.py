#!/usr/bin/env python3
"""
🌉 LIVE BRIDGE TROLL AGENT
Production bridge agent that creates instruction files for MT5 execution
and monitors for results - connects to Fire Loop Validation System
"""

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# UUID tracking integration
try:
    from tools.uuid_trade_tracker import UUIDTradeTracker
    UUID_TRACKING_AVAILABLE = True
except ImportError:
    UUID_TRACKING_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/live_bridge_troll.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LiveBridgeTrollAgent')

class LiveBridgeTrollAgent:
    """Production bridge agent for Fire Loop Validation System"""
    
    def __init__(self):
        # Fire Loop Validation file paths
        self.instructions_file = Path("/root/HydraX-v2/bitten_instructions.txt")
        self.secure_file = Path("/root/HydraX-v2/bitten_instructions_secure.txt")
        self.result_file = Path("/root/HydraX-v2/bitten_results.txt")
        
        # Mission monitoring
        self.missions_dir = Path("/root/HydraX-v2/missions")
        self.missions_dir.mkdir(exist_ok=True)
        
        # UUID tracking
        self.uuid_tracker = None
        if UUID_TRACKING_AVAILABLE:
            self.uuid_tracker = UUIDTradeTracker()
            logger.info("🔗 UUID tracking system initialized")
        
        # Last processed mission
        self.last_processed_mission = None
        
        logger.info("🌉 Live Bridge Troll Agent initialized")
        logger.info(f"📁 Instructions: {self.instructions_file}")
        logger.info(f"📁 Secure relay: {self.secure_file}")
        logger.info(f"📁 Results: {self.result_file}")
    
    def monitor_missions(self):
        """Monitor missions directory for new fired missions"""
        try:
            # Get all mission files
            mission_files = list(self.missions_dir.glob("*.json"))
            
            for mission_file in mission_files:
                try:
                    with open(mission_file, 'r') as f:
                        mission_data = json.load(f)
                    
                    # Check if mission was recently fired
                    if (mission_data.get('status') == 'fired' and 
                        mission_data.get('fired_at') and
                        mission_file.name != self.last_processed_mission):
                        
                        logger.info(f"🔥 Found fired mission: {mission_file.name}")
                        self.process_fired_mission(mission_data, mission_file.name)
                        self.last_processed_mission = mission_file.name
                
                except Exception as e:
                    logger.error(f"Error processing mission {mission_file.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error monitoring missions: {e}")
    
    def process_fired_mission(self, mission_data: Dict, mission_filename: str):
        """Process a fired mission and create instruction files"""
        try:
            # Extract trade data
            signal = mission_data.get('signal', {})
            enhanced_signal = mission_data.get('enhanced_signal', signal)
            trade_uuid = mission_data.get('trade_uuid')
            
            # Create instruction line for MT5 EA
            symbol = enhanced_signal.get('symbol', 'EURUSD')
            direction = enhanced_signal.get('direction', 'BUY')
            volume = 0.01  # Safe volume for production
            entry_price = enhanced_signal.get('entry_price', 0)
            tp_price = enhanced_signal.get('take_profit', 0)
            sl_price = enhanced_signal.get('stop_loss', 0)
            
            # Format instruction line
            instruction_line = f"{trade_uuid or mission_filename},{symbol},{direction},{volume},{entry_price},{tp_price},{sl_price}"
            
            # Write to instructions file
            with open(self.instructions_file, 'w') as f:
                f.write(instruction_line)
            
            logger.info(f"📄 Instruction file created: {instruction_line}")
            
            # Track file relay with UUID
            if self.uuid_tracker and trade_uuid:
                self.uuid_tracker.track_file_relay(trade_uuid, str(self.instructions_file), "bridge_troll_relay")
                logger.info(f"🔗 UUID tracking: File relay tracked for {trade_uuid}")
            
            # Create secure relay file
            with open(self.secure_file, 'w') as f:
                f.write(f"RELAYED:{trade_uuid or mission_filename}:SECURE")
            
            logger.info(f"🔐 Secure relay file created for {trade_uuid or mission_filename}")
            
        except Exception as e:
            logger.error(f"Error processing fired mission: {e}")
    
    def monitor_ea_results(self):
        """Monitor for EA execution results"""
        try:
            if self.result_file.exists():
                # Read result file
                with open(self.result_file, 'r') as f:
                    result_line = f.read().strip()
                
                if result_line:
                    # Parse result line
                    parts = result_line.split(',')
                    if len(parts) >= 5:
                        trade_uuid = parts[0]
                        status = parts[1]
                        ticket = parts[2]
                        message = parts[3]
                        price = parts[4]
                        
                        # Track EA detection and execution
                        if self.uuid_tracker and trade_uuid:
                            # Track EA detection
                            ea_log = f"[{datetime.utcnow().strftime('%H:%M:%S')}] EA detected and processed: {trade_uuid}"
                            self.uuid_tracker.track_ea_detection(trade_uuid, ea_log)
                            
                            # Track execution result
                            execution_result = {
                                'success': status == 'success',
                                'ticket': int(ticket) if ticket.isdigit() else None,
                                'message': message,
                                'execution_price': float(price) if price.replace('.', '').isdigit() else None,
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            
                            self.uuid_tracker.track_trade_execution(trade_uuid, execution_result)
                            logger.info(f"🔗 UUID tracking: EA result tracked for {trade_uuid}")
                        
                        logger.info(f"📊 EA result processed: {trade_uuid} - {status}")
                        
                        # Archive result file
                        archive_name = f"result_{trade_uuid}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
                        archive_path = Path("/root/HydraX-v2/results_archive")
                        archive_path.mkdir(exist_ok=True)
                        
                        os.rename(self.result_file, archive_path / archive_name)
                        logger.info(f"📁 Result archived: {archive_name}")
                
        except Exception as e:
            logger.error(f"Error monitoring EA results: {e}")
    
    def update_heartbeat(self):
        """Update bridge heartbeat file"""
        try:
            heartbeat_file = Path("/var/run/bridge_troll_heartbeat.txt")
            with open(heartbeat_file, 'w') as f:
                f.write(f"[HEARTBEAT] {datetime.utcnow().isoformat()}Z")
            
        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
    
    def run_monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting live bridge troll monitoring loop...")
        
        try:
            while True:
                # Monitor for new fired missions
                self.monitor_missions()
                
                # Monitor for EA results
                self.monitor_ea_results()
                
                # Update heartbeat
                self.update_heartbeat()
                
                # Sleep for 5 seconds
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Bridge troll monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Bridge troll monitoring error: {e}")
            raise
    
    def run_single_check(self):
        """Run single monitoring check"""
        logger.info("🔍 Running single bridge troll check...")
        
        self.monitor_missions()
        self.monitor_ea_results()
        self.update_heartbeat()
        
        logger.info("✅ Single check completed")

def main():
    """Main bridge troll agent"""
    agent = LiveBridgeTrollAgent()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        agent.run_single_check()
    else:
        agent.run_monitoring_loop()

if __name__ == "__main__":
    main()