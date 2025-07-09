"""
BITTEN Trade Confirmation System
Handles real-time trade confirmations to Telegram for all trade activities
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ConfirmationType(Enum):
    """Types of trade confirmations"""
    TRADE_OPENED = "trade_opened"
    TRADE_CLOSED = "trade_closed"
    TRADE_MODIFIED = "trade_modified"
    STOP_LOSS_HIT = "stop_loss_hit"
    TAKE_PROFIT_HIT = "take_profit_hit"
    PARTIAL_CLOSE = "partial_close"
    POSITION_MODIFIED = "position_modified"
    TRAILING_STOP_MOVED = "trailing_stop_moved"
    BREAKEVEN_MOVED = "breakeven_moved"
    EMERGENCY_CLOSE = "emergency_close"
    PARACHUTE_EXIT = "parachute_exit"
    MARGIN_CALL = "margin_call"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"

@dataclass
class TradeConfirmation:
    """Trade confirmation data structure"""
    confirmation_id: str
    user_id: int
    confirmation_type: ConfirmationType
    timestamp: datetime
    
    # Trade details
    trade_id: Optional[str] = None
    ticket: Optional[int] = None
    symbol: Optional[str] = None
    direction: Optional[str] = None
    volume: Optional[float] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # P&L information
    pnl_pips: Optional[float] = None
    pnl_dollars: Optional[float] = None
    swap: Optional[float] = None
    commission: Optional[float] = None
    
    # Additional context
    reason: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

class TradeConfirmationSystem:
    """
    Handles all trade confirmations and notifications to Telegram
    """
    
    def __init__(self, telegram_sender: Optional[Callable] = None):
        self.telegram_sender = telegram_sender
        self.confirmation_queue = asyncio.Queue()
        self.processing = False
        self.confirmation_history: List[TradeConfirmation] = []
        self.user_preferences = {}  # user_id -> preferences
        
        # Template configurations
        self.templates = self._initialize_templates()
        
        # Processing stats
        self.stats = {
            'total_sent': 0,
            'failed_sends': 0,
            'last_send_time': None,
            'queue_size': 0
        }
    
    def _initialize_templates(self) -> Dict[ConfirmationType, Dict]:
        """Initialize message templates for different confirmation types"""
        return {
            ConfirmationType.TRADE_OPENED: {
                'emoji': '🔫',
                'title': 'POSITION OPENED',
                'color': '🟢',
                'sound': 'trade_open'
            },
            ConfirmationType.TRADE_CLOSED: {
                'emoji': '🎯',
                'title': 'POSITION CLOSED',
                'color': '🔵',
                'sound': 'trade_close'
            },
            ConfirmationType.STOP_LOSS_HIT: {
                'emoji': '❌',
                'title': 'STOP LOSS HIT',
                'color': '🔴',
                'sound': 'stop_loss'
            },
            ConfirmationType.TAKE_PROFIT_HIT: {
                'emoji': '💰',
                'title': 'TAKE PROFIT HIT',
                'color': '🟢',
                'sound': 'cash_register'
            },
            ConfirmationType.PARTIAL_CLOSE: {
                'emoji': '⚡',
                'title': 'PARTIAL CLOSE',
                'color': '🟡',
                'sound': 'partial_close'
            },
            ConfirmationType.TRAILING_STOP_MOVED: {
                'emoji': '📈',
                'title': 'TRAILING STOP MOVED',
                'color': '🟡',
                'sound': 'trail_move'
            },
            ConfirmationType.BREAKEVEN_MOVED: {
                'emoji': '🛡️',
                'title': 'MOVED TO BREAKEVEN',
                'color': '🟡',
                'sound': 'breakeven'
            },
            ConfirmationType.EMERGENCY_CLOSE: {
                'emoji': '🚨',
                'title': 'EMERGENCY CLOSE',
                'color': '🔴',
                'sound': 'emergency'
            },
            ConfirmationType.PARACHUTE_EXIT: {
                'emoji': '🪂',
                'title': 'PARACHUTE EXIT',
                'color': '🟡',
                'sound': 'parachute'
            },
            ConfirmationType.MARGIN_CALL: {
                'emoji': '⚠️',
                'title': 'MARGIN CALL',
                'color': '🔴',
                'sound': 'alarm'
            },
            ConfirmationType.CONNECTION_LOST: {
                'emoji': '🔌',
                'title': 'CONNECTION LOST',
                'color': '🔴',
                'sound': 'disconnect'
            },
            ConfirmationType.CONNECTION_RESTORED: {
                'emoji': '✅',
                'title': 'CONNECTION RESTORED',
                'color': '🟢',
                'sound': 'connect'
            }
        }
    
    async def start_processing(self):
        """Start the confirmation processing loop"""
        if self.processing:
            return
        
        self.processing = True
        asyncio.create_task(self._process_confirmations())
        logger.info("Trade confirmation processing started")
    
    async def stop_processing(self):
        """Stop the confirmation processing"""
        self.processing = False
        logger.info("Trade confirmation processing stopped")
    
    async def _process_confirmations(self):
        """Main processing loop for confirmations"""
        while self.processing:
            try:
                # Get confirmation from queue (wait up to 1 second)
                confirmation = await asyncio.wait_for(
                    self.confirmation_queue.get(), 
                    timeout=1.0
                )
                
                # Process the confirmation
                await self._send_confirmation(confirmation)
                
                # Update stats
                self.stats['queue_size'] = self.confirmation_queue.qsize()
                
            except asyncio.TimeoutError:
                # No confirmations in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing confirmation: {e}")
                self.stats['failed_sends'] += 1
    
    async def send_trade_opened_confirmation(self, user_id: int, trade_data: Dict):
        """Send confirmation for trade opened"""
        confirmation = TradeConfirmation(
            confirmation_id=f"open_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.TRADE_OPENED,
            timestamp=datetime.now(),
            trade_id=trade_data.get('trade_id'),
            ticket=trade_data.get('ticket'),
            symbol=trade_data.get('symbol'),
            direction=trade_data.get('direction'),
            volume=trade_data.get('volume'),
            entry_price=trade_data.get('entry_price'),
            stop_loss=trade_data.get('stop_loss'),
            take_profit=trade_data.get('take_profit'),
            metadata=trade_data.get('metadata', {})
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_trade_closed_confirmation(self, user_id: int, trade_data: Dict):
        """Send confirmation for trade closed"""
        confirmation = TradeConfirmation(
            confirmation_id=f"close_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.TRADE_CLOSED,
            timestamp=datetime.now(),
            trade_id=trade_data.get('trade_id'),
            ticket=trade_data.get('ticket'),
            symbol=trade_data.get('symbol'),
            direction=trade_data.get('direction'),
            volume=trade_data.get('volume'),
            entry_price=trade_data.get('entry_price'),
            exit_price=trade_data.get('exit_price'),
            pnl_pips=trade_data.get('pnl_pips'),
            pnl_dollars=trade_data.get('pnl_dollars'),
            swap=trade_data.get('swap', 0),
            commission=trade_data.get('commission', 0),
            reason=trade_data.get('reason'),
            metadata=trade_data.get('metadata', {})
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_stop_loss_hit_confirmation(self, user_id: int, trade_data: Dict):
        """Send confirmation for stop loss hit"""
        confirmation = TradeConfirmation(
            confirmation_id=f"sl_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.STOP_LOSS_HIT,
            timestamp=datetime.now(),
            trade_id=trade_data.get('trade_id'),
            ticket=trade_data.get('ticket'),
            symbol=trade_data.get('symbol'),
            direction=trade_data.get('direction'),
            volume=trade_data.get('volume'),
            entry_price=trade_data.get('entry_price'),
            exit_price=trade_data.get('exit_price'),
            stop_loss=trade_data.get('stop_loss'),
            pnl_pips=trade_data.get('pnl_pips'),
            pnl_dollars=trade_data.get('pnl_dollars'),
            metadata=trade_data.get('metadata', {})
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_take_profit_hit_confirmation(self, user_id: int, trade_data: Dict):
        """Send confirmation for take profit hit"""
        confirmation = TradeConfirmation(
            confirmation_id=f"tp_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.TAKE_PROFIT_HIT,
            timestamp=datetime.now(),
            trade_id=trade_data.get('trade_id'),
            ticket=trade_data.get('ticket'),
            symbol=trade_data.get('symbol'),
            direction=trade_data.get('direction'),
            volume=trade_data.get('volume'),
            entry_price=trade_data.get('entry_price'),
            exit_price=trade_data.get('exit_price'),
            take_profit=trade_data.get('take_profit'),
            pnl_pips=trade_data.get('pnl_pips'),
            pnl_dollars=trade_data.get('pnl_dollars'),
            metadata=trade_data.get('metadata', {})
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_partial_close_confirmation(self, user_id: int, trade_data: Dict):
        """Send confirmation for partial close"""
        confirmation = TradeConfirmation(
            confirmation_id=f"partial_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.PARTIAL_CLOSE,
            timestamp=datetime.now(),
            trade_id=trade_data.get('trade_id'),
            ticket=trade_data.get('ticket'),
            symbol=trade_data.get('symbol'),
            direction=trade_data.get('direction'),
            volume=trade_data.get('closed_volume'),
            exit_price=trade_data.get('exit_price'),
            pnl_pips=trade_data.get('pnl_pips'),
            pnl_dollars=trade_data.get('pnl_dollars'),
            reason=trade_data.get('reason', 'Partial close'),
            metadata={
                'remaining_volume': trade_data.get('remaining_volume'),
                'closed_percent': trade_data.get('closed_percent'),
                **trade_data.get('metadata', {})
            }
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_position_modified_confirmation(self, user_id: int, modification_data: Dict):
        """Send confirmation for position modification (SL/TP changes)"""
        confirmation = TradeConfirmation(
            confirmation_id=f"mod_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.POSITION_MODIFIED,
            timestamp=datetime.now(),
            trade_id=modification_data.get('trade_id'),
            ticket=modification_data.get('ticket'),
            symbol=modification_data.get('symbol'),
            stop_loss=modification_data.get('new_stop_loss'),
            take_profit=modification_data.get('new_take_profit'),
            reason=modification_data.get('reason'),
            metadata={
                'old_stop_loss': modification_data.get('old_stop_loss'),
                'old_take_profit': modification_data.get('old_take_profit'),
                'modification_type': modification_data.get('modification_type'),
                **modification_data.get('metadata', {})
            }
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_trailing_stop_moved_confirmation(self, user_id: int, trail_data: Dict):
        """Send confirmation for trailing stop movement"""
        confirmation = TradeConfirmation(
            confirmation_id=f"trail_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.TRAILING_STOP_MOVED,
            timestamp=datetime.now(),
            trade_id=trail_data.get('trade_id'),
            ticket=trail_data.get('ticket'),
            symbol=trail_data.get('symbol'),
            stop_loss=trail_data.get('new_stop_loss'),
            pnl_pips=trail_data.get('current_pnl_pips'),
            metadata={
                'old_stop_loss': trail_data.get('old_stop_loss'),
                'trail_distance': trail_data.get('trail_distance'),
                'current_price': trail_data.get('current_price'),
                **trail_data.get('metadata', {})
            }
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_breakeven_moved_confirmation(self, user_id: int, breakeven_data: Dict):
        """Send confirmation for breakeven movement"""
        confirmation = TradeConfirmation(
            confirmation_id=f"be_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.BREAKEVEN_MOVED,
            timestamp=datetime.now(),
            trade_id=breakeven_data.get('trade_id'),
            ticket=breakeven_data.get('ticket'),
            symbol=breakeven_data.get('symbol'),
            stop_loss=breakeven_data.get('new_stop_loss'),
            entry_price=breakeven_data.get('entry_price'),
            pnl_pips=breakeven_data.get('current_pnl_pips'),
            metadata={
                'breakeven_plus_pips': breakeven_data.get('breakeven_plus_pips', 0),
                'trigger_pips': breakeven_data.get('trigger_pips'),
                **breakeven_data.get('metadata', {})
            }
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_emergency_close_confirmation(self, user_id: int, emergency_data: Dict):
        """Send confirmation for emergency close"""
        confirmation = TradeConfirmation(
            confirmation_id=f"emrg_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.EMERGENCY_CLOSE,
            timestamp=datetime.now(),
            trade_id=emergency_data.get('trade_id'),
            ticket=emergency_data.get('ticket'),
            symbol=emergency_data.get('symbol'),
            exit_price=emergency_data.get('exit_price'),
            pnl_pips=emergency_data.get('pnl_pips'),
            pnl_dollars=emergency_data.get('pnl_dollars'),
            reason=emergency_data.get('reason', 'Emergency close'),
            metadata={
                'trigger': emergency_data.get('trigger'),
                'approval_code': emergency_data.get('approval_code'),
                **emergency_data.get('metadata', {})
            }
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_parachute_exit_confirmation(self, user_id: int, parachute_data: Dict):
        """Send confirmation for parachute exit"""
        confirmation = TradeConfirmation(
            confirmation_id=f"para_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=ConfirmationType.PARACHUTE_EXIT,
            timestamp=datetime.now(),
            trade_id=parachute_data.get('trade_id'),
            ticket=parachute_data.get('ticket'),
            symbol=parachute_data.get('symbol'),
            exit_price=parachute_data.get('exit_price'),
            pnl_pips=parachute_data.get('pnl_pips'),
            pnl_dollars=parachute_data.get('pnl_dollars'),
            reason="Parachute exit - No XP penalty",
            metadata={
                'xp_penalty_waived': True,
                **parachute_data.get('metadata', {})
            }
        )
        
        await self.queue_confirmation(confirmation)
    
    async def send_connection_status_confirmation(self, user_id: int, status_data: Dict):
        """Send confirmation for connection status changes"""
        confirmation_type = (ConfirmationType.CONNECTION_RESTORED 
                           if status_data.get('connected', False) 
                           else ConfirmationType.CONNECTION_LOST)
        
        confirmation = TradeConfirmation(
            confirmation_id=f"conn_{int(time.time() * 1000)}",
            user_id=user_id,
            confirmation_type=confirmation_type,
            timestamp=datetime.now(),
            reason=status_data.get('reason'),
            metadata={
                'broker': status_data.get('broker'),
                'server': status_data.get('server'),
                'last_ping': status_data.get('last_ping'),
                **status_data.get('metadata', {})
            }
        )
        
        await self.queue_confirmation(confirmation)
    
    async def queue_confirmation(self, confirmation: TradeConfirmation):
        """Add confirmation to processing queue"""
        await self.confirmation_queue.put(confirmation)
        self.stats['queue_size'] = self.confirmation_queue.qsize()
        logger.debug(f"Queued confirmation: {confirmation.confirmation_type.value} for user {confirmation.user_id}")
    
    async def _send_confirmation(self, confirmation: TradeConfirmation):
        """Send confirmation to Telegram"""
        try:
            # Check user preferences
            if not self._should_send_confirmation(confirmation):
                return
            
            # Generate message
            message = self._generate_confirmation_message(confirmation)
            
            # Send to Telegram
            if self.telegram_sender:
                success = await self.telegram_sender(confirmation.user_id, message)
                if success:
                    self.stats['total_sent'] += 1
                    self.stats['last_send_time'] = datetime.now()
                    logger.info(f"Sent {confirmation.confirmation_type.value} confirmation to user {confirmation.user_id}")
                else:
                    self.stats['failed_sends'] += 1
                    logger.error(f"Failed to send confirmation to user {confirmation.user_id}")
            else:
                # Log the message if no sender configured
                logger.info(f"Confirmation message (no sender): {message}")
            
            # Store in history
            self.confirmation_history.append(confirmation)
            
            # Keep only recent history (last 1000 confirmations)
            if len(self.confirmation_history) > 1000:
                self.confirmation_history = self.confirmation_history[-500:]
                
        except Exception as e:
            logger.error(f"Error sending confirmation: {e}")
            self.stats['failed_sends'] += 1
    
    def _should_send_confirmation(self, confirmation: TradeConfirmation) -> bool:
        """Check if confirmation should be sent based on user preferences"""
        user_prefs = self.user_preferences.get(confirmation.user_id, {})
        
        # Check if confirmations are enabled
        if not user_prefs.get('confirmations_enabled', True):
            return False
        
        # Check specific confirmation type preferences
        type_key = f"{confirmation.confirmation_type.value}_enabled"
        if not user_prefs.get(type_key, True):
            return False
        
        # Check minimum P&L thresholds
        if confirmation.pnl_dollars is not None:
            min_pnl = user_prefs.get('min_pnl_threshold', 0)
            if abs(confirmation.pnl_dollars) < min_pnl:
                return False
        
        return True
    
    def _generate_confirmation_message(self, confirmation: TradeConfirmation) -> str:
        """Generate formatted confirmation message"""
        template = self.templates.get(confirmation.confirmation_type, {})
        emoji = template.get('emoji', '📊')
        title = template.get('title', 'TRADE UPDATE')
        color = template.get('color', '🔵')
        
        # Start building message
        message = f"{color} **{emoji} {title}** {emoji}\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Add timestamp
        time_str = confirmation.timestamp.strftime("%H:%M:%S UTC")
        message += f"🕐 **Time**: {time_str}\n"
        
        # Add trade details if available
        if confirmation.symbol:
            message += f"📈 **Symbol**: {confirmation.symbol}\n"
        
        if confirmation.direction:
            direction_emoji = "📈" if confirmation.direction == "BUY" else "📉"
            message += f"{direction_emoji} **Direction**: {confirmation.direction}\n"
        
        if confirmation.volume:
            message += f"📦 **Volume**: {confirmation.volume} lots\n"
        
        # Add price information
        if confirmation.entry_price:
            message += f"🎯 **Entry**: {confirmation.entry_price:.5f}\n"
        
        if confirmation.exit_price:
            message += f"🚪 **Exit**: {confirmation.exit_price:.5f}\n"
        
        if confirmation.stop_loss:
            message += f"🛡️ **Stop Loss**: {confirmation.stop_loss:.5f}\n"
        
        if confirmation.take_profit:
            message += f"💰 **Take Profit**: {confirmation.take_profit:.5f}\n"
        
        # Add P&L information
        if confirmation.pnl_pips is not None:
            pnl_emoji = "✅" if confirmation.pnl_pips >= 0 else "❌"
            message += f"{pnl_emoji} **P&L**: {confirmation.pnl_pips:+.1f} pips\n"
        
        if confirmation.pnl_dollars is not None:
            dollar_emoji = "💵" if confirmation.pnl_dollars >= 0 else "💸"
            message += f"{dollar_emoji} **P&L**: ${confirmation.pnl_dollars:+.2f}\n"
        
        # Add fees if present
        if confirmation.swap or confirmation.commission:
            swap = confirmation.swap or 0
            commission = confirmation.commission or 0
            total_fees = swap + commission
            if total_fees != 0:
                message += f"💳 **Fees**: ${total_fees:.2f}\n"
        
        # Add reason if present
        if confirmation.reason:
            message += f"📝 **Reason**: {confirmation.reason}\n"
        
        # Add ticket number
        if confirmation.ticket:
            message += f"🎫 **Ticket**: #{confirmation.ticket}\n"
        
        # Add type-specific information
        message += self._add_type_specific_info(confirmation)
        
        # Add footer
        message += "\n━━━━━━━━━━━━━━━━━━━━\n"
        message += "📱 *B.I.T.T.E.N. Trade Monitor*"
        
        return message
    
    def _add_type_specific_info(self, confirmation: TradeConfirmation) -> str:
        """Add confirmation type-specific information"""
        extra_info = ""
        metadata = confirmation.metadata or {}
        
        if confirmation.confirmation_type == ConfirmationType.PARTIAL_CLOSE:
            if 'closed_percent' in metadata:
                extra_info += f"📊 **Closed**: {metadata['closed_percent']:.1f}%\n"
            if 'remaining_volume' in metadata:
                extra_info += f"📦 **Remaining**: {metadata['remaining_volume']} lots\n"
        
        elif confirmation.confirmation_type == ConfirmationType.TRAILING_STOP_MOVED:
            if 'trail_distance' in metadata:
                extra_info += f"📏 **Trail Distance**: {metadata['trail_distance']} pips\n"
            if 'old_stop_loss' in metadata:
                extra_info += f"🔄 **Previous SL**: {metadata['old_stop_loss']:.5f}\n"
        
        elif confirmation.confirmation_type == ConfirmationType.BREAKEVEN_MOVED:
            if 'breakeven_plus_pips' in metadata:
                plus_pips = metadata['breakeven_plus_pips']
                if plus_pips > 0:
                    extra_info += f"➕ **Breakeven+**: {plus_pips} pips\n"
                else:
                    extra_info += "🛡️ **Status**: Pure breakeven\n"
        
        elif confirmation.confirmation_type == ConfirmationType.PARACHUTE_EXIT:
            extra_info += "🪂 **XP Penalty**: WAIVED\n"
            extra_info += "💡 **Status**: Emergency exit approved\n"
        
        elif confirmation.confirmation_type == ConfirmationType.CONNECTION_LOST:
            if 'broker' in metadata:
                extra_info += f"🏛️ **Broker**: {metadata['broker']}\n"
            extra_info += "⚠️ **Action**: Monitoring trades manually\n"
        
        elif confirmation.confirmation_type == ConfirmationType.CONNECTION_RESTORED:
            if 'broker' in metadata:
                extra_info += f"🏛️ **Broker**: {metadata['broker']}\n"
            extra_info += "✅ **Status**: Full automation resumed\n"
        
        return extra_info
    
    def set_user_preferences(self, user_id: int, preferences: Dict):
        """Set user notification preferences"""
        self.user_preferences[user_id] = preferences
        logger.info(f"Updated preferences for user {user_id}")
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user notification preferences"""
        return self.user_preferences.get(user_id, {
            'confirmations_enabled': True,
            'min_pnl_threshold': 0,
            'trade_opened_enabled': True,
            'trade_closed_enabled': True,
            'stop_loss_hit_enabled': True,
            'take_profit_hit_enabled': True,
            'partial_close_enabled': True,
            'trailing_stop_moved_enabled': False,
            'breakeven_moved_enabled': True,
            'emergency_close_enabled': True,
            'parachute_exit_enabled': True,
            'connection_lost_enabled': True,
            'connection_restored_enabled': True
        })
    
    def get_confirmation_history(self, user_id: Optional[int] = None, 
                               limit: int = 50) -> List[TradeConfirmation]:
        """Get confirmation history"""
        history = self.confirmation_history
        
        if user_id:
            history = [c for c in history if c.user_id == user_id]
        
        return history[-limit:] if limit else history
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        return {
            **self.stats,
            'confirmation_history_count': len(self.confirmation_history),
            'active_users': len(self.user_preferences),
            'processing': self.processing
        }


