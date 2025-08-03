#!/usr/bin/env python3
"""
Simple Market Data Receiver - Fixed threading issues
Lightweight version focused on core functionality without threading problems
"""

from flask import Flask, request, jsonify
import json
import time
from datetime import datetime
from collections import defaultdict, deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple market data storage - NO LOCKS NEEDED
market_data_store = defaultdict(lambda: {
    'ticks': deque(maxlen=50),  # Reduced size to prevent memory issues
    'last_update': None,
    'sources': set()
})

# Configuration
STALE_DATA_THRESHOLD = 30
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """Simple market data receiver"""
    try:
        data = request.get_json()
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
                
                # Block XAUUSD and validate symbol
                if not symbol or symbol not in VALID_SYMBOLS:
                    continue
                
                # Store tick data
                tick_data = {
                    'bid': float(tick.get('bid', 0)),
                    'ask': float(tick.get('ask', 0)),
                    'volume': int(tick.get('volume', 0)),
                    'time': tick.get('time', current_time),
                    'broker': broker
                }
                
                # Simple storage without locks
                market_data_store[symbol]['ticks'].append(tick_data)
                market_data_store[symbol]['last_update'] = current_time
                market_data_store[symbol]['sources'].add(uuid)
                
                valid_ticks += 1
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid tick data: {e}")
                continue
        
        logger.info(f"Received {valid_ticks} valid ticks from {uuid} ({broker})")
        
        return jsonify({
            'status': 'success',
            'processed': valid_ticks,
            'broker': broker
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Health check endpoint - NO LOCKS"""
    active_symbols = 0
    total_sources = set()
    current_time = time.time()
    
    # Simple check without locks
    for symbol in VALID_SYMBOLS:
        data = market_data_store[symbol]
        if data['last_update'] and (current_time - data['last_update']) < STALE_DATA_THRESHOLD:
            active_symbols += 1
            total_sources.update(data['sources'])
    
    return jsonify({
        'status': 'healthy',
        'active_symbols': active_symbols,
        'total_sources': len(total_sources),
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/market-data/venom-feed', methods=['GET'])
def get_venom_feed():
    """Simple feed for VENOM"""
    symbol = request.args.get('symbol')
    
    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400
    
    if symbol not in VALID_SYMBOLS:
        return jsonify({'error': f'Invalid symbol. Use one of: {", ".join(VALID_SYMBOLS)}'}), 400
    
    data = market_data_store[symbol]
    
    if data['ticks'] and data['last_update']:
        current_time = time.time()
        if (current_time - data['last_update']) < STALE_DATA_THRESHOLD:
            latest_tick = data['ticks'][-1]
            
            response = {
                'symbol': symbol,
                'bid': latest_tick.get('bid', 0),
                'ask': latest_tick.get('ask', 0),
                'spread': abs(latest_tick.get('ask', 0) - latest_tick.get('bid', 0)),
                'volume': latest_tick.get('volume', 0),
                'time': latest_tick.get('time', current_time),
                'broker': latest_tick.get('broker', 'unknown'),
                'sources': len(data['sources']),
                'last_update': data['last_update']
            }
            
            return jsonify(response), 200
    
    return jsonify({'error': 'No recent data available'}), 404

@app.route('/market-data/all', methods=['GET'])
def get_all_market_data():
    """Get all current market data"""
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
    
    return jsonify({
        'data': all_data,
        'timestamp': datetime.now().isoformat(),
        'total_symbols': len(all_data)
    }), 200

if __name__ == '__main__':
    logger.info("Starting Simple Market Data Receiver on port 8001")
    logger.info(f"Valid symbols: {', '.join(VALID_SYMBOLS)}")
    logger.info("XAUUSD/GOLD is BLOCKED")
    logger.info("Simplified version - no threading issues")
    
    # Start Flask with single-threaded mode to avoid conflicts
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True, processes=1)