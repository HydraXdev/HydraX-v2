"""
Microstructure Pattern Detection - Identify institutional footprints

Purpose: Detect subtle market microstructure patterns that reveal institutional
activity, helping traders identify smart money movements.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class InstitutionalFootprint(Enum):
    """Types of institutional footprints"""
    WHALE_ACCUMULATION = "whale_accumulation"
    WHALE_DISTRIBUTION = "whale_distribution"
    ICEBERG_ORDER = "iceberg_order"
    STOP_HUNT = "stop_hunt"
    ABSORPTION = "absorption"
    EXHAUSTION = "exhaustion"
    SMART_MONEY_REVERSAL = "smart_money_reversal"
    POSITION_BUILDING = "position_building"


class OrderFlowPattern(Enum):
    """Order flow patterns"""
    AGGRESSIVE_BUYING = "aggressive_buying"
    AGGRESSIVE_SELLING = "aggressive_selling"
    PASSIVE_ACCUMULATION = "passive_accumulation"
    PASSIVE_DISTRIBUTION = "passive_distribution"
    BALANCED = "balanced"


class MicroStructure:
    """
    Detects institutional activity through market microstructure analysis.
    
    Identifies whale movements, iceberg orders, absorption patterns, and other
    smart money footprints that retail traders typically miss.
    """
    
    def __init__(self):
        # Pattern detection thresholds
        self.thresholds = {
            'whale_volume_multiplier': 3.0,    # Volume 3x average
            'iceberg_slice_similarity': 0.85,  # 85% size similarity
            'absorption_rejection_ratio': 0.7,  # 70% of volume absorbed
            'exhaustion_volume_spike': 2.5,    # 2.5x average volume
            'smart_money_time_window': 15,     # Minutes for pattern
            'position_building_periods': 5      # Consecutive periods
        }
        
        # Institutional behavior patterns
        self.institutional_patterns = {
            'accumulation_signature': {
                'description': 'Quiet accumulation at support',
                'characteristics': [
                    'Multiple touches of support',
                    'Decreasing selling volume',
                    'Narrowing range',
                    'Absorption of sell orders'
                ],
                'typical_duration': '30-120 minutes',
                'expected_outcome': 'Bullish breakout'
            },
            'distribution_signature': {
                'description': 'Smart money distribution at resistance',
                'characteristics': [
                    'Multiple touches of resistance',
                    'Decreasing buying volume',
                    'Widening spread',
                    'Supply overwhelming demand'
                ],
                'typical_duration': '30-120 minutes',
                'expected_outcome': 'Bearish breakdown'
            },
            'stop_hunt_signature': {
                'description': 'Liquidity grab before reversal',
                'characteristics': [
                    'Quick spike beyond key level',
                    'High volume on spike',
                    'Immediate rejection',
                    'Return to pre-spike range'
                ],
                'typical_duration': '5-15 minutes',
                'expected_outcome': 'Reversal in opposite direction'
            },
            'iceberg_signature': {
                'description': 'Large hidden order being filled',
                'characteristics': [
                    'Consistent order sizes',
                    'Price absorption at level',
                    'Regenerating liquidity',
                    'Extended time at price'
                ],
                'typical_duration': '15-60 minutes',
                'expected_outcome': 'Continuation after fill'
            }
        }
        
        # Volume profile patterns
        self.volume_profiles = {
            'whale_entry': {
                'pattern': 'Single large volume spike',
                'interpretation': 'Institutional position initiated',
                'reliability': 0.75
            },
            'accumulation': {
                'pattern': 'Increasing volume on dips',
                'interpretation': 'Smart money buying weakness',
                'reliability': 0.80
            },
            'distribution': {
                'pattern': 'Increasing volume on rallies',
                'interpretation': 'Smart money selling strength',
                'reliability': 0.80
            },
            'exhaustion': {
                'pattern': 'Climactic volume then silence',
                'interpretation': 'Move completion likely',
                'reliability': 0.70
            }
        }
        
        # Price action footprints
        self.price_footprints = {
            'absorption': 'Price holds despite selling pressure',
            'rejection': 'Quick reversal from level with volume',
            'acceptance': 'Price settles and builds value',
            'migration': 'Gradual shift in value area',
            'initiative': 'Aggressive move starting new trend'
        }
    
    def detect_institutional_footprints(self, price_data: List[Dict[str, Any]],
                                      volume_data: List[Dict[str, Any]],
                                      depth_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect institutional footprints in market data.
        
        Args:
            price_data: Recent price candles
            volume_data: Volume information
            depth_data: Optional order book depth
            
        Returns:
            Detected footprints and interpretations
        """
        if not price_data or not volume_data:
            return self._get_no_footprint_result()
        
        footprints = []
        
        # Detect whale activity
        whale_activity = self._detect_whale_activity(price_data, volume_data)
        if whale_activity['detected']:
            footprints.append(whale_activity)
        
        # Detect iceberg orders
        iceberg_detection = self._detect_iceberg_orders(
            price_data, volume_data, depth_data
        )
        if iceberg_detection['detected']:
            footprints.append(iceberg_detection)
        
        # Detect absorption/exhaustion
        absorption_pattern = self._detect_absorption_pattern(
            price_data, volume_data
        )
        if absorption_pattern['detected']:
            footprints.append(absorption_pattern)
        
        # Detect smart money reversal
        reversal_pattern = self._detect_smart_money_reversal(
            price_data, volume_data
        )
        if reversal_pattern['detected']:
            footprints.append(reversal_pattern)
        
        # Analyze order flow
        order_flow = self._analyze_order_flow(price_data, volume_data)
        
        # Identify position building
        position_building = self._detect_position_building(
            price_data, volume_data
        )
        
        # Generate interpretation
        interpretation = self._interpret_footprints(
            footprints, order_flow, position_building
        )
        
        # Calculate institutional probability
        inst_probability = self._calculate_institutional_probability(
            footprints, order_flow
        )
        
        return {
            'footprints_detected': len(footprints),
            'footprints': footprints,
            'order_flow': order_flow,
            'position_building': position_building,
            'interpretation': interpretation,
            'institutional_probability': inst_probability,
            'trading_implications': self._get_trading_implications(
                footprints, order_flow
            ),
            'key_levels': self._identify_institutional_levels(
                price_data, footprints
            )
        }
    
    def analyze_market_depth_imbalance(self, depth_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze order book for institutional presence.
        
        Args:
            depth_data: Current order book data
            
        Returns:
            Depth analysis and imbalances
        """
        if not depth_data:
            return {'imbalance': 'unknown', 'institutional_bias': 'neutral'}
        
        bids = depth_data.get('bids', [])
        asks = depth_data.get('asks', [])
        
        if not bids or not asks:
            return {'imbalance': 'unknown', 'institutional_bias': 'neutral'}
        
        # Calculate imbalances
        bid_volume = sum(order['size'] for order in bids[:10])
        ask_volume = sum(order['size'] for order in asks[:10])
        
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return {'imbalance': 'unknown', 'institutional_bias': 'neutral'}
        
        bid_ratio = bid_volume / total_volume
        
        # Detect large orders (potential institutional)
        large_bids = [o for o in bids if o['size'] > self._get_average_size(bids) * 3]
        large_asks = [o for o in asks if o['size'] > self._get_average_size(asks) * 3]
        
        # Analyze order clustering
        bid_clustering = self._detect_order_clustering(bids)
        ask_clustering = self._detect_order_clustering(asks)
        
        # Determine institutional bias
        if bid_ratio > 0.65 and len(large_bids) > len(large_asks):
            inst_bias = 'bullish'
            strength = 'strong' if bid_ratio > 0.75 else 'moderate'
        elif bid_ratio < 0.35 and len(large_asks) > len(large_bids):
            inst_bias = 'bearish'
            strength = 'strong' if bid_ratio < 0.25 else 'moderate'
        else:
            inst_bias = 'neutral'
            strength = 'balanced'
        
        return {
            'imbalance': f"{bid_ratio:.1%} bid ratio",
            'institutional_bias': inst_bias,
            'strength': strength,
            'large_orders': {
                'bid_side': len(large_bids),
                'ask_side': len(large_asks)
            },
            'clustering': {
                'bids': bid_clustering,
                'asks': ask_clustering
            },
            'interpretation': self._interpret_depth_imbalance(
                bid_ratio, inst_bias, large_bids, large_asks
            )
        }
    
    def identify_smart_money_zones(self, price_data: List[Dict[str, Any]],
                                 volume_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify price zones where smart money is likely active.
        
        Args:
            price_data: Historical price data
            volume_data: Historical volume data
            
        Returns:
            List of smart money zones
        """
        zones = []
        
        if len(price_data) < 20:
            return zones
        
        # Identify high volume nodes
        volume_nodes = self._find_volume_nodes(price_data, volume_data)
        
        for node in volume_nodes:
            # Check for institutional characteristics
            if self._has_institutional_characteristics(node, price_data):
                zones.append({
                    'price': node['price'],
                    'type': node['type'],
                    'strength': node['strength'],
                    'description': self._get_zone_description(node),
                    'trading_bias': node['bias']
                })
        
        # Sort by strength
        zones.sort(key=lambda x: x['strength'], reverse=True)
        
        return zones[:5]  # Top 5 zones
    
    def _detect_whale_activity(self, price_data: List[Dict], 
                             volume_data: List[Dict]) -> Dict[str, Any]:
        """Detect whale-sized volume activity."""
        if len(volume_data) < 10:
            return {'detected': False}
        
        # Calculate average volume
        avg_volume = statistics.mean([v.get('volume', 0) for v in volume_data[:-1]])
        
        if avg_volume == 0:
            return {'detected': False}
        
        # Check latest volume
        latest_volume = volume_data[-1].get('volume', 0)
        volume_ratio = latest_volume / avg_volume
        
        if volume_ratio >= self.thresholds['whale_volume_multiplier']:
            # Determine direction
            latest_candle = price_data[-1]
            direction = 'buying' if latest_candle['close'] > latest_candle['open'] else 'selling'
            
            return {
                'detected': True,
                'type': InstitutionalFootprint.WHALE_ACCUMULATION if direction == 'buying' 
                       else InstitutionalFootprint.WHALE_DISTRIBUTION,
                'volume_ratio': round(volume_ratio, 1),
                'interpretation': f"🐋 Whale {direction} detected - {volume_ratio:.1f}x normal volume",
                'reliability': min(0.9, 0.6 + (volume_ratio - 3) * 0.1)
            }
        
        return {'detected': False}
    
    def _detect_iceberg_orders(self, price_data: List[Dict],
                             volume_data: List[Dict],
                             depth_data: Optional[Dict]) -> Dict[str, Any]:
        """Detect hidden iceberg orders."""
        if len(price_data) < 5:
            return {'detected': False}
        
        # Look for consistent order sizes at same price level
        price_levels = {}
        
        for i, candle in enumerate(price_data[-5:]):
            price = round(candle['close'], 5)
            volume = volume_data[-(5-i)].get('volume', 0)
            
            if price not in price_levels:
                price_levels[price] = []
            price_levels[price].append(volume)
        
        # Check for iceberg pattern
        for price, volumes in price_levels.items():
            if len(volumes) >= 3:
                # Check consistency
                avg_vol = statistics.mean(volumes)
                std_dev = statistics.stdev(volumes) if len(volumes) > 1 else 0
                
                if std_dev / avg_vol < 0.15:  # Less than 15% variation
                    return {
                        'detected': True,
                        'type': InstitutionalFootprint.ICEBERG_ORDER,
                        'price_level': price,
                        'slice_size': round(avg_vol),
                        'slices_detected': len(volumes),
                        'interpretation': f"🧊 Iceberg order at {price} - Hidden liquidity",
                        'reliability': 0.75
                    }
        
        return {'detected': False}
    
    def _detect_absorption_pattern(self, price_data: List[Dict],
                                 volume_data: List[Dict]) -> Dict[str, Any]:
        """Detect price absorption patterns."""
        if len(price_data) < 3:
            return {'detected': False}
        
        # Check last few candles for absorption
        recent_candles = price_data[-3:]
        recent_volumes = volume_data[-3:]
        
        # High volume but small price movement = absorption
        total_volume = sum(v.get('volume', 0) for v in recent_volumes)
        price_range = max(c['high'] for c in recent_candles) - min(c['low'] for c in recent_candles)
        avg_range = statistics.mean([c['high'] - c['low'] for c in price_data[:-3]])
        
        if total_volume > 0 and avg_range > 0:
            # High volume with compressed range indicates absorption
            if price_range < avg_range * 0.5 and total_volume > statistics.mean(
                [v.get('volume', 0) for v in volume_data[:-3]]
            ) * 2:
                # Determine if accumulation or distribution
                close_position = (recent_candles[-1]['close'] - recent_candles[-1]['low']) / (
                    recent_candles[-1]['high'] - recent_candles[-1]['low']
                ) if recent_candles[-1]['high'] != recent_candles[-1]['low'] else 0.5
                
                absorption_type = 'demand' if close_position > 0.6 else 'supply'
                
                return {
                    'detected': True,
                    'type': InstitutionalFootprint.ABSORPTION,
                    'absorption_type': absorption_type,
                    'interpretation': f"📊 {absorption_type.title()} absorption detected - "
                                    f"Institutional {absorption_type}",
                    'reliability': 0.8
                }
        
        return {'detected': False}
    
    def _detect_smart_money_reversal(self, price_data: List[Dict],
                                   volume_data: List[Dict]) -> Dict[str, Any]:
        """Detect smart money reversal patterns."""
        if len(price_data) < 5:
            return {'detected': False}
        
        # Look for climactic volume followed by reversal
        recent_volumes = [v.get('volume', 0) for v in volume_data[-5:]]
        avg_volume = statistics.mean(recent_volumes[:-1])
        
        if avg_volume == 0:
            return {'detected': False}
        
        # Check for exhaustion spike
        if recent_volumes[-2] > avg_volume * self.thresholds['exhaustion_volume_spike']:
            # Check for reversal after spike
            spike_candle = price_data[-2]
            reversal_candle = price_data[-1]
            
            # Bearish reversal
            if (spike_candle['close'] > spike_candle['open'] and
                reversal_candle['close'] < reversal_candle['open'] and
                reversal_candle['close'] < spike_candle['low']):
                
                return {
                    'detected': True,
                    'type': InstitutionalFootprint.SMART_MONEY_REVERSAL,
                    'direction': 'bearish',
                    'interpretation': "🔄 Smart money reversal - Distribution after exhaustion",
                    'reliability': 0.85
                }
            
            # Bullish reversal
            elif (spike_candle['close'] < spike_candle['open'] and
                  reversal_candle['close'] > reversal_candle['open'] and
                  reversal_candle['close'] > spike_candle['high']):
                
                return {
                    'detected': True,
                    'type': InstitutionalFootprint.SMART_MONEY_REVERSAL,
                    'direction': 'bullish',
                    'interpretation': "🔄 Smart money reversal - Accumulation after exhaustion",
                    'reliability': 0.85
                }
        
        return {'detected': False}
    
    def _analyze_order_flow(self, price_data: List[Dict],
                          volume_data: List[Dict]) -> Dict[str, Any]:
        """Analyze order flow characteristics."""
        if len(price_data) < 5:
            return {'pattern': OrderFlowPattern.BALANCED.value, 'strength': 0}
        
        # Analyze recent candles
        buying_pressure = 0
        selling_pressure = 0
        
        for i in range(-5, 0):
            candle = price_data[i]
            volume = volume_data[i].get('volume', 0)
            
            # Estimate buying/selling pressure
            body = abs(candle['close'] - candle['open'])
            range_size = candle['high'] - candle['low']
            
            if range_size > 0:
                if candle['close'] > candle['open']:
                    buying_pressure += volume * (body / range_size)
                else:
                    selling_pressure += volume * (body / range_size)
        
        total_pressure = buying_pressure + selling_pressure
        
        if total_pressure == 0:
            return {'pattern': OrderFlowPattern.BALANCED.value, 'strength': 0}
        
        buy_ratio = buying_pressure / total_pressure
        
        # Classify order flow
        if buy_ratio > 0.7:
            pattern = OrderFlowPattern.AGGRESSIVE_BUYING
            strength = min(1.0, (buy_ratio - 0.7) * 3.33)
        elif buy_ratio < 0.3:
            pattern = OrderFlowPattern.AGGRESSIVE_SELLING
            strength = min(1.0, (0.3 - buy_ratio) * 3.33)
        elif 0.55 < buy_ratio < 0.7:
            pattern = OrderFlowPattern.PASSIVE_ACCUMULATION
            strength = (buy_ratio - 0.55) * 6.67
        elif 0.3 < buy_ratio < 0.45:
            pattern = OrderFlowPattern.PASSIVE_DISTRIBUTION
            strength = (0.45 - buy_ratio) * 6.67
        else:
            pattern = OrderFlowPattern.BALANCED
            strength = 0.5
        
        return {
            'pattern': pattern.value,
            'strength': round(strength, 2),
            'buy_ratio': round(buy_ratio, 2),
            'interpretation': self._interpret_order_flow(pattern, strength)
        }
    
    def _detect_position_building(self, price_data: List[Dict],
                                volume_data: List[Dict]) -> Dict[str, Any]:
        """Detect institutional position building."""
        if len(price_data) < self.thresholds['position_building_periods']:
            return {'detected': False}
        
        # Look for consistent accumulation/distribution
        periods = self.thresholds['position_building_periods']
        recent_candles = price_data[-periods:]
        recent_volumes = volume_data[-periods:]
        
        # Check for consistent direction with increasing volume
        directions = [1 if c['close'] > c['open'] else -1 for c in recent_candles]
        
        # Accumulation pattern
        if sum(directions) >= periods - 1:  # Mostly bullish
            volume_trend = self._check_volume_trend(recent_volumes)
            if volume_trend == 'increasing':
                return {
                    'detected': True,
                    'type': InstitutionalFootprint.POSITION_BUILDING,
                    'direction': 'long',
                    'periods': periods,
                    'interpretation': "🏗️ Institutional long position building detected",
                    'reliability': 0.8
                }
        
        # Distribution pattern
        elif sum(directions) <= -(periods - 1):  # Mostly bearish
            volume_trend = self._check_volume_trend(recent_volumes)
            if volume_trend == 'increasing':
                return {
                    'detected': True,
                    'type': InstitutionalFootprint.POSITION_BUILDING,
                    'direction': 'short',
                    'periods': periods,
                    'interpretation': "🏗️ Institutional short position building detected",
                    'reliability': 0.8
                }
        
        return {'detected': False}
    
    def _interpret_footprints(self, footprints: List[Dict],
                            order_flow: Dict, position_building: Dict) -> str:
        """Generate interpretation of detected footprints."""
        if not footprints and order_flow['pattern'] == OrderFlowPattern.BALANCED.value:
            return "No significant institutional activity detected"
        
        interpretations = []
        
        # Prioritize footprints
        if footprints:
            primary_footprint = max(footprints, key=lambda x: x.get('reliability', 0))
            interpretations.append(primary_footprint['interpretation'])
        
        # Add order flow context
        if order_flow['strength'] > 0.7:
            interpretations.append(order_flow['interpretation'])
        
        # Add position building
        if position_building['detected']:
            interpretations.append(position_building['interpretation'])
        
        return ' | '.join(interpretations[:2])  # Top 2 interpretations
    
    def _calculate_institutional_probability(self, footprints: List[Dict],
                                          order_flow: Dict) -> float:
        """Calculate probability of institutional involvement."""
        if not footprints:
            base_probability = 0.2
        else:
            # Average reliability of detected footprints
            base_probability = statistics.mean(
                [f.get('reliability', 0.5) for f in footprints]
            )
        
        # Adjust for order flow
        if order_flow['pattern'] in [OrderFlowPattern.AGGRESSIVE_BUYING.value,
                                     OrderFlowPattern.AGGRESSIVE_SELLING.value]:
            base_probability = min(1.0, base_probability + 0.2)
        
        return round(base_probability, 2)
    
    def _get_trading_implications(self, footprints: List[Dict],
                                order_flow: Dict) -> List[str]:
        """Generate trading implications from microstructure analysis."""
        implications = []
        
        # Check for whale activity
        whale_footprints = [f for f in footprints 
                           if f.get('type') in [InstitutionalFootprint.WHALE_ACCUMULATION,
                                               InstitutionalFootprint.WHALE_DISTRIBUTION]]
        if whale_footprints:
            whale_type = whale_footprints[0]['type']
            if whale_type == InstitutionalFootprint.WHALE_ACCUMULATION:
                implications.append("🐋 Follow whale accumulation - Consider long positions")
            else:
                implications.append("🐋 Whale distribution detected - Consider shorts or exit longs")
        
        # Check for iceberg orders
        if any(f.get('type') == InstitutionalFootprint.ICEBERG_ORDER for f in footprints):
            implications.append("🧊 Hidden liquidity present - Expect extended consolidation")
        
        # Check for smart money reversal
        reversal_footprints = [f for f in footprints
                              if f.get('type') == InstitutionalFootprint.SMART_MONEY_REVERSAL]
        if reversal_footprints:
            direction = reversal_footprints[0].get('direction', 'unknown')
            implications.append(f"🔄 Smart money {direction} reversal - Trade the new direction")
        
        # Order flow implications
        if order_flow['pattern'] == OrderFlowPattern.AGGRESSIVE_BUYING.value:
            implications.append("📈 Strong buying pressure - Bullish bias")
        elif order_flow['pattern'] == OrderFlowPattern.AGGRESSIVE_SELLING.value:
            implications.append("📉 Strong selling pressure - Bearish bias")
        
        return implications[:3]  # Top 3 implications
    
    def _identify_institutional_levels(self, price_data: List[Dict],
                                     footprints: List[Dict]) -> List[Dict[str, Any]]:
        """Identify key institutional levels from footprints."""
        levels = []
        
        # Extract levels from footprints
        for footprint in footprints:
            if footprint.get('type') == InstitutionalFootprint.ICEBERG_ORDER:
                levels.append({
                    'price': footprint.get('price_level'),
                    'type': 'iceberg',
                    'description': 'Hidden institutional orders'
                })
        
        # Add high volume nodes
        if len(price_data) >= 10:
            volume_weighted_prices = []
            for i, candle in enumerate(price_data[-10:]):
                mid_price = (candle['high'] + candle['low']) / 2
                volume_weighted_prices.append(mid_price)
            
            if volume_weighted_prices:
                vwap = statistics.mean(volume_weighted_prices)
                levels.append({
                    'price': round(vwap, 5),
                    'type': 'vwap',
                    'description': 'Volume-weighted average price'
                })
        
        return levels
    
    def _get_average_size(self, orders: List[Dict]) -> float:
        """Calculate average order size."""
        if not orders:
            return 0
        sizes = [o.get('size', 0) for o in orders]
        return statistics.mean(sizes) if sizes else 0
    
    def _detect_order_clustering(self, orders: List[Dict]) -> str:
        """Detect if orders are clustered at specific levels."""
        if len(orders) < 5:
            return 'insufficient_data'
        
        # Group orders by price proximity
        price_groups = {}
        for order in orders[:10]:  # Top 10 orders
            price = order.get('price', 0)
            grouped = False
            
            for group_price in price_groups:
                if abs(price - group_price) / group_price < 0.001:  # 0.1% proximity
                    price_groups[group_price].append(order)
                    grouped = True
                    break
            
            if not grouped:
                price_groups[price] = [order]
        
        # Check for clustering
        max_cluster = max(len(orders) for orders in price_groups.values())
        
        if max_cluster >= 3:
            return 'high_clustering'
        elif max_cluster >= 2:
            return 'moderate_clustering'
        else:
            return 'dispersed'
    
    def _interpret_depth_imbalance(self, bid_ratio: float, inst_bias: str,
                                  large_bids: List, large_asks: List) -> str:
        """Interpret order book imbalance."""
        if inst_bias == 'bullish':
            return f"Institutional buyers present - {len(large_bids)} large bid orders"
        elif inst_bias == 'bearish':
            return f"Institutional sellers present - {len(large_asks)} large ask orders"
        else:
            return "Balanced order book - No clear institutional bias"
    
    def _find_volume_nodes(self, price_data: List[Dict],
                         volume_data: List[Dict]) -> List[Dict]:
        """Find high volume price nodes."""
        nodes = []
        
        # Create price-volume profile
        price_volume = {}
        for i, candle in enumerate(price_data):
            price_level = round((candle['high'] + candle['low']) / 2, 5)
            volume = volume_data[i].get('volume', 0)
            
            if price_level not in price_volume:
                price_volume[price_level] = 0
            price_volume[price_level] += volume
        
        # Find high volume nodes
        avg_volume = statistics.mean(price_volume.values()) if price_volume else 0
        
        for price, volume in price_volume.items():
            if volume > avg_volume * 1.5:
                # Determine node type
                current_price = price_data[-1]['close']
                if price > current_price:
                    node_type = 'resistance'
                    bias = 'bearish'
                else:
                    node_type = 'support'
                    bias = 'bullish'
                
                nodes.append({
                    'price': price,
                    'volume': volume,
                    'type': node_type,
                    'bias': bias,
                    'strength': min(1.0, volume / (avg_volume * 3))
                })
        
        return nodes
    
    def _has_institutional_characteristics(self, node: Dict,
                                         price_data: List[Dict]) -> bool:
        """Check if volume node has institutional characteristics."""
        # High volume node with multiple touches
        touches = 0
        for candle in price_data:
            if (candle['low'] <= node['price'] <= candle['high']):
                touches += 1
        
        return touches >= 3 and node['strength'] > 0.7
    
    def _get_zone_description(self, node: Dict) -> str:
        """Generate description for smart money zone."""
        if node['type'] == 'support':
            return f"Institutional buying zone - High volume {node['type']}"
        else:
            return f"Institutional selling zone - High volume {node['type']}"
    
    def _check_volume_trend(self, volumes: List[Dict]) -> str:
        """Check if volume is trending."""
        if len(volumes) < 3:
            return 'unknown'
        
        volume_values = [v.get('volume', 0) for v in volumes]
        
        # Simple linear trend
        first_half_avg = statistics.mean(volume_values[:len(volumes)//2])
        second_half_avg = statistics.mean(volume_values[len(volumes)//2:])
        
        if second_half_avg > first_half_avg * 1.2:
            return 'increasing'
        elif second_half_avg < first_half_avg * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _interpret_order_flow(self, pattern: OrderFlowPattern, strength: float) -> str:
        """Generate order flow interpretation."""
        interpretations = {
            OrderFlowPattern.AGGRESSIVE_BUYING: "Aggressive institutional buying detected",
            OrderFlowPattern.AGGRESSIVE_SELLING: "Aggressive institutional selling detected",
            OrderFlowPattern.PASSIVE_ACCUMULATION: "Quiet accumulation in progress",
            OrderFlowPattern.PASSIVE_DISTRIBUTION: "Stealth distribution occurring",
            OrderFlowPattern.BALANCED: "Balanced order flow - No directional bias"
        }
        
        base_interpretation = interpretations.get(pattern, "Unknown order flow")
        
        if strength > 0.8:
            return f"🔥 {base_interpretation} (Very Strong)"
        elif strength > 0.6:
            return f"💪 {base_interpretation} (Strong)"
        else:
            return base_interpretation
    
    def _get_no_footprint_result(self) -> Dict[str, Any]:
        """Return result when no footprints detected."""
        return {
            'footprints_detected': 0,
            'footprints': [],
            'order_flow': {'pattern': OrderFlowPattern.BALANCED.value, 'strength': 0},
            'position_building': {'detected': False},
            'interpretation': 'No significant institutional activity detected',
            'institutional_probability': 0.2,
            'trading_implications': ['Trade with standard approach'],
            'key_levels': []
        }


# Example usage
if __name__ == "__main__":
    detector = MicroStructure()
    
    # Test data
    test_price_data = [
        {'open': 1.0840, 'high': 1.0845, 'low': 1.0838, 'close': 1.0842},
        {'open': 1.0842, 'high': 1.0843, 'low': 1.0840, 'close': 1.0841},
        {'open': 1.0841, 'high': 1.0841, 'low': 1.0839, 'close': 1.0840},
        {'open': 1.0840, 'high': 1.0842, 'low': 1.0839, 'close': 1.0841},
        {'open': 1.0841, 'high': 1.0845, 'low': 1.0841, 'close': 1.0844}
    ]
    
    test_volume_data = [
        {'volume': 1000},
        {'volume': 1200},
        {'volume': 3500},  # Whale volume
        {'volume': 1100},
        {'volume': 1300}
    ]
    
    # Detect footprints
    result = detector.detect_institutional_footprints(test_price_data, test_volume_data)
    
    print("Microstructure Analysis:")
    print(f"Footprints Detected: {result['footprints_detected']}")
    print(f"Interpretation: {result['interpretation']}")
    print(f"Institutional Probability: {result['institutional_probability']:.0%}")
    
    print("\nTrading Implications:")
    for impl in result['trading_implications']:
        print(f"  {impl}")