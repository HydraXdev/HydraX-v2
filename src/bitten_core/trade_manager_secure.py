"""
BITTEN Trade Management Executor - SECURE VERSION
Handles advanced trade modifications and monitoring
Enhanced with security features from security_utils.py
"""

import asyncio
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from decimal import Decimal

from .risk_management_secure import TradeManagementPlan, TradeManagementFeature, RiskProfile
from .mt5_bridge_adapter_secure import get_bridge_adapter
from .security_utils import (
    validate_symbol, validate_price, validate_volume,
    sanitize_log_output, ValidationError, SecurityError
)

logger = logging.getLogger(__name__)

# Thread safety lock for active trades dictionary
_trades_lock = threading.RLock()

@dataclass
class ActiveTrade:
    """Active trade being managed"""
    trade_id: str
    ticket: int
    symbol: str
    direction: str  # BUY or SELL
    entry_price: Decimal
    current_sl: Decimal
    current_tp: Decimal
    original_sl: Decimal
    volume: Decimal
    open_time: datetime
    management_plans: List[TradeManagementPlan]
    user_id: int
    
    # Management state
    is_breakeven: bool = False
    is_trailing: bool = False
    partial_closed: Decimal = Decimal('0')  # Percentage already closed
    last_trail_price: Decimal = Decimal('0')
    peak_price: Decimal = Decimal('0')  # Highest/lowest price reached
    current_pnl_pips: Decimal = Decimal('0')
    
    def __post_init__(self):
        """Validate trade data"""
        self.symbol = validate_symbol(self.symbol)
        self.entry_price = validate_price(self.entry_price)
        self.current_sl = validate_price(self.current_sl) if self.current_sl > 0 else Decimal('0')
        self.current_tp = validate_price(self.current_tp) if self.current_tp > 0 else Decimal('0')
        self.original_sl = validate_price(self.original_sl) if self.original_sl > 0 else Decimal('0')
        self.volume = validate_volume(self.volume)
        
        if self.direction not in ['BUY', 'SELL']:
            raise ValidationError(f"Invalid direction: {self.direction}")
        
        if self.user_id < 0:
            raise ValidationError(f"Invalid user ID: {self.user_id}")
    
    def update_pnl(self, current_price: Decimal, pip_value: Decimal):
        """Update current P&L in pips"""
        current_price = validate_price(current_price)
        pip_value = validate_price(pip_value)
        
        if pip_value == 0:
            raise ValidationError("Pip value cannot be zero")
        
        if self.direction == "BUY":
            self.current_pnl_pips = (current_price - self.entry_price) / pip_value
            self.peak_price = max(self.peak_price or current_price, current_price)
        else:
            self.current_pnl_pips = (self.entry_price - current_price) / pip_value
            self.peak_price = min(self.peak_price or current_price, current_price)

