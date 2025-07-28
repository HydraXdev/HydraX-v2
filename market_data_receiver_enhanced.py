#!/usr/bin/env python3
"""
Enhanced Market Data Receiver - Provides data for VENOM + CITADEL
Collects not just tick data but also:
- Order flow imbalances
- Liquidity maps
- Volume profiles
- Broker comparisons
NO SYNTHETIC DATA - 100% real from MT5 terminals
"""

from flask import Flask, request, jsonify
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import logging
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enhanced market data storage
market_data_store = defaultdict(lambda: {
    'ticks': deque(maxlen=100),
    'volumes': deque(maxlen=100),
    'brokers': defaultdict(lambda: deque(maxlen=20)),
    'order_flow': {
        'bid_volume': 0,
        'ask_volume': 0,
        'imbalance': 0,
        'large_orders': deque(maxlen=10)
    },
    'liquidity_map': {
        'levels_above': [],
        'levels_below': [],
        'sweep_zones': []
    },
    'last_update': None,
    'sources': set()
})

# Aggregated analytics
analytics_store = defaultdict(lambda: {
    'volatility': 0,
    'trend_strength': 0,
    'institutional_bias': 'neutral',
    'retail_positioning': 'neutral'
})

# Lock for thread safety
data_lock = threading.Lock()

# Configuration
STALE_DATA_THRESHOLD = 30
LARGE_ORDER_THRESHOLD = 100000  # $100k+ orders

# Valid symbols (NO XAUUSD)
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

def calculate_order_flow_imbalance(symbol: str) -> dict:
    """Calculate order flow metrics for CITADEL"""
    with data_lock:
        data = market_data_store[symbol]
        
        # Get recent ticks
        recent_ticks = list(data['ticks'])[-20:]  # Last 20 ticks
        if len(recent_ticks) < 5:
            return data['order_flow']
        
        # Calculate bid/ask pressure
        bid_volume = sum(t.get('volume', 0) for t in recent_ticks if t.get('bid', 0) > 0)
        ask_volume = sum(t.get('volume', 0) for t in recent_ticks if t.get('ask', 0) > 0)
        
        # Calculate imbalance
        total_volume = bid_volume + ask_volume
        if total_volume > 0:
            imbalance = (bid_volume - ask_volume) / total_volume
        else:
            imbalance = 0
        
        # Update order flow
        data['order_flow']['bid_volume'] = bid_volume
        data['order_flow']['ask_volume'] = ask_volume
        data['order_flow']['imbalance'] = round(imbalance, 3)
        
        return data['order_flow']

def detect_liquidity_zones(symbol: str) -> dict:
    """Detect potential liquidity zones for sweep analysis"""
    with data_lock:
        data = market_data_store[symbol]
        ticks = list(data['ticks'])[-50:]  # Last 50 ticks
        
        if len(ticks) < 10:
            return data['liquidity_map']
        
        # Get current price
        current_price = ticks[-1].get('bid', 0)
        if current_price == 0:
            return data['liquidity_map']
        
        # Find price levels with high activity
        price_levels = defaultdict(int)
        for tick in ticks:
            price = round(tick.get('bid', 0), 5)
            volume = tick.get('volume', 0)
            price_levels[price] += volume
        
        # Sort by volume
        sorted_levels = sorted(price_levels.items(), key=lambda x: x[1], reverse=True)
        
        # Identify liquidity zones
        levels_above = []
        levels_below = []
        
        for price, volume in sorted_levels[:10]:  # Top 10 levels
            if volume > LARGE_ORDER_THRESHOLD:
                if price > current_price:
                    levels_above.append(price)
                else:
                    levels_below.append(price)
        
        # Update liquidity map
        data['liquidity_map']['levels_above'] = sorted(levels_above)[:3]
        data['liquidity_map']['levels_below'] = sorted(levels_below, reverse=True)[:3]
        
        # Detect potential sweep zones (clusters of liquidity)
        if levels_above and levels_below:
            nearest_above = min(levels_above)
            nearest_below = max(levels_below)
            
            # If liquidity is very close, it's a potential sweep zone
            if (nearest_above - current_price) < 0.0010:  # 10 pips
                data['liquidity_map']['sweep_zones'].append({
                    'zone': 'above',
                    'price': nearest_above,
                    'distance_pips': round((nearest_above - current_price) * 10000, 1)
                })
            
            if (current_price - nearest_below) < 0.0010:  # 10 pips
                data['liquidity_map']['sweep_zones'].append({
                    'zone': 'below',
                    'price': nearest_below,
                    'distance_pips': round((current_price - nearest_below) * 10000, 1)
                })
        
        # Keep only recent sweep zones
        data['liquidity_map']['sweep_zones'] = list(data['liquidity_map']['sweep_zones'])[-3:]
        
        return data['liquidity_map']

