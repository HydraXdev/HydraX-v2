# cross_asset_correlation.py
# Cross-Asset Correlation System for Multi-Market Analysis

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AssetClass(Enum):
    """Asset class enumeration"""
    FOREX = "forex"
    INDEX = "index"
    COMMODITY = "commodity"
    BOND = "bond"
    CRYPTO = "crypto"

class RiskSentiment(Enum):
    """Market risk sentiment"""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"
    MIXED = "mixed"

@dataclass
class AssetData:
    """Data structure for asset information"""
    symbol: str
    asset_class: AssetClass
    price: float
    change_pct: float
    volume: float
    timestamp: datetime
    additional_data: Dict[str, Any] = None

@dataclass
class CorrelationResult:
    """Correlation analysis result"""
    asset1: str
    asset2: str
    correlation: float
    period: int
    strength: str  # 'strong', 'moderate', 'weak'
    direction: str  # 'positive', 'negative', 'neutral'

@dataclass
class IntermarketDivergence:
    """Intermarket divergence detection result"""
    assets: List[str]
    divergence_type: str  # 'price', 'momentum', 'volume'
    severity: float  # 0-100
    expected_resolution: str  # 'asset1_up', 'asset2_down', etc.
    confidence: float  # 0-1

class BondYieldCalculator:
    """Bond yield differential calculator"""
    
    def __init__(self):
        self.yield_data = {}
        self.historical_yields = {}
        
    def update_yield(self, bond_symbol: str, yield_value: float, timestamp: datetime):
        """Update bond yield data"""
        if bond_symbol not in self.yield_data:
            self.yield_data[bond_symbol] = deque(maxlen=500)
            
        self.yield_data[bond_symbol].append({
            'yield': yield_value,
            'timestamp': timestamp
        })
    
    def calculate_yield_differential(self, bond1: str, bond2: str) -> Optional[float]:
        """Calculate yield differential between two bonds"""
        if bond1 not in self.yield_data or bond2 not in self.yield_data:
            return None
            
        if not self.yield_data[bond1] or not self.yield_data[bond2]:
            return None
            
        latest_yield1 = self.yield_data[bond1][-1]['yield']
        latest_yield2 = self.yield_data[bond2][-1]['yield']
        
        return latest_yield1 - latest_yield2
    
    def get_yield_curve_slope(self, short_term_bond: str, long_term_bond: str) -> Optional[float]:
        """Calculate yield curve slope (indicator of economic expectations)"""
        differential = self.calculate_yield_differential(long_term_bond, short_term_bond)
        return differential
    
    def analyze_yield_trends(self) -> Dict[str, str]:
        """Analyze yield trends across all tracked bonds"""
        trends = {}
        
        for bond, data in self.yield_data.items():
            if len(data) < 20:
                trends[bond] = 'insufficient_data'
                continue
                
            recent_yields = [d['yield'] for d in list(data)[-20:]]
            
            # Simple trend detection
            if recent_yields[-1] > recent_yields[0]:
                if recent_yields[-1] > recent_yields[0] * 1.05:  # 5% increase
                    trends[bond] = 'rising_fast'
                else:
                    trends[bond] = 'rising'
            elif recent_yields[-1] < recent_yields[0]:
                if recent_yields[-1] < recent_yields[0] * 0.95:  # 5% decrease
                    trends[bond] = 'falling_fast'
                else:
                    trends[bond] = 'falling'
            else:
                trends[bond] = 'stable'
                
        return trends

