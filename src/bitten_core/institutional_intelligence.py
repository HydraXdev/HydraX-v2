#!/usr/bin/env python3
"""
BITTEN Institutional Intelligence Engine
Smart Money Tracking, Correlation Storm Detection, Cross-Asset Analysis
"""

import json
import time
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class LiquidityEvent(Enum):
    """Types of liquidity events"""
    SWEEP = "liquidity_sweep"
    ABSORPTION = "absorption"
    VOID = "liquidity_void"
    INJECTION = "institutional_injection"
    WITHDRAWAL = "institutional_withdrawal"

class SmartMoneyAction(Enum):
    """Smart money activity types"""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    ROTATION = "sector_rotation"
    HEDGING = "hedging"
    SPECULATION = "speculation"

class CorrelationState(Enum):
    """Market correlation states"""
    NORMAL = "normal"
    HIGH_CORRELATION = "high_correlation"
    CORRELATION_STORM = "correlation_storm"
    DECOUPLING = "decoupling"
    CHAOS = "chaos"

@dataclass
class SmartMoneySignal:
    """Smart money activity signal"""
    timestamp: datetime
    symbol: str
    action: SmartMoneyAction
    confidence: float
    volume_anomaly: float
    price_impact: float
    institutional_indicators: List[str]
    time_horizon: str  # intraday/daily/weekly
    related_assets: List[str]

@dataclass
class LiquidityAnalysis:
    """Liquidity zone analysis"""
    symbol: str
    timestamp: datetime
    event_type: LiquidityEvent
    price_level: float
    volume_spike: float
    liquidity_depth: float
    market_impact: float
    recovery_time_minutes: int
    follow_through_probability: float

@dataclass
class CorrelationAlert:
    """Correlation storm alert"""
    timestamp: datetime
    state: CorrelationState
    affected_pairs: List[str]
    correlation_strength: float
    duration_minutes: int
    risk_multiplier: float
    recommended_action: str
    confidence: float

@dataclass
class CrossAssetSignal:
    """Cross-asset analysis signal"""
    primary_asset: str
    related_assets: List[str]
    signal_strength: float
    direction: str
    catalyst: str  # bonds/commodities/equities/crypto
    time_lag_minutes: int
    reliability_score: float

