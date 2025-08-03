#!/usr/bin/env python3
"""
🏛️ ATHENA SIGNAL DISPATCHER
Replaces generic mission briefing system with ATHENA tactical command
Routes all signals through ATHENA Mission Bot for tactical briefings
"""

import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AthenaSignalDispatcher')

class AthenaSignalDispatcher:
    """
    Strategic signal dispatcher that routes all BITTEN signals through ATHENA
    Replaces generic briefing system with tactical command authority
    """
    
    def __init__(self):
        # ATHENA Mission Bot configuration
        self.athena_bot_token = "8322305650:AAGtBpEMm759_7gI4m9sg0OJwFhBVjR4pEI"
        self.telegram_api_base = f"https://api.telegram.org/bot{self.athena_bot_token}"
        
        # Signal dispatch tracking
        self.dispatched_signals = {}
        self.dispatch_counter = 0
        
        # Authorized users for signal dispatch
        self.authorized_users = {
            "7176191872": {
                "tier": "COMMANDER",
                "chat_id": "7176191872",
                "name": "Commander"
            }
            # Add more users as needed
        }
        
        # Load ATHENA personality
        try:
            from src.bitten_core.personality.athena_personality import AthenaPersonality
            self.athena = AthenaPersonality()
            self.athena_available = True
            logger.info("✅ ATHENA personality loaded for signal dispatch")
        except ImportError as e:
            logger.error(f"❌ ATHENA personality not available: {e}")
            self.athena_available = False
        
        logger.info("🏛️ ATHENA Signal Dispatcher initialized")
    
    def dispatch_signal_via_athena(self, signal_data: Dict) -> Dict:
        """
        Main method to dispatch signals through ATHENA tactical voice
        This replaces the generic mission briefing system
        """
        if not self.athena_available:
            logger.error("❌ ATHENA personality offline - cannot dispatch tactical briefing")
            return {'success': False, 'error': 'ATHENA offline'}
        
        try:
            # Extract signal information
            signal_id = signal_data.get('signal_id', f'ATHENA_{int(time.time())}')
            symbol = signal_data.get('symbol', 'UNKNOWN')
            direction = signal_data.get('direction', 'UNKNOWN')
            confidence = signal_data.get('confidence', 0)
            entry_price = signal_data.get('entry_price', 0)
            
            logger.info(f"🏛️ Dispatching tactical briefing: {signal_id} - {symbol} {direction}")
            
            # Generate mission briefing for each authorized user
            dispatch_results = []
            
            for user_id, user_data in self.authorized_users.items():
                try:
                    # Generate ATHENA mission briefing
                    mission_id = f"ATHENA_{symbol}_{self.dispatch_counter:04d}"
                    briefing = self.athena.get_mission_briefing(
                        signal_data, 
                        user_data['tier'], 
                        mission_id
                    )
                    
                    # Add tactical enhancements for high confidence signals
                    if confidence > 85:
                        tactical_line = f"\n\n🎯 **TACTICAL ASSESSMENT**\nIntel confirms {confidence:.1f}% likelihood of mission success.\nStrategic conditions: OPTIMAL"
                        briefing += tactical_line
                    
                    # Add signal tracking
                    briefing += f"\n\n📋 **MISSION CODE**: `{signal_id}`"
                    
                    # Add CITADEL shield information if available
                    if 'citadel_shield' in signal_data:
                        shield_data = signal_data['citadel_shield']
                        shield_score = shield_data.get('score', 0)
                        shield_class = shield_data.get('classification', 'UNVERIFIED')
                        
                        briefing += f"\n\n🛡️ **CITADEL SHIELD ANALYSIS**\nShield Score: {shield_score}/10 - {shield_class}\nRisk Assessment: {shield_data.get('insights', 'Standard parameters')}"
                    
                    # Create fire button for COMMANDER tier
                    reply_markup = None
                    if user_data['tier'] == "COMMANDER":
                        reply_markup = {
                            "inline_keyboard": [[
                                {
                                    "text": "🔥 EXECUTE MISSION",
                                    "callback_data": f"fire_{signal_id}"
                                }
                            ]]
                        }
                    
                    # Send via Telegram API (no markdown to avoid parsing errors)
                    result = self._send_telegram_message(
                        chat_id=user_data['chat_id'],
                        text=briefing,
                        reply_markup=reply_markup,
                        parse_mode=None  # Disable markdown parsing
                    )
                    
                    if result['success']:
                        dispatch_results.append({
                            'user_id': user_id,
                            'message_id': result.get('message_id'),
                            'status': 'dispatched'
                        })
                        logger.info(f"✅ Tactical briefing delivered to {user_data['name']} ({user_id})")
                    else:
                        dispatch_results.append({
                            'user_id': user_id,
                            'status': 'failed',
                            'error': result.get('error')
                        })
                        logger.error(f"❌ Failed to deliver briefing to {user_id}: {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"❌ Dispatch error for user {user_id}: {e}")
                    dispatch_results.append({
                        'user_id': user_id,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Track dispatched signal
            self.dispatch_counter += 1
            self.dispatched_signals[signal_id] = {
                'signal_data': signal_data,
                'dispatched_at': datetime.now().isoformat(),
                'dispatch_results': dispatch_results,
                'mission_counter': self.dispatch_counter
            }
            
            successful_dispatches = len([r for r in dispatch_results if r['status'] == 'dispatched'])
            
            logger.info(f"🏛️ Signal dispatch complete: {successful_dispatches}/{len(dispatch_results)} delivered")
            
            return {
                'success': True,
                'signal_id': signal_id,
                'dispatched_to': successful_dispatches,
                'total_users': len(dispatch_results),
                'dispatch_results': dispatch_results
            }
            
        except Exception as e:
            logger.error(f"❌ ATHENA signal dispatch failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'signal_id': signal_data.get('signal_id', 'unknown')
            }
    
    def send_execution_result(self, signal_id: str, execution_result: Dict) -> Dict:
        """Send execution results via ATHENA tactical voice"""
        if not self.athena_available:
            return {'success': False, 'error': 'ATHENA offline'}
        
        try:
            # Get original signal data
            signal_info = self.dispatched_signals.get(signal_id)
            if not signal_info:
                logger.error(f"❌ Signal {signal_id} not found in dispatch history")
                return {'success': False, 'error': 'Signal not found'}
            
            signal_data = signal_info['signal_data']
            
            # Generate ATHENA execution response
            if execution_result.get('success'):
                response = self.athena.get_execution_success(signal_data, execution_result)
            else:
                response = self.athena.get_execution_failure(signal_data, execution_result)
            
            # Send to all users who received the original signal
            results = []
            for dispatch_result in signal_info['dispatch_results']:
                if dispatch_result['status'] == 'dispatched':
                    user_id = dispatch_result['user_id']
                    user_data = self.authorized_users.get(user_id)
                    
                    if user_data:
                        telegram_result = self._send_telegram_message(
                            chat_id=user_data['chat_id'],
                            text=f"🏛️ **MISSION UPDATE**\n\n{response}"
                        )
                        
                        results.append({
                            'user_id': user_id,
                            'success': telegram_result['success'],
                            'error': telegram_result.get('error')
                        })
            
            logger.info(f"🏛️ Execution results sent for {signal_id}")
            return {
                'success': True,
                'signal_id': signal_id,
                'notification_results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Execution result dispatch failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_telegram_message(self, chat_id: str, text: str, reply_markup: Optional[Dict] = None, parse_mode: Optional[str] = 'Markdown') -> Dict:
        """Send message via Telegram API"""
        try:
            url = f"{self.telegram_api_base}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text
            }
            
            if parse_mode:
                payload['parse_mode'] = parse_mode
            
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return {
                        'success': True,
                        'message_id': result['result']['message_id']
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('description', 'Unknown Telegram error')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
    
    def add_authorized_user(self, user_id: str, tier: str, chat_id: str, name: str = None):
        """Add authorized user for signal dispatch"""
        self.authorized_users[user_id] = {
            'tier': tier,
            'chat_id': chat_id,
            'name': name or f"User_{user_id}"
        }
        logger.info(f"✅ Added authorized user: {name} ({user_id}) - {tier} tier")
    
    def get_dispatch_stats(self) -> Dict:
        """Get signal dispatch statistics"""
        return {
            'total_signals_dispatched': len(self.dispatched_signals),
            'dispatch_counter': self.dispatch_counter,
            'authorized_users': len(self.authorized_users),
            'athena_available': self.athena_available,
            'last_dispatch': max([s['dispatched_at'] for s in self.dispatched_signals.values()]) if self.dispatched_signals else None
        }

# Global instance for easy import
athena_dispatcher = AthenaSignalDispatcher()

def dispatch_signal(signal_data: Dict) -> Dict:
    """Convenience function to dispatch signal via ATHENA"""
    return athena_dispatcher.dispatch_signal_via_athena(signal_data)

def send_execution_result(signal_id: str, execution_result: Dict) -> Dict:
    """Convenience function to send execution results via ATHENA"""
    return athena_dispatcher.send_execution_result(signal_id, execution_result)