class CommodityCorrelationAnalyzer:
    """Commodity correlation analyzer for commodity currencies"""
    
    # Commodity currency mappings
    COMMODITY_CURRENCY_MAP = {
        'AUD': ['GOLD', 'IRON_ORE', 'COAL'],  # Australian Dollar
        'CAD': ['OIL', 'NATURAL_GAS', 'LUMBER'],  # Canadian Dollar
        'NZD': ['DAIRY', 'WOOL', 'MEAT'],  # New Zealand Dollar
        'NOK': ['OIL', 'NATURAL_GAS', 'FISH'],  # Norwegian Krone
        'ZAR': ['GOLD', 'PLATINUM', 'DIAMONDS'],  # South African Rand
        'BRL': ['IRON_ORE', 'SOYBEANS', 'COFFEE'],  # Brazilian Real
        'RUB': ['OIL', 'NATURAL_GAS', 'GOLD'],  # Russian Ruble
        'CLP': ['COPPER', 'LITHIUM'],  # Chilean Peso
    }
    
    def __init__(self):
        self.commodity_data = {}
        self.currency_data = {}
        self.correlation_cache = {}
        
    def update_commodity_price(self, commodity: str, price: float, timestamp: datetime):
        """Update commodity price data"""
        if commodity not in self.commodity_data:
            self.commodity_data[commodity] = deque(maxlen=500)
            
        self.commodity_data[commodity].append({
            'price': price,
            'timestamp': timestamp
        })
    
    def update_currency_price(self, currency: str, price: float, timestamp: datetime):
        """Update currency price data"""
        if currency not in self.currency_data:
            self.currency_data[currency] = deque(maxlen=500)
            
        self.currency_data[currency].append({
            'price': price,
            'timestamp': timestamp
        })
    
    def calculate_correlation(self, currency: str, commodity: str, period: int = 50) -> Optional[float]:
        """Calculate correlation between commodity and currency"""
        if currency not in self.currency_data or commodity not in self.commodity_data:
            return None
            
        currency_prices = [d['price'] for d in list(self.currency_data[currency])[-period:]]
        commodity_prices = [d['price'] for d in list(self.commodity_data[commodity])[-period:]]
        
        if len(currency_prices) < period or len(commodity_prices) < period:
            return None
            
        # Calculate percentage changes
        currency_returns = np.diff(currency_prices) / currency_prices[:-1]
        commodity_returns = np.diff(commodity_prices) / commodity_prices[:-1]
        
        # Calculate correlation
        if len(currency_returns) > 0 and len(commodity_returns) > 0:
            correlation = np.corrcoef(currency_returns, commodity_returns)[0, 1]
            return correlation
        
        return None
    
    def get_commodity_currency_signals(self) -> Dict[str, Dict[str, Any]]:
        """Get trading signals based on commodity-currency correlations"""
        signals = {}
        
        for currency, commodities in self.COMMODITY_CURRENCY_MAP.items():
            currency_signals = {
                'correlations': {},
                'signal': 'neutral',
                'strength': 0.0
            }
            
            total_correlation = 0
            valid_correlations = 0
            
            for commodity in commodities:
                corr = self.calculate_correlation(currency, commodity)
                if corr is not None:
                    currency_signals['correlations'][commodity] = corr
                    total_correlation += corr
                    valid_correlations += 1
            
            if valid_correlations > 0:
                avg_correlation = total_correlation / valid_correlations
                
                # Determine signal based on correlation strength
                if avg_correlation > 0.7:
                    currency_signals['signal'] = 'strong_positive'
                    currency_signals['strength'] = avg_correlation
                elif avg_correlation > 0.3:
                    currency_signals['signal'] = 'moderate_positive'
                    currency_signals['strength'] = avg_correlation
                elif avg_correlation < -0.7:
                    currency_signals['signal'] = 'strong_negative'
                    currency_signals['strength'] = abs(avg_correlation)
                elif avg_correlation < -0.3:
                    currency_signals['signal'] = 'moderate_negative'
                    currency_signals['strength'] = abs(avg_correlation)
                    
            signals[currency] = currency_signals
            
        return signals

