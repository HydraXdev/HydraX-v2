#!/usr/bin/env python3
"""
AUTO Fire Mode Monitor
Monitors new missions and auto-fires 90%+ TCS signals for COMMANDER+ users
"""

import json
import logging
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from .fire_mode_database import fire_mode_db
from .fire_mode_executor import fire_mode_executor

logger = logging.getLogger(__name__)

class AutoFireMonitor:
    """Monitors and executes AUTO mode trades"""
    
    def __init__(self, missions_dir: str = "/root/HydraX-v2/missions/"):
        self.missions_dir = Path(missions_dir)
        self.running = False
        self.monitor_thread = None
        self.processed_missions = set()
        self.check_interval = 5  # seconds
        
    def start(self):
        """Start the AUTO fire monitor"""
        if self.running:
            logger.warning("AUTO fire monitor already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("AUTO fire monitor started")
    
    def stop(self):
        """Stop the AUTO fire monitor"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("AUTO fire monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_new_missions()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in AUTO fire monitor: {e}")
                time.sleep(self.check_interval)
    
    def _check_new_missions(self):
        """Check for new missions that should be auto-fired"""
        try:
            # Get all mission files
            if not self.missions_dir.exists():
                return
                
            mission_files = list(self.missions_dir.glob("*.json"))
            
            for mission_file in mission_files:
                # Skip if already processed
                mission_id = mission_file.stem
                if mission_id in self.processed_missions:
                    continue
                
                # Load mission
                try:
                    with open(mission_file, 'r') as f:
                        mission = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading mission {mission_file}: {e}")
                    continue
                
                # Mark as processed
                self.processed_missions.add(mission_id)
                
                # Check if mission should be auto-fired
                self._process_mission_for_auto_fire(mission)
                
        except Exception as e:
            logger.error(f"Error checking new missions: {e}")
    
    def _process_mission_for_auto_fire(self, mission: Dict):
        """Process a mission for potential auto-fire"""
        try:
            # Extract user info
            user_id = mission.get('user_id')
            if not user_id:
                return
            
            # Get user mode info
            mode_info = fire_mode_db.get_user_mode(user_id)
            if mode_info['current_mode'] != 'AUTO':
                return
            
            # TODO: Get user tier from database/config
            # For now, we'll need to integrate with user management
            user_tier = self._get_user_tier(user_id)
            if not user_tier:
                return
            
            # Check if should auto-fire
            should_fire, reason = fire_mode_executor.should_auto_fire(
                user_id, user_tier, mission
            )
            
            if should_fire:
                logger.info(f"AUTO-FIRING mission {mission.get('mission_id')} for user {user_id}")
                
                # Execute auto-fire
                result = fire_mode_executor.execute_auto_fire(user_id, mission)
                
                if result['success']:
                    logger.info(f"AUTO-FIRE successful: {result}")
                    self._notify_user_of_auto_fire(user_id, mission, result)
                else:
                    logger.error(f"AUTO-FIRE failed: {result}")
            else:
                logger.debug(f"Mission not auto-fired for user {user_id}: {reason}")
                
        except Exception as e:
            logger.error(f"Error processing mission for auto-fire: {e}")
    
    def _get_user_tier(self, user_id: str) -> Optional[str]:
        """Get user tier - TODO: integrate with user management"""
        # This should connect to your user database
        # For now, return None
        return None
    
    def _notify_user_of_auto_fire(self, user_id: str, mission: Dict, result: Dict):
        """Notify user that trade was auto-fired"""
        # TODO: Send Telegram notification
        # This should integrate with the bot to send a message
        logger.info(f"Would notify user {user_id} of auto-fire: {mission.get('symbol')}")
    
    def get_auto_fire_stats(self) -> Dict:
        """Get statistics about auto-fire activity"""
        # Get all AUTO mode users
        auto_users = []
        
        # TODO: Query database for users in AUTO mode
        # This is a placeholder structure
        
        return {
            'monitor_status': 'running' if self.running else 'stopped',
            'processed_missions': len(self.processed_missions),
            'auto_mode_users': len(auto_users),
            'check_interval': self.check_interval
        }
    
    def clear_processed_missions(self):
        """Clear the processed missions set (for daily reset)"""
        self.processed_missions.clear()
        logger.info("Cleared processed missions set")

# Create singleton instance
auto_fire_monitor = AutoFireMonitor()

# Start monitoring when module is imported
# auto_fire_monitor.start()  # Uncomment to auto-start