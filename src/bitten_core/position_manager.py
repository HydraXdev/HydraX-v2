# position_manager.py
# BITTEN Position Management - Account Protection & Slot Control

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from .fire_modes import TierLevel, TIER_CONFIGS

@dataclass
class OpenPosition:
    """Active position tracking"""
    position_id: str
    symbol: str
    direction: str
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    open_time: datetime
    position_type: str  # 'arcade' or 'sniper'
    risk_amount: float

class PositionManager:
    """
    POSITION & RISK MANAGEMENT ENGINE
    
    Protects accounts with tier-based limits and balance requirements.
    Manages concurrent positions based on account size.
    """
    
    def __init__(self):
        # Position limits by account balance
        self.balance_limits = {
            500: 1,    # <$1000: 1 position max
            1000: 2,   # $1000-2000: 2 positions
            2000: 3,   # $2000-5000: 3 positions
            5000: 5,   # $5000+: 5 positions
            10000: 10  # $10k+: 10 positions (unlimited)
        }
        
        # Risk parameters
        self.risk_per_trade = 0.02  # 2% per position
        self.max_daily_risk = 0.06  # 6% daily max
        self.max_total_exposure = 0.10  # 10% total exposure
        
        # Active tracking
        self.open_positions: Dict[int, List[OpenPosition]] = {}  # user_id -> positions
        self.daily_risk: Dict[int, float] = {}  # user_id -> risk used today
        self.user_balances: Dict[int, float] = {}  # user_id -> account balance
        
    def can_open_position(self, user_id: int, tier: TierLevel, 
                         balance: float, signal_type: str) -> Tuple[bool, str]:
        """
        Comprehensive position authorization check
        
        THE LAW:
        - Balance-based position limits
        - Daily risk limits
        - Tier access for snipers
        - Concurrent position management
        """
        
        # Update balance tracking
        self.user_balances[user_id] = balance
        
        # Get user's open positions
        user_positions = self.open_positions.get(user_id, [])
        open_count = len(user_positions)
        
        # 1. Check tier access for snipers
        if signal_type == 'sniper' and tier == TierLevel.NIBBLER:
            return False, "🔒 SNIPER LOCKED - UPGRADE TO FANG"
        
        # 2. Check balance-based position limits
        max_positions = self._get_position_limit(balance, tier)
        if open_count >= max_positions:
            return False, f"SLOTS FULL ({open_count}/{max_positions})"
        
        # 3. Check daily risk limit
        daily_risk_used = self.daily_risk.get(user_id, 0)
        if daily_risk_used >= self.max_daily_risk:
            return False, f"DAILY RISK LIMIT ({daily_risk_used:.1%}/{self.max_daily_risk:.0%})"
        
        # 4. Check total exposure
        total_exposure = self._calculate_total_exposure(user_id)
        if total_exposure >= self.max_total_exposure:
            return False, f"MAX EXPOSURE ({total_exposure:.1%}/{self.max_total_exposure:.0%})"
        
        # 5. Check minimum balance requirements
        min_balance = self._get_minimum_balance(tier)
        if balance < min_balance:
            return False, f"MIN BALANCE ${min_balance} REQUIRED"
        
        # 6. Special checks for low balance accounts
        if balance < 1000 and open_count >= 1:
            return False, "ACCOUNT <$1K LIMITED TO 1 POSITION"
        
        return True, "AUTHORIZED"
    
    def open_position(self, user_id: int, position: OpenPosition) -> bool:
        """Record new position opening"""
        if user_id not in self.open_positions:
            self.open_positions[user_id] = []
        
        # Add position
        self.open_positions[user_id].append(position)
        
        # Update daily risk
        if user_id not in self.daily_risk:
            self.daily_risk[user_id] = 0
        self.daily_risk[user_id] += position.risk_amount
        
        return True
    
    def close_position(self, user_id: int, position_id: str, 
                      result: str, pnl: float) -> bool:
        """Close position and update tracking"""
        if user_id not in self.open_positions:
            return False
        
        # Find and remove position
        positions = self.open_positions[user_id]
        for i, pos in enumerate(positions):
            if pos.position_id == position_id:
                positions.pop(i)
                
                # Update daily risk if loss
                if result == 'loss' and pnl < 0:
                    # Already counted in daily risk
                    pass
                
                return True
        
        return False
    
    def _get_position_limit(self, balance: float, tier: TierLevel) -> int:
        """Get position limit based on balance and tier"""
        
        # gets special treatment
        if tier == TierLevel.:
            if balance >= 10000:
                return 99  # Effectively unlimited
            elif balance >= 5000:
                return 10
            else:
                return 5
        
        # Other tiers use balance-based limits
        if balance < 1000:
            return 1
        elif balance < 2000:
            return 2
        elif balance < 5000:
            return 3
        elif balance < 10000:
            return 5
        else:
            return 10
    
    def _get_minimum_balance(self, tier: TierLevel) -> float:
        """Get minimum balance requirement by tier"""
        min_balances = {
            TierLevel.NIBBLER: 500,
            TierLevel.FANG: 500,
            TierLevel.COMMANDER: 1000,
            TierLevel.: 2000
        }
        return min_balances.get(tier, 500)
    
    def _calculate_total_exposure(self, user_id: int) -> float:
        """Calculate total exposure as % of balance"""
        positions = self.open_positions.get(user_id, [])
        if not positions:
            return 0.0
        
        balance = self.user_balances.get(user_id, 1000)
        total_risk = sum(pos.risk_amount for pos in positions)
        
        return total_risk / balance if balance > 0 else 0.0
    
    def get_user_status(self, user_id: int) -> Dict:
        """Get comprehensive position status"""
        positions = self.open_positions.get(user_id, [])
        balance = self.user_balances.get(user_id, 0)
        
        return {
            'open_positions': len(positions),
            'position_details': [
                {
                    'id': p.position_id,
                    'symbol': p.symbol,
                    'type': p.position_type,
                    'risk': p.risk_amount
                } for p in positions
            ],
            'daily_risk_used': self.daily_risk.get(user_id, 0),
            'total_exposure': self._calculate_total_exposure(user_id),
            'available_slots': self._get_available_slots(user_id, balance),
            'can_trade': len(positions) < self._get_position_limit(balance, TierLevel.FANG)
        }
    
    def _get_available_slots(self, user_id: int, balance: float) -> int:
        """Calculate available position slots"""
        current_positions = len(self.open_positions.get(user_id, []))
        max_positions = self._get_position_limit(balance, TierLevel.FANG)  # Default
        return max(0, max_positions - current_positions)
    
    def reset_daily_risk(self):
        """Reset daily risk tracking (run at midnight)"""
        self.daily_risk.clear()
    
    def emergency_close_all(self, user_id: int) -> List[str]:
        """Emergency close all positions for user"""
        if user_id not in self.open_positions:
            return []
        
        position_ids = [p.position_id for p in self.open_positions[user_id]]
        self.open_positions[user_id] = []
        
        return position_ids

