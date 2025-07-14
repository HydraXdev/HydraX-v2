"""
BITTEN Fire Mode Configuration
Defines signal access and execution modes by tier
"""

class FireModeConfig:
    """Fire mode access control by tier"""
    
    # TCS Thresholds (dynamically adjustable)
    TCS_THRESHOLDS = {
        "RAPID_ASSAULT": 87,  # Currently testing at 87%
        "SNIPER_OPS": 87,     # Currently testing at 87%
        "MIDNIGHT_HAMMER": 92  # Special occasion shots (future)
    }
    
    # Signal Access by Tier
    SIGNAL_ACCESS = {
        "PRESS_PASS": {
            "view": ["RAPID_ASSAULT"],  # Can only view RAPID ASSAULT
            "execute": ["RAPID_ASSAULT"],  # Same execution as NIBBLER
            "fire_modes": ["MANUAL"]  # Manual execution only
        },
        "NIBBLER": {
            "view": ["RAPID_ASSAULT", "SNIPER_OPS"],  # Can view both
            "execute": ["RAPID_ASSAULT"],  # Manual execution only
            "fire_modes": ["MANUAL"]
        },
        "FANG": {
            "view": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "execute": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],  # All signals
            "fire_modes": ["MANUAL"]  # Manual only
        },
        "COMMANDER": {
            "view": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "execute": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "fire_modes": ["MANUAL", "SEMI_AUTO", "FULL_AUTO"],  # Fire selector switch
            "auto_execution": True  # Can use autonomous slot-based execution
        },
        "APEX": {
            "view": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "execute": ["RAPID_ASSAULT", "SNIPER_OPS", "MIDNIGHT_HAMMER"],
            "fire_modes": ["MANUAL", "SEMI_AUTO", "FULL_AUTO"],  # Same as COMMANDER
            "auto_execution": True,  # Same as COMMANDER
            "exclusive_features": ["ADVANCED_ANALYTICS", "PRIORITY_SIGNALS"]  # Future exclusives
        }
    }
    
    # Fire Mode Descriptions
    FIRE_MODE_DESC = {
        "MANUAL": "Click to execute each trade manually",
        "SEMI_AUTO": "Manual selection with assisted execution",
        "FULL_AUTO": "Autonomous slot-based execution - trades drop into available slots automatically"
    }
    
    # Execution Rules
    EXECUTION_RULES = {
        "FULL_AUTO": {
            "description": "When a slot opens, next available signal executes automatically",
            "requirements": ["COMMANDER", "APEX"],
            "slot_based": True,
            "manual_override": True  # Can switch to SEMI for manual control
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
        return tier_config.get("fire_modes", ["MANUAL"])
    
    @classmethod
    def has_auto_execution(cls, user_tier: str) -> bool:
        """Check if tier has auto execution capability"""
        tier_config = cls.SIGNAL_ACCESS.get(user_tier, {})
        return tier_config.get("auto_execution", False)