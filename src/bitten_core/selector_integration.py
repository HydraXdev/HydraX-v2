# selector_integration.py
# Integration layer between Selector Switch and Master Filter

from typing import Dict, List, Optional, Callable
from datetime import datetime
from .selector_switch import CommanderSelector, SelectorMode, SelectorUI
from .master_filter import MasterFilter, FilteredSignal
from .fire_modes import TierLevel
import asyncio
import logging

logger = logging.getLogger(__name__)

class SelectorIntegration:
    """
    Integrates Commander Selector with the trading system
    
    Handles the flow from signal detection to execution
    based on selector mode settings.
    """
    
    def __init__(self, master_filter: MasterFilter):
        self.master_filter = master_filter
        self.user_selectors: Dict[int, CommanderSelector] = {}
        
        # Callback handlers
        self.telegram_callback: Optional[Callable] = None
        self.execution_callback: Optional[Callable] = None
        
    def get_user_selector(self, user_id: int, tier: TierLevel) -> Optional[CommanderSelector]:
        """Get or create selector for user"""
        
        # Only COMMANDER and get selectors
        if tier not in [TierLevel.COMMANDER, TierLevel.]:
            return None
        
        if user_id not in self.user_selectors:
            self.user_selectors[user_id] = CommanderSelector(user_id)
            
        return self.user_selectors[user_id]
    
    async def process_signals_for_user(self, user_id: int, tier: TierLevel, 
                                      balance: float, signals: Dict[str, List[FilteredSignal]]) -> List[Dict]:
        """
        Process all signals for a user based on their selector mode
        
        Returns list of actions to take
        """
        
        actions = []
        
        # Get user's selector (if they have one)
        selector = self.get_user_selector(user_id, tier)
        
        # Process each signal category
        for signal_type, signal_list in signals.items():
            for signal in signal_list:
                # Validate if user can execute
                can_execute, restriction, params = self.master_filter.validate_shot(
                    user_id, signal.signal_id, tier, balance
                )
                
                # Convert signal to dict for selector
                signal_dict = {
                    'signal_id': signal.signal_id,
                    'signal_type': signal.signal_type,
                    'display_type': signal.display_type,
                    'symbol': signal.symbol,
                    'direction': signal.direction,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'tcs_score': signal.tcs_score,
                    'expected_pips': signal.expected_pips,
                    'expected_duration': signal.expected_duration,
                    'restriction_reason': restriction if not can_execute else None
                }
                
                if selector:
                    # Commander/with selector
                    action = selector.process_signal(signal_dict, can_execute)
                    action['signal'] = signal
                    action['execution_params'] = params
                    actions.append(action)
                else:
                    # Nibbler/Fang - always manual
                    actions.append({
                        'action': 'display_only',
                        'signal': signal,
                        'can_execute': can_execute,
                        'restriction_reason': restriction,
                        'show_fire_button': can_execute
                    })
        
        return actions
    
    async def handle_selector_action(self, user_id: int, action: Dict) -> Dict:
        """Handle the action determined by selector"""
        
        result = {'success': False, 'message': 'Unknown action'}
        
        if action['action'] == 'display_only':
            # Send to Telegram for display
            if self.telegram_callback:
                await self.telegram_callback(user_id, action)
            result = {'success': True, 'message': 'Signal displayed'}
            
        elif action['action'] == 'request_confirmation':
            # Send confirmation popup to Telegram
            if self.telegram_callback:
                await self.telegram_callback(user_id, {
                    'type': 'confirmation_request',
                    'data': action['popup_data'],
                    'confirmation_id': action['confirmation_id']
                })
            result = {'success': True, 'message': 'Confirmation requested'}
            
        elif action['action'] == 'auto_execute':
            # Execute immediately
            if action.get('execution_params'):
                execution_result = await self._execute_trade(
                    user_id, action['signal'], action['execution_params']
                )
                
                # Notify user of auto execution
                if self.telegram_callback:
                    await self.telegram_callback(user_id, {
                        'type': 'auto_execution',
                        'message': SelectorUI.format_auto_notification(action),
                        'result': execution_result
                    })
                
                result = execution_result
            
        elif action['action'] in ['auto_rejected', 'rejected']:
            # Log rejection
            logger.info(f"Signal rejected for user {user_id}: {action.get('reason')}")
            result = {'success': True, 'message': action.get('reason', 'Signal rejected')}
        
        return result
    
    async def handle_user_confirmation(self, user_id: int, confirmation_id: str, 
                                     decision: str) -> Dict:
        """Handle user's confirmation decision"""
        
        selector = self.user_selectors.get(user_id)
        if not selector:
            return {'success': False, 'message': 'No selector found'}
        
        result = selector.handle_confirmation(confirmation_id, decision)
        
        if result['success'] and result['action'] == 'execute':
            # Get signal and execute
            signal = result['signal']
            # Need to retrieve execution params
            can_execute, _, params = self.master_filter.validate_shot(
                user_id, signal['signal_id'], TierLevel.COMMANDER, 
                self.master_filter.user_states[user_id]['balance']
            )
            
            if can_execute:
                execution_result = await self._execute_trade(
                    user_id, signal, params
                )
                result.update(execution_result)
        
        return result
    
    async def _execute_trade(self, user_id: int, signal: Dict, 
                           execution_params: Dict) -> Dict:
        """Execute the trade through master filter"""
        
        try:
            # Execute through master filter
            result = self.master_filter.execute_shot(user_id, execution_params)
            
            # Call execution callback if provided
            if self.execution_callback:
                await self.execution_callback(user_id, signal, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error for user {user_id}: {e}")
            return {
                'success': False,
                'message': f"Execution failed: {str(e)}"
            }
    
    def handle_selector_command(self, user_id: int, command: str, 
                              tier: TierLevel) -> str:
        """Handle selector-related commands"""
        
        selector = self.get_user_selector(user_id, tier)
        if not selector:
            return "⚠️ Selector switch requires COMMANDER or tier"
        
        if command == '/selector':
            # Show current status
            status = selector.get_mode_status()
            return SelectorUI.format_mode_display(selector.mode, status)
            
        elif command == '/selector safe':
            success, message = selector.set_mode(SelectorMode.SAFE)
            return f"✅ {message}" if success else f"❌ {message}"
            
        elif command == '/selector semi':
            success, message = selector.set_mode(SelectorMode.SEMI)
            return f"✅ {message}" if success else f"❌ {message}"
            
        elif command == '/selector full':
            success, message = selector.set_mode(SelectorMode.FULL)
            return f"✅ {message}" if success else f"❌ {message}"
            
        elif command == '/selector stop':
            result = selector.emergency_stop()
            return f"🛑 {result['message']}"
            
        elif command.startswith('/selector config'):
            # Parse config updates
            # Example: /selector config min_tcs=93
            parts = command.split()
            if len(parts) > 2:
                config_updates = {}
                for part in parts[2:]:
                    if '=' in part:
                        key, value = part.split('=')
                        # Convert value type
                        if value.isdigit():
                            value = int(value)
                        elif value.lower() in ['true', 'false']:
                            value = value.lower() == 'true'
                        config_updates[key] = value
                
                if selector.configure_auto_mode(**config_updates):
                    return f"✅ AUTO mode config updated: {config_updates}"
            
            return "❌ Invalid config format. Use: /selector config key=value"
        
        return "❓ Unknown selector command"
    
    def get_selector_dashboard(self, user_id: int) -> Optional[Dict]:
        """Get selector dashboard data"""
        
        selector = self.user_selectors.get(user_id)
        if not selector:
            return None
        
        return {
            'mode': selector.mode.value,
            'status': selector.get_mode_status(),
            'auto_config': selector.auto_config.__dict__ if selector.mode == SelectorMode.FULL else None,
            'semi_config': selector.semi_config.__dict__ if selector.mode == SelectorMode.SEMI else None
        }

# Example integration with Telegram
async def selector_telegram_handler(update: Dict, integration: SelectorIntegration):
    """Example handler for Telegram integration"""
    
    user_id = update.get('user_id')
    text = update.get('text', '')
    
    if text.startswith('/selector'):
        # Handle selector commands
        response = integration.handle_selector_command(
            user_id, text, TierLevel.COMMANDER  # Would get from user data
        )
        return {'type': 'message', 'text': response}
    
    elif text.startswith('confirm_'):
        # Handle confirmation response
        confirmation_id = text.replace('confirm_', '')
        result = await integration.handle_user_confirmation(
            user_id, confirmation_id, 'confirm'
        )
        return {'type': 'message', 'text': f"✅ {result.get('message', 'Processed')}"}
    
    elif text.startswith('reject_'):
        # Handle rejection
        confirmation_id = text.replace('reject_', '')
        result = await integration.handle_user_confirmation(
            user_id, confirmation_id, 'reject'
        )
        return {'type': 'message', 'text': f"❌ {result.get('message', 'Rejected')}"}