class TradeManager:
    """
    Advanced trade management system - SECURE VERSION
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
        self._price_lock = threading.Lock()
        
        # Symbol specifications
        self.symbol_specs = {
            'XAUUSD': {'pip_value': Decimal('0.1')},
            'EURUSD': {'pip_value': Decimal('0.0001')},
            'GBPUSD': {'pip_value': Decimal('0.0001')},
            'USDJPY': {'pip_value': Decimal('0.01')},
            'USDCAD': {'pip_value': Decimal('0.0001')},
            'GBPJPY': {'pip_value': Decimal('0.01')}
        }
        
        # Notifications queue for UI updates
        self.notifications = []
        self._notifications_lock = threading.Lock()
        
        # Maximum trades to manage
        self.max_managed_trades = 100
        
    def add_trade(self, trade: ActiveTrade):
        """Add a trade to be managed"""
        with _trades_lock:
            # Check maximum trades limit
            if len(self.active_trades) >= self.max_managed_trades:
                raise SecurityError(f"Maximum managed trades limit reached: {self.max_managed_trades}")
            
            # Validate trade doesn't already exist
            if trade.trade_id in self.active_trades:
                raise ValidationError(f"Trade {trade.trade_id} already being managed")
            
            self.active_trades[trade.trade_id] = trade
            logger.info(f"Added trade {trade.trade_id} for management")
            
            # Initialize peak price
            if trade.direction == "BUY":
                trade.peak_price = trade.entry_price
            else:
                trade.peak_price = trade.entry_price
    
    def remove_trade(self, trade_id: str):
        """Remove a trade from management"""
        with _trades_lock:
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
        error_count = 0
        max_consecutive_errors = 10
        
        while self.monitoring:
            try:
                # Update prices (would come from broker feed)
                await self._update_prices()
                
                # Check each active trade
                with _trades_lock:
                    trades_to_check = list(self.active_trades.items())
                
                for trade_id, trade in trades_to_check:
                    await self._manage_trade(trade)
                
                # Reset error count on successful iteration
                error_count = 0
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error in monitor loop: {sanitize_log_output(str(e))}")
                
                # Stop monitoring if too many consecutive errors
                if error_count >= max_consecutive_errors:
                    logger.error("Too many consecutive errors, stopping monitor")
                    self.monitoring = False
                    break
            
            await asyncio.sleep(self.check_interval)
    
    async def _update_prices(self):
        """Update current market prices"""
        # In production, this would connect to broker price feed
        # For now, simulate with small random movements
        import random
        
        with self._price_lock:
            for symbol in self.symbol_specs.keys():
                if symbol not in self.current_prices:
                    # Initialize with dummy prices
                    self.current_prices[symbol] = {
                        'XAUUSD': Decimal('1950.00'),
                        'EURUSD': Decimal('1.0800'),
                        'GBPUSD': Decimal('1.2500'),
                        'USDJPY': Decimal('145.00'),
                        'USDCAD': Decimal('1.3500'),
                        'GBPJPY': Decimal('180.00')
                    }.get(symbol, Decimal('1.0000'))
                
                # Small random movement for testing
                change = Decimal(str(random.uniform(-0.0005, 0.0005)))
                self.current_prices[symbol] *= (Decimal('1') + change)
                self.current_prices[symbol] = self.current_prices[symbol].quantize(Decimal('0.00001'))
    
    async def _manage_trade(self, trade: ActiveTrade):
        """Apply management rules to a single trade"""
        with self._price_lock:
            current_price = self.current_prices.get(trade.symbol)
        
        if not current_price:
            return
        
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', Decimal('0.0001'))
        
        try:
            # Update P&L
            trade.update_pnl(current_price, pip_value)
            
            # Check each management plan
            for plan in trade.management_plans:
                await self._execute_plan(trade, plan, current_price, pip_value)
        except Exception as e:
            logger.error(f"Error managing trade {trade.trade_id}: {sanitize_log_output(str(e))}")
    
    async def _execute_plan(self, trade: ActiveTrade, plan: TradeManagementPlan, 
                           current_price: Decimal, pip_value: Decimal):
        """Execute a specific management plan"""
        
        # Breakeven
        if (plan.feature == TradeManagementFeature.BREAKEVEN and 
            not trade.is_breakeven and 
            trade.current_pnl_pips >= plan.breakeven_trigger_pips):
            
            await self._move_to_breakeven(trade, Decimal('0'))
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
                await self._move_to_breakeven(trade, Decimal('0'))
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
    
    async def _move_to_breakeven(self, trade: ActiveTrade, plus_pips: Decimal):
        """Move stop loss to breakeven (plus optional pips)"""
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', Decimal('0.0001'))
        
        if trade.direction == "BUY":
            new_sl = trade.entry_price + (plus_pips * pip_value)
            if new_sl > trade.current_sl:
                success = await self._modify_stop_loss(trade, new_sl)
                if success:
                    trade.current_sl = new_sl
                    plus_str = f'+{plus_pips}' if plus_pips > 0 else ''
                    self._notify(f"✅ Moved {trade.symbol} to breakeven{plus_str}")
        else:
            new_sl = trade.entry_price - (plus_pips * pip_value)
            if new_sl < trade.current_sl:
                success = await self._modify_stop_loss(trade, new_sl)
                if success:
                    trade.current_sl = new_sl
                    plus_str = f'+{plus_pips}' if plus_pips > 0 else ''
                    self._notify(f"✅ Moved {trade.symbol} to breakeven{plus_str}")
    
    async def _trail_stop(self, trade: ActiveTrade, plan: TradeManagementPlan, 
                         current_price: Decimal, pip_value: Decimal):
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
    
    async def _partial_close(self, trade: ActiveTrade, percent: Decimal):
        """Partially close a position"""
        # Validate percent
        if percent <= 0 or percent > 100:
            raise ValidationError(f"Invalid partial close percent: {percent}")
        
        # Prevent closing more than 100%
        if trade.partial_closed + percent > 100:
            percent = Decimal('100') - trade.partial_closed
        
        close_volume = trade.volume * (percent / Decimal('100'))
        close_volume = close_volume.quantize(Decimal('0.01'))
        
        if close_volume >= Decimal('0.01'):  # Minimum lot size
            result = await self._close_partial_position(trade, close_volume)
            if result:
                trade.partial_closed += percent
                trade.volume -= close_volume
                self._notify(f"💰 Closed {percent}% of {trade.symbol} at {trade.current_pnl_pips:.1f} pips profit!")
    
    async def _modify_stop_loss(self, trade: ActiveTrade, new_sl: Decimal) -> bool:
        """Send stop loss modification to MT5"""
        try:
            # Validate new stop loss
            new_sl = validate_price(new_sl)
            
            # Create modification instruction
            instruction = {
                'action': 'modify',
                'ticket': trade.ticket,
                'sl': float(new_sl),
                'tp': float(trade.current_tp)
            }
            
            # In production, this would send to MT5
            logger.info(f"Modifying SL for {trade.ticket}: {new_sl}")
            
            # For now, simulate success
            return True
        except Exception as e:
            logger.error(f"Error modifying stop loss: {sanitize_log_output(str(e))}")
            return False
    
    async def _close_partial_position(self, trade: ActiveTrade, volume: Decimal) -> bool:
        """Send partial close to MT5"""
        try:
            # Validate volume
            volume = validate_volume(volume)
            
            # Create close instruction
            instruction = {
                'action': 'close_partial',
                'ticket': trade.ticket,
                'volume': float(volume)
            }
            
            logger.info(f"Partial closing {volume} lots of {trade.ticket}")
            
            # For now, simulate success
            return True
        except Exception as e:
            logger.error(f"Error closing partial position: {sanitize_log_output(str(e))}")
            return False
    
    def _notify(self, message: str):
        """Add notification for UI"""
        with self._notifications_lock:
            # Limit notifications queue size
            if len(self.notifications) >= 1000:
                self.notifications = self.notifications[-500:]  # Keep last 500
            
            notification = {
                'timestamp': datetime.now().isoformat(),
                'message': message,
                'type': 'trade_management'
            }
            self.notifications.append(notification)
            logger.info(f"Notification: {message}")
    
    def get_trade_status(self, trade_id: str) -> Optional[Dict]:
        """Get current status of a managed trade"""
        with _trades_lock:
            trade = self.active_trades.get(trade_id)
        
        if not trade:
            return None
        
        with self._price_lock:
            current_price = self.current_prices.get(trade.symbol, trade.entry_price)
        
        pip_value = self.symbol_specs.get(trade.symbol, {}).get('pip_value', Decimal('0.0001'))
        
        return {
            'trade_id': trade.trade_id,
            'symbol': trade.symbol,
            'direction': trade.direction,
            'entry_price': float(trade.entry_price),
            'current_price': float(current_price),
            'current_sl': float(trade.current_sl),
            'current_tp': float(trade.current_tp),
            'volume': float(trade.volume),
            'pnl_pips': float(trade.current_pnl_pips),
            'pnl_dollars': float(trade.current_pnl_pips * pip_value * trade.volume * 100000),  # Approximate
            'is_breakeven': trade.is_breakeven,
            'is_trailing': trade.is_trailing,
            'partial_closed': float(trade.partial_closed),
            'peak_pips': float(abs(trade.peak_price - trade.entry_price) / pip_value) if trade.peak_price else 0,
            'active_features': [plan.feature.value for plan in trade.management_plans]
        }
    
    def get_all_trades_status(self) -> List[Dict]:
        """Get status of all managed trades"""
        with _trades_lock:
            trade_ids = list(self.active_trades.keys())
        
        statuses = []
        for trade_id in trade_ids:
            status = self.get_trade_status(trade_id)
            if status:
                statuses.append(status)
        
        return statuses


# Example usage
async def example_usage():
    """Example of using the trade manager"""
    from .risk_management_secure import RiskProfile, TradeManagementFeature
    
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
        entry_price=Decimal('1950.00'),
        current_sl=Decimal('1945.00'),
        current_tp=Decimal('1960.00'),
        original_sl=Decimal('1945.00'),
        volume=Decimal('0.10'),
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