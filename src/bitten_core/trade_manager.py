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

from .risk_management import TradeManagementPlan, TradeManagementFeature, RiskProfile
from .mt5_bridge_adapter import get_bridge_adapter

logger = logging.getLogger(__name__)

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
    
    def __init__(self):
        self.adapter = get_bridge_adapter()
        self.active_trades: Dict[str, ActiveTrade] = {}
        self.monitoring = False
        self.monitor_task = None
        self.check_interval = 1.0  # Check every second
        
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
        
    def add_trade(self, trade: ActiveTrade):
        """Add a trade to be managed"""
        self.active_trades[trade.trade_id] = trade
        logger.info(f"Added trade {trade.trade_id} for management")
        
        # Initialize peak price
        if trade.direction == "BUY":
            trade.peak_price = trade.entry_price
        else:
            trade.peak_price = trade.entry_price
    
    def remove_trade(self, trade_id: str):
        """Remove a trade from management"""
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
            logger.info(f"Removed trade {trade_id} from management")
    
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
                await self._partial_close(trade, plan.partial_close_percent)
                # Move to breakeven after partial close
                await self._move_to_breakeven(trade, 0)
                trade.is_breakeven = True
            
        # Zero Risk Runner
        elif (plan.feature == TradeManagementFeature.ZERO_RISK_RUNNER and 
              trade.current_pnl_pips >= plan.partial_close_at_pips):
            
            if trade.partial_closed < plan.partial_close_percent:
                await self._partial_close(trade, plan.partial_close_percent)
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
        
        if trade.direction == "BUY":
            new_sl = trade.entry_price + (plus_pips * pip_value)
            if new_sl > trade.current_sl:
                success = await self._modify_stop_loss(trade, new_sl)
                if success:
                    trade.current_sl = new_sl
                    self._notify(f"✅ Moved {trade.symbol} to breakeven{f'+{plus_pips}' if plus_pips > 0 else ''}")
        else:
            new_sl = trade.entry_price - (plus_pips * pip_value)
            if new_sl < trade.current_sl:
                success = await self._modify_stop_loss(trade, new_sl)
                if success:
                    trade.current_sl = new_sl
                    self._notify(f"✅ Moved {trade.symbol} to breakeven{f'+{plus_pips}' if plus_pips > 0 else ''}")
    
    async def _trail_stop(self, trade: ActiveTrade, plan: TradeManagementPlan, 
                         current_price: float, pip_value: float):
        """Trail the stop loss"""
        if trade.direction == "BUY":
            trail_price = current_price - (plan.trailing_distance_pips * pip_value)
            if trail_price > trade.current_sl and (not trade.last_trail_price or 
                current_price >= trade.last_trail_price + plan.trailing_step_pips * pip_value):
                success = await self._modify_stop_loss(trade, trail_price)
                if success:
                    trade.current_sl = trail_price
                    trade.last_trail_price = current_price
                    trade.is_trailing = True
        else:
            trail_price = current_price + (plan.trailing_distance_pips * pip_value)
            if trail_price < trade.current_sl and (not trade.last_trail_price or 
                current_price <= trade.last_trail_price - plan.trailing_step_pips * pip_value):
                success = await self._modify_stop_loss(trade, trail_price)
                if success:
                    trade.current_sl = trail_price
                    trade.last_trail_price = current_price
                    trade.is_trailing = True
    
    async def _partial_close(self, trade: ActiveTrade, percent: float):
        """Partially close a position"""
        close_volume = trade.volume * (percent / 100)
        close_volume = round(close_volume, 2)
        
        if close_volume >= 0.01:  # Minimum lot size
            result = await self._close_partial_position(trade, close_volume)
            if result:
                trade.partial_closed += percent
                trade.volume -= close_volume
                self._notify(f"💰 Closed {percent}% of {trade.symbol} at {trade.current_pnl_pips:.1f} pips profit!")
    
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
    
    def _notify(self, message: str):
        """Add notification for UI"""
        notification = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'type': 'trade_management'
        }
        self.notifications.append(notification)
        logger.info(f"Notification: {message}")
    
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
            'active_features': [plan.feature.value for plan in trade.management_plans]
        }


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