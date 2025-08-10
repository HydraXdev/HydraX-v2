#!/usr/bin/env python3
"""
Signal Vitality Engine - Market-Based Signal Decay System
Calculates real-time signal health based on market conditions, not just time
Educational component teaches users WHY signals degrade
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import redis
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VitalityMetrics:
    """Complete vitality assessment with educational context"""
    vitality_score: float  # 0-100
    status: str  # FRESH, VALID, AGING, EXPIRED
    icon: str  # 🟢🟡🟠🔴
    color: str  # Hex color for UI
    
    # Market drift metrics
    price_drift_pips: float
    spread_ratio: float  # Current/original
    volume_ratio: float  # Current/original
    
    # Execution adjustments
    adjusted_entry: float
    adjusted_sl: float
    adjusted_tp: float
    expected_slippage_pips: float
    
    # Risk recalculation
    original_risk_dollars: float
    current_risk_dollars: float
    lot_size_adjustment: float
    
    # Educational content
    degradation_reasons: List[str]
    execution_warnings: List[str]
    educational_tip: str
    
    # XP and rewards
    xp_multiplier: float
    can_execute: bool
    

class SignalVitalityEngine:
    """
    Calculates signal vitality based on real market conditions
    Provides educational insights about signal degradation
    """
    
    def __init__(self):
        try:
            self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.cache_ttl = 30  # 30 second cache
        except:
            self.redis = None
            logger.warning("Redis not available, using in-memory cache")
            self.memory_cache = {}
            
        # Educational content library
        self.education_library = {
            'price_drift': {
                'minor': "📚 Small price movements (1-5 pips) are normal market fluctuations.",
                'moderate': "⚠️ Price has moved significantly. The original entry may no longer be optimal.",
                'major': "❌ Major price movement detected. The setup conditions have changed.",
                'explanation': "When price moves away from the original entry, you're essentially entering a different trade than analyzed."
            },
            'spread': {
                'normal': "✅ Spread is normal. Good execution conditions.",
                'elevated': "⚠️ Spread has widened. This increases your trading costs.",
                'extreme': "❌ Spread is very wide. Each trade costs significantly more.",
                'explanation': "Spread is the difference between buy/sell prices. Wider spreads mean you start with a bigger loss."
            },
            'volume': {
                'liquid': "✅ Good liquidity. Your order should fill at expected price.",
                'moderate': "⚠️ Liquidity dropping. Possible slippage on larger orders.",
                'thin': "❌ Low liquidity. High slippage risk, prices may jump.",
                'explanation': "Volume represents how many traders are active. Low volume means fewer people to take the other side of your trade."
            },
            'timing': {
                'session': "Different trading sessions have different characteristics. London/NY are most liquid.",
                'news': "News events can cause sudden volatility and spreads to widen dramatically.",
                'weekend': "Weekend gaps can invalidate setups that looked good on Friday.",
                'explanation': "Timing affects everything from spread costs to probability of success."
            }
        }
    
    def calculate_vitality(self, mission_id: str, user_balance: float = 10000) -> VitalityMetrics:
        """
        Calculate comprehensive signal vitality with educational context
        """
        # Check cache first
        cached = self._get_cached_vitality(mission_id)
        if cached:
            logger.info(f"Returning cached vitality for {mission_id}")
            return cached
            
        # Load original mission
        try:
            with open(f'/root/HydraX-v2/missions/{mission_id}.json', 'r') as f:
                original = json.load(f)
        except FileNotFoundError:
            logger.error(f"Mission {mission_id} not found")
            return self._create_expired_vitality()
            
        # Get current market data
        current_market = self._get_current_market_data(original.get('symbol', 'EURUSD'))
        
        # Calculate all vitality components
        price_metrics = self._calculate_price_drift(original, current_market)
        spread_metrics = self._calculate_spread_change(original, current_market)
        volume_metrics = self._calculate_volume_change(original, current_market)
        
        # Calculate composite vitality score
        vitality_score = self._calculate_composite_score(
            price_metrics, spread_metrics, volume_metrics
        )
        
        # Determine status and visual indicators
        status, icon, color, xp_mult = self._determine_status(vitality_score)
        
        # Calculate adjusted trading parameters
        adjusted_params = self._calculate_adjusted_parameters(
            original, current_market, price_metrics['drift_pips']
        )
        
        # Calculate risk in dollars
        risk_dollars = self._calculate_risk_dollars(
            original, adjusted_params, user_balance
        )
        
        # Generate educational content
        degradation_reasons = self._analyze_degradation_reasons(
            price_metrics, spread_metrics, volume_metrics
        )
        
        warnings = self._generate_execution_warnings(
            vitality_score, price_metrics, spread_metrics
        )
        
        educational_tip = self._select_educational_tip(
            degradation_reasons, vitality_score
        )
        
        # Create vitality metrics object
        metrics = VitalityMetrics(
            vitality_score=vitality_score,
            status=status,
            icon=icon,
            color=color,
            price_drift_pips=price_metrics['drift_pips'],
            spread_ratio=spread_metrics['ratio'],
            volume_ratio=volume_metrics['ratio'],
            adjusted_entry=adjusted_params['entry'],
            adjusted_sl=adjusted_params['sl'],
            adjusted_tp=adjusted_params['tp'],
            expected_slippage_pips=adjusted_params['slippage'],
            original_risk_dollars=risk_dollars['original'],
            current_risk_dollars=risk_dollars['current'],
            lot_size_adjustment=risk_dollars['lot_adjustment'],
            degradation_reasons=degradation_reasons,
            execution_warnings=warnings,
            educational_tip=educational_tip,
            xp_multiplier=xp_mult,
            can_execute=vitality_score >= 20
        )
        
        # Cache the result
        self._cache_vitality(mission_id, metrics)
        
        return metrics
    
    def _get_current_market_data(self, symbol: str) -> Dict:
        """Get current market data from market_data_receiver"""
        try:
            import requests
            response = requests.get(
                f'http://localhost:8001/market-data/venom-feed?symbol={symbol}',
                timeout=1
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'price': data.get('bid', 0),
                    'spread': data.get('spread', 0),
                    'volume': data.get('volume', 0),
                    'timestamp': datetime.now()
                }
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            
        # Fallback data
        return {
            'price': 0,
            'spread': 2.0,
            'volume': 1000,
            'timestamp': datetime.now()
        }
    
    def _calculate_price_drift(self, original: Dict, current: Dict) -> Dict:
        """Calculate how far price has moved from entry"""
        original_price = original.get('entry_price', 0) or original.get('signal', {}).get('entry_price', 0)
        current_price = current.get('price', original_price)
        
        drift = abs(current_price - original_price)
        drift_pips = drift * 10000 if 'JPY' not in original.get('symbol', '') else drift * 100
        
        # Educational classification
        if drift_pips < 5:
            classification = 'minor'
            impact = 0.95  # 95% vitality retained
        elif drift_pips < 15:
            classification = 'moderate'
            impact = 0.70  # 70% vitality retained
        else:
            classification = 'major'
            impact = 0.30  # 30% vitality retained
            
        return {
            'drift': drift,
            'drift_pips': drift_pips,
            'classification': classification,
            'impact': impact,
            'education': self.education_library['price_drift'][classification]
        }
    
    def _calculate_spread_change(self, original: Dict, current: Dict) -> Dict:
        """Calculate spread deterioration"""
        original_spread = original.get('spread_at_generation', 1.5)
        current_spread = current.get('spread', original_spread)
        
        ratio = current_spread / original_spread if original_spread > 0 else 1
        
        if ratio <= 1.5:
            classification = 'normal'
            impact = 1.0
        elif ratio <= 2.5:
            classification = 'elevated'
            impact = 0.8
        else:
            classification = 'extreme'
            impact = 0.5
            
        return {
            'original': original_spread,
            'current': current_spread,
            'ratio': ratio,
            'classification': classification,
            'impact': impact,
            'education': self.education_library['spread'][classification]
        }
    
    def _calculate_volume_change(self, original: Dict, current: Dict) -> Dict:
        """Calculate volume/liquidity change"""
        original_volume = original.get('volume_at_generation', 1000) or 1000
        current_volume = current.get('volume', original_volume)
        
        ratio = current_volume / original_volume if original_volume > 0 else 1
        
        if ratio >= 0.7:
            classification = 'liquid'
            impact = 1.0
        elif ratio >= 0.4:
            classification = 'moderate'
            impact = 0.85
        else:
            classification = 'thin'
            impact = 0.6
            
        return {
            'original': original_volume,
            'current': current_volume,
            'ratio': ratio,
            'classification': classification,
            'impact': impact,
            'education': self.education_library['volume'][classification]
        }
    
    def _calculate_composite_score(self, price: Dict, spread: Dict, volume: Dict) -> float:
        """Calculate overall vitality score with weighted factors"""
        # Weighted average: Price drift is most important
        weights = {
            'price': 0.5,   # 50% weight
            'spread': 0.3,  # 30% weight
            'volume': 0.2   # 20% weight
        }
        
        score = (
            price['impact'] * weights['price'] +
            spread['impact'] * weights['spread'] +
            volume['impact'] * weights['volume']
        ) * 100
        
        return min(100, max(0, score))
    
    def _determine_status(self, score: float) -> Tuple[str, str, str, float]:
        """Determine status, icon, color, and XP multiplier based on score"""
        if score >= 80:
            return "FRESH", "🟢", "#00ff00", 2.0
        elif score >= 50:
            return "VALID", "🟡", "#ffff00", 1.5
        elif score >= 20:
            return "AGING", "🟠", "#ff8800", 1.0
        else:
            return "EXPIRED", "🔴", "#ff0000", 0.0
    
    def _calculate_adjusted_parameters(self, original: Dict, current: Dict, drift_pips: float) -> Dict:
        """Calculate adjusted entry, SL, TP based on current conditions"""
        signal = original.get('signal', original)
        original_entry = signal.get('entry_price', 0)
        original_sl = signal.get('stop_loss', 0)
        original_tp = signal.get('take_profit', 0)
        direction = signal.get('direction', 'BUY').upper()
        
        current_price = current.get('price', original_entry)
        
        # If price drifted significantly, adjust entry
        if drift_pips > 5:
            # Enter at current market + small buffer
            buffer = 0.0002 if direction == 'BUY' else -0.0002
            adjusted_entry = current_price + buffer
            
            # Keep same pip distances for SL/TP
            sl_distance = abs(original_entry - original_sl)
            tp_distance = abs(original_tp - original_entry)
            
            if direction == 'BUY':
                adjusted_sl = adjusted_entry - sl_distance
                adjusted_tp = adjusted_entry + tp_distance
            else:
                adjusted_sl = adjusted_entry + sl_distance
                adjusted_tp = adjusted_entry - tp_distance
        else:
            # Minor drift, keep original levels
            adjusted_entry = original_entry
            adjusted_sl = original_sl
            adjusted_tp = original_tp
        
        # Calculate expected slippage
        slippage = current.get('spread', 2) * 0.5  # Half spread as slippage estimate
        
        return {
            'entry': round(adjusted_entry, 5),
            'sl': round(adjusted_sl, 5),
            'tp': round(adjusted_tp, 5),
            'slippage': round(slippage, 1)
        }
    
    def _calculate_risk_dollars(self, original: Dict, adjusted: Dict, balance: float) -> Dict:
        """Calculate risk in dollar amounts"""
        pip_value = 10  # $10 per pip per standard lot
        
        # Original risk
        signal = original.get('signal', original)
        original_sl_pips = abs(signal.get('entry_price', 0) - signal.get('stop_loss', 0)) * 10000
        original_lot = min(0.5, (balance * 0.02) / (original_sl_pips * pip_value)) if original_sl_pips > 0 else 0.1
        original_risk = original_sl_pips * pip_value * original_lot
        
        # Current risk with adjusted levels
        current_sl_pips = abs(adjusted['entry'] - adjusted['sl']) * 10000
        current_lot = min(0.5, (balance * 0.02) / (current_sl_pips * pip_value)) if current_sl_pips > 0 else 0.1
        current_risk = current_sl_pips * pip_value * current_lot
        
        return {
            'original': round(original_risk, 2),
            'current': round(current_risk, 2),
            'lot_adjustment': round(current_lot / original_lot, 2) if original_lot > 0 else 1.0
        }
    
    def _analyze_degradation_reasons(self, price: Dict, spread: Dict, volume: Dict) -> List[str]:
        """Generate list of reasons why signal degraded"""
        reasons = []
        
        if price['drift_pips'] > 5:
            reasons.append(f"Price moved {price['drift_pips']:.1f} pips from entry")
        
        if spread['ratio'] > 1.5:
            reasons.append(f"Spread increased {(spread['ratio']-1)*100:.0f}%")
        
        if volume['ratio'] < 0.7:
            reasons.append(f"Volume decreased {(1-volume['ratio'])*100:.0f}%")
            
        if not reasons:
            reasons.append("Signal conditions remain favorable")
            
        return reasons
    
    def _generate_execution_warnings(self, score: float, price: Dict, spread: Dict) -> List[str]:
        """Generate warnings about execution risks"""
        warnings = []
        
        if score < 30:
            warnings.append("⛔ Signal expired - DO NOT EXECUTE")
        elif score < 50:
            warnings.append("⚠️ Signal significantly degraded - high risk")
        
        if price['drift_pips'] > 10:
            warnings.append(f"⚠️ Entry will be adjusted by {price['drift_pips']:.0f} pips")
        
        if spread['ratio'] > 2:
            warnings.append(f"⚠️ High spread will cost extra ${spread['current']*10:.0f}")
        
        return warnings
    
    def _select_educational_tip(self, reasons: List[str], score: float) -> str:
        """Select most relevant educational tip based on degradation"""
        if score < 30:
            return "💡 When signals expire, the original analysis no longer applies. Wait for fresh setups."
        
        if any('Price moved' in r for r in reasons):
            return self.education_library['price_drift']['explanation']
        
        if any('Spread increased' in r for r in reasons):
            return self.education_library['spread']['explanation']
            
        if any('Volume decreased' in r for r in reasons):
            return self.education_library['volume']['explanation']
        
        return "💡 Fresh signals have the highest probability of success. Execute quickly for best results."
    
    def _get_cached_vitality(self, mission_id: str) -> Optional[VitalityMetrics]:
        """Get cached vitality if available and fresh"""
        cache_key = f"vitality:{mission_id}"
        
        if self.redis:
            try:
                cached_json = self.redis.get(cache_key)
                if cached_json:
                    data = json.loads(cached_json)
                    # Reconstruct VitalityMetrics from JSON
                    return VitalityMetrics(**data)
            except Exception as e:
                logger.error(f"Cache retrieval error: {e}")
        else:
            # Memory cache fallback
            if cache_key in self.memory_cache:
                cached_time, metrics = self.memory_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return metrics
        
        return None
    
    def _cache_vitality(self, mission_id: str, metrics: VitalityMetrics):
        """Cache vitality metrics"""
        cache_key = f"vitality:{mission_id}"
        
        if self.redis:
            try:
                # Convert to dict for JSON serialization
                metrics_dict = {
                    'vitality_score': metrics.vitality_score,
                    'status': metrics.status,
                    'icon': metrics.icon,
                    'color': metrics.color,
                    'price_drift_pips': metrics.price_drift_pips,
                    'spread_ratio': metrics.spread_ratio,
                    'volume_ratio': metrics.volume_ratio,
                    'adjusted_entry': metrics.adjusted_entry,
                    'adjusted_sl': metrics.adjusted_sl,
                    'adjusted_tp': metrics.adjusted_tp,
                    'expected_slippage_pips': metrics.expected_slippage_pips,
                    'original_risk_dollars': metrics.original_risk_dollars,
                    'current_risk_dollars': metrics.current_risk_dollars,
                    'lot_size_adjustment': metrics.lot_size_adjustment,
                    'degradation_reasons': metrics.degradation_reasons,
                    'execution_warnings': metrics.execution_warnings,
                    'educational_tip': metrics.educational_tip,
                    'xp_multiplier': metrics.xp_multiplier,
                    'can_execute': metrics.can_execute
                }
                self.redis.setex(cache_key, self.cache_ttl, json.dumps(metrics_dict))
            except Exception as e:
                logger.error(f"Cache storage error: {e}")
        else:
            # Memory cache fallback
            self.memory_cache[cache_key] = (time.time(), metrics)
    
    def _create_expired_vitality(self) -> VitalityMetrics:
        """Create an expired vitality response for missing missions"""
        return VitalityMetrics(
            vitality_score=0,
            status="EXPIRED",
            icon="🔴",
            color="#ff0000",
            price_drift_pips=999,
            spread_ratio=999,
            volume_ratio=0,
            adjusted_entry=0,
            adjusted_sl=0,
            adjusted_tp=0,
            expected_slippage_pips=0,
            original_risk_dollars=0,
            current_risk_dollars=0,
            lot_size_adjustment=0,
            degradation_reasons=["Mission not found or expired"],
            execution_warnings=["Cannot execute - mission data unavailable"],
            educational_tip="Expired signals cannot be executed. Wait for fresh opportunities.",
            xp_multiplier=0,
            can_execute=False
        )


# Singleton instance
_vitality_engine = None

def get_vitality_engine() -> SignalVitalityEngine:
    """Get singleton instance of vitality engine"""
    global _vitality_engine
    if _vitality_engine is None:
        _vitality_engine = SignalVitalityEngine()
    return _vitality_engine