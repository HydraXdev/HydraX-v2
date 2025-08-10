#!/usr/bin/env python3
"""
🎯 OPTIMIZED SIGNAL SYSTEM - Scalable for 5,000+ Users
Instead of creating individual mission files, we create ONE signal file
and apply user-specific overlays at runtime
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

class OptimizedSignalSystem:
    """
    Scalable signal system that creates ONE signal file per signal,
    not thousands of personalized copies
    """
    
    def __init__(self):
        self.signals_dir = "/root/HydraX-v2/signals/shared/"
        self.user_overlays_dir = "/root/HydraX-v2/user_overlays/"
        os.makedirs(self.signals_dir, exist_ok=True)
        os.makedirs(self.user_overlays_dir, exist_ok=True)
    
    def save_shared_signal(self, signal_data: Dict) -> str:
        """
        Save ONE shared signal file that all users reference
        Size: ~1-2 KB per signal (not per user!)
        """
        signal_id = signal_data['signal_id']
        signal_file = f"{self.signals_dir}{signal_id}.json"
        
        # Store only the universal signal data
        shared_data = {
            'signal_id': signal_id,
            'symbol': signal_data['symbol'],
            'direction': signal_data['direction'],
            'entry_price': signal_data['entry_price'],
            'stop_loss': signal_data['stop_loss'],
            'take_profit': signal_data['take_profit'],
            'pattern_type': signal_data.get('pattern_type'),
            'confidence': signal_data.get('confidence', 75),
            'citadel_score': signal_data.get('citadel_score', 7.0),
            'citadel_insights': signal_data.get('citadel_insights'),
            'session': signal_data.get('session'),
            'expires_timestamp': signal_data.get('expires_timestamp'),
            'created_timestamp': signal_data.get('created_timestamp', int(datetime.now().timestamp()))
        }
        
        with open(signal_file, 'w') as f:
            json.dump(shared_data, f, compact=True)  # Compact JSON to save space
        
        return signal_id
    
    def get_user_overlay(self, user_id: str) -> Dict:
        """
        Get or create minimal user overlay data
        This is cached and only updated when user data changes
        Size: ~200-300 bytes per user (one-time storage)
        """
        overlay_file = f"{self.user_overlays_dir}{user_id}.json"
        
        if os.path.exists(overlay_file):
            with open(overlay_file, 'r') as f:
                return json.load(f)
        
        # Default overlay for new users
        default_overlay = {
            'user_id': user_id,
            'tier': 'NIBBLER',
            'risk_percent': 2.0,
            'account_balance': 10000,  # Updated via API when needed
            'win_rate': 0,
            'trades_remaining': 5
        }
        
        # Cache it
        with open(overlay_file, 'w') as f:
            json.dump(default_overlay, f, compact=True)
        
        return default_overlay
    
    def build_mission_view(self, signal_id: str, user_id: str) -> Dict:
        """
        Combine shared signal + user overlay at runtime
        No storage needed - computed on demand!
        """
        # Load shared signal (cached in memory in production)
        signal_file = f"{self.signals_dir}{signal_id}.json"
        if not os.path.exists(signal_file):
            return None
        
        with open(signal_file, 'r') as f:
            signal_data = json.load(f)
        
        # Get user overlay (cached in memory in production)
        user_overlay = self.get_user_overlay(user_id)
        
        # Calculate user-specific values at runtime
        account_balance = user_overlay['account_balance']
        risk_amount = account_balance * (user_overlay['risk_percent'] / 100)
        
        # Estimate position size (simplified)
        sl_pips = abs(signal_data['entry_price'] - signal_data['stop_loss']) * 10000
        position_size = round(risk_amount / (sl_pips * 10), 2)
        
        # Build complete mission view (no storage, just computation)
        return {
            **signal_data,  # All shared signal data
            'user': {
                'user_id': user_id,
                'tier': user_overlay['tier'],
                'account_balance': account_balance,
                'position_size': position_size,
                'risk_amount': risk_amount,
                'win_rate': user_overlay['win_rate'],
                'trades_remaining': user_overlay['trades_remaining']
            }
        }

# STORAGE COMPARISON:
# Old way: 30 signals × 5000 users = 150,000 files = 450 MB/day
# New way: 30 signals + 5000 user overlays (one-time) = 30 files/day + 5000 cached = ~2 MB/day
# SAVINGS: 99.5% storage reduction!