"""
BITTEN Bonus Management System
Handles special events, user bonuses, and achievement rewards
"""

import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class BonusManager:
    """Manages all bonus operations for the BITTEN system"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            '..', 
            'config', 
            'tier_settings.yml'
        )
        self.load_config()
    
    def load_config(self):
        """Load the current configuration"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def save_config(self):
        """Save the configuration back to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
    
    def activate_special_event(self, event_name: str) -> bool:
        """Activate a special event"""
        if event_name in self.config.get('special_events', {}):
            self.config['special_events'][event_name]['active'] = True
            self.save_config()
            return True
        return False
    
    def deactivate_special_event(self, event_name: str) -> bool:
        """Deactivate a special event"""
        if event_name in self.config.get('special_events', {}):
            self.config['special_events'][event_name]['active'] = False
            self.save_config()
            return True
        return False
    
    def create_special_event(self, event_name: str, event_data: Dict) -> bool:
        """Create a new special event"""
        if 'special_events' not in self.config:
            self.config['special_events'] = {}
        
        # Required fields
        required = ['start_datetime', 'end_datetime', 'eligible_tiers', 'bonuses', 'message']
        if not all(field in event_data for field in required):
            return False
        
        # Set default active state
        event_data['active'] = event_data.get('active', False)
        
        self.config['special_events'][event_name] = event_data
        self.save_config()
        return True
    
    def grant_user_bonus(self, user_id: int, bonus_type: str, duration_hours: int, bonuses: Dict, reason: str) -> str:
        """Grant a temporary bonus to a user"""
        user_id_str = str(user_id)
        
        # Initialize user bonuses if needed
        if 'user_bonuses' not in self.config:
            self.config['user_bonuses'] = {}
        if user_id_str not in self.config['user_bonuses']:
            self.config['user_bonuses'][user_id_str] = []
        
        # Create bonus entry
        bonus_id = f"{bonus_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        expires = datetime.now() + timedelta(hours=duration_hours)
        
        bonus_entry = {
            'id': bonus_id,
            'type': bonus_type,
            'active': True,
            'expires': expires.isoformat(),
            'bonuses': bonuses,
            'reason': reason
        }
        
        self.config['user_bonuses'][user_id_str].append(bonus_entry)
        self.save_config()
        
        return bonus_id
    
    def grant_achievement_bonus(self, user_id: int, achievement_name: str) -> Optional[str]:
        """Grant an achievement bonus from templates"""
        if achievement_name not in self.config.get('achievement_bonuses', {}):
            return None
        
        achievement = self.config['achievement_bonuses'][achievement_name]
        
        return self.grant_user_bonus(
            user_id=user_id,
            bonus_type='achievement',
            duration_hours=achievement.get('duration_hours', 24),
            bonuses=achievement['bonuses'],
            reason=achievement.get('message', f'Achievement: {achievement_name}')
        )
    
    def revoke_user_bonus(self, user_id: int, bonus_id: str) -> bool:
        """Revoke a specific user bonus"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.config.get('user_bonuses', {}):
            return False
        
        # Find and deactivate the bonus
        for bonus in self.config['user_bonuses'][user_id_str]:
            if bonus['id'] == bonus_id:
                bonus['active'] = False
                self.save_config()
                return True
        
        return False
    
    def cleanup_expired_bonuses(self):
        """Remove expired bonuses from all users"""
        if 'user_bonuses' not in self.config:
            return
        
        now = datetime.now()
        cleaned = 0
        
        for user_id_str, bonuses in self.config['user_bonuses'].items():
            # Keep only active, non-expired bonuses
            original_count = len(bonuses)
            self.config['user_bonuses'][user_id_str] = [
                bonus for bonus in bonuses
                if bonus.get('active', False) and 
                datetime.fromisoformat(bonus['expires']) > now
            ]
            cleaned += original_count - len(self.config['user_bonuses'][user_id_str])
        
        if cleaned > 0:
            self.save_config()
        
        return cleaned
    
    def get_user_bonuses(self, user_id: int) -> List[Dict]:
        """Get all active bonuses for a user"""
        user_id_str = str(user_id)
        bonuses = []
        
        # Cleanup expired first
        self.cleanup_expired_bonuses()
        
        # Get user bonuses
        if user_id_str in self.config.get('user_bonuses', {}):
            bonuses.extend([
                bonus for bonus in self.config['user_bonuses'][user_id_str]
                if bonus.get('active', False)
            ])
        
        return bonuses
    
    def get_active_events(self, tier: str = None) -> List[Dict]:
        """Get all active special events"""
        active_events = []
        now = datetime.now()
        
        for event_name, event_data in self.config.get('special_events', {}).items():
            if not event_data.get('active', False):
                continue
            
            # Check date range
            start = datetime.fromisoformat(event_data['start_datetime'])
            end = datetime.fromisoformat(event_data['end_datetime'])
            
            if start <= now <= end:
                if tier is None or tier in event_data.get('eligible_tiers', []):
                    active_events.append({
                        'name': event_name,
                        **event_data
                    })
        
        return active_events

# Example usage functions
def example_fourth_of_july_event():
    """Example: Create and activate Fourth of July event"""
    manager = BonusManager()
    
    # Create the event
    event_data = {
        'start_datetime': '2024-07-04 00:00:00',
        'end_datetime': '2024-07-04 23:59:59',
        'eligible_tiers': ['NIBBLER', 'FANG', 'COMMANDER', 'APEX'],
        'bonuses': {
            'risk_percent': 0.5,
            'daily_shots': 2,
            'positions': 0,
            'tcs_reduction': 0
        },
        'message': '🎆 Independence Day Special: +0.5% risk & 2 bonus shots!'
    }
    
    manager.create_special_event('fourth_of_july_2024', event_data)
    manager.activate_special_event('fourth_of_july_2024')
    
    print("Fourth of July event created and activated!")

def example_grant_win_streak_bonus(user_id: int):
    """Example: Grant a win streak bonus"""
    manager = BonusManager()
    
    bonus_id = manager.grant_user_bonus(
        user_id=user_id,
        bonus_type='win_streak',
        duration_hours=48,
        bonuses={
            'risk_percent': 0.25,
            'daily_shots': 3,
            'positions': 0,
            'tcs_reduction': 0
        },
        reason='5-day win streak! +0.25% risk & 3 bonus shots!'
    )
    
    print(f"Win streak bonus granted: {bonus_id}")

def example_grant_achievement(user_id: int):
    """Example: Grant an achievement bonus"""
    manager = BonusManager()
    
    # Grant the 'week_warrior' achievement
    bonus_id = manager.grant_achievement_bonus(user_id, 'week_warrior')
    
    if bonus_id:
        print(f"Week Warrior achievement granted: {bonus_id}")
    else:
        print("Achievement not found")