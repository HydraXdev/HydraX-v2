"""
BITTEN Fire Mode Configuration
Defines signal access and execution modes by tier
"""

class FireModeConfig:
    """Fire mode access control by tier"""
    
    # TCS Thresholds (dynamically adjustable)
    TCS_THRESHOLDS = {
        "RAPID_ASSAULT": 60,  # Adjusted for NIBBLER behavioral strategies (user request)
        "SNIPER_OPS": 87,     # Currently testing at 87%
        "MIDNIGHT_HAMMER": 92  # Special occasion shots (future)
    }
    
    # Signal Access by Tier
    SIGNAL_ACCESS = {
        "PRESS_PASS": {
            "view": ["RAPID_ASSAULT"],  # Can only view RAPID ASSAULT
            "execute": ["RAPID_ASSAULT"],  # Same execution as NIBBLER
            "fire_modes": ["SELECT"],  # SELECT FIRE execution only
            "voice_enabled": "NEXUS_ONLY",  # Only SERGEANT NEXUS speaks during trial
            "forced_personality": "NEXUS"  # Trial users always get SERGEANT NEXUS (The Recruiter Protocol)
        },
        "NIBBLER": {
            "view": ["RAPID_ASSAULT", "SNIPER_OPS"],  # Can view both
            "execute": ["RAPID_ASSAULT"],  # SELECT FIRE execution only
            "fire_modes": ["SELECT"],
            "max_concurrent_trades": 1,  # 1 trade slot
            "voice_enabled": True  # Voice personalities available
        },
        "FANG": {
            "view": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "execute": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],  # All signals
            "fire_modes": ["SELECT"],  # SELECT FIRE only
            "max_concurrent_trades": 2,  # 2 trade slots
            "voice_enabled": True  # Voice personalities available
        },
        "COMMANDER": {
            "view": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "execute": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "fire_modes": ["SELECT", "AUTO"],  # Full fire selector switch
            "auto_execution": True,  # Full autonomous slot-based execution
            "max_auto_slots": 3,  # COMMANDER gets 3 auto slots
            "max_concurrent_trades": "unlimited",  # Unlimited concurrent trades
            "voice_enabled": True,  # Voice personalities available
            "exclusive_features": ["UNLIMITED_TRADES", "PRIORITY_SUPPORT", "EXCLUSIVE_SIGNALS", "ADVANCED_ANALYTICS", "PRIORITY_SIGNALS"]  # All premium features
        }
    }
    
    # Fire Mode Descriptions
    FIRE_MODE_DESC = {
        "SELECT": "One-click confirmation for each trade",
        "AUTO": "Autonomous slot-based execution - trades drop into available slots automatically"
    }
    
    # Execution Rules
    EXECUTION_RULES = {
        "AUTO": {
            "description": "When a slot opens, next available signal executes automatically",
            "requirements": ["COMMANDER"],  # Only COMMANDER gets AUTO mode
            "slot_based": True,
            "manual_override": True  # Can switch to SELECT for manual control
        }
    }
    
    @classmethod
    def can_execute_signal(cls, user_tier: str, signal_type: str) -> bool:
        """Check if user tier can execute signal type"""
        tier_config = cls.SIGNAL_ACCESS.get(user_tier, {})
        return signal_type in tier_config.get("execute", [])
    
    @classmethod
    def can_view_signal(cls, user_tier: str, signal_type: str) -> bool:
        """Check if user tier can view signal type"""
        tier_config = cls.SIGNAL_ACCESS.get(user_tier, {})
        return signal_type in tier_config.get("view", [])
    
    @classmethod
    def get_fire_modes(cls, user_tier: str) -> list:
        """Get available fire modes for tier"""
        tier_config = cls.SIGNAL_ACCESS.get(user_tier, {})
        return tier_config.get("fire_modes", ["SELECT"])
    
    @classmethod
    def has_auto_execution(cls, user_tier: str) -> bool:
        """Check if tier has auto execution capability"""
        tier_config = cls.SIGNAL_ACCESS.get(user_tier, {})
        return tier_config.get("auto_execution", False)