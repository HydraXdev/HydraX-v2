"""
BITTEN Tier Mapping Configuration
Standardizes tier naming across the codebase
"""

# Official tier names (use these everywhere)
class TierNames:
    PRESS_PASS = "PRESS_PASS"  # 7-day trial
    NIBBLER = "NIBBLER"        # $39/month
    FANG = "FANG"              # $89/month
    COMMANDER = "COMMANDER"    # $139/month
    APEX = "APEX"              # $188/month (includes all COMMANDER features + exclusives)
    
    # List for validation
    ALL_TIERS = [PRESS_PASS, NIBBLER, FANG, COMMANDER, APEX]
    PAID_TIERS = [NIBBLER, FANG, COMMANDER, APEX]
    
    # Tier hierarchy (for access control)
    TIER_HIERARCHY = {
        PRESS_PASS: 0,
        NIBBLER: 1,
        FANG: 2,
        COMMANDER: 3,
        APEX: 4  # Highest level (COMMANDER + APEX addon)
    }


# Legacy mapping (for migration only)
LEGACY_TO_NEW = {
    "tier_1": TierNames.NIBBLER,
    "tier_2": TierNames.FANG,
    "tier_3": TierNames.COMMANDER,
    "tier_4": TierNames.APEX,
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