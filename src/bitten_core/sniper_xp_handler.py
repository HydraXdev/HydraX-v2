"""
Sniper Trade XP Handler
Manages XP bonuses and penalties for FANG tier sniper trades
"""

from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SniperXPHandler:
    """Handles XP calculations for sniper trades"""
    
    # XP modifiers
    SNIPER_TP_BONUS_MULTIPLIER = 1.5    # 50% bonus for holding to TP
    SNIPER_EARLY_EXIT_PENALTY = 0.5     # 50% penalty for early exit
    RAPID_ASSAULT_BASE_XP = 100                 # Base XP for arcade trades
    SNIPER_BASE_XP = 150                 # Base XP for sniper trades (higher risk/reward)
    
    def __init__(self):
        self.active_sniper_trades = {}  # track_id -> trade_data
    
    def register_sniper_trade(self, trade_id: str, user_id: int, symbol: str, 
                            entry_price: float, tp_price: float, sl_price: float):
        """Register a new sniper trade for XP tracking"""
        self.active_sniper_trades[trade_id] = {
            'user_id': user_id,
            'symbol': symbol,
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'opened_at': datetime.now(),
            'signal_type': 'sniper'
        }
        logger.info(f"Registered sniper trade {trade_id} for XP tracking")
    
    def calculate_trade_xp(self, trade_id: str, exit_price: float, 
                         exit_reason: str, pnl: float) -> Dict:
        """
        Calculate XP for a closing trade
        
        Args:
            trade_id: Unique trade identifier
            exit_price: Price at which trade was closed
            exit_reason: 'tp_hit', 'sl_hit', 'manual_close'
            pnl: Profit/loss amount
            
        Returns:
            Dict with XP calculation details
        """
        # Check if this is a tracked sniper trade
        if trade_id not in self.active_sniper_trades:
            # Not a sniper trade, calculate arcade XP
            return self._calculate_arcade_xp(pnl)
        
        trade_data = self.active_sniper_trades[trade_id]
        base_xp = self.SNIPER_BASE_XP
        
        # Calculate XP based on exit reason
        if exit_reason == 'tp_hit':
            # Full TP hit - apply bonus
            final_xp = int(base_xp * self.SNIPER_TP_BONUS_MULTIPLIER)
            message = f"🎯 SNIPER PERFECTION! Held to TP (+{int(base_xp * 0.5)} XP bonus)"
            xp_modifier = self.SNIPER_TP_BONUS_MULTIPLIER
            
        elif exit_reason == 'sl_hit':
            # Stop loss hit - normal XP (no penalty for proper risk management)
            final_xp = base_xp
            message = "💀 Sniper shot missed. Risk managed properly."
            xp_modifier = 1.0
            
        else:  # manual_close
            # Early exit - apply penalty
            # Calculate how close they were to TP
            tp_distance = abs(trade_data['tp_price'] - trade_data['entry_price'])
            exit_distance = abs(exit_price - trade_data['entry_price'])
            progress_percent = (exit_distance / tp_distance) * 100 if tp_distance > 0 else 0
            
            if progress_percent >= 80:
                # Close to TP, reduced penalty
                xp_modifier = 0.8
                final_xp = int(base_xp * xp_modifier)
                message = f"🎯 Sniper exit at {progress_percent:.0f}% of target (-20% XP)"
            else:
                # Early exit, full penalty
                xp_modifier = self.SNIPER_EARLY_EXIT_PENALTY
                final_xp = int(base_xp * xp_modifier)
                message = f"⚠️ SNIPER DISCIPLINE BREACH! Early exit (-50% XP)"
        
        # Additional XP for profitable trades
        if pnl > 0:
            profit_bonus = min(int(pnl * 0.1), 50)  # 10% of profit as XP, max 50
            final_xp += profit_bonus
            message += f" +{profit_bonus} profit bonus"
        
        # Clean up tracked trade
        del self.active_sniper_trades[trade_id]
        
        return {
            'base_xp': base_xp,
            'final_xp': final_xp,
            'xp_modifier': xp_modifier,
            'signal_type': 'sniper',
            'exit_reason': exit_reason,
            'message': message,
            'progress_percent': progress_percent if exit_reason == 'manual_close' else 100
        }
    
    def _calculate_arcade_xp(self, pnl: float) -> Dict:
        """Calculate XP for arcade trades"""
        base_xp = self.RAPID_ASSAULT_BASE_XP
        
        # Simple XP based on win/loss
        if pnl > 0:
            final_xp = base_xp + min(int(pnl * 0.1), 50)
            message = "⚡ Arcade win! Quick and clean."
        else:
            final_xp = int(base_xp * 0.7)  # 30% reduction for losses
            message = "💥 Arcade loss. Learn and adapt."
        
        return {
            'base_xp': base_xp,
            'final_xp': final_xp,
            'xp_modifier': final_xp / base_xp,
            'signal_type': 'arcade',
            'exit_reason': 'trade_closed',
            'message': message
        }
    
    def get_active_sniper_count(self, user_id: int) -> int:
        """Get count of active sniper trades for a user"""
        return sum(1 for trade in self.active_sniper_trades.values() 
                  if trade['user_id'] == user_id)
    
    def is_sniper_trade(self, trade_id: str) -> bool:
        """Check if a trade is registered as sniper"""
        return trade_id in self.active_sniper_trades

# Global instance
sniper_xp_handler = SniperXPHandler()

def calculate_fang_trade_xp(trade_id: str, signal_type: str, exit_price: float,
                          exit_reason: str, pnl: float, entry_data: Optional[Dict] = None) -> Dict:
    """
    Main function to calculate XP for FANG tier trades
    
    Args:
        trade_id: Unique trade identifier
        signal_type: 'arcade' or 'sniper'
        exit_price: Exit price
        exit_reason: 'tp_hit', 'sl_hit', 'manual_close'
        pnl: Profit/loss
        entry_data: Optional dict with entry_price, tp_price, sl_price for new trades
        
    Returns:
        XP calculation details
    """
    global sniper_xp_handler
    
    # Register sniper trade if this is entry
    if entry_data and signal_type == 'sniper':
        sniper_xp_handler.register_sniper_trade(
            trade_id=trade_id,
            user_id=entry_data.get('user_id', 0),
            symbol=entry_data.get('symbol', ''),
            entry_price=entry_data['entry_price'],
            tp_price=entry_data['tp_price'],
            sl_price=entry_data['sl_price']
        )
        return {'message': 'Sniper trade registered for XP tracking'}
    
    # Calculate XP for closing trade
    return sniper_xp_handler.calculate_trade_xp(trade_id, exit_price, exit_reason, pnl)