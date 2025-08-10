#!/usr/bin/env python3
"""
CITADEL PROTECTION MONITOR v1.0
Independent 24/7 market protection and liquidity sweep detection service

Author: BITTEN Trading System
Date: August 6, 2025
Purpose: Real-time liquidity zone tracking and protection scoring
"""

import zmq
import json
import time
import logging
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import redis
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CITADEL - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/citadel_protection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LiquidityZone:
    def __init__(self, price: float, zone_type: str, strength: int, created_at: float):
        self.price = price
        self.zone_type = zone_type  # 'resistance' or 'support'
        self.strength = strength    # 1-10 based on touches and volume
        self.created_at = created_at
        self.last_test = created_at
        self.test_count = 0
        self.volume_at_creation = 0
        self.swept = False
        self.sweep_time = None

class MarketSweep:
    def __init__(self, symbol: str, sweep_type: str, price: float, timestamp: float):
        self.symbol = symbol
        self.sweep_type = sweep_type  # 'bullish_sweep' or 'bearish_sweep'
        self.price = price
        self.timestamp = timestamp
        self.recovery_time = None
        self.recovery_strength = 0

class CITADEL_Monitor:
    def __init__(self):
        self.context = zmq.Context()
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Market data subscriber (port 5560)
        self.market_subscriber = self.context.socket(zmq.SUB)
        self.market_subscriber.connect("tcp://127.0.0.1:5560")
        self.market_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Protection score query responder (port 5566)
        self.query_socket = self.context.socket(zmq.REP)
        self.query_socket.bind("tcp://*:5566")
        
        # Alert publisher (port 5565)
        self.alert_publisher = self.context.socket(zmq.PUB)
        self.alert_publisher.bind("tcp://*:5565")
        
        # Data structures
        self.liquidity_zones = defaultdict(list)  # symbol -> [LiquidityZone]
        self.recent_sweeps = defaultdict(deque)   # symbol -> deque[MarketSweep]
        self.market_data = defaultdict(dict)      # symbol -> latest_data
        self.price_history = defaultdict(deque)   # symbol -> deque[price_points]
        
        # Configuration
        self.sweep_threshold = 3.0  # pips for sweep detection
        self.zone_strength_decay = 0.95  # daily decay factor
        self.max_history_size = 1000
        self.sweep_history_hours = 24
        
        self.running = True
        
        logger.info("🛡️ CITADEL Protection Monitor v1.0 initialized")

    def update_liquidity_zones(self, symbol: str, price_data: Dict):
        """Find and update liquidity zones based on swing highs/lows"""
        try:
            current_price = float(price_data.get('bid', 0))
            volume = float(price_data.get('volume', 0))
            timestamp = time.time()
            
            # Add to price history
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=self.max_history_size)
            
            self.price_history[symbol].append({
                'price': current_price,
                'volume': volume,
                'timestamp': timestamp
            })
            
            # Need at least 20 data points to identify zones
            if len(self.price_history[symbol]) < 20:
                return
            
            # Find swing highs and lows (last 50 periods)
            recent_data = list(self.price_history[symbol])[-50:]
            swing_highs = self._find_swing_highs(recent_data)
            swing_lows = self._find_swing_lows(recent_data)
            
            # Update liquidity zones
            for high in swing_highs:
                self._add_or_update_zone(symbol, high['price'], 'resistance', high['strength'], timestamp)
            
            for low in swing_lows:
                self._add_or_update_zone(symbol, low['price'], 'support', low['strength'], timestamp)
            
            # Clean old zones (older than 24 hours)
            self._clean_old_zones(symbol, timestamp)
            
            logger.debug(f"Updated liquidity zones for {symbol}: {len(self.liquidity_zones[symbol])} zones")
            
        except Exception as e:
            logger.error(f"Error updating liquidity zones for {symbol}: {str(e)}")

    def _find_swing_highs(self, data: List[Dict]) -> List[Dict]:
        """Identify swing highs with volume confirmation"""
        swing_highs = []
        
        for i in range(5, len(data) - 5):
            current = data[i]
            is_swing_high = True
            
            # Check if current point is higher than surrounding points
            for j in range(i - 5, i + 6):
                if j != i and data[j]['price'] >= current['price']:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                # Calculate strength based on volume and price action
                volume_strength = min(current['volume'] / 1000, 5)  # Max 5 points from volume
                price_significance = self._calculate_price_significance(data, i)
                
                swing_highs.append({
                    'price': current['price'],
                    'strength': int(volume_strength + price_significance),
                    'timestamp': current['timestamp']
                })
        
        return swing_highs

    def _find_swing_lows(self, data: List[Dict]) -> List[Dict]:
        """Identify swing lows with volume confirmation"""
        swing_lows = []
        
        for i in range(5, len(data) - 5):
            current = data[i]
            is_swing_low = True
            
            # Check if current point is lower than surrounding points
            for j in range(i - 5, i + 6):
                if j != i and data[j]['price'] <= current['price']:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                # Calculate strength based on volume and price action
                volume_strength = min(current['volume'] / 1000, 5)
                price_significance = self._calculate_price_significance(data, i)
                
                swing_lows.append({
                    'price': current['price'],
                    'strength': int(volume_strength + price_significance),
                    'timestamp': current['timestamp']
                })
        
        return swing_lows

    def _calculate_price_significance(self, data: List[Dict], index: int) -> float:
        """Calculate how significant a price level is based on touches and reactions"""
        current_price = data[index]['price']
        significance = 1.0
        
        # Look for price reactions around this level (within 2 pips)
        pip_size = 0.0001 if 'JPY' not in str(current_price) else 0.01
        tolerance = 2 * pip_size
        
        touches = 0
        for point in data:
            if abs(point['price'] - current_price) <= tolerance:
                touches += 1
        
        # More touches = more significant
        significance += min(touches * 0.5, 3.0)
        
        return significance

    def _add_or_update_zone(self, symbol: str, price: float, zone_type: str, strength: int, timestamp: float):
        """Add new liquidity zone or update existing one"""
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        tolerance = 5 * pip_size
        
        # Check if zone already exists
        for zone in self.liquidity_zones[symbol]:
            if abs(zone.price - price) <= tolerance and zone.zone_type == zone_type:
                # Update existing zone
                zone.test_count += 1
                zone.last_test = timestamp
                zone.strength = min(zone.strength + 1, 10)  # Cap at 10
                return
        
        # Create new zone
        new_zone = LiquidityZone(price, zone_type, min(strength, 10), timestamp)
        self.liquidity_zones[symbol].append(new_zone)
        
        # Limit number of zones per symbol
        if len(self.liquidity_zones[symbol]) > 20:
            self.liquidity_zones[symbol].sort(key=lambda z: z.strength, reverse=True)
            self.liquidity_zones[symbol] = self.liquidity_zones[symbol][:15]

    def _clean_old_zones(self, symbol: str, current_time: float):
        """Remove zones older than 24 hours"""
        cutoff_time = current_time - (24 * 3600)  # 24 hours ago
        
        self.liquidity_zones[symbol] = [
            zone for zone in self.liquidity_zones[symbol] 
            if zone.created_at > cutoff_time
        ]

    def check_for_sweep(self, symbol: str, price_data: Dict):
        """Real-time detection of liquidity sweeps"""
        try:
            current_price = float(price_data.get('bid', 0))
            volume = float(price_data.get('volume', 0))
            timestamp = time.time()
            
            pip_size = 0.0001 if 'JPY' not in symbol else 0.01
            
            for zone in self.liquidity_zones[symbol]:
                if zone.swept:
                    continue
                
                # Check for bullish sweep (price spikes above resistance then falls back)
                if zone.zone_type == 'resistance':
                    if current_price > (zone.price + self.sweep_threshold * pip_size):
                        # Potential bullish sweep - need to see reversal
                        if self._confirm_sweep_reversal(symbol, zone.price, 'bullish', timestamp):
                            self._record_sweep(symbol, zone, 'bullish_sweep', timestamp)
                
                # Check for bearish sweep (price spikes below support then recovers)
                elif zone.zone_type == 'support':
                    if current_price < (zone.price - self.sweep_threshold * pip_size):
                        # Potential bearish sweep - need to see reversal
                        if self._confirm_sweep_reversal(symbol, zone.price, 'bearish', timestamp):
                            self._record_sweep(symbol, zone, 'bearish_sweep', timestamp)
            
        except Exception as e:
            logger.error(f"Error checking for sweep on {symbol}: {str(e)}")

    def _confirm_sweep_reversal(self, symbol: str, zone_price: float, sweep_type: str, timestamp: float) -> bool:
        """Confirm that price reversed after sweeping the zone"""
        if len(self.price_history[symbol]) < 10:
            return False
        
        recent_prices = list(self.price_history[symbol])[-10:]
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        
        if sweep_type == 'bullish':
            # Look for price falling back below the zone after spiking above
            max_price = max([p['price'] for p in recent_prices[-5:]])
            current_price = recent_prices[-1]['price']
            
            return (max_price > zone_price + self.sweep_threshold * pip_size and 
                   current_price < zone_price + pip_size)
        
        else:  # bearish sweep
            # Look for price recovering above the zone after spiking below
            min_price = min([p['price'] for p in recent_prices[-5:]])
            current_price = recent_prices[-1]['price']
            
            return (min_price < zone_price - self.sweep_threshold * pip_size and 
                   current_price > zone_price - pip_size)

    def _record_sweep(self, symbol: str, zone: LiquidityZone, sweep_type: str, timestamp: float):
        """Record a confirmed liquidity sweep"""
        zone.swept = True
        zone.sweep_time = timestamp
        
        sweep = MarketSweep(symbol, sweep_type, zone.price, timestamp)
        
        # Add to recent sweeps with 24-hour expiry
        if symbol not in self.recent_sweeps:
            self.recent_sweeps[symbol] = deque(maxlen=100)
        
        self.recent_sweeps[symbol].append(sweep)
        
        # Publish alert
        alert = {
            'type': 'liquidity_sweep',
            'symbol': symbol,
            'sweep_type': sweep_type,
            'price': zone.price,
            'zone_strength': zone.strength,
            'timestamp': timestamp
        }
        
        self.alert_publisher.send_string(f"CITADEL_ALERT {json.dumps(alert)}")
        logger.warning(f"🚨 LIQUIDITY SWEEP DETECTED: {symbol} {sweep_type} at {zone.price}")
        
        # Store in Redis for persistence
        self.redis_client.lpush(f"sweeps:{symbol}", json.dumps(alert))
        self.redis_client.expire(f"sweeps:{symbol}", 86400)  # 24 hour expiry

    def calculate_protection_score(self, symbol: str, entry_price: float) -> Dict:
        """Calculate 1-10 protection score with detailed factors"""
        try:
            base_score = 5.0  # Neutral starting point
            factors = {}
            timestamp = time.time()
            
            # Factor 1: Distance from liquidity zones (30% weight)
            zone_risk = self._assess_zone_proximity(symbol, entry_price)
            zone_score = max(1, min(10, base_score + zone_risk))
            factors['zone_proximity'] = zone_score
            base_score = (base_score * 0.7) + (zone_score * 0.3)
            
            # Factor 2: Recent sweep activity (25% weight)
            sweep_protection = self._assess_sweep_protection(symbol, entry_price, timestamp)
            factors['sweep_protection'] = sweep_protection
            base_score = (base_score * 0.75) + (sweep_protection * 0.25)
            
            # Factor 3: Market volatility (20% weight)
            volatility_score = self._assess_market_volatility(symbol)
            factors['volatility'] = volatility_score
            base_score = (base_score * 0.8) + (volatility_score * 0.2)
            
            # Factor 4: Time-based risk (15% weight)
            time_score = self._assess_time_based_risk(timestamp)
            factors['time_risk'] = time_score
            base_score = (base_score * 0.85) + (time_score * 0.15)
            
            # Factor 5: Multi-timeframe confluence (10% weight)
            confluence_score = self._assess_timeframe_confluence(symbol, entry_price)
            factors['confluence'] = confluence_score
            base_score = (base_score * 0.9) + (confluence_score * 0.1)
            
            final_score = max(1.0, min(10.0, base_score))
            
            # Generate recommendation
            recommendation = self._generate_recommendation(final_score, factors)
            
            return {
                'symbol': symbol,
                'entry_price': entry_price,
                'protection_score': round(final_score, 1),
                'risk_level': self._get_risk_level(final_score),
                'recommendation': recommendation,
                'factors': factors,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error calculating protection score: {str(e)}")
            return {
                'symbol': symbol,
                'entry_price': entry_price,
                'protection_score': 5.0,
                'risk_level': 'UNKNOWN',
                'recommendation': 'Use caution - calculation error',
                'error': str(e)
            }

    def _assess_zone_proximity(self, symbol: str, entry_price: float) -> float:
        """Assess risk based on proximity to liquidity zones"""
        if symbol not in self.liquidity_zones or not self.liquidity_zones[symbol]:
            return 0  # No zones = neutral
        
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        min_distance = float('inf')
        strongest_zone_strength = 0
        
        for zone in self.liquidity_zones[symbol]:
            if zone.swept:
                continue
                
            distance_pips = abs(entry_price - zone.price) / pip_size
            
            if distance_pips < min_distance:
                min_distance = distance_pips
                strongest_zone_strength = zone.strength
        
        if min_distance == float('inf'):
            return 0  # No active zones
        
        # Score based on distance and zone strength
        if min_distance < 5:  # Very close to strong zone
            risk_penalty = -3 * (strongest_zone_strength / 10)
        elif min_distance < 15:  # Close to zone
            risk_penalty = -2 * (strongest_zone_strength / 10)
        elif min_distance < 30:  # Moderate distance
            risk_penalty = -1 * (strongest_zone_strength / 10)
        else:  # Safe distance
            risk_penalty = 1
        
        return risk_penalty

    def _assess_sweep_protection(self, symbol: str, entry_price: float, timestamp: float) -> float:
        """Higher score if recent sweep created favorable conditions"""
        if symbol not in self.recent_sweeps:
            return 5.0  # Neutral
        
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        recent_cutoff = timestamp - 3600  # Last hour
        
        protection_boost = 5.0
        
        for sweep in self.recent_sweeps[symbol]:
            if sweep.timestamp < recent_cutoff:
                continue
            
            distance_pips = abs(entry_price - sweep.price) / pip_size
            
            # Recent sweep near entry = good protection (liquidity grabbed)
            if distance_pips < 20:
                if sweep.sweep_type == 'bullish_sweep' and entry_price < sweep.price:
                    protection_boost += 2.5  # Buying after bullish sweep above
                elif sweep.sweep_type == 'bearish_sweep' and entry_price > sweep.price:
                    protection_boost += 2.5  # Selling after bearish sweep below
        
        return min(10.0, protection_boost)

    def _assess_market_volatility(self, symbol: str) -> float:
        """Score based on current market volatility"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return 5.0
        
        # Calculate recent volatility (last 20 periods)
        recent_prices = [p['price'] for p in list(self.price_history[symbol])[-20:]]
        volatility = np.std(recent_prices) if len(recent_prices) > 1 else 0
        
        # Normalize volatility score (lower volatility = higher protection)
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        volatility_pips = volatility / pip_size
        
        if volatility_pips < 5:
            return 8.0  # Low volatility = safer
        elif volatility_pips < 15:
            return 6.0  # Medium volatility
        elif volatility_pips < 30:
            return 4.0  # High volatility
        else:
            return 2.0  # Extreme volatility = dangerous

    def _assess_time_based_risk(self, timestamp: float) -> float:
        """Score based on trading session and market hours"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        
        # London session (8-17 GMT) - highest liquidity
        if 8 <= hour <= 17:
            return 8.0
        # New York session (13-22 GMT) - good liquidity  
        elif 13 <= hour <= 22:
            return 7.0
        # Asian session (0-9 GMT) - moderate liquidity
        elif 0 <= hour <= 9:
            return 5.0
        # Low liquidity hours
        else:
            return 3.0

    def _assess_timeframe_confluence(self, symbol: str, entry_price: float) -> float:
        """Assess multi-timeframe alignment (simplified)"""
        # This would require multiple timeframe data - simplified for now
        return 6.0  # Neutral confluence

    def _generate_recommendation(self, score: float, factors: Dict) -> str:
        """Generate human-readable recommendation"""
        if score >= 8.5:
            return "FORTRESS PROTECTION - Ideal entry conditions"
        elif score >= 7.0:
            return "STRONG PROTECTION - Good entry with minor risks"
        elif score >= 5.5:
            return "MODERATE PROTECTION - Average risk/reward"
        elif score >= 4.0:
            return "ELEVATED RISK - Exercise caution"
        elif score >= 2.5:
            return "HIGH RISK - Consider avoiding"
        else:
            return "EXTREME DANGER - Liquidity sweep imminent"

    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score >= 8.0:
            return "FORTRESS"
        elif score >= 6.0:
            return "PROTECTED"
        elif score >= 4.0:
            return "CAUTION"
        elif score >= 2.0:
            return "HIGH_RISK"
        else:
            return "DANGER"

    def detect_manipulation(self, symbol: str, price_data: Dict) -> Optional[Dict]:
        """Detect stop hunting and manipulation patterns"""
        try:
            if len(self.price_history[symbol]) < 50:
                return None
            
            recent_data = list(self.price_history[symbol])[-50:]
            current_price = float(price_data.get('bid', 0))
            volume = float(price_data.get('volume', 0))
            
            # Pattern 1: Volume spike with immediate reversal
            if len(recent_data) >= 10:
                avg_volume = np.mean([p['volume'] for p in recent_data[-20:-10]])
                recent_volume = np.mean([p['volume'] for p in recent_data[-5:]])
                
                if recent_volume > avg_volume * 2:  # 200% volume spike
                    price_range = max([p['price'] for p in recent_data[-5:]]) - min([p['price'] for p in recent_data[-5:]])
                    pip_size = 0.0001 if 'JPY' not in symbol else 0.01
                    
                    if price_range > 10 * pip_size:  # Significant price movement
                        return {
                            'type': 'volume_manipulation',
                            'confidence': 0.7,
                            'description': 'High volume with excessive price movement detected'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting manipulation for {symbol}: {str(e)}")
            return None

    def run_market_monitor(self):
        """Main market data processing loop"""
        logger.info("🔄 Starting market data monitoring...")
        
        while self.running:
            try:
                # Non-blocking receive with timeout
                if self.market_subscriber.poll(1000):  # 1 second timeout
                    message = self.market_subscriber.recv_string(zmq.NOBLOCK)
                    
                    try:
                        data = json.loads(message)
                        symbol = data.get('symbol', 'UNKNOWN')
                        
                        # Update market data
                        self.market_data[symbol] = data
                        
                        # Update liquidity zones
                        self.update_liquidity_zones(symbol, data)
                        
                        # Check for sweeps
                        self.check_for_sweep(symbol, data)
                        
                        # Check for manipulation
                        manipulation = self.detect_manipulation(symbol, data)
                        if manipulation:
                            alert = {
                                'type': 'manipulation_detected',
                                'symbol': symbol,
                                'details': manipulation,
                                'timestamp': time.time()
                            }
                            self.alert_publisher.send_string(f"CITADEL_ALERT {json.dumps(alert)}")
                    
                    except json.JSONDecodeError:
                        continue
                        
            except zmq.Again:
                continue
            except Exception as e:
                logger.error(f"Error in market monitor: {str(e)}")
                time.sleep(1)

    def run_query_responder(self):
        """Handle protection score queries"""
        logger.info("🔍 Starting protection score query service...")
        
        while self.running:
            try:
                # Wait for protection score requests
                if self.query_socket.poll(1000):  # 1 second timeout
                    request = self.query_socket.recv_string(zmq.NOBLOCK)
                    
                    try:
                        query = json.loads(request)
                        symbol = query.get('symbol', 'EURUSD')
                        entry_price = float(query.get('entry_price', 0))
                        
                        if entry_price > 0:
                            result = self.calculate_protection_score(symbol, entry_price)
                            self.query_socket.send_string(json.dumps(result))
                        else:
                            error_response = {
                                'error': 'Invalid entry_price',
                                'protection_score': 1.0,
                                'risk_level': 'ERROR'
                            }
                            self.query_socket.send_string(json.dumps(error_response))
                    
                    except (json.JSONDecodeError, ValueError) as e:
                        error_response = {
                            'error': f'Invalid request: {str(e)}',
                            'protection_score': 1.0,
                            'risk_level': 'ERROR'
                        }
                        self.query_socket.send_string(json.dumps(error_response))
                        
            except zmq.Again:
                continue
            except Exception as e:
                logger.error(f"Error in query responder: {str(e)}")
                time.sleep(1)

    def cleanup_old_data(self):
        """Periodic cleanup of old data"""
        while self.running:
            try:
                current_time = time.time()
                cutoff_time = current_time - (self.sweep_history_hours * 3600)
                
                # Clean old sweeps
                for symbol in self.recent_sweeps:
                    self.recent_sweeps[symbol] = deque([
                        sweep for sweep in self.recent_sweeps[symbol]
                        if sweep.timestamp > cutoff_time
                    ], maxlen=100)
                
                # Clean old zones
                for symbol in list(self.liquidity_zones.keys()):
                    self._clean_old_zones(symbol, current_time)
                
                logger.debug("🧹 Completed data cleanup cycle")
                time.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cleanup: {str(e)}")
                time.sleep(60)

    def start(self):
        """Start all monitoring services"""
        logger.info("🛡️ CITADEL Protection Monitor starting up...")
        
        # Start threads
        market_thread = threading.Thread(target=self.run_market_monitor, daemon=True)
        query_thread = threading.Thread(target=self.run_query_responder, daemon=True)
        cleanup_thread = threading.Thread(target=self.cleanup_old_data, daemon=True)
        
        market_thread.start()
        query_thread.start()
        cleanup_thread.start()
        
        logger.info("✅ All CITADEL services online")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(10)
                # Heartbeat log every minute
                if int(time.time()) % 60 == 0:
                    active_symbols = len(self.market_data)
                    total_zones = sum(len(zones) for zones in self.liquidity_zones.values())
                    total_sweeps = sum(len(sweeps) for sweeps in self.recent_sweeps.values())
                    
                    logger.info(f"🔄 CITADEL Status: {active_symbols} symbols, {total_zones} zones, {total_sweeps} recent sweeps")
        
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down CITADEL Protection Monitor...")
            self.running = False

if __name__ == "__main__":
    monitor = CITADEL_Monitor()
    monitor.start()