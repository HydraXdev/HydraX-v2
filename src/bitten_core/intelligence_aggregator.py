"""
BITTEN Intelligence Aggregator
Collects and normalizes signals from all intelligence sources
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import numpy as np

from .signal_fusion import IntelSource, SignalFusionEngine, FusedSignal
from .market_analyzer import MarketAnalyzer, MarketStructure
from .intel_bot_personalities import bot_personalities, BotPersonality
from .strategies.london_breakout import LondonBreakoutStrategy
from .strategies.support_resistance import SupportResistanceStrategy
from .strategies.momentum_continuation import MomentumContinuationStrategy
from .strategies.mean_reversion import MeanReversionStrategy

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """Technical analysis intelligence source"""
    
    def __init__(self):
        self.strategies = {
            'london_breakout': LondonBreakoutStrategy(),
            'support_resistance': SupportResistanceStrategy(),
            'momentum_continuation': MomentumContinuationStrategy(),
            'mean_reversion': MeanReversionStrategy()
        }
        
    async def analyze(self, pair: str, market_data: Dict) -> Optional[IntelSource]:
        """Run technical analysis and return intel source"""
        try:
            # Run all strategies and aggregate
            signals = []
            confidences = []
            
            for name, strategy in self.strategies.items():
                try:
                    signal = strategy.analyze(market_data)
                    if signal and signal.get('signal') in ['BUY', 'SELL']:
                        signals.append(signal)
                        confidences.append(signal.get('confidence', 70))
                except Exception as e:
                    logger.error(f"Strategy {name} error: {e}")
            
            if not signals:
                return None
            
            # Determine consensus
            buy_count = sum(1 for s in signals if s['signal'] == 'BUY')
            sell_count = sum(1 for s in signals if s['signal'] == 'SELL')
            
            if buy_count == sell_count:
                return None  # No consensus
            
            direction = 'BUY' if buy_count > sell_count else 'SELL'
            
            # Calculate confidence based on agreement
            agreement_ratio = max(buy_count, sell_count) / len(signals)
            base_confidence = np.mean(confidences)
            final_confidence = base_confidence * (0.5 + agreement_ratio * 0.5)
            
            # Get levels from majority signals
            majority_signals = [s for s in signals if s['signal'] == direction]
            entry = np.mean([s.get('entry', 0) for s in majority_signals if s.get('entry')])
            sl = np.mean([s.get('sl', 0) for s in majority_signals if s.get('sl')])
            tp = np.mean([s.get('tp', 0) for s in majority_signals if s.get('tp')])
            
            return IntelSource(
                source_id='technical_analyzer',
                source_type='technical',
                signal=direction,
                confidence=final_confidence,
                weight=0.4,  # High weight for technical
                metadata={
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'strategies_agree': len(majority_signals),
                    'total_strategies': len(signals)
                }
            )
            
        except Exception as e:
            logger.error(f"Technical analyzer error: {e}")
            return None

class SentimentAnalyzer:
    """Market sentiment intelligence source"""
    
    def __init__(self):
        self.sentiment_indicators = {
            'volatility': {'threshold': 50, 'weight': 0.3},
            'volume': {'threshold': 1.2, 'weight': 0.3},
            'spread': {'threshold': 3, 'weight': 0.2},
            'momentum': {'threshold': 0.6, 'weight': 0.2}
        }
        
    async def analyze(self, pair: str, market_data: Dict) -> Optional[IntelSource]:
        """Analyze market sentiment"""
        try:
            sentiment_scores = {}
            
            # Volatility sentiment
            atr = market_data.get('atr', 30)
            if atr < 20:
                sentiment_scores['volatility'] = ('NEUTRAL', 60)
            elif atr > 50:
                sentiment_scores['volatility'] = ('SELL', 70)  # High volatility = caution
            else:
                sentiment_scores['volatility'] = ('BUY', 65)
            
            # Volume sentiment
            volume_ratio = market_data.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                sentiment_scores['volume'] = ('BUY', 75)  # High volume = interest
            elif volume_ratio < 0.7:
                sentiment_scores['volume'] = ('SELL', 65)
            else:
                sentiment_scores['volume'] = ('NEUTRAL', 60)
            
            # Spread sentiment
            spread = market_data.get('spread', 2.0)
            normal_spread = market_data.get('normal_spread', 2.0)
            spread_ratio = spread / normal_spread if normal_spread > 0 else 1.0
            
            if spread_ratio > 1.5:
                sentiment_scores['spread'] = ('SELL', 70)  # Wide spread = low liquidity
            else:
                sentiment_scores['spread'] = ('BUY', 65)
            
            # Momentum sentiment (simple price action)
            prices = market_data.get('price_history', [])
            if len(prices) >= 20:
                recent_prices = prices[-20:]
                momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                if abs(momentum) > 0.002:  # 0.2% move
                    direction = 'BUY' if momentum > 0 else 'SELL'
                    confidence = min(80, 60 + abs(momentum) * 10000)
                    sentiment_scores['momentum'] = (direction, confidence)
                else:
                    sentiment_scores['momentum'] = ('NEUTRAL', 50)
            
            # Aggregate sentiment
            buy_score = 0
            sell_score = 0
            total_weight = 0
            
            for indicator, (signal, conf) in sentiment_scores.items():
                weight = self.sentiment_indicators[indicator]['weight']
                if signal == 'BUY':
                    buy_score += conf * weight
                elif signal == 'SELL':
                    sell_score += conf * weight
                total_weight += weight
            
            if buy_score == sell_score:
                return None
            
            direction = 'BUY' if buy_score > sell_score else 'SELL'
            confidence = max(buy_score, sell_score) / total_weight
            
            return IntelSource(
                source_id='sentiment_analyzer',
                source_type='sentiment',
                signal=direction,
                confidence=confidence,
                weight=0.2,
                metadata={
                    'indicators': sentiment_scores,
                    'buy_pressure': buy_score / total_weight,
                    'sell_pressure': sell_score / total_weight
                }
            )
            
        except Exception as e:
            logger.error(f"Sentiment analyzer error: {e}")
            return None

class FundamentalAnalyzer:
    """Fundamental analysis intelligence source"""
    
    def __init__(self):
        self.session_biases = {
            'LONDON': {'pairs': ['GBPUSD', 'EURUSD', 'EURGBP'], 'bias': 'volatile'},
            'NEW_YORK': {'pairs': ['EURUSD', 'GBPUSD', 'USDJPY'], 'bias': 'trending'},
            'TOKYO': {'pairs': ['USDJPY', 'AUDJPY', 'EURJPY'], 'bias': 'ranging'},
            'OVERLAP': {'pairs': 'all', 'bias': 'high_volume'}
        }
        
    async def analyze(self, pair: str, market_data: Dict) -> Optional[IntelSource]:
        """Analyze fundamental factors"""
        try:
            scores = {}
            
            # Session analysis
            session = market_data.get('session', 'DEAD_ZONE')
            session_data = self.session_biases.get(session, {})
            
            if session != 'DEAD_ZONE':
                if session_data['pairs'] == 'all' or pair in session_data['pairs']:
                    scores['session'] = ('BUY', 70)  # Good session for this pair
                else:
                    scores['session'] = ('NEUTRAL', 50)
            else:
                scores['session'] = ('SELL', 60)  # Poor liquidity
            
            # Day of week analysis
            dow = datetime.now().weekday()
            if dow in [1, 2, 3]:  # Tuesday, Wednesday, Thursday
                scores['dow'] = ('BUY', 65)
            elif dow == 4:  # Friday
                scores['dow'] = ('SELL', 65)  # Friday caution
            else:
                scores['dow'] = ('NEUTRAL', 50)
            
            # Time of day analysis
            hour = datetime.now().hour
            if 8 <= hour <= 16:  # Main trading hours
                scores['time'] = ('BUY', 70)
            elif hour < 6 or hour > 22:
                scores['time'] = ('SELL', 60)
            else:
                scores['time'] = ('NEUTRAL', 55)
            
            # Economic calendar (simplified - would connect to real data)
            # For now, assume no major news
            scores['news'] = ('NEUTRAL', 50)
            
            # Aggregate fundamental view
            buy_score = sum(conf for signal, conf in scores.values() if signal == 'BUY')
            sell_score = sum(conf for signal, conf in scores.values() if signal == 'SELL')
            neutral_score = sum(conf for signal, conf in scores.values() if signal == 'NEUTRAL')
            
            total_score = buy_score + sell_score + neutral_score
            
            if total_score == 0:
                return None
            
            # Determine direction
            if buy_score > sell_score * 1.2:  # Require 20% more for signal
                direction = 'BUY'
                confidence = (buy_score / total_score) * 100
            elif sell_score > buy_score * 1.2:
                direction = 'SELL'
                confidence = (sell_score / total_score) * 100
            else:
                return None  # No clear fundamental bias
            
            return IntelSource(
                source_id='fundamental_analyzer',
                source_type='fundamental',
                signal=direction,
                confidence=confidence,
                weight=0.2,
                metadata={
                    'factors': scores,
                    'session': session,
                    'day_of_week': dow
                }
            )
            
        except Exception as e:
            logger.error(f"Fundamental analyzer error: {e}")
            return None

class AIBotAnalyzer:
    """AI bot personality intelligence source"""
    
    def __init__(self):
        self.bot_specialties = {
            BotPersonality.OVERWATCH: {'weight': 0.3, 'style': 'tactical'},
            BotPersonality.ANALYST: {'weight': 0.4, 'style': 'analytical'},
            BotPersonality.RISK: {'weight': 0.3, 'style': 'conservative'}
        }
        
    async def analyze(self, pair: str, market_data: Dict) -> Optional[IntelSource]:
        """Get AI bot analysis"""
        try:
            bot_signals = []
            
            # Query each specialist bot
            market_context = {
                'pair': pair,
                'trend': market_data.get('trend_direction', 'neutral'),
                'volatility': market_data.get('atr', 30),
                'near_level': market_data.get('near_key_level', False)
            }
            
            # Overwatch tactical analysis
            if market_context['trend'] == 'up' and not market_context['near_level']:
                bot_signals.append({
                    'bot': BotPersonality.OVERWATCH,
                    'signal': 'BUY',
                    'confidence': 75,
                    'reason': 'Clear trend with room to run'
                })
            elif market_context['trend'] == 'down' and not market_context['near_level']:
                bot_signals.append({
                    'bot': BotPersonality.OVERWATCH,
                    'signal': 'SELL',
                    'confidence': 75,
                    'reason': 'Downtrend continuation opportunity'
                })
            
            # Analyst data-driven view
            if market_context['volatility'] < 25:
                bot_signals.append({
                    'bot': BotPersonality.ANALYST,
                    'signal': 'NEUTRAL',
                    'confidence': 60,
                    'reason': 'Low volatility environment'
                })
            elif market_context['volatility'] > 50:
                # High volatility - look for mean reversion
                current_signal = 'SELL' if market_context['trend'] == 'up' else 'BUY'
                bot_signals.append({
                    'bot': BotPersonality.ANALYST,
                    'signal': current_signal,
                    'confidence': 65,
                    'reason': 'Volatility mean reversion setup'
                })
            
            # Risk officer conservative view
            if market_context['near_level']:
                bot_signals.append({
                    'bot': BotPersonality.RISK,
                    'signal': 'NEUTRAL',
                    'confidence': 70,
                    'reason': 'Too close to key level'
                })
            elif market_context['volatility'] > 40:
                bot_signals.append({
                    'bot': BotPersonality.RISK,
                    'signal': 'NEUTRAL',
                    'confidence': 65,
                    'reason': 'Volatility too high for safe entry'
                })
            
            if not bot_signals:
                return None
            
            # Aggregate bot opinions
            buy_weighted = sum(
                s['confidence'] * self.bot_specialties[s['bot']]['weight']
                for s in bot_signals if s['signal'] == 'BUY'
            )
            sell_weighted = sum(
                s['confidence'] * self.bot_specialties[s['bot']]['weight']
                for s in bot_signals if s['signal'] == 'SELL'
            )
            
            if buy_weighted == sell_weighted:
                return None
            
            direction = 'BUY' if buy_weighted > sell_weighted else 'SELL'
            confidence = max(buy_weighted, sell_weighted)
            
            return IntelSource(
                source_id='ai_bot_analyzer',
                source_type='ai_bot',
                signal=direction,
                confidence=confidence,
                weight=0.2,
                metadata={
                    'bot_opinions': bot_signals,
                    'consensus_strength': len([s for s in bot_signals if s['signal'] == direction]) / len(bot_signals)
                }
            )
            
        except Exception as e:
            logger.error(f"AI bot analyzer error: {e}")
            return None

class IntelligenceAggregator:
    """
    Main aggregator that collects from all intelligence sources
    """
    
    def __init__(self, fusion_engine: SignalFusionEngine):
        self.fusion_engine = fusion_engine
        
        # Initialize all analyzers
        self.technical = TechnicalAnalyzer()
        self.sentiment = SentimentAnalyzer()
        self.fundamental = FundamentalAnalyzer()
        self.ai_bot = AIBotAnalyzer()
        
        # Market analyzer for data
        self.market_analyzer = MarketAnalyzer()
        
    async def collect_intelligence(self, pair: str) -> Optional[FusedSignal]:
        """
        Collect intelligence from all sources and fuse into signal
        """
        try:
            # Get current market data
            market_data = await self._get_market_data(pair)
            if not market_data:
                logger.warning(f"No market data available for {pair}")
                return None
            
            # Collect from all sources in parallel
            tasks = [
                self.technical.analyze(pair, market_data),
                self.sentiment.analyze(pair, market_data),
                self.fundamental.analyze(pair, market_data),
                self.ai_bot.analyze(pair, market_data)
            ]
            
            sources = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors and None results
            valid_sources = []
            for source in sources:
                if isinstance(source, IntelSource):
                    valid_sources.append(source)
                elif isinstance(source, Exception):
                    logger.error(f"Source error: {source}")
            
            if len(valid_sources) < 3:
                logger.info(f"Insufficient sources for {pair}: {len(valid_sources)}")
                return None
            
            # Fuse signals
            fused_signal = self.fusion_engine.fuse_signals(valid_sources, pair)
            
            return fused_signal
            
        except Exception as e:
            logger.error(f"Intelligence aggregation error: {e}")
            return None
    
    async def _get_market_data(self, pair: str) -> Optional[Dict]:
        """Get current market data for analysis"""
        try:
            # In production, this would fetch real-time data
            # For now, return mock data structure
            market_conditions = self.market_analyzer.get_market_conditions()
            
            # Add mock price history
            market_conditions['price_history'] = [
                1.1000 + i * 0.0001 for i in range(50)
            ]
            
            return market_conditions
            
        except Exception as e:
            logger.error(f"Market data error: {e}")
            return None
    
    async def continuous_monitoring(self, pairs: List[str], interval: int = 60):
        """
        Continuously monitor pairs and generate signals
        """
        logger.info(f"Starting continuous monitoring for {pairs}")
        
        while True:
            try:
                for pair in pairs:
                    signal = await self.collect_intelligence(pair)
                    if signal:
                        logger.info(
                            f"Generated {signal.tier.value} signal for {pair} "
                            f"with {signal.confidence:.1f}% confidence"
                        )
                        
                        # Signal would be sent to distribution system here
                        await self._distribute_signal(signal)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def _distribute_signal(self, signal: FusedSignal):
        """Distribute signal through the system"""
        # This would connect to the signal distribution system
        # For now, just log
        logger.info(f"Signal ready for distribution: {signal.signal_id}")

# Global instance
intelligence_aggregator = None

def initialize_aggregator(fusion_engine: SignalFusionEngine):
    """Initialize the global aggregator"""
    global intelligence_aggregator
    intelligence_aggregator = IntelligenceAggregator(fusion_engine)
    return intelligence_aggregator