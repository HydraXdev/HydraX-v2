#!/usr/bin/env python3
"""
Complete BITTEN Signal Flow V2
Enhanced with two-way MT5 communication and advanced trade management
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
import json
import os
from .mt5_enhanced_adapter import MT5EnhancedAdapter, MT5AccountMonitor

# Import existing components (we'll keep compatibility)
from .market_analyzer import MarketAnalyzer 
from .tcs_engine import TCSEngine
from .signal_alerts import SignalAlerts
from .live_data_filter import LiveDataFilter

logger = logging.getLogger(__name__)

@dataclass
class ActiveSignal:
    """Enhanced signal tracking with live data"""
    id: str
    data: Dict
    timestamp: datetime
    tcs_score: float
    fired_by: set
    executions: Dict[int, Dict]  # user_id -> execution data

class EnhancedSignalFlow:
    """
    Enhanced signal flow with account-aware trading and advanced management
    """
    
    def __init__(self, 
                 market_analyzer=None,
                 tcs_engine=None, 
                 signal_alerts=None,
                 webapp_url: str = "https://joinbitten.com",
                 bot_token: str = None,
                 chat_id: str = None):
        
        # Initialize components
        self.market_analyzer = market_analyzer or MarketAnalyzer()
        self.tcs_engine = tcs_engine or TCSEngine()
        self.signal_alerts = signal_alerts or SignalAlerts(bot_token, chat_id)
        self.webapp_url = webapp_url
        
        # Initialize enhanced MT5 adapter
        self.mt5_adapter = MT5EnhancedAdapter()
        self.account_monitor = MT5AccountMonitor(self.mt5_adapter)
        
        # Initialize live data filter for farm
        self.live_filter = LiveDataFilter()
        
        # Track active signals
        self.active_signals: Dict[str, ActiveSignal] = {}
        
        # Background tasks
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """Start monitoring with account awareness"""
        logger.info("Starting enhanced signal monitoring...")
        
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        
        # Also start account monitoring
        asyncio.create_task(self._monitor_account())
        
    async def _monitor_loop(self):
        """Main monitoring loop with live filtering"""
        while True:
            try:
                # Check account status first
                session_stats = self.account_monitor.get_session_stats()
                
                if not session_stats.get('can_trade'):
                    logger.warning(f"Trading disabled: {session_stats.get('risk_status')}")
                    await asyncio.sleep(60)  # Wait longer if can't trade
                    continue
                
                # Get market data
                symbols = await self._get_active_symbols()
                
                for symbol in symbols:
                    # Check if we should analyze this symbol
                    if not self._should_analyze_symbol(symbol):
                        continue
                    
                    # Run analysis
                    signal = await self._analyze_symbol(symbol)
                    
                    if signal:
                        # Apply live filter
                        if self.live_filter.should_take_signal(signal):
                            await self._process_signal(signal)
                        else:
                            logger.info(f"Signal filtered out: {symbol}")
                
                await asyncio.sleep(5)  # 5 second cycle
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_account(self):
        """Monitor account health and send alerts"""
        last_alert_time = None
        
        while True:
            try:
                stats = self.account_monitor.get_session_stats()
                
                # Check for critical conditions
                if stats.get('risk_status') == 'CRITICAL':
                    if not last_alert_time or (datetime.now() - last_alert_time) > timedelta(minutes=30):
                        await self._send_risk_alert(stats)
                        last_alert_time = datetime.now()
                
                # Log session stats
                if stats.get('session_pl', 0) != 0:
                    logger.info(
                        f"Session P&L: ${stats['session_pl']:.2f} "
                        f"({stats['session_pl_percent']:.2f}%) | "
                        f"Positions: {stats['open_positions']}"
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Account monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _get_active_symbols(self) -> List[str]:
        """Get symbols to monitor based on market conditions"""
        # Start with main pairs
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        
        # Add more based on volatility or news
        market_data = self.mt5_adapter.get_market_data()
        if market_data:
            # Could add logic to include high-volatility pairs
            pass
        
        return symbols
    
    def _should_analyze_symbol(self, symbol: str) -> bool:
        """Check if we should analyze this symbol"""
        positions = self.mt5_adapter.get_positions()
        
        # Check symbol exposure
        symbol_positions = [
            p for p in positions.get('positions', []) 
            if p.get('symbol') == symbol
        ]
        
        # Skip if already have 2 positions in this symbol
        if len(symbol_positions) >= 2:
            return False
        
        return True
    
    async def _analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Analyze symbol for trading opportunity"""
        # Get market data
        market_state = await self.market_analyzer.analyze(symbol)
        
        if not market_state or not market_state.get('signal'):
            return None
        
        # Calculate TCS score
        tcs_score = self.tcs_engine.calculate(market_state)
        
        # Check minimum score
        if tcs_score < 70:
            return None
        
        # Build signal
        signal = {
            'pair': symbol,
            'signal': market_state['signal'],  # BUY/SELL
            'entry': market_state['entry'],
            'sl': market_state.get('sl'),
            'tp': market_state.get('tp'),
            'tcs_score': tcs_score,
            'indicators': market_state.get('indicators', {}),
            'timeframe': 'M5'
        }
        
        return signal
    
    async def _process_signal(self, signal: Dict):
        """Process new signal with enhanced features"""
        # Create signal ID
        signal_id = f"SIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{signal['pair']}"
        
        # Store signal
        self.active_signals[signal_id] = ActiveSignal(
            id=signal_id,
            data=signal,
            timestamp=datetime.now(),
            tcs_score=signal['tcs_score'],
            fired_by=set(),
            executions={}
        )
        
        # Send alert via Telegram
        await self.signal_alerts.send_signal(
            signal_id=signal_id,
            pair=signal['pair'],
            direction=signal['signal'],
            confidence=signal['tcs_score'],
            webapp_url=f"{self.webapp_url}/mission/{signal_id}"
        )
        
        logger.info(f"Signal sent: {signal_id} - {signal['pair']} {signal['signal']} @ {signal['tcs_score']}%")
    
    async def handle_fire_action(self, user_id: int, signal_id: str) -> Dict:
        """
        Handle when user fires on a signal from WebApp
        Now with enhanced MT5 integration!
        """
        if signal_id not in self.active_signals:
            return {'success': False, 'message': 'Signal expired or not found'}
        
        signal = self.active_signals[signal_id]
        
        # Check if signal is still valid (10 minute window)
        if datetime.now() - signal.timestamp > timedelta(minutes=10):
            del self.active_signals[signal_id]
            return {'success': False, 'message': 'Signal expired'}
        
        # Get user tier (would come from database)
        user_tier = self._get_user_tier(user_id)
        
        # Check if we can take the trade
        can_trade, reason = self.mt5_adapter.should_take_trade(
            signal.data['pair'], 
            risk_percent=2.0
        )
        
        if not can_trade:
            return {
                'success': False, 
                'message': f'Trade blocked: {reason}',
                'reason': reason
            }
        
        # Calculate SL/TP prices
        entry = signal.data['entry']
        sl = signal.data.get('sl', 0)
        tp = signal.data.get('tp', 0)
        
        # For multi-step TP (Commander+ feature)
        tp1 = tp
        tp2 = 0
        tp3 = 0
        
        if user_tier in ['commander', 'apex']:
            # Calculate 3 TP levels
            if signal.data['signal'] == 'BUY':
                tp_distance = tp - entry if tp > 0 else 0
                if tp_distance > 0:
                    tp1 = entry + (tp_distance * 0.5)   # 50% of move
                    tp2 = entry + (tp_distance * 0.75)  # 75% of move  
                    tp3 = tp  # Full TP
            else:  # SELL
                tp_distance = entry - tp if tp > 0 else 0
                if tp_distance > 0:
                    tp1 = entry - (tp_distance * 0.5)
                    tp2 = entry - (tp_distance * 0.75)
                    tp3 = tp
        
        # Execute trade with risk-based sizing
        trade_result = self.mt5_adapter.execute_trade_with_risk(
            symbol=signal.data['pair'],
            direction=signal.data['signal'],
            risk_percent=2.0,
            sl=sl,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            comment=f"BITTEN_{user_tier}_{signal.tcs_score}",
            break_even=True,
            trailing=user_tier in ['commander', 'apex'],
            partial_close=50.0 if user_tier != 'nibbler' else 0
        )
        
        if trade_result['success']:
            # Get actual executed data
            exec_data = trade_result['data']
            account_after = trade_result.get('account_after', {})
            
            # Store execution
            signal.executions[user_id] = exec_data
            
            # Send confirmation back to user
            confirmation_msg = (
                f"✅ **TRADE EXECUTED**\n"
                f"📊 {signal.data['pair']} {signal.data['signal']}\n"
                f"💰 Size: {exec_data.get('volume', 'Auto')} lots\n"
                f"🎯 Entry: {exec_data.get('price', entry)}\n"
                f"🛡 SL: {sl}\n"
            )
            
            if tp3 > 0:
                confirmation_msg += (
                    f"💎 TP1: {tp1:.5f} (30%)\n"
                    f"💎 TP2: {tp2:.5f} (30%)\n"
                    f"💎 TP3: {tp3:.5f} (40%)\n"
                )
            else:
                confirmation_msg += f"💎 TP: {tp}\n"
            
            confirmation_msg += (
                f"📋 Ticket: {exec_data.get('ticket', 'N/A')}\n"
                f"💼 Balance: ${account_after.get('balance', 0):.2f}"
            )
            
            await self.signal_alerts.send_user_confirmation(user_id, confirmation_msg)
            
            # Mark signal as fired
            signal.fired_by.add(user_id)
            
            # If Commander+, set up advanced management
            if user_tier in ['commander', 'apex'] and exec_data.get('ticket'):
                asyncio.create_task(
                    self._manage_advanced_position(
                        exec_data['ticket'], 
                        signal.data['pair'],
                        user_tier
                    )
                )
            
            return {
                'success': True,
                'trade_id': exec_data.get('ticket'),
                'execution': exec_data,
                'account': account_after
            }
        else:
            # Trade failed
            error_msg = trade_result.get('error', 'Unknown error')
            
            await self.signal_alerts.send_user_confirmation(
                user_id, 
                f"❌ **TRADE FAILED**\n{error_msg}"
            )
            
            return {
                'success': False,
                'message': error_msg,
                'details': trade_result
            }
    
    async def _manage_advanced_position(self, ticket: int, symbol: str, tier: str):
        """Advanced position management for Commander+ tiers"""
        await asyncio.sleep(5)  # Initial delay
        
        managed = False
        check_count = 0
        
        while not managed and check_count < 60:  # Check for 5 minutes
            positions = self.mt5_adapter.get_positions()
            
            # Find our position
            position = None
            for p in positions.get('positions', []):
                if p.get('ticket') == ticket:
                    position = p
                    break
            
            if not position:
                logger.info(f"Position {ticket} closed")
                return
            
            # Check if break-even should be set
            if not position.get('break_even_set'):
                pnl_percent = position.get('pnl_percent', 0)
                if pnl_percent >= 0.5:  # 0.5% in profit
                    success = self.mt5_adapter.set_break_even(ticket, buffer=5)
                    if success:
                        logger.info(f"Break-even set for {ticket}")
                        managed = True
            
            # Check for partial close opportunity
            if not position.get('partial_closed') and tier == 'apex':
                pnl_percent = position.get('pnl_percent', 0)
                if pnl_percent >= 1.0:  # 1% in profit
                    success = self.mt5_adapter.close_partial(ticket, percent=50)
                    if success:
                        logger.info(f"Partial close executed for {ticket}")
                        # Continue managing the remaining position
            
            await asyncio.sleep(5)
            check_count += 1
    
    async def _send_risk_alert(self, stats: Dict):
        """Send risk alert to users"""
        message = (
            f"⚠️ **RISK ALERT**\n"
            f"Daily P&L: {stats['daily_pl_percent']:.1f}%\n"
            f"Status: {stats['risk_status']}\n"
            f"Trading may be restricted."
        )
        
        await self.signal_alerts.broadcast_message(message)
    
    def _get_user_tier(self, user_id: int) -> str:
        """Get user tier (would come from database)"""
        # Placeholder - in production this would query the database
        return 'commander'  # Default for testing
    
    def _calculate_lot_size(self, user_tier: str, risk_percent: float = 2.0) -> float:
        """Calculate lot size based on tier and risk"""
        # This is now handled by the MT5 EA with proper calculations
        # We just return 0 to let the EA calculate based on risk
        return 0

# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize enhanced flow
    flow = EnhancedSignalFlow(
        bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        webapp_url="https://joinbitten.com"
    )
    
    # Start monitoring
    asyncio.run(flow.start_monitoring())