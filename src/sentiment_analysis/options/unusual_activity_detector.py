"""
Unusual Options Activity Detector

Specialized module for detecting and analyzing unusual options activity
patterns that may indicate institutional or insider trading.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import logging
from collections import defaultdict
import asyncio
import statistics

from .options_flow_analyzer import OptionsFlowAnalyzer, OptionsFlow, UnusualOption

logger = logging.getLogger(__name__)


@dataclass
class UnusualPattern:
    """Unusual options pattern data"""
    pattern_type: str
    confidence: float
    symbols: List[str]
    description: str
    sentiment: str
    urgency: str  # 'high', 'medium', 'low'
    details: Dict[str, any]
    

class UnusualActivityDetector:
    """
    Advanced detector for unusual options activity patterns
    """
    
    def __init__(self, options_analyzer: Optional[OptionsFlowAnalyzer] = None):
        """
        Initialize unusual activity detector
        
        Args:
            options_analyzer: Options flow analyzer instance
        """
        self.analyzer = options_analyzer or OptionsFlowAnalyzer()
        
        # Pattern detection thresholds
        self.patterns = {
            'golden_sweep': {
                'min_contracts': 500,
                'time_window': 300,  # 5 minutes
                'min_exchanges': 3
            },
            'repeated_buying': {
                'min_occurrences': 3,
                'time_window': 3600,  # 1 hour
                'same_strike_threshold': 0.9
            },
            'volatility_crush_play': {
                'iv_percentile': 80,
                'days_to_event': 5,
                'min_volume': 1000
            },
            'insider_pattern': {
                'otm_threshold': 0.15,  # 15% OTM
                'volume_oi_ratio': 10,
                'min_value': 100000
            },
            'whale_accumulation': {
                'min_value': 500000,
                'time_window': 7200,  # 2 hours
                'same_direction': True
            }
        }
        
        # Historical patterns for comparison
        self.historical_patterns = defaultdict(list)
        
    async def detect_unusual_patterns(
        self,
        lookback_hours: int = 24,
        min_confidence: float = 0.7
    ) -> List[UnusualPattern]:
        """
        Detect unusual options patterns across the market
        
        Args:
            lookback_hours: Hours to analyze
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of detected unusual patterns
        """
        try:
            # Get market-wide options flow
            flow_data = await self.analyzer._get_market_flow(lookback_hours)
            
            # Detect various patterns
            patterns = []
            
            # Golden sweep detection
            golden_sweeps = await self._detect_golden_sweeps(flow_data)
            patterns.extend(golden_sweeps)
            
            # Repeated buying patterns
            repeated_patterns = self._detect_repeated_buying(flow_data)
            patterns.extend(repeated_patterns)
            
            # Volatility plays
            vol_plays = self._detect_volatility_plays(flow_data)
            patterns.extend(vol_plays)
            
            # Potential insider patterns
            insider_patterns = self._detect_insider_patterns(flow_data)
            patterns.extend(insider_patterns)
            
            # Whale accumulation
            whale_patterns = self._detect_whale_accumulation(flow_data)
            patterns.extend(whale_patterns)
            
            # Filter by confidence
            high_confidence_patterns = [
                p for p in patterns 
                if p.confidence >= min_confidence
            ]
            
            # Sort by urgency and confidence
            high_confidence_patterns.sort(
                key=lambda x: (
                    {'high': 3, 'medium': 2, 'low': 1}[x.urgency],
                    x.confidence
                ),
                reverse=True
            )
            
            return high_confidence_patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    async def analyze_symbol_patterns(
        self,
        symbol: str,
        lookback_hours: int = 48
    ) -> Dict[str, any]:
        """
        Detect unusual patterns for specific symbol
        
        Args:
            symbol: Stock symbol
            lookback_hours: Hours to analyze
            
        Returns:
            Symbol-specific pattern analysis
        """
        try:
            # Get symbol options data
            flow_data = await self.analyzer._get_options_flow([symbol], lookback_hours)
            
            # Analyze patterns
            results = {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'unusual_score': 0,
                'detected_patterns': [],
                'risk_indicators': [],
                'opportunity_score': 0,
                'recommended_action': None
            }
            
            # Check each pattern type
            patterns = []
            
            # Check for accumulation
            accumulation = self._check_accumulation_pattern(flow_data)
            if accumulation:
                patterns.append(accumulation)
            
            # Check for distribution
            distribution = self._check_distribution_pattern(flow_data)
            if distribution:
                patterns.append(distribution)
            
            # Check for hedging
            hedging = self._check_hedging_pattern(flow_data)
            if hedging:
                patterns.append(hedging)
            
            # Calculate scores
            if patterns:
                results['detected_patterns'] = patterns
                results['unusual_score'] = max(p.confidence for p in patterns) * 100
                
                # Determine opportunity
                bullish_patterns = [p for p in patterns if p.sentiment == 'bullish']
                bearish_patterns = [p for p in patterns if p.sentiment == 'bearish']
                
                if bullish_patterns and not bearish_patterns:
                    results['opportunity_score'] = max(p.confidence for p in bullish_patterns) * 100
                    results['recommended_action'] = 'consider_long'
                elif bearish_patterns and not bullish_patterns:
                    results['opportunity_score'] = max(p.confidence for p in bearish_patterns) * 100
                    results['recommended_action'] = 'consider_short'
                else:
                    results['recommended_action'] = 'wait_for_clarity'
            
            # Add risk indicators
            results['risk_indicators'] = self._assess_risk_indicators(flow_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol} patterns: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def _detect_golden_sweeps(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[UnusualPattern]:
        """Detect golden sweep patterns (rapid multi-exchange buying)"""
        patterns = []
        
        # Group by symbol and time windows
        time_windows = defaultdict(lambda: defaultdict(list))
        
        for flow in flow_data:
            # Create 5-minute windows
            window = flow.timestamp.replace(
                minute=flow.timestamp.minute // 5 * 5,
                second=0,
                microsecond=0
            )
            time_windows[flow.symbol][window].append(flow)
        
        # Check each symbol's windows
        for symbol, windows in time_windows.items():
            for window_time, flows in windows.items():
                # Check for sweep characteristics
                if len(flows) >= 3:  # Multiple trades
                    total_volume = sum(f.volume for f in flows)
                    
                    if total_volume >= self.patterns['golden_sweep']['min_contracts']:
                        # Check if same direction
                        call_count = sum(1 for f in flows if f.option_type == 'call')
                        put_count = len(flows) - call_count
                        
                        if call_count > put_count * 2 or put_count > call_count * 2:
                            direction = 'call' if call_count > put_count else 'put'
                            
                            pattern = UnusualPattern(
                                pattern_type='golden_sweep',
                                confidence=0.85,
                                symbols=[symbol],
                                description=f"Golden sweep detected: {total_volume} {direction}s in 5 minutes",
                                sentiment='bullish' if direction == 'call' else 'bearish',
                                urgency='high',
                                details={
                                    'volume': total_volume,
                                    'trade_count': len(flows),
                                    'direction': direction,
                                    'time': window_time.isoformat()
                                }
                            )
                            patterns.append(pattern)
        
        return patterns
    
    def _detect_repeated_buying(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[UnusualPattern]:
        """Detect repeated buying at same strikes"""
        patterns = []
        
        # Group by symbol, strike, and type
        strike_activity = defaultdict(lambda: defaultdict(list))
        
        for flow in flow_data:
            key = (flow.symbol, flow.strike, flow.option_type)
            strike_activity[flow.symbol][key].append(flow)
        
        # Check for repeated activity
        for symbol, strikes in strike_activity.items():
            for (sym, strike, opt_type), flows in strikes.items():
                if len(flows) >= self.patterns['repeated_buying']['min_occurrences']:
                    # Check time distribution
                    time_span = (
                        max(f.timestamp for f in flows) - 
                        min(f.timestamp for f in flows)
                    ).total_seconds()
                    
                    if time_span > 300:  # Not all at once
                        total_volume = sum(f.volume for f in flows)
                        total_value = sum(f.volume * f.last_price * 100 for f in flows)
                        
                        pattern = UnusualPattern(
                            pattern_type='repeated_buying',
                            confidence=0.75,
                            symbols=[symbol],
                            description=f"Repeated {opt_type} buying at ${strike} strike",
                            sentiment='bullish' if opt_type == 'call' else 'bearish',
                            urgency='medium',
                            details={
                                'strike': strike,
                                'type': opt_type,
                                'occurrences': len(flows),
                                'total_volume': total_volume,
                                'total_value': total_value,
                                'time_span_minutes': time_span / 60
                            }
                        )
                        patterns.append(pattern)
        
        return patterns
    
    def _detect_volatility_plays(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[UnusualPattern]:
        """Detect volatility-based plays (straddles, strangles)"""
        patterns = []
        
        # Group by symbol and expiry
        symbol_expiry = defaultdict(lambda: defaultdict(list))
        
        for flow in flow_data:
            key = (flow.symbol, flow.expiry)
            symbol_expiry[key[0]][key[1]].append(flow)
        
        # Check for vol plays
        for symbol, expiries in symbol_expiry.items():
            for expiry, flows in expiries.items():
                # Separate calls and puts
                calls = [f for f in flows if f.option_type == 'call']
                puts = [f for f in flows if f.option_type == 'put']
                
                if calls and puts:
                    # Check for similar volume
                    call_volume = sum(f.volume for f in calls)
                    put_volume = sum(f.volume for f in puts)
                    
                    ratio = min(call_volume, put_volume) / max(call_volume, put_volume)
                    
                    if ratio > 0.7:  # Similar volumes
                        # Check for high IV
                        avg_iv = np.mean([f.implied_volatility for f in flows])
                        
                        if avg_iv > 0.5:  # 50% IV
                            pattern = UnusualPattern(
                                pattern_type='volatility_play',
                                confidence=0.8,
                                symbols=[symbol],
                                description=f"Volatility play detected - possible straddle/strangle",
                                sentiment='neutral',
                                urgency='medium',
                                details={
                                    'expiry': expiry.isoformat(),
                                    'call_volume': call_volume,
                                    'put_volume': put_volume,
                                    'avg_iv': avg_iv,
                                    'strategy': 'straddle' if ratio > 0.9 else 'strangle'
                                }
                            )
                            patterns.append(pattern)
        
        return patterns
    
    def _detect_insider_patterns(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[UnusualPattern]:
        """Detect potential insider-like patterns"""
        patterns = []
        
        for flow in flow_data:
            # Check for far OTM large trades
            # This is simplified - real detection would need stock price
            if flow.volume > 1000:
                value = flow.volume * flow.last_price * 100
                
                if value > self.patterns['insider_pattern']['min_value']:
                    # Check volume/OI ratio
                    if flow.open_interest > 0:
                        vol_oi_ratio = flow.volume / flow.open_interest
                        
                        if vol_oi_ratio > self.patterns['insider_pattern']['volume_oi_ratio']:
                            pattern = UnusualPattern(
                                pattern_type='insider_pattern',
                                confidence=0.7,
                                symbols=[flow.symbol],
                                description=f"Unusual large {flow.option_type} trade detected",
                                sentiment='bullish' if flow.option_type == 'call' else 'bearish',
                                urgency='high',
                                details={
                                    'strike': flow.strike,
                                    'type': flow.option_type,
                                    'volume': flow.volume,
                                    'value': value,
                                    'vol_oi_ratio': vol_oi_ratio,
                                    'expiry': flow.expiry.isoformat()
                                }
                            )
                            patterns.append(pattern)
        
        return patterns
    
    def _detect_whale_accumulation(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[UnusualPattern]:
        """Detect whale accumulation patterns"""
        patterns = []
        
        # Group by symbol
        symbol_flows = defaultdict(list)
        for flow in flow_data:
            symbol_flows[flow.symbol].append(flow)
        
        # Check each symbol
        for symbol, flows in symbol_flows.items():
            # Calculate total value
            call_value = sum(
                f.volume * f.last_price * 100 
                for f in flows 
                if f.option_type == 'call'
            )
            put_value = sum(
                f.volume * f.last_price * 100 
                for f in flows 
                if f.option_type == 'put'
            )
            
            total_value = call_value + put_value
            
            if total_value > self.patterns['whale_accumulation']['min_value']:
                # Determine direction
                if call_value > put_value * 2:
                    direction = 'bullish'
                    sentiment = 'bullish'
                elif put_value > call_value * 2:
                    direction = 'bearish'
                    sentiment = 'bearish'
                else:
                    direction = 'mixed'
                    sentiment = 'neutral'
                
                pattern = UnusualPattern(
                    pattern_type='whale_accumulation',
                    confidence=0.85,
                    symbols=[symbol],
                    description=f"Whale accumulation detected - ${total_value:,.0f} in options",
                    sentiment=sentiment,
                    urgency='high',
                    details={
                        'total_value': total_value,
                        'call_value': call_value,
                        'put_value': put_value,
                        'direction': direction,
                        'trade_count': len(flows)
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
    def _check_accumulation_pattern(
        self, 
        flow_data: List[OptionsFlow]
    ) -> Optional[UnusualPattern]:
        """Check for accumulation pattern in symbol"""
        if not flow_data:
            return None
        
        # Calculate metrics
        call_volume = sum(f.volume for f in flow_data if f.option_type == 'call')
        put_volume = sum(f.volume for f in flow_data if f.option_type == 'put')
        
        if call_volume > put_volume * 3:
            # Strong call accumulation
            total_value = sum(
                f.volume * f.last_price * 100 
                for f in flow_data 
                if f.option_type == 'call'
            )
            
            return UnusualPattern(
                pattern_type='accumulation',
                confidence=0.8,
                symbols=[flow_data[0].symbol],
                description=f"Strong call accumulation detected",
                sentiment='bullish',
                urgency='medium',
                details={
                    'call_volume': call_volume,
                    'put_volume': put_volume,
                    'call_value': total_value,
                    'ratio': call_volume / put_volume if put_volume > 0 else 0
                }
            )
        
        return None
    
    def _check_distribution_pattern(
        self, 
        flow_data: List[OptionsFlow]
    ) -> Optional[UnusualPattern]:
        """Check for distribution pattern"""
        if not flow_data:
            return None
        
        # Look for put buying or call selling indicators
        put_volume = sum(f.volume for f in flow_data if f.option_type == 'put')
        call_volume = sum(f.volume for f in flow_data if f.option_type == 'call')
        
        if put_volume > call_volume * 2:
            total_value = sum(
                f.volume * f.last_price * 100 
                for f in flow_data 
                if f.option_type == 'put'
            )
            
            return UnusualPattern(
                pattern_type='distribution',
                confidence=0.75,
                symbols=[flow_data[0].symbol],
                description=f"Distribution pattern detected - heavy put buying",
                sentiment='bearish',
                urgency='medium',
                details={
                    'put_volume': put_volume,
                    'call_volume': call_volume,
                    'put_value': total_value,
                    'ratio': put_volume / call_volume if call_volume > 0 else 0
                }
            )
        
        return None
    
    def _check_hedging_pattern(
        self, 
        flow_data: List[OptionsFlow]
    ) -> Optional[UnusualPattern]:
        """Check for hedging patterns"""
        if not flow_data:
            return None
        
        # Look for protective put buying
        puts = [f for f in flow_data if f.option_type == 'put']
        
        if puts:
            # Check for OTM puts with high volume
            otm_puts = [p for p in puts if p.delta and abs(p.delta) < 0.3]
            
            if otm_puts:
                total_volume = sum(p.volume for p in otm_puts)
                
                if total_volume > 1000:
                    return UnusualPattern(
                        pattern_type='hedging',
                        confidence=0.7,
                        symbols=[flow_data[0].symbol],
                        description=f"Hedging activity detected - protective put buying",
                        sentiment='cautious',
                        urgency='low',
                        details={
                            'put_volume': total_volume,
                            'otm_put_count': len(otm_puts),
                            'avg_delta': np.mean([abs(p.delta) for p in otm_puts if p.delta])
                        }
                    )
        
        return None
    
    def _assess_risk_indicators(
        self, 
        flow_data: List[OptionsFlow]
    ) -> List[Dict[str, any]]:
        """Assess risk indicators from options flow"""
        indicators = []
        
        if not flow_data:
            return indicators
        
        # High IV indicator
        avg_iv = np.mean([f.implied_volatility for f in flow_data if f.implied_volatility > 0])
        if avg_iv > 0.6:  # 60% IV
            indicators.append({
                'type': 'high_volatility',
                'severity': 'high',
                'value': avg_iv,
                'description': 'Implied volatility is elevated'
            })
        
        # Volume/OI imbalance
        high_vol_oi = [
            f for f in flow_data 
            if f.open_interest > 0 and f.volume > f.open_interest * 5
        ]
        if len(high_vol_oi) > 5:
            indicators.append({
                'type': 'volume_surge',
                'severity': 'medium',
                'value': len(high_vol_oi),
                'description': 'Multiple strikes showing unusual volume'
            })
        
        # Wide bid-ask spreads
        wide_spreads = [
            f for f in flow_data 
            if f.bid > 0 and (f.ask - f.bid) / f.bid > 0.2
        ]
        if len(wide_spreads) > len(flow_data) * 0.3:
            indicators.append({
                'type': 'liquidity_concern',
                'severity': 'medium',
                'value': len(wide_spreads) / len(flow_data),
                'description': 'Wide bid-ask spreads indicate lower liquidity'
            })
        
        return indicators
    
    async def get_real_time_alerts(
        self,
        min_value: float = 100000,
        callback = None
    ) -> None:
        """
        Monitor for real-time unusual activity alerts
        
        Args:
            min_value: Minimum trade value for alerts
            callback: Function to call with alerts
        """
        logger.info("Starting real-time unusual activity monitoring...")
        
        while True:
            try:
                # Get recent flow (last 5 minutes)
                flow_data = await self.analyzer._get_market_flow(0.083)  # 5 minutes
                
                # Check for unusual activity
                for flow in flow_data:
                    trade_value = flow.volume * flow.last_price * 100
                    
                    if trade_value >= min_value:
                        # Check various alert conditions
                        alerts = []
                        
                        # Large trade alert
                        if trade_value >= 500000:
                            alerts.append({
                                'type': 'large_trade',
                                'symbol': flow.symbol,
                                'value': trade_value,
                                'details': f"{flow.volume} {flow.option_type}s at ${flow.strike}"
                            })
                        
                        # High volume/OI ratio
                        if flow.open_interest > 0 and flow.volume > flow.open_interest * 10:
                            alerts.append({
                                'type': 'unusual_volume',
                                'symbol': flow.symbol,
                                'ratio': flow.volume / flow.open_interest,
                                'details': f"Volume {flow.volume} vs OI {flow.open_interest}"
                            })
                        
                        # Send alerts
                        if alerts and callback:
                            for alert in alerts:
                                await callback(alert)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in real-time monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error