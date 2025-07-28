"""
CITADEL Analyzer - Main entry point for shield analysis

This is the primary interface that coordinates all CITADEL modules to provide
comprehensive signal analysis and protection scoring.
"""

from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime
import os

# Import all CITADEL modules
from .analyzers.signal_inspector import SignalInspector
from .analyzers.market_regime import MarketRegimeAnalyzer
from .analyzers.liquidity_mapper import LiquidityMapper
from .analyzers.cross_tf_validator import CrossTimeframeValidator
from .scoring.shield_engine import ShieldScoringEngine
from .formatters.telegram_formatter import TelegramShieldFormatter
from .storage.shield_logger import ShieldLogger
from .data_stream_enhancer import get_data_enhancer

logger = logging.getLogger(__name__)


class CitadelAnalyzer:
    """
    Main CITADEL analyzer that orchestrates all protection modules.
    
    This class serves as the primary interface for the BITTEN system to
    analyze signals and receive shield protection scores.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize CITADEL analyzer with all modules.
        
        Args:
            config_dir: Optional custom config directory path
        """
        # Set config directory
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), 'config')
        self.config_dir = config_dir
        
        # Load configurations
        self.market_dna = self._load_config('market_dna.json')
        self.scoring_weights = self._load_config('scoring_weights.json')
        
        # Initialize all modules
        self.signal_inspector = SignalInspector()
        self.market_regime_analyzer = MarketRegimeAnalyzer()
        self.liquidity_mapper = LiquidityMapper()
        self.tf_validator = CrossTimeframeValidator()
        self.scoring_engine = ShieldScoringEngine()
        self.telegram_formatter = TelegramShieldFormatter()
        self.shield_logger = ShieldLogger()
        
        # Cache for recent analyses
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("CITADEL Analyzer initialized successfully")
    
    def analyze_signal(self, signal: Dict[str, Any], 
                      market_data: Dict[str, Any],
                      user_id: Optional[int] = None,
                      use_live_data: bool = True) -> Dict[str, Any]:
        """
        Perform complete CITADEL analysis on a trading signal.
        
        Args:
            signal: Trading signal containing pair, direction, entry, sl, tp
            market_data: Current market data including candles, indicators, etc.
            user_id: Optional user ID for personalized analysis
            use_live_data: Whether to enhance with live broker data stream
            
        Returns:
            Complete shield analysis with score, classification, and recommendations
        """
        try:
            signal_id = signal.get('signal_id', self._generate_signal_id(signal))
            
            # Check cache first
            cached = self._get_from_cache(signal_id)
            if cached:
                logger.info(f"Returning cached analysis for {signal_id}")
                return cached
            
            # Get pair-specific market DNA
            pair = signal.get('pair', '')
            pair_dna = self._get_pair_dna(pair)
            
            # Enhance market data with live broker stream if available
            enhanced_market_data = market_data
            if use_live_data:
                enhanced_market_data = self._enhance_with_live_data(pair, market_data)
            
            # 1. Signal Inspection (now with enhanced data)
            signal_analysis = self.signal_inspector.analyze(signal, enhanced_market_data)
            
            # 2. Market Regime Analysis (now with session/volatility data)
            regime_analysis = self.market_regime_analyzer.analyze(pair, enhanced_market_data)
            
            # 3. Liquidity Mapping (now with real sweep detection)
            liquidity_analysis = self.liquidity_mapper.analyze(signal, enhanced_market_data)
            
            # 4. Cross-Timeframe Validation (now with multiple TF candles)
            tf_data = enhanced_market_data.get('timeframes', {})
            tf_analysis = self.tf_validator.validate(signal, tf_data)
            
            # 5. Calculate Shield Score (enhanced with real market intelligence)
            shield_result = self.scoring_engine.calculate_score(
                signal_analysis,
                regime_analysis,
                liquidity_analysis,
                tf_analysis
            )
            
            # 6. Add CITADEL metadata
            shield_result['signal_id'] = signal_id
            shield_result['pair'] = pair
            shield_result['timestamp'] = datetime.now().isoformat()
            shield_result['citadel_version'] = '1.0.0'
            
            # 7. Apply user personalization if available
            if user_id:
                shield_result = self._apply_user_personalization(
                    shield_result, user_id, signal_analysis
                )
            
            # 8. Log the analysis
            self.shield_logger.log_shield_analysis(signal_id, signal, shield_result)
            
            # 9. Cache the result
            self._add_to_cache(signal_id, shield_result)
            
            logger.info(f"CITADEL analysis complete for {pair}: "
                       f"Score={shield_result['shield_score']}, "
                       f"Classification={shield_result['classification']}")
            
            return shield_result
            
        except Exception as e:
            logger.error(f"CITADEL analysis error: {str(e)}")
            return self._get_error_result(signal)
    
    def format_for_telegram(self, signal: Dict[str, Any], 
                          shield_analysis: Dict[str, Any],
                          compact: bool = True) -> str:
        """
        Format signal with shield analysis for Telegram display.
        
        Args:
            signal: Original signal data
            shield_analysis: CITADEL analysis results
            compact: Whether to use compact formatting
            
        Returns:
            Formatted Telegram message
        """
        return self.telegram_formatter.format_enhanced_signal(
            signal, shield_analysis, compact
        )
    
    def get_shield_insight(self, signal_id: str) -> str:
        """
        Get detailed shield insight for a signal.
        
        Args:
            signal_id: Signal identifier
            
        Returns:
            Detailed explanation message
        """
        # Try cache first
        analysis = self._get_from_cache(signal_id)
        
        if not analysis:
            # Try to retrieve from logger
            recent = self.shield_logger.get_recent_signals(24)
            for signal in recent:
                if signal['signal_id'] == signal_id:
                    # Would need to retrieve full analysis from DB
                    return "Shield details no longer in cache. Please analyze again."
        
        if analysis:
            return self.telegram_formatter.format_shield_insight(analysis)
        else:
            return "Shield analysis not found for this signal."
    
    def get_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Get CITADEL performance report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance statistics and insights
        """
        return self.shield_logger.get_shield_performance(days)
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get shield statistics for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            User's shield performance stats
        """
        return self.shield_logger.get_user_shield_stats(user_id)
    
    def log_trade_outcome(self, signal_id: str, user_id: int, 
                         outcome: str, pips_result: float,
                         followed_shield: bool) -> bool:
        """
        Log the outcome of a trade for shield performance tracking.
        
        Args:
            signal_id: Signal identifier
            user_id: User who traded
            outcome: 'WIN', 'LOSS', 'BE', or 'SKIPPED'
            pips_result: Pip result
            followed_shield: Whether user followed shield recommendation
            
        Returns:
            Success status
        """
        return self.shield_logger.log_trade_outcome(
            signal_id, user_id, outcome, pips_result, followed_shield
        )
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load configuration file."""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config {filename}: {str(e)}")
            return {}
    
    def _get_pair_dna(self, pair: str) -> Dict[str, Any]:
        """Get market DNA for specific pair."""
        profiles = self.market_dna.get('market_profiles', {})
        
        # Try exact match first
        if pair.upper() in profiles:
            return profiles[pair.upper()]
        
        # Try without slash
        pair_no_slash = pair.replace('/', '')
        if pair_no_slash.upper() in profiles:
            return profiles[pair_no_slash.upper()]
        
        # Return default profile
        return {
            'pair_type': 'unknown',
            'trap_frequency': 'medium',
            'news_sensitivity': 'medium',
            'sweep_reliability': 0.7
        }
    
    def _generate_signal_id(self, signal: Dict[str, Any]) -> str:
        """Generate unique signal ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pair = signal.get('pair', 'UNKNOWN').replace('/', '')
        direction = signal.get('direction', 'X')
        return f"CITADEL_{pair}_{direction}_{timestamp}"
    
    def _get_from_cache(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis from cache if still valid."""
        if signal_id in self.analysis_cache:
            cached_data, cached_time = self.analysis_cache[signal_id]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return cached_data
            else:
                # Remove expired entry
                del self.analysis_cache[signal_id]
        return None
    
    def _add_to_cache(self, signal_id: str, analysis: Dict[str, Any]):
        """Add analysis to cache."""
        self.analysis_cache[signal_id] = (analysis, datetime.now())
        
        # Limit cache size
        if len(self.analysis_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self.analysis_cache.keys(), 
                           key=lambda k: self.analysis_cache[k][1])
            del self.analysis_cache[oldest_key]
    
    def _apply_user_personalization(self, shield_result: Dict[str, Any],
                                   user_id: int, signal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply user-specific adjustments to shield score."""
        try:
            user_stats = self.shield_logger.get_user_shield_stats(user_id)
            
            if user_stats and user_stats.get('total_signals_seen', 0) > 10:
                # Get user's performance patterns
                trust_score = user_stats.get('trust_score', 0.5)
                
                # Adjust recommendations based on user behavior
                if trust_score < 0.3 and shield_result['shield_score'] >= 6:
                    shield_result['personalized_note'] = (
                        "📊 You typically ignore shield advice. "
                        "This signal has strong protection - consider following it."
                    )
                elif trust_score > 0.8 and shield_result['classification'] == 'SHIELD_APPROVED':
                    shield_result['personalized_note'] = (
                        "🎯 Your shield discipline is excellent. "
                        "Another high-confidence setup for you."
                    )
                
                # Check if this pair is a weakness for the user
                class_performance = user_stats.get('performance_by_classification', {})
                current_class = shield_result['classification']
                
                if current_class in class_performance:
                    class_stats = class_performance[current_class]
                    if class_stats['win_rate'] < 50 and class_stats['trades'] > 5:
                        shield_result['personalized_warning'] = (
                            f"⚠️ You have {class_stats['win_rate']}% win rate "
                            f"on {current_class} signals. Extra caution advised."
                        )
                
        except Exception as e:
            logger.error(f"Personalization error: {str(e)}")
        
        return shield_result
    
    def _enhance_with_live_data(self, pair: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance market data with live broker stream intelligence."""
        try:
            # Get the data stream enhancer
            enhancer = get_data_enhancer()
            
            # Read latest broker data
            try:
                with open('/tmp/ea_raw_data.json', 'r') as f:
                    raw_broker_data = json.load(f)
                    
                # Process through enhancer
                enhanced_stream = enhancer.process_broker_stream(raw_broker_data)
                
                # Get enhanced data for this pair
                if pair in enhanced_stream:
                    pair_enhanced = enhanced_stream[pair]
                    
                    # Merge enhanced data with existing market data
                    market_data = market_data.copy()
                    
                    # Add real support/resistance levels
                    market_data['support_levels'] = pair_enhanced.get('support_levels', [])
                    market_data['resistance_levels'] = pair_enhanced.get('resistance_levels', [])
                    
                    # Add real ATR and volatility
                    market_data['atr'] = pair_enhanced.get('atr', market_data.get('atr', 0))
                    market_data['atr_history'] = pair_enhanced.get('atr_history', [])
                    market_data['volatility_percentile'] = pair_enhanced.get('volatility_percentile', 50)
                    
                    # Add liquidity intelligence
                    market_data['liquidity_sweeps'] = pair_enhanced.get('liquidity_sweeps', [])
                    market_data['volume_spikes'] = pair_enhanced.get('volume_spikes', [])
                    market_data['order_blocks'] = pair_enhanced.get('order_blocks', [])
                    
                    # Add multi-timeframe candle data
                    if 'timeframes' not in market_data:
                        market_data['timeframes'] = {}
                    
                    enhanced_tf = pair_enhanced.get('timeframes', {})
                    for tf_name, tf_data in enhanced_tf.items():
                        if tf_name in market_data['timeframes']:
                            # Merge with existing, prioritizing enhanced data
                            market_data['timeframes'][tf_name].update(tf_data)
                        else:
                            market_data['timeframes'][tf_name] = tf_data
                    
                    # Add market structure analysis
                    market_data['market_structure'] = pair_enhanced.get('market_structure', 'unknown')
                    market_data['trend_direction'] = pair_enhanced.get('trend_direction', 'neutral')
                    market_data['session'] = pair_enhanced.get('session', 'unknown')
                    
                    # Add spread and momentum analysis
                    market_data['spread_analysis'] = pair_enhanced.get('spread_analysis', {})
                    market_data['price_momentum'] = pair_enhanced.get('price_momentum', {})
                    
                    # Add confluence zones
                    market_data['confluence_zones'] = pair_enhanced.get('confluence_zones', [])
                    
                    # Add institutional signals
                    market_data['institutional_signals'] = self._detect_institutional_signals(pair_enhanced)
                    
                    logger.info(f"Enhanced {pair} with live broker data: "
                              f"{len(market_data.get('support_levels', []))} support levels, "
                              f"{len(market_data.get('liquidity_sweeps', []))} liquidity events")
                              
            except FileNotFoundError:
                logger.warning("No live broker data available at /tmp/ea_raw_data.json")
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in broker data file")
                
        except Exception as e:
            logger.error(f"Error enhancing with live data: {e}")
            
        return market_data
    
    def _detect_institutional_signals(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect institutional trading patterns from enhanced data."""
        signals = {
            'liquidity_hunt_detected': False,
            'order_block_test': False,
            'stop_hunt_probability': 0.0,
            'accumulation_distribution': 'neutral',
            'smart_money_direction': 'neutral'
        }
        
        try:
            # Check for liquidity hunt patterns
            sweeps = enhanced_data.get('liquidity_sweeps', [])
            if sweeps:
                recent_sweep = sweeps[-1]
                time_since_sweep = int(time.time()) - recent_sweep['timestamp']
                if time_since_sweep < 300:  # Within 5 minutes
                    signals['liquidity_hunt_detected'] = True
                    signals['stop_hunt_probability'] = min(recent_sweep['magnitude'] * 100, 80)
            
            # Check volume spikes for accumulation/distribution
            volume_spikes = enhanced_data.get('volume_spikes', [])
            if volume_spikes:
                # High volume at lows = accumulation
                # High volume at highs = distribution
                current_price = enhanced_data.get('current_price', 0)
                recent_low = min([s['price'] for s in volume_spikes]) if volume_spikes else current_price
                recent_high = max([s['price'] for s in volume_spikes]) if volume_spikes else current_price
                
                for spike in volume_spikes[-3:]:  # Last 3 spikes
                    if abs(spike['price'] - recent_low) < recent_low * 0.001:
                        signals['accumulation_distribution'] = 'accumulation'
                    elif abs(spike['price'] - recent_high) < recent_high * 0.001:
                        signals['accumulation_distribution'] = 'distribution'
            
            # Determine smart money direction
            momentum = enhanced_data.get('price_momentum', {})
            if momentum.get('momentum_direction') == 'bullish' and signals['accumulation_distribution'] == 'accumulation':
                signals['smart_money_direction'] = 'bullish'
            elif momentum.get('momentum_direction') == 'bearish' and signals['accumulation_distribution'] == 'distribution':
                signals['smart_money_direction'] = 'bearish'
                
        except Exception as e:
            logger.error(f"Error detecting institutional signals: {e}")
            
        return signals
    
    def _calculate_trap_probability(self, enhanced_data: Dict[str, Any], signal: Dict[str, Any]) -> float:
        """Calculate probability of retail trap using enhanced data."""
        trap_score = 0.0
        
        try:
            # Check if entry is near recent sweep
            sweeps = enhanced_data.get('liquidity_sweeps', [])
            entry_price = signal.get('entry_price', 0)
            
            for sweep in sweeps[-3:]:  # Last 3 sweeps
                if abs(sweep['price'] - entry_price) < entry_price * 0.002:  # Within 0.2%
                    # Entry near recent sweep = potential trap
                    trap_score += 30
            
            # Check spread behavior
            spread_analysis = enhanced_data.get('spread_analysis', {})
            if spread_analysis.get('spread_trend') == 'widening':
                trap_score += 20
            
            # Check if against smart money
            institutional = enhanced_data.get('institutional_signals', {})
            signal_direction = signal.get('direction', '').lower()
            
            if institutional.get('smart_money_direction') == 'bullish' and signal_direction == 'sell':
                trap_score += 25
            elif institutional.get('smart_money_direction') == 'bearish' and signal_direction == 'buy':
                trap_score += 25
            
            # Check volatility spike
            if enhanced_data.get('volatility_percentile', 50) > 80:
                trap_score += 15
                
        except Exception as e:
            logger.error(f"Error calculating trap probability: {e}")
            
        return min(trap_score, 100)
    
    def _assess_entry_quality(self, enhanced_data: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
        """Assess entry quality using enhanced broker data."""
        assessment = {
            'quality_score': 0,
            'factors': [],
            'warnings': []
        }
        
        try:
            entry_price = signal.get('entry_price', 0)
            
            # Check confluence zones
            confluences = enhanced_data.get('confluence_zones', [])
            for zone in confluences:
                if abs(zone['price'] - entry_price) < entry_price * 0.001:
                    assessment['quality_score'] += zone['strength'] * 10
                    assessment['factors'].append(f"Confluence zone (strength: {zone['strength']})")
            
            # Check support/resistance proximity
            supports = enhanced_data.get('support_levels', [])
            resistances = enhanced_data.get('resistance_levels', [])
            
            if signal.get('direction', '').lower() == 'buy':
                # For buy, check if above support
                for support in supports:
                    if entry_price > support and (entry_price - support) < entry_price * 0.002:
                        assessment['quality_score'] += 15
                        assessment['factors'].append("Above key support")
                        break
            else:
                # For sell, check if below resistance
                for resistance in resistances:
                    if entry_price < resistance and (resistance - entry_price) < entry_price * 0.002:
                        assessment['quality_score'] += 15
                        assessment['factors'].append("Below key resistance")
                        break
            
            # Check momentum alignment
            momentum = enhanced_data.get('price_momentum', {})
            if momentum.get('momentum_direction') == signal.get('direction', '').lower():
                assessment['quality_score'] += 20
                assessment['factors'].append("Momentum aligned")
            else:
                assessment['warnings'].append("Against momentum")
            
            # Check for post-sweep entry
            institutional = enhanced_data.get('institutional_signals', {})
            if institutional.get('liquidity_hunt_detected'):
                assessment['quality_score'] += 25
                assessment['factors'].append("Post-liquidity sweep entry")
                
        except Exception as e:
            logger.error(f"Error assessing entry quality: {e}")
            
        return assessment
    
    def _get_error_result(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Return error result when analysis fails."""
        return {
            'signal_id': self._generate_signal_id(signal),
            'shield_score': 5.0,
            'classification': 'UNVERIFIED',
            'label': 'ANALYSIS ERROR',
            'emoji': '❌',
            'explanation': 'Unable to complete shield analysis',
            'recommendation': 'Manual analysis recommended',
            'error': True
        }


# Singleton instance for easy import
_citadel_instance = None

def get_citadel_analyzer() -> CitadelAnalyzer:
    """Get singleton CITADEL analyzer instance."""
    global _citadel_instance
    if _citadel_instance is None:
        _citadel_instance = CitadelAnalyzer()
    return _citadel_instance


# Example usage
if __name__ == "__main__":
    # Initialize CITADEL
    citadel = CitadelAnalyzer()
    
    # Test signal
    test_signal = {
        'signal_id': 'VENOM_EURUSD_BUY_001',
        'pair': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'sl': 1.0820,
        'tp': 1.0910,
        'signal_type': 'PRECISION_STRIKE'
    }
    
    # Test market data
    test_market_data = {
        'recent_candles': [
            {'open': 1.0840, 'high': 1.0845, 'low': 1.0835, 'close': 1.0842},
            {'open': 1.0842, 'high': 1.0843, 'low': 1.0825, 'close': 1.0841},
            {'open': 1.0841, 'high': 1.0850, 'low': 1.0840, 'close': 1.0848},
            {'open': 1.0848, 'high': 1.0852, 'low': 1.0846, 'close': 1.0850}
        ],
        'recent_high': 1.0860,
        'recent_low': 1.0820,
        'atr': 0.0045,
        'atr_history': [0.0040, 0.0042, 0.0045, 0.0043, 0.0041],
        'timeframes': {
            'M5': {
                'close': 1.0850,
                'ma_fast': 1.0845,
                'ma_slow': 1.0840,
                'rsi': 55,
                'recent_highs': [1.0855, 1.0860],
                'recent_lows': [1.0835, 1.0840]
            },
            'M15': {
                'close': 1.0850,
                'ma_fast': 1.0848,
                'ma_slow': 1.0843,
                'rsi': 58,
                'recent_highs': [1.0860, 1.0865],
                'recent_lows': [1.0830, 1.0835]
            },
            'H1': {
                'close': 1.0850,
                'ma_fast': 1.0847,
                'ma_slow': 1.0842,
                'rsi': 60,
                'recent_highs': [1.0870, 1.0875],
                'recent_lows': [1.0820, 1.0825]
            },
            'H4': {
                'close': 1.0850,
                'ma_fast': 1.0845,
                'ma_slow': 1.0840,
                'rsi': 62,
                'recent_highs': [1.0880, 1.0890],
                'recent_lows': [1.0800, 1.0810]
            }
        }
    }
    
    # Analyze signal
    result = citadel.analyze_signal(test_signal, test_market_data, user_id=12345)
    
    print("\n=== CITADEL ANALYSIS RESULT ===")
    print(f"Shield Score: {result['shield_score']}/10")
    print(f"Classification: {result['emoji']} {result['label']}")
    print(f"Explanation: {result['explanation']}")
    print(f"Recommendation: {result['recommendation']}")
    
    # Format for Telegram
    print("\n=== TELEGRAM MESSAGE ===")
    telegram_msg = citadel.format_for_telegram(test_signal, result, compact=True)
    print(telegram_msg)
    
    # Get detailed insight
    print("\n=== SHIELD INSIGHT ===")
    insight = citadel.get_shield_insight(result['signal_id'])
    print(insight)