def analyze_broker_differences(symbol: str) -> dict:
    """Analyze differences between brokers for slippage detection"""
    with data_lock:
        data = market_data_store[symbol]
        broker_data = data['brokers']
        
        if len(broker_data) < 2:
            return {}
        
        # Compare spreads across brokers
        broker_spreads = {}
        for broker, ticks in broker_data.items():
            if ticks:
                recent_ticks = list(ticks)[-5:]
                avg_spread = statistics.mean([t.get('spread', 0) for t in recent_ticks])
                broker_spreads[broker] = avg_spread
        
        # Find best and worst brokers
        if broker_spreads:
            best_broker = min(broker_spreads.items(), key=lambda x: x[1])
            worst_broker = max(broker_spreads.items(), key=lambda x: x[1])
            
            return {
                'best_broker': best_broker[0],
                'best_spread': round(best_broker[1], 1),
                'worst_broker': worst_broker[0],
                'worst_spread': round(worst_broker[1], 1),
                'spread_difference': round(worst_broker[1] - best_broker[1], 1)
            }
        
        return {}

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """Enhanced receiver with order flow and liquidity tracking"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        uuid = data.get('uuid', 'unknown')
        ticks = data.get('ticks', [])
        broker = data.get('broker', 'Unknown')
        balance = data.get('account_balance', 0)
        
        # Process each tick
        valid_ticks = 0
        with data_lock:
            for tick in ticks:
                symbol = tick.get('symbol')
                
                # Block XAUUSD
                if not symbol or symbol not in VALID_SYMBOLS:
                    continue
                
                # Enhanced tick data
                enhanced_tick = {
                    **tick,
                    'uuid': uuid,
                    'broker': broker,
                    'balance': balance,
                    'received_at': time.time()
                }
                
                # Store by symbol
                market_data_store[symbol]['ticks'].append(enhanced_tick)
                market_data_store[symbol]['last_update'] = time.time()
                market_data_store[symbol]['sources'].add(uuid)
                
                # Store by broker for comparison
                market_data_store[symbol]['brokers'][broker].append(enhanced_tick)
                
                # Track volumes for large order detection
                volume = tick.get('volume', 0)
                if volume > 0:
                    market_data_store[symbol]['volumes'].append(volume)
                
                valid_ticks += 1
        
        # Update analytics after receiving data
        for symbol in VALID_SYMBOLS:
            calculate_order_flow_imbalance(symbol)
            detect_liquidity_zones(symbol)
        
        logger.info(f"Received {valid_ticks} valid ticks from {uuid} ({broker})")
        
        return jsonify({
            'status': 'success',
            'processed': valid_ticks,
            'broker': broker
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/venom-feed', methods=['GET'])
def get_venom_feed():
    """Enhanced feed for VENOM with CITADEL data"""
    symbol = request.args.get('symbol')
    
    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400
    
    if symbol not in VALID_SYMBOLS:
        return jsonify({'error': f'Invalid symbol. Use one of: {", ".join(VALID_SYMBOLS)}'}), 400
    
    with data_lock:
        data = market_data_store[symbol]
        
        # Check if data is fresh
        if not data['last_update'] or (time.time() - data['last_update']) > STALE_DATA_THRESHOLD:
            return jsonify({'error': 'No recent data available'}), 404
        
        # Get latest tick
        if data['ticks']:
            latest_tick = data['ticks'][-1]
            
            # Enhanced response with CITADEL data
            response = {
                'symbol': symbol,
                'ticks': [latest_tick],
                'order_flow': calculate_order_flow_imbalance(symbol),
                'liquidity_map': detect_liquidity_zones(symbol),
                'broker_analysis': analyze_broker_differences(symbol),
                'sources': len(data['sources']),
                'last_update': data['last_update']
            }
            
            return jsonify(response), 200
        else:
            return jsonify({'error': 'No tick data available'}), 404

@app.route('/market-data/order-flow', methods=['GET'])
def get_order_flow():
    """Get order flow data for CITADEL"""
    symbol = request.args.get('symbol')
    
    if not symbol or symbol not in VALID_SYMBOLS:
        return jsonify({'error': 'Valid symbol required'}), 400
    
    order_flow = calculate_order_flow_imbalance(symbol)
    return jsonify(order_flow), 200

@app.route('/market-data/liquidity', methods=['GET'])
def get_liquidity():
    """Get liquidity map for CITADEL sweep detection"""
    symbol = request.args.get('symbol')
    
    if not symbol or symbol not in VALID_SYMBOLS:
        return jsonify({'error': 'Valid symbol required'}), 400
    
    liquidity = detect_liquidity_zones(symbol)
    return jsonify(liquidity), 200

@app.route('/market-data/all', methods=['GET'])
def get_all_market_data():
    """Get all current market data with enhancements"""
    current_time = time.time()
    all_data = {}
    
    with data_lock:
        for symbol in VALID_SYMBOLS:
            data = market_data_store[symbol]
            
            # Skip stale data
            if not data['last_update'] or (current_time - data['last_update']) > STALE_DATA_THRESHOLD:
                continue
            
            # Get latest tick with enhancements
            if data['ticks']:
                latest_tick = data['ticks'][-1]
                # Make sure to convert any deque objects
                all_data[symbol] = {
                    **latest_tick,
                    'order_flow': dict(data['order_flow']),  # Convert to regular dict
                    'liquidity_nearby': bool(data['liquidity_map'].get('sweep_zones', [])),
                    'sources': len(data['sources'])
                }
    
    return jsonify(all_data), 200

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    active_symbols = 0
    total_sources = set()
    
    with data_lock:
        for symbol in VALID_SYMBOLS:
            if market_data_store[symbol]['last_update']:
                if (time.time() - market_data_store[symbol]['last_update']) < STALE_DATA_THRESHOLD:
                    active_symbols += 1
                    total_sources.update(market_data_store[symbol]['sources'])
    
    return jsonify({
        'status': 'healthy',
        'active_symbols': active_symbols,
        'total_sources': len(total_sources),
        'timestamp': datetime.now().isoformat()
    }), 200

def cleanup_stale_data():
    """Background task to clean up old data"""
    while True:
        try:
            current_time = time.time()
            
            with data_lock:
                for symbol in VALID_SYMBOLS:
                    data = market_data_store[symbol]
                    
                    # Clean old sweep zones
                    if data['liquidity_map']['sweep_zones']:
                        data['liquidity_map']['sweep_zones'] = [
                            zone for zone in data['liquidity_map']['sweep_zones']
                            if current_time - zone.get('detected_at', 0) < 300  # 5 min
                        ]
            
            time.sleep(60)  # Run every minute
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    logger.info("Starting Enhanced Market Data Receiver on port 8001")
    logger.info(f"Valid symbols: {', '.join(VALID_SYMBOLS)}")
    logger.info("XAUUSD/GOLD is BLOCKED")
    logger.info("Enhanced features: Order flow, Liquidity maps, Broker analysis")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_stale_data, daemon=True)
    cleanup_thread.start()
    
    # Start Flask
    app.run(host='0.0.0.0', port=8001, debug=False)