# hud_router.py
# BITTEN HUD Backend Router - Signal data and tier validation

import json
import time
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from flask import Flask, request, jsonify
import asyncio

from .rank_access import RankAccess, UserRank
from .signal_alerts import SignalAlert, SignalAlertSystem
from .user_profile import UserProfileManager

@dataclass
class HUDSignalData:
    """Extended signal data for HUD display"""
    id: str
    symbol: str
    direction: str
    confidence: float
    urgency: str
    entry_price: float
    stop_loss: float
    take_profit: float
    expires_at: int
    strategy: Dict
    created_at: int
    
class HUDRouter:
    """Backend router for Sniper HUD operations"""
    
    def __init__(self, app: Flask, bot_token: str):
        self.app = app
        self.bot_token = bot_token
        self.rank_access = RankAccess()
        self.profile_manager = UserProfileManager()
        self.active_signals: Dict[str, HUDSignalData] = {}
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes for HUD"""
        
        @self.app.route('/api/hud/signal/<signal_id>', methods=['GET'])
        def get_signal(signal_id):
            return self._handle_get_signal(signal_id)
        
        @self.app.route('/api/hud/execute', methods=['POST'])
        def execute_signal():
            return self._handle_execute_signal()
        
        @self.app.route('/api/hud/profile', methods=['GET'])
        def get_profile():
            return self._handle_get_profile()
        
        @self.app.route('/api/hud/recruit/<telegram_id>', methods=['POST'])
        def register_recruit(telegram_id):
            return self._handle_register_recruit(telegram_id)
    
    def _verify_telegram_auth(self) -> Tuple[bool, Optional[int]]:
        """Verify Telegram WebApp authentication"""
        auth_header = request.headers.get('Authorization', '')
        user_id_header = request.headers.get('X-User-ID', '')
        
        if not auth_header.startswith('Bearer '):
            return False, None
        
        init_data = auth_header[7:]  # Remove 'Bearer '
        
        # Verify init data (simplified - in production use proper validation)
        # https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
        try:
            # Parse init data
            parsed_data = {}
            for param in init_data.split('&'):
                key, value = param.split('=')
                parsed_data[key] = value
            
            # Verify hash (simplified)
            if 'hash' not in parsed_data:
                return False, None
            
            # Extract user ID
            user_id = int(user_id_header) if user_id_header else None
            return True, user_id
            
        except Exception:
            return False, None
    
    def _handle_get_signal(self, signal_id: str):
        """Get signal data for HUD display"""
        # Verify authentication
        is_valid, user_id = self._verify_telegram_auth()
        if not is_valid:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get signal
        signal = self.active_signals.get(signal_id)
        if not signal:
            return jsonify({'error': 'Signal not found'}), 404
        
        # Check if expired
        if signal.expires_at < time.time():
            return jsonify({'error': 'Signal expired'}), 410
        
        # Get user rank
        user_rank = self.rank_access.get_user_rank(user_id)
        
        # Check access level
        access_info = self._check_signal_access(signal, user_rank)
        
        # Prepare response
        response_data = {
            'signal': {
                'id': signal.id,
                'symbol': signal.symbol,
                'direction': signal.direction,
                'confidence': signal.confidence,
                'urgency': signal.urgency,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'expires_at': signal.expires_at,
                'strategy': signal.strategy
            },
            'access': access_info,
            'user_tier': user_rank.name
        }
        
        return jsonify(response_data)
    
    def _handle_execute_signal(self):
        """Execute signal from HUD"""
        # Verify authentication
        is_valid, user_id = self._verify_telegram_auth()
        if not is_valid:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Parse request data
        data = request.get_json()
        signal_id = data.get('signal_id')
        position_size = data.get('position_size', 0.01)
        
        # Get signal
        signal = self.active_signals.get(signal_id)
        if not signal:
            return jsonify({'success': False, 'message': 'Signal not found'}), 404
        
        # Check if expired
        if signal.expires_at < time.time():
            return jsonify({'success': False, 'message': 'Signal expired'}), 410
        
        # Get user rank
        user_rank = self.rank_access.get_user_rank(user_id)
        
        # Check access
        access_info = self._check_signal_access(signal, user_rank)
        if not access_info['can_execute']:
            return jsonify({
                'success': False, 
                'message': f'Tier {access_info["required_tier"]} required'
            }), 403
        
        # Execute trade (integrate with your trading system)
        execution_result = self._execute_trade(user_id, signal, position_size)
        
        if execution_result['success']:
            # Update user stats
            self.profile_manager.record_trade_execution(
                user_id, 
                signal_id, 
                execution_result['position_id']
            )
            
            # Get updated stats
            updated_stats = self.profile_manager.get_user_stats(user_id)
            
            return jsonify({
                'success': True,
                'position_id': execution_result['position_id'],
                'entry_price': execution_result['entry_price'],
                'updated_stats': updated_stats
            })
        else:
            return jsonify({
                'success': False,
                'message': execution_result['message']
            })
    
    def _handle_get_profile(self):
        """Get user profile data"""
        # Verify authentication
        is_valid, user_id = self._verify_telegram_auth()
        if not is_valid:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get profile data
        profile_data = self.profile_manager.get_full_profile(user_id)
        
        return jsonify(profile_data)
    
    def _handle_register_recruit(self, recruit_telegram_id: str):
        """Register a new recruit"""
        # Verify authentication
        is_valid, recruiter_id = self._verify_telegram_auth()
        if not is_valid:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Parse request data
        data = request.get_json()
        recruit_username = data.get('username', 'Unknown')
        
        # Register recruit
        success = self.profile_manager.register_recruit(
            recruiter_id, 
            int(recruit_telegram_id),
            recruit_username
        )
        
        if success:
            # Get updated recruiter stats
            recruiter_stats = self.profile_manager.get_recruiting_stats(recruiter_id)
            
            return jsonify({
                'success': True,
                'message': 'Recruit registered successfully',
                'updated_stats': recruiter_stats
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to register recruit'
            })
    
    def _check_signal_access(self, signal: HUDSignalData, user_rank: UserRank) -> Dict:
        """Check if user has access to execute signal"""
        # Define urgency requirements
        urgency_requirements = {
            'MEDIUM': UserRank.USER,
            'HIGH': UserRank.AUTHORIZED,
            'CRITICAL': UserRank.ELITE
        }
        
        required_rank = urgency_requirements.get(signal.urgency, UserRank.ELITE)
        can_execute = user_rank.value >= required_rank.value
        
        return {
            'can_execute': can_execute,
            'required_tier': required_rank.name if not can_execute else None,
            'user_tier': user_rank.name
        }
    
    def _execute_trade(self, user_id: int, signal: HUDSignalData, position_size: float) -> Dict:
        """Execute trade based on signal"""
        # This would integrate with your actual trading system
        # For now, return mock result
        
        # Simulate execution
        import random
        success = random.random() > 0.1  # 90% success rate
        
        if success:
            return {
                'success': True,
                'position_id': f"POS-{int(time.time())}-{user_id}",
                'entry_price': signal.entry_price + random.uniform(-0.0001, 0.0001)
            }
        else:
            return {
                'success': False,
                'message': 'Execution failed - market conditions changed'
            }
    
    def add_signal(self, signal_data: Dict) -> str:
        """Add new signal to active signals"""
        signal_id = f"SIG-{int(time.time())}-{signal_data['symbol']}"
        
        signal = HUDSignalData(
            id=signal_id,
            symbol=signal_data['symbol'],
            direction=signal_data['direction'],
            confidence=signal_data['confidence'],
            urgency=signal_data['urgency'],
            entry_price=signal_data['entry_price'],
            stop_loss=signal_data['stop_loss'],
            take_profit=signal_data['take_profit'],
            expires_at=int(time.time()) + signal_data.get('ttl', 300),  # 5 min default
            strategy=signal_data.get('strategy', {}),
            created_at=int(time.time())
        )
        
        self.active_signals[signal_id] = signal
        return signal_id
    
    def cleanup_expired_signals(self):
        """Remove expired signals"""
        current_time = time.time()
        expired = [
            sid for sid, signal in self.active_signals.items()
            if signal.expires_at < current_time
        ]
        
        for sid in expired:
            del self.active_signals[sid]
        
        return len(expired)
    
    def get_active_signals_count(self) -> Dict[str, int]:
        """Get count of active signals by urgency"""
        counts = {'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        current_time = time.time()
        
        for signal in self.active_signals.values():
            if signal.expires_at > current_time:
                counts[signal.urgency] = counts.get(signal.urgency, 0) + 1
        
        return counts