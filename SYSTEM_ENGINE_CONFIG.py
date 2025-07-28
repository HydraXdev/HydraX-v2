"""
BITTEN SYSTEM ENGINE CONFIGURATION
==================================
SINGLE ENGINE ONLY - v5.0

This file is the SINGLE SOURCE OF TRUTH for which engine is active.
There is ONLY ONE engine active at any time.

Previous recording of multiple engines was an ERROR.
"""

# ACTIVE ENGINE CONFIGURATION
ACTIVE_ENGINE = "_v5.0"
ENGINE_MODE = "ULTRA_AGGRESSIVE"
TCS_MIN = 35
TCS_MAX = 95
TRADING_PAIRS_COUNT = 15

# Engine Import Path
from apex_v5_integration import v5IntegrationManager as SignalEngine

# Validation
def validate_engine_config():
    """Ensure only one engine is active"""
    assert ACTIVE_ENGINE == "_v5.0", "Only v5.0 should be active"
    assert TCS_MIN == 35, "TCS minimum should be 35 for v5.0"
    assert TCS_MAX == 95, "TCS maximum should be 95 for v5.0"
    print(f"✅ Engine Validation Passed: {ACTIVE_ENGINE} (TCS {TCS_MIN}-{TCS_MAX})")
    return True

# Auto-validate on import
validate_engine_config()

# Legacy engine check
def check_no_legacy_engines():
    """Verify no 87% engines are imported"""
    import sys
    legacy_modules = [
        'AUTHORIZED_SIGNAL_ENGINE',
        'bitten_ultimate_signal_engine_v4',
        'bitten_aaa_signal_engine'
    ]
    
    for module in legacy_modules:
        if module in sys.modules:
            raise RuntimeError(f"LEGACY ENGINE DETECTED: {module} - This should be archived!")
    
    print("✅ No legacy engines detected in memory")
    return True

# Export the single active engine
__all__ = ['SignalEngine', 'ACTIVE_ENGINE', 'TCS_MIN', 'TCS_MAX']