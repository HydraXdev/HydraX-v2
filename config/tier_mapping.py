"""
BITTEN Tier Mapping Configuration
Standardizes tier naming across the codebase
"""

# Official tier names (use these everywhere)
class TierNames:
    PRESS_PASS = "PRESS_PASS"  # 7-day trial
    NIBBLER = "NIBBLER"        # $39/month
    FANG = "FANG"              # $89/month
    COMMANDER = "COMMANDER"    # $189/month (premium tier with all features)
    
    # List for validation
    ALL_TIERS = [PRESS_PASS, NIBBLER, FANG, COMMANDER]
    PAID_TIERS = [NIBBLER, FANG, COMMANDER]
    
    # Tier hierarchy (for access control)
    TIER_HIERARCHY = {
        PRESS_PASS: 0,
        NIBBLER: 1,
        FANG: 2,
        COMMANDER: 3  # Highest level with all premium features
    }

# Legacy mapping (for migration only)
LEGACY_TO_NEW = {
    "tier_1": TierNames.NIBBLER,
    "tier_2": TierNames.FANG,
    "tier_3": TierNames.COMMANDER,
    "tier_4": TierNames.COMMANDER,  # migrates to COMMANDER
    : TierNames.COMMANDER,   # tier becomes COMMANDER
    "tier_general": None,  # Maps to no specific tier
    "TRIAL": TierNames.PRESS_PASS,
    "PRESS PASS": TierNames.PRESS_PASS,
    "FREE_TRIAL": TierNames.PRESS_PASS
}

def get_tier_name(legacy_name: str) -> str:
    """Convert legacy tier name to new standard name"""
    if legacy_name in TierNames.ALL_TIERS:
        return legacy_name  # Already using new name
    
    return LEGACY_TO_NEW.get(legacy_name, legacy_name)

def get_tier_level(tier_name: str) -> int:
    """Get numeric level for tier comparison"""
    tier_name = get_tier_name(tier_name)
    return TierNames.TIER_HIERARCHY.get(tier_name, -1)

def has_tier_access(user_tier: str, required_tier: str) -> bool:
    """Check if user tier has access to required tier features"""
    user_level = get_tier_level(user_tier)
    required_level = get_tier_level(required_tier)
    
    return user_level >= required_level