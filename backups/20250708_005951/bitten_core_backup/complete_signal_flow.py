#!/usr/bin/env python3
"""
Complete BITTEN Signal Flow
Connects all existing components for automated trading
"""

import asyncio
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import existing components
from .signal_alerts import SignalAlertSystem, SignalAlert
from .market_analyzer import MarketAnalyzer
from .tcs_scoring import TCSCalculator
from .fire_router import FireRouter
from .user_profile import UserProfileManager
from .mt5_farm_adapter import MT5FarmAdapter as MT5BridgeAdapter
from .trade_confirmation_system import TradeConfirmationSystem

@dataclass
class UserTradeData:
    """Track individual user's trade data"""
    user_id: int
    signal_id: str
    fired_at: Optional[int] = None
    trade_result: Optional[Dict] = None
    confirmation_sent: bool = False

class CompleteBITTENFlow:
    """
    Complete automated signal flow:
    1. Monitor live data
    2. Send brief Telegram alerts
    3. Show mission briefing in WebApp
    4. Execute trades automatically
    5. Track confirmations per user
    """
    
    def __init__(self, bot_token: str, webapp_base_url: str):
        # Initialize all components
        self.signal_alerts = SignalAlertSystem(
            bot_token=bot_token,
            hud_webapp_url=f"{webapp_base_url}/mission"
        )
        self.market_analyzer = MarketAnalyzer()
        self.tcs_calculator = TCSCalculator()
        self.fire_router = FireRouter()
        self.user_profiles = UserProfileManager()
        self.mt5_bridge = MT5BridgeAdapter()
        self.confirmations = TradeConfirmationSystem()
        
        # Track active signals and user actions
        self.active_signals: Dict[str, Dict] = {}
        self.user_trades: Dict[str, UserTradeData] = {}
        self.signal_fire_counts: Dict[str, int] = {}  # Track how many fired
        
    async def start_live_monitoring(self):
        """Start monitoring live market data"""
        print("🔍 Starting live market monitoring...")
        
        while True:
            try:
                # Get current market data
                market_data = await self.market_analyzer.get_current_state()
                
                # Check each currency pair
                for symbol in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']:
                    # Analyze for signal
                    signal_data = await self._analyze_for_signal(symbol, market_data)
                    
                    if signal_data:
                        # Signal detected! Process it
                        await self._process_new_signal(signal_data)
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _analyze_for_signal(self, symbol: str, market_data: Dict) -> Optional[Dict]:
        """Analyze market data for trading opportunity"""
        # Get strategy recommendation
        strategy = self.market_analyzer.determine_strategy(symbol, market_data)
        
        if not strategy:
            return None
        
        # Calculate TCS score
        tcs_score = self.tcs_calculator.calculate_score(
            symbol=symbol,
            timeframe='M5',
            indicators=market_data.get('indicators', {})
        )
        
        # Check if meets minimum requirements
        if tcs_score < 70:  # Minimum 70% confidence
            return None
        
        # Create signal data
        signal_data = {
            'symbol': symbol,
            'direction': strategy['direction'],
            'entry_price': market_data['current_price'],
            'stop_loss': strategy['stop_loss'],
            'take_profit': strategy['take_profit'],
            'tcs_score': tcs_score,
            'strategy_type': strategy['type'],
            'expires_in': 600  # 10 minutes
        }
        
        return signal_data
    
    async def _process_new_signal(self, signal_data: Dict):
        """Process detected signal and alert users"""
        # Generate unique signal ID
        signal_id = f"sig_{int(time.time())}_{signal_data['symbol']}"
        
        # Store signal
        self.active_signals[signal_id] = {
            **signal_data,
            'id': signal_id,
            'created_at': int(time.time()),
            'expires_at': int(time.time()) + signal_data['expires_in']
        }
        
        # Initialize fire count
        self.signal_fire_counts[signal_id] = 0
        
        # Create signal alert
        signal_alert = SignalAlert(
            signal_id=signal_id,
            symbol=signal_data['symbol'],
            direction=signal_data['direction'],
            confidence=signal_data['tcs_score'] / 100,
            urgency='HIGH' if signal_data['tcs_score'] > 85 else 'MEDIUM',
            timestamp=int(time.time()),
            expires_at=int(time.time()) + signal_data['expires_in']
        )
        
        # Get eligible users based on tier and TCS requirements
        eligible_users = await self._get_eligible_users(signal_data)
        
        # Send alerts to eligible users
        for user in eligible_users:
            await self.signal_alerts.send_signal_alert(
                user_id=user['user_id'],
                signal=signal_alert,
                user_tier=user['tier']
            )
            
            # Track user's potential trade
            trade_key = f"{user['user_id']}_{signal_id}"
            self.user_trades[trade_key] = UserTradeData(
                user_id=user['user_id'],
                signal_id=signal_id
            )
    
    async def _get_eligible_users(self, signal_data: Dict) -> List[Dict]:
        """Get users eligible for this signal based on tier"""
        all_users = await self.user_profiles.get_active_users()
        eligible = []
        
        # Check tier requirements
        min_tier = 'NIBBLER'  # Default
        if signal_data['tcs_score'] > 85:
            min_tier = 'FANG'  # High confidence signals for Fang+
        
        tier_hierarchy = ['NIBBLER', 'FANG', 'COMMANDER', 'APEX']
        min_tier_index = tier_hierarchy.index(min_tier)
        
        for user in all_users:
            user_tier_index = tier_hierarchy.index(user['tier'])
            if user_tier_index >= min_tier_index:
                eligible.append(user)
        
        return eligible
    
    async def handle_fire_action(self, user_id: int, signal_id: str) -> Dict:
        """Handle when user fires on a signal from WebApp"""
        # Validate signal is still active
        if signal_id not in self.active_signals:
            return {'success': False, 'error': 'Signal expired'}
        
        signal = self.active_signals[signal_id]
        
        # Check if expired
        if time.time() > signal['expires_at']:
            return {'success': False, 'error': 'Signal expired'}
        
        # Get user profile
        user = await self.user_profiles.get_user(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Calculate lot size based on risk management
        lot_size = self._calculate_lot_size(user, signal)
        
        # Execute trade via MT5 bridge
        trade_params = {
            'symbol': signal['symbol'],
            'direction': signal['direction'],
            'lot_size': lot_size,
            'entry_price': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'user_id': user_id,
            'signal_id': signal_id
        }
        
        result = await self.mt5_bridge.execute_trade(trade_params)
        
        # Update fire count
        self.signal_fire_counts[signal_id] += 1
        
        # Track user's trade
        trade_key = f"{user_id}_{signal_id}"
        if trade_key in self.user_trades:
            self.user_trades[trade_key].fired_at = int(time.time())
            self.user_trades[trade_key].trade_result = result
        
        # Send confirmation to user's briefing
        await self._send_trade_confirmation(user_id, signal_id, result)
        
        # Update user stats
        await self._update_user_stats(user_id, result)
        
        return {
            'success': result['success'],
            'trade_id': result.get('ticket'),
            'message': result.get('message', 'Trade executed'),
            'fire_count': self.signal_fire_counts[signal_id]
        }
    
    def _calculate_lot_size(self, user: Dict, signal: Dict) -> float:
        """Calculate lot size based on user's risk management"""
        # Get user's account balance
        balance = user.get('account_balance', 1000)
        
        # Risk percentage based on tier
        risk_percentages = {
            'NIBBLER': 0.02,    # 2%
            'FANG': 0.02,       # 2%
            'COMMANDER': 0.02,  # 2%
            'APEX': 0.02        # 2% (can be increased for special modes)
        }
        
        risk_percent = risk_percentages.get(user['tier'], 0.02)
        
        # Calculate risk amount
        risk_amount = balance * risk_percent
        
        # Calculate pip value and lot size
        # Simplified calculation - in production use proper pip value calculation
        pip_risk = abs(signal['entry_price'] - signal['stop_loss']) * 10000
        lot_size = risk_amount / (pip_risk * 10)  # $10 per pip for standard lot
        
        # Round to valid lot size
        lot_size = round(lot_size, 2)
        
        # Apply limits
        min_lot = 0.01
        max_lot = 0.10 if user['tier'] == 'NIBBLER' else 0.50
        
        return max(min_lot, min(lot_size, max_lot))
    
    async def _send_trade_confirmation(self, user_id: int, signal_id: str, result: Dict):
        """Send trade confirmation back to user's briefing"""
        confirmation_data = {
            'user_id': user_id,
            'signal_id': signal_id,
            'success': result['success'],
            'ticket': result.get('ticket'),
            'executed_at': int(time.time()),
            'message': result.get('message')
        }
        
        # Send to confirmation system
        await self.confirmations.send_confirmation(confirmation_data)
        
        # Update WebApp with real-time confirmation
        # This would update the user's mission briefing page
        await self._update_webapp_confirmation(user_id, signal_id, confirmation_data)
    
    async def _update_webapp_confirmation(self, user_id: int, signal_id: str, confirmation: Dict):
        """Update WebApp with trade confirmation"""
        # In production, this would use WebSocket or Server-Sent Events
        # to update the user's mission briefing in real-time
        pass
    
    async def _update_user_stats(self, user_id: int, trade_result: Dict):
        """Update user's stats after trade"""
        if trade_result['success']:
            # Update trades taken
            await self.user_profiles.increment_stat(user_id, 'trades_taken')
            
            # Update daily stats
            await self.user_profiles.update_daily_stats(user_id, {
                'trades': 1,
                'last_trade': int(time.time())
            })
    
    async def get_signal_stats(self, signal_id: str) -> Dict:
        """Get live stats for a signal (for WebApp display)"""
        if signal_id not in self.active_signals:
            return None
        
        signal = self.active_signals[signal_id]
        
        return {
            'signal_id': signal_id,
            'fire_count': self.signal_fire_counts.get(signal_id, 0),
            'time_remaining': max(0, signal['expires_at'] - int(time.time())),
            'active': time.time() < signal['expires_at']
        }
    
    async def get_user_mission_data(self, user_id: int, signal_id: str) -> Dict:
        """Get complete mission briefing data for WebApp"""
        # Get user profile
        user = await self.user_profiles.get_user(user_id)
        
        # Get signal data
        signal = self.active_signals.get(signal_id)
        if not signal:
            return None
        
        # Get user's recent stats
        user_stats = {
            'last_7d_pnl': user.get('stats', {}).get('last_7d_pnl', 0),
            'win_rate': user.get('stats', {}).get('win_rate', 0),
            'trades_today': user.get('stats', {}).get('trades_today', 0),
            'rank': user.get('rank', 'RECRUIT'),
            'xp': user.get('xp', 0)
        }
        
        # Get live signal stats
        signal_stats = await self.get_signal_stats(signal_id)
        
        # Check if user already fired
        trade_key = f"{user_id}_{signal_id}"
        user_fired = trade_key in self.user_trades and self.user_trades[trade_key].fired_at
        
        return {
            'user': {
                'id': user_id,
                'tier': user['tier'],
                'stats': user_stats,
                'profile_url': f"/me/{user_id}"
            },
            'signal': signal,
            'signal_stats': signal_stats,
            'user_fired': user_fired,
            'tier_features': self._get_tier_features(user['tier'])
        }
    
    def _get_tier_features(self, tier: str) -> Dict:
        """Get tier-specific features for mission briefing"""
        features = {
            'NIBBLER': {
                'analysis_depth': 'basic',
                'indicators_shown': ['price', 'trend'],
                'education_tabs': ['basics']
            },
            'FANG': {
                'analysis_depth': 'advanced',
                'indicators_shown': ['price', 'trend', 'rsi', 'macd'],
                'education_tabs': ['basics', 'advanced']
            },
            'COMMANDER': {
                'analysis_depth': 'expert',
                'indicators_shown': 'all',
                'education_tabs': ['basics', 'advanced', 'pro']
            },
            'APEX': {
                'analysis_depth': 'elite',
                'indicators_shown': 'all',
                'education_tabs': 'all',
                'special_features': ['ai_analysis', 'multi_timeframe']
            }
        }
        
        return features.get(tier, features['NIBBLER'])