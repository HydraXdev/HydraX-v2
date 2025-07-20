#!/usr/bin/env python3
"""
User-Specific Mission System
Creates personalized missions for each user with their stats, tier, and fire package
"""

import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

class UserMissionSystem:
    """Creates personalized missions for each user"""
    
    def __init__(self):
        self.missions_dir = Path("/root/HydraX-v2/missions")
        self.missions_dir.mkdir(exist_ok=True)
        
        # TOC integration for real account data
        self.toc_url = "http://localhost:5000"
        
        # Sample user database - in production this would come from engagement_db
        self.users = {
            "7176191872": {
                "tier": "COMMANDER", 
                "daily_fires": 23,
                "daily_limit": 999,  # Unlimited for COMMANDER
                "win_rate": 78.5,
                "streak_days": 12,
                "total_pips": 1247.3,
                "rank": "VETERAN",
                "account_balance": 15750.25,  # Your real balance from TOC when available
                "risk_per_trade": 0.03,  # 3% for COMMANDER
                "live_testing": True  # Enable for live fire testing
            },
            "123456789": {  # Sample FANG user
                "tier": "FANG",
                "daily_fires": 8,
                "daily_limit": 15,
                "win_rate": 72.1,
                "streak_days": 3,
                "total_pips": 423.7,
                "rank": "SOLDIER",
                "account_balance": 2500.00,
                "risk_per_trade": 0.025  # 2.5% for FANG
            },
            "987654321": {  # Sample NIBBLER user
                "tier": "NIBBLER",
                "daily_fires": 3,
                "daily_limit": 5,
                "win_rate": 65.4,
                "streak_days": 1,
                "total_pips": 87.2,
                "rank": "RECRUIT",
                "account_balance": 500.00,
                "risk_per_trade": 0.02  # 2% for NIBBLER
            }
        }
    
    def create_user_missions(self, base_signal: Dict) -> Dict[str, str]:
        """Create personalized missions for all users from base signal"""
        
        mission_urls = {}
        engagement_count = 0
        
        # Generate base mission data
        signal_id = f"APEX5_{base_signal['symbol']}_{int(time.time())}"
        expiry_time = datetime.now() + timedelta(hours=4)  # 4-hour self-destruct for data efficiency
        
        for user_id, user_data in self.users.items():
            
            # Create user-specific mission ID
            user_mission_id = f"{signal_id}_USER{user_id}"
            
            # Get real account data from TOC if available, fallback to estimates
            account_data = self._get_account_via_toc(user_id) or self._estimate_account_data(user_data)
            
            # Calculate personalized risk/reward based on real account
            actual_balance = account_data.get('balance', user_data['account_balance'])
            risk_amount = actual_balance * user_data['risk_per_trade']
            
            # Calculate position size based on risk and signal
            stop_loss_pips = abs(base_signal['entry_price'] - base_signal['stop_loss']) * 10000
            pip_value = 10  # Simplified - would be calculated per pair
            position_size = risk_amount / (stop_loss_pips * pip_value) if stop_loss_pips > 0 else 0.01
            
            # Calculate reward
            take_profit_pips = abs(base_signal['take_profit'] - base_signal['entry_price']) * 10000
            reward_amount = position_size * take_profit_pips * pip_value
            
            # Create personalized mission
            user_mission = {
                "mission_id": user_mission_id,
                "base_signal_id": signal_id,
                "user_id": user_id,
                
                # Signal data
                "symbol": base_signal['symbol'],
                "direction": base_signal['direction'],
                "tcs_score": base_signal['tcs_score'],
                "entry_price": base_signal['entry_price'],
                "stop_loss": base_signal['stop_loss'],
                "take_profit": base_signal['take_profit'],
                "signal_type": base_signal.get('signal_type', 'RAPID_ASSAULT'),
                
                # User-specific data
                "user_tier": user_data['tier'],
                "user_rank": user_data['rank'],
                "daily_fires": user_data['daily_fires'],
                "ammo_left": max(0, user_data['daily_limit'] - user_data['daily_fires']),
                "win_rate": user_data['win_rate'],
                "streak_days": user_data['streak_days'],
                "total_pips": user_data['total_pips'],
                
                # Financial calculations (from TOC or estimates)
                "account_balance": actual_balance,
                "account_equity": account_data.get('equity', actual_balance),
                "margin_free": account_data.get('margin_free', actual_balance * 0.85),
                "risk_amount": round(risk_amount, 2),
                "reward_amount": round(reward_amount, 2),
                "risk_reward_ratio": round(reward_amount / risk_amount, 2) if risk_amount > 0 else 0,
                "position_size": round(position_size, 3),
                "risk_percentage": user_data['risk_per_trade'] * 100,
                
                # Mission metadata
                "created_at": datetime.now().isoformat(),
                "expires_at": expiry_time.isoformat(),
                "self_destruct_hours": 4,
                "status": "active",
                
                # Social elements (will be updated dynamically)
                "engagement_count": 0,  # Will be calculated in real-time
                "fired_count": 0
            }
            
            # Save user mission file
            mission_file = self.missions_dir / f"{user_mission_id}.json"
            with open(mission_file, 'w') as f:
                json.dump(user_mission, f, indent=2)
            
            # Create personalized URL
            mission_urls[user_id] = f"https://joinbitten.com/hud?mission_id={user_mission_id}"
            engagement_count += 1
        
        # Update engagement count in all missions
        self._update_engagement_count(signal_id, engagement_count)
        
        return mission_urls
    
    def _update_engagement_count(self, base_signal_id: str, count: int):
        """Update engagement count across all related missions"""
        for mission_file in self.missions_dir.glob(f"{base_signal_id}_USER*.json"):
            try:
                with open(mission_file, 'r') as f:
                    mission = json.load(f)
                
                mission['engagement_count'] = count
                
                with open(mission_file, 'w') as f:
                    json.dump(mission, f, indent=2)
            except Exception as e:
                print(f"Error updating engagement count: {e}")
    
    def cleanup_expired_missions(self):
        """Remove missions older than 8 hours (self-destruct)"""
        current_time = datetime.now()
        cleaned_count = 0
        
        for mission_file in self.missions_dir.glob("APEX5_*.json"):
            try:
                with open(mission_file, 'r') as f:
                    mission = json.load(f)
                
                expires_at = datetime.fromisoformat(mission['expires_at'])
                
                if current_time > expires_at:
                    mission_file.unlink()  # Delete the file
                    cleaned_count += 1
                    print(f"🗑️ Self-destructed expired mission: {mission['mission_id']}")
                    
            except Exception as e:
                print(f"Error checking mission expiry: {e}")
        
        return cleaned_count
    
    def _get_account_via_toc(self, user_id: str) -> Optional[Dict]:
        """Get real account data from TOC system"""
        try:
            import requests
            
            # Check if TOC is running
            response = requests.get(f"{self.toc_url}/health", timeout=3)
            if response.status_code != 200:
                return None
            
            # Get user account status from TOC
            response = requests.get(f"{self.toc_url}/status/{user_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Extract account info if available
                session = data.get('session', {})
                if session:
                    # TOC would provide real MT5 account data here
                    return {
                        'balance': session.get('account_balance', 0),
                        'equity': session.get('account_equity', 0),
                        'margin_free': session.get('margin_free', 0),
                        'currency': 'USD'
                    }
            return None
            
        except Exception as e:
            # TOC not available, fall back to estimates
            return None
    
    def _estimate_account_data(self, user_data: Dict) -> Dict:
        """Estimate account data based on tier and activity when TOC unavailable"""
        tier = user_data.get('tier', 'FANG')
        total_fires = user_data.get('total_fires', 0)
        
        # Base account sizes by tier
        base_balances = {
            'PRESS_PASS': 10000.0,   # Demo account - generous for trial
            'NIBBLER': 2500.0,
            'FANG': 7500.0,
            'COMMANDER': 15000.0
        }
        
        base_balance = base_balances.get(tier, 5000.0)
        
        # Add experience factor
        experience_bonus = min(total_fires * 10, base_balance * 0.5)
        estimated_balance = base_balance + experience_bonus
        
        return {
            'balance': estimated_balance,
            'equity': estimated_balance * 1.02,
            'margin_free': estimated_balance * 0.85,
            'currency': 'USD'
        }
    
    def get_engagement_stats(self, base_signal_id: str) -> Dict:
        """Get real-time engagement statistics for a signal"""
        total_users = 0
        fired_count = 0
        
        for mission_file in self.missions_dir.glob(f"{base_signal_id}_USER*.json"):
            try:
                with open(mission_file, 'r') as f:
                    mission = json.load(f)
                
                total_users += 1
                if mission.get('status') == 'fired':
                    fired_count += 1
                    
            except Exception as e:
                print(f"Error reading mission stats: {e}")
        
        return {
            'total_engaged': total_users,
            'fired_count': fired_count,
            'viewing_count': total_users - fired_count
        }

# Example usage and testing
if __name__ == "__main__":
    
    # Sample signal from APEX
    sample_signal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 87,
        'entry_price': 1.09235,
        'stop_loss': 1.09035,
        'take_profit': 1.09635,
        'signal_type': 'SNIPER_OPS'
    }
    
    # Create user mission system
    mission_system = UserMissionSystem()
    
    # Create personalized missions for all users
    user_urls = mission_system.create_user_missions(sample_signal)
    
    print("🎯 User-Specific Mission URLs Generated:")
    for user_id, url in user_urls.items():
        user_tier = mission_system.users[user_id]['tier']
        print(f"  {user_tier} User {user_id}: {url}")
    
    # Show engagement stats
    base_id = f"APEX5_{sample_signal['symbol']}_{int(time.time())}"
    stats = mission_system.get_engagement_stats(base_id)
    print(f"\n📊 Engagement Stats: {stats['total_engaged']} engaged, {stats['fired_count']} fired")
    
    # Cleanup demo
    print(f"\n🗑️ Cleaned up {mission_system.cleanup_expired_missions()} expired missions")