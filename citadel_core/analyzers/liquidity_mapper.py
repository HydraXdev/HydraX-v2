"""
Liquidity Mapper - Detect liquidity zones, sweeps, and trap formations

Purpose: Identify where stop losses cluster, detect liquidity sweeps, and determine
if a signal is positioned before or after a likely retail trap.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)


class LiquidityMapper:
    """
    Maps liquidity zones and detects institutional liquidity hunting patterns.
    Identifies stop loss clusters, sweep events, and order block zones.
    """
    
    def __init__(self):
        # Common pip distances for stop losses by pair type
        self.typical_sl_distances = {
            'majors': [10, 15, 20, 25, 30, 40, 50],  # EURUSD, GBPUSD, etc.
            'jpy_pairs': [10, 15, 20, 30, 40, 50, 75, 100],  # USDJPY, GBPJPY
            'metals': [50, 100, 150, 200, 300, 500],  # XAUUSD
            'indices': [50, 100, 200, 300, 500]  # US30, NAS100
        }
        
        # Psychological levels
        self.round_number_strengths = {
            'xx000': 5,  # 1.1000 - Strongest
            'xx500': 4,  # 1.1050 - Strong  
            'xx250': 3,  # 1.1025 - Medium
            'xx100': 2,  # 1.1010 - Weak
            'other': 1   # 1.1013 - Minimal
        }
        
    def analyze(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze liquidity landscape around the signal.
        
        Args:
            signal: Trading signal with entry, sl, tp
            market_data: Market data including price history, highs/lows
            
        Returns:
            Dict containing liquidity analysis
        """
        try:
            pair = signal.get('pair', '')
            entry_price = float(signal.get('entry_price', 0))
            direction = signal.get('direction', '')
            
            # Identify pair type for proper pip calculation
            pair_type = self._identify_pair_type(pair)
            pip_value = self._get_pip_value(pair)
            
            # Detect recent liquidity sweeps
            sweep_analysis = self._detect_liquidity_sweep(market_data, direction)
            
            # Map stop loss clusters
            sl_clusters = self._map_sl_clusters(entry_price, pair_type, pip_value, market_data)
            
            # Identify order blocks
            order_blocks = self._identify_order_blocks(market_data, entry_price, direction)
            
            # Check if we're near liquidity zones
            liquidity_proximity = self._check_liquidity_proximity(
                entry_price, sl_clusters, order_blocks, pip_value
            )
            
            # Determine trap probability
            trap_analysis = self._analyze_trap_formation(
                sweep_analysis, liquidity_proximity, direction, market_data
            )
            
            # Check psychological levels
            psych_level = self._check_psychological_level(entry_price, pair_type)
            
            result = {
                'liquidity_zone_hit': sweep_analysis['sweep_detected'],
                'sweep_detected': sweep_analysis['sweep_detected'],
                'sweep_type': sweep_analysis['sweep_type'],
                'sweep_quality': sweep_analysis['quality'],
                'time_since_sweep': sweep_analysis['time_since'],
                'sl_clusters_nearby': len(sl_clusters) > 0,
                'nearest_cluster': sl_clusters[0] if sl_clusters else None,
                'order_block_nearby': len(order_blocks) > 0,
                'nearest_order_block': order_blocks[0] if order_blocks else None,
                'trap_probability': trap_analysis['probability'],
                'trap_type': trap_analysis['type'],
                'psychological_level': psych_level,
                'liquidity_score': self._calculate_liquidity_score(
                    sweep_analysis, trap_analysis, liquidity_proximity
                )
            }
            
            logger.info(f"Liquidity analysis for {pair}: Sweep={sweep_analysis['sweep_detected']}, "
                       f"Trap probability={trap_analysis['probability']}")
            return result
            
        except Exception as e:
            logger.error(f"Liquidity mapping error: {str(e)}")
            return self._get_default_analysis()
    
    def _identify_pair_type(self, pair: str) -> str:
        """Identify the type of trading pair."""
        pair_upper = pair.upper()
        
        if 'JPY' in pair_upper:
            return 'jpy_pairs'
        elif 'XAU' in pair_upper or 'GOLD' in pair_upper:
            return 'metals'
        elif any(idx in pair_upper for idx in ['US30', 'NAS', 'SP500', 'DAX']):
            return 'indices'
        else:
            return 'majors'
    
    def _get_pip_value(self, pair: str) -> float:
        """Get pip value for the pair."""
        pair_upper = pair.upper()
        
        if 'JPY' in pair_upper:
            return 0.01
        elif 'XAU' in pair_upper:
            return 0.1
        else:
            return 0.0001
    
    def _detect_liquidity_sweep(self, market_data: Dict[str, Any], 
                                direction: str) -> Dict[str, Any]:
        """Detect if a liquidity sweep has occurred recently."""
        # First check if we have real liquidity sweep data from enhanced stream
        real_sweeps = market_data.get('liquidity_sweeps', [])
        if real_sweeps:
            # Use real sweep data if available
            for sweep in real_sweeps:
                # Check if sweep aligns with signal direction
                if (direction == 'BUY' and sweep['type'] == 'support_sweep') or \
                   (direction == 'SELL' and sweep['type'] == 'resistance_sweep'):
                    
                    # Calculate time since sweep
                    import time
                    current_time = int(time.time())
                    time_since_sweep = current_time - sweep['timestamp']
                    
                    # Quality based on magnitude
                    quality = 'high' if sweep['magnitude'] > 0.0003 else 'medium' if sweep['magnitude'] > 0.0001 else 'low'
                    
                    return {
                        'sweep_detected': True,
                        'sweep_type': 'bullish_sweep' if direction == 'BUY' else 'bearish_sweep',
                        'quality': quality,
                        'time_since': time_since_sweep // 60,  # Convert to minutes
                        'real_data': True,
                        'sweep_price': sweep['price']
                    }
        
        # Fallback to candle-based detection if no real sweep data
        candles = market_data.get('recent_candles', [])
        
        if not candles or len(candles) < 10:
            return {
                'sweep_detected': False,
                'sweep_type': None,
                'quality': 'none',
                'time_since': None
            }
        
        # Look for sweep patterns in last 10 candles
        for i in range(len(candles) - 3, 0, -1):
            current = candles[i]
            prev = candles[i-1]
            next_candle = candles[i+1]
            
            # Bullish sweep (spike down, then reversal up)
            if direction == 'BUY':
                spike_down = current['low'] < prev['low'] and current['low'] < next_candle['low']
                reversal_up = next_candle['close'] > current['close'] and next_candle['close'] > current['open']
                
                if spike_down and reversal_up:
                    # Check sweep quality
                    wick_ratio = (current['open'] - current['low']) / (current['high'] - current['low'])
                    quality = 'high' if wick_ratio > 0.7 else 'medium' if wick_ratio > 0.5 else 'low'
                    
                    return {
                        'sweep_detected': True,
                        'sweep_type': 'bullish_sweep',
                        'quality': quality,
                        'time_since': len(candles) - i - 1
                    }
            
            # Bearish sweep (spike up, then reversal down)
            elif direction == 'SELL':
                spike_up = current['high'] > prev['high'] and current['high'] > next_candle['high']
                reversal_down = next_candle['close'] < current['close'] and next_candle['close'] < current['open']
                
                if spike_up and reversal_down:
                    # Check sweep quality
                    wick_ratio = (current['high'] - current['open']) / (current['high'] - current['low'])
                    quality = 'high' if wick_ratio > 0.7 else 'medium' if wick_ratio > 0.5 else 'low'
                    
                    return {
                        'sweep_detected': True,
                        'sweep_type': 'bearish_sweep',
                        'quality': quality,
                        'time_since': len(candles) - i - 1
                    }
        
        return {
            'sweep_detected': False,
            'sweep_type': None,
            'quality': 'none',
            'time_since': None
        }
    
    def _map_sl_clusters(self, entry_price: float, pair_type: str, 
                        pip_value: float, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map potential stop loss cluster zones."""
        clusters = []
        recent_high = market_data.get('recent_high', entry_price)
        recent_low = market_data.get('recent_low', entry_price)
        
        # Get typical SL distances for this pair type
        typical_distances = self.typical_sl_distances.get(pair_type, [20, 30, 50])
        
        # Map clusters above and below current price
        for distance in typical_distances:
            # Cluster above (for short positions)
            cluster_above = recent_high + (distance * pip_value)
            cluster_strength = self._calculate_cluster_strength(
                cluster_above, market_data, 'resistance'
            )
            
            if cluster_strength > 0:
                clusters.append({
                    'price': cluster_above,
                    'distance_pips': distance,
                    'type': 'sell_stops',
                    'strength': cluster_strength
                })
            
            # Cluster below (for long positions)
            cluster_below = recent_low - (distance * pip_value)
            cluster_strength = self._calculate_cluster_strength(
                cluster_below, market_data, 'support'
            )
            
            if cluster_strength > 0:
                clusters.append({
                    'price': cluster_below,
                    'distance_pips': distance,
                    'type': 'buy_stops',
                    'strength': cluster_strength
                })
        
        # Sort by distance from entry
        clusters.sort(key=lambda x: abs(x['price'] - entry_price))
        
        return clusters[:5]  # Return top 5 nearest clusters
    
    def _identify_order_blocks(self, market_data: Dict[str, Any], 
                              entry_price: float, direction: str) -> List[Dict[str, Any]]:
        """Identify institutional order block zones."""
        order_blocks = []
        candles = market_data.get('recent_candles', [])
        
        if not candles or len(candles) < 20:
            return order_blocks
        
        # Look for order blocks in last 20 candles
        for i in range(1, len(candles) - 1):
            current = candles[i]
            prev = candles[i-1]
            next_candle = candles[i+1] if i < len(candles) - 1 else None
            
            # Bullish order block (last bearish before bullish move)
            if direction == 'BUY':
                is_bearish = current['close'] < current['open']
                strong_bull_after = next_candle and (next_candle['close'] - next_candle['open']) > \
                                   2 * abs(current['close'] - current['open'])
                
                if is_bearish and strong_bull_after:
                    order_blocks.append({
                        'type': 'bullish_ob',
                        'high': current['high'],
                        'low': current['low'],
                        'mid': (current['high'] + current['low']) / 2,
                        'strength': self._calculate_ob_strength(current, candles[i:])
                    })
            
            # Bearish order block (last bullish before bearish move)
            elif direction == 'SELL':
                is_bullish = current['close'] > current['open']
                strong_bear_after = next_candle and (next_candle['open'] - next_candle['close']) > \
                                   2 * abs(current['close'] - current['open'])
                
                if is_bullish and strong_bear_after:
                    order_blocks.append({
                        'type': 'bearish_ob',
                        'high': current['high'],
                        'low': current['low'],
                        'mid': (current['high'] + current['low']) / 2,
                        'strength': self._calculate_ob_strength(current, candles[i:])
                    })
        
        # Filter order blocks near entry
        nearby_obs = [ob for ob in order_blocks 
                     if abs(ob['mid'] - entry_price) < entry_price * 0.01]
        
        return sorted(nearby_obs, key=lambda x: x['strength'], reverse=True)[:3]
    
    def _check_liquidity_proximity(self, entry_price: float, sl_clusters: List[Dict],
                                  order_blocks: List[Dict], pip_value: float) -> Dict[str, Any]:
        """Check proximity to liquidity zones."""
        proximity_data = {
            'near_cluster': False,
            'near_order_block': False,
            'danger_zone': False
        }
        
        # Check SL cluster proximity
        if sl_clusters:
            nearest_cluster = sl_clusters[0]
            distance_pips = abs(nearest_cluster['price'] - entry_price) / pip_value
            proximity_data['near_cluster'] = distance_pips < 30
            proximity_data['cluster_distance_pips'] = distance_pips
        
        # Check order block proximity  
        if order_blocks:
            nearest_ob = order_blocks[0]
            in_ob = nearest_ob['low'] <= entry_price <= nearest_ob['high']
            proximity_data['near_order_block'] = in_ob
            proximity_data['in_order_block'] = in_ob
        
        # Danger zone: very close to liquidity
        proximity_data['danger_zone'] = (
            proximity_data.get('cluster_distance_pips', 999) < 15 or
            proximity_data.get('in_order_block', False)
        )
        
        return proximity_data
    
    def _analyze_trap_formation(self, sweep_analysis: Dict, liquidity_proximity: Dict,
                               direction: str, market_data: Dict) -> Dict[str, Any]:
        """Analyze probability of trap formation."""
        trap_score = 0
        trap_type = 'none'
        
        # Post-sweep entry is good (not a trap)
        if sweep_analysis['sweep_detected']:
            trap_score -= 3
            trap_type = 'post_sweep_entry'
        
        # Near liquidity without sweep is dangerous
        if liquidity_proximity['danger_zone'] and not sweep_analysis['sweep_detected']:
            trap_score += 4
            trap_type = 'liquidity_trap'
        
        # Check for false breakout setup
        if market_data.get('near_resistance') and direction == 'BUY':
            trap_score += 2
            trap_type = 'false_breakout' if trap_type == 'none' else trap_type
        elif market_data.get('near_support') and direction == 'SELL':
            trap_score += 2
            trap_type = 'false_breakout' if trap_type == 'none' else trap_type
        
        # Time of day trap risk
        hour = datetime.now().hour
        if hour in [0, 1, 2, 3, 4, 5]:  # Low liquidity hours
            trap_score += 1
        
        # Calculate probability
        if trap_score >= 4:
            probability = 'HIGH'
        elif trap_score >= 2:
            probability = 'MEDIUM'
        elif trap_score >= 0:
            probability = 'LOW'
        else:
            probability = 'MINIMAL'
        
        return {
            'probability': probability,
            'type': trap_type,
            'score': trap_score
        }
    
    def _check_psychological_level(self, price: float, pair_type: str) -> Dict[str, Any]:
        """Check if price is at a psychological level."""
        # Adjust decimal places based on pair type
        if pair_type == 'jpy_pairs':
            decimal_places = 2
            multiplier = 100
        else:
            decimal_places = 4
            multiplier = 10000
        
        # Get the fractional part
        price_int = int(price * multiplier)
        fractional = price_int % 1000
        
        # Determine psychological level strength
        if fractional == 0:
            strength = 'major'
            level_type = 'xx000'
        elif fractional == 500:
            strength = 'strong'
            level_type = 'xx500'
        elif fractional in [250, 750]:
            strength = 'medium'
            level_type = 'xx250'
        elif fractional % 100 == 0:
            strength = 'minor'
            level_type = 'xx100'
        else:
            strength = 'none'
            level_type = 'none'
        
        return {
            'at_level': strength != 'none',
            'strength': strength,
            'type': level_type
        }
    
    def _calculate_cluster_strength(self, price: float, market_data: Dict, 
                                   zone_type: str) -> int:
        """Calculate strength of a potential SL cluster zone."""
        strength = 0
        
        # Check if it's near historical highs/lows
        historical_levels = market_data.get(f'historical_{zone_type}_levels', [])
        for level in historical_levels:
            if abs(price - level) < price * 0.001:  # Within 0.1%
                strength += 1
        
        # Check if it's a round number
        if price % 0.01 == 0:  # Round to 2 decimals
            strength += 1
        
        # Check previous price reactions
        reactions = market_data.get('price_reactions', {})
        if price in reactions and reactions[price] > 2:
            strength += 2
        
        return min(strength, 5)  # Cap at 5
    
    def _calculate_ob_strength(self, ob_candle: Dict, following_candles: List[Dict]) -> int:
        """Calculate order block strength."""
        strength = 3  # Base strength
        
        # Check how far price moved away
        if len(following_candles) > 3:
            move_away = abs(following_candles[3]['close'] - ob_candle['close'])
            ob_size = abs(ob_candle['high'] - ob_candle['low'])
            
            if move_away > ob_size * 3:
                strength += 2
            elif move_away > ob_size * 2:
                strength += 1
        
        # Check if it's been tested
        tested = False
        for candle in following_candles[4:]:
            if candle['low'] <= ob_candle['high'] and candle['high'] >= ob_candle['low']:
                tested = True
                break
        
        if not tested:
            strength += 1
        
        return min(strength, 5)
    
    def _calculate_liquidity_score(self, sweep_analysis: Dict, trap_analysis: Dict,
                                  liquidity_proximity: Dict) -> int:
        """Calculate overall liquidity-based score contribution."""
        score = 0
        
        # Positive factors
        if sweep_analysis['sweep_detected']:
            if sweep_analysis['quality'] == 'high':
                score += 3
            elif sweep_analysis['quality'] == 'medium':
                score += 2
            else:
                score += 1
        
        # Negative factors
        if trap_analysis['probability'] == 'HIGH':
            score -= 3
        elif trap_analysis['probability'] == 'MEDIUM':
            score -= 1
        
        if liquidity_proximity['danger_zone'] and not sweep_analysis['sweep_detected']:
            score -= 2
        
        return score
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when error occurs."""
        return {
            'liquidity_zone_hit': False,
            'sweep_detected': False,
            'sweep_type': None,
            'sweep_quality': 'none',
            'time_since_sweep': None,
            'sl_clusters_nearby': False,
            'nearest_cluster': None,
            'order_block_nearby': False,
            'nearest_order_block': None,
            'trap_probability': 'UNKNOWN',
            'trap_type': 'none',
            'psychological_level': {'at_level': False, 'strength': 'none'},
            'liquidity_score': 0
        }


# Example usage
if __name__ == "__main__":
    mapper = LiquidityMapper()
    
    # Test signal
    test_signal = {
        'pair': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'sl': 1.0820,
        'tp': 1.0900
    }
    
    # Test market data with sweep
    test_market = {
        'recent_candles': [
            {'open': 1.0840, 'high': 1.0845, 'low': 1.0835, 'close': 1.0842},
            {'open': 1.0842, 'high': 1.0843, 'low': 1.0825, 'close': 1.0841},  # Sweep candle
            {'open': 1.0841, 'high': 1.0850, 'low': 1.0840, 'close': 1.0848},  # Reversal
            {'open': 1.0848, 'high': 1.0852, 'low': 1.0846, 'close': 1.0850},
        ],
        'recent_high': 1.0860,
        'recent_low': 1.0820,
        'historical_support_levels': [1.0800, 1.0820, 1.0850],
        'historical_resistance_levels': [1.0900, 1.0920, 1.0950]
    }
    
    result = mapper.analyze(test_signal, test_market)
    print("Liquidity Analysis:")
    for key, value in result.items():
        print(f"  {key}: {value}")