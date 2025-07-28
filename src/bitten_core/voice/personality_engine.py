#!/usr/bin/env python3
"""
🧠 BITTEN Personality Engine
Assigns, evolves, and manages user personality profiles with voice adaptation
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

from .voice_personality_map import (
    VOICE_PERSONALITY_MAP, 
    PERSONALITY_ASSIGNMENT_RULES, 
    EVOLUTION_TRIGGERS,
    calculate_personality_score,
    get_personality_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('PersonalityEngine')

class PersonalityEngine:
    """
    Core personality management system that handles:
    - Initial personality assignment
    - Behavioral analysis and adaptation
    - Voice evolution based on XP and usage
    - Mood state management
    """
    
    def __init__(self, profiles_path: str = "/root/HydraX-v2/data/user_voice_profiles.json"):
        self.profiles_path = Path(profiles_path)
        self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles = self.load_profiles()
        
        # Behavioral tracking
        self.behavior_history_path = self.profiles_path.parent / "user_behavior_history.json"
        self.behavior_history = self.load_behavior_history()
        
        # Evolution tracking
        self.evolution_log_path = self.profiles_path.parent / "personality_evolution_log.json"
        self.evolution_log = self.load_evolution_log()
        
    def load_profiles(self) -> Dict:
        """Load user voice profiles from JSON file"""
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading profiles: {e}")
                return {}
        return {}
    
    def save_profiles(self):
        """Save user voice profiles to JSON file"""
        try:
            with open(self.profiles_path, 'w') as f:
                json.dump(self.profiles, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")
    
    def load_behavior_history(self) -> Dict:
        """Load user behavior history"""
        if self.behavior_history_path.exists():
            try:
                with open(self.behavior_history_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading behavior history: {e}")
                return {}
        return {}
    
    def save_behavior_history(self):
        """Save user behavior history"""
        try:
            with open(self.behavior_history_path, 'w') as f:
                json.dump(self.behavior_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving behavior history: {e}")
    
    def load_evolution_log(self) -> List:
        """Load personality evolution log"""
        if self.evolution_log_path.exists():
            try:
                with open(self.evolution_log_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading evolution log: {e}")
                return []
        return []
    
    def save_evolution_log(self):
        """Save personality evolution log"""
        try:
            with open(self.evolution_log_path, 'w') as f:
                json.dump(self.evolution_log, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving evolution log: {e}")
    
    def analyze_user_behavior(self, user_id: str, message: str, action: str = None) -> Dict:
        """Analyze user behavior from message and actions"""
        user_id = str(user_id)
        
        # Initialize behavior tracking for new user
        if user_id not in self.behavior_history:
            self.behavior_history[user_id] = {
                "messages": [],
                "patterns": [],
                "traits": {},
                "last_updated": datetime.now().isoformat(),
                "interaction_count": 0
            }
        
        behavior = self.behavior_history[user_id]
        behavior["interaction_count"] += 1
        behavior["last_updated"] = datetime.now().isoformat()
        
        # Add message to history (keep last 50)
        behavior["messages"].append(message.lower())
        if len(behavior["messages"]) > 50:
            behavior["messages"] = behavior["messages"][-50:]
        
        # Analyze patterns from message
        patterns = self.extract_behavioral_patterns(message, action)
        for pattern in patterns:
            if pattern not in behavior["patterns"]:
                behavior["patterns"].append(pattern)
        
        # Update traits based on patterns
        self.update_user_traits(user_id, patterns)
        
        self.save_behavior_history()
        return behavior
    
    def extract_behavioral_patterns(self, message: str, action: str = None) -> List[str]:
        """Extract behavioral patterns from user message and actions"""
        patterns = []
        message_lower = message.lower()
        
        # Speed patterns
        if any(word in message_lower for word in ["fast", "quick", "now", "immediately"]):
            patterns.append("fast_execution")
        
        # Analytical patterns
        if any(word in message_lower for word in ["why", "how", "analyze", "explain", "understand"]):
            patterns.append("analytical")
        
        # Risk patterns
        if any(word in message_lower for word in ["risk", "safe", "careful", "cautious"]):
            patterns.append("risk_aware")
        elif any(word in message_lower for word in ["bold", "aggressive", "high", "max"]):
            patterns.append("risk_taking")
        
        # Social patterns
        if any(word in message_lower for word in ["team", "friends", "share", "invite"]):
            patterns.append("social_activity")
        
        # Learning patterns
        if any(word in message_lower for word in ["learn", "study", "educate", "teach"]):
            patterns.append("educational")
        
        # Precision patterns
        if any(word in message_lower for word in ["precise", "exact", "perfect", "sniper"]):
            patterns.append("precision_focused")
        
        # Action-based patterns
        if action:
            if action == "execute_trade":
                patterns.append("trading_active")
            elif action == "ask_question":
                patterns.append("question_heavy")
            elif action == "check_stats":
                patterns.append("data_focused")
        
        return patterns
    
    def update_user_traits(self, user_id: str, patterns: List[str]):
        """Update user personality traits based on behavioral patterns"""
        user_id = str(user_id)
        behavior = self.behavior_history[user_id]
        
        if "traits" not in behavior:
            behavior["traits"] = {}
        
        traits = behavior["traits"]
        
        # Update trait scores based on patterns
        trait_updates = {
            "fast_execution": {"speed": 0.1, "patience": -0.05},
            "analytical": {"precision": 0.1, "spontaneity": -0.05},
            "risk_aware": {"caution": 0.1, "aggression": -0.05},
            "risk_taking": {"aggression": 0.1, "caution": -0.05},
            "social_activity": {"sociability": 0.1, "isolation": -0.05},
            "educational": {"learning": 0.1, "impulsiveness": -0.05},
            "precision_focused": {"precision": 0.1, "casualness": -0.05}
        }
        
        for pattern in patterns:
            if pattern in trait_updates:
                for trait, change in trait_updates[pattern].items():
                    current_value = traits.get(trait, 0.0)
                    new_value = max(-1.0, min(1.0, current_value + change))
                    traits[trait] = new_value
    
    def assign_personality(self, user_id: str, user_tier: str = "NIBBLER", force_personality: str = None) -> str:
        """Assign personality to user based on behavior analysis"""
        user_id = str(user_id)
        
        if force_personality and force_personality in VOICE_PERSONALITY_MAP:
            assigned_personality = force_personality
        else:
            # Get user behavior data
            behavior = self.behavior_history.get(user_id, {})
            behavior["tier"] = user_tier
            
            # Calculate scores for each personality
            scores = {}
            for personality_name in VOICE_PERSONALITY_MAP.keys():
                scores[personality_name] = calculate_personality_score(behavior, personality_name)
            
            # Choose personality with highest score
            assigned_personality = max(scores, key=scores.get)
        
        # Get personality configuration
        personality_config = get_personality_config(assigned_personality, "default")
        
        # Create user profile
        profile = {
            "assigned_personality": assigned_personality,
            "voice_id": personality_config["voice_id"],
            "current_mood": "default",
            "energy": personality_config["current_mood"]["energy"],
            "humor": personality_config["current_mood"]["humor"],
            "aggression": personality_config["current_mood"]["aggression"],
            "voice_settings": personality_config["current_mood"]["voice_settings"],
            "xp_tier": user_tier,
            "assigned_at": datetime.now().isoformat(),
            "last_evolution": datetime.now().isoformat(),
            "evolution_stage": 0,
            "adaptation_factors": {
                "success_rate": 0.5,
                "engagement_level": 0.5,
                "interaction_frequency": 0.5
            }
        }
        
        self.profiles[user_id] = profile
        self.save_profiles()
        
        logger.info(f"Assigned personality {assigned_personality} to user {user_id}")
        return assigned_personality
    
    def evolve_personality(self, user_id: str, trigger_type: str, trigger_data: Dict) -> bool:
        """Evolve user's personality based on triggers"""
        user_id = str(user_id)
        
        if user_id not in self.profiles:
            return False
        
        profile = self.profiles[user_id]
        personality_name = profile["assigned_personality"]
        
        # Check if evolution is needed
        evolution_needed = False
        old_profile = profile.copy()
        
        if trigger_type == "tier_advancement":
            new_tier = trigger_data.get("new_tier")
            if new_tier != profile["xp_tier"]:
                tier_config = EVOLUTION_TRIGGERS["tier_advancement"].get(new_tier, {})
                if tier_config:
                    profile["xp_tier"] = new_tier
                    profile["current_mood"] = tier_config["mood"]
                    profile["evolution_stage"] = tier_config["evolution_factor"]
                    evolution_needed = True
        
        elif trigger_type == "behavior_adaptation":
            behavior_type = trigger_data.get("behavior_type")
            if behavior_type in EVOLUTION_TRIGGERS["behavior_adaptation"]:
                adaptations = EVOLUTION_TRIGGERS["behavior_adaptation"][behavior_type]
                for trait, change in adaptations.items():
                    if trait in profile:
                        profile[trait] = max(0.0, min(1.0, profile[trait] + change))
                        evolution_needed = True
        
        elif trigger_type == "interaction_patterns":
            pattern_type = trigger_data.get("pattern_type")
            if pattern_type in EVOLUTION_TRIGGERS["interaction_patterns"]:
                adaptations = EVOLUTION_TRIGGERS["interaction_patterns"][pattern_type]
                for trait, change in adaptations.items():
                    # Store interaction-based traits in adaptation_factors
                    if trait not in profile["adaptation_factors"]:
                        profile["adaptation_factors"][trait] = 0.5
                    profile["adaptation_factors"][trait] = max(0.0, min(1.0, 
                        profile["adaptation_factors"][trait] + change))
                    evolution_needed = True
        
        if evolution_needed:
            # Update personality configuration based on new mood
            personality_config = get_personality_config(personality_name, profile["current_mood"])
            profile["voice_settings"] = personality_config["current_mood"]["voice_settings"]
            profile["last_evolution"] = datetime.now().isoformat()
            
            # Log evolution
            evolution_entry = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "trigger_type": trigger_type,
                "trigger_data": trigger_data,
                "old_profile": old_profile,
                "new_profile": profile.copy(),
                "personality": personality_name
            }
            self.evolution_log.append(evolution_entry)
            self.save_evolution_log()
            
            self.profiles[user_id] = profile
            self.save_profiles()
            
            logger.info(f"Evolved personality for user {user_id} due to {trigger_type}")
            return True
        
        return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get complete user personality profile"""
        user_id = str(user_id)
        return self.profiles.get(user_id)
    
    def format_personality_message(self, user_id: str, message_text: str) -> Tuple[str, Dict]:
        """Format message with personality-specific styling and return voice settings"""
        user_id = str(user_id)
        profile = self.get_user_profile(user_id)
        
        if not profile:
            # Create default profile if doesn't exist
            self.assign_personality(user_id)
            profile = self.get_user_profile(user_id)
        
        personality_name = profile["assigned_personality"]
        
        # Get personality emoji and formatting
        personality_emojis = {
            "DRILL_SERGEANT": "🔥",
            "DOC_AEGIS": "🩺",
            "RECRUITER": "📣",
            "OVERWATCH": "🎯",
            "STEALTH": "🕶️"
        }
        
        # Format message with personality tag
        emoji = personality_emojis.get(personality_name, "🤖")
        tag = f"{emoji} **{personality_name}**"
        
        # Apply personality-specific formatting
        if personality_name == "DRILL_SERGEANT":
            formatted_message = f"{tag}\n{message_text.upper()}"
        elif personality_name == "DOC_AEGIS":
            formatted_message = f"{tag}\n*{message_text}*"
        elif personality_name == "RECRUITER":
            formatted_message = f"{tag}\n{message_text} 🎉"
        elif personality_name == "OVERWATCH":
            formatted_message = f"{tag}\n`{message_text}`"
        elif personality_name == "STEALTH":
            formatted_message = f"{tag}\n_{message_text}_"
        else:
            formatted_message = f"{tag}\n{message_text}"
        
        # Return formatted message and voice settings
        voice_settings = {
            "voice_id": profile["voice_id"],
            "voice_settings": profile["voice_settings"],
            "personality": personality_name,
            "energy": profile["energy"],
            "humor": profile["humor"]
        }
        
        return formatted_message, voice_settings
    
    def update_on_xp_change(self, user_id: str, new_xp: int, new_tier: str):
        """Update personality when user's XP or tier changes"""
        return self.evolve_personality(user_id, "tier_advancement", {
            "new_tier": new_tier,
            "new_xp": new_xp
        })
    
    def update_on_user_action(self, user_id: str, action: str, success: bool = True):
        """Update personality based on user actions"""
        # Determine behavior type from action
        behavior_mapping = {
            "trade_success": "high_success_rate",
            "trade_loss": "frequent_losses",
            "frequent_user": "long_term_user",
            "new_user": "new_user"
        }
        
        behavior_type = behavior_mapping.get(action)
        if behavior_type:
            return self.evolve_personality(user_id, "behavior_adaptation", {
                "behavior_type": behavior_type,
                "success": success
            })
        
        return False
    
    def get_personality_stats(self, user_id: str) -> Dict:
        """Get personality statistics for user"""
        user_id = str(user_id)
        profile = self.get_user_profile(user_id)
        behavior = self.behavior_history.get(user_id, {})
        
        if not profile:
            return {"error": "No personality profile found"}
        
        # Calculate evolution progress
        evolution_count = len([log for log in self.evolution_log if log["user_id"] == user_id])
        
        stats = {
            "personality": profile["assigned_personality"],
            "current_mood": profile["current_mood"],
            "evolution_stage": profile["evolution_stage"],
            "evolution_count": evolution_count,
            "interaction_count": behavior.get("interaction_count", 0),
            "traits": behavior.get("traits", {}),
            "adaptation_factors": profile.get("adaptation_factors", {}),
            "last_evolution": profile.get("last_evolution", "Never")
        }
        
        return stats

# Global personality engine instance
personality_engine = PersonalityEngine()