class DrawdownProtection:
    """
    DRAWDOWN PROTECTION SYSTEM
    
    Monitors account performance and implements protective measures.
    """
    
    def __init__(self):
        self.daily_loss_limit = 0.07  # 7% daily max loss
        self.consecutive_loss_limit = 3  # 3 losses in a row
        self.cooldown_period = 60  # minutes after hitting limit
        
        # Tracking
        self.daily_pnl: Dict[int, float] = {}  # user_id -> daily P&L
        self.loss_streaks: Dict[int, int] = {}  # user_id -> consecutive losses
        self.cooldowns: Dict[int, datetime] = {}  # user_id -> cooldown end time
        
    def check_drawdown_status(self, user_id: int, balance: float) -> Tuple[bool, str]:
        """Check if user is in drawdown protection"""
        
        # Check cooldown
        if user_id in self.cooldowns:
            if datetime.now() < self.cooldowns[user_id]:
                remaining = (self.cooldowns[user_id] - datetime.now()).seconds // 60
                return False, f"COOLDOWN ACTIVE: {remaining} minutes remaining"
        
        # Check daily loss
        daily_loss = abs(self.daily_pnl.get(user_id, 0))
        if daily_loss >= balance * self.daily_loss_limit:
            return False, f"DAILY LOSS LIMIT: -{daily_loss/balance:.1%}"
        
        # Check loss streak
        streak = self.loss_streaks.get(user_id, 0)
        if streak >= self.consecutive_loss_limit:
            return False, f"LOSS STREAK: {streak} consecutive losses"
        
        return True, "OK"
    
    def record_trade_result(self, user_id: int, pnl: float, balance: float):
        """Record trade result and update protection status"""
        
        # Update daily P&L
        if user_id not in self.daily_pnl:
            self.daily_pnl[user_id] = 0
        self.daily_pnl[user_id] += pnl
        
        # Update loss streak
        if pnl < 0:
            self.loss_streaks[user_id] = self.loss_streaks.get(user_id, 0) + 1
            
            # Check if protection triggered
            if self.loss_streaks[user_id] >= self.consecutive_loss_limit:
                self.cooldowns[user_id] = datetime.now() + timedelta(minutes=self.cooldown_period)
                
            if abs(self.daily_pnl[user_id]) >= balance * self.daily_loss_limit:
                self.cooldowns[user_id] = datetime.now() + timedelta(minutes=self.cooldown_period)
        else:
            # Reset streak on win
            self.loss_streaks[user_id] = 0
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_pnl.clear()
        # Keep loss streaks as they span days