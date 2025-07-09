"""
Complete BITTEN Signal Flow V3
Enhanced with Signal Fusion and Confidence Tiers
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
import json
import os

# Import fusion components
from .signal_fusion import (
    signal_fusion_engine, tier_router, engagement_balancer,
    FusedSignal, ConfidenceTier
)
from .intelligence_aggregator import initialize_aggregator

# Import TCS integration components
from .tcs_integration import initialize_tcs_integration, TCSIntegrationLayer
from .tcs_performance_tracker import AdvancedTCSPerformanceTracker

# Import existing components
from .mt5_enhanced_adapter import MT5EnhancedAdapter, MT5AccountMonitor
from .signal_alerts import SignalAlerts
from .live_data_filter import LiveDataFilter

logger = logging.getLogger(__name__)


@dataclass
class EnhancedActiveSignal:
    """Enhanced signal tracking with fusion data"""
    id: str
    fused_signal: FusedSignal
    timestamp: datetime
    fired_by: set
    executions: Dict[int, Dict]  # user_id -> execution data
    performance: Dict[str, Any]  # Performance tracking


class FusionEnhancedSignalFlow:
    """
    Signal flow with intelligence fusion and tier-based distribution
    """
    
    def __init__(self, 
                 webapp_url: str = "https://joinbitten.com",
                 bot_token: str = None,
                 chat_id: str = None):
        
        # Initialize components
        self.signal_alerts = SignalAlerts(bot_token, chat_id)
        self.webapp_url = webapp_url
        
        # Initialize MT5 components
        self.mt5_adapter = MT5EnhancedAdapter()
        self.account_monitor = MT5AccountMonitor(self.mt5_adapter)
        
        # Initialize live data filter
        self.live_filter = LiveDataFilter()
        
        # Initialize intelligence aggregator
        self.intelligence_aggregator = initialize_aggregator(signal_fusion_engine)
        
        # Initialize TCS integration
        self.tcs_integration = initialize_tcs_integration(self.mt5_adapter, signal_fusion_engine)
        self.tcs_performance_tracker = AdvancedTCSPerformanceTracker(self.mt5_adapter)
        
        # Enable TCS integration in fusion engine
        signal_fusion_engine.set_tcs_integration(self.tcs_integration)
        
        # Track active signals
        self.active_signals: Dict[str, EnhancedActiveSignal] = {}
        
        # Performance tracking
        self.signal_performance = {}
        
        # Background tasks
        self.monitoring_task = None
        
        # Monitored pairs
        self.monitored_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'AUDUSD']
        
    async def start_monitoring(self):
        """Start enhanced monitoring with fusion system"""
        logger.info("Starting fusion-enhanced signal monitoring...")
        
        # Start main monitoring
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        
        # Start account monitoring
        asyncio.create_task(self._monitor_account())
        
        # Start performance tracking
        asyncio.create_task(self._track_performance())
        
        # Start TCS integration monitoring
        await self.tcs_integration.start_monitoring()
        await self.tcs_performance_tracker.start_monitoring()
        
    async def _monitor_loop(self):
        """Main monitoring loop with fusion system"""
        while True:
            try:
                # Check account status
                session_stats = self.account_monitor.get_session_stats()
                
                if not session_stats.get('can_trade'):
                    logger.warning(f"Trading disabled: {session_stats.get('risk_status')}")
                    await asyncio.sleep(60)
                    continue
                
                # Collect intelligence for all pairs
                for pair in self.monitored_pairs:
                    try:
                        # Get fused signal from aggregator
                        fused_signal = await self.intelligence_aggregator.collect_intelligence(pair)
                        
                        if fused_signal:
                            # Apply TCS filtering (already integrated in fusion engine)
                            # Apply live filter
                            if self.live_filter.should_take_signal({
                                'pair': pair,
                                'confidence': fused_signal.confidence
                            }):
                                await self._process_fused_signal(fused_signal)
                            else:
                                logger.info(f"Signal filtered: {pair} ({fused_signal.tier.value})")
                    
                    except Exception as e:
                        logger.error(f"Error processing {pair}: {e}")
                
                # Shorter cycle for fusion system
                await asyncio.sleep(30)  # 30 second cycle
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(60)
    
    async def _process_fused_signal(self, fused_signal: FusedSignal):
        """Process fused signal with tier-based distribution"""
        signal_id = fused_signal.signal_id
        
        # Store enhanced active signal
        self.active_signals[signal_id] = EnhancedActiveSignal(
            id=signal_id,
            fused_signal=fused_signal,
            timestamp=datetime.now(),
            fired_by=set(),
            executions={},
            performance={'sent_to_tiers': {}}
        )
        
        # Distribute based on tiers
        distribution_count = await self._distribute_by_tier(fused_signal)
        
        logger.info(
            f"Fused signal {signal_id}: {fused_signal.pair} {fused_signal.direction} "
            f"@ {fused_signal.confidence:.1f}% ({fused_signal.tier.value}) "
            f"- Distributed to {distribution_count} tiers"
        )
    
    async def _distribute_by_tier(self, signal: FusedSignal) -> int:
        """Distribute signal based on user tiers"""
        tiers_sent = 0
        
        # Check each tier
        for tier in ['apex', 'commander', 'fang', 'nibbler']:
            # Check if tier should receive this signal
            if tier_router.route_signal(signal, tier):
                # Get users in this tier (would query database)
                tier_users = await self._get_tier_users(tier)
                
                for user_id in tier_users:
                    # Check engagement rules
                    should_send, reason = engagement_balancer.should_send_signal(
                        signal, str(user_id), tier
                    )
                    
                    if should_send:
                        await self._send_signal_to_user(signal, user_id, tier)
                        engagement_balancer.record_signal_sent(signal, str(user_id))
                    else:
                        logger.debug(f"Skipped user {user_id}: {reason}")
                
                self.active_signals[signal.signal_id].performance['sent_to_tiers'][tier] = len(tier_users)
                tiers_sent += 1
        
        return tiers_sent
    
    async def _send_signal_to_user(self, signal: FusedSignal, user_id: int, tier: str):
        """Send signal alert to specific user"""
        # Format message based on tier
        message = self._format_signal_message(signal, tier)
        
        # Send via Telegram
        await self.signal_alerts.send_signal_to_user(
            user_id=user_id,
            signal_id=signal.signal_id,
            message=message,
            webapp_url=f"{self.webapp_url}/mission/{signal.signal_id}"
        )
    
    def _format_signal_message(self, signal: FusedSignal, tier: str) -> str:
        """Format signal message based on tier"""
        # Tier-specific emojis
        tier_emojis = {
            ConfidenceTier.SNIPER: "🎯💎",
            ConfidenceTier.PRECISION: "⭐🔥",
            ConfidenceTier.RAPID: "⚡💪",
            ConfidenceTier.TRAINING: "📚🎓"
        }
        
        emoji = tier_emojis.get(signal.tier, "🚀")
        
        # Base message
        message = f"""
{emoji} **{signal.tier.name} SIGNAL** {emoji}

