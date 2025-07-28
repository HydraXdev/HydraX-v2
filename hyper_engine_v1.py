#!/usr/bin/env python3
"""
HYPER ENGINE v1.0 - Six-Layer Intelligence System
Built on v6.0's proven foundation with enhanced intelligence
TARGET: Beat 56.1% win rate → Achieve 65%+ win rate

ARCHITECTURE:
Layer 0 (BASE): v6.0 TCS System (proven 56.1% baseline)
Layer 1: Volume-Price Analysis (VPA) - only trade when volume confirms
Layer 2: Multi-Timeframe Alignment (MTA) - ensure trend agreement
Layer 3: Market Regime Detection (MRD) - avoid choppy markets
Layer 4: Dynamic Position Sizing (DPS) - bigger positions on higher confidence
Layer 5: Smart Exit Management (SEM) - trailing stops and partial profits
Layer 6: Economic Calendar Filter (ECF) - avoid high-impact news

STRATEGY: Keep 95% of winning trades, filter out 30% of losing trades
"""

import sys
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class MarketRegime(Enum):
    TRENDING_STRONG = "trending_strong"
    TRENDING_WEAK = "trending_weak"
    RANGING_TIGHT = "ranging_tight"
    RANGING_WIDE = "ranging_wide"
    BREAKOUT_PENDING = "breakout_pending"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"

class SignalStrength(Enum):
    ULTRA = "ultra"      # 90%+ confidence
    STRONG = "strong"    # 80-89% confidence  
    MODERATE = "moderate" # 70-79% confidence
    WEAK = "weak"        # 60-69% confidence

@dataclass
class HyperSignal:
    """Enhanced signal with six-layer intelligence"""
    symbol: str
    direction: str
    base_tcs: float                    # Original TCS
    enhanced_confidence: float         # After all layers
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    position_size_multiplier: float
    expected_duration_minutes: int
    
    # Intelligence layer scores
    volume_score: float               # Layer 1: VPA
    timeframe_score: float           # Layer 2: MTA
    regime_score: float              # Layer 3: MRD
    sizing_confidence: float         # Layer 4: DPS
    exit_optimization: float         # Layer 5: SEM
    news_safety_score: float         # Layer 6: ECF
    
    signal_strength: SignalStrength
    market_regime: MarketRegime
    reasoning: str
    layer_breakdown: Dict