class InstitutionalIntelligence:
    """
    Advanced market intelligence engine for institutional-grade analysis
    Tracks smart money, detects correlation storms, analyzes cross-asset flows
    """
    
    def __init__(self):
        self.smart_money_signals: List[SmartMoneySignal] = []
        self.liquidity_events: List[LiquidityAnalysis] = []
        self.correlation_alerts: List[CorrelationAlert] = []
        self.cross_asset_signals: List[CrossAssetSignal] = []
        
        # Analysis parameters
        self.volume_anomaly_threshold = 2.5  # 2.5x normal volume
        self.correlation_threshold = 0.8  # 80% correlation for alerts
        self.liquidity_impact_threshold = 0.5  # 50 pips for major pairs
        
        # Market data cache
        self.market_data_cache = {}
        self.volume_profiles = {}
        self.correlation_matrix = {}
        
        # Institutional indicators
        self.institutional_patterns = {
            "block_trades": {"min_volume": 10000000, "time_concentration": 300},  # 5 minutes
            "iceberg_orders": {"volume_fragments": 5, "price_levels": 3},
            "sweep_patterns": {"liquidity_zones": 2, "follow_through": 0.7},
            "dark_pool_prints": {"size_threshold": 1000000, "frequency": 60}
        }
        
        logger.info("Institutional Intelligence Engine initialized")
    
    def analyze_market_structure(self, symbol: str, timeframe: str = "M5") -> Dict[str, Any]:
        """
        Comprehensive market structure analysis
        Returns institutional activity, liquidity events, and correlation data
        """
        analysis_start = time.time()
        
        # 1. Smart Money Detection
        smart_money_activity = self._detect_smart_money_activity(symbol, timeframe)
        
        # 2. Liquidity Analysis
        liquidity_analysis = self._analyze_liquidity_zones(symbol, timeframe)
        
        # 3. Correlation Storm Detection
        correlation_state = self._detect_correlation_storms(symbol)
        
        # 4. Cross-Asset Analysis
        cross_asset_signals = self._analyze_cross_asset_flows(symbol)
        
        # 5. Volume Profile Analysis
        volume_profile = self._analyze_volume_profile(symbol, timeframe)
        
        # 6. Order Flow Intelligence
        order_flow = self._analyze_order_flow_patterns(symbol)
        
        analysis_time = time.time() - analysis_start
        
        return {
            "symbol": symbol,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_time_ms": int(analysis_time * 1000),
            "smart_money": {
                "current_activity": smart_money_activity["current_action"].value if smart_money_activity else "neutral",
                "confidence": smart_money_activity["confidence"] if smart_money_activity else 0.5,
                "signals": [asdict(signal) for signal in smart_money_activity.get("signals", [])],
                "institutional_indicators": smart_money_activity.get("indicators", [])
            },
            "liquidity": {
                "current_state": liquidity_analysis["state"],
                "key_levels": liquidity_analysis["levels"],
                "recent_events": [asdict(event) for event in liquidity_analysis.get("events", [])],
                "sweep_probability": liquidity_analysis.get("sweep_probability", 0.3)
            },
            "correlation": {
                "state": correlation_state["state"].value,
                "strength": correlation_state["strength"],
                "affected_pairs": correlation_state["affected_pairs"],
                "risk_multiplier": correlation_state["risk_multiplier"],
                "alert_active": correlation_state["alert_active"]
            },
            "cross_asset": {
                "primary_drivers": cross_asset_signals["drivers"],
                "signals": [asdict(signal) for signal in cross_asset_signals.get("signals", [])],
                "strength": cross_asset_signals.get("overall_strength", 0.5)
            },
            "volume_profile": volume_profile,
            "order_flow": order_flow,
            "overall_intelligence_score": self._calculate_intelligence_score(
                smart_money_activity, liquidity_analysis, correlation_state, cross_asset_signals
            )
        }
    
    def _detect_smart_money_activity(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Detect institutional smart money activity"""
        
        # Simulate institutional detection - in production would use real data
        current_time = datetime.now()
        
        # Check for volume anomalies
        volume_anomalies = self._detect_volume_anomalies(symbol, timeframe)
        
        # Check for block trade patterns
        block_trades = self._detect_block_trades(symbol)
        
        # Check for iceberg order patterns
        iceberg_patterns = self._detect_iceberg_orders(symbol)
        
        # Check for dark pool activity
        dark_pool_activity = self._detect_dark_pool_prints(symbol)
        
        # Determine primary smart money action
        indicators = []
        confidence = 0.5
        current_action = SmartMoneyAction.SPECULATION
        
        if volume_anomalies["detected"]:
            indicators.append("volume_spike")
            confidence += 0.2
            
        if block_trades["detected"]:
            indicators.append("block_trades")
            confidence += 0.3
            current_action = SmartMoneyAction.ACCUMULATION
            
        if iceberg_patterns["detected"]:
            indicators.append("iceberg_orders")
            confidence += 0.2
            
        if dark_pool_activity["detected"]:
            indicators.append("dark_pool_prints")
            confidence += 0.25
            current_action = SmartMoneyAction.DISTRIBUTION
        
        # Create smart money signals
        signals = []
        if confidence > 0.7:
            signals.append(SmartMoneySignal(
                timestamp=current_time,
                symbol=symbol,
                action=current_action,
                confidence=min(0.95, confidence),
                volume_anomaly=volume_anomalies.get("multiplier", 1.0),
                price_impact=self._calculate_price_impact(symbol),
                institutional_indicators=indicators,
                time_horizon="intraday",
                related_assets=self._get_related_assets(symbol)
            ))
        
        return {
            "current_action": current_action,
            "confidence": min(0.95, confidence),
            "signals": signals,
            "indicators": indicators,
            "volume_anomaly": volume_anomalies,
            "block_trades": block_trades,
            "dark_pool_activity": dark_pool_activity
        }
    
    def _analyze_liquidity_zones(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Analyze liquidity zones and potential sweep events"""
        
        # Get recent price action for liquidity analysis
        price_levels = self._get_key_price_levels(symbol)
        
        # Identify liquidity zones
        liquidity_zones = []
        for level in price_levels:
            liquidity_zones.append({
                "price": level["price"],
                "strength": level["strength"],
                "type": level["type"],  # support/resistance/pivot
                "volume": level.get("volume", 0),
                "touch_count": level.get("touches", 1)
            })
        
        # Detect recent liquidity events
        recent_events = []
        
        # Check for liquidity sweeps
        sweep_probability = self._calculate_sweep_probability(symbol, liquidity_zones)
        if sweep_probability > 0.6:
            recent_events.append(LiquidityAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                event_type=LiquidityEvent.SWEEP,
                price_level=liquidity_zones[0]["price"] if liquidity_zones else 0,
                volume_spike=2.5,
                liquidity_depth=liquidity_zones[0]["strength"] if liquidity_zones else 1.0,
                market_impact=self._calculate_market_impact(symbol),
                recovery_time_minutes=15,
                follow_through_probability=0.75
            ))
        
        # Check for liquidity voids
        void_probability = self._detect_liquidity_voids(symbol)
        if void_probability > 0.5:
            recent_events.append(LiquidityAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                event_type=LiquidityEvent.VOID,
                price_level=0,  # Would be calculated from actual data
                volume_spike=0.3,  # Low volume = void
                liquidity_depth=0.2,
                market_impact=1.8,
                recovery_time_minutes=45,
                follow_through_probability=0.4
            ))
        
        return {
            "state": "normal" if not recent_events else "active",
            "levels": liquidity_zones[:5],  # Top 5 levels
            "events": recent_events,
            "sweep_probability": sweep_probability,
            "void_risk": void_probability
        }
    
    def _detect_correlation_storms(self, symbol: str) -> Dict[str, Any]:
        """Detect correlation storms across currency pairs"""
        
        # Define major currency pairs for correlation analysis
        major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]
        
        # Calculate current correlations
        correlations = {}
        high_correlations = []
        
        for pair in major_pairs:
            if pair != symbol:
                correlation = self._calculate_pair_correlation(symbol, pair)
                correlations[pair] = correlation
                
                if abs(correlation) > self.correlation_threshold:
                    high_correlations.append({
                        "pair": pair,
                        "correlation": correlation,
                        "strength": "strong" if abs(correlation) > 0.9 else "moderate"
                    })
        
        # Determine correlation state
        correlation_state = CorrelationState.NORMAL
        risk_multiplier = 1.0
        alert_active = False
        
        if len(high_correlations) >= 4:
            correlation_state = CorrelationState.CORRELATION_STORM
            risk_multiplier = 2.5
            alert_active = True
        elif len(high_correlations) >= 2:
            correlation_state = CorrelationState.HIGH_CORRELATION
            risk_multiplier = 1.8
            alert_active = True
        
        # Create correlation alert if needed
        if alert_active:
            alert = CorrelationAlert(
                timestamp=datetime.now(),
                state=correlation_state,
                affected_pairs=[hc["pair"] for hc in high_correlations],
                correlation_strength=statistics.mean([abs(hc["correlation"]) for hc in high_correlations]),
                duration_minutes=30,  # Estimated duration
                risk_multiplier=risk_multiplier,
                recommended_action=self._get_correlation_recommendation(correlation_state),
                confidence=0.8
            )
            self.correlation_alerts.append(alert)
        
        return {
            "state": correlation_state,
            "strength": statistics.mean([abs(corr) for corr in correlations.values()]) if correlations else 0,
            "affected_pairs": [hc["pair"] for hc in high_correlations],
            "risk_multiplier": risk_multiplier,
            "alert_active": alert_active,
            "correlations": correlations,
            "high_correlations": high_correlations
        }
    
    def _analyze_cross_asset_flows(self, symbol: str) -> Dict[str, Any]:
        """Analyze cross-asset flows affecting forex"""
        
        # Define cross-asset relationships
        cross_asset_map = {
            "EURUSD": ["EUR/USD Bond Yield Spread", "DXY", "SPX", "Gold"],
            "GBPUSD": ["UK Gilt Yields", "DXY", "FTSE", "Oil"],
            "USDJPY": ["US-Japan Yield Spread", "Nikkei", "SPX", "Gold"],
            "AUDUSD": ["RBA Cash Rate", "Iron Ore", "Gold", "ASX"],
            "USDCAD": ["Oil Prices", "BoC Rate", "TSX", "Gold"],
            "XAUUSD": ["Real Yields", "DXY", "SPX", "VIX"]
        }
        
        related_assets = cross_asset_map.get(symbol, ["DXY", "SPX", "Gold"])
        
        # Analyze each related asset
        cross_asset_signals = []
        primary_drivers = []
        
        for asset in related_assets:
            signal_strength = self._calculate_cross_asset_signal_strength(symbol, asset)
            
            if signal_strength > 0.6:
                direction = "bullish" if signal_strength > 0 else "bearish"
                
                cross_asset_signals.append(CrossAssetSignal(
                    primary_asset=symbol,
                    related_assets=[asset],
                    signal_strength=abs(signal_strength),
                    direction=direction,
                    catalyst=self._identify_catalyst(asset),
                    time_lag_minutes=self._estimate_time_lag(symbol, asset),
                    reliability_score=self._calculate_reliability_score(symbol, asset)
                ))
                
                primary_drivers.append({
                    "asset": asset,
                    "impact": signal_strength,
                    "catalyst": self._identify_catalyst(asset)
                })
        
        # Calculate overall cross-asset strength
        overall_strength = statistics.mean([signal.signal_strength for signal in cross_asset_signals]) if cross_asset_signals else 0.3
        
        return {
            "drivers": primary_drivers[:3],  # Top 3 drivers
            "signals": cross_asset_signals,
            "overall_strength": overall_strength,
            "related_assets": related_assets
        }
    
    def _analyze_volume_profile(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Analyze volume profile for institutional activity"""
        
        # Simulate volume profile analysis
        volume_data = {
            "total_volume": 1250000,  # Total volume
            "average_volume": 850000,  # Average volume
            "volume_ratio": 1.47,  # Current vs average
            "poc_price": 1.0847,  # Point of Control
            "value_area_high": 1.0865,
            "value_area_low": 1.0832,
            "volume_nodes": [
                {"price": 1.0847, "volume": 180000, "type": "high_volume_node"},
                {"price": 1.0855, "volume": 150000, "type": "high_volume_node"},
                {"price": 1.0840, "volume": 45000, "type": "low_volume_node"}
            ]
        }
        
        # Identify institutional volume patterns
        institutional_patterns = []
        
        if volume_data["volume_ratio"] > 2.0:
            institutional_patterns.append("volume_spike")
        
        if len([node for node in volume_data["volume_nodes"] if node["type"] == "high_volume_node"]) > 2:
            institutional_patterns.append("multiple_absorption_zones")
        
        return {
            **volume_data,
            "institutional_patterns": institutional_patterns,
            "analysis_confidence": 0.75
        }
    
    def _analyze_order_flow_patterns(self, symbol: str) -> Dict[str, Any]:
        """Analyze order flow for institutional patterns"""
        
        # Simulate order flow analysis
        order_flow = {
            "bid_ask_spread": 1.2,  # pips
            "market_depth": {
                "bid_depth": 25000000,
                "ask_depth": 22000000,
                "imbalance": 0.12  # 12% bid heavy
            },
            "trade_size_distribution": {
                "retail_percent": 65,
                "institutional_percent": 35,
                "block_trades": 8  # Count of block trades
            },
            "order_flow_imbalance": 0.15,  # 15% buy side
            "aggressive_orders": {
                "buy_aggression": 0.68,
                "sell_aggression": 0.32
            }
        }
        
        # Identify patterns
        patterns = []
        
        if order_flow["market_depth"]["imbalance"] > 0.1:
            patterns.append("depth_imbalance")
        
        if order_flow["trade_size_distribution"]["block_trades"] > 5:
            patterns.append("institutional_activity")
        
        if order_flow["order_flow_imbalance"] > 0.1:
            patterns.append("directional_bias")
        
        return {
            **order_flow,
            "identified_patterns": patterns,
            "institutional_probability": 0.7 if "institutional_activity" in patterns else 0.3
        }
    
    def _calculate_intelligence_score(self, smart_money: Dict, liquidity: Dict, 
                                    correlation: Dict, cross_asset: Dict) -> float:
        """Calculate overall institutional intelligence score"""
        
        scores = []
        
        # Smart money component
        if smart_money and smart_money.get("confidence", 0) > 0.6:
            scores.append(smart_money["confidence"] * 0.3)
        else:
            scores.append(0.15)
        
        # Liquidity component
        if liquidity.get("sweep_probability", 0) > 0.5:
            scores.append(liquidity["sweep_probability"] * 0.25)
        else:
            scores.append(0.1)
        
        # Correlation component
        correlation_score = 0.2
        if correlation["state"] == CorrelationState.CORRELATION_STORM:
            correlation_score = 0.9
        elif correlation["state"] == CorrelationState.HIGH_CORRELATION:
            correlation_score = 0.7
        scores.append(correlation_score * 0.2)
        
        # Cross-asset component
        scores.append(cross_asset.get("overall_strength", 0.3) * 0.25)
        
        return min(1.0, sum(scores))
    
    # Helper methods for institutional detection
    def _detect_volume_anomalies(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Detect volume anomalies indicating institutional activity"""
        # Simulate volume anomaly detection
        current_volume = 1250000
        average_volume = 850000
        multiplier = current_volume / average_volume
        
        return {
            "detected": multiplier > self.volume_anomaly_threshold,
            "multiplier": multiplier,
            "current_volume": current_volume,
            "average_volume": average_volume,
            "threshold": self.volume_anomaly_threshold
        }
    
    def _detect_block_trades(self, symbol: str) -> Dict[str, Any]:
        """Detect block trades indicating institutional activity"""
        # Simulate block trade detection
        block_trades_count = 3
        min_threshold = self.institutional_patterns["block_trades"]["min_volume"]
        
        return {
            "detected": block_trades_count > 2,
            "count": block_trades_count,
            "threshold": min_threshold,
            "largest_block": 15000000
        }
    
    def _detect_iceberg_orders(self, symbol: str) -> Dict[str, Any]:
        """Detect iceberg order patterns"""
        # Simulate iceberg detection
        fragments_detected = 4
        price_levels = 2
        
        return {
            "detected": fragments_detected >= self.institutional_patterns["iceberg_orders"]["volume_fragments"],
            "fragments": fragments_detected,
            "price_levels": price_levels,
            "pattern_strength": 0.7
        }
    
    def _detect_dark_pool_prints(self, symbol: str) -> Dict[str, Any]:
        """Detect dark pool print activity"""
        # Simulate dark pool detection
        prints_count = 2
        average_size = 2500000
        
        return {
            "detected": prints_count > 1 and average_size > self.institutional_patterns["dark_pool_prints"]["size_threshold"],
            "prints_count": prints_count,
            "average_size": average_size,
            "total_volume": prints_count * average_size
        }
    
    def _calculate_price_impact(self, symbol: str) -> float:
        """Calculate price impact of institutional activity"""
        # Simulate price impact calculation
        base_impacts = {
            "EURUSD": 0.0008, "GBPUSD": 0.0012, "USDJPY": 0.08,
            "USDCAD": 0.0015, "AUDUSD": 0.0018, "XAUUSD": 2.5
        }
        return base_impacts.get(symbol, 0.001)
    
    def _get_related_assets(self, symbol: str) -> List[str]:
        """Get assets related to the symbol"""
        related_map = {
            "EURUSD": ["GBPUSD", "EURGBP", "EURJPY"],
            "GBPUSD": ["EURUSD", "EURGBP", "GBPJPY"],
            "USDJPY": ["EURJPY", "GBPJPY", "AUDJPY"],
            "XAUUSD": ["XAGUSD", "DXY", "US10Y"]
        }
        return related_map.get(symbol, [])
    
    def _get_key_price_levels(self, symbol: str) -> List[Dict[str, Any]]:
        """Get key price levels for liquidity analysis"""
        # Simulate key levels - in production would calculate from real data
        return [
            {"price": 1.0850, "strength": 0.8, "type": "resistance", "touches": 3},
            {"price": 1.0825, "strength": 0.9, "type": "support", "touches": 4},
            {"price": 1.0875, "strength": 0.6, "type": "resistance", "touches": 2}
        ]
    
    def _calculate_sweep_probability(self, symbol: str, liquidity_zones: List[Dict]) -> float:
        """Calculate probability of liquidity sweep"""
        if not liquidity_zones:
            return 0.3
        
        # Higher probability if multiple weak levels nearby
        weak_levels = [zone for zone in liquidity_zones if zone["strength"] < 0.7]
        return min(0.9, 0.3 + (len(weak_levels) * 0.15))
    
    def _detect_liquidity_voids(self, symbol: str) -> float:
        """Detect liquidity void probability"""
        # Simulate void detection
        return 0.4  # 40% probability
    
    def _calculate_market_impact(self, symbol: str) -> float:
        """Calculate market impact factor"""
        # Market impact in pips
        impacts = {
            "EURUSD": 15, "GBPUSD": 20, "USDJPY": 18,
            "USDCAD": 25, "AUDUSD": 22, "XAUUSD": 8
        }
        return impacts.get(symbol, 20)
    
    def _calculate_pair_correlation(self, symbol1: str, symbol2: str) -> float:
        """Calculate correlation between two currency pairs"""
        # Simulate correlation calculation
        # In production, would calculate from real price data
        correlation_matrix = {
            ("EURUSD", "GBPUSD"): 0.75,
            ("EURUSD", "AUDUSD"): 0.68,
            ("GBPUSD", "AUDUSD"): 0.72,
            ("USDJPY", "USDCAD"): 0.45,
            ("EURUSD", "USDCHF"): -0.82
        }
        
        key = (symbol1, symbol2) if (symbol1, symbol2) in correlation_matrix else (symbol2, symbol1)
        return correlation_matrix.get(key, 0.3)  # Default low correlation
    
    def _get_correlation_recommendation(self, state: CorrelationState) -> str:
        """Get recommendation based on correlation state"""
        recommendations = {
            CorrelationState.CORRELATION_STORM: "Reduce position sizes across correlated pairs",
            CorrelationState.HIGH_CORRELATION: "Monitor correlated pairs for risk management",
            CorrelationState.NORMAL: "Normal correlation levels - proceed as planned",
            CorrelationState.DECOUPLING: "Opportunity for pair-specific strategies"
        }
        return recommendations.get(state, "Monitor correlation levels")
    
    def _calculate_cross_asset_signal_strength(self, forex_symbol: str, asset: str) -> float:
        """Calculate signal strength from cross-asset analysis"""
        # Simulate cross-asset signal strength
        strength_map = {
            ("EURUSD", "DXY"): -0.85,  # Strong negative correlation
            ("EURUSD", "SPX"): 0.62,   # Moderate positive correlation
            ("XAUUSD", "DXY"): -0.78,  # Strong negative correlation
            ("GBPUSD", "Oil"): 0.45,   # Moderate positive correlation
            ("AUDUSD", "Gold"): 0.55   # Moderate positive correlation
        }
        
        key = (forex_symbol, asset)
        return strength_map.get(key, 0.3)  # Default weak signal
    
    def _identify_catalyst(self, asset: str) -> str:
        """Identify the catalyst type for cross-asset move"""
        catalyst_map = {
            "DXY": "monetary_policy",
            "SPX": "risk_sentiment", 
            "Gold": "inflation_hedge",
            "Oil": "commodity_demand",
            "US10Y": "interest_rates"
        }
        return catalyst_map.get(asset, "unknown")
    
    def _estimate_time_lag(self, forex_symbol: str, asset: str) -> int:
        """Estimate time lag between asset move and forex impact"""
        # Time lag in minutes
        lag_map = {
            ("EURUSD", "DXY"): 5,      # Very fast
            ("EURUSD", "SPX"): 15,     # Fast
            ("XAUUSD", "DXY"): 3,      # Very fast
            ("AUDUSD", "Gold"): 30,    # Slower
            ("GBPUSD", "Oil"): 45      # Slower
        }
        
        key = (forex_symbol, asset)
        return lag_map.get(key, 20)  # Default 20 minutes
    
    def _calculate_reliability_score(self, forex_symbol: str, asset: str) -> float:
        """Calculate reliability of cross-asset signal"""
        # Historical reliability
        reliability_map = {
            ("EURUSD", "DXY"): 0.88,
            ("XAUUSD", "DXY"): 0.85,
            ("AUDUSD", "Gold"): 0.72,
            ("GBPUSD", "Oil"): 0.65
        }
        
        key = (forex_symbol, asset)
        return reliability_map.get(key, 0.6)  # Default reliability
    
    def get_institutional_summary(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive institutional intelligence summary"""
        
        analysis = self.analyze_market_structure(symbol)
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "intelligence_grade": "A" if analysis["overall_intelligence_score"] > 0.8 else 
                                "B" if analysis["overall_intelligence_score"] > 0.6 else
                                "C" if analysis["overall_intelligence_score"] > 0.4 else "D",
            "key_insights": self._generate_key_insights(analysis),
            "risk_alerts": self._generate_risk_alerts(analysis),
            "opportunities": self._identify_opportunities(analysis),
            "institutional_bias": self._determine_institutional_bias(analysis),
            "confidence_level": analysis["overall_intelligence_score"]
        }
    
    def _generate_key_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key insights from analysis"""
        insights = []
        
        if analysis["smart_money"]["confidence"] > 0.7:
            action = analysis["smart_money"]["current_activity"]
            insights.append(f"Strong institutional {action} detected with {analysis['smart_money']['confidence']:.1%} confidence")
        
        if analysis["correlation"]["alert_active"]:
            state = analysis["correlation"]["state"]
            insights.append(f"Correlation {state} active - Risk multiplier: {analysis['correlation']['risk_multiplier']:.1f}x")
        
        if analysis["liquidity"]["sweep_probability"] > 0.6:
            insights.append(f"High liquidity sweep probability ({analysis['liquidity']['sweep_probability']:.1%})")
        
        if analysis["cross_asset"].get("overall_strength", 0) > 0.7:
            drivers = analysis["cross_asset"]["primary_drivers"]
            if drivers:
                insights.append(f"Strong cross-asset signal from {drivers[0]['asset']}")
        
        return insights[:3]  # Top 3 insights
    
    def _generate_risk_alerts(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate risk alerts from analysis"""
        alerts = []
        
        if analysis["correlation"]["state"] == "correlation_storm":
            alerts.append("⚠️ CORRELATION STORM: Reduce position sizes across all pairs")
        
        if analysis["liquidity"]["sweep_probability"] > 0.8:
            alerts.append("🚨 LIQUIDITY SWEEP IMMINENT: Expect volatile price action")
        
        if analysis["volume_profile"]["volume_ratio"] > 3.0:
            alerts.append("📊 EXTREME VOLUME: Institutional activity likely")
        
        return alerts
    
    def _identify_opportunities(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify trading opportunities from analysis"""
        opportunities = []
        
        if (analysis["smart_money"]["current_activity"] == "accumulation" and 
            analysis["smart_money"]["confidence"] > 0.8):
            opportunities.append("💡 Follow smart money accumulation - Bullish bias")
        
        if analysis["liquidity"].get("void_risk", 0) > 0.6:
            opportunities.append("🎯 Liquidity void detected - Expect rapid price movement")
        
        if (analysis["cross_asset"]["overall_strength"] > 0.7 and 
            len(analysis["cross_asset"]["primary_drivers"]) >= 2):
            opportunities.append("🔗 Strong cross-asset confluence - High probability setup")
        
        return opportunities
    
    def _determine_institutional_bias(self, analysis: Dict[str, Any]) -> str:
        """Determine overall institutional bias"""
        
        bias_factors = []
        
        # Smart money bias
        smart_money_action = analysis["smart_money"]["current_activity"]
        if smart_money_action == "accumulation":
            bias_factors.append("bullish")
        elif smart_money_action == "distribution":
            bias_factors.append("bearish")
        
        # Cross-asset bias
        primary_drivers = analysis["cross_asset"]["primary_drivers"]
        for driver in primary_drivers:
            if driver["impact"] > 0.6:
                bias_factors.append("bullish")
            elif driver["impact"] < -0.6:
                bias_factors.append("bearish")
        
        # Determine overall bias
        bullish_count = bias_factors.count("bullish")
        bearish_count = bias_factors.count("bearish")
        
        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        else:
            return "neutral"

# Helper function for integration
def get_institutional_intelligence() -> InstitutionalIntelligence:
    """Get institutional intelligence engine"""
    return InstitutionalIntelligence()