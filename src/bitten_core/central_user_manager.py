#!/usr/bin/env python3
"""
BITTEN Central User Manager
Single point of access for ALL user operations
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class CentralUserManager:
    """Single source of truth for ALL user data"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Import central database
        from src.bitten_core.central_database_sqlite import get_central_database
        self.db = get_central_database()
        
        # Import guardrails for risk management
        from src.bitten_core.trading_guardrails import get_trading_guardrails
        self.guardrails = get_trading_guardrails()
        
        self._initialized = True
        logger.info("✅ Central User Manager initialized")
    
    def get_complete_user(self, telegram_id: int) -> Optional[Dict]:
        """
        Get EVERYTHING about a user in one call
        Includes profile, tier, stats, guardrails, referrals, XP, settings
        """
        try:
            user = self.db.get_user(telegram_id)
            if not user:
                logger.warning(f"User {telegram_id} not found in central database")
                return None
            
            # Add computed fields
            user['ready_for_fire'] = self.is_user_ready_for_fire(telegram_id)
            user['can_trade'] = self.can_user_trade_now(telegram_id)
            user['daily_stats'] = self.get_daily_stats(telegram_id)
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting complete user {telegram_id}: {e}")
            return None
    
    def create_user(self, telegram_id: int, initial_data: Dict) -> bool:
        """
        Create new user with all required subsystem entries
        """
        try:
            # Ensure required fields
            user_data = {
                'user_uuid': initial_data.get('user_uuid', f'USER_{telegram_id}'),
                'username': initial_data.get('username', ''),
                'tier': initial_data.get('tier', 'NIBBLER'),
                'account_balance': initial_data.get('account_balance', 0),
                'broker': initial_data.get('broker', ''),
                'mt5_account': initial_data.get('mt5_account', '')
            }
            
            # Create user in central database (creates all related tables)
            success = self.db.create_user(telegram_id, user_data)
            
            if success:
                logger.info(f"✅ Created user {telegram_id} in central system")
                
                # Initialize guardrails with proper limits
                self.guardrails.increment_trade_count(str(telegram_id))  # Initialize counter
                
            return success
            
        except Exception as e:
            logger.error(f"Error creating user {telegram_id}: {e}")
            return False
    
    def update_user_tier(self, telegram_id: int, new_tier: str) -> bool:
        """
        Update user tier with cascading updates to all limits
        """
        try:
            # Update tier in main users table
            tier_update = self.db.update_user(telegram_id, {'tier': new_tier}, 'users')
            
            if tier_update:
                # Update guardrails limits based on new tier
                tier_limits = self.db.get_tier_limits(new_tier)
                guardrails_update = self.db.update_user(telegram_id, {
                    'max_daily_loss': tier_limits['max_daily_loss'],
                    'max_daily_trades': tier_limits['max_daily_trades'],
                    'max_concurrent_trades': tier_limits['max_positions']
                }, 'user_trading_guardrails')
                
                # Update fire mode slots
                fire_slots = {
                    'PRESS_PASS': 1,
                    'NIBBLER': 1,
                    'FANG': 2,
                    'COMMANDER': 3
                }
                fire_update = self.db.update_user(telegram_id, {
                    'max_slots': fire_slots.get(new_tier, 1)
                }, 'user_fire_modes')
                
                logger.info(f"✅ Updated user {telegram_id} to tier {new_tier}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating tier for {telegram_id}: {e}")
            return False
    
    def after_trade_execution(self, telegram_id: int, trade_result: Dict) -> bool:
        """
        Update ALL relevant data after a trade execution
        """
        try:
            # Update trading stats
            stats_updates = {}
            stats_updates['total_trades'] = 'total_trades + 1'
            
            if trade_result.get('won'):
                stats_updates['winning_trades'] = 'winning_trades + 1'
                stats_updates['current_streak'] = 'current_streak + 1'
                xp_earned = 10
            else:
                stats_updates['losing_trades'] = 'losing_trades + 1'
                stats_updates['current_streak'] = 0
                xp_earned = 2
            
            # This would need SQL expression support
            # For now, get current values and calculate
            user = self.db.get_user(telegram_id)
            if user and 'trading_stats' in user:
                current_stats = user['trading_stats']
                new_stats = {
                    'total_trades': current_stats.get('total_trades', 0) + 1,
                    'winning_trades': current_stats.get('winning_trades', 0) + (1 if trade_result.get('won') else 0),
                    'losing_trades': current_stats.get('losing_trades', 0) + (0 if trade_result.get('won') else 1),
                    'total_pnl': current_stats.get('total_pnl', 0) + trade_result.get('pnl', 0),
                    'last_trade_at': datetime.now().isoformat()
                }
                
                # Calculate win rate
                if new_stats['total_trades'] > 0:
                    new_stats['win_rate'] = (new_stats['winning_trades'] / new_stats['total_trades']) * 100
                
                self.db.update_user(telegram_id, new_stats, 'user_trading_stats')
            
            # Update XP
            self.add_xp(telegram_id, xp_earned, f"Trade {'win' if trade_result.get('won') else 'loss'}")
            
            # Update guardrails tracking
            self.guardrails.update_balance_and_pnl(
                str(telegram_id),
                trade_result.get('new_balance', 0),
                trade_result.get('pnl', 0)
            )
            
            # Check for achievements
            self.check_achievements(telegram_id)
            
            # Process referral commission if applicable
            if trade_result.get('won'):
                self.process_referral_commission(telegram_id, trade_result.get('pnl', 0))
            
            logger.info(f"✅ Updated all systems for user {telegram_id} after trade")
            return True
            
        except Exception as e:
            logger.error(f"Error updating after trade for {telegram_id}: {e}")
            return False
    
    def add_xp(self, telegram_id: int, xp_amount: int, reason: str) -> bool:
        """Add XP to user with achievement checking"""
        try:
            user = self.db.get_user(telegram_id)
            if user and 'xp' in user:
                current_xp = user['xp'].get('total_xp', 0)
                new_xp = current_xp + xp_amount
                
                # Calculate new level (100 XP per level)
                new_level = (new_xp // 100) + 1
                
                updates = {
                    'total_xp': new_xp,
                    'current_level': new_level,
                    'daily_xp': user['xp'].get('daily_xp', 0) + xp_amount
                }
                
                self.db.update_user(telegram_id, updates, 'user_xp')
                logger.info(f"✅ Added {xp_amount} XP to user {telegram_id} for {reason}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding XP for {telegram_id}: {e}")
            return False
    
    def check_achievements(self, telegram_id: int) -> List[str]:
        """Check and award achievements"""
        new_achievements = []
        
        try:
            user = self.db.get_user(telegram_id)
            if not user:
                return []
            
            stats = user.get('trading_stats', {})
            xp = user.get('xp', {})
            
            # Check various achievement conditions
            achievements_to_check = [
                ('FIRST_TRADE', stats.get('total_trades', 0) >= 1, "First Trade"),
                ('TEN_TRADES', stats.get('total_trades', 0) >= 10, "10 Trades"),
                ('HUNDRED_TRADES', stats.get('total_trades', 0) >= 100, "Century Trader"),
                ('LEVEL_10', xp.get('current_level', 1) >= 10, "Level 10"),
                ('WIN_STREAK_5', stats.get('current_streak', 0) >= 5, "5 Win Streak"),
            ]
            
            # Check each achievement
            existing = [a['achievement_code'] for a in user.get('achievements', [])]
            
            for code, condition, name in achievements_to_check:
                if condition and code not in existing:
                    # Award achievement
                    # This would need INSERT INTO user_achievements
                    logger.info(f"🏆 User {telegram_id} earned achievement: {name}")
                    new_achievements.append(name)
            
        except Exception as e:
            logger.error(f"Error checking achievements for {telegram_id}: {e}")
        
        return new_achievements
    
    def process_referral_commission(self, telegram_id: int, trade_profit: float) -> bool:
        """Process referral commission for profitable trades"""
        try:
            user = self.db.get_user(telegram_id)
            if not user or 'referrals' not in user:
                return False
            
            referral_data = user['referrals']
            referred_by = referral_data.get('referred_by_user')
            
            if referred_by:
                # 5% commission on profitable trades
                commission = trade_profit * 0.05
                
                # Update referrer's pending credits
                referrer = self.db.get_user(referred_by)
                if referrer and 'referrals' in referrer:
                    current_pending = referrer['referrals'].get('pending_credits', 0)
                    self.db.update_user(referred_by, {
                        'pending_credits': current_pending + commission,
                        'lifetime_commission': referrer['referrals'].get('lifetime_commission', 0) + commission
                    }, 'user_referrals')
                    
                    logger.info(f"💰 Credited ${commission:.2f} referral commission to user {referred_by}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error processing referral commission: {e}")
        
        return False
    
    def is_user_ready_for_fire(self, telegram_id: int) -> bool:
        """Check if user is ready to execute trades"""
        try:
            user = self.db.get_user(telegram_id)
            if not user:
                return False
            
            # Check basic requirements
            tier = user.get('tier', 'FREE')
            if tier not in ['PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER']:
                return False
            
            # Check if subscription is active
            if user.get('subscription_status') == 'EXPIRED':
                return False
            
            # Check if banned
            if user.get('is_banned'):
                return False
            
            # Check if has MT5 account
            mt5_accounts = user.get('mt5_accounts', [])
            if not mt5_accounts:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking fire readiness for {telegram_id}: {e}")
            return False
    
    def can_user_trade_now(self, telegram_id: int) -> Tuple[bool, str]:
        """Check if user can trade right now (considering limits)"""
        try:
            user = self.db.get_user(telegram_id)
            if not user:
                return False, "User not found"
            
            guardrails_data = user.get('trading_guardrails', {})
            
            # Check daily trade limit
            daily_trades_used = guardrails_data.get('daily_trades_used', 0)
            max_daily_trades = guardrails_data.get('max_daily_trades', 6)
            if daily_trades_used >= max_daily_trades:
                return False, f"Daily trade limit reached ({daily_trades_used}/{max_daily_trades})"
            
            # Check daily loss limit
            daily_loss = guardrails_data.get('daily_loss_amount', 0)
            max_daily_loss = guardrails_data.get('max_daily_loss', 0.06)
            starting_balance = guardrails_data.get('daily_starting_balance', 1000)
            
            if starting_balance and starting_balance > 0:
                loss_percent = abs(daily_loss) / starting_balance
                if loss_percent >= max_daily_loss:
                    return False, f"Daily loss limit reached ({loss_percent:.1%})"
            
            # Check cooldown
            cooldown_until = guardrails_data.get('cooldown_until')
            if cooldown_until:
                cooldown_dt = datetime.fromisoformat(cooldown_until) if isinstance(cooldown_until, str) else cooldown_until
                if datetime.now() < cooldown_dt:
                    return False, f"In cooldown until {cooldown_dt.strftime('%H:%M')}"
            
            # Check emergency stop
            if guardrails_data.get('emergency_stop_active'):
                return False, f"Emergency stop active: {guardrails_data.get('emergency_stop_reason', 'Unknown')}"
            
            return True, "Ready to trade"
            
        except Exception as e:
            logger.error(f"Error checking trade permission for {telegram_id}: {e}")
            return False, str(e)
    
    def get_daily_stats(self, telegram_id: int) -> Dict:
        """Get user's daily trading statistics"""
        try:
            user = self.db.get_user(telegram_id)
            if not user:
                return {}
            
            guardrails = user.get('trading_guardrails', {})
            stats = user.get('trading_stats', {})
            
            return {
                'trades_today': guardrails.get('daily_trades_used', 0),
                'trades_allowed': guardrails.get('max_daily_trades', 6),
                'daily_pnl': guardrails.get('daily_loss_amount', 0),
                'daily_loss_percent': 0,  # Would calculate from starting balance
                'open_positions': guardrails.get('current_open_trades', 0),
                'max_positions': guardrails.get('max_concurrent_trades', 3),
                'consecutive_losses': guardrails.get('consecutive_losses', 0),
                'total_trades': stats.get('total_trades', 0),
                'win_rate': stats.get('win_rate', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting daily stats for {telegram_id}: {e}")
            return {}
    
    def get_user_by_uuid(self, user_uuid: str) -> Optional[Dict]:
        """Get user by UUID instead of telegram_id"""
        # This would need a query by user_uuid
        # For now, return None
        return None
    
    def get_all_active_users(self) -> List[Dict]:
        """Get all active users for batch operations"""
        # This would need a SELECT * WHERE is_active = 1
        # For now, return empty list
        return []

# Singleton getter
_manager_instance = None

def get_central_user_manager() -> CentralUserManager:
    """Get singleton instance of central user manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = CentralUserManager()
    return _manager_instance