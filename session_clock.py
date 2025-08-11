# session_clock.py
import datetime as dt

def current_session(now=None):
    now = now or dt.datetime.utcnow()
    h = now.hour
    if 12 <= h < 15: return 'OVERLAP'  # 12–15 UTC
    if 7  <= h < 12: return 'LONDON'   # 07–12 UTC
    if 15 <= h < 20: return 'NY'       # 15–20 UTC
    return 'ASIAN'

def volatility_okay():
    # placeholder (engine has ATR checks already); keep True
    return True

def active_hours_remaining(now=None):
    """Calculate remaining active trading hours in current 24h period"""
    now = now or dt.datetime.utcnow()
    current_hour = now.hour
    
    # Count remaining hours in active sessions (LONDON, OVERLAP, NY)
    # Active hours: 7-20 UTC (13 hours total)
    if current_hour < 7:
        # Before London open, all active hours remain
        return 13.0
    elif 7 <= current_hour < 20:
        # During active sessions, calculate remaining
        return 20 - current_hour
    else:
        # After NY close, wait for next day
        return 7 + (24 - current_hour) + 13  # Hours until next London + active hours