#!/usr/bin/env python3
"""
Fixed Market Data Receiver - Addresses specific issues found
- Fast response times
- No threading issues
- Handles malformed POST requests gracefully
- Rate limiting for excessive GET requests
"""

from flask import Flask, request, jsonify
import json
import time
from datetime import datetime
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple in-memory storage
market_data_store = defaultdict(lambda: {
    'ticks': [],
    'last_update': None,
    'sources': set()
})

# Rate limiting for GET requests
request_counts = defaultdict(int)
last_request_time = defaultdict(float)

# Configuration
STALE_DATA_THRESHOLD = 30
MAX_REQUESTS_PER_SECOND = 10
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

def check_rate_limit(client_ip):
    """Simple rate limiting"""
    current_time = time.time()
    
    # Reset counter if more than 1 second has passed
    if current_time - last_request_time[client_ip] > 1.0:
        request_counts[client_ip] = 0
        last_request_time[client_ip] = current_time
    
    request_counts[client_ip] += 1
    
    if request_counts[client_ip] > MAX_REQUESTS_PER_SECOND:
        return False
    
    return True

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """Handle market data POST requests with better error handling"""
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    try:
        # Check for JSON content
        if not request.is_json:
            logger.warning(f"Non-JSON request from {client_ip}")
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json(force=True)
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Extract basic info
        broker = data.get('broker', 'unknown')
        uuid = data.get('uuid', 'unknown')
        ticks = data.get('ticks', [])
        
        valid_ticks = 0
        current_time = time.time()
        
        for tick in ticks:
            try:
                symbol = tick.get('symbol', '').upper()
                
                # Validate symbol
                if not symbol or symbol not in VALID_SYMBOLS:
                    continue
                
                # Store tick data (keep last 20 only)
                tick_data = {
                    'bid': float(tick.get('bid', 0)),
                    'ask': float(tick.get('ask', 0)),
                    'volume': int(tick.get('volume', 0)),
                    'time': tick.get('time', current_time),
                    'broker': broker
                }
                
                # Add to storage and limit size
                market_data_store[symbol]['ticks'].append(tick_data)
                if len(market_data_store[symbol]['ticks']) > 20:
                    market_data_store[symbol]['ticks'] = market_data_store[symbol]['ticks'][-20:]
                
                market_data_store[symbol]['last_update'] = current_time
                market_data_store[symbol]['sources'].add(uuid)
                
                valid_ticks += 1
                
            except (ValueError, TypeError) as e:
                continue
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"POST /market-data: {valid_ticks} ticks from {uuid} ({duration:.1f}ms)")
        
        return jsonify({
            'status': 'success',
            'processed': valid_ticks,
            'broker': broker,
            'processing_time_ms': round(duration, 1)
        }), 200
        
    except json.JSONDecodeError:
        duration = (time.time() - start_time) * 1000
        logger.error(f"JSON decode error from {client_ip} ({duration:.1f}ms)")
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"POST /market-data error from {client_ip} ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Fast health check with rate limiting"""
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    try:
        current_time = time.time()
        active_symbols = 0
        total_sources = set()
        
        # Quick check - don't iterate if no data
        if not market_data_store:
            duration = (time.time() - start_time) * 1000
            return jsonify({
                'status': 'healthy',
                'active_symbols': 0,
                'total_sources': 0,
                'timestamp': datetime.now().isoformat(),
                'response_time_ms': round(duration, 1)
            }), 200
        
        # Check active symbols
        for symbol in VALID_SYMBOLS:
            data = market_data_store[symbol]
            if data['last_update'] and (current_time - data['last_update']) < STALE_DATA_THRESHOLD:
                active_symbols += 1
                total_sources.update(data['sources'])
        
        duration = (time.time() - start_time) * 1000
        
        return jsonify({
            'status': 'healthy',
            'active_symbols': active_symbols,
            'total_sources': len(total_sources),
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': round(duration, 1)
        }), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Health check error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/venom-feed', methods=['GET'])
