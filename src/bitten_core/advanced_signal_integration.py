"""
Advanced Signal Integration Module
Bridges the advanced intelligence system with existing BITTEN infrastructure
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
import json

from .advanced_intelligence_aggregator import advanced_aggregator
from .signal_fusion import tier_router, engagement_balancer
from .bitten_core import bitten
from .telegram_router import TelegramRouter
from .signal_display import SignalDisplay
from .fire_router import FireRouter
from .complete_signal_flow_v3 import SignalFlow
from .test_signal_system import test_signal_system, TestSignalSystem

logger = logging.getLogger(__name__)


class AdvancedSignalIntegration:
    """
    Integrates advanced signal intelligence with BITTEN's existing systems
    """
    
    def __init__(self):
        self.advanced_aggregator = advanced_aggregator
        self.telegram_router = TelegramRouter()
        self.signal_display = SignalDisplay()
        self.fire_router = FireRouter()
        self.signal_flow = SignalFlow()
        self.test_signal_system = test_signal_system
        
        # Market data cache
        self.market_data_cache = {}
        
        # Active monitoring
        self.monitoring_active = False
        self.monitored_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
            'NZDUSD', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY'
        ]
        
        # Test signal tracking
        self.test_signals_sent = {}
        
    async def start_monitoring(self):
        """Start monitoring markets with advanced intelligence"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
            
        self.monitoring_active = True
        logger.info("Starting advanced signal monitoring...")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        # Start market data collection
        asyncio.create_task(self._market_data_collection_loop())
        
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("Stopped advanced signal monitoring")
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Analyze each pair
                for pair in self.monitored_pairs:
                    if not self.monitoring_active:
                        break
                        
                    # Get market data
                    market_data = self.market_data_cache.get(pair)
                    if not market_data:
                        continue
                    
                    # Generate advanced signal
                    fused_signal = await self.advanced_aggregator.generate_fused_signal(
                        pair, market_data
                    )
                    
                    if fused_signal:
                        # Process through existing BITTEN flow
                        await self._process_signal(fused_signal)
                
                # Wait before next scan
                await asyncio.sleep(30)  # Scan every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    async def _market_data_collection_loop(self):
        """Collect market data for all pairs"""
        while self.monitoring_active:
            try:
                for pair in self.monitored_pairs:
                    # Collect market data (this would connect to real data sources)
                    market_data = await self._collect_market_data(pair)
                    self.market_data_cache[pair] = market_data
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Market data collection error: {e}")
                await asyncio.sleep(5)
    
    async def _collect_market_data(self, pair: str) -> Dict:
        """
        Collect comprehensive market data for a pair
        In production, this would connect to:
        - MT5 for price/volume data
        - Order book data providers
        - News APIs
        - Social media APIs
        """
        # For now, return mock data structure
        return {
            'pair': pair,
            'timestamp': datetime.now(),
            'current_price': 1.0850,  # Mock price
            'volume': 50000,
            'spread': 1.2,
            'normal_spread': 1.5,
            'atr': 25,
            'rsi': 55,
            'macd': 0.0002,
            'bb_upper': 1.0870,
            'bb_lower': 1.0830,
            'volume_ratio': 1.2,
            'price_history': [1.0840 + i * 0.0001 for i in range(100)],
            'order_book': {
                'bids': [(1.0849, 1000), (1.0848, 2000), (1.0847, 1500)],
                'asks': [(1.0851, 1200), (1.0852, 1800), (1.0853, 2200)],
                'timestamp': datetime.now()
            },
            'session': self._get_current_session(),
            'economic_calendar': [],  # Would fetch real calendar events
            'market_sentiment': 'neutral'
        }
    
    def _get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now().hour
        if 7 <= hour < 16:  # London
            return 'LONDON'
        elif 13 <= hour < 22:  # New York
            return 'NEW_YORK'
        elif 23 <= hour or hour < 8:  # Tokyo
            return 'TOKYO'
        else:
            return 'OVERLAP'
    
    async def _process_signal(self, fused_signal):
        """Process signal through BITTEN's existing infrastructure"""
        try:
            # Convert to BITTEN signal format
            bitten_signal = self._convert_to_bitten_format(fused_signal)
            
            # Check if we should generate a test signal
            test_signal = None
            if self.test_signal_system.should_generate_test_signal():
                test_signal = self.test_signal_system.generate_test_signal(bitten_signal)
            
            # Get all active users
            users = await self._get_active_users()
            
            for user in users:
                # Decide which signal to send (test or regular)
                signal_to_send = bitten_signal
                is_test_signal = False
                
                # Check if this user should get the test signal
                if test_signal and self.test_signal_system.should_send_to_user(user['user_id'], user['tier']):
                    signal_to_send = test_signal
                    is_test_signal = True
                    logger.info(f"Sending TEST signal to user {user['user_id']}")
                
                # Check tier routing (skip for test signals)
                if not is_test_signal and not tier_router.route_signal(fused_signal, user['tier']):
                    continue
                
                # Check engagement balancing (skip for test signals)
                if not is_test_signal:
                    should_send, reason = engagement_balancer.should_send_signal(
                        fused_signal, user['user_id'], user['tier']
                    )
                    
                    if not should_send:
                        logger.debug(f"Signal not sent to {user['user_id']}: {reason}")
                        continue
                
                # Check fire mode permissions
                if not self._check_fire_mode_permission(user, signal_to_send):
                    continue
                
                # Send signal to user
                if is_test_signal:
                    await self._send_test_signal_to_user(user, signal_to_send)
                else:
                    await self._send_signal_to_user(user, signal_to_send, fused_signal)
                    # Record signal sent
                    engagement_balancer.record_signal_sent(fused_signal, user['user_id'])
            
        except Exception as e:
            logger.error(f"Signal processing error: {e}")
    
    def _convert_to_bitten_format(self, fused_signal) -> Dict:
        """Convert fused signal to BITTEN format"""
        return {
            'signal_id': fused_signal.signal_id,
            'pair': fused_signal.pair,
            'action': fused_signal.direction,
            'entry': fused_signal.entry,
            'sl': fused_signal.sl,
            'tp': fused_signal.tp,
            'confidence': fused_signal.confidence,
            'tier': fused_signal.tier.value,
            'timestamp': fused_signal.timestamp,
            'metadata': {
                'sources': len(fused_signal.sources),
                'agreement_score': fused_signal.agreement_score,
                'fusion_scores': fused_signal.fusion_scores
            }
        }
    
    async def _get_active_users(self) -> List[Dict]:
        """Get list of active users with their tiers"""
        # In production, this would query the database
        # For now, return mock data
        return [
            {'user_id': '123', 'tier': 'nibbler', 'fire_mode': 'SEMI_AUTO'},
            {'user_id': '456', 'tier': 'fang', 'fire_mode': 'SEMI_AUTO'},
            {'user_id': '789', 'tier': 'commander', 'fire_mode': 'AUTO_FIRE'}
        ]
    
    def _check_fire_mode_permission(self, user: Dict, signal: Dict) -> bool:
        """Check if user's fire mode allows this signal"""
        fire_mode = user.get('fire_mode', 'SEMI_AUTO')
        tier = user.get('tier', 'nibbler')
        
        # Use existing fire mode validation
        # For now, simplified check
        if fire_mode == 'CEASEFIRE':
            return False
        
        if signal['confidence'] < 70 and tier == 'nibbler':
            return False
        
        return True
    
    async def _send_signal_to_user(self, user: Dict, signal: Dict, fused_signal):
        """Send signal to user via Telegram"""
        try:
            # Format signal for display
            formatted_signal = self.signal_display.format_signal(
                signal, user['tier']
            )
            
            # Add advanced intelligence insights
            insights = self._generate_insights(fused_signal)
            
            message = f"{formatted_signal}\n\n{insights}"
            
            # Send via Telegram (would use actual bot in production)
            logger.info(f"Sending signal to user {user['user_id']}: {signal['pair']} {signal['action']}")
            
            # Track signal sent
            await self._track_signal_sent(user['user_id'], signal)
            
        except Exception as e:
            logger.error(f"Error sending signal to user {user['user_id']}: {e}")
    
    async def _send_test_signal_to_user(self, user: Dict, test_signal: Dict):
        """Send test signal to user via Telegram"""
        try:
            # Format signal for display (will show the 60 pip SL prominently)
            formatted_signal = self.signal_display.format_signal(
                test_signal, user['tier']
            )
            
            # Add subtle warning indicators (but not too obvious)
            warning_hints = "\n\n⚠️ TCS: 60 pips | R:R 1:0.33"
            
            message = f"{formatted_signal}{warning_hints}"
            
            # Send via Telegram
            logger.info(f"Sending TEST signal to user {user['user_id']}: {test_signal['pair']} (60 TCS)")
            
            # Track test signal sent
            self.test_signal_system.record_signal_sent(
                test_signal['test_signal_id'], 
                user['user_id']
            )
            
            # Store in tracking dict for later result processing
            self.test_signals_sent[test_signal['test_signal_id']] = {
                'user_id': user['user_id'],
                'sent_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error sending test signal to user {user['user_id']}: {e}")
    
    def _generate_insights(self, fused_signal) -> str:
        """Generate human-readable insights from signal intelligence"""
        insights = []
        
        # Source agreement
        insights.append(f"📊 Source Agreement: {fused_signal.agreement_score:.0f}%")
        
        # Key factors
        for source in fused_signal.sources[:3]:  # Top 3 sources
            emoji = {
                'technical': '📈',
                'sentiment': '💭',
                'order_flow': '📊',
                'ai_ml': '🤖',
                'fundamental': '🌍'
            }.get(source.source_type, '📌')
            
            insights.append(f"{emoji} {source.source_id}: {source.confidence:.0f}%")
        
        return '\n'.join(insights)
    
    async def _track_signal_sent(self, user_id: str, signal: Dict):
        """Track that signal was sent to user"""
        # In production, this would write to database
        logger.debug(f"Tracked signal {signal['signal_id']} sent to {user_id}")
    
    async def process_trade_result(self, trade_id: str, result: Dict):
        """Process trade result to update signal performance"""
        try:
            # Extract signal ID from trade
            signal_id = result.get('signal_id')
            if not signal_id:
                return
            
            # Check if this is a test signal result
            if signal_id.startswith('TEST_'):
                await self._process_test_signal_result(signal_id, result)
                return
            
            # Determine if trade was successful
            profit = result.get('profit', 0)
            success = profit > 0
            
            # Update advanced aggregator
            self.advanced_aggregator.update_signal_result(signal_id, success)
            
            logger.info(f"Updated signal {signal_id} with result: {'WIN' if success else 'LOSS'}")
            
        except Exception as e:
            logger.error(f"Error processing trade result: {e}")
    
    async def _process_test_signal_result(self, signal_id: str, result: Dict):
        """Process test signal trade result"""
        try:
            # Get user info
            test_info = self.test_signals_sent.get(signal_id)
            if not test_info:
                logger.warning(f"Test signal {signal_id} not found in tracking")
                return
            
            user_id = test_info['user_id']
            
            # Determine result
            profit = result.get('profit', 0)
            hit_sl = result.get('hit_stop_loss', False)
            
            if hit_sl:
                trade_result = "hit_sl"
            elif profit > 0:
                trade_result = "won"
            else:
                trade_result = "hit_sl"  # Any loss counts as hitting SL for test
            
            # Record the result
            rewards = self.test_signal_system.record_user_action(
                signal_id, user_id, "taken", trade_result
            )
            
            # Process rewards
            await self._process_test_signal_rewards(user_id, rewards)
            
            logger.info(f"Processed test signal {signal_id} result for user {user_id}: {trade_result}")
            
        except Exception as e:
            logger.error(f"Error processing test signal result: {e}")
    
    async def process_user_passed_signal(self, user_id: str, signal_id: str):
        """Process when user passes on a signal (doesn't take it)"""
        try:
            # Check if this was a test signal
            if signal_id.startswith('TEST_'):
                # User correctly identified and passed the test signal
                rewards = self.test_signal_system.record_user_action(
                    signal_id, user_id, "passed"
                )
                
                # Process rewards
                await self._process_test_signal_rewards(user_id, rewards)
                
                logger.info(f"User {user_id} passed test signal {signal_id} - Good catch!")
                
        except Exception as e:
            logger.error(f"Error processing passed signal: {e}")
    
    async def _process_test_signal_rewards(self, user_id: str, rewards: Dict):
        """Process rewards from test signal actions"""
        try:
            # Award XP if earned
            if rewards['xp_earned'] > 0:
                # This would integrate with the XP system
                logger.info(f"Awarding {rewards['xp_earned']} XP to user {user_id}")
                # TODO: Call XP integration manager to add XP
            
            # Grant extra shots if earned
            if rewards['extra_shots'] > 0:
                # This would integrate with daily shot system
                logger.info(f"Granting {rewards['extra_shots']} extra shots to user {user_id}")
                # TODO: Call shot manager to add extra shots
            
            # Process achievement if earned
            if rewards['achievement']:
                achievement = rewards['achievement']
                logger.info(f"User {user_id} earned achievement: {achievement['name']}")
                # TODO: Call achievement system to unlock
            
            # Send notification to user
            if rewards['message']:
                # This would send via Telegram
                logger.info(f"Notifying user {user_id}: {rewards['message']}")
                # TODO: Send telegram message
                
        except Exception as e:
            logger.error(f"Error processing test signal rewards: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'monitoring_active': self.monitoring_active,
            'monitored_pairs': len(self.monitored_pairs),
            'cached_data_pairs': len(self.market_data_cache),
            'performance': self.advanced_aggregator.get_performance_stats(),
            'tier_routing': {
                tier: tier_router.get_user_stats(tier)
                for tier in ['nibbler', 'fang', 'commander', 'apex']
            },
            'test_signals': {
                'total_sent': len(self.test_signal_system.signal_history),
                'active_tracking': len(self.test_signals_sent),
                'top_detectors': self.test_signal_system.get_leaderboard(5)
            }
        }
        
        return stats
    
    def get_test_signal_stats(self, user_id: str) -> Dict[str, Any]:
        """Get test signal statistics for a specific user"""
        return self.test_signal_system.get_user_stats(user_id)


# Create global instance
advanced_integration = AdvancedSignalIntegration()


# Integration functions for existing BITTEN system
async def start_advanced_signals():
    """Start the advanced signal system"""
    await advanced_integration.start_monitoring()
    return {"status": "Advanced signals started"}


async def stop_advanced_signals():
    """Stop the advanced signal system"""
    await advanced_integration.stop_monitoring()
    return {"status": "Advanced signals stopped"}


async def get_advanced_stats():
    """Get advanced system statistics"""
    return advanced_integration.get_system_stats()


async def process_trade_result(trade_id: str, result: Dict):
    """Process trade result for learning"""
    await advanced_integration.process_trade_result(trade_id, result)