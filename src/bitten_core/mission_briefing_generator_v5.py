# INTEGRATED MISSION BRIEFING GENERATOR v5.0
# Combines simple file persistence with comprehensive APEXv5MissionBriefing system
# Generates rich mission briefing objects AND saves them to files for WebApp retrieval

import json
import os
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Mission storage directory
MISSION_DIR = "./missions/"

# Import the APEXv5 classes from the active generator
from .mission_briefing_generator_active import (
    APEXv5MissionType,
    APEXv5UrgencyLevel,
    APEXv5SignalClass,
    APEXv5MissionBriefing,
    APEXv5MissionBriefingGenerator
)

class IntegratedMissionBriefingGenerator:
    """
    Integrated Mission Briefing Generator that combines:
    1. Simple file-based persistence from the deployment version
    2. Rich APEXv5MissionBriefing data structures from the complex version
    3. Proper expiry timestamp management
    4. WebApp-ready file storage
    """
    
    def __init__(self):
        self.apex_generator = APEXv5MissionBriefingGenerator()
        # Ensure missions directory exists
        os.makedirs(MISSION_DIR, exist_ok=True)
        logger.info("Integrated Mission Briefing Generator initialized")
    
    def generate_mission(self, signal: Dict, user_id: str, user_data: Dict = None, 
                        account_data: Dict = None) -> Dict:
        """
        Generate a mission combining simple format for backward compatibility
        and comprehensive APEXv5MissionBriefing for rich data.
        
        Args:
            signal: Signal data from trading engine
            user_id: User identifier
            user_data: Optional user profile data
            account_data: Optional account information
            
        Returns:
            Dict: Mission data in simple format + comprehensive briefing
        """
        
        # Set default values if not provided
        if user_data is None:
            user_data = {
                'tier': 'AUTHORIZED',
                'daily_signals': 0,
                'daily_pips': 0.0,
                'win_rate': 89.0
            }
        
        if account_data is None:
            account_data = {
                'balance': 2913.25
            }
        
        # Generate timestamps
        current_time = datetime.utcnow()
        expiry_minutes = self._calculate_expiry_minutes(signal, user_data.get('tier', 'AUTHORIZED'))
        expires_at = current_time + timedelta(minutes=expiry_minutes)
        
        # Create mission ID
        mission_id = f"{user_id}_{int(time.time())}"
        
        # Prepare signal data for APEXv5 generator
        apex_signal_data = self._prepare_apex_signal_data(signal, mission_id)
        
        # Generate comprehensive APEXv5 mission briefing
        try:
            apex_briefing = self.apex_generator.generate_v5_mission_briefing(
                apex_signal_data, user_data, account_data
            )
            
            # Convert to webapp format
            webapp_briefing = self.apex_generator.format_for_webapp(apex_briefing)
            
        except Exception as e:
            logger.error(f"Error generating APEX briefing: {e}")
            # Fallback to basic briefing
            apex_briefing = None
            webapp_briefing = {}
        
        # Create simple mission format (backward compatibility)
        simple_mission = {
            "mission_id": mission_id,
            "user_id": user_id,
            "symbol": signal.get("symbol", "EURUSD"),
            "type": signal.get("type", "arcade"),
            "tp": signal.get("tp", signal.get("take_profit", 20)),
            "sl": signal.get("sl", signal.get("stop_loss", 10)),
            "tcs": signal.get("tcs_score", signal.get("tcs", 75)),
            "risk": 1.5,
            "account_balance": account_data.get('balance', 2913.25),
            "lot_size": 0.12,
            "timestamp": current_time.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "pending"
        }
        
        # Create comprehensive mission data
        comprehensive_mission = {
            # Simple format for backward compatibility
            **simple_mission,
            
            # Enhanced mission data
            "mission_type": signal.get("type", "arcade"),
            "direction": signal.get("direction", "BUY"),
            "entry_price": signal.get("entry_price", 1.0000),
            "timeframe": signal.get("timeframe", "M5"),
            "session": signal.get("session", "LONDON"),
            "confidence": signal.get("confidence", 0.75),
            "pattern_name": signal.get("pattern", "Unknown Pattern"),
            "confluence_count": signal.get("confluence_count", 1),
            
            # User context
            "user_tier": user_data.get('tier', 'AUTHORIZED'),
            "daily_signals_count": user_data.get('daily_signals', 0),
            "user_win_rate": user_data.get('win_rate', 89.0),
            
            # Timing enhancements
            "expiry_minutes": expiry_minutes,
            "countdown_seconds": int(expiry_minutes * 60),
            "execution_window": int(expiry_minutes * 60),
            
            # File metadata
            "file_path": f"{MISSION_DIR}{mission_id}.json",
            "created_timestamp": int(time.time()),
            "expires_timestamp": int(expires_at.timestamp()),
            
            # APEX v5.0 briefing data (if available)
            "apex_briefing": webapp_briefing if apex_briefing else None,
            "has_apex_briefing": apex_briefing is not None,
            
            # Version info
            "generator_version": "v5.0_integrated",
            "format_version": "1.0"
        }
        
        # Save to file with proper error handling
        try:
            self._save_mission_to_file(comprehensive_mission)
            logger.info(f"Mission {mission_id} saved successfully")
        except Exception as e:
            logger.error(f"Error saving mission {mission_id}: {e}")
            comprehensive_mission["file_save_error"] = str(e)
        
        # Clean up expired missions
        self._cleanup_expired_missions()
        
        return comprehensive_mission
    
    def _prepare_apex_signal_data(self, signal: Dict, mission_id: str) -> Dict:
        """Prepare signal data for APEXv5 generator"""
        return {
            'symbol': signal.get("symbol", "EURUSD"),
            'direction': signal.get("direction", "BUY"),
            'entry_price': signal.get("entry_price", 1.0000),
            'stop_loss': signal.get("sl", signal.get("stop_loss", 10)),
            'take_profit': signal.get("tp", signal.get("take_profit", 20)),
            'tcs': signal.get("tcs_score", signal.get("tcs", 75)),
            'pattern': signal.get("pattern", "Unknown Pattern"),
            'timeframe': signal.get("timeframe", "M5"),
            'session': signal.get("session", "LONDON"),
            'confidence': signal.get("confidence", 0.75),
            'confluence_count': signal.get("confluence_count", 1),
            'type': signal.get("type", "arcade"),
            'mission_id': mission_id
        }
    
    def _calculate_expiry_minutes(self, signal: Dict, user_tier: str) -> int:
        """Calculate expiry minutes based on signal type and user tier"""
        base_expiry = 5  # Default 5 minutes
        
        # Adjust based on signal type
        signal_type = signal.get("type", "arcade")
        if signal_type == "sniper":
            base_expiry = 15  # Sniper signals get more time
        elif signal_type == "midnight_hammer":
            base_expiry = 10  # Coordinated signals get medium time
        elif signal_type == "arcade":
            base_expiry = 5   # Fast arcade signals
        
        # Adjust based on timeframe
        timeframe = signal.get("timeframe", "M5")
        if timeframe == "M1":
            base_expiry = max(2, base_expiry - 2)  # Shorter for M1
        elif timeframe == "M15":
            base_expiry += 5  # Longer for M15
        elif timeframe == "H1":
            base_expiry += 10  # Much longer for H1
        
        # Adjust based on user tier
        tier_multipliers = {
            'PRESS_PASS': 0.8,  # Less time for basic users
            'NIBBLER': 0.9,
            'FANG': 1.0,
            'COMMANDER': 1.2,
            'APEX': 1.5,  # More time for premium users
            'AUTHORIZED': 1.0,
            'ELITE': 1.3,
            'ADMIN': 2.0
        }
        
        multiplier = tier_multipliers.get(user_tier, 1.0)
        final_expiry = int(base_expiry * multiplier)
        
        # Ensure reasonable bounds
        return max(1, min(final_expiry, 60))  # Between 1 and 60 minutes
    
    def _save_mission_to_file(self, mission: Dict) -> None:
        """Save mission to file with proper error handling"""
        mission_id = mission["mission_id"]
        file_path = f"{MISSION_DIR}{mission_id}.json"
        
        # Create backup copy of existing file if it exists
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
            except Exception as e:
                logger.warning(f"Could not create backup for {mission_id}: {e}")
        
        # Save mission data
        try:
            with open(file_path, "w", encoding='utf-8') as f:
                json.dump(mission, f, indent=2, ensure_ascii=False)
            
            # Remove backup if save was successful
            backup_path = f"{file_path}.backup"
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            # Restore backup if save failed
            backup_path = f"{file_path}.backup"
            if os.path.exists(backup_path):
                try:
                    os.rename(backup_path, file_path)
                except Exception as restore_error:
                    logger.error(f"Could not restore backup for {mission_id}: {restore_error}")
            raise e
    
    def _cleanup_expired_missions(self) -> None:
        """Clean up expired mission files"""
        try:
            current_time = int(time.time())
            cleaned_count = 0
            
            if not os.path.exists(MISSION_DIR):
                return
            
            for filename in os.listdir(MISSION_DIR):
                if filename.endswith(".json") and not filename.endswith(".backup"):
                    file_path = os.path.join(MISSION_DIR, filename)
                    
                    try:
                        # Check if file is expired
                        with open(file_path, 'r', encoding='utf-8') as f:
                            mission_data = json.load(f)
                        
                        expires_timestamp = mission_data.get("expires_timestamp")
                        if expires_timestamp and expires_timestamp < current_time:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.debug(f"Cleaned expired mission: {filename}")
                    
                    except Exception as e:
                        logger.warning(f"Error processing file {filename} during cleanup: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired mission files")
                
        except Exception as e:
            logger.error(f"Error during mission cleanup: {e}")
    
    def get_mission_by_id(self, mission_id: str) -> Optional[Dict]:
        """Retrieve mission by ID from file"""
        file_path = f"{MISSION_DIR}{mission_id}.json"
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    mission_data = json.load(f)
                
                # Check if mission is expired
                expires_timestamp = mission_data.get("expires_timestamp")
                if expires_timestamp and expires_timestamp < int(time.time()):
                    logger.info(f"Mission {mission_id} is expired")
                    return None
                
                return mission_data
            else:
                logger.warning(f"Mission file not found: {mission_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving mission {mission_id}: {e}")
            return None
    
    def get_active_missions(self, user_id: str = None) -> List[Dict]:
        """Get all active (non-expired) missions, optionally filtered by user"""
        active_missions = []
        current_time = int(time.time())
        
        try:
            if not os.path.exists(MISSION_DIR):
                return active_missions
            
            for filename in os.listdir(MISSION_DIR):
                if filename.endswith(".json") and not filename.endswith(".backup"):
                    file_path = os.path.join(MISSION_DIR, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            mission_data = json.load(f)
                        
                        # Check if mission is active
                        expires_timestamp = mission_data.get("expires_timestamp")
                        if expires_timestamp and expires_timestamp >= current_time:
                            # Filter by user if specified
                            if user_id is None or mission_data.get("user_id") == user_id:
                                active_missions.append(mission_data)
                    
                    except Exception as e:
                        logger.warning(f"Error reading mission file {filename}: {e}")
            
            # Sort by creation time (newest first)
            active_missions.sort(key=lambda x: x.get("created_timestamp", 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error retrieving active missions: {e}")
        
        return active_missions

# Factory function for backward compatibility
def generate_mission(signal: Dict, user_id: str, user_data: Dict = None, 
                    account_data: Dict = None) -> Dict:
    """
    Generate mission using the integrated system.
    Maintains backward compatibility with the simple interface.
    """
    generator = IntegratedMissionBriefingGenerator()
    return generator.generate_mission(signal, user_id, user_data, account_data)

# Initialize global generator instance
_global_generator = None

def get_mission_generator() -> IntegratedMissionBriefingGenerator:
    """Get or create the global mission generator instance"""
    global _global_generator
    if _global_generator is None:
        _global_generator = IntegratedMissionBriefingGenerator()
    return _global_generator

# Convenience functions for WebApp integration
def get_mission_by_id(mission_id: str) -> Optional[Dict]:
    """Retrieve mission by ID"""
    return get_mission_generator().get_mission_by_id(mission_id)

def get_active_missions(user_id: str = None) -> List[Dict]:
    """Get all active missions"""
    return get_mission_generator().get_active_missions(user_id)

def cleanup_expired_missions() -> None:
    """Clean up expired mission files"""
    return get_mission_generator()._cleanup_expired_missions()

# Testing
if __name__ == "__main__":
    # Test the integrated system
    generator = IntegratedMissionBriefingGenerator()
    
    # Test signal data
    test_signal = {
        "symbol": "GBPUSD",
        "type": "arcade",
        "direction": "BUY",
        "entry_price": 1.27650,
        "sl": 10,
        "tp": 20,
        "tcs_score": 87,
        "timeframe": "M5",
        "session": "LONDON",
        "pattern": "Double Bottom",
        "confluence_count": 2,
        "confidence": 0.87
    }
    
    # Test user data
    test_user_data = {
        "tier": "AUTHORIZED",
        "daily_signals": 5,
        "daily_pips": 45.2,
        "win_rate": 89.0
    }
    
    # Test account data
    test_account_data = {
        "balance": 5000.00
    }
    
    # Generate mission
    print("=== GENERATING INTEGRATED MISSION ===")
    mission = generator.generate_mission(test_signal, "test_user_123", test_user_data, test_account_data)
    
    print(f"Mission ID: {mission['mission_id']}")
    print(f"Symbol: {mission['symbol']}")
    print(f"Type: {mission['type']}")
    print(f"User Tier: {mission['user_tier']}")
    print(f"Expires At: {mission['expires_at']}")
    print(f"Has APEX Briefing: {mission['has_apex_briefing']}")
    
    # Test retrieval
    print("\n=== TESTING RETRIEVAL ===")
    retrieved = generator.get_mission_by_id(mission['mission_id'])
    if retrieved:
        print(f"Successfully retrieved mission: {retrieved['mission_id']}")
    else:
        print("Failed to retrieve mission")
    
    # Test active missions
    print("\n=== TESTING ACTIVE MISSIONS ===")
    active = generator.get_active_missions("test_user_123")
    print(f"Found {len(active)} active missions for user")
    
    print("\n=== INTEGRATION TEST COMPLETE ===")