class EquityRiskDetector:
    """Equity market risk on/off detector"""
    
    # Risk-on and risk-off assets
    RISK_ON_ASSETS = ['SPX', 'NDX', 'DAX', 'NKY', 'EMERGING_MARKETS']
    RISK_OFF_ASSETS = ['GOLD', 'JPY', 'CHF', 'US_BONDS', 'GERMAN_BONDS']
    
    def __init__(self):
        self.asset_data = {}
        self.risk_history = deque(maxlen=100)
        
    def update_asset_data(self, asset: str, price: float, volume: float, timestamp: datetime):
        """Update asset data"""
        if asset not in self.asset_data:
            self.asset_data[asset] = deque(maxlen=500)
            
        self.asset_data[asset].append({
            'price': price,
            'volume': volume,
            'timestamp': timestamp
        })
    
    def calculate_risk_sentiment(self) -> RiskSentiment:
        """Calculate current market risk sentiment"""
        risk_on_score = 0
        risk_off_score = 0
        
        # Analyze risk-on assets
        for asset in self.RISK_ON_ASSETS:
            if asset in self.asset_data and len(self.asset_data[asset]) >= 20:
                recent_data = list(self.asset_data[asset])[-20:]
                prices = [d['price'] for d in recent_data]
                
                # Calculate momentum
                momentum = (prices[-1] - prices[0]) / prices[0]
                
                # Calculate volume trend
                volumes = [d['volume'] for d in recent_data]
                volume_trend = np.mean(volumes[-5:]) / np.mean(volumes[-20:-15]) if np.mean(volumes[-20:-15]) > 0 else 1
                
                if momentum > 0.02:  # 2% positive
                    risk_on_score += 2
                elif momentum > 0:
                    risk_on_score += 1
                    
                if volume_trend > 1.2:  # 20% volume increase
                    risk_on_score += 1
        
        # Analyze risk-off assets
        for asset in self.RISK_OFF_ASSETS:
            if asset in self.asset_data and len(self.asset_data[asset]) >= 20:
                recent_data = list(self.asset_data[asset])[-20:]
                prices = [d['price'] for d in recent_data]
                
                # Calculate momentum
                momentum = (prices[-1] - prices[0]) / prices[0]
                
                # Calculate volume trend
                volumes = [d['volume'] for d in recent_data]
                volume_trend = np.mean(volumes[-5:]) / np.mean(volumes[-20:-15]) if np.mean(volumes[-20:-15]) > 0 else 1
                
                if momentum > 0.02:  # 2% positive
                    risk_off_score += 2
                elif momentum > 0:
                    risk_off_score += 1
                    
                if volume_trend > 1.2:  # 20% volume increase
                    risk_off_score += 1
        
        # Determine sentiment
        total_score = risk_on_score + risk_off_score
        if total_score == 0:
            return RiskSentiment.NEUTRAL
            
        risk_on_ratio = risk_on_score / total_score
        
        if risk_on_ratio > 0.7:
            return RiskSentiment.RISK_ON
        elif risk_on_ratio < 0.3:
            return RiskSentiment.RISK_OFF
        elif abs(risk_on_score - risk_off_score) < 3:
            return RiskSentiment.MIXED
        else:
            return RiskSentiment.NEUTRAL
    
    def get_sector_rotation_signals(self) -> Dict[str, str]:
        """Identify sector rotation based on risk sentiment"""
        sentiment = self.calculate_risk_sentiment()
        
        signals = {
            'sentiment': sentiment.value,
            'recommended_sectors': [],
            'avoid_sectors': []
        }
        
        if sentiment == RiskSentiment.RISK_ON:
            signals['recommended_sectors'] = ['Technology', 'Consumer Discretionary', 'Financials']
            signals['avoid_sectors'] = ['Utilities', 'Consumer Staples', 'Real Estate']
        elif sentiment == RiskSentiment.RISK_OFF:
            signals['recommended_sectors'] = ['Utilities', 'Consumer Staples', 'Healthcare']
            signals['avoid_sectors'] = ['Technology', 'Energy', 'Financials']
        elif sentiment == RiskSentiment.MIXED:
            signals['recommended_sectors'] = ['Healthcare', 'Industrials']
            signals['avoid_sectors'] = ['Energy', 'Real Estate']
            
        return signals

class DollarIndexAnalyzer:
    """US Dollar Index (DXY) analyzer"""
    
    # DXY component weights
    DXY_WEIGHTS = {
        'EUR': 0.576,  # 57.6%
        'JPY': 0.136,  # 13.6%
        'GBP': 0.119,  # 11.9%
        'CAD': 0.091,  # 9.1%
        'SEK': 0.042,  # 4.2%
        'CHF': 0.036   # 3.6%
    }
    
    def __init__(self):
        self.currency_data = {}
        self.dxy_history = deque(maxlen=500)
        
    def update_currency_rate(self, currency: str, rate: float, timestamp: datetime):
        """Update currency exchange rate (vs USD)"""
        if currency not in self.currency_data:
            self.currency_data[currency] = deque(maxlen=500)
            
        self.currency_data[currency].append({
            'rate': rate,
            'timestamp': timestamp
        })
    
    def calculate_dxy(self) -> Optional[float]:
        """Calculate current DXY value"""
        dxy_value = 50.14348112  # Base value
        
        for currency, weight in self.DXY_WEIGHTS.items():
            if currency not in self.currency_data or not self.currency_data[currency]:
                return None
                
            latest_rate = self.currency_data[currency][-1]['rate']
            
            # DXY uses inverse rates for calculation
            if currency == 'EUR':
                # EUR/USD is already in correct format
                currency_contribution = (1 / latest_rate) ** weight
            else:
                # Other pairs need to be inverted (USD/XXX format)
                currency_contribution = latest_rate ** weight
                
            dxy_value *= currency_contribution
            
        return dxy_value
    
    def analyze_dollar_strength(self) -> Dict[str, Any]:
        """Analyze dollar strength and trend"""
        current_dxy = self.calculate_dxy()
        if current_dxy is None:
            return {'status': 'insufficient_data'}
            
        # Store current DXY
        self.dxy_history.append({
            'value': current_dxy,
            'timestamp': datetime.now()
        })
        
        if len(self.dxy_history) < 20:
            return {
                'status': 'calculating',
                'current_value': current_dxy
            }
            
        # Analyze trend
        recent_values = [d['value'] for d in list(self.dxy_history)[-20:]]
        
        # Calculate various metrics
        sma_20 = np.mean(recent_values)
        trend = 'bullish' if current_dxy > sma_20 else 'bearish'
        
        # Calculate momentum
        momentum = (current_dxy - recent_values[0]) / recent_values[0] * 100
        
        # Support and resistance levels
        support = min(recent_values[-50:]) if len(self.dxy_history) >= 50 else min(recent_values)
        resistance = max(recent_values[-50:]) if len(self.dxy_history) >= 50 else max(recent_values)
        
        return {
            'status': 'active',
            'current_value': current_dxy,
            'sma_20': sma_20,
            'trend': trend,
            'momentum_pct': momentum,
            'support': support,
            'resistance': resistance,
            'signal': self._generate_dxy_signal(current_dxy, sma_20, momentum)
        }
    
    def _generate_dxy_signal(self, current: float, sma: float, momentum: float) -> str:
        """Generate trading signal based on DXY analysis"""
        if current > sma and momentum > 2:
            return 'strong_dollar_buy_usd_pairs'
        elif current > sma and momentum > 0:
            return 'moderate_dollar_favor_usd'
        elif current < sma and momentum < -2:
            return 'weak_dollar_sell_usd_pairs'
        elif current < sma and momentum < 0:
            return 'moderate_weak_favor_non_usd'
        else:
            return 'neutral_no_clear_bias'

