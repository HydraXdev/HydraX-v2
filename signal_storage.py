#!/usr/bin/env python3
"""Simple signal storage for webapp access"""

import json
import os
from datetime import datetime, timedelta

SIGNAL_FILE = "/root/HydraX-v2/latest_signals.json"

def save_signal(user_id, signal_data):
    """Save signal data for user"""
    # Load existing signals
    if os.path.exists(SIGNAL_FILE):
        with open(SIGNAL_FILE, 'r') as f:
            signals = json.load(f)
    else:
        signals = {}
    
    # Initialize user signals if needed
    if user_id not in signals:
        signals[user_id] = []
    
    # Add timestamp
    signal_data['timestamp'] = datetime.now().isoformat()
    
    # Add to user's signals (keep last 10)
    signals[user_id].insert(0, signal_data)
    signals[user_id] = signals[user_id][:10]
    
    # Clean old signals (older than 1 hour)
    cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
    for uid in signals:
        signals[uid] = [s for s in signals[uid] if s.get('timestamp', '') > cutoff]
    
    # Save
    with open(SIGNAL_FILE, 'w') as f:
        json.dump(signals, f, indent=2)
    
    return signal_data

def get_latest_signal(user_id):
    """Get latest signal for user"""
    if not os.path.exists(SIGNAL_FILE):
        return None
    
    with open(SIGNAL_FILE, 'r') as f:
        signals = json.load(f)
    
    user_signals = signals.get(user_id, [])
    if not user_signals:
        return None
    
    # Return latest non-expired signal
    now = datetime.now()
    for signal in user_signals:
        timestamp = datetime.fromisoformat(signal.get('timestamp', ''))
        if now - timestamp < timedelta(minutes=10):  # 10 min expiry
            return signal
    
    return None

def get_active_signals(user_id):
    """Get all active signals for user"""
    if not os.path.exists(SIGNAL_FILE):
        return []
    
    with open(SIGNAL_FILE, 'r') as f:
        signals = json.load(f)
    
    user_signals = signals.get(user_id, [])
    active = []
    
    now = datetime.now()
    for signal in user_signals:
        timestamp = datetime.fromisoformat(signal.get('timestamp', ''))
        if now - timestamp < timedelta(minutes=10):
            # Add time remaining
            remaining = 600 - int((now - timestamp).total_seconds())
            signal['time_remaining'] = max(0, remaining)
            active.append(signal)
    
    return active