def get_venom_feed():
    """VENOM feed endpoint with rate limiting"""
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    try:
        symbol = request.args.get('symbol')
        
        if not symbol:
            return jsonify({'error': 'Symbol parameter required'}), 400
        
        if symbol not in VALID_SYMBOLS:
            return jsonify({'error': f'Invalid symbol. Valid: {", ".join(VALID_SYMBOLS)}'}), 400
        
        data = market_data_store[symbol]
        
        if data['ticks'] and data['last_update']:
            current_time = time.time()
            if (current_time - data['last_update']) < STALE_DATA_THRESHOLD:
                latest_tick = data['ticks'][-1]
                
                duration = (time.time() - start_time) * 1000
                
                response = {
                    'symbol': symbol,
                    'bid': latest_tick.get('bid', 0),
                    'ask': latest_tick.get('ask', 0),
                    'spread': abs(latest_tick.get('ask', 0) - latest_tick.get('bid', 0)),
                    'volume': latest_tick.get('volume', 0),
                    'time': latest_tick.get('time', current_time),
                    'broker': latest_tick.get('broker', 'unknown'),
                    'sources': len(data['sources']),
                    'last_update': data['last_update'],
                    'response_time_ms': round(duration, 1)
                }
                
                return jsonify(response), 200
        
        duration = (time.time() - start_time) * 1000
        return jsonify({
            'error': 'No recent data available', 
            'response_time_ms': round(duration, 1)
        }), 404
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"VENOM feed error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/all', methods=['GET'])
def get_all_market_data():
    """Get all market data with rate limiting"""
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    # Special handling for fast=true parameter (common polling)
    if request.args.get('fast') == 'true':
        if not check_rate_limit(client_ip):
            return jsonify({
                'error': 'Rate limit exceeded - too many fast requests',
                'data': {},
                'total_symbols': 0
            }), 429
    
    try:
        current_time = time.time()
        all_data = {}
        
        for symbol in VALID_SYMBOLS:
            data = market_data_store[symbol]
            
            if data['ticks'] and data['last_update']:
                if (current_time - data['last_update']) < STALE_DATA_THRESHOLD:
                    latest_tick = data['ticks'][-1]
                    
                    all_data[symbol] = {
                        'bid': latest_tick.get('bid', 0),
                        'ask': latest_tick.get('ask', 0),
                        'volume': latest_tick.get('volume', 0),
                        'time': latest_tick.get('time', current_time),
                        'broker': latest_tick.get('broker', 'unknown'),
                        'last_update': data['last_update']
                    }
        
        duration = (time.time() - start_time) * 1000
        
        return jsonify({
            'data': all_data,
            'timestamp': datetime.now().isoformat(),
            'total_symbols': len(all_data),
            'response_time_ms': round(duration, 1)
        }), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"GET /all error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/order-flow', methods=['GET'])
def get_order_flow():
    """Get order flow data for a symbol"""
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    if not check_rate_limit(client_ip):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    try:
        symbol = request.args.get('symbol')
        if not symbol or symbol not in VALID_SYMBOLS:
            return jsonify({'error': 'Valid symbol required'}), 400
        
        data = market_data_store[symbol]
        ticks = data['ticks']
        
        if len(ticks) < 2:
            return jsonify({
                'order_flow': {'imbalance': 0, 'bid_volume': 0, 'ask_volume': 0},
                'liquidity': {'levels_above': [], 'levels_below': []}
            }), 200
        
        # Simple order flow calculation
        recent_ticks = ticks[-10:] if len(ticks) >= 10 else ticks
        bid_volume = sum(t.get('volume', 0) for t in recent_ticks)
        ask_volume = bid_volume  # Simplified
        total_volume = bid_volume + ask_volume
        imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
        
        duration = (time.time() - start_time) * 1000
        
        return jsonify({
            'order_flow': {
                'imbalance': round(imbalance, 3),
                'bid_volume': bid_volume,
                'ask_volume': ask_volume
            },
            'liquidity': {
                'levels_above': [],
                'levels_below': []
            },
            'response_time_ms': round(duration, 1)
        }), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Order flow error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Fixed Market Data Receiver on port 8001")
    logger.info(f"Valid symbols: {len(VALID_SYMBOLS)} pairs")
    logger.info(f"Rate limit: {MAX_REQUESTS_PER_SECOND} requests/second per IP")
    logger.info("Features: Rate limiting, better error handling, fast responses")
    logger.info("XAUUSD/GOLD is BLOCKED")
    
    # Single-threaded Flask configuration
    app.run(
        host='0.0.0.0', 
        port=8001, 
        debug=False, 
        threaded=False,  # Single-threaded to avoid issues
        processes=1,     # Single process
        use_reloader=False
    )