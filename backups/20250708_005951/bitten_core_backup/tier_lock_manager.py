# tier_lock_manager.py
# BITTEN Tier Lock Manager - Access control for tier-based features

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .rank_access import UserRank

class AccessTier(Enum):
    """Access tiers for BITTEN features"""
    USER = "USER"
    AUTHORIZED = "AUTHORIZED"
    ELITE = "ELITE"
    ADMIN = "ADMIN"

@dataclass
class TierFeature:
    """Feature definition with tier requirements"""
    feature_id: str
    name: str
    description: str
    required_tier: AccessTier
    unlock_message: str
    benefits: Dict[str, Any]

@dataclass
class TierAccess:
    """Tier access check result"""
    has_access: bool
    current_tier: str
    required_tier: str
    message: str
    unlock_options: List[Dict[str, Any]]

class TierLockManager:
    """Manages tier-based access control for BITTEN features"""
    
    def __init__(self):
        # Define tier hierarchy
        self.tier_hierarchy = {
            AccessTier.USER: 0,
            AccessTier.AUTHORIZED: 1,
            AccessTier.ELITE: 2,
            AccessTier.ADMIN: 3
        }
        
        # Define features and their tier requirements
        self.features = {
            # Signal Types
            'arcade_signals': TierFeature(
                feature_id='arcade_signals',
                name='Arcade Signals',
                description='Quick scalp trading signals',
                required_tier=AccessTier.USER,
                unlock_message='Available to all users',
                benefits={'signal_delay': 60, 'max_daily': 3}
            ),
            'sniper_signals': TierFeature(
                feature_id='sniper_signals',
                name='Sniper Signals',
                description='High-precision elite signals',
                required_tier=AccessTier.ELITE,
                unlock_message='Unlock with ELITE tier for precision trades',
                benefits={'signal_delay': 0, 'enhanced_tp': 1.2, 'priority_execution': True}
            ),
            'midnight_hammer': TierFeature(
                feature_id='midnight_hammer',
                name='Midnight Hammer Events',
                description='Community-wide trading events',
                required_tier=AccessTier.AUTHORIZED,
                unlock_message='Join the community with AUTHORIZED tier',
                benefits={'unity_bonus': 0.15, 'group_power': True}
            ),
            
            # Trading Features
            'live_trading': TierFeature(
                feature_id='live_trading',
                name='Live Trading',
                description='Execute trades directly',
                required_tier=AccessTier.AUTHORIZED,
                unlock_message='Upgrade to AUTHORIZED to start trading',
                benefits={'max_positions': 3, 'risk_limit': 0.02}
            ),
            'advanced_risk': TierFeature(
                feature_id='advanced_risk',
                name='Advanced Risk Management',
                description='Customizable risk parameters',
                required_tier=AccessTier.ELITE,
                unlock_message='ELITE traders get full risk control',
                benefits={'max_positions': 6, 'risk_limit': 0.05, 'custom_sl_tp': True}
            ),
            
            # Analytics Features
            'basic_stats': TierFeature(
                feature_id='basic_stats',
                name='Basic Statistics',
                description='View your trading performance',
                required_tier=AccessTier.USER,
                unlock_message='Available to all users',
                benefits={'history_days': 7}
            ),
            'advanced_analytics': TierFeature(
                feature_id='advanced_analytics',
                name='Advanced Analytics',
                description='Detailed performance metrics',
                required_tier=AccessTier.ELITE,
                unlock_message='Unlock deep insights with ELITE tier',
                benefits={'history_days': -1, 'correlation_analysis': True, 'ml_predictions': True}
            ),
            
            # Social Features
            'recruitment': TierFeature(
                feature_id='recruitment',
                name='Recruitment Program',
                description='Earn by inviting traders',
                required_tier=AccessTier.USER,
                unlock_message='Start recruiting immediately',
                benefits={'commission_rate': 0.05, 'xp_bonus': 50}
            ),
            'squad_features': TierFeature(
                feature_id='squad_features',
                name='Squad Features',
                description='Create and manage trading squads',
                required_tier=AccessTier.ELITE,
                unlock_message='Lead your squad with ELITE access',
                benefits={'max_squad_size': 20, 'squad_signals': True}
            ),
            
            # WebApp Features
            'webapp_basic': TierFeature(
                feature_id='webapp_basic',
                name='WebApp Basic Access',
                description='Access BITTEN HUD interface',
                required_tier=AccessTier.USER,
                unlock_message='All users can access basic HUD',
                benefits={'refresh_rate': 60, 'views': ['profile', 'signals']}
            ),
            'webapp_advanced': TierFeature(
                feature_id='webapp_advanced',
                name='WebApp Advanced Features',
                description='Full HUD with real-time data',
                required_tier=AccessTier.ELITE,
                unlock_message='Real-time HUD for ELITE traders',
                benefits={'refresh_rate': 5, 'views': 'all', 'custom_dashboard': True}
            )
        }
        
        # Tier upgrade paths
        self.upgrade_paths = {
            AccessTier.USER: {
                'next_tier': AccessTier.AUTHORIZED,
                'requirements': {
                    'min_trades': 10,
                    'min_profit': 100,
                    'min_days': 7,
                    'verification': True
                },
                'benefits': [
                    'Unlock live trading',
                    'Access Midnight Hammer events',
                    'Higher position limits',
                    'Priority support'
                ]
            },
            AccessTier.AUTHORIZED: {
                'next_tier': AccessTier.ELITE,
                'requirements': {
                    'min_trades': 100,
                    'min_profit': 1000,
                    'win_rate': 0.65,
                    'recruits': 5,
                    'consistency_score': 0.8
                },
                'benefits': [
                    'Sniper signals access',
                    'Advanced risk management',
                    'Squad leadership',
                    'Real-time WebApp HUD',
                    'ML-powered analytics'
                ]
            },
            AccessTier.ELITE: {
                'next_tier': AccessTier.ADMIN,
                'requirements': {
                    'invitation_only': True,
                    'exceptional_performance': True,
                    'community_contribution': True
                },
                'benefits': [
                    'System administration',
                    'Signal creation',
                    'Community management',
                    'Revenue sharing'
                ]
            }
        }
        
        # Tier colors and icons for UI
        self.tier_visuals = {
            AccessTier.USER: {
                'color': '#3498db',
                'icon': '👤',
                'badge': '🥉',
                'glow': 'blue'
            },
            AccessTier.AUTHORIZED: {
                'color': '#2ecc71',
                'icon': '🔑',
                'badge': '🥈',
                'glow': 'green'
            },
            AccessTier.ELITE: {
                'color': '#f39c12',
                'icon': '⭐',
                'badge': '🥇',
                'glow': 'gold'
            },
            AccessTier.ADMIN: {
                'color': '#e74c3c',
                'icon': '🛡️',
                'badge': '💎',
                'glow': 'red'
            }
        }
    
    def check_feature_access(self, user_tier: str, feature_id: str) -> TierAccess:
        """Check if user has access to a specific feature"""
        feature = self.features.get(feature_id)
        if not feature:
            return TierAccess(
                has_access=False,
                current_tier=user_tier,
                required_tier="UNKNOWN",
                message="Feature not found",
                unlock_options=[]
            )
        
        try:
            user_tier_enum = AccessTier(user_tier)
            has_access = self._compare_tiers(user_tier_enum, feature.required_tier)
            
            if has_access:
                message = f"✅ You have access to {feature.name}"
                unlock_options = []
            else:
                message = feature.unlock_message
                unlock_options = self._get_unlock_options(user_tier_enum, feature.required_tier)
            
            return TierAccess(
                has_access=has_access,
                current_tier=user_tier,
                required_tier=feature.required_tier.value,
                message=message,
                unlock_options=unlock_options
            )
        except ValueError:
            return TierAccess(
                has_access=False,
                current_tier=user_tier,
                required_tier=feature.required_tier.value,
                message="Invalid user tier",
                unlock_options=[]
            )
    
    def check_mission_access(self, user_tier: str, required_tier: str) -> Dict[str, Any]:
        """Check if user can access a mission based on tier"""
        try:
            user_tier_enum = AccessTier(user_tier)
            required_tier_enum = AccessTier(required_tier)
            
            has_access = self._compare_tiers(user_tier_enum, required_tier_enum)
            
            if has_access:
                return {
                    'has_access': True,
                    'message': "Access granted",
                    'delay': 0
                }
            else:
                # Calculate access delay for lower tiers
                delay = self._calculate_access_delay(user_tier_enum, required_tier_enum)
                
                return {
                    'has_access': False,
                    'message': f"Requires {required_tier} tier",
                    'delay': delay,
                    'unlock_hint': self._get_tier_unlock_hint(user_tier_enum, required_tier_enum)
                }
        except ValueError:
            return {
                'has_access': False,
                'message': "Invalid tier configuration",
                'delay': -1
            }
    
    def filter_signals_by_tier(self, signals: List[Dict], user_tier: str) -> List[Dict]:
        """Filter signals based on user tier"""
        try:
            user_tier_enum = AccessTier(user_tier)
        except ValueError:
            user_tier_enum = AccessTier.USER
        
        filtered_signals = []
        
        for signal in signals:
            signal_type = signal.get('type', 'arcade')
            
            # Determine required tier for signal
            if signal_type == 'sniper':
                required_tier = AccessTier.ELITE
            elif signal_type == 'midnight_hammer':
                required_tier = AccessTier.AUTHORIZED
            else:
                required_tier = AccessTier.USER
            
            # Check access
            if self._compare_tiers(user_tier_enum, required_tier):
                filtered_signals.append(signal)
            else:
                # Add locked preview for higher tier signals
                locked_signal = signal.copy()
                locked_signal['locked'] = True
                locked_signal['required_tier'] = required_tier.value
                locked_signal['unlock_message'] = f"Unlock with {required_tier.value} tier"
                
                # Blur sensitive data
                locked_signal['entry_price'] = "🔒 LOCKED"
                locked_signal['stop_loss'] = "🔒 LOCKED"
                locked_signal['take_profit'] = "🔒 LOCKED"
                
                filtered_signals.append(locked_signal)
        
        return filtered_signals
    
    def get_tier_benefits(self, tier: str) -> Dict[str, Any]:
        """Get all benefits for a specific tier"""
        try:
            tier_enum = AccessTier(tier)
        except ValueError:
            return {}
        
        benefits = {
            'features': [],
            'limits': {},
            'bonuses': {},
            'visual': self.tier_visuals.get(tier_enum, {})
        }
        
        # Collect all features available at this tier
        for feature_id, feature in self.features.items():
            if self._compare_tiers(tier_enum, feature.required_tier):
                benefits['features'].append({
                    'id': feature_id,
                    'name': feature.name,
                    'description': feature.description,
                    'specific_benefits': feature.benefits
                })
        
        # Add tier-specific limits and bonuses
        if tier_enum == AccessTier.USER:
            benefits['limits'] = {
                'max_positions': 1,
                'max_risk': 0.01,
                'signal_delay': 60,
                'daily_signals': 3
            }
            benefits['bonuses'] = {
                'xp_multiplier': 1.0,
                'recruitment_bonus': 50
            }
        elif tier_enum == AccessTier.AUTHORIZED:
            benefits['limits'] = {
                'max_positions': 3,
                'max_risk': 0.02,
                'signal_delay': 0,
                'daily_signals': 10
            }
            benefits['bonuses'] = {
                'xp_multiplier': 1.2,
                'recruitment_bonus': 75,
                'event_access': True
            }
        elif tier_enum == AccessTier.ELITE:
            benefits['limits'] = {
                'max_positions': 6,
                'max_risk': 0.05,
                'signal_delay': 0,
                'daily_signals': -1  # Unlimited
            }
            benefits['bonuses'] = {
                'xp_multiplier': 1.5,
                'recruitment_bonus': 100,
                'event_access': True,
                'priority_execution': True,
                'advanced_analytics': True
            }
        elif tier_enum == AccessTier.ADMIN:
            benefits['limits'] = {
                'max_positions': -1,  # Unlimited
                'max_risk': 0.10,
                'signal_delay': 0,
                'daily_signals': -1
            }
            benefits['bonuses'] = {
                'xp_multiplier': 2.0,
                'recruitment_bonus': 200,
                'all_access': True,
                'system_control': True
            }
        
        return benefits
    
    def get_upgrade_requirements(self, current_tier: str) -> Dict[str, Any]:
        """Get requirements to upgrade to next tier"""
        try:
            tier_enum = AccessTier(current_tier)
        except ValueError:
            return {}
        
        upgrade_path = self.upgrade_paths.get(tier_enum)
        if not upgrade_path:
            return {
                'max_tier': True,
                'message': "You have reached the maximum tier"
            }
        
        return {
            'current_tier': current_tier,
            'next_tier': upgrade_path['next_tier'].value,
            'requirements': upgrade_path['requirements'],
            'benefits': upgrade_path['benefits'],
            'visual': {
                'current': self.tier_visuals[tier_enum],
                'next': self.tier_visuals[upgrade_path['next_tier']]
            }
        }
    
    def check_upgrade_eligibility(self, user_id: int, current_tier: str, user_stats: Dict) -> Dict[str, Any]:
        """Check if user is eligible for tier upgrade"""
        try:
            tier_enum = AccessTier(current_tier)
        except ValueError:
            return {'eligible': False, 'message': 'Invalid tier'}
        
        upgrade_path = self.upgrade_paths.get(tier_enum)
        if not upgrade_path:
            return {'eligible': False, 'message': 'Maximum tier reached'}
        
        requirements = upgrade_path['requirements']
        checks = {}
        
        # Check each requirement
        if 'min_trades' in requirements:
            user_trades = user_stats.get('total_trades', 0)
            checks['trades'] = {
                'required': requirements['min_trades'],
                'current': user_trades,
                'met': user_trades >= requirements['min_trades']
            }
        
        if 'min_profit' in requirements:
            user_profit = user_stats.get('total_profit', 0)
            checks['profit'] = {
                'required': requirements['min_profit'],
                'current': user_profit,
                'met': user_profit >= requirements['min_profit']
            }
        
        if 'win_rate' in requirements:
            user_win_rate = user_stats.get('win_rate', 0)
            checks['win_rate'] = {
                'required': requirements['win_rate'],
                'current': user_win_rate,
                'met': user_win_rate >= requirements['win_rate']
            }
        
        if 'recruits' in requirements:
            user_recruits = user_stats.get('total_recruits', 0)
            checks['recruits'] = {
                'required': requirements['recruits'],
                'current': user_recruits,
                'met': user_recruits >= requirements['recruits']
            }
        
        # Special checks
        if 'invitation_only' in requirements and requirements['invitation_only']:
            checks['invitation'] = {
                'required': True,
                'current': user_stats.get('has_invitation', False),
                'met': user_stats.get('has_invitation', False)
            }
        
        # Calculate overall eligibility
        all_met = all(check['met'] for check in checks.values())
        
        # Calculate progress percentage
        total_requirements = len(checks)
        met_requirements = sum(1 for check in checks.values() if check['met'])
        progress = (met_requirements / total_requirements * 100) if total_requirements > 0 else 0
        
        return {
            'eligible': all_met,
            'next_tier': upgrade_path['next_tier'].value,
            'checks': checks,
            'progress': progress,
            'message': f"Upgrade progress: {progress:.0f}%"
        }
    
    def _compare_tiers(self, user_tier: AccessTier, required_tier: AccessTier) -> bool:
        """Compare tier levels"""
        user_level = self.tier_hierarchy.get(user_tier, 0)
        required_level = self.tier_hierarchy.get(required_tier, 0)
        return user_level >= required_level
    
    def _calculate_access_delay(self, user_tier: AccessTier, required_tier: AccessTier) -> int:
        """Calculate access delay in seconds for lower tiers"""
        if self._compare_tiers(user_tier, required_tier):
            return 0
        
        # Base delays
        delays = {
            (AccessTier.USER, AccessTier.AUTHORIZED): 60,  # 1 minute
            (AccessTier.USER, AccessTier.ELITE): 300,      # 5 minutes
            (AccessTier.AUTHORIZED, AccessTier.ELITE): 120 # 2 minutes
        }
        
        return delays.get((user_tier, required_tier), 600)  # Default 10 minutes
    
    def _get_unlock_options(self, current_tier: AccessTier, required_tier: AccessTier) -> List[Dict[str, Any]]:
        """Get options to unlock higher tier access"""
        options = []
        
        # Upgrade option
        if current_tier in self.upgrade_paths:
            upgrade_path = self.upgrade_paths[current_tier]
            if self._compare_tiers(upgrade_path['next_tier'], required_tier):
                options.append({
                    'type': 'upgrade',
                    'action': 'upgrade_tier',
                    'label': f"Upgrade to {upgrade_path['next_tier'].value}",
                    'description': "Permanent tier upgrade",
                    'requirements': upgrade_path['requirements']
                })
        
        # Temporary access options (future feature)
        if required_tier == AccessTier.ELITE and current_tier == AccessTier.AUTHORIZED:
            options.append({
                'type': 'trial',
                'action': 'request_trial',
                'label': "Request 24h Trial",
                'description': "Try ELITE features for 24 hours",
                'cost': {'xp': 500}
            })
        
        # Referral bonus option
        options.append({
            'type': 'referral',
            'action': 'share_referral',
            'label': "Invite Friends",
            'description': "Earn XP and unlock features faster",
            'bonus': {'xp_per_recruit': 50}
        })
        
        return options
    
    def _get_tier_unlock_hint(self, current_tier: AccessTier, required_tier: AccessTier) -> str:
        """Get hint for unlocking higher tier"""
        hints = {
            (AccessTier.USER, AccessTier.AUTHORIZED): "Complete 10 trades and verify your account",
            (AccessTier.USER, AccessTier.ELITE): "Build your trading history and recruit active traders",
            (AccessTier.AUTHORIZED, AccessTier.ELITE): "Maintain 65% win rate and recruit 5 traders",
            (AccessTier.ELITE, AccessTier.ADMIN): "By invitation only - exceptional traders"
        }
        
        return hints.get((current_tier, required_tier), "Keep trading and improving your stats")
    
    def generate_tier_comparison_table(self) -> Dict[str, Any]:
        """Generate comparison table of all tiers"""
        comparison = {
            'tiers': [],
            'features': []
        }
        
        # Build tier list
        for tier in AccessTier:
            tier_data = {
                'id': tier.value,
                'name': tier.value,
                'visual': self.tier_visuals[tier],
                'benefits': self.get_tier_benefits(tier.value)
            }
            comparison['tiers'].append(tier_data)
        
        # Build feature comparison
        feature_categories = {
            'Trading': ['arcade_signals', 'sniper_signals', 'live_trading', 'advanced_risk'],
            'Analytics': ['basic_stats', 'advanced_analytics'],
            'Social': ['recruitment', 'squad_features'],
            'Platform': ['webapp_basic', 'webapp_advanced']
        }
        
        for category, feature_ids in feature_categories.items():
            category_features = []
            for feature_id in feature_ids:
                if feature_id in self.features:
                    feature = self.features[feature_id]
                    feature_comparison = {
                        'name': feature.name,
                        'tiers': {}
                    }
                    
                    # Check which tiers have access
                    for tier in AccessTier:
                        has_access = self._compare_tiers(tier, feature.required_tier)
                        feature_comparison['tiers'][tier.value] = {
                            'access': has_access,
                            'icon': '✅' if has_access else '🔒'
                        }
                    
                    category_features.append(feature_comparison)
            
            comparison['features'].append({
                'category': category,
                'items': category_features
            })
        
        return comparison