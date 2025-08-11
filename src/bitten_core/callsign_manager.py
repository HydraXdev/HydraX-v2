#!/usr/bin/env python3
"""
BITTEN Callsign Manager
Handles user screen names/gamer tags for subscribed users
"""

import re
import random
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class CallsignManager:
    """Manages user callsigns/screen names"""
    
    def __init__(self):
        from src.bitten_core.central_user_manager import get_central_user_manager
        self.user_mgr = get_central_user_manager()
        
        # Callsign validation rules
        self.MIN_LENGTH = 3
        self.MAX_LENGTH = 20
        self.CHANGE_COOLDOWN_DAYS = 7  # Can only change once per week
        
        # Reserved/banned words
        self.RESERVED_WORDS = {
            'admin', 'commander', 'bitten', 'system', 'bot', 'official',
            'moderator', 'mod', 'staff', 'support', 'help', 'test'
        }
        
        # Cool default suggestions for new users
        self.CALLSIGN_PREFIXES = [
            'Shadow', 'Ghost', 'Viper', 'Hawk', 'Wolf', 'Eagle', 'Cobra',
            'Storm', 'Thunder', 'Lightning', 'Blade', 'Razor', 'Phoenix',
            'Titan', 'Reaper', 'Hunter', 'Striker', 'Sniper', 'Phantom'
        ]
        
        self.CALLSIGN_SUFFIXES = [
            'Alpha', 'Bravo', 'Delta', 'Echo', 'Omega', 'Prime', 'Elite',
            '001', '007', '117', '420', '666', '777', '999', 
            'X', 'Z', 'One', 'Zero', 'Max', 'Pro', 'God'
        ]
    
    def can_set_callsign(self, telegram_id: int) -> Tuple[bool, str]:
        """
        Check if user can set/change their callsign
        Returns (can_set, reason_message)
        """
        user = self.user_mgr.get_complete_user(telegram_id)
        
        if not user:
            return False, "User not found"
        
        # Check tier - only paid users can have callsigns
        tier = user.get('tier', 'PRESS_PASS')
        if tier == 'PRESS_PASS':
            return False, "🎮 Callsigns are available for subscribed members only. Upgrade to unlock your identity!"
        
        # Check cooldown for changes
        profile = user.get('profiles', {})
        current_callsign = profile.get('callsign')
        
        if current_callsign:
            # User already has a callsign - check cooldown
            last_change = profile.get('callsign_changed_at')
            if last_change:
                try:
                    last_change_dt = datetime.fromisoformat(last_change)
                    days_since_change = (datetime.now() - last_change_dt).days
                    
                    if days_since_change < self.CHANGE_COOLDOWN_DAYS:
                        days_left = self.CHANGE_COOLDOWN_DAYS - days_since_change
                        return False, f"⏰ Callsign can be changed in {days_left} days"
                except:
                    pass  # If date parsing fails, allow change
        
        return True, "Ready to set callsign"
    
    def validate_callsign(self, callsign: str) -> Tuple[bool, str]:
        """
        Validate a callsign string
        Returns (is_valid, error_message)
        """
        # Length check
        if len(callsign) < self.MIN_LENGTH:
            return False, f"Callsign too short (min {self.MIN_LENGTH} characters)"
        
        if len(callsign) > self.MAX_LENGTH:
            return False, f"Callsign too long (max {self.MAX_LENGTH} characters)"
        
        # Character check - alphanumeric, underscores, and hyphens only
        if not re.match(r'^[a-zA-Z0-9_-]+$', callsign):
            return False, "Callsign can only contain letters, numbers, underscores, and hyphens"
        
        # Reserved word check
        callsign_lower = callsign.lower()
        for reserved in self.RESERVED_WORDS:
            if reserved in callsign_lower:
                return False, f"Callsign contains reserved word: {reserved}"
        
        # Profanity check (basic)
        profanity_patterns = ['fuck', 'shit', 'ass', 'dick', 'cock', 'pussy', 'nigga', 'fag']
        for profanity in profanity_patterns:
            if profanity in callsign_lower:
                return False, "Callsign contains inappropriate content"
        
        return True, "Valid"
    
    def check_availability(self, callsign: str, exclude_telegram_id: Optional[int] = None) -> bool:
        """
        Check if a callsign is available (not taken by another user)
        """
        # This would need a database query to check uniqueness
        # For now, we'll allow duplicates but could enforce uniqueness later
        
        # TODO: Implement actual database check
        # SELECT telegram_id FROM user_profiles WHERE LOWER(callsign) = LOWER(?)
        # AND telegram_id != exclude_telegram_id
        
        return True  # For now, all validated callsigns are available
    
    def set_callsign(self, telegram_id: int, callsign: str) -> Tuple[bool, str]:
        """
        Set or update user's callsign
        Returns (success, message)
        """
        # Check if user can set callsign
        can_set, reason = self.can_set_callsign(telegram_id)
        if not can_set:
            return False, reason
        
        # Validate callsign
        is_valid, error_msg = self.validate_callsign(callsign)
        if not is_valid:
            return False, f"❌ {error_msg}"
        
        # Check availability
        if not self.check_availability(callsign, telegram_id):
            return False, "❌ This callsign is already taken. Choose another!"
        
        # Update in database
        try:
            from src.bitten_core.central_database_sqlite import get_central_database
            db = get_central_database()
            
            # Get current callsign for comparison
            user = self.user_mgr.get_complete_user(telegram_id)
            old_callsign = user.get('profiles', {}).get('callsign')
            
            # Update callsign and timestamp
            success = db.update_user(telegram_id, {
                'callsign': callsign,
                'callsign_changed_at': datetime.now().isoformat()
            }, 'user_profiles')
            
            if success:
                if old_callsign:
                    message = f"✅ Callsign changed from **{old_callsign}** to **{callsign}**!"
                else:
                    message = f"✅ Welcome to the battlefield, **{callsign}**!"
                
                # Award XP for first callsign
                if not old_callsign:
                    self.user_mgr.add_xp(telegram_id, 10, "Set callsign")
                
                logger.info(f"User {telegram_id} set callsign to: {callsign}")
                return True, message
            else:
                return False, "❌ Failed to update callsign. Try again later."
                
        except Exception as e:
            logger.error(f"Error setting callsign for {telegram_id}: {e}")
            return False, "❌ An error occurred. Please try again."
    
    def generate_suggestions(self, telegram_id: int) -> List[str]:
        """
        Generate cool callsign suggestions for a user
        """
        suggestions = []
        
        # Generate 5 random combinations
        for _ in range(5):
            prefix = random.choice(self.CALLSIGN_PREFIXES)
            suffix = random.choice(self.CALLSIGN_SUFFIXES)
            suggestions.append(f"{prefix}{suffix}")
        
        # Add one with user ID for uniqueness
        user = self.user_mgr.get_complete_user(telegram_id)
        if user:
            username = user.get('username', '')
            if username and len(username) >= 3:
                # Use first part of username
                base = username[:10] if len(username) > 10 else username
                suggestions.append(f"{base}_{random.randint(100, 999)}")
        
        return suggestions[:6]  # Return max 6 suggestions
    
    def get_callsign_or_default(self, telegram_id: int) -> str:
        """
        Get user's callsign or a default display name
        """
        user = self.user_mgr.get_complete_user(telegram_id)
        
        if not user:
            return f"User_{telegram_id}"
        
        # Check for callsign
        callsign = user.get('profiles', {}).get('callsign')
        if callsign:
            return callsign
        
        # Check tier - only show default for paid users
        tier = user.get('tier', 'PRESS_PASS')
        if tier == 'PRESS_PASS':
            # Press Pass users don't get callsigns
            username = user.get('username')
            if username:
                return f"@{username}"
            else:
                first_name = user.get('first_name', '')
                if first_name:
                    return first_name
                else:
                    return f"Operative_{telegram_id % 10000}"
        else:
            # Paid user without callsign yet
            return f"{tier}_{telegram_id % 10000}"
    
    def format_leaderboard_name(self, telegram_id: int) -> str:
        """
        Format user's display name for leaderboards
        Shows callsign for paid users, username for free users
        """
        user = self.user_mgr.get_complete_user(telegram_id)
        
        if not user:
            return "Unknown"
        
        tier = user.get('tier', 'PRESS_PASS')
        callsign = user.get('profiles', {}).get('callsign')
        
        if callsign and tier != 'PRESS_PASS':
            # Show callsign with tier badge
            tier_badges = {
                'NIBBLER': '🔰',
                'FANG': '⚔️',
                'COMMANDER': '👑'
            }
            badge = tier_badges.get(tier, '')
            return f"{badge} {callsign}"
        else:
            # Show username or first name
            username = user.get('username')
            if username:
                return f"@{username}"
            else:
                first_name = user.get('first_name', 'Operative')
                return first_name

# Singleton
_callsign_instance = None

def get_callsign_manager() -> CallsignManager:
    """Get singleton instance of callsign manager"""
    global _callsign_instance
    if _callsign_instance is None:
        _callsign_instance = CallsignManager()
    return _callsign_instance