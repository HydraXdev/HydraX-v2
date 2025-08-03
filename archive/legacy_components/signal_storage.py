"""
Signal storage module for BITTEN webapp
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from pathlib import Path

# Mission storage directory
MISSIONS_DIR = Path("/root/HydraX-v2/missions")
MISSIONS_DIR.mkdir(exist_ok=True)

def get_latest_signal() -> Optional[Dict]:
    """Get the most recent signal"""
    try:
        # Find the most recent mission file
        mission_files = list(MISSIONS_DIR.glob("*.json"))
        if not mission_files:
            return None
            
        latest_file = max(mission_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            mission = json.load(f)
            
        return {
            'id': mission.get('mission_id'),
            'symbol': mission.get('symbol'),
            'direction': mission.get('type'),
            'tcs_score': mission.get('tcs', 0),
            'timestamp': mission.get('timestamp', datetime.now().isoformat())
        }
    except Exception as e:
        print(f"Error getting latest signal: {e}")
        return None

def get_active_signals() -> List[Dict]:
    """Get all active signals (last 5 minutes)"""
    try:
        active_signals = []
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        for mission_file in MISSIONS_DIR.glob("*.json"):
            # Skip if file is older than 5 minutes
            if datetime.fromtimestamp(mission_file.stat().st_mtime) < cutoff_time:
                continue
                
            try:
                with open(mission_file, 'r') as f:
                    mission = json.load(f)
                    
                signal = {
                    'id': mission.get('mission_id'),
                    'symbol': mission.get('symbol'),
                    'direction': mission.get('type'),
                    'tcs_score': mission.get('tcs', 0),
                    'timestamp': mission.get('timestamp', datetime.now().isoformat())
                }
                active_signals.append(signal)
            except:
                continue
                
        # Sort by timestamp, newest first
        active_signals.sort(key=lambda x: x['timestamp'], reverse=True)
        return active_signals[:10]  # Return max 10 signals
        
    except Exception as e:
        print(f"Error getting active signals: {e}")
        return []

def get_signal_by_id(signal_id: str) -> Optional[Dict]:
    """Get a specific signal by ID"""
    try:
        # Try to find the mission file
        for mission_file in MISSIONS_DIR.glob("*.json"):
            try:
                with open(mission_file, 'r') as f:
                    mission = json.load(f)
                    
                if mission.get('mission_id') == signal_id:
                    # Extract data from the mission structure
                    signal_data = mission.get('signal', {})
                    enhanced_signal = mission.get('enhanced_signal', {})
                    timing = mission.get('timing', {})
                    
                    # Calculate expiry time
                    expires_at = timing.get('expires_at')
                    expiry_seconds = 0
                    if expires_at:
                        try:
                            from datetime import datetime
                            expiry_time = datetime.fromisoformat(expires_at)
                            expiry_seconds = max(0, int((expiry_time - datetime.now()).total_seconds()))
                        except:
                            expiry_seconds = 300  # Default 5 minutes
                    
                    return {
                        'id': mission.get('mission_id'),
                        'signal_id': mission.get('mission_id'),
                        'symbol': signal_data.get('symbol', enhanced_signal.get('symbol')),
                        'direction': signal_data.get('direction', enhanced_signal.get('direction')),
                        'signal_type': signal_data.get('signal_type', enhanced_signal.get('signal_type', 'STANDARD')),
                        'tcs_score': signal_data.get('tcs_score', enhanced_signal.get('tcs_score', 0)),
                        'entry': signal_data.get('entry_price', enhanced_signal.get('entry_price', 0)),
                        'sl': signal_data.get('stop_loss', enhanced_signal.get('stop_loss', 0)),
                        'tp': signal_data.get('take_profit', enhanced_signal.get('take_profit', 0)),
                        'rr_ratio': signal_data.get('risk_reward_ratio', enhanced_signal.get('risk_reward_ratio', 0)),
                        'timestamp': timing.get('created_at', datetime.now().isoformat()),
                        'expiry_seconds': expiry_seconds,
                        'expires_at': expires_at,
                        # Calculate pips (basic estimation)
                        'sl_pips': abs(signal_data.get('entry_price', 0) - signal_data.get('stop_loss', 0)) * 10000,
                        'tp_pips': abs(signal_data.get('take_profit', 0) - signal_data.get('entry_price', 0)) * 10000
                    }
            except Exception as e:
                print(f"Error processing mission file {mission_file}: {e}")
                continue
                
        return None
    except Exception as e:
        print(f"Error getting signal by id: {e}")
        return None