class IntermarketDivergenceDetector:
    """Detects divergences between correlated markets"""
    
    # Known correlations to monitor
    CORRELATION_PAIRS = [
        ('GOLD', 'DXY', 'negative'),
        ('OIL', 'CAD', 'positive'),
        ('AUD', 'GOLD', 'positive'),
        ('USDJPY', 'US10Y', 'positive'),
        ('SPX', 'VIX', 'negative'),
        ('EURUSD', 'DXY', 'negative'),
        ('COPPER', 'AUD', 'positive'),
        ('DAX', 'EURUSD', 'mixed'),
    ]
    
    def __init__(self):
        self.market_data = {}
        self.divergences = []
        
    def update_market_data(self, market: str, price: float, timestamp: datetime):
        """Update market data"""
        if market not in self.market_data:
            self.market_data[market] = deque(maxlen=200)
            
        self.market_data[market].append({
            'price': price,
            'timestamp': timestamp
        })
    
    def detect_divergences(self) -> List[IntermarketDivergence]:
        """Detect divergences between correlated markets"""
        divergences = []
        
        for asset1, asset2, expected_correlation in self.CORRELATION_PAIRS:
            if asset1 not in self.market_data or asset2 not in self.market_data:
                continue
                
            if len(self.market_data[asset1]) < 50 or len(self.market_data[asset2]) < 50:
                continue
                
            # Get recent price data
            asset1_prices = [d['price'] for d in list(self.market_data[asset1])[-50:]]
            asset2_prices = [d['price'] for d in list(self.market_data[asset2])[-50:]]
            
            # Calculate recent trends
            asset1_trend = (asset1_prices[-1] - asset1_prices[-20]) / asset1_prices[-20]
            asset2_trend = (asset2_prices[-1] - asset2_prices[-20]) / asset2_prices[-20]
            
            # Check for divergence
            divergence_detected = False
            
            if expected_correlation == 'positive':
                # Should move together
                if (asset1_trend > 0.02 and asset2_trend < -0.02) or \
                   (asset1_trend < -0.02 and asset2_trend > 0.02):
                    divergence_detected = True
                    
            elif expected_correlation == 'negative':
                # Should move opposite
                if (asset1_trend > 0.02 and asset2_trend > 0.02) or \
                   (asset1_trend < -0.02 and asset2_trend < -0.02):
                    divergence_detected = True
                    
            if divergence_detected:
                # Calculate divergence severity
                severity = abs(asset1_trend - asset2_trend) * 100
                if expected_correlation == 'negative':
                    severity = abs(asset1_trend + asset2_trend) * 100
                    
                # Predict resolution
                resolution = self._predict_divergence_resolution(
                    asset1, asset2, asset1_trend, asset2_trend, expected_correlation
                )
                
                divergences.append(IntermarketDivergence(
                    assets=[asset1, asset2],
                    divergence_type='price',
                    severity=min(100, severity * 20),  # Scale to 0-100
                    expected_resolution=resolution,
                    confidence=0.7  # Could be enhanced with more sophisticated models
                ))
                
        return divergences
    
    def _predict_divergence_resolution(self, asset1: str, asset2: str, 
                                     trend1: float, trend2: float, 
                                     correlation: str) -> str:
        """Predict how divergence will resolve"""
        # Simplified resolution prediction
        # In practice, this would use more sophisticated analysis
        
        if correlation == 'positive':
            if abs(trend1) > abs(trend2):
                return f"{asset2}_follows_{asset1}"
            else:
                return f"{asset1}_follows_{asset2}"
        else:  # negative correlation
            if trend1 > 0 and trend2 > 0:
                return f"{asset1}_reverses_down_or_{asset2}_reverses_down"
            elif trend1 < 0 and trend2 < 0:
                return f"{asset1}_reverses_up_or_{asset2}_reverses_up"
                
        return "uncertain_resolution"

