"""
🎯 MT5 Bridge Integration
Connects MT5 results to BITTEN core system
Handles trade confirmations, XP updates, and Telegram notifications
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from src.mt5_bridge.result_parser import MT5ResultParser
from src.mt5_bridge.mt5_bridge_adapter import TradeResult
from src.database.connection import get_db_manager
from src.database.models import User, Trade, RiskSession, XPTransaction
# TODO: Import these when implemented
# from src.bitten_core.xp_system import XPCalculator, XPEventType
# from src.bitten_core.telegram_router import TelegramRouter
# from src.bitten_core.signal_display import create_trade_confirmation_message

# Temporary placeholders
class XPCalculator:
    def calculate_xp(self, event_type, **kwargs):
        return 10  # Default XP
        
class XPEventType:
    TRADE_WIN = 'trade_win'
    TRADE_LOSS = 'trade_loss'

class TelegramRouter:
    async def send_message(self, chat_id, text, **kwargs):
        pass

def create_trade_confirmation_message(*args, **kwargs):
    return "Trade confirmation"

logger = logging.getLogger(__name__)

class MT5BridgeIntegration:
    """
    Integrates MT5 trade results with BITTEN system
    Handles the flow from MT5 -> Parser -> Database -> XP -> Telegram
    """
    
    def __init__(self, telegram_router: Optional[TelegramRouter] = None):
        self.parser = MT5ResultParser()
        self.db = get_db_manager()
        self.xp_calculator = XPCalculator()
        self.telegram = telegram_router
        self.result_queue = asyncio.Queue()
        self.processing = False
        
    async def process_mt5_result(self, result_string: str, user_id: int, 
                               fire_mode: str = None) -> Dict[str, Any]:
        """
        Process a single MT5 result
        
        Args:
            result_string: Raw MT5 result
            user_id: User who initiated the trade
            fire_mode: Fire mode used (optional)
            
        Returns:
            Processing result with status and details
        """
        try:
            # Parse the result
            parsed = self.parser.parse(result_string)
            
            # Validate
            is_valid, error = self.parser.validate_result(parsed)
            if not is_valid:
                logger.error(f"Invalid MT5 result: {error}")
                return {
                    'success': False,
                    'error': error,
                    'parsed': parsed
                }
            
            # Create trade result model
            trade_result = TradeResult.from_parser_result(parsed)
            
            # Process based on type
            if parsed['type'] == 'trade_opened':
                return await self._process_trade_opened(trade_result, user_id, fire_mode)
                
            elif parsed['type'] == 'trade_closed':
                return await self._process_trade_closed(trade_result, user_id)
                
            elif parsed['type'] == 'error':
                return await self._process_trade_error(trade_result, user_id)
                
            else:
                # Other types (order placed, position modified, etc.)
                return {
                    'success': True,
                    'type': parsed['type'],
                    'result': trade_result.to_dict()
                }
                
        except Exception as e:
            logger.error(f"Error processing MT5 result: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _process_trade_opened(self, trade_result: TradeResult, 
                                  user_id: int, fire_mode: str) -> Dict[str, Any]:
        """Process trade opened result"""
        with self.db.session_scope() as session:
            # Get user
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Create database trade
            db_trade = trade_result.to_database_model(user_id, fire_mode)
            session.add(db_trade)
            
            # Update risk session
            today = datetime.utcnow().date()
            risk_session = session.query(RiskSession).filter_by(
                user_id=user_id,
                session_date=today
            ).first()
            
            if risk_session:
                risk_session.trades_opened += 1
                risk_session.last_trade_time = datetime.utcnow()
            
            session.commit()
            
            # Send Telegram confirmation
            if self.telegram:
                message = create_trade_confirmation_message(
                    'opened',
                    trade_result.symbol,
                    trade_result.order_type,
                    trade_result.volume,
                    trade_result.open_price,
                    stop_loss=trade_result.stop_loss,
                    take_profit=trade_result.take_profit,
                    fire_mode=fire_mode
                )
                
                await self.telegram.send_message(
                    user.telegram_id,
                    message,
                    parse_mode='HTML'
                )
            
            return {
                'success': True,
                'type': 'trade_opened',
                'trade_id': db_trade.trade_id,
                'ticket': trade_result.ticket,
                'message': f"Trade {trade_result.ticket} opened successfully"
            }
    
    async def _process_trade_closed(self, trade_result: TradeResult, 
                                  user_id: int) -> Dict[str, Any]:
        """Process trade closed result"""
        with self.db.session_scope() as session:
            # Get user
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Find existing trade
            db_trade = session.query(Trade).filter_by(
                user_id=user_id,
                mt5_ticket=trade_result.ticket
            ).first()
            
            if not db_trade:
                # Create new closed trade record
                db_trade = trade_result.to_database_model(user_id)
                session.add(db_trade)
            else:
                # Update existing trade
                db_trade.status = 'closed'
                db_trade.close_price = Decimal(str(trade_result.close_price))
                db_trade.close_time = trade_result.close_time
                db_trade.profit = Decimal(str(trade_result.profit))
                db_trade.commission = Decimal(str(trade_result.commission))
                db_trade.swap = Decimal(str(trade_result.swap))
            
            # Calculate XP
            xp_earned = 0
            xp_deducted = 0
            
            # Check if this was an early exit (didn't hit TP or SL)
            is_early_exit = False
            if db_trade and trade_result.close_price:
                # If we have the original trade data
                if db_trade.stop_loss and db_trade.take_profit:
                    # Check if close price is between SL and TP (early exit)
                    if 'BUY' in str(db_trade.order_type).upper():
                        is_early_exit = (
                            float(db_trade.stop_loss) < float(trade_result.close_price) < float(db_trade.take_profit)
                        )
                    else:  # SELL
                        is_early_exit = (
                            float(db_trade.take_profit) < float(trade_result.close_price) < float(db_trade.stop_loss)
                        )
            
            if is_early_exit:
                # PENALTY: Early exit = didn't trust the system
                # Trying to grab quick money and move on
                xp_deducted = 20  # Base penalty
                if trade_result.net_profit > 0:
                    # Even worse - took profit early, greedy behavior
                    xp_deducted = 30
                xp_earned = -xp_deducted
                
            elif trade_result.is_successful():
                # Full win - trusted the system, hit TP
                xp_event = XPEventType.TRADE_WIN
                xp_earned = self.xp_calculator.calculate_xp(
                    xp_event,
                    tier=user.tier,
                    profit=trade_result.net_profit
                )
            else:
                # Hit stop loss - NO XP deduction, they already lost money
                # BITTEN philosophy: never kick someone when they're down
                xp_earned = 0
            
            # Record XP transaction
            if xp_earned != 0:
                if xp_earned > 0:
                    xp_transaction = XPTransaction(
                        user_id=user_id,
                        amount=xp_earned,
                        transaction_type='earned',
                        source='trade',
                        description=f"Trade {trade_result.ticket} win - trusted the system"
                    )
                    # Update user profile XP
                    user.profile.current_xp += xp_earned
                    user.profile.total_xp_earned += xp_earned
                else:
                    # XP penalty for early exit
                    xp_transaction = XPTransaction(
                        user_id=user_id,
                        amount=abs(xp_earned),
                        transaction_type='spent',
                        source='penalty',
                        description=f"Trade {trade_result.ticket} early exit - lack of trust"
                    )
                    # Deduct from user profile XP
                    user.profile.current_xp = max(0, user.profile.current_xp + xp_earned)
                    
                session.add(xp_transaction)
            
            # Update risk session
            today = datetime.utcnow().date()
            risk_session = session.query(RiskSession).filter_by(
                user_id=user_id,
                session_date=today
            ).first()
            
            if risk_session:
                risk_session.trades_closed += 1
                risk_session.total_profit += Decimal(str(trade_result.net_profit))
                if trade_result.is_successful():
                    risk_session.trades_won += 1
                else:
                    risk_session.trades_lost += 1
            
            # Update user profile stats
            user.profile.total_trades += 1
            user.profile.total_profit_usd += Decimal(str(trade_result.net_profit))
            if trade_result.is_successful():
                user.profile.win_rate = (
                    (user.profile.win_rate * (user.profile.total_trades - 1) + 100) 
                    / user.profile.total_trades
                )
            else:
                user.profile.win_rate = (
                    (user.profile.win_rate * (user.profile.total_trades - 1)) 
                    / user.profile.total_trades
                )
            
            session.commit()
            
            # Send Telegram confirmation
            if self.telegram:
                # Determine emoji and message based on outcome
                if is_early_exit:
                    profit_emoji = "⚠️"  # Warning for early exit
                    if xp_earned < 0:
                        xp_message = f"\n🎖️ -{abs(xp_earned)} XP (early exit penalty)"
                    else:
                        xp_message = ""
                    
                    if trade_result.net_profit > 0:
                        encouragement = "\n\n⚡ <i>Impatient, soldier? Trust the system next time.</i>"
                    else:
                        encouragement = "\n\n⚡ <i>Scared money don't make money. Trust your TCS.</i>"
                else:
                    profit_emoji = "✅" if trade_result.is_successful() else "❌"
                    xp_message = f"\n🎖️ +{xp_earned} XP" if xp_earned > 0 else ""
                    
                    # Add encouragement for losses
                    if not trade_result.is_successful():
                        encouragement = "\n\n💪 <i>Dust yourself off, soldier. Next one.</i>"
                    else:
                        encouragement = ""
                
                message = (
                    f"{profit_emoji} <b>Trade Closed</b>\n"
                    f"Symbol: {trade_result.symbol}\n"
                    f"Profit: ${trade_result.net_profit:.2f}\n"
                    f"Pips: {trade_result.get_pips() or 0}"
                    f"{xp_message}"
                    f"{encouragement}"
                )
                
                await self.telegram.send_message(
                    user.telegram_id,
                    message,
                    parse_mode='HTML'
                )
            
            return {
                'success': True,
                'type': 'trade_closed',
                'trade_id': db_trade.trade_id,
                'ticket': trade_result.ticket,
                'profit': float(trade_result.net_profit),
                'xp_earned': xp_earned,
                'message': f"Trade {trade_result.ticket} closed with ${trade_result.net_profit:.2f} profit"
            }
    
    async def _process_trade_error(self, trade_result: TradeResult, 
                                 user_id: int) -> Dict[str, Any]:
        """Process trade error result"""
        with self.db.session_scope() as session:
            # Get user
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Log error in database (could create error log table)
            logger.error(
                f"MT5 trade error for user {user_id}: "
                f"Code {trade_result.error_code} - {trade_result.error_message}"
            )
            
            # Send Telegram notification
            if self.telegram:
                message = (
                    f"⚠️ <b>Trade Error</b>\n"
                    f"Error: {trade_result.error_message}\n"
                    f"Code: {trade_result.error_code}\n"
                    f"\n"
                    f"<i>Check your MT5 terminal for details</i>"
                )
                
                await self.telegram.send_message(
                    user.telegram_id,
                    message,
                    parse_mode='HTML'
                )
            
            return {
                'success': False,
                'type': 'trade_error',
                'error_code': trade_result.error_code,
                'error_message': trade_result.error_message,
                'message': f"Trade failed: {trade_result.error_message}"
            }
    
    async def process_batch_results(self, results: List[str], user_id: int,
                                  fire_mode: str = None) -> Dict[str, Any]:
        """
        Process multiple MT5 results in batch
        
        Args:
            results: List of MT5 result strings
            user_id: User who initiated trades
            fire_mode: Fire mode used
            
        Returns:
            Batch processing summary
        """
        batch = TradeResultBatch()
        processed_results = []
        
        for result_string in results:
            result = await self.process_mt5_result(result_string, user_id, fire_mode)
            processed_results.append(result)
            
            # Add to batch if successful
            if result.get('success'):
                parsed = self.parser.parse(result_string)
                trade_result = TradeResult.from_parser_result(parsed)
                batch.add_result(trade_result)
        
        # Get batch summary
        summary = batch.get_summary()
        summary['processed_count'] = len(processed_results)
        summary['success_count'] = sum(1 for r in processed_results if r.get('success'))
        summary['error_count'] = sum(1 for r in processed_results if not r.get('success'))
        
        return {
            'success': True,
            'summary': summary,
            'results': processed_results
        }
    
    async def start_result_processor(self):
        """Start background result processor"""
        if self.processing:
            return
            
        self.processing = True
        asyncio.create_task(self._process_result_queue())
        logger.info("MT5 result processor started")
    
    async def stop_result_processor(self):
        """Stop background result processor"""
        self.processing = False
        logger.info("MT5 result processor stopped")
    
    async def _process_result_queue(self):
        """Process results from queue"""
        while self.processing:
            try:
                # Wait for result with timeout
                result_data = await asyncio.wait_for(
                    self.result_queue.get(),
                    timeout=1.0
                )
                
                # Process the result
                await self.process_mt5_result(
                    result_data['result_string'],
                    result_data['user_id'],
                    result_data.get('fire_mode')
                )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in result processor: {e}")
    
    async def queue_result(self, result_string: str, user_id: int, 
                         fire_mode: str = None):
        """Queue result for processing"""
        await self.result_queue.put({
            'result_string': result_string,
            'user_id': user_id,
            'fire_mode': fire_mode
        })

# Global instance
_bridge_integration: Optional[MT5BridgeIntegration] = None

def get_bridge_integration(telegram_router: Optional[TelegramRouter] = None) -> MT5BridgeIntegration:
    """Get or create global bridge integration instance"""
    global _bridge_integration
    if _bridge_integration is None:
        _bridge_integration = MT5BridgeIntegration(telegram_router)
    return _bridge_integration

async def process_mt5_result(result_string: str, user_id: int, 
                           fire_mode: str = None) -> Dict[str, Any]:
    """Convenience function to process MT5 result"""
    bridge = get_bridge_integration()
    return await bridge.process_mt5_result(result_string, user_id, fire_mode)