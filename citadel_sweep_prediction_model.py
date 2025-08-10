#!/usr/bin/env python3
"""
CITADEL Sweep Prediction Model - Predict liquidity sweeps before they happen

Uses machine learning and market microstructure analysis to predict when
institutional traders will sweep liquidity levels, providing early warning
for high-probability reversal setups.
"""

import json
import time
import redis
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pickle
import os
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CitadelSweepPrediction')

@dataclass
class LiquidityLevel:
    """Represents a potential liquidity level"""
    price: float
    level_type: str  # 'swing_high', 'swing_low', 'round_number', 'pivot'
    strength: float  # 0-100, strength of the level
    age_minutes: float
    touch_count: int
    volume_accumulation: float
    distance_from_current: float
    symbol: str
    detected_at: float

@dataclass
class SweepEvent:
    """Historical sweep event for training"""
    symbol: str
    sweep_price: float
    sweep_direction: str  # 'bullish_sweep', 'bearish_sweep'
    pre_sweep_features: Dict
    post_sweep_outcome: str  # 'reversal_success', 'reversal_failed', 'continuation'
    timestamp: float
    reversal_pips: Optional[float]
    time_to_reversal: Optional[float]

@dataclass
class SweepPrediction:
    """Sweep prediction output"""
    symbol: str
    predicted_sweep_price: float
    sweep_direction: str
    probability: float
    confidence_level: str  # 'HIGH', 'MEDIUM', 'LOW'
    time_horizon: str  # 'immediate', 'short_term', 'medium_term'
    supporting_factors: List[str]
    risk_factors: List[str]
    prediction_timestamp: float