class CorrelationMatrixCalculator:
    """Calculate and maintain correlation matrices across assets"""
    
    def __init__(self):
        self.asset_data = {}
        self.correlation_matrix = None
        self.last_calculation = None
        
    def update_asset_price(self, asset: str, price: float, timestamp: datetime):
        """Update asset price data"""
        if asset not in self.asset_data:
            self.asset_data[asset] = deque(maxlen=500)
            
        self.asset_data[asset].append({
            'price': price,
            'timestamp': timestamp
        })
    
    def calculate_correlation_matrix(self, period: int = 50) -> Optional[pd.DataFrame]:
        """Calculate correlation matrix for all assets"""
        # Check if we have enough data
        valid_assets = []
        price_data = {}
        
        for asset, data in self.asset_data.items():
            if len(data) >= period:
                valid_assets.append(asset)
                prices = [d['price'] for d in list(data)[-period:]]
                # Calculate returns
                returns = np.diff(prices) / prices[:-1]
                price_data[asset] = returns
                
        if len(valid_assets) < 2:
            return None
            
        # Create DataFrame
        df = pd.DataFrame(price_data)
        
        # Calculate correlation matrix
        self.correlation_matrix = df.corr()
        self.last_calculation = datetime.now()
        
        return self.correlation_matrix
    
    def get_strongest_correlations(self, threshold: float = 0.7) -> List[CorrelationResult]:
        """Get strongest correlations above threshold"""
        if self.correlation_matrix is None:
            return []
            
        correlations = []
        
        # Extract upper triangle to avoid duplicates
        for i in range(len(self.correlation_matrix.columns)):
            for j in range(i + 1, len(self.correlation_matrix.columns)):
                asset1 = self.correlation_matrix.columns[i]
                asset2 = self.correlation_matrix.columns[j]
                corr_value = self.correlation_matrix.iloc[i, j]
                
                if abs(corr_value) >= threshold:
                    # Determine strength
                    if abs(corr_value) >= 0.9:
                        strength = 'very_strong'
                    elif abs(corr_value) >= 0.7:
                        strength = 'strong'
                    elif abs(corr_value) >= 0.5:
                        strength = 'moderate'
                    else:
                        strength = 'weak'
                        
                    # Determine direction
                    direction = 'positive' if corr_value > 0 else 'negative'
                    
                    correlations.append(CorrelationResult(
                        asset1=asset1,
                        asset2=asset2,
                        correlation=corr_value,
                        period=len(self.correlation_matrix),
                        strength=strength,
                        direction=direction
                    ))
                    
        # Sort by absolute correlation value
        correlations.sort(key=lambda x: abs(x.correlation), reverse=True)
        
        return correlations
    
    def get_asset_correlation_summary(self, asset: str) -> Dict[str, Any]:
        """Get correlation summary for a specific asset"""
        if self.correlation_matrix is None or asset not in self.correlation_matrix.columns:
            return {'status': 'no_data'}
            
        asset_correlations = self.correlation_matrix[asset]
        
        # Find most correlated assets
        positive_corr = asset_correlations[asset_correlations > 0.5].sort_values(ascending=False)
        negative_corr = asset_correlations[asset_correlations < -0.5].sort_values()
        
        return {
            'status': 'calculated',
            'asset': asset,
            'positive_correlations': positive_corr.to_dict(),
            'negative_correlations': negative_corr.to_dict(),
            'average_correlation': asset_correlations.mean(),
            'correlation_volatility': asset_correlations.std()
        }

