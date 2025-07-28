#!/usr/bin/env python3
"""
Market Data Receiver - HTTP endpoint for EA market data streaming
Receives tick data from all MT5 EAs and provides it to VENOM engine
NO SYNTHETIC DATA - only real tick data from MT5
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

# Market data storage (in-memory for now, could be Redis later)
market_data_store = defaultdict(lambda: {
    'ticks': deque(maxlen=100),  # Keep last 100 ticks per symbol
    'last_update': None,
    'sources': set()  # Track unique data sources
})

# Lock for thread safety
data_lock = threading.Lock()

# Configuration
STALE_DATA_THRESHOLD = 30  # seconds before data is considered stale
REQUIRED_SOURCES_MIN = 1   # Minimum sources before data is valid

# 15 currency pairs (NO XAUUSD)
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """Receive market data from MT5 EA"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract metadata
        uuid = data.get('uuid', 'unknown')
        timestamp = data.get('timestamp', int(time.time()))
        ticks = data.get('ticks', [])
        
        # Validate and store tick data
        with data_lock:
            valid_ticks = 0
            
            for tick in ticks:
                symbol = tick.get('symbol')
                
                # Skip invalid symbols
                if symbol not in VALID_SYMBOLS:
                    logger.warning(f"Rejected invalid symbol: {symbol}")
                    continue
                
                # Block XAUUSD explicitly
                if symbol == "XAUUSD" or "XAU" in symbol:
                    logger.error(f"BLOCKED: Attempted to send XAUUSD data from {uuid}")
                    continue
                
                # Store tick data
                tick_data = {
                    'uuid': uuid,
                    'symbol': symbol,
                    'bid': float(tick.get('bid', 0)),
                    'ask': float(tick.get('ask', 0)),
                    'spread': float(tick.get('spread', 0)),
                    'volume': int(tick.get('volume', 0)),
                    'time': tick.get('time', timestamp),
                    'received_at': datetime.now().isoformat()
                }
                
                market_data_store[symbol]['ticks'].append(tick_data)
                market_data_store[symbol]['last_update'] = datetime.now()
                market_data_store[symbol]['sources'].add(uuid)
                
                valid_ticks += 1
            
            logger.info(f"Received {valid_ticks} valid ticks from {uuid}")
        
        return jsonify({
            'status': 'success',
            'processed': valid_ticks,
            'uuid': uuid
        })
        
    except Exception as e:
        logger.error(f"Error processing market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/<symbol>', methods=['GET'])
def get_symbol_data(symbol):
    """Get latest market data for a specific symbol"""
    
    # Validate symbol
    if symbol not in VALID_SYMBOLS:
        return jsonify({'error': f'Invalid symbol: {symbol}'}), 400
    
    with data_lock:
        if symbol not in market_data_store:
            return jsonify({'error': f'No data for symbol: {symbol}'}), 404
        
        data = market_data_store[symbol]
        
        # Check if data is stale
        if data['last_update']:
            age = (datetime.now() - data['last_update']).total_seconds()
            is_stale = age > STALE_DATA_THRESHOLD
        else:
            is_stale = True
        
        # Get latest tick
        latest_tick = None
        if data['ticks']:
            latest_tick = data['ticks'][-1]
        
        # Calculate aggregated values from recent ticks
        recent_ticks = list(data['ticks'])[-10:]  # Last 10 ticks
        
        if recent_ticks:
            avg_bid = sum(t['bid'] for t in recent_ticks) / len(recent_ticks)
            avg_ask = sum(t['ask'] for t in recent_ticks) / len(recent_ticks)
            avg_spread = sum(t['spread'] for t in recent_ticks) / len(recent_ticks)
        else:
            avg_bid = avg_ask = avg_spread = 0
        
        return jsonify({
            'symbol': symbol,
            'latest_tick': latest_tick,
            'average_bid': round(avg_bid, 5),
            'average_ask': round(avg_ask, 5),
            'average_spread': round(avg_spread, 1),
            'tick_count': len(data['ticks']),
            'source_count': len(data['sources']),
            'is_stale': is_stale,
            'last_update': data['last_update'].isoformat() if data['last_update'] else None
        })

@app.route('/market-data/all', methods=['GET'])
def get_all_data():
    """Get latest market data for all symbols"""
    
    with data_lock:
        result = {}
        
        for symbol in VALID_SYMBOLS:
            if symbol in market_data_store and market_data_store[symbol]['ticks']:
                data = market_data_store[symbol]
                latest_tick = data['ticks'][-1]
                
                # Check staleness
                age = (datetime.now() - data['last_update']).total_seconds() if data['last_update'] else 999
                
                result[symbol] = {
                    'bid': latest_tick['bid'],
                    'ask': latest_tick['ask'],
                    'spread': latest_tick['spread'],
                    'volume': latest_tick['volume'],
                    'last_update': data['last_update'].isoformat() if data['last_update'] else None,
                    'is_stale': age > STALE_DATA_THRESHOLD,
                    'source_count': len(data['sources'])
                }
        
        return jsonify({
            'symbols': result,
            'timestamp': datetime.now().isoformat(),
            'active_symbols': len(result),
            'total_symbols': len(VALID_SYMBOLS)
        })

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    
    with data_lock:
        active_symbols = 0
        stale_symbols = 0
        total_sources = set()
        
        for symbol, data in market_data_store.items():
            if data['last_update']:
                age = (datetime.now() - data['last_update']).total_seconds()
                if age <= STALE_DATA_THRESHOLD:
                    active_symbols += 1
                else:
                    stale_symbols += 1
                
                total_sources.update(data['sources'])
        
        return jsonify({
            'status': 'healthy' if active_symbols > 0 else 'no_data',
            'active_symbols': active_symbols,
            'stale_symbols': stale_symbols,
            'total_sources': len(total_sources),
            'valid_symbols': VALID_SYMBOLS,
            'timestamp': datetime.now().isoformat()
        })

@app.route('/market-data/venom-feed', methods=['GET'])
def get_venom_feed():
    """
    Special endpoint for VENOM engine to get real-time data
    Returns data in format expected by VENOM's get_real_mt5_data()
    """
    symbol = request.args.get('symbol', 'EURUSD')
    
    # Validate symbol
    if symbol not in VALID_SYMBOLS:
        return jsonify({'error': f'Invalid symbol: {symbol}'}), 400
    
    with data_lock:
        if symbol in market_data_store and market_data_store[symbol]['ticks']:
            data = market_data_store[symbol]
            latest_tick = data['ticks'][-1]
            
            # Check if data is fresh
            age = (datetime.now() - data['last_update']).total_seconds() if data['last_update'] else 999
            
            if age > STALE_DATA_THRESHOLD:
                # Data too old, return empty (VENOM will handle)
                return jsonify({})
            
            # Return in VENOM's expected format
            return jsonify({
                'close': latest_tick['bid'],  # Use bid as close price
                'spread': latest_tick['spread'],
                'volume': latest_tick['volume'],
                'timestamp': datetime.now().isoformat(),
                'source_count': len(data['sources']),
                'is_real': True  # Confirm this is real data
            })
        else:
            # No data available
            return jsonify({})

def cleanup_stale_data():
    """Background task to clean up stale data"""
    while True:
        try:
            with data_lock:
                for symbol in list(market_data_store.keys()):
                    data = market_data_store[symbol]
                    if data['last_update']:
                        age = (datetime.now() - data['last_update']).total_seconds()
                        # Remove very old data (>5 minutes)
                        if age > 300:
                            del market_data_store[symbol]
                            logger.info(f"Cleaned up stale data for {symbol}")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        
        time.sleep(60)  # Run every minute

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_stale_data, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    logger.info("Starting Market Data Receiver on port 8001")
    logger.info(f"Valid symbols: {', '.join(VALID_SYMBOLS)}")
    logger.info("XAUUSD/GOLD is BLOCKED")
    
    # Run on all interfaces for Docker compatibility
    app.run(host='0.0.0.0', port=8001, debug=False)