class HyperEngineV1:
    """Six-Layer Intelligence Trading Engine"""
    
    def __init__(self):
        self.setup_logging()
        
        # Base v6.0 parameters (proven foundation)
        self.apex_base_config = {
            'min_tcs_threshold': 70,        # Start higher for quality
            'session_boosts': {
                'LONDON': 8, 'OVERLAP': 12, 'NEW_YORK': 7, 'SYDNEY_TOKYO': 3
            },
            'risk_base_pct': 0.02          # 2% base risk
        }
        
        # HYPER layer thresholds (designed to filter out losers)
        self.hyper_thresholds = {
            'volume_min_score': 0.6,       # Layer 1: VPA minimum
            'timeframe_min_score': 0.7,    # Layer 2: MTA minimum
            'regime_min_score': 0.5,       # Layer 3: MRD minimum
            'overall_confidence_min': 75,   # Combined minimum confidence
            'max_signals_per_day': 25,     # Quality over quantity
            'news_blackout_hours': 2       # Hours to avoid around news
        }
        
        # Advanced exit management
        self.exit_config = {
            'trailing_stop_activation': 0.5,  # Activate after 50% to TP
            'partial_profit_level': 0.7,      # Take 50% at 70% to TP
            'dynamic_tp_extension': True       # Extend TP in strong trends
        }
        
        self.logger.info("🚀 HYPER ENGINE v1.0 - Six-Layer Intelligence System")
        self.logger.info("🎯 TARGET: Beat v6.0's 56.1% → Achieve 65%+ win rate")
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - HYPER_ENGINE - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/hyper_engine.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('HyperEngine')
    
    def generate_hyper_signal(self, symbol: str, market_data: List[Dict], session: str = "LONDON") -> Optional[HyperSignal]:
        """Generate signal using six-layer intelligence system"""
        try:
            if len(market_data) < 50:  # Need sufficient data for analysis
                return None
            
            # LAYER 0: Generate base v6.0 signal
            base_signal = self._generate_apex_base_signal(symbol, market_data, session)
            if not base_signal:
                return None
            
            # LAYER 1: Volume-Price Analysis (VPA)
            volume_analysis = self._analyze_volume_price_relationship(market_data)
            if volume_analysis['score'] < self.hyper_thresholds['volume_min_score']:
                self.logger.debug(f"Signal filtered by VPA: {volume_analysis['score']:.2f}")
                return None
            
            # LAYER 2: Multi-Timeframe Alignment (MTA)
            timeframe_analysis = self._analyze_multi_timeframe_alignment(market_data, base_signal['direction'])
            if timeframe_analysis['score'] < self.hyper_thresholds['timeframe_min_score']:
                self.logger.debug(f"Signal filtered by MTA: {timeframe_analysis['score']:.2f}")
                return None
            
            # LAYER 3: Market Regime Detection (MRD)
            regime_analysis = self._detect_market_regime(market_data)
            if regime_analysis['score'] < self.hyper_thresholds['regime_min_score']:
                self.logger.debug(f"Signal filtered by MRD: {regime_analysis['score']:.2f}")
                return None
            
            # LAYER 4: Dynamic Position Sizing (DPS)
            sizing_analysis = self._calculate_dynamic_position_sizing(
                base_signal, volume_analysis, timeframe_analysis, regime_analysis
            )
            
            # LAYER 5: Smart Exit Management (SEM)
            exit_optimization = self._optimize_exit_levels(
                base_signal, market_data, regime_analysis
            )
            
            # LAYER 6: Economic Calendar Filter (ECF)
            news_analysis = self._analyze_news_impact_risk(market_data[-1]['timestamp'])
            if news_analysis['score'] < 0.5:  # High news risk
                self.logger.debug(f"Signal filtered by ECF: {news_analysis['score']:.2f}")
                return None
            
            # COMBINE ALL LAYERS: Calculate enhanced confidence
            enhanced_confidence = self._calculate_enhanced_confidence(
                base_signal['tcs'], volume_analysis, timeframe_analysis, 
                regime_analysis, sizing_analysis, news_analysis
            )
            
            if enhanced_confidence < self.hyper_thresholds['overall_confidence_min']:
                self.logger.debug(f"Signal filtered by overall confidence: {enhanced_confidence:.1f}")
                return None
            
            # DETERMINE SIGNAL STRENGTH
            signal_strength = self._classify_signal_strength(enhanced_confidence)
            
            # GENERATE ENHANCED SIGNAL
            return HyperSignal(
                symbol=symbol,
                direction=base_signal['direction'],
                base_tcs=base_signal['tcs'],
                enhanced_confidence=enhanced_confidence,
                entry_price=exit_optimization['entry'],
                stop_loss=exit_optimization['stop_loss'],
                take_profit_1=exit_optimization['tp1'],
                take_profit_2=exit_optimization['tp2'],
                position_size_multiplier=sizing_analysis['multiplier'],
                expected_duration_minutes=base_signal['duration'],
                volume_score=volume_analysis['score'],
                timeframe_score=timeframe_analysis['score'],
                regime_score=regime_analysis['score'],
                sizing_confidence=sizing_analysis['confidence'],
                exit_optimization=exit_optimization['optimization_score'],
                news_safety_score=news_analysis['score'],
                signal_strength=signal_strength,
                market_regime=regime_analysis['regime'],
                reasoning=self._generate_hyper_reasoning(
                    base_signal, volume_analysis, timeframe_analysis, regime_analysis
                ),
                layer_breakdown={
                    'base_tcs': base_signal['tcs'],
                    'volume': volume_analysis['score'],
                    'timeframe': timeframe_analysis['score'],
                    'regime': regime_analysis['score'],
                    'news': news_analysis['score'],
                    'final_confidence': enhanced_confidence
                }
            )
            
        except Exception as e:
            self.logger.error(f"HYPER signal generation error for {symbol}: {e}")
            return None
    
    def _generate_apex_base_signal(self, symbol: str, market_data: List[Dict], session: str) -> Optional[Dict]:
        """Layer 0: Generate base v6.0 style signal"""
        try:
            df = pd.DataFrame(market_data)
            current_price = df['close'].iloc[-1]
            
            # Calculate base TCS (v6.0 style)
            tcs = self._calculate_apex_tcs(df, session)
            
            if tcs < self.apex_base_config['min_tcs_threshold']:
                return None
            
            # Direction analysis
            direction = self._determine_signal_direction(df)
            if not direction:
                return None
            
            # Entry levels
            entry_levels = self._calculate_base_entry_levels(current_price, direction, tcs)
            if not entry_levels:
                return None
            
            return {
                'symbol': symbol,
                'direction': direction,
                'tcs': tcs,
                'entry': entry_levels['entry'],
                'stop_loss': entry_levels['stop_loss'],
                'tp1': entry_levels['tp1'],
                'tp2': entry_levels['tp2'],
                'duration': self._calculate_base_duration(tcs)
            }
            
        except Exception as e:
            self.logger.error(f"Base signal error: {e}")
            return None
    
    def _analyze_volume_price_relationship(self, market_data: List[Dict]) -> Dict:
        """Layer 1: Volume-Price Analysis (VPA)"""
        try:
            df = pd.DataFrame(market_data)
            
            # Volume confirmation score
            recent_volume = df['volume'].tail(5).mean()
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Price movement vs volume relationship
            price_change = abs(df['close'].iloc[-1] - df['close'].iloc[-5])
            price_change_pct = price_change / df['close'].iloc[-5]
            
            # Volume-price divergence analysis
            volume_trend = df['volume'].tail(10).corr(df['close'].tail(10))
            
            # Combined VPA score
            volume_score = 0.0
            
            # Strong volume confirmation
            if volume_ratio > 1.3:
                volume_score += 0.4
            elif volume_ratio > 1.1:
                volume_score += 0.2
            
            # Price-volume alignment
            if abs(volume_trend) > 0.3:  # Good correlation
                volume_score += 0.3
            
            # Breakout volume
            if volume_ratio > 1.5 and price_change_pct > 0.001:
                volume_score += 0.3
            
            return {
                'score': min(1.0, volume_score),
                'volume_ratio': volume_ratio,
                'price_volume_corr': volume_trend,
                'analysis': f"Volume: {volume_ratio:.2f}x avg, Corr: {volume_trend:.2f}"
            }
            
        except Exception as e:
            self.logger.error(f"VPA error: {e}")
            return {'score': 0.5, 'analysis': 'VPA analysis failed'}
    
    def _analyze_multi_timeframe_alignment(self, market_data: List[Dict], direction: str) -> Dict:
        """Layer 2: Multi-Timeframe Alignment (MTA)"""
        try:
            df = pd.DataFrame(market_data)
            
            # Simulate different timeframes using different periods
            short_trend = self._calculate_trend_strength(df.tail(10))   # 5-hour trend
            medium_trend = self._calculate_trend_strength(df.tail(20))  # 10-hour trend
            long_trend = self._calculate_trend_strength(df.tail(40))    # 20-hour trend
            
            # Check alignment with signal direction
            alignment_score = 0.0
            
            if direction == "buy":
                if short_trend > 0:
                    alignment_score += 0.4
                if medium_trend > 0:
                    alignment_score += 0.3
                if long_trend > 0:
                    alignment_score += 0.3
            else:  # sell
                if short_trend < 0:
                    alignment_score += 0.4
                if medium_trend < 0:
                    alignment_score += 0.3
                if long_trend < 0:
                    alignment_score += 0.3
            
            return {
                'score': alignment_score,
                'short_trend': short_trend,
                'medium_trend': medium_trend,
                'long_trend': long_trend,
                'analysis': f"Trends: {short_trend:.3f}/{medium_trend:.3f}/{long_trend:.3f}"
            }
            
        except Exception as e:
            self.logger.error(f"MTA error: {e}")
            return {'score': 0.5, 'analysis': 'MTA analysis failed'}
    
    def _detect_market_regime(self, market_data: List[Dict]) -> Dict:
        """Layer 3: Market Regime Detection (MRD)"""
        try:
            df = pd.DataFrame(market_data)
            
            # Calculate regime indicators
            volatility = df['close'].rolling(20).std().iloc[-1]
            avg_volatility = df['close'].rolling(50).std().mean()
            vol_ratio = volatility / avg_volatility if avg_volatility > 0 else 1.0
            
            # Trend strength
            trend_strength = abs(self._calculate_trend_strength(df.tail(20)))
            
            # Range analysis
            high_low_range = (df['high'].tail(20).max() - df['low'].tail(20).min())
            avg_range = df['close'].tail(20).mean() * 0.02  # 2% typical range
            range_ratio = high_low_range / avg_range if avg_range > 0 else 1.0
            
            # Determine regime
            if vol_ratio > 2.0:
                regime = MarketRegime.HIGH_VOLATILITY
                score = 0.3  # Avoid high volatility
            elif vol_ratio < 0.5:
                regime = MarketRegime.LOW_VOLATILITY
                score = 0.4  # Avoid low volatility
            elif trend_strength > 0.002:
                regime = MarketRegime.TRENDING_STRONG
                score = 0.9  # Love strong trends
            elif trend_strength > 0.001:
                regime = MarketRegime.TRENDING_WEAK
                score = 0.7  # Good for trending
            elif range_ratio < 0.5:
                regime = MarketRegime.RANGING_TIGHT
                score = 0.4  # Avoid tight ranges
            elif range_ratio > 2.0:
                regime = MarketRegime.RANGING_WIDE
                score = 0.5  # OK for wide ranges
            else:
                regime = MarketRegime.BREAKOUT_PENDING
                score = 0.8  # Good for breakouts
            
            return {
                'score': score,
                'regime': regime,
                'volatility_ratio': vol_ratio,
                'trend_strength': trend_strength,
                'range_ratio': range_ratio,
                'analysis': f"Regime: {regime.value}, Vol: {vol_ratio:.2f}, Trend: {trend_strength:.3f}"
            }
            
        except Exception as e:
            self.logger.error(f"MRD error: {e}")
            return {'score': 0.5, 'regime': MarketRegime.RANGING_WIDE, 'analysis': 'MRD analysis failed'}
    
    def _calculate_dynamic_position_sizing(self, base_signal: Dict, volume_analysis: Dict, 
                                         timeframe_analysis: Dict, regime_analysis: Dict) -> Dict:
        """Layer 4: Dynamic Position Sizing (DPS)"""
        try:
            # Base position size
            base_multiplier = 1.0
            
            # Adjust based on confidence layers
            confidence_multiplier = 1.0
            
            # Volume boost
            if volume_analysis['score'] > 0.8:
                confidence_multiplier += 0.3
            elif volume_analysis['score'] > 0.6:
                confidence_multiplier += 0.1
            
            # Timeframe alignment boost
            if timeframe_analysis['score'] > 0.8:
                confidence_multiplier += 0.3
            elif timeframe_analysis['score'] > 0.7:
                confidence_multiplier += 0.1
            
            # Regime boost
            if regime_analysis['regime'] in [MarketRegime.TRENDING_STRONG, MarketRegime.BREAKOUT_PENDING]:
                confidence_multiplier += 0.2
            
            # TCS boost
            if base_signal['tcs'] > 85:
                confidence_multiplier += 0.3
            elif base_signal['tcs'] > 80:
                confidence_multiplier += 0.2
            
            # Final multiplier (cap at 2.0x for safety)
            final_multiplier = min(2.0, base_multiplier * confidence_multiplier)
            
            return {
                'multiplier': final_multiplier,
                'confidence': confidence_multiplier,
                'analysis': f"Size: {final_multiplier:.2f}x (confidence: {confidence_multiplier:.2f})"
            }
            
        except Exception as e:
            self.logger.error(f"DPS error: {e}")
            return {'multiplier': 1.0, 'confidence': 1.0, 'analysis': 'DPS analysis failed'}
    
    def _optimize_exit_levels(self, base_signal: Dict, market_data: List[Dict], regime_analysis: Dict) -> Dict:
        """Layer 5: Smart Exit Management (SEM)"""
        try:
            df = pd.DataFrame(market_data)
            current_price = base_signal['entry']
            direction = base_signal['direction']
            
            # Base levels from entry = current_price
            base_stop = base_signal['stop_loss']
            base_tp1 = base_signal['tp1']
            
            # Calculate ATR for dynamic levels
            df['tr'] = np.maximum(df['high'] - df['low'], 
                                 np.maximum(abs(df['high'] - df['close'].shift(1)),
                                           abs(df['low'] - df['close'].shift(1))))
            atr = df['tr'].rolling(14).mean().iloc[-1]
            
            # Optimize based on market regime
            optimization_factor = 1.0
            
            if regime_analysis['regime'] == MarketRegime.TRENDING_STRONG:
                optimization_factor = 1.3  # Wider targets in strong trends
            elif regime_analysis['regime'] == MarketRegime.HIGH_VOLATILITY:
                optimization_factor = 0.8  # Tighter targets in volatility
            
            # Optimized levels
            if direction == "buy":
                optimized_stop = entry - (atr * 1.5 * optimization_factor)
                optimized_tp1 = entry + (atr * 2.5 * optimization_factor)
                optimized_tp2 = entry + (atr * 4.0 * optimization_factor)
            else:
                optimized_stop = entry + (atr * 1.5 * optimization_factor)
                optimized_tp1 = entry - (atr * 2.5 * optimization_factor)
                optimized_tp2 = entry - (atr * 4.0 * optimization_factor)
            
            # Use better of base or optimized levels
            final_stop = optimized_stop
            final_tp1 = optimized_tp1
            final_tp2 = optimized_tp2
            
            return {
                'entry': entry,
                'stop_loss': final_stop,
                'tp1': final_tp1,
                'tp2': final_tp2,
                'optimization_score': optimization_factor,
                'analysis': f"SEM optimized: {optimization_factor:.2f}x factor"
            }
            
        except Exception as e:
            self.logger.error(f"SEM error: {e}")
            return {
                'entry': base_signal['entry'],
                'stop_loss': base_signal['stop_loss'],
                'tp1': base_signal['tp1'],
                'tp2': base_signal['tp2'],
                'optimization_score': 1.0,
                'analysis': 'SEM optimization failed'
            }
    
    def _analyze_news_impact_risk(self, timestamp: int) -> Dict:
        """Layer 6: Economic Calendar Filter (ECF)"""
        try:
            # Simplified news risk analysis
            # In production, this would integrate with economic calendar API
            
            current_time = datetime.fromtimestamp(timestamp)
            hour = current_time.hour
            minute = current_time.minute
            
            # High-risk times (major news release times)
            high_risk_hours = [8, 10, 14, 16, 20]  # Common news times
            
            risk_score = 1.0  # Default safe
            
            # Check if within high-risk hour
            if hour in high_risk_hours:
                # Higher risk in first 30 minutes of hour
                if minute < 30:
                    risk_score = 0.3  # High risk
                else:
                    risk_score = 0.6  # Medium risk
            
            # Friday afternoon risk
            if current_time.weekday() == 4 and hour >= 15:  # Friday 3pm+
                risk_score *= 0.7
            
            return {
                'score': risk_score,
                'risk_level': 'high' if risk_score < 0.5 else 'medium' if risk_score < 0.8 else 'low',
                'analysis': f"News risk: {risk_score:.2f} at {hour:02d}:{minute:02d}"
            }
            
        except Exception as e:
            self.logger.error(f"ECF error: {e}")
            return {'score': 0.8, 'analysis': 'ECF analysis failed'}
    
    def _calculate_enhanced_confidence(self, base_tcs: float, volume_analysis: Dict, 
                                     timeframe_analysis: Dict, regime_analysis: Dict,
                                     sizing_analysis: Dict, news_analysis: Dict) -> float:
        """Combine all layer scores into enhanced confidence"""
        try:
            # Weighted combination of all factors
            enhanced_confidence = (
                base_tcs * 0.4 +                           # Base TCS (40%)
                volume_analysis['score'] * 15 +            # Volume confirmation (15%)
                timeframe_analysis['score'] * 15 +         # Timeframe alignment (15%)
                regime_analysis['score'] * 15 +            # Market regime (15%)
                news_analysis['score'] * 10 +              # News safety (10%)
                (sizing_analysis['confidence'] - 1) * 5   # Sizing confidence bonus (5%)
            )
            
            return min(95, max(50, enhanced_confidence))
            
        except Exception as e:
            self.logger.error(f"Enhanced confidence calculation error: {e}")
            return base_tcs
    
    def _classify_signal_strength(self, confidence: float) -> SignalStrength:
        """Classify signal strength based on enhanced confidence"""
        if confidence >= 90:
            return SignalStrength.ULTRA
        elif confidence >= 80:
            return SignalStrength.STRONG
        elif confidence >= 70:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _generate_hyper_reasoning(self, base_signal: Dict, volume_analysis: Dict,
                                 timeframe_analysis: Dict, regime_analysis: Dict) -> str:
        """Generate detailed reasoning for signal"""
        reasoning_parts = [
            f"TCS: {base_signal['tcs']:.0f}",
            f"Vol: {volume_analysis['score']:.2f}",
            f"MTA: {timeframe_analysis['score']:.2f}",
            f"Regime: {regime_analysis['regime'].value}",
            f"Direction: {base_signal['direction'].upper()}"
        ]
        return " | ".join(reasoning_parts)
    
    # Helper methods
    def _calculate_apex_tcs(self, df: pd.DataFrame, session: str) -> float:
        """Calculate -style TCS score"""
        tcs = 60.0  # Base
        
        # Moving averages
        df['sma_10'] = df['close'].rolling(10).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        
        current_price = df['close'].iloc[-1]
        sma_10 = df['sma_10'].iloc[-1]
        sma_20 = df['sma_20'].iloc[-1]
        
        # Trend analysis
        if current_price > sma_10 > sma_20:
            tcs += 12
        elif current_price < sma_10 < sma_20:
            tcs += 12
        elif current_price > sma_10 or current_price > sma_20:
            tcs += 6
        
        # Momentum
        momentum = (current_price - df['close'].iloc[-5]) / current_price
        tcs += min(8, abs(momentum) * 8000)
        
        # Session boost
        session_boost = self.apex_base_config['session_boosts'].get(session, 0)
        tcs += session_boost
        
        # Volatility
        volatility = df['close'].rolling(10).std().iloc[-1] / current_price
        if 0.001 <= volatility <= 0.005:
            tcs += 5
        
        return min(95, max(45, tcs + np.random.uniform(-2, 2)))
    
    def _determine_signal_direction(self, df: pd.DataFrame) -> Optional[str]:
        """Determine signal direction"""
        current_price = df['close'].iloc[-1]
        sma_10 = df['close'].rolling(10).mean().iloc[-1]
        momentum = (current_price - df['close'].iloc[-3]) / current_price
        
        if momentum > 0.0001 and current_price > sma_10:
            return "buy"
        elif momentum < -0.0001 and current_price < sma_10:
            return "sell"
        elif abs(momentum) > 0.0005:  # Strong momentum
            return "buy" if momentum > 0 else "sell"
        
        return None
    
    def _calculate_base_entry_levels(self, current_price: float, direction: str, tcs: float) -> Optional[Dict]:
        """Calculate base entry levels"""
        try:
            # Risk based on TCS
            if tcs >= 85:
                risk_pct = 0.018
                rr_ratio = 2.5
            elif tcs >= 75:
                risk_pct = 0.020
                rr_ratio = 2.0
            else:
                risk_pct = 0.025
                rr_ratio = 1.8
            
            if direction == "buy":
                entry = current_price
                stop_loss = current_price * (1 - risk_pct)
                risk = entry - stop_loss
                tp1 = entry + risk * rr_ratio
                tp2 = entry + risk * (rr_ratio + 0.5)
            else:
                entry = current_price
                stop_loss = current_price * (1 + risk_pct)
                risk = stop_loss - entry
                tp1 = entry - risk * rr_ratio
                tp2 = entry - risk * (rr_ratio + 0.5)
            
            if risk <= 0:
                return None
            
            return {
                'entry': entry,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2
            }
            
        except Exception as e:
            self.logger.error(f"Entry levels error: {e}")
            return None
    
    def _calculate_base_duration(self, tcs: float) -> int:
        """Calculate expected duration"""
        if tcs >= 85:
            return 60  # 1 hour
        elif tcs >= 75:
            return 45  # 45 minutes
        else:
            return 30  # 30 minutes
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength"""
        try:
            if len(df) < 2:
                return 0.0
            
            prices = df['close'].values
            x = np.arange(len(prices))
            slope, _ = np.polyfit(x, prices, 1)
            return slope / prices[-1]  # Normalized slope
            
        except Exception:
            return 0.0

def test_hyper_engine():
    """Test the HYPER engine"""
    print("🚀 Testing HYPER ENGINE v1.0")
    print("=" * 50)
    
    engine = HyperEngineV1()
    
    # Create realistic test data
    market_data = []
    base_price = 1.0850
    
    for i in range(60):  # 30 hours of data
        trend = 0.00008 * np.sin(i * 0.1)
        noise = np.random.normal(0, 0.00005)
        base_price += trend + noise
        
        market_data.append({
            'timestamp': int(datetime.now().timestamp()) + i * 1800,  # 30-min intervals
            'open': base_price - np.random.uniform(0, 0.00002),
            'high': base_price + np.random.uniform(0.00003, 0.00012),
            'low': base_price - np.random.uniform(0.00003, 0.00012),
            'close': base_price,
            'volume': np.random.randint(800, 2000)
        })
    
    # Test signal generation
    signal = engine.generate_hyper_signal("EURUSD", market_data, "LONDON")
    
    if signal:
        print("✅ HYPER signal generated!")
        print(f"   Symbol: {signal.symbol}")
        print(f"   Direction: {signal.direction.upper()}")
        print(f"   Base TCS: {signal.base_tcs:.1f}")
        print(f"   Enhanced Confidence: {signal.enhanced_confidence:.1f}")
        print(f"   Signal Strength: {signal.signal_strength.value.upper()}")
        print(f"   Entry: {signal.entry_price:.5f}")
        print(f"   Stop Loss: {signal.stop_loss:.5f}")
        print(f"   Take Profit 1: {signal.take_profit_1:.5f}")
        print(f"   Position Size: {signal.position_size_multiplier:.2f}x")
        print(f"   Market Regime: {signal.market_regime.value}")
        print(f"   Duration: {signal.expected_duration_minutes} minutes")
        print(f"   Reasoning: {signal.reasoning}")
        print("\n   Layer Breakdown:")
        for layer, score in signal.layer_breakdown.items():
            print(f"     {layer}: {score:.2f}")
        return True
    else:
        print("❌ No HYPER signal generated")
        return False

if __name__ == "__main__":
    success = test_hyper_engine()
    exit(0 if success else 1)