class PredictiveCorrelationModel:
    """Predictive correlation models using rolling windows and regime detection"""
    
    def __init__(self):
        self.correlation_history = {}
        self.regime_history = deque(maxlen=100)
        self.predictions = {}
        
    def update_correlation(self, asset1: str, asset2: str, correlation: float, timestamp: datetime):
        """Update correlation history"""
        pair_key = f"{asset1}_{asset2}"
        
        if pair_key not in self.correlation_history:
            self.correlation_history[pair_key] = deque(maxlen=200)
            
        self.correlation_history[pair_key].append({
            'correlation': correlation,
            'timestamp': timestamp
        })
    
    def predict_correlation_change(self, asset1: str, asset2: str, horizon: int = 5) -> Dict[str, Any]:
        """Predict future correlation changes"""
        pair_key = f"{asset1}_{asset2}"
        
        if pair_key not in self.correlation_history or len(self.correlation_history[pair_key]) < 30:
            return {'status': 'insufficient_data'}
            
        # Get historical correlations
        correlations = [d['correlation'] for d in self.correlation_history[pair_key]]
        
        # Simple trend analysis
        recent_trend = np.polyfit(range(10), correlations[-10:], 1)[0]
        
        # Volatility of correlation
        correlation_std = np.std(correlations[-30:])
        
        # Mean reversion tendency
        mean_correlation = np.mean(correlations)
        current_correlation = correlations[-1]
        deviation_from_mean = current_correlation - mean_correlation
        
        # Simple prediction model
        predicted_change = -deviation_from_mean * 0.3  # Mean reversion factor
        predicted_change += recent_trend * horizon * 0.5  # Trend continuation
        
        # Add noise based on historical volatility
        uncertainty = correlation_std * np.sqrt(horizon)
        
        predicted_correlation = current_correlation + predicted_change
        predicted_correlation = np.clip(predicted_correlation, -1, 1)
        
        return {
            'status': 'calculated',
            'current_correlation': current_correlation,
            'predicted_correlation': predicted_correlation,
            'confidence_interval': (
                max(-1, predicted_correlation - 2 * uncertainty),
                min(1, predicted_correlation + 2 * uncertainty)
            ),
            'trend': 'strengthening' if recent_trend > 0 else 'weakening',
            'volatility': 'high' if correlation_std > 0.2 else 'normal'
        }
    
    def detect_correlation_regime_change(self) -> Dict[str, Any]:
        """Detect regime changes in correlation patterns"""
        regime_changes = []
        
        for pair_key, history in self.correlation_history.items():
            if len(history) < 50:
                continue
                
            correlations = [d['correlation'] for d in history]
            
            # Calculate rolling statistics
            recent_mean = np.mean(correlations[-20:])
            historical_mean = np.mean(correlations[-50:-20])
            recent_std = np.std(correlations[-20:])
            historical_std = np.std(correlations[-50:-20])
            
            # Detect significant changes
            mean_change = abs(recent_mean - historical_mean)
            std_change = abs(recent_std - historical_std)
            
            if mean_change > 0.3 or std_change > 0.2:
                assets = pair_key.split('_')
                regime_changes.append({
                    'pair': pair_key,
                    'assets': assets,
                    'type': 'mean_shift' if mean_change > 0.3 else 'volatility_shift',
                    'old_mean': historical_mean,
                    'new_mean': recent_mean,
                    'significance': mean_change + std_change
                })
                
        # Sort by significance
        regime_changes.sort(key=lambda x: x['significance'], reverse=True)
        
        return {
            'detected_changes': regime_changes[:5],  # Top 5 most significant
            'market_regime': self._classify_market_regime(regime_changes)
        }
    
    def _classify_market_regime(self, changes: List[Dict]) -> str:
        """Classify overall market regime based on correlation changes"""
        if not changes:
            return 'stable'
            
        # Count types of changes
        mean_shifts = sum(1 for c in changes if c['type'] == 'mean_shift')
        volatility_shifts = sum(1 for c in changes if c['type'] == 'volatility_shift')
        
        if mean_shifts > 3 and volatility_shifts > 2:
            return 'regime_transition'
        elif mean_shifts > 2:
            return 'correlation_breakdown'
        elif volatility_shifts > 2:
            return 'increasing_dispersion'
        else:
            return 'minor_adjustments'

