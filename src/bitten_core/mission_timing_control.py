#!/usr/bin/env python3
"""
Mission Timing Control System
Enforces timeboxing and one-at-a-time trading rules
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MissionTimingControl:
    """Controls mission timing and position limits"""
    
    def __init__(self):
        self.mission_dir = Path("/root/HydraX-v2/missions")
        self.user_missions_dir = Path("/root/HydraX-v2/user_missions")
        self.active_positions_file = Path("/root/HydraX-v2/active_positions.json")
        
        # Timing rules (in minutes)
        self.timing_rules = {
            "RAPID_ASSAULT": {
                "max_duration": 60,      # 1 hour for scalp
                "warning_at": 50,        # Warning at 50 minutes
                "auto_cancel": 65        # Force cancel at 65 minutes
            },
            "PRECISION_STRIKE": {
                "max_duration": 120,     # 2 hours for sniper
                "warning_at": 110,       # Warning at 1h50m
                "auto_cancel": 125       # Force cancel at 2h5m
            }
        }
        
        # Position limits by tier
        self.position_limits = {
            "PRESS_PASS": 1,
            "NIBBLER": 1,      # ONE AT A TIME for lower tiers
            "FANG": 1,         # ONE AT A TIME enforcement
            "COMMANDER": 2     # Allow 2 concurrent for COMMANDER only
        }
        
        self._ensure_tracking_files()
        
    def _ensure_tracking_files(self):
        """Ensure tracking files exist"""
        if not self.active_positions_file.exists():
            with open(self.active_positions_file, 'w') as f:
                json.dump({}, f)
                
    def can_open_position(self, user_id: str, user_tier: str = "NIBBLER") -> tuple[bool, str]:
        """
        Check if user can open a new position (ONE AT A TIME enforcement)
        Returns: (can_open, reason)
        """
        active_positions = self._get_active_positions()
        user_positions = active_positions.get(str(user_id), [])
        
        # Remove expired positions
        user_positions = self._clean_expired_positions(user_positions)
        
        # Get position limit for tier
        max_positions = self.position_limits.get(user_tier, 1)
        
        # Check current position count
        current_count = len(user_positions)
        
        if current_count >= max_positions:
            active_ids = [p['signal_id'] for p in user_positions]
            return False, f"⚠️ ONE AT A TIME: You have {current_count} active position(s): {', '.join(active_ids[:3])}. Close or wait for timeout."
            
        return True, "✅ Position slot available"
        
    def register_position(self, user_id: str, signal_id: str, signal_type: str = "RAPID_ASSAULT"):
        """Register a new active position"""
        active_positions = self._get_active_positions()
        user_id = str(user_id)
        
        if user_id not in active_positions:
            active_positions[user_id] = []
            
        # Add new position with timestamp
        active_positions[user_id].append({
            "signal_id": signal_id,
            "signal_type": signal_type,
            "opened_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=self.timing_rules[signal_type]["auto_cancel"])).isoformat()
        })
        
        # Save updated positions
        self._save_active_positions(active_positions)
        logger.info(f"Registered position {signal_id} for user {user_id}")
        
    def close_position(self, user_id: str, signal_id: str):
        """Close an active position"""
        active_positions = self._get_active_positions()
        user_id = str(user_id)
        
        if user_id in active_positions:
            active_positions[user_id] = [
                p for p in active_positions[user_id] 
                if p['signal_id'] != signal_id
            ]
            
            if not active_positions[user_id]:
                del active_positions[user_id]
                
            self._save_active_positions(active_positions)
            logger.info(f"Closed position {signal_id} for user {user_id}")
            
    def check_position_expiry(self, signal_id: str) -> tuple[bool, str]:
        """
        Check if a position should be expired
        Returns: (should_expire, reason)
        """
        # Find the position across all users
        active_positions = self._get_active_positions()
        
        for user_id, positions in active_positions.items():
            for pos in positions:
                if pos['signal_id'] == signal_id:
                    expires_at = datetime.fromisoformat(pos['expires_at'])
                    now = datetime.now()
                    
                    if now >= expires_at:
                        return True, f"Position expired after {self.timing_rules[pos['signal_type']]['auto_cancel']} minutes"
                        
                    # Check if warning needed
                    opened_at = datetime.fromisoformat(pos['opened_at'])
                    minutes_open = (now - opened_at).total_seconds() / 60
                    warning_minutes = self.timing_rules[pos['signal_type']]['warning_at']
                    
                    if minutes_open >= warning_minutes:
                        remaining = (expires_at - now).total_seconds() / 60
                        return False, f"⚠️ Position expires in {int(remaining)} minutes"
                        
        return False, "Position not found or not expired"
        
    def get_user_positions(self, user_id: str) -> List[Dict]:
        """Get all active positions for a user"""
        active_positions = self._get_active_positions()
        user_positions = active_positions.get(str(user_id), [])
        
        # Clean expired and return
        return self._clean_expired_positions(user_positions)
        
    def _clean_expired_positions(self, positions: List[Dict]) -> List[Dict]:
        """Remove expired positions from list"""
        now = datetime.now()
        active = []
        
        for pos in positions:
            expires_at = datetime.fromisoformat(pos['expires_at'])
            if now < expires_at:
                active.append(pos)
            else:
                logger.info(f"Auto-expiring position {pos['signal_id']}")
                
        return active
        
    def _get_active_positions(self) -> Dict:
        """Load active positions from file"""
        try:
            with open(self.active_positions_file, 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def _save_active_positions(self, positions: Dict):
        """Save active positions to file"""
        with open(self.active_positions_file, 'w') as f:
            json.dump(positions, f, indent=2)
            
    def enforce_auto_cancel(self):
        """
        Background task to auto-cancel overdue positions
        Should be called periodically (every minute)
        """
        active_positions = self._get_active_positions()
        updated = False
        
        for user_id, positions in list(active_positions.items()):
            cleaned = self._clean_expired_positions(positions)
            
            if len(cleaned) != len(positions):
                updated = True
                if cleaned:
                    active_positions[user_id] = cleaned
                else:
                    del active_positions[user_id]
                    
        if updated:
            self._save_active_positions(active_positions)
            logger.info("Auto-cancel sweep completed")
            
    def get_position_status(self, signal_id: str) -> Dict:
        """Get detailed status of a position"""
        active_positions = self._get_active_positions()
        
        for user_id, positions in active_positions.items():
            for pos in positions:
                if pos['signal_id'] == signal_id:
                    opened_at = datetime.fromisoformat(pos['opened_at'])
                    expires_at = datetime.fromisoformat(pos['expires_at'])
                    now = datetime.now()
                    
                    minutes_open = (now - opened_at).total_seconds() / 60
                    minutes_remaining = (expires_at - now).total_seconds() / 60
                    
                    return {
                        "signal_id": signal_id,
                        "user_id": user_id,
                        "signal_type": pos['signal_type'],
                        "opened_at": pos['opened_at'],
                        "expires_at": pos['expires_at'],
                        "minutes_open": round(minutes_open, 1),
                        "minutes_remaining": round(minutes_remaining, 1),
                        "status": "ACTIVE" if minutes_remaining > 0 else "EXPIRED",
                        "warning": minutes_open >= self.timing_rules[pos['signal_type']]['warning_at']
                    }
                    
        return {"status": "NOT_FOUND"}

# Singleton instance
mission_timing = MissionTimingControl()

if __name__ == "__main__":
    # Test the system
    mtc = MissionTimingControl()
    
    # Test position limit check
    can_open, reason = mtc.can_open_position("123456", "NIBBLER")
    print(f"Can open: {can_open}, Reason: {reason}")
    
    # Test registration
    if can_open:
        mtc.register_position("123456", "TEST_SIGNAL_001", "RAPID_ASSAULT")
        print("Position registered")
        
        # Check again (should fail for ONE AT A TIME)
        can_open, reason = mtc.can_open_position("123456", "NIBBLER")
        print(f"Can open another: {can_open}, Reason: {reason}")
        
    # Check status
    status = mtc.get_position_status("TEST_SIGNAL_001")
    print(f"Position status: {status}")