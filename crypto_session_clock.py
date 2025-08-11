# crypto_session_clock.py
import datetime as dt

# UTC session bands for crypto pacing (tune as needed)
# Asia   00:00–07:59, EU 08:00–13:59, US 14:00–21:59, Graveyard 22:00–23:59
def current_session(now=None):
    now = now or dt.datetime.utcnow()
    h = now.hour
    if 0 <= h < 8:   return 'ASIA'
    if 8 <= h < 14:  return 'EU'
    if 14 <= h < 22: return 'US'
    return 'GRAVEYARD'

def hours_left_active(now=None):
    now = now or dt.datetime.utcnow()
    # assume EU+US are main active blocks; return hours left in EU/US today
    h = now.hour + now.minute/60.0
    left = 0.0
    if h < 14:  left += (14 - max(h, 8)) if h < 14 else 0
    if h < 22:  left += (22 - max(h, 14)) if h < 22 else 0
    return max(0.25, left)  # avoid zero