# Helper function for integration with existing systems
def create_confirmation_system(telegram_sender: Optional[Callable] = None) -> TradeConfirmationSystem:
    """Create and configure trade confirmation system"""
    system = TradeConfirmationSystem(telegram_sender)
    return system


# Example usage and testing
async def example_usage():
    """Example of using the trade confirmation system"""
    
    # Mock telegram sender
    async def mock_telegram_sender(user_id: int, message: str) -> bool:
        print(f"[TELEGRAM] To user {user_id}:")
        print(message)
        print("-" * 50)
        return True
    
    # Create system
    confirmation_system = create_confirmation_system(mock_telegram_sender)
    
    # Start processing
    await confirmation_system.start_processing()
    
    # Example: Trade opened
    await confirmation_system.send_trade_opened_confirmation(
        user_id=123456,
        trade_data={
            'trade_id': 'T001',
            'ticket': 987654,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'volume': 0.1,
            'entry_price': 1.08500,
            'stop_loss': 1.08000,
            'take_profit': 1.09000,
            'metadata': {'strategy': 'London Breakout'}
        }
    )
    
    # Example: Take profit hit
    await confirmation_system.send_take_profit_hit_confirmation(
        user_id=123456,
        trade_data={
            'trade_id': 'T001',
            'ticket': 987654,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'volume': 0.1,
            'entry_price': 1.08500,
            'exit_price': 1.09000,
            'take_profit': 1.09000,
            'pnl_pips': 50.0,
            'pnl_dollars': 50.00,
            'metadata': {'duration_minutes': 15}
        }
    )
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Stop processing
    await confirmation_system.stop_processing()
    
    # Show stats
    stats = confirmation_system.get_system_stats()
    print(f"System stats: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())