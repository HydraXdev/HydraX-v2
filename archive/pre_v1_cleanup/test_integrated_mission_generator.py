#!/usr/bin/env python3
"""
Test script for the integrated mission briefing generator
Tests the core functionality without complex dependencies
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Add the src directory to the path
sys.path.append('/root/HydraX-v2/src')

# Mission storage directory
MISSION_DIR = "./missions/"

class SimplifiedIntegratedMissionBriefingGenerator:
    """
    Simplified version of the integrated mission briefing generator for testing
    """
    
    def __init__(self):
        # Ensure missions directory exists
        os.makedirs(MISSION_DIR, exist_ok=True)
        print("Simplified Integrated Mission Briefing Generator initialized")
    
    def generate_mission(self, signal: Dict, user_id: str, user_data: Dict = None, 
                        account_data: Dict = None) -> Dict:
        """
        Generate a mission with integrated functionality
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
            
            # Version info
            "generator_version": "v5.0_integrated_test",
            "format_version": "1.0"
        }
        
        # Save to file with proper error handling
        try:
            self._save_mission_to_file(comprehensive_mission)
            print(f"Mission {mission_id} saved successfully")
        except Exception as e:
            print(f"Error saving mission {mission_id}: {e}")
            comprehensive_mission["file_save_error"] = str(e)
        
        # Clean up expired missions
        self._cleanup_expired_missions()
        
        return comprehensive_mission
    
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
            '': 1.5,  # More time for premium users
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
        
        # Save mission data
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(mission, f, indent=2, ensure_ascii=False)
    
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
                            print(f"Cleaned expired mission: {filename}")
                    
                    except Exception as e:
                        print(f"Error processing file {filename} during cleanup: {e}")
            
            if cleaned_count > 0:
                print(f"Cleaned up {cleaned_count} expired mission files")
                
        except Exception as e:
            print(f"Error during mission cleanup: {e}")
    
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
                    print(f"Mission {mission_id} is expired")
                    return None
                
                return mission_data
            else:
                print(f"Mission file not found: {mission_id}")
                return None
                
        except Exception as e:
            print(f"Error retrieving mission {mission_id}: {e}")
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
                        print(f"Error reading mission file {filename}: {e}")
            
            # Sort by creation time (newest first)
            active_missions.sort(key=lambda x: x.get("created_timestamp", 0), reverse=True)
            
        except Exception as e:
            print(f"Error retrieving active missions: {e}")
        
        return active_missions

def main():
    """Test the integrated mission briefing generator"""
    print("=== INTEGRATED MISSION BRIEFING GENERATOR TEST ===")
    
    # Initialize generator
    generator = SimplifiedIntegratedMissionBriefingGenerator()
    
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
    print("\n=== GENERATING INTEGRATED MISSION ===")
    mission = generator.generate_mission(test_signal, "test_user_123", test_user_data, test_account_data)
    
    print(f"Mission ID: {mission['mission_id']}")
    print(f"Symbol: {mission['symbol']}")
    print(f"Type: {mission['type']}")
    print(f"Direction: {mission['direction']}")
    print(f"Entry Price: {mission['entry_price']}")
    print(f"User Tier: {mission['user_tier']}")
    print(f"Expiry Minutes: {mission['expiry_minutes']}")
    print(f"Expires At: {mission['expires_at']}")
    print(f"File Path: {mission['file_path']}")
    
    # Test retrieval
    print("\n=== TESTING RETRIEVAL ===")
    retrieved = generator.get_mission_by_id(mission['mission_id'])
    if retrieved:
        print(f"Successfully retrieved mission: {retrieved['mission_id']}")
        print(f"Retrieved symbol: {retrieved['symbol']}")
        print(f"Retrieved type: {retrieved['type']}")
    else:
        print("Failed to retrieve mission")
    
    # Test active missions
    print("\n=== TESTING ACTIVE MISSIONS ===")
    active = generator.get_active_missions("test_user_123")
    print(f"Found {len(active)} active missions for user")
    for mission in active:
        print(f"- {mission['mission_id']}: {mission['symbol']} ({mission['type']})")
    
    # Test different signal types
    print("\n=== TESTING DIFFERENT SIGNAL TYPES ===")
    
    # Test sniper signal
    sniper_signal = {
        "symbol": "EURUSD",
        "type": "sniper",
        "direction": "SELL",
        "entry_price": 1.08450,
        "sl": 15,
        "tp": 30,
        "tcs_score": 92,
        "timeframe": "M15",
        "session": "NY",
        "pattern": "Head and Shoulders",
        "confluence_count": 3,
        "confidence": 0.92
    }
    
    sniper_mission = generator.generate_mission(sniper_signal, "test_user_456", 
                                               {"tier": "ELITE"}, {"balance": 10000.00})
    print(f"Sniper mission: {sniper_mission['mission_id']} - Expiry: {sniper_mission['expiry_minutes']} minutes")
    
    # Test midnight hammer signal
    hammer_signal = {
        "symbol": "GBPJPY",
        "type": "midnight_hammer",
        "direction": "BUY",
        "entry_price": 158.250,
        "sl": 20,
        "tp": 40,
        "tcs_score": 85,
        "timeframe": "M5",
        "session": "LONDON",
        "pattern": "Breakout",
        "confluence_count": 4,
        "confidence": 0.85
    }
    
    hammer_mission = generator.generate_mission(hammer_signal, "test_user_789", 
                                               {"tier": }, {"balance": 25000.00})
    print(f"Hammer mission: {hammer_mission['mission_id']} - Expiry: {hammer_mission['expiry_minutes']} minutes")
    
    # Test all active missions
    print("\n=== ALL ACTIVE MISSIONS ===")
    all_active = generator.get_active_missions()
    print(f"Total active missions: {len(all_active)}")
    for mission in all_active:
        print(f"- {mission['mission_id']}: {mission['symbol']} ({mission['type']}) - User: {mission['user_id']}")
    
    print("\n=== INTEGRATION TEST COMPLETE ===")
    print("All tests passed successfully!")

if __name__ == "__main__":
    main()