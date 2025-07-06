"""
BITTEN Trade Management Executor
Handles advanced trade modifications and monitoring
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from enum import Enum

from .risk_management import TradeManagementPlan, TradeManagementFeature, RiskProfile
from ..mt5_bridge.mt5_bridge_adapter import get_bridge_adapter
from .trade_confirmation_system import TradeConfirmationSystem

logger = logging.getLogger(__name__)

class ExitType(Enum):
    """Types of trade exits for XP tracking"""
    MANUAL = "manual"  # Regular manual exit
    STOP_LOSS = "stop_loss"  # Hit stop loss
    TAKE_PROFIT = "take_profit"  # Hit take profit
    PARACHUTE = "parachute"  # Emergency exit with no XP penalty
    CHAINGUN = "chaingun"  # Rapid fire exit mode
    PROFIT_RUNNER = "profit_runner"  # Partial exit from runner mode
    TRAILING_STOP = "trailing_stop"  # Exit via trailing stop
    EMERGENCY = "emergency"  # Approved emergency exit
    BREAKEVEN = "breakeven"  # Exit at breakeven
    TIME_BASED = "time_based"  # Exit based on time rules

@dataclass
class ActiveTrade:
    """Active trade being managed"""
    trade_id: str
    ticket: int
    symbol: str
    direction: str  # BUY or SELL
    entry_price: float
    current_sl: float
    current_tp: float
    original_sl: float
    volume: float
    open_time: datetime
    management_plans: List[TradeManagementPlan]
    user_id: int
    
    # Management state
    is_breakeven: bool = False
    is_trailing: bool = False
    partial_closed: float = 0  # Percentage already closed
    last_trail_price: float = 0
    peak_price: float = 0  # Highest/lowest price reached
    current_pnl_pips: float = 0
    
    # Exit tracking
    exit_type: Optional[ExitType] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_pnl_pips: Optional[float] = None
    parachute_activated: bool = False
    emergency_approved: bool = False
    chaingun_mode: bool = False
    
    def update_pnl(self, current_price: float, pip_value: float):
        """Update current P&L in pips"""
        if self.direction == "BUY":
            self.current_pnl_pips = (current_price - self.entry_price) / pip_value
            self.peak_price = max(self.peak_price or current_price, current_price)
        else:
            self.current_pnl_pips = (self.entry_price - current_price) / pip_value
            self.peak_price = min(self.peak_price or current_price, current_price)

class TradeManager:
    """
    Advanced trade management system
    Monitors and modifies trades based on XP-unlocked features
    """
    
    def __init__(self, confirmation_system: Optional[TradeConfirmationSystem] = None):
        self.adapter = get_bridge_adapter()
        self.active_trades: Dict[str, ActiveTrade] = {}
        self.monitoring = False
        self.monitor_task = None
        self.check_interval = 1.0  # Check every second
        
        # Trade confirmation system
        self.confirmation_system = confirmation_system
        
        # Price data (would come from broker feed in production)
        self.current_prices = {}
        
        # Symbol specifications
        self.symbol_specs = {
            'XAUUSD': {'pip_value': 0.1},
            'EURUSD': {'pip_value': 0.0001},
            'GBPUSD': {'pip_value': 0.0001},
            'USDJPY': {'pip_value': 0.01},
            'USDCAD': {'pip_value': 0.0001},
            'GBPJPY': {'pip_value': 0.01}
        }
        
        # Notifications queue for UI updates
        self.notifications = []
        
        # Exit history for XP tracking
        self.exit_history: List[Dict] = []
        
    def add_trade(self, trade: ActiveTrade):
        """Add a trade to be managed"""
        self.active_trades[trade.trade_id] = trade
        logger.info(f"Added trade {trade.trade_id} for management")
        
        # Initialize peak price
        if trade.direction == "BUY":
            trade.peak_price = trade.entry_price
        else:
            trade.peak_price = trade.entry_price
        
        # Send trade opened confirmation
        if self.confirmation_system:
            asyncio.create_task(self._send_trade_opened_confirmation(trade))
    
    async def _send_trade_opened_confirmation(self, trade: ActiveTrade):
        """Send trade opened confirmation to Telegram"""
        trade_data = {
            'trade_id': trade.trade_id,
            'ticket': trade.ticket,
            'symbol': trade.symbol,
            'direction': trade.direction,
            'volume': trade.volume,
            'entry_price': trade.entry_price,
            'stop_loss': trade.current_sl,
            'take_profit': trade.current_tp,
            'metadata': {
                'open_time': trade.open_time.isoformat(),
                'management_features': [plan.feature.value for plan in trade.management_plans]
            }
        }
        
        await self.confirmation_system.send_trade_opened_confirmation(
            trade.user_id, trade_data
        )
    
    def remove_trade(self, trade_id: str):
        """Remove a trade from management"""
        if trade_id in self.active_trades:
            trade = self.active_trades[trade_id]
            # Store exit data for XP tracking
            exit_data = self.get_exit_data_for_xp(trade)
            self.exit_history.append(exit_data)
            
            # Send trade closed confirmation
            if self.confirmation_system:
                asyncio.create_task(self._send_trade_closed_confirmation(trade))
            
            del self.active_trades[trade_id]
            logger.info(f"Removed trade {trade_id} from management")
            
            # Send exit data to XP system (would be async in production)
            self._send_exit_to_xp_system(exit_data)
    
    async def _send_trade_closed_confirmation(self, trade: ActiveTrade):
        """Send trade closed confirmation to Telegram"""
        trade_data = {
            'trade_id': trade.trade_id,
            'ticket': trade.ticket,
            'symbol': trade.symbol,
            'direction': trade.direction,
            'volume': trade.volume,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price or self.current_prices.get(trade.symbol, trade.entry_price),
            'pnl_pips': trade.exit_pnl_pips or trade.current_pnl_pips,
            'pnl_dollars': (trade.exit_pnl_pips or trade.current_pnl_pips) * 10,  # Approximate
            'reason': self._get_exit_reason(trade),
            'metadata': {
                'exit_type': trade.exit_type.value if trade.exit_type else 'manual',
                'duration_minutes': (trade.exit_time - trade.open_time).total_seconds() / 60 if trade.exit_time else 0,
                'partial_closed': trade.partial_closed,
                'was_breakeven': trade.is_breakeven,
                'was_trailing': trade.is_trailing
            }
        }
        
        # Choose appropriate confirmation type
        if trade.exit_type == ExitType.STOP_LOSS:
            await self.confirmation_system.send_stop_loss_hit_confirmation(
                trade.user_id, trade_data
            )
        elif trade.exit_type == ExitType.TAKE_PROFIT:
            await self.confirmation_system.send_take_profit_hit_confirmation(
                trade.user_id, trade_data
            )
        elif trade.exit_type == ExitType.EMERGENCY:
            await self.confirmation_system.send_emergency_close_confirmation(
                trade.user_id, trade_data
            )
        elif trade.exit_type == ExitType.PARACHUTE:
            await self.confirmation_system.send_parachute_exit_confirmation(
                trade.user_id, trade_data
            )
        else:
            await self.confirmation_system.send_trade_closed_confirmation(
                trade.user_id, trade_data
            )
    
    def _get_exit_reason(self, trade: ActiveTrade) -> str:
        """Get human-readable exit reason"""
        if trade.exit_type == ExitType.STOP_LOSS:
            return "Stop loss hit"
        elif trade.exit_type == ExitType.TAKE_PROFIT:
            return "Take profit hit"
        elif trade.exit_type == ExitType.TRAILING_STOP:
            return "Trailing stop hit"
        elif trade.exit_type == ExitType.PARACHUTE:
            return "Parachute exit (no XP penalty)"
        elif trade.exit_type == ExitType.EMERGENCY:
            return "Emergency close"
        elif trade.exit_type == ExitType.CHAINGUN:
            return "Chaingun mode exit"
        elif trade.exit_type == ExitType.PROFIT_RUNNER:
            return "Profit runner partial close"
        else:
            return "Manual close"
    
    def _send_exit_to_xp_system(self, exit_data: Dict):
        """Send exit data to XP calculation system"""
        # In production, this would send to the XP microservice
        logger.info(f"Sending exit data to XP system: {exit_data['trade_id']} - "
                   f"Exit type: {exit_data['exit_type']}, "
                   f"P&L: {exit_data['pnl_pips']:.1f} pips, "
                   f"No XP penalty: {exit_data['no_xp_penalty']}")
    
    def get_exit_history(self, user_id: Optional[int] = None) -> List[Dict]:
        """Get exit history, optionally filtered by user"""
        if user_id:
            return [exit for exit in self.exit_history if exit['user_id'] == user_id]
        return self.exit_history.copy()
    
    async def start_monitoring(self):
        """Start the trade monitoring loop"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Trade monitoring started")
    
    async def stop_monitoring(self):
        """Stop the trade monitoring loop"""
        self.monitoring = False
        if self.monitor_task:
            await self.monitor_task
        logger.info("Trade monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Update prices (would come from broker feed)
                await self._update_prices()
                
                # Check each active trade
                for trade_id, trade in list(self.active_trades.items()):
                    await self._manage_trade(trade)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _update_prices(self):
        """Update current market prices"""
        # In production, this would connect to broker price feed
        # For now, simulate with small random movements
        import random
        
        for symbol in self.symbol_specs.keys():
            if symbol not in self.current_prices:
                # Initialize with dummy prices
                self.current_prices[symbol] = {
                    'XAUUSD': 1950.00,
                    'EURUSD': 1.0800,
                    'GBPUSD': 1.2500,
                    'USDJPY': 145.00,
                    'USDCAD': 1.3500,
                    'GBPJPY': 180.00
                }.get(symbol, 1.0000)
            
            # Small random movement for testing
            change = random.uniform(-0.0005, 0.0005)
            self.current_prices[symbol] *= (1 + change)
    
    async def _manage_trade(self, trade: ActiveTrade):
        """Apply management rules to a single trade"""
        current_price = self.current_prices.get(trade.symbol)
        if not current_price:
            return
        
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', 0.0001)
        
        # Update P&L
        trade.update_pnl(current_price, pip_value)
        
        # Check exit conditions first
        await self.check_exit_conditions(trade, current_price)
        
        # If trade is still active, apply management plans
        if trade.trade_id in self.active_trades:
            # Check each management plan
            for plan in trade.management_plans:
                await self._execute_plan(trade, plan, current_price, pip_value)
    
    async def _execute_plan(self, trade: ActiveTrade, plan: TradeManagementPlan, 
                           current_price: float, pip_value: float):
        """Execute a specific management plan"""
        
        # Breakeven
        if (plan.feature == TradeManagementFeature.BREAKEVEN and 
            not trade.is_breakeven and 
            trade.current_pnl_pips >= plan.breakeven_trigger_pips):
            
            await self._move_to_breakeven(trade, 0)
            trade.is_breakeven = True
            
        # Breakeven Plus
        elif (plan.feature == TradeManagementFeature.BREAKEVEN_PLUS and 
              not trade.is_breakeven and 
              trade.current_pnl_pips >= plan.breakeven_trigger_pips):
            
            await self._move_to_breakeven(trade, plan.breakeven_plus_pips)
            trade.is_breakeven = True
            
        # Trailing Stop
        elif (plan.feature == TradeManagementFeature.TRAILING_STOP and 
              trade.current_pnl_pips >= plan.trailing_start_pips):
            
            await self._trail_stop(trade, plan, current_price, pip_value)
            
        # Partial Close
        elif (plan.feature == TradeManagementFeature.PARTIAL_CLOSE and 
              trade.partial_closed < plan.partial_close_percent and
              trade.current_pnl_pips >= plan.partial_close_at_pips):
            
            await self._partial_close(trade, plan.partial_close_percent)
            
        # Runner Mode
        elif (plan.feature == TradeManagementFeature.RUNNER_MODE and 
              trade.current_pnl_pips >= plan.partial_close_at_pips):
            
            if trade.partial_closed < plan.partial_close_percent:
                # Use profit runner exit for runner mode
                await self.execute_profit_runner_exit(trade.trade_id, plan.partial_close_percent)
                # Move to breakeven after partial close
                if trade.trade_id in self.active_trades:  # Check if still active
                    await self._move_to_breakeven(trade, 0)
                    trade.is_breakeven = True
            
        # Zero Risk Runner
        elif (plan.feature == TradeManagementFeature.ZERO_RISK_RUNNER and 
              trade.current_pnl_pips >= plan.partial_close_at_pips):
            
            if trade.partial_closed < plan.partial_close_percent:
                await self.execute_profit_runner_exit(trade.trade_id, plan.partial_close_percent)
                if trade.trade_id in self.active_trades:  # Check if still active
                    await self._move_to_breakeven(trade, plan.breakeven_plus_pips)
                    trade.is_breakeven = True
                    self._notify(f"🎯 ZERO RISK ACTIVATED on {trade.symbol}! Running risk-free to the moon! 🚀")
            
        # Leroy Jenkins Mode
        elif plan.feature == TradeManagementFeature.LEROY_JENKINS:
            # Aggressive management
            if trade.current_pnl_pips >= plan.partial_close_at_pips and trade.partial_closed == 0:
                await self._partial_close(trade, plan.partial_close_percent)
                self._notify(f"🔥 LEEEEROYYY JENKINS! Secured {plan.partial_close_percent}% on {trade.symbol}!")
            
            # Super tight trailing
            if trade.current_pnl_pips >= plan.trailing_start_pips:
                await self._trail_stop(trade, plan, current_price, pip_value)
    
    async def _move_to_breakeven(self, trade: ActiveTrade, plus_pips: float):
        """Move stop loss to breakeven (plus optional pips)"""
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', 0.0001)
        old_sl = trade.current_sl
        
        if trade.direction == "BUY":
            new_sl = trade.entry_price + (plus_pips * pip_value)
            if new_sl > trade.current_sl:
                success = await self._modify_stop_loss(trade, new_sl)
                if success:
                    trade.current_sl = new_sl
                    self._notify(f"✅ Moved {trade.symbol} to breakeven{f'+{plus_pips}' if plus_pips > 0 else ''}")
                    
                    # Send breakeven confirmation
                    if self.confirmation_system:
                        await self._send_breakeven_confirmation(trade, old_sl, plus_pips)
        else:
            new_sl = trade.entry_price - (plus_pips * pip_value)
            if new_sl < trade.current_sl:
                success = await self._modify_stop_loss(trade, new_sl)
                if success:
                    trade.current_sl = new_sl
                    self._notify(f"✅ Moved {trade.symbol} to breakeven{f'+{plus_pips}' if plus_pips > 0 else ''}")
                    
                    # Send breakeven confirmation
                    if self.confirmation_system:
                        await self._send_breakeven_confirmation(trade, old_sl, plus_pips)
    
    async def _send_breakeven_confirmation(self, trade: ActiveTrade, old_sl: float, plus_pips: float):
        """Send breakeven move confirmation"""
        breakeven_data = {
            'trade_id': trade.trade_id,
            'ticket': trade.ticket,
            'symbol': trade.symbol,
            'new_stop_loss': trade.current_sl,
            'entry_price': trade.entry_price,
            'current_pnl_pips': trade.current_pnl_pips,
            'metadata': {
                'old_stop_loss': old_sl,
                'breakeven_plus_pips': plus_pips,
                'trigger_pips': trade.current_pnl_pips
            }
        }
        
        await self.confirmation_system.send_breakeven_moved_confirmation(
            trade.user_id, breakeven_data
        )
    
    async def _trail_stop(self, trade: ActiveTrade, plan: TradeManagementPlan, 
                         current_price: float, pip_value: float):
        """Trail the stop loss"""
        old_sl = trade.current_sl
        
        if trade.direction == "BUY":
            trail_price = current_price - (plan.trailing_distance_pips * pip_value)
            if trail_price > trade.current_sl and (not trade.last_trail_price or 
                current_price >= trade.last_trail_price + plan.trailing_step_pips * pip_value):
                success = await self._modify_stop_loss(trade, trail_price)
                if success:
                    trade.current_sl = trail_price
                    trade.last_trail_price = current_price
                    trade.is_trailing = True
                    
                    # Send trailing stop confirmation
                    if self.confirmation_system:
                        await self._send_trailing_stop_confirmation(trade, old_sl, plan.trailing_distance_pips, current_price)
        else:
            trail_price = current_price + (plan.trailing_distance_pips * pip_value)
            if trail_price < trade.current_sl and (not trade.last_trail_price or 
                current_price <= trade.last_trail_price - plan.trailing_step_pips * pip_value):
                success = await self._modify_stop_loss(trade, trail_price)
                if success:
                    trade.current_sl = trail_price
                    trade.last_trail_price = current_price
                    trade.is_trailing = True
                    
                    # Send trailing stop confirmation
                    if self.confirmation_system:
                        await self._send_trailing_stop_confirmation(trade, old_sl, plan.trailing_distance_pips, current_price)
    
    async def _send_trailing_stop_confirmation(self, trade: ActiveTrade, old_sl: float, 
                                             trail_distance: float, current_price: float):
        """Send trailing stop move confirmation"""
        trail_data = {
            'trade_id': trade.trade_id,
            'ticket': trade.ticket,
            'symbol': trade.symbol,
            'new_stop_loss': trade.current_sl,
            'current_pnl_pips': trade.current_pnl_pips,
            'metadata': {
                'old_stop_loss': old_sl,
                'trail_distance': trail_distance,
                'current_price': current_price
            }
        }
        
        await self.confirmation_system.send_trailing_stop_moved_confirmation(
            trade.user_id, trail_data
        )
    
    async def _partial_close(self, trade: ActiveTrade, percent: float):
        """Partially close a position"""
        close_volume = trade.volume * (percent / 100)
        close_volume = round(close_volume, 2)
        
        if close_volume >= 0.01:  # Minimum lot size
            result = await self._close_partial_position(trade, close_volume)
            if result:
                old_volume = trade.volume
                trade.partial_closed += percent
                trade.volume -= close_volume
                self._notify(f"💰 Closed {percent}% of {trade.symbol} at {trade.current_pnl_pips:.1f} pips profit!")
                
                # Send partial close confirmation
                if self.confirmation_system:
                    await self._send_partial_close_confirmation(trade, close_volume, percent, old_volume)
    
    async def _send_partial_close_confirmation(self, trade: ActiveTrade, closed_volume: float, 
                                             closed_percent: float, original_volume: float):
        """Send partial close confirmation"""
        current_price = self.current_prices.get(trade.symbol, trade.entry_price)
        
        partial_data = {
            'trade_id': trade.trade_id,
            'ticket': trade.ticket,
            'symbol': trade.symbol,
            'direction': trade.direction,
            'closed_volume': closed_volume,
            'exit_price': current_price,
            'pnl_pips': trade.current_pnl_pips,
            'pnl_dollars': trade.current_pnl_pips * 10,  # Approximate
            'reason': f'Partial close ({closed_percent:.1f}%)',
            'metadata': {
                'remaining_volume': trade.volume,
                'closed_percent': closed_percent,
                'original_volume': original_volume,
                'total_closed_percent': trade.partial_closed
            }
        }
        
        await self.confirmation_system.send_partial_close_confirmation(
            trade.user_id, partial_data
        )
    
    async def _modify_stop_loss(self, trade: ActiveTrade, new_sl: float) -> bool:
        """Send stop loss modification to MT5"""
        # Create modification instruction
        instruction = {
            'action': 'modify',
            'ticket': trade.ticket,
            'sl': new_sl,
            'tp': trade.current_tp
        }
        
        # In production, this would send to MT5
        logger.info(f"Modifying SL for {trade.ticket}: {new_sl}")
        
        # For now, simulate success
        return True
    
    async def _close_partial_position(self, trade: ActiveTrade, volume: float) -> bool:
        """Send partial close to MT5"""
        # Create close instruction
        instruction = {
            'action': 'close_partial',
            'ticket': trade.ticket,
            'volume': volume
        }
        
        logger.info(f"Partial closing {volume} lots of {trade.ticket}")
        
        # For now, simulate success
        return True
    
    def _notify(self, message: str, sound_type: Optional[str] = None, event_type: Optional[str] = None):
        """Add notification for UI with optional sound"""
        from .user_settings import should_play_sound
        
        notification = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'type': 'trade_management',
            'event_type': event_type or 'general'
        }
        
        # Check if sound should be played
        if sound_type and hasattr(self, 'user_id'):
            should_play = should_play_sound(str(self.user_id), sound_type)
            notification['play_sound'] = sound_type if should_play else None
        
        self.notifications.append(notification)
        logger.info(f"Notification: {message}")
    
    async def activate_parachute_exit(self, trade_id: str) -> bool:
        """
        Activate parachute exit protocol - immediate exit with no XP penalty
        Used for emergency situations where trader needs to exit quickly
        """
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False
        
        trade.parachute_activated = True
        trade.exit_type = ExitType.PARACHUTE
        
        # Close the entire position immediately
        result = await self._close_full_position(trade)
        if result:
            trade.exit_time = datetime.now()
            trade.exit_price = self.current_prices.get(trade.symbol, trade.entry_price)
            trade.exit_pnl_pips = trade.current_pnl_pips
            
            self._notify(f"🪂 PARACHUTE EXIT on {trade.symbol}! Position closed at {trade.current_pnl_pips:.1f} pips (NO XP PENALTY)")
            self.remove_trade(trade_id)
            
        return result
    
    async def activate_chaingun_mode(self, trade_id: str, exit_percent: float = 10.0) -> bool:
        """
        Activate chaingun fire mode - rapid partial exits
        Allows multiple quick exits without waiting
        """
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False
        
        trade.chaingun_mode = True
        trade.exit_type = ExitType.CHAINGUN
        
        # Execute rapid partial close
        if trade.volume * (exit_percent / 100) >= 0.01:  # Check minimum lot
            result = await self._partial_close(trade, exit_percent)
            if result:
                self._notify(f"🔫 CHAINGUN EXIT! Closed {exit_percent}% of {trade.symbol} - RAT-TAT-TAT!")
                
                # If fully closed, remove from management
                if trade.partial_closed >= 100:
                    trade.exit_time = datetime.now()
                    trade.exit_price = self.current_prices.get(trade.symbol, trade.entry_price)
                    trade.exit_pnl_pips = trade.current_pnl_pips
                    self.remove_trade(trade_id)
            
            return result
        
        return False
    
    async def execute_profit_runner_exit(self, trade_id: str, exit_percent: float) -> bool:
        """
        Execute profit runner partial exit
        Used when runner mode triggers partial close
        """
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False
        
        trade.exit_type = ExitType.PROFIT_RUNNER
        
        result = await self._partial_close(trade, exit_percent)
        if result:
            self._notify(f"🏃 PROFIT RUNNER EXIT! Secured {exit_percent}% of {trade.symbol} at {trade.current_pnl_pips:.1f} pips!")
            
            # Track partial exit
            if trade.partial_closed >= 100:
                trade.exit_time = datetime.now()
                trade.exit_price = self.current_prices.get(trade.symbol, trade.entry_price)
                trade.exit_pnl_pips = trade.current_pnl_pips
                self.remove_trade(trade_id)
        
        return result
    
    async def execute_trailing_stop_exit(self, trade_id: str) -> bool:
        """
        Execute exit via trailing stop hit
        """
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False
        
        trade.exit_type = ExitType.TRAILING_STOP
        trade.exit_time = datetime.now()
        trade.exit_price = trade.current_sl  # Exit at stop price
        
        # Calculate exit P&L
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', 0.0001)
        if trade.direction == "BUY":
            trade.exit_pnl_pips = (trade.exit_price - trade.entry_price) / pip_value
        else:
            trade.exit_pnl_pips = (trade.entry_price - trade.exit_price) / pip_value
        
        result = await self._close_full_position(trade)
        if result:
            self._notify(f"📈 TRAILING STOP EXIT on {trade.symbol}! Closed at {trade.exit_pnl_pips:.1f} pips profit!")
            self.remove_trade(trade_id)
        
        return result
    
    async def approve_emergency_exit(self, trade_id: str, approval_code: str) -> bool:
        """
        Approve emergency exit with special authorization
        Requires approval code from risk management system
        """
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False
        
        # Verify approval code (would check against risk system in production)
        if approval_code.startswith("EMRG-"):
            trade.emergency_approved = True
            trade.exit_type = ExitType.EMERGENCY
            
            result = await self._close_full_position(trade)
            if result:
                trade.exit_time = datetime.now()
                trade.exit_price = self.current_prices.get(trade.symbol, trade.entry_price)
                trade.exit_pnl_pips = trade.current_pnl_pips
                
                self._notify(f"🚨 EMERGENCY EXIT APPROVED on {trade.symbol}! Position closed at {trade.exit_pnl_pips:.1f} pips")
                self.remove_trade(trade_id)
            
            return result
        
        return False
    
    async def _close_full_position(self, trade: ActiveTrade) -> bool:
        """Close entire position"""
        instruction = {
            'action': 'close',
            'ticket': trade.ticket,
            'volume': trade.volume
        }
        
        logger.info(f"Closing full position for {trade.ticket}")
        
        # For now, simulate success
        return True
    
    def get_trade_status(self, trade_id: str) -> Optional[Dict]:
        """Get current status of a managed trade"""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return None
        
        current_price = self.current_prices.get(trade.symbol, trade.entry_price)
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', 0.0001)
        
        return {
            'trade_id': trade.trade_id,
            'symbol': trade.symbol,
            'direction': trade.direction,
            'entry_price': trade.entry_price,
            'current_price': current_price,
            'current_sl': trade.current_sl,
            'current_tp': trade.current_tp,
            'volume': trade.volume,
            'pnl_pips': trade.current_pnl_pips,
            'pnl_dollars': trade.current_pnl_pips * pip_value * trade.volume * 100000,  # Approximate
            'is_breakeven': trade.is_breakeven,
            'is_trailing': trade.is_trailing,
            'partial_closed': trade.partial_closed,
            'peak_pips': abs(trade.peak_price - trade.entry_price) / pip_value if trade.peak_price else 0,
            'active_features': [plan.feature.value for plan in trade.management_plans],
            'exit_type': trade.exit_type.value if trade.exit_type else None,
            'parachute_activated': trade.parachute_activated,
            'emergency_approved': trade.emergency_approved,
            'chaingun_mode': trade.chaingun_mode
        }
    
    def get_exit_data_for_xp(self, trade: ActiveTrade) -> Dict:
        """
        Get exit data formatted for XP system
        Returns data needed to calculate XP impact
        """
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', 0.0001)
        
        return {
            'trade_id': trade.trade_id,
            'user_id': trade.user_id,
            'symbol': trade.symbol,
            'exit_type': trade.exit_type.value if trade.exit_type else ExitType.MANUAL.value,
            'exit_time': trade.exit_time.isoformat() if trade.exit_time else datetime.now().isoformat(),
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price or self.current_prices.get(trade.symbol, trade.entry_price),
            'pnl_pips': trade.exit_pnl_pips or trade.current_pnl_pips,
            'volume': trade.volume,
            'duration_minutes': (trade.exit_time - trade.open_time).total_seconds() / 60 if trade.exit_time else 0,
            'peak_pips': abs(trade.peak_price - trade.entry_price) / pip_value if trade.peak_price else 0,
            'partial_closed_percent': trade.partial_closed,
            'hit_breakeven': trade.is_breakeven,
            'used_trailing': trade.is_trailing,
            'no_xp_penalty': trade.exit_type in [ExitType.PARACHUTE, ExitType.EMERGENCY] if trade.exit_type else False
        }
    
    async def check_exit_conditions(self, trade: ActiveTrade, current_price: float):
        """
        Check if any automatic exit conditions are met
        Called during the monitoring loop
        """
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', 0.0001)
        
        # Check if trailing stop is hit
        if trade.is_trailing:
            if trade.direction == "BUY" and current_price <= trade.current_sl:
                await self.execute_trailing_stop_exit(trade.trade_id)
            elif trade.direction == "SELL" and current_price >= trade.current_sl:
                await self.execute_trailing_stop_exit(trade.trade_id)
        
        # Check if regular stop loss is hit
        elif not trade.parachute_activated and not trade.emergency_approved:
            if trade.direction == "BUY" and current_price <= trade.current_sl:
                trade.exit_type = ExitType.STOP_LOSS
                trade.exit_time = datetime.now()
                trade.exit_price = trade.current_sl
                trade.exit_pnl_pips = (trade.exit_price - trade.entry_price) / pip_value
                await self._close_full_position(trade)
                self._notify(f"❌ STOP LOSS HIT on {trade.symbol} at {trade.exit_pnl_pips:.1f} pips loss")
                self.remove_trade(trade.trade_id)
            elif trade.direction == "SELL" and current_price >= trade.current_sl:
                trade.exit_type = ExitType.STOP_LOSS
                trade.exit_time = datetime.now()
                trade.exit_price = trade.current_sl
                trade.exit_pnl_pips = (trade.entry_price - trade.exit_price) / pip_value
                await self._close_full_position(trade)
                self._notify(f"❌ STOP LOSS HIT on {trade.symbol} at {trade.exit_pnl_pips:.1f} pips loss")
                self.remove_trade(trade.trade_id)
        
        # Check if take profit is hit
        if trade.current_tp > 0:
            if trade.direction == "BUY" and current_price >= trade.current_tp:
                trade.exit_type = ExitType.TAKE_PROFIT
                trade.exit_time = datetime.now()
                trade.exit_price = trade.current_tp
                trade.exit_pnl_pips = (trade.exit_price - trade.entry_price) / pip_value
                await self._close_full_position(trade)
                self._notify(f"🎯 TAKE PROFIT HIT on {trade.symbol} at {trade.exit_pnl_pips:.1f} pips profit!", 
                           sound_type="cash_register", event_type="tp_hit")
                self.remove_trade(trade.trade_id)
            elif trade.direction == "SELL" and current_price <= trade.current_tp:
                trade.exit_type = ExitType.TAKE_PROFIT
                trade.exit_time = datetime.now()
                trade.exit_price = trade.current_tp
                trade.exit_pnl_pips = (trade.entry_price - trade.exit_price) / pip_value
                await self._close_full_position(trade)
                self._notify(f"🎯 TAKE PROFIT HIT on {trade.symbol} at {trade.exit_pnl_pips:.1f} pips profit!", 
                           sound_type="cash_register", event_type="tp_hit")
                self.remove_trade(trade.trade_id)


# Example usage
async def example_usage():
    """Example of using the trade manager"""
    from .risk_management import RiskProfile, TradeManagementFeature
    
    # Create manager
    manager = TradeManager()
    
    # Create a profile with high XP
    profile = RiskProfile(
        user_id=123456,
        current_xp=20000,  # Unlocks Leroy Jenkins
        tier_level="APEX"
    )
    
    # Get management plans
    plans = []
    unlocked = profile.get_unlocked_features()
    
    # Create an active trade
    trade = ActiveTrade(
        trade_id="T123456",
        ticket=987654,
        symbol="XAUUSD",
        direction="BUY",
        entry_price=1950.00,
        current_sl=1945.00,
        current_tp=1960.00,
        original_sl=1945.00,
        volume=0.10,
        open_time=datetime.now(),
        management_plans=plans,
        user_id=123456
    )
    
    # Add to manager
    manager.add_trade(trade)
    
    # Start monitoring
    await manager.start_monitoring()
    
    # Let it run for a bit
    await asyncio.sleep(30)
    
    # Check status
    status = manager.get_trade_status("T123456")
    print(f"Trade status: {status}")
    
    # Stop monitoring
    await manager.stop_monitoring()