#!/usr/bin/env python3
"""
Streaming Market Data Receiver with Smart Buffer
Handles truncated JSON from EA while maintaining real-time continuous flow
"""

import json
import time
import logging
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Thread-safe data storage
data_lock = Lock()
market_data = {}
last_update_times = {}
partial_buffers = defaultdict(str)  # Buffer for incomplete JSON per source

# Valid symbols (INCLUDING XAUUSD)
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY",
    "XAUUSD"
]

def extract_complete_json(data_str):
    """
    Extract complete JSON objects from a potentially truncated string
    Returns (complete_json, remaining_partial)
    """
    # Find all complete tick objects
    tick_pattern = r'\{"symbol":"[^"]+","bid":\d+\.\d+,"ask":\d+\.\d+,"spread":\d+\.\d+,"volume":\d+,"time":\d+,"source":"[^"]+"\}'
    
    # Try to parse as complete JSON first
    try:
        parsed = json.loads(data_str)
        return parsed, ""
    except json.JSONDecodeError:
        pass
    
    # If that fails, try to extract what we can
    try:
        # Find the last complete tick object
        last_complete = data_str.rfind(',"source":"MT5_LIVE"}')
        if last_complete > 0:
            # Include the closing bracket and trim
            cutoff = last_complete + len(',"source":"MT5_LIVE"}')
            clean_json = data_str[:cutoff] + ']}'
            
            # Verify it's valid JSON
            parsed = json.loads(clean_json)
            remaining = data_str[cutoff:]
            return parsed, remaining
    except:
        pass
    
    return None, data_str

def process_streaming_data(source_id, raw_data):
    """
    Process incoming data with smart buffering for truncated JSON
    """
    global partial_buffers
    
    # Combine with any partial buffer from previous request
    full_data = partial_buffers[source_id] + raw_data
    
    # Try to extract complete JSON
    parsed_data, remaining = extract_complete_json(full_data)
    
    if parsed_data:
        # Successfully parsed data
        partial_buffers[source_id] = remaining  # Save any partial for next time
        
        # Process the ticks
        process_ticks(parsed_data)
        
        # Log success
        tick_count = len(parsed_data.get('ticks', []))
        logger.info(f"✅ Processed {tick_count} ticks from {source_id}")
        
        return True
    else:
        # Still incomplete, buffer it
        partial_buffers[source_id] = full_data
        
        # But don't let buffer grow too large (safety valve)
        if len(partial_buffers[source_id]) > 10000:
            logger.warning(f"Buffer overflow for {source_id}, resetting")
            partial_buffers[source_id] = ""
        
        return False

def process_ticks(data):
    """
    Process tick data and update market data store
    """
    with data_lock:
        current_time = time.time()
        
        for tick in data.get('ticks', []):
            symbol = tick.get('symbol', '')
            
            # Include XAUUSD/GOLD - no longer skip
                
            if symbol in VALID_SYMBOLS:
                # Update market data with streaming tick
                market_data[symbol] = {
                    'bid': tick.get('bid', 0),
                    'ask': tick.get('ask', 0),
                    'spread': tick.get('spread', 0),
                    'volume': tick.get('volume', 0),
                    'timestamp': current_time,
                    'source': tick.get('source', 'MT5_LIVE'),
                    'broker': data.get('broker', 'Unknown'),
                    'account_balance': data.get('account_balance', 0)
                }
                last_update_times[symbol] = current_time

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """
    Streaming endpoint that handles truncated JSON gracefully
    """
    try:
        # Get raw data
        raw_data = request.data.decode('utf-8', errors='ignore')
        
        # Extract source ID from partial data if possible
        source_match = re.search(r'"uuid":"([^"]+)"', raw_data)
        source_id = source_match.group(1) if source_match else 'unknown'
        
        # Process with streaming buffer
        success = process_streaming_data(source_id, raw_data)
        
        # Always return 200 to keep EA connection alive
        return jsonify({
            'status': 'received',
            'processed': success,
            'buffer_size': len(partial_buffers[source_id])
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 200

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    with data_lock:
        current_time = time.time()
        active_symbols = sum(1 for t in last_update_times.values() 
                           if current_time - t < 30)
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_symbols': active_symbols,
        'streaming': True
    })

@app.route('/market-data/all', methods=['GET'])
def get_all_data():
    """Get all current market data"""
    with data_lock:
        current_time = time.time()
        
        # Filter to only recent data (last 30 seconds)
        active_data = {
            symbol: data for symbol, data in market_data.items()
            if current_time - data['timestamp'] < 30
        }
        
        # Add volatility info for VENOM
        for symbol, data in active_data.items():
            data['volatility'] = calculate_volatility(symbol)
    
    return jsonify({
        'status': 'success',
        'data': active_data,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/market-data/venom-feed', methods=['GET'])
def get_venom_feed():
    """Optimized feed for VENOM consumption"""
    symbol = request.args.get('symbol', 'EURUSD')
    
    with data_lock:
        if symbol in market_data:
            data = market_data[symbol].copy()
            data['volatility'] = calculate_volatility(symbol)
            return jsonify(data)
    
    return jsonify({'error': 'No data available'}), 404

def calculate_volatility(symbol):
    """Simple volatility calculation for VENOM"""
    # This would ideally track price changes over time
    # For now, return a reasonable default
    return 0.0001 if symbol in ['EURUSD', 'GBPUSD'] else 0.0002

if __name__ == '__main__':
    logger.info("🚀 Starting Streaming Market Data Receiver")
    logger.info("✨ Features: Smart buffering, truncation handling, continuous flow")
    logger.info("🔄 No batching - pure streaming architecture")
    
    # Run with single process to avoid threading issues
    app.run(
        host='0.0.0.0',
        port=8001,
        debug=False,
        threaded=False,
        processes=1
    )