📊 **{signal.pair}** - {signal.direction}
🎯 **Confidence**: {signal.confidence:.0f}%
💡 **Sources**: {len(signal.sources)} intel streams

📍 **Entry**: {signal.entry:.5f}
🛡 **SL**: {signal.sl:.5f}
💎 **TP**: {signal.tp:.5f}

🔍 **Intel Consensus**: {signal.agreement_score:.0f}%
"""
        
        # Add tier-specific content
        if tier in ['apex', 'commander']:
            # Add advanced metrics
            message += f"\n📈 **Fusion Scores**:\n"
            for metric, score in signal.fusion_scores.items():
                if metric != 'weighted_confidence':  # Already shown as confidence
                    message += f"  • {metric.replace('_', ' ').title()}: {score:.0f}%\n"
        
        if signal.tier == ConfidenceTier.SNIPER:
            message += "\n⚡ **ELITE OPPORTUNITY - Maximum Confidence!**"
        elif signal.tier == ConfidenceTier.TRAINING:
            message += "\n📚 **Training Signal - Use smaller position**"
        
        return message
    
    async def handle_fire_action(self, user_id: int, signal_id: str) -> Dict:
        """Enhanced fire action with fusion signal handling"""
        if signal_id not in self.active_signals:
            return {'success': False, 'message': 'Signal expired or not found'}
        
        active_signal = self.active_signals[signal_id]
        fused_signal = active_signal.fused_signal
        
        # Check signal expiry (tier-based)
        expiry_times = {
            ConfidenceTier.SNIPER: timedelta(minutes=15),
            ConfidenceTier.PRECISION: timedelta(minutes=12),
            ConfidenceTier.RAPID: timedelta(minutes=10),
            ConfidenceTier.TRAINING: timedelta(minutes=8)
        }
        
        expiry = expiry_times.get(fused_signal.tier, timedelta(minutes=10))
        
        if datetime.now() - active_signal.timestamp > expiry:
            del self.active_signals[signal_id]
            return {'success': False, 'message': f'Signal expired ({expiry.total_seconds()/60:.0f} min window)'}
        
        # Get user tier
        user_tier = await self._get_user_tier(user_id)
        
        # Verify user can access this signal tier
        tier_access = {
            'nibbler': [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION],
            'fang': [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION, ConfidenceTier.RAPID],
            'commander': [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION, 
                         ConfidenceTier.RAPID, ConfidenceTier.TRAINING],
            'apex': [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION, 
                    ConfidenceTier.RAPID, ConfidenceTier.TRAINING]
        }
        
        if fused_signal.tier not in tier_access.get(user_tier, []):
            return {
                'success': False,
                'message': f'{fused_signal.tier.name} signals not available in {user_tier} tier'
            }
        
        # Check MT5 conditions
        can_trade, reason = self.mt5_adapter.should_take_trade(
            fused_signal.pair, 
            risk_percent=self._get_risk_for_tier(fused_signal.tier)
        )
        
        if not can_trade:
            return {
                'success': False,
                'message': f'Trade blocked: {reason}',
                'reason': reason
            }
        
        # Execute trade with tier-based parameters
        trade_result = await self._execute_fusion_trade(fused_signal, user_tier, user_id)
        
        if trade_result['success']:
            # Record execution
            active_signal.executions[user_id] = trade_result['data']
            active_signal.fired_by.add(user_id)
            
            # Send confirmation
            await self._send_execution_confirmation(
                user_id, fused_signal, trade_result, user_tier
            )
            
            return trade_result
        else:
            # Send failure notification
            await self.signal_alerts.send_user_confirmation(
                user_id,
                f"❌ **TRADE FAILED**\n{trade_result.get('error', 'Unknown error')}"
            )
            
            return trade_result
    
    def _get_risk_for_tier(self, tier: ConfidenceTier) -> float:
        """Get risk percentage based on signal tier"""
        risk_map = {
            ConfidenceTier.SNIPER: 2.5,      # Higher risk for elite signals
            ConfidenceTier.PRECISION: 2.0,   # Standard risk
            ConfidenceTier.RAPID: 1.5,       # Lower risk
            ConfidenceTier.TRAINING: 1.0     # Minimal risk
        }
        return risk_map.get(tier, 2.0)
    
    async def _execute_fusion_trade(self, signal: FusedSignal, 
                                   user_tier: str, user_id: int) -> Dict:
        """Execute trade with fusion signal parameters"""
        # Calculate multi-level TPs for higher tiers
        tp1 = signal.tp
        tp2 = 0
        tp3 = 0
        
        if user_tier in ['commander', 'apex'] and signal.tier in [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION]:
            # Enhanced TP levels for high-confidence signals
            if signal.direction == 'BUY':
                tp_distance = signal.tp - signal.entry
                tp1 = signal.entry + (tp_distance * 0.5)
                tp2 = signal.entry + (tp_distance * 0.8)
                tp3 = signal.tp
            else:  # SELL
                tp_distance = signal.entry - signal.tp
                tp1 = signal.entry - (tp_distance * 0.5)
                tp2 = signal.entry - (tp_distance * 0.8)
                tp3 = signal.tp
        
        # Add signal metadata to comment
        comment = f"BITTEN_{user_tier}_{signal.tier.value}_{signal.confidence:.0f}"
        
        # Execute trade
        trade_result = self.mt5_adapter.execute_trade_with_risk(
            symbol=signal.pair,
            direction=signal.direction,
            risk_percent=self._get_risk_for_tier(signal.tier),
            sl=signal.sl,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            comment=comment,
            break_even=signal.tier in [ConfidenceTier.SNIPER, ConfidenceTier.PRECISION],
            trailing=user_tier == 'apex',
            partial_close=50.0 if user_tier != 'nibbler' else 0
        )
        
        # Track trade execution in TCS system
        if trade_result['success']:
            ticket = trade_result['data'].get('ticket')
            if ticket:
                # Get TCS threshold used
                tcs_threshold = signal.metadata.get('tcs_threshold', 75.0)
                
                # Get market condition from TCS integration
                market_condition = await self.tcs_integration.market_analyzer.get_current_market_condition(signal.pair)
                
                # Track in TCS performance tracker
                await self.tcs_performance_tracker.track_signal_execution(
                    signal=signal,
                    ticket=ticket,
                    tcs_threshold=tcs_threshold,
                    market_condition=market_condition,
                    user_id=user_id,
                    user_tier=user_tier,
                    position_data=trade_result['data']
                )
                
                # Record execution in TCS integration
                await self.tcs_integration.record_signal_execution(signal.signal_id, ticket, user_id)
        
        return trade_result
    
    async def _send_execution_confirmation(self, user_id: int, signal: FusedSignal,
                                         trade_result: Dict, user_tier: str):
        """Send detailed execution confirmation"""
        exec_data = trade_result['data']
        account_after = trade_result.get('account_after', {})
        
        # Tier-specific confirmation
        tier_badge = {
            ConfidenceTier.SNIPER: "🎯💎 SNIPER",
            ConfidenceTier.PRECISION: "⭐🔥 PRECISION",
            ConfidenceTier.RAPID: "⚡💪 RAPID",
            ConfidenceTier.TRAINING: "📚🎓 TRAINING"
        }.get(signal.tier, "🚀")
        
        confirmation_msg = f"""
