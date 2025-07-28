#!/usr/bin/env python3
"""
Unified Market Data Service - Clean Architecture
Provides real-time market data from MT5 to VENOM with proper data flow
NO FAKE DATA - 100% REAL MT5 DATA
"""

from flask import Flask, request, jsonify
import json
import time
from datetime import datetime
from collections import defaultdict, deque
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Market data storage - simple and clean
market_data = defaultdict(lambda: {
    'bid': 0.0,
    'ask': 0.0,
    'spread': 0.0,
    'volume': 0,
    'last_update': None,
    'source': None
})

# Thread safety
data_lock = threading.Lock()

# Valid pairs (NO XAUUSD)
VALID_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

@app.route('/market-data', methods=['POST'])
def receive_data():
    """Receive market data from MT5 EA"""
    try:
        # Debug: Log raw request details
        logger.info(f"Request from {request.remote_addr}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Content-Length: {request.content_length}")
        
        # Try to get raw data first
        raw_data = request.get_data(as_text=True)
        if raw_data:
            logger.info(f"Raw data preview: {raw_data[:200]}...")
            # Save full data for debugging
            with open('/tmp/ea_raw_data.json', 'w') as f:
                f.write(raw_data)
            logger.info(f"Full data saved to /tmp/ea_raw_data.json (length: {len(raw_data)})")
            
            # Check if data looks truncated or missing closing brace
            if len(raw_data) > 1400 and not raw_data.strip().endswith('}'):
                logger.warning(f"Data appears truncated at {len(raw_data)} bytes - attempting repair")
                
                # EA data typically ends with }] but missing the final closing brace
                if raw_data.endswith('}]'):
                    # Add the missing closing brace for the main JSON object
                    raw_data = raw_data + '}'
                    logger.info(f"Repaired EA data by adding missing closing brace")
                else:
                    # General case: find last complete JSON object
                    last_brace = raw_data.rfind('}')
                    if last_brace > 0:
                        raw_data = raw_data[:last_brace + 1]
                        logger.info(f"Truncated to last complete brace at position {last_brace}")
        
        # Try parsing JSON with force=True to ignore Content-Type
        try:
            data = json.loads(raw_data) if raw_data else None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Error at position {e.pos if hasattr(e, 'pos') else 'unknown'}")
            logger.error(f"Raw data around error: {raw_data[max(0, e.pos-50):e.pos+50] if hasattr(e, 'pos') and raw_data else 'N/A'}")
            return jsonify({'error': f'JSON parse error: {str(e)}'}), 400
            
        if not data:
            logger.error(f"Failed to parse JSON from: {raw_data[:100]}")
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract only market data - IGNORE user account info (balance, broker, server, etc.)
        # This is for signal filtering and CITADEL analysis only - NOT user account tracking
        ticks = data.get('ticks', [])
        processed = 0
        
        with data_lock:
            for tick in ticks:
                symbol = tick.get('symbol')
                if symbol in VALID_PAIRS:
                    # Store ONLY market data - no user account information
                    market_data[symbol] = {
                        'bid': float(tick.get('bid', 0)),
                        'ask': float(tick.get('ask', 0)),
                        'spread': float(tick.get('spread', 0)),
                        'volume': int(tick.get('volume', 0)),
                        'last_update': time.time(),
                        'source': 'market_feed'  # Generic source for signal analysis
                    }
                    processed += 1
        
        logger.info(f"Received {processed} ticks from {source}")
        return jsonify({'status': 'success', 'processed': processed})
        
    except Exception as e:
        import traceback
        logger.error(f"Error processing data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/get/<symbol>', methods=['GET'])
def get_symbol_data(symbol):
    """Get data for specific symbol - used by VENOM"""
    if symbol not in VALID_PAIRS:
        return jsonify({'error': 'Invalid symbol'}), 400
    
    with data_lock:
        data = market_data[symbol]
        
        # Check if data is fresh (within 30 seconds)
        if data['last_update'] and (time.time() - data['last_update']) < 30:
            return jsonify({
                'symbol': symbol,
                'bid': data['bid'],
                'ask': data['ask'],
                'spread': data['spread'],
                'volume': data['volume'],
                'timestamp': datetime.now().isoformat(),
                'is_real': True
            })
        else:
            return jsonify({'error': 'No recent data'}), 404

@app.route('/market-data/all', methods=['GET'])
def get_all_data():
    """Get all available market data"""
    result = {}
    current_time = time.time()
    
    with data_lock:
        for symbol in VALID_PAIRS:
            data = market_data[symbol]
            if data['last_update'] and (current_time - data['last_update']) < 30:
                result[symbol] = {
                    'bid': data['bid'],
                    'ask': data['ask'],
                    'spread': data['spread'],
                    'volume': data['volume']
                }
    
    return jsonify(result)

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Simple health check"""
    active_count = 0
    current_time = time.time()
    
    with data_lock:
        for symbol in VALID_PAIRS:
            if market_data[symbol]['last_update']:
                if (current_time - market_data[symbol]['last_update']) < 30:
                    active_count += 1
    
    return jsonify({
        'status': 'healthy',
        'active_symbols': active_count,
        'total_symbols': len(VALID_PAIRS),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("Starting Unified Market Service on port 8001")
    logger.info(f"Valid pairs: {', '.join(VALID_PAIRS)}")
    app.run(host='0.0.0.0', port=8001, debug=False)