class CrossAssetCorrelationSystem:
    """Main cross-asset correlation system integrating all components"""
    
    def __init__(self):
        self.bond_calculator = BondYieldCalculator()
        self.commodity_analyzer = CommodityCorrelationAnalyzer()
        self.equity_detector = EquityRiskDetector()
        self.dollar_analyzer = DollarIndexAnalyzer()
        self.divergence_detector = IntermarketDivergenceDetector()
        self.correlation_calculator = CorrelationMatrixCalculator()
        self.predictive_model = PredictiveCorrelationModel()
        
        # Major asset tracking
        self.major_assets = {
            'forex': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD'],
            'indices': ['SPX', 'NDX', 'DJI', 'DAX', 'FTSE', 'NKY', 'HSI'],
            'commodities': ['GOLD', 'SILVER', 'OIL', 'NATURAL_GAS', 'COPPER', 'WHEAT', 'CORN'],
            'bonds': ['US10Y', 'US2Y', 'BUND10Y', 'JGB10Y', 'GILT10Y']
        }
        
        logger.info("Cross-Asset Correlation System initialized")
    
    def update_market_data(self, asset_data: AssetData):
        """Update all relevant components with new market data"""
        symbol = asset_data.symbol
        price = asset_data.price
        timestamp = asset_data.timestamp
        
        # Update correlation calculator
        self.correlation_calculator.update_asset_price(symbol, price, timestamp)
        
        # Update specific components based on asset class
        if asset_data.asset_class == AssetClass.BOND:
            if 'yield' in asset_data.additional_data:
                self.bond_calculator.update_yield(
                    symbol, 
                    asset_data.additional_data['yield'], 
                    timestamp
                )
                
        elif asset_data.asset_class == AssetClass.COMMODITY:
            self.commodity_analyzer.update_commodity_price(symbol, price, timestamp)
            
        elif asset_data.asset_class == AssetClass.FOREX:
            # Update currency data
            if symbol.startswith('USD'):
                currency = symbol[3:6]
                self.commodity_analyzer.update_currency_price(currency, 1/price, timestamp)
            else:
                currency = symbol[0:3]
                self.commodity_analyzer.update_currency_price(currency, price, timestamp)
                
            # Update dollar index components
            if symbol in ['EURUSD', 'USDJPY', 'GBPUSD', 'USDCAD', 'USDSEK', 'USDCHF']:
                if symbol == 'EURUSD':
                    self.dollar_analyzer.update_currency_rate('EUR', price, timestamp)
                else:
                    currency = symbol[3:6]
                    self.dollar_analyzer.update_currency_rate(currency, 1/price, timestamp)
                    
        elif asset_data.asset_class == AssetClass.INDEX:
            # Update equity risk detector
            volume = asset_data.volume if asset_data.volume else 1000000
            self.equity_detector.update_asset_data(symbol, price, volume, timestamp)
            
        # Update divergence detector for all assets
        self.divergence_detector.update_market_data(symbol, price, timestamp)
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive cross-asset analysis"""
        
        # Calculate correlation matrix
        correlation_matrix = self.correlation_calculator.calculate_correlation_matrix()
        
        # Get various analyses
        bond_analysis = {
            'yield_trends': self.bond_calculator.analyze_yield_trends(),
            'us_german_spread': self.bond_calculator.calculate_yield_differential('US10Y', 'BUND10Y'),
            'yield_curve_slope': self.bond_calculator.get_yield_curve_slope('US2Y', 'US10Y')
        }
        
        commodity_signals = self.commodity_analyzer.get_commodity_currency_signals()
        
        risk_sentiment = self.equity_detector.calculate_risk_sentiment()
        sector_signals = self.equity_detector.get_sector_rotation_signals()
        
        dollar_analysis = self.dollar_analyzer.analyze_dollar_strength()
        
        divergences = self.divergence_detector.detect_divergences()
        
        strongest_correlations = self.correlation_calculator.get_strongest_correlations()
        
        regime_analysis = self.predictive_model.detect_correlation_regime_change()
        
        return {
            'timestamp': datetime.now(),
            'risk_sentiment': risk_sentiment.value,
            'dollar_analysis': dollar_analysis,
            'bond_analysis': bond_analysis,
            'commodity_currency_signals': commodity_signals,
            'sector_rotation': sector_signals,
            'divergences': [
                {
                    'assets': d.assets,
                    'type': d.divergence_type,
                    'severity': d.severity,
                    'resolution': d.expected_resolution,
                    'confidence': d.confidence
                } for d in divergences
            ],
            'strongest_correlations': [
                {
                    'pair': f"{c.asset1}/{c.asset2}",
                    'correlation': c.correlation,
                    'strength': c.strength,
                    'direction': c.direction
                } for c in strongest_correlations[:10]
            ],
            'regime_status': regime_analysis,
            'trading_bias': self._generate_trading_bias(risk_sentiment, dollar_analysis)
        }
    
    def _generate_trading_bias(self, risk_sentiment: RiskSentiment, 
                              dollar_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate trading bias based on cross-asset analysis"""
        bias = {
            'overall': 'neutral',
            'forex': '',
            'equity': '',
            'commodity': ''
        }
        
        # Risk sentiment bias
        if risk_sentiment == RiskSentiment.RISK_ON:
            bias['equity'] = 'bullish_growth_stocks'
            bias['commodity'] = 'bullish_industrial_metals'
            bias['forex'] = 'bearish_safe_havens'
        elif risk_sentiment == RiskSentiment.RISK_OFF:
            bias['equity'] = 'bearish_defensive_only'
            bias['commodity'] = 'bullish_gold_silver'
            bias['forex'] = 'bullish_jpy_chf'
            
        # Dollar bias overlay
        if dollar_analysis.get('signal', '').startswith('strong_dollar'):
            bias['forex'] = 'bullish_usd_pairs'
        elif dollar_analysis.get('signal', '').startswith('weak_dollar'):
            bias['forex'] = 'bearish_usd_pairs'
            
        # Overall bias
        if risk_sentiment == RiskSentiment.RISK_ON and 'weak_dollar' in dollar_analysis.get('signal', ''):
            bias['overall'] = 'strong_bullish_risk_assets'
        elif risk_sentiment == RiskSentiment.RISK_OFF and 'strong_dollar' in dollar_analysis.get('signal', ''):
            bias['overall'] = 'strong_bearish_risk_assets'
        else:
            bias['overall'] = 'mixed_selective_opportunities'
            
        return bias
    
    def get_pair_specific_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get analysis specific to a trading pair"""
        
        # Get correlations for this asset
        asset_correlations = self.correlation_calculator.get_asset_correlation_summary(symbol)
        
        # Check for relevant divergences
        relevant_divergences = []
        for divergence in self.divergence_detector.detect_divergences():
            if symbol in divergence.assets:
                relevant_divergences.append(divergence)
                
        # Get predictive correlation for key pairs
        predictions = {}
        if symbol == 'EURUSD':
            predictions['DXY'] = self.predictive_model.predict_correlation_change('EURUSD', 'DXY')
        elif symbol == 'GOLD':
            predictions['DXY'] = self.predictive_model.predict_correlation_change('GOLD', 'DXY')
            predictions['USDJPY'] = self.predictive_model.predict_correlation_change('GOLD', 'USDJPY')
            
        return {
            'symbol': symbol,
            'correlations': asset_correlations,
            'divergences': relevant_divergences,
            'correlation_predictions': predictions,
            'trading_implications': self._generate_pair_implications(
                symbol, asset_correlations, relevant_divergences
            )
        }
    
    def _generate_pair_implications(self, symbol: str, correlations: Dict, 
                                   divergences: List) -> Dict[str, Any]:
        """Generate trading implications for a specific pair"""
        implications = {
            'primary_drivers': [],
            'risk_factors': [],
            'optimal_timeframe': '',
            'position_sizing': 'normal'
        }
        
        # Analyze correlations
        if 'positive_correlations' in correlations:
            for asset, corr in correlations['positive_correlations'].items():
                if corr > 0.7:
                    implications['primary_drivers'].append(f"{asset} (strong positive)")
                    
        if 'negative_correlations' in correlations:
            for asset, corr in correlations['negative_correlations'].items():
                if corr < -0.7:
                    implications['primary_drivers'].append(f"{asset} (strong negative)")
                    
        # Check divergences
        if divergences:
            implications['risk_factors'].append('Active divergence detected')
            implications['position_sizing'] = 'reduced'
            
        # Determine optimal timeframe based on correlation volatility
        if correlations.get('correlation_volatility', 0) > 0.3:
            implications['optimal_timeframe'] = 'short_term_intraday'
        else:
            implications['optimal_timeframe'] = 'medium_term_swing'
            
        return implications

# Usage example
if __name__ == "__main__":
    # Initialize system
    correlation_system = CrossAssetCorrelationSystem()
    
    # Simulate market updates
    test_data = [
        AssetData('EURUSD', AssetClass.FOREX, 1.0850, 0.5, 1000000, datetime.now()),
        AssetData('GOLD', AssetClass.COMMODITY, 2050.50, 1.2, 500000, datetime.now()),
        AssetData('SPX', AssetClass.INDEX, 4500.00, 0.8, 2000000, datetime.now()),
        AssetData('US10Y', AssetClass.BOND, 4.25, 0.1, 0, datetime.now(), {'yield': 4.25}),
    ]
    
    for data in test_data:
        correlation_system.update_market_data(data)
    
    # Get analysis
    analysis = correlation_system.get_comprehensive_analysis()
    print(f"Risk Sentiment: {analysis['risk_sentiment']}")
    print(f"Trading Bias: {analysis['trading_bias']}")