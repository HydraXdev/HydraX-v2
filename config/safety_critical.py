"""
CRITICAL SAFETY CONFIGURATION
DO NOT MODIFY WITHOUT UNDERSTANDING CONSEQUENCES
"""

# CRITICAL: NEVER use demo/fake data in production
ALLOW_DEMO_DATA = False

# CRITICAL: Require real MT5 connection for signals
REQUIRE_MT5_CONNECTION = True

# CRITICAL: Stop all signals if MT5 disconnected
HALT_ON_DISCONNECT = True

# CRITICAL: Maximum time to wait for MT5 data (seconds)
MT5_TIMEOUT = 10

# CRITICAL: Minimum data points required for signal generation
MIN_BARS_REQUIRED = 100

# CRITICAL: Safety checks before signal generation
SAFETY_CHECKS = {
    'verify_mt5_connection': True,
    'verify_real_data': True,
    'verify_spreads': True,
    'verify_timestamps': True,
    'prevent_stale_data': True
}

# CRITICAL: Maximum age of data before considered stale (seconds)
MAX_DATA_AGE = 300  # 5 minutes

# CRITICAL: Emergency stop conditions
EMERGENCY_STOP_CONDITIONS = {
    'no_mt5_data': True,
    'stale_data': True,
    'abnormal_spreads': True,
    'connection_lost': True
}

# CRITICAL: Open position handling during disconnect
OPEN_POSITION_HANDLING = {
    'close_all_on_disconnect': False,  # NO! Let them run
    'allow_natural_exit': True,         # Let SL/TP work
    'panic_close': False,               # Never panic
    'trust_the_math': True              # 75%+ win rate
}

# CRITICAL: Logging for safety events
LOG_SAFETY_EVENTS = True
SAFETY_LOG_FILE = 'logs/safety_critical.log'

# CRITICAL: Alert on safety violations
ALERT_ON_SAFETY_VIOLATION = True

def verify_safety_conditions(data):
    """
    Verify all safety conditions before allowing signals
    
    Returns:
        (bool, str): (is_safe, reason_if_not_safe)
    """
    if not data:
        return False, "No MT5 data available"
    
    # Check data freshness
    for pair, df in data.items():
        if hasattr(df, 'index') and len(df) > 0:
            latest_time = df.index[-1]
            age = (datetime.now() - latest_time).total_seconds()
            if age > MAX_DATA_AGE:
                return False, f"Data for {pair} is stale ({age}s old)"
    
    return True, "All safety checks passed"