class CitadelSweepPredictionModel:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.truth_log_path = '/root/HydraX-v2/truth_log.jsonl'
        self.model_path = '/root/HydraX-v2/models/sweep_prediction_model.pkl'
        self.scaler_path = '/root/HydraX-v2/models/sweep_prediction_scaler.pkl'
        
        # Model components
        self.sweep_classifier = None
        self.feature_scaler = None
        self.feature_importance = {}
        
        # Market data storage
        self.price_history = defaultdict(lambda: deque(maxlen=200))  # 200 ticks
        self.liquidity_levels = defaultdict(list)  # Current liquidity levels per symbol
        self.volume_profile = defaultdict(lambda: deque(maxlen=100))
        self.order_flow_imbalance = defaultdict(float)
        
        # Sweep detection parameters
        self.sweep_detection_pips = {
            'EURUSD': 3, 'GBPUSD': 4, 'USDJPY': 3, 'USDCAD': 3,
            'EURJPY': 4, 'GBPJPY': 5, 'XAUUSD': 8
        }
        
        self.min_level_strength = 25  # Minimum strength for a level to be considered
        self.max_level_age = 4 * 60 * 60  # 4 hours maximum age for levels
        
        # Load or create models
        self.load_or_create_models()
        
        logger.info("🛡️ CITADEL Sweep Prediction Model initialized")

    def load_or_create_models(self):
        """Load existing models or create new ones"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                with open(self.model_path, 'rb') as f:
                    self.sweep_classifier = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.feature_scaler = pickle.load(f)
                logger.info("✅ Loaded existing sweep prediction models")
            else:
                self.create_initial_models()
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.create_initial_models()

    def create_initial_models(self):
        """Create initial ML models"""
        # Initialize with default models
        self.sweep_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        self.feature_scaler = StandardScaler()
        
        # Train on historical data if available
        self.train_models_from_history()
        
        logger.info("✅ Created initial sweep prediction models")

    def update_market_data(self, tick_data: Dict):
        """Update internal market data structures with new tick"""
        symbol = tick_data.get('symbol')
        if not symbol:
            return
            
        current_price = (tick_data.get('bid', 0) + tick_data.get('ask', 0)) / 2
        volume = tick_data.get('volume', 1)
        timestamp = tick_data.get('timestamp', time.time())
        
        # Update price history
        self.price_history[symbol].append({
            'price': current_price,
            'volume': volume,
            'timestamp': timestamp,
            'bid': tick_data.get('bid', 0),
            'ask': tick_data.get('ask', 0)
        })
        
        # Update volume profile
        self.volume_profile[symbol].append({
            'price': current_price,
            'volume': volume,
            'timestamp': timestamp
        })
        
        # Detect and update liquidity levels
        self.update_liquidity_levels(symbol)
        
        # Update order flow imbalance (simplified)
        self.update_order_flow_imbalance(symbol, tick_data)

    def update_liquidity_levels(self, symbol: str):
        """Detect and update liquidity levels for a symbol"""
        if len(self.price_history[symbol]) < 50:
            return
            
        prices = [tick['price'] for tick in list(self.price_history[symbol])[-50:]]
        timestamps = [tick['timestamp'] for tick in list(self.price_history[symbol])[-50:]]
        volumes = [tick['volume'] for tick in list(self.price_history[symbol])[-50:]]
        current_price = prices[-1]
        current_time = time.time()
        
        # Clean old levels
        self.liquidity_levels[symbol] = [
            level for level in self.liquidity_levels[symbol]
            if current_time - level.detected_at < self.max_level_age
        ]
        
        # Detect swing highs and lows
        new_levels = []
        
        # Swing high detection (local maxima)
        for i in range(2, len(prices) - 2):
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and 
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                
                # Calculate level strength
                strength = self.calculate_level_strength(symbol, prices[i], 'swing_high', volumes[i])
                
                if strength > self.min_level_strength:
                    level = LiquidityLevel(
                        price=prices[i],
                        level_type='swing_high',
                        strength=strength,
                        age_minutes=(current_time - timestamps[i]) / 60,
                        touch_count=1,
                        volume_accumulation=volumes[i],
                        distance_from_current=abs(prices[i] - current_price),
                        symbol=symbol,
                        detected_at=timestamps[i]
                    )
                    new_levels.append(level)
        
        # Swing low detection (local minima)
        for i in range(2, len(prices) - 2):
            if (prices[i] < prices[i-1] and prices[i] < prices[i-2] and 
                prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                
                strength = self.calculate_level_strength(symbol, prices[i], 'swing_low', volumes[i])
                
                if strength > self.min_level_strength:
                    level = LiquidityLevel(
                        price=prices[i],
                        level_type='swing_low',
                        strength=strength,
                        age_minutes=(current_time - timestamps[i]) / 60,
                        touch_count=1,
                        volume_accumulation=volumes[i],
                        distance_from_current=abs(prices[i] - current_price),
                        symbol=symbol,
                        detected_at=timestamps[i]
                    )
                    new_levels.append(level)
        
        # Round number levels (psychological levels)
        round_levels = self.detect_round_number_levels(symbol, current_price)
        new_levels.extend(round_levels)
        
        # Merge with existing levels (avoid duplicates)
        for new_level in new_levels:
            # Check if similar level already exists
            duplicate = False
            for existing_level in self.liquidity_levels[symbol]:
                if (abs(new_level.price - existing_level.price) < self.get_pip_size(symbol) * 2 and
                    new_level.level_type == existing_level.level_type):
                    # Update existing level
                    existing_level.touch_count += 1
                    existing_level.volume_accumulation += new_level.volume_accumulation
                    existing_level.age_minutes = (current_time - existing_level.detected_at) / 60
                    duplicate = True
                    break
            
            if not duplicate:
                self.liquidity_levels[symbol].append(new_level)
        
        # Sort by strength
        self.liquidity_levels[symbol].sort(key=lambda x: x.strength, reverse=True)
        
        # Keep only top levels
        self.liquidity_levels[symbol] = self.liquidity_levels[symbol][:20]

    def calculate_level_strength(self, symbol: str, price: float, level_type: str, volume: float) -> float:
        """Calculate the strength of a liquidity level"""
        if len(self.price_history[symbol]) < 20:
            return 0
        
        recent_prices = [tick['price'] for tick in list(self.price_history[symbol])[-20:]]
        recent_volumes = [tick['volume'] for tick in list(self.price_history[symbol])[-20:]]
        
        pip_size = self.get_pip_size(symbol)
        strength = 0
        
        # Base strength from volume
        avg_volume = np.mean(recent_volumes)
        if avg_volume > 0:
            volume_strength = min(50, (volume / avg_volume) * 25)
            strength += volume_strength
        
        # Touch count strength (how many times price approached this level)
        touch_count = sum(1 for p in recent_prices if abs(p - price) < pip_size * 2)
        strength += min(25, touch_count * 5)
        
        # Rejection strength (how far price moved away after touching)
        max_rejection = 0
        for i, p in enumerate(recent_prices):
            if abs(p - price) < pip_size * 2:
                # Look for rejection in next few prices
                for j in range(i + 1, min(i + 5, len(recent_prices))):
                    if level_type == 'swing_high' and recent_prices[j] < p:
                        rejection = abs(recent_prices[j] - p) / pip_size
                        max_rejection = max(max_rejection, rejection)
                    elif level_type == 'swing_low' and recent_prices[j] > p:
                        rejection = abs(recent_prices[j] - p) / pip_size
                        max_rejection = max(max_rejection, rejection)
        
        strength += min(25, max_rejection * 2)
        
        return min(100, strength)

    def detect_round_number_levels(self, symbol: str, current_price: float) -> List[LiquidityLevel]:
        """Detect psychological round number levels"""
        levels = []
        pip_size = self.get_pip_size(symbol)
        
        # Round to different decimal places based on symbol
        if 'JPY' in symbol:
            # For JPY pairs, round to whole numbers and half numbers
            round_levels = [
                round(current_price),
                round(current_price) + 0.5,
                round(current_price) - 0.5,
                round(current_price) + 1.0,
                round(current_price) - 1.0
            ]
        else:
            # For other pairs, round to 4 decimal places with focus on 00, 25, 50, 75
            base = int(current_price * 10000) / 10000
            round_levels = []
            for offset in [-0.0100, -0.0075, -0.0050, -0.0025, 0, 0.0025, 0.0050, 0.0075, 0.0100]:
                round_levels.append(base + offset)
        
        for level_price in round_levels:
            if abs(level_price - current_price) > pip_size * 5:  # Only consider distant levels
                # Determine level type based on position relative to current price
                level_type = 'round_resistance' if level_price > current_price else 'round_support'
                
                strength = 30 + (abs(level_price - current_price) / pip_size)  # Strength increases with distance
                strength = min(60, strength)  # Cap at 60 for round numbers
                
                level = LiquidityLevel(
                    price=level_price,
                    level_type=level_type,
                    strength=strength,
                    age_minutes=0,  # Round numbers are always "fresh"
                    touch_count=0,
                    volume_accumulation=0,
                    distance_from_current=abs(level_price - current_price),
                    symbol=symbol,
                    detected_at=time.time()
                )
                levels.append(level)
        
        return levels

    def update_order_flow_imbalance(self, symbol: str, tick_data: Dict):
        """Update order flow imbalance indicator (simplified)"""
        bid = tick_data.get('bid', 0)
        ask = tick_data.get('ask', 0)
        volume = tick_data.get('volume', 1)
        
        if bid and ask and volume:
            spread = ask - bid
            mid_price = (bid + ask) / 2
            
            # Simple imbalance calculation based on spread and volume
            # In a real implementation, this would use order book data
            if spread > 0:
                imbalance = volume * ((ask - mid_price) - (mid_price - bid)) / spread
                
                # Smooth the imbalance with exponential moving average
                alpha = 0.1
                current_imbalance = self.order_flow_imbalance.get(symbol, 0)
                self.order_flow_imbalance[symbol] = current_imbalance * (1 - alpha) + imbalance * alpha

    def get_pip_size(self, symbol: str) -> float:
        """Get pip size for a symbol"""
        if 'JPY' in symbol:
            return 0.01
        else:
            return 0.0001

    def extract_sweep_features(self, symbol: str) -> Dict:
        """Extract features for sweep prediction"""
        if len(self.price_history[symbol]) < 50:
            return {}
        
        recent_ticks = list(self.price_history[symbol])[-50:]
        prices = [tick['price'] for tick in recent_ticks]
        volumes = [tick['volume'] for tick in recent_ticks]
        current_price = prices[-1]
        
        # Get top liquidity levels
        top_levels = sorted(self.liquidity_levels[symbol], key=lambda x: x.strength, reverse=True)[:10]
        
        features = {
            # Price momentum features
            'price_momentum_5': (prices[-1] - prices[-5]) if len(prices) >= 5 else 0,
            'price_momentum_10': (prices[-1] - prices[-10]) if len(prices) >= 10 else 0,
            'price_momentum_20': (prices[-1] - prices[-20]) if len(prices) >= 20 else 0,
            
            # Volatility features
            'recent_volatility': np.std(prices[-20:]) if len(prices) >= 20 else 0,
            'volatility_ratio': (np.std(prices[-10:]) / np.std(prices[-20:])) if len(prices) >= 20 and np.std(prices[-20:]) > 0 else 1,
            
            # Volume features
            'volume_avg': np.mean(volumes),
            'volume_recent': np.mean(volumes[-5:]),
            'volume_ratio': (np.mean(volumes[-5:]) / np.mean(volumes)) if np.mean(volumes) > 0 else 1,
            
            # Order flow features
            'order_flow_imbalance': self.order_flow_imbalance.get(symbol, 0),
            
            # Liquidity level proximity features
            'distance_to_nearest_resistance': float('inf'),
            'distance_to_nearest_support': float('inf'),
            'nearest_resistance_strength': 0,
            'nearest_support_strength': 0,
            'levels_above_count': 0,
            'levels_below_count': 0,
            'avg_level_strength_above': 0,
            'avg_level_strength_below': 0,
        }
        
        # Calculate liquidity level features
        levels_above = [level for level in top_levels if level.price > current_price]
        levels_below = [level for level in top_levels if level.price < current_price]
        
        if levels_above:
            nearest_resistance = min(levels_above, key=lambda x: x.distance_from_current)
            features['distance_to_nearest_resistance'] = nearest_resistance.distance_from_current
            features['nearest_resistance_strength'] = nearest_resistance.strength
            features['levels_above_count'] = len(levels_above)
            features['avg_level_strength_above'] = np.mean([level.strength for level in levels_above])
        
        if levels_below:
            nearest_support = min(levels_below, key=lambda x: x.distance_from_current)
            features['distance_to_nearest_support'] = nearest_support.distance_from_current
            features['nearest_support_strength'] = nearest_support.strength
            features['levels_below_count'] = len(levels_below)
            features['avg_level_strength_below'] = np.mean([level.strength for level in levels_below])
        
        # Market structure features
        recent_highs = [prices[i] for i in range(2, len(prices)-2) 
                       if prices[i] > prices[i-1] and prices[i] > prices[i-2] and 
                          prices[i] > prices[i+1] and prices[i] > prices[i+2]]
        recent_lows = [prices[i] for i in range(2, len(prices)-2) 
                      if prices[i] < prices[i-1] and prices[i] < prices[i-2] and 
                         prices[i] < prices[i+1] and prices[i] < prices[i+2]]
        
        features['higher_highs_count'] = len([h for h in recent_highs if h > current_price])
        features['lower_lows_count'] = len([l for l in recent_lows if l < current_price])
        features['recent_high_low_ratio'] = len(recent_highs) / max(1, len(recent_lows))
        
        # Time-based features (session impact)
        current_hour = datetime.now().hour
        features['london_session'] = 1 if 8 <= current_hour <= 16 else 0
        features['ny_session'] = 1 if 13 <= current_hour <= 21 else 0
        features['overlap_session'] = 1 if 13 <= current_hour <= 16 else 0
        
        return features

    def predict_sweep(self, symbol: str) -> Optional[SweepPrediction]:
        """Predict potential liquidity sweep for a symbol"""
        if not self.sweep_classifier or len(self.liquidity_levels[symbol]) < 3:
            return None
        
        features = self.extract_sweep_features(symbol)
        if not features:
            return None
        
        try:
            # Prepare feature array
            feature_names = [
                'price_momentum_5', 'price_momentum_10', 'price_momentum_20',
                'recent_volatility', 'volatility_ratio',
                'volume_avg', 'volume_recent', 'volume_ratio',
                'order_flow_imbalance',
                'distance_to_nearest_resistance', 'distance_to_nearest_support',
                'nearest_resistance_strength', 'nearest_support_strength',
                'levels_above_count', 'levels_below_count',
                'avg_level_strength_above', 'avg_level_strength_below',
                'higher_highs_count', 'lower_lows_count', 'recent_high_low_ratio',
                'london_session', 'ny_session', 'overlap_session'
            ]
            
            feature_array = []
            for name in feature_names:
                value = features.get(name, 0)
                # Handle infinite values
                if value == float('inf') or value == float('-inf'):
                    value = 0
                feature_array.append(value)
            
            feature_array = np.array(feature_array).reshape(1, -1)
            
            # Scale features
            feature_array_scaled = self.feature_scaler.transform(feature_array)
            
            # Predict
            probabilities = self.sweep_classifier.predict_proba(feature_array_scaled)[0]
            prediction_class = self.sweep_classifier.predict(feature_array_scaled)[0]
            
            if prediction_class == 0:  # No sweep predicted
                return None
            
            # Determine sweep direction and target
            if prediction_class == 1:  # Bullish sweep (sweep below support then reverse up)
                sweep_direction = 'bullish_sweep'
                target_levels = [level for level in self.liquidity_levels[symbol] 
                               if level.price < features.get('distance_to_nearest_support', float('inf'))]
            else:  # Bearish sweep (sweep above resistance then reverse down)
                sweep_direction = 'bearish_sweep' 
                target_levels = [level for level in self.liquidity_levels[symbol]
                               if level.price > features.get('distance_to_nearest_resistance', float('inf'))]
            
            if not target_levels:
                return None
            
            # Select most likely target level
            target_level = max(target_levels, key=lambda x: x.strength)
            probability = max(probabilities)
            
            # Generate supporting and risk factors
            supporting_factors, risk_factors = self.analyze_prediction_factors(symbol, features, sweep_direction)
            
            # Determine confidence level
            confidence_level = 'HIGH' if probability > 0.75 else 'MEDIUM' if probability > 0.6 else 'LOW'
            
            # Determine time horizon
            time_horizon = self.estimate_time_horizon(symbol, features, sweep_direction)
            
            prediction = SweepPrediction(
                symbol=symbol,
                predicted_sweep_price=target_level.price,
                sweep_direction=sweep_direction,
                probability=round(probability * 100, 1),
                confidence_level=confidence_level,
                time_horizon=time_horizon,
                supporting_factors=supporting_factors,
                risk_factors=risk_factors,
                prediction_timestamp=time.time()
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting sweep for {symbol}: {e}")
            return None

    def analyze_prediction_factors(self, symbol: str, features: Dict, sweep_direction: str) -> Tuple[List[str], List[str]]:
        """Analyze factors supporting and opposing the prediction"""
        supporting_factors = []
        risk_factors = []
        
        # Volume analysis
        volume_ratio = features.get('volume_ratio', 1)
        if volume_ratio > 1.2:
            supporting_factors.append(f"High volume activity ({volume_ratio:.1f}x average)")
        elif volume_ratio < 0.8:
            risk_factors.append(f"Low volume ({volume_ratio:.1f}x average)")
        
        # Momentum analysis
        momentum_10 = features.get('price_momentum_10', 0)
        if sweep_direction == 'bullish_sweep' and momentum_10 < 0:
            supporting_factors.append("Bearish momentum approaching support")
        elif sweep_direction == 'bearish_sweep' and momentum_10 > 0:
            supporting_factors.append("Bullish momentum approaching resistance")
        else:
            risk_factors.append("Momentum not aligned with sweep direction")
        
        # Volatility analysis
        volatility_ratio = features.get('volatility_ratio', 1)
        if volatility_ratio > 1.3:
            supporting_factors.append("Increasing volatility suggests breakout attempt")
        elif volatility_ratio < 0.7:
            risk_factors.append("Decreasing volatility may limit sweep potential")
        
        # Level strength analysis
        if sweep_direction == 'bullish_sweep':
            support_strength = features.get('nearest_support_strength', 0)
            if support_strength > 60:
                supporting_factors.append(f"Strong support level ({support_strength:.0f} strength)")
            elif support_strength < 30:
                risk_factors.append("Weak support may not generate significant liquidity")
        else:
            resistance_strength = features.get('nearest_resistance_strength', 0)
            if resistance_strength > 60:
                supporting_factors.append(f"Strong resistance level ({resistance_strength:.0f} strength)")
            elif resistance_strength < 30:
                risk_factors.append("Weak resistance may not generate significant liquidity")
        
        # Session analysis
        if features.get('overlap_session', 0):
            supporting_factors.append("London/NY overlap provides high institutional activity")
        elif not (features.get('london_session', 0) or features.get('ny_session', 0)):
            risk_factors.append("Asian session typically has lower institutional activity")
        
        # Order flow analysis
        order_flow = features.get('order_flow_imbalance', 0)
        if abs(order_flow) > 10:
            if (sweep_direction == 'bullish_sweep' and order_flow < -10) or \
               (sweep_direction == 'bearish_sweep' and order_flow > 10):
                supporting_factors.append("Order flow imbalance supports sweep direction")
            else:
                risk_factors.append("Order flow imbalance opposes prediction")
        
        return supporting_factors, risk_factors

    def estimate_time_horizon(self, symbol: str, features: Dict, sweep_direction: str) -> str:
        """Estimate time horizon for the predicted sweep"""
        
        # Factors that influence timing
        volatility_ratio = features.get('volatility_ratio', 1)
        volume_ratio = features.get('volume_ratio', 1)
        momentum = abs(features.get('price_momentum_5', 0))
        
        # Calculate urgency score
        urgency_score = 0
        
        if volatility_ratio > 1.5:
            urgency_score += 2
        elif volatility_ratio > 1.2:
            urgency_score += 1
        
        if volume_ratio > 1.5:
            urgency_score += 2
        elif volume_ratio > 1.2:
            urgency_score += 1
        
        if momentum > self.get_pip_size(symbol) * 5:
            urgency_score += 1
        
        # Session factor
        if features.get('overlap_session', 0):
            urgency_score += 1
        
        # Determine time horizon
        if urgency_score >= 4:
            return 'immediate'  # Within 30 minutes
        elif urgency_score >= 2:
            return 'short_term'  # Within 2 hours
        else:
            return 'medium_term'  # Within 8 hours

    def train_models_from_history(self):
        """Train models from historical sweep events"""
        logger.info("Training sweep prediction models from historical data...")
        
        # Load historical sweep events
        sweep_events = self.load_historical_sweep_events()
        
        if len(sweep_events) < 50:
            logger.warning("Insufficient historical data for meaningful training")
            return
        
        # Prepare training data
        X = []
        y = []
        
        feature_names = [
            'price_momentum_5', 'price_momentum_10', 'price_momentum_20',
            'recent_volatility', 'volatility_ratio',
            'volume_avg', 'volume_recent', 'volume_ratio',
            'order_flow_imbalance',
            'distance_to_nearest_resistance', 'distance_to_nearest_support',
            'nearest_resistance_strength', 'nearest_support_strength',
            'levels_above_count', 'levels_below_count',
            'avg_level_strength_above', 'avg_level_strength_below',
            'higher_highs_count', 'lower_lows_count', 'recent_high_low_ratio',
            'london_session', 'ny_session', 'overlap_session'
        ]
        
        for event in sweep_events:
            features = event.pre_sweep_features
            feature_array = []
            
            for name in feature_names:
                value = features.get(name, 0)
                if value == float('inf') or value == float('-inf'):
                    value = 0
                feature_array.append(value)
            
            X.append(feature_array)
            
            # Label encoding: 0 = no sweep, 1 = bullish sweep, 2 = bearish sweep
            if event.sweep_direction == 'bullish_sweep':
                y.append(1)
            elif event.sweep_direction == 'bearish_sweep':
                y.append(2)
            else:
                y.append(0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.feature_scaler.fit_transform(X)
        
        # Train classifier
        self.sweep_classifier.fit(X_scaled, y)
        
        # Calculate feature importance
        if hasattr(self.sweep_classifier, 'feature_importances_'):
            self.feature_importance = dict(zip(feature_names, self.sweep_classifier.feature_importances_))
        
        # Save models
        self.save_models()
        
        logger.info(f"✅ Models trained on {len(sweep_events)} historical sweep events")

    def load_historical_sweep_events(self) -> List[SweepEvent]:
        """Load historical sweep events from truth tracker"""
        sweep_events = []
        
        try:
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line)
                        
                        # Look for sweep patterns in trade data
                        signal_type = trade.get('signal_type', '')
                        if 'LIQUIDITY_SWEEP' in signal_type or 'SWEEP' in signal_type.upper():
                            
                            # Extract sweep event data
                            sweep_event = self.extract_sweep_event_from_trade(trade)
                            if sweep_event:
                                sweep_events.append(sweep_event)
                                
        except FileNotFoundError:
            logger.warning("Truth log file not found for historical training")
        except Exception as e:
            logger.error(f"Error loading historical sweep events: {e}")
        
        return sweep_events

    def extract_sweep_event_from_trade(self, trade: Dict) -> Optional[SweepEvent]:
        """Extract sweep event data from trade record"""
        try:
            # This would need to be enhanced with actual sweep detection logic
            # For now, create a placeholder implementation
            
            symbol = trade.get('symbol', '')
            entry_price = trade.get('entry_price', 0)
            outcome = trade.get('outcome', '')
            pips_result = trade.get('pips_result', 0)
            
            if not symbol or not entry_price:
                return None
            
            # Simple heuristic: if signal type contains SWEEP and was profitable
            sweep_direction = 'bullish_sweep' if pips_result > 0 else 'bearish_sweep'
            
            # Create placeholder features (in real implementation, would reconstruct from historical data)
            pre_sweep_features = {
                'price_momentum_5': 0,
                'price_momentum_10': 0,
                'recent_volatility': 0.0005,
                'volume_ratio': 1.0,
                'distance_to_nearest_resistance': 50,
                'distance_to_nearest_support': 50,
                'london_session': 1 if 8 <= datetime.now().hour <= 16 else 0,
                # ... other features would be reconstructed from historical market data
            }
            
            post_sweep_outcome = 'reversal_success' if outcome == 'WIN' else 'reversal_failed'
            
            sweep_event = SweepEvent(
                symbol=symbol,
                sweep_price=entry_price,
                sweep_direction=sweep_direction,
                pre_sweep_features=pre_sweep_features,
                post_sweep_outcome=post_sweep_outcome,
                timestamp=trade.get('signal_creation_time', time.time()),
                reversal_pips=pips_result if pips_result > 0 else None,
                time_to_reversal=trade.get('runtime_seconds', 0)
            )
            
            return sweep_event
            
        except Exception as e:
            logger.error(f"Error extracting sweep event: {e}")
            return None

    def save_models(self):
        """Save trained models to disk"""
        try:
            # Ensure models directory exists
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.sweep_classifier, f)
            
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.feature_scaler, f)
                
            logger.info("✅ Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def get_all_predictions(self) -> Dict[str, SweepPrediction]:
        """Get sweep predictions for all monitored symbols"""
        predictions = {}
        
        monitored_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'EURJPY', 'GBPJPY', 'XAUUSD']
        
        for symbol in monitored_symbols:
            prediction = self.predict_sweep(symbol)
            if prediction and prediction.probability > 60:  # Only high-confidence predictions
                predictions[symbol] = prediction
        
        return predictions

    def generate_prediction_report(self) -> Dict:
        """Generate comprehensive sweep prediction report"""
        
        predictions = self.get_all_predictions()
        
        # Analyze current market conditions
        market_conditions = self.analyze_current_market_conditions()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'high_confidence_predictions': len([p for p in predictions.values() if p.confidence_level == 'HIGH']),
            'immediate_horizon_predictions': len([p for p in predictions.values() if p.time_horizon == 'immediate']),
            'predictions': {symbol: asdict(pred) for symbol, pred in predictions.items()},
            'market_conditions': market_conditions,
            'model_performance': self.get_model_performance_metrics(),
            'feature_importance': self.feature_importance,
            'recommendations': self.generate_trading_recommendations(predictions)
        }
        
        return report

    def analyze_current_market_conditions(self) -> Dict:
        """Analyze current overall market conditions"""
        conditions = {
            'overall_volatility': 'medium',
            'dominant_session': 'unknown',
            'risk_sentiment': 'neutral',
            'liquidity_conditions': 'normal'
        }
        
        current_hour = datetime.now().hour
        
        # Session analysis
        if 13 <= current_hour <= 16:
            conditions['dominant_session'] = 'overlap'
        elif 8 <= current_hour <= 16:
            conditions['dominant_session'] = 'london'
        elif 13 <= current_hour <= 21:
            conditions['dominant_session'] = 'ny'
        else:
            conditions['dominant_session'] = 'asian'
        
        # Analyze volatility across all symbols
        all_volatilities = []
        for symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
            if len(self.price_history[symbol]) >= 20:
                prices = [tick['price'] for tick in list(self.price_history[symbol])[-20:]]
                volatility = np.std(prices)
                all_volatilities.append(volatility)
        
        if all_volatilities:
            avg_volatility = np.mean(all_volatilities)
            if avg_volatility > 0.0008:
                conditions['overall_volatility'] = 'high'
            elif avg_volatility > 0.0005:
                conditions['overall_volatility'] = 'medium'
            else:
                conditions['overall_volatility'] = 'low'
        
        return conditions

    def get_model_performance_metrics(self) -> Dict:
        """Get model performance metrics if available"""
        metrics = {
            'model_trained': self.sweep_classifier is not None,
            'feature_count': len(self.feature_importance) if self.feature_importance else 0,
            'top_features': []
        }
        
        if self.feature_importance:
            # Get top 5 most important features
            sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
            metrics['top_features'] = [
                {'feature': name, 'importance': round(importance, 3)}
                for name, importance in sorted_features[:5]
            ]
        
        return metrics

    def generate_trading_recommendations(self, predictions: Dict[str, SweepPrediction]) -> List[str]:
        """Generate actionable trading recommendations"""
        recommendations = []
        
        high_confidence = [p for p in predictions.values() if p.confidence_level == 'HIGH']
        immediate_predictions = [p for p in predictions.values() if p.time_horizon == 'immediate']
        
        if high_confidence:
            recommendations.append(f"🎯 {len(high_confidence)} HIGH confidence sweep predictions active")
            
        if immediate_predictions:
            recommendations.append(f"⚡ {len(immediate_predictions)} IMMEDIATE horizon predictions - watch closely")
            
        for symbol, prediction in predictions.items():
            if prediction.confidence_level == 'HIGH' and prediction.time_horizon == 'immediate':
                direction = "bullish reversal" if prediction.sweep_direction == 'bullish_sweep' else "bearish reversal"
                recommendations.append(f"🔥 {symbol}: {direction} setup at {prediction.predicted_sweep_price:.5f}")
        
        if not predictions:
            recommendations.append("📊 No high-probability sweep setups detected currently")
            recommendations.append("💡 Monitor for increasing volatility and level approaches")
        
        return recommendations

def main():
    """Run CITADEL Sweep Prediction analysis"""
    
    model = CitadelSweepPredictionModel()
    
    print("=== CITADEL SWEEP PREDICTION MODEL ===")
    
    # Generate prediction report
    report = model.generate_prediction_report()
    
    print(f"\nPredictions Generated: {report['total_predictions']}")
    print(f"High Confidence: {report['high_confidence_predictions']}")
    print(f"Immediate Horizon: {report['immediate_horizon_predictions']}")
    
    if report['predictions']:
        print("\n🎯 ACTIVE PREDICTIONS:")
        for symbol, prediction in report['predictions'].items():
            print(f"{symbol}: {prediction['sweep_direction']} at {prediction['predicted_sweep_price']:.5f}")
            print(f"  Confidence: {prediction['confidence_level']} ({prediction['probability']}%)")
            print(f"  Horizon: {prediction['time_horizon']}")
    
    print("\n💡 RECOMMENDATIONS:")
    for recommendation in report['recommendations']:
        print(f"  {recommendation}")
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f'/root/HydraX-v2/reports/sweep_prediction_report_{timestamp}.json'
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Report saved to: {report_path}")

if __name__ == "__main__":
    main()