✅ **{tier_badge} TRADE EXECUTED**

📊 **{signal.pair} {signal.direction}**
🎯 **Confidence**: {signal.confidence:.0f}%
💰 **Size**: {exec_data.get('volume', 'Auto')} lots
🎪 **Entry**: {exec_data.get('price', signal.entry):.5f}
🛡 **SL**: {signal.sl:.5f}
"""
        
        if trade_result.get('tp3', 0) > 0:
            confirmation_msg += f"""
💎 **TP1**: {trade_result['tp1']:.5f} (30%)
💎 **TP2**: {trade_result['tp2']:.5f} (30%)
💎 **TP3**: {trade_result['tp3']:.5f} (40%)
"""
        else:
            confirmation_msg += f"💎 **TP**: {signal.tp:.5f}\n"
        
        confirmation_msg += f"""
📋 **Ticket**: {exec_data.get('ticket', 'N/A')}
💼 **Balance**: ${account_after.get('balance', 0):.2f}

🔍 **Intel Sources**: {len(signal.sources)}
📊 **Agreement**: {signal.agreement_score:.0f}%
"""
        
        await self.signal_alerts.send_user_confirmation(user_id, confirmation_msg)
    
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
                
                # Log performance by tier
                if stats.get('session_pl', 0) != 0:
                    tier_stats = signal_fusion_engine.get_tier_stats()
                    logger.info(
                        f"Session P&L: ${stats['session_pl']:.2f} | "
                        f"Sniper WR: {tier_stats['sniper']['win_rate']:.1%} | "
                        f"Precision WR: {tier_stats['precision']['win_rate']:.1%}"
                    )
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Account monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _track_performance(self):
        """Track signal performance for optimization"""
        while True:
            try:
                # Check closed positions
                closed_positions = self.mt5_adapter.get_closed_positions_since(
                    datetime.now() - timedelta(hours=24)
                )
                
                for position in closed_positions:
                    # Extract signal ID from comment
                    comment = position.get('comment', '')
                    if comment.startswith('BITTEN_'):
                        parts = comment.split('_')
                        if len(parts) >= 4:
                            tier_name = parts[2]
                            
                            # Find matching signal
                            for signal_id, active_signal in list(self.active_signals.items()):
                                if active_signal.fused_signal.tier.value == tier_name:
                                    # Update performance
                                    result = position.get('profit', 0) > 0
                                    signal_fusion_engine.quality_optimizer.update_performance(
                                        active_signal.fused_signal, result
                                    )
                                    
                                    # Clean up old signal
                                    if datetime.now() - active_signal.timestamp > timedelta(hours=24):
                                        del self.active_signals[signal_id]
                                    
                                    break
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Performance tracking error: {e}")
                await asyncio.sleep(600)
    
    async def _get_tier_users(self, tier: str) -> List[int]:
        """Get users in a specific tier (mock implementation)"""
        # In production, this would query the database
        # For now, return mock data
        mock_users = {
            'nibbler': [1001, 1002, 1003],
            'fang': [2001, 2002],
            'commander': [3001],
            'apex': [4001]
        }
        return mock_users.get(tier, [])
    
    async def _get_user_tier(self, user_id: int) -> str:
        """Get user's subscription tier (mock implementation)"""
        # In production, this would query the database
        # For now, return based on user_id range
        if user_id < 2000:
            return 'nibbler'
        elif user_id < 3000:
            return 'fang'
        elif user_id < 4000:
            return 'commander'
        else:
            return 'apex'
    
    async def _send_risk_alert(self, stats: Dict):
        """Send risk alert to users"""
        message = (
            f"⚠️ **RISK ALERT**\n"
            f"Daily P&L: {stats['daily_pl_percent']:.1f}%\n"
            f"Status: {stats['risk_status']}\n"
            f"Trading may be restricted."
        )
        
        await self.signal_alerts.broadcast_message(message)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        tier_stats = signal_fusion_engine.get_tier_stats()
        
        # Calculate active signals by tier
        active_by_tier = {}
        for tier in ConfidenceTier:
            active_by_tier[tier.value] = sum(
                1 for s in self.active_signals.values()
                if s.fused_signal.tier == tier
            )
        
        # Get TCS integration stats
        tcs_stats = self.tcs_integration.get_integration_stats()
        tcs_performance_stats = self.tcs_performance_tracker.get_real_time_stats()
        
        # Get enhanced fusion stats with TCS data
        fusion_stats = signal_fusion_engine.get_tcs_enhanced_stats()
        
        return {
            'tier_performance': tier_stats,
            'active_signals': {
                'total': len(self.active_signals),
                'by_tier': active_by_tier
            },
            'router_stats': {
                tier: tier_router.get_user_stats(tier)
                for tier in ['nibbler', 'fang', 'commander', 'apex']
            },
            'fusion_quality': {
                'min_confidence': min(
                    (s.fused_signal.confidence for s in self.active_signals.values()),
                    default=0
                ),
                'avg_confidence': sum(
                    s.fused_signal.confidence for s in self.active_signals.values()
                ) / len(self.active_signals) if self.active_signals else 0,
                'avg_sources': sum(
                    len(s.fused_signal.sources) for s in self.active_signals.values()
                ) / len(self.active_signals) if self.active_signals else 0
            },
            'tcs_integration': tcs_stats,
            'tcs_performance': tcs_performance_stats,
            'fusion_enhanced': fusion_stats
        }


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize fusion-enhanced flow
    flow = FusionEnhancedSignalFlow(
        bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        webapp_url="https://joinbitten.com"
    )
    
    # Start monitoring
    asyncio.run(flow.start_monitoring())