#!/usr/bin/env python3
"""
BITTEN Training Academy - Lesson Day Advancement System
Advances users to the next lesson day based on engagement criteria
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_user_registry() -> Dict[str, Any]:
    """Load user registry from JSON file"""
    try:
        with open('/root/HydraX-v2/user_registry.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading user registry: {e}")
        return {}

def save_user_registry(registry: Dict[str, Any]) -> bool:
    """Save user registry to JSON file"""
    try:
        with open('/root/HydraX-v2/user_registry.json', 'w') as f:
            json.dump(registry, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving user registry: {e}")
        return False

def should_advance_lesson(training_data: Dict[str, Any]) -> bool:
    """
    Determine if user should advance to next lesson day
    
    Advancement Criteria:
    - User has opened at least 1 mission on current lesson day
    - At least 24 hours since last lesson access (prevents rushing)
    - User is not already graduated (lesson_day <= 10)
    """
    if not training_data:
        return False
        
    current_lesson = training_data.get('lesson_day', 1)
    missions_today = training_data.get('missions_opened_today', 0)
    last_access = training_data.get('last_lesson_access')
    
    # Already graduated
    if current_lesson > 10:
        return False
        
    # Must have opened at least 1 mission
    if missions_today < 1:
        return False
        
    # Check 24-hour cooldown (prevents lesson rushing)
    if last_access:
        try:
            last_access_time = datetime.fromisoformat(last_access.replace('Z', '+00:00'))
            now = datetime.now()
            hours_since_access = (now - last_access_time).total_seconds() / 3600
            
            # Must wait at least 20 hours before advancing (allows some flexibility)
            if hours_since_access < 20:
                return False
        except Exception as e:
            logger.warning(f"Error parsing last access time: {e}")
            # If we can't parse, allow advancement
            pass
    
    return True

def advance_user_lesson(user_id: str, training_data: Dict[str, Any]) -> Dict[str, Any]:
    """Advance user to next lesson day"""
    new_lesson_day = training_data.get('lesson_day', 1) + 1
    
    # Update training data
    updated_data = training_data.copy()
    updated_data.update({
        'lesson_day': new_lesson_day,
        'missions_opened_today': 0,  # Reset daily counter
        'lesson_progress': 'completed' if new_lesson_day > 10 else 'active',
        'academy_graduate': new_lesson_day > 10,
        'last_advancement': datetime.now().isoformat()
    })
    
    logger.info(f"Advanced user {user_id} from Day {training_data.get('lesson_day', 1)} to Day {new_lesson_day}")
    
    return updated_data

def check_all_users_for_advancement():
    """Check all users and advance those ready for next lesson"""
    registry = load_user_registry()
    changes_made = False
    
    for user_id, user_data in registry.items():
        if user_id == 'users':  # Skip the nested users object
            continue
            
        training_data = user_data.get('training_academy', {})
        
        if should_advance_lesson(training_data):
            updated_training = advance_user_lesson(user_id, training_data)
            registry[user_id]['training_academy'] = updated_training
            changes_made = True
            
            # Log graduation
            if updated_training.get('academy_graduate', False):
                logger.info(f"🎓 User {user_id} graduated from Training Academy!")
    
    if changes_made:
        if save_user_registry(registry):
            logger.info("User registry updated successfully")
        else:
            logger.error("Failed to save user registry updates")
    
    return changes_made

def manual_advance_user(user_id: str) -> bool:
    """Manually advance a specific user (admin function)"""
    registry = load_user_registry()
    
    if user_id not in registry:
        logger.error(f"User {user_id} not found")
        return False
        
    training_data = registry[user_id].get('training_academy', {})
    updated_training = advance_user_lesson(user_id, training_data)
    registry[user_id]['training_academy'] = updated_training
    
    return save_user_registry(registry)

if __name__ == "__main__":
    # Run the advancement check
    print("🎓 Checking Training Academy advancement eligibility...")
    changes = check_all_users_for_advancement()
    if changes:
        print("✅ User advancement completed")
    else:
        print("ℹ️ No users ready for advancement")