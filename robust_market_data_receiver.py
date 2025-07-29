#!/usr/bin/env python3
"""
ROBUST MARKET DATA RECEIVER
Handles EA data transmission issues without requiring EA changes
- JSON truncation/chunking
- Partial payloads  
- Buffer reconstruction
- Multiple EA formats
- Future-proof for 1500+ EAs
"""

from flask import Flask, request, jsonify
import json
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enhanced market data storage with buffer management
market_data_store = defaultdict(lambda: {
    'ticks': deque(maxlen=200),  # Increased buffer
    'last_update': None,
    'source_uuid': None,
    'broker': 'Unknown',
    'balance': 0.0,
    'server': 'Unknown'
})

# Buffer management for incomplete JSON
json_buffers = defaultdict(lambda: {
    'buffer': '',
    'last_update': time.time(),
    'attempts': 0
})

# Data lock for thread safety
data_lock = threading.Lock()

# Valid symbols (15 pairs, NO XAUUSD)
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

STALE_DATA_THRESHOLD = 120  # 2 minutes

def clean_json_buffer(raw_data):
    """Clean and attempt to repair JSON data"""
    try:
        # Convert bytes to string
        if isinstance(raw_data, bytes):
            text_data = raw_data.decode('utf-8', errors='ignore')
        else:
            text_data = str(raw_data)
        
        # Remove any null bytes or control characters
        text_data = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text_data)
        
        # Try to fix common JSON truncation issues
        if text_data.endswith('"'):
            text_data += '}'
        elif text_data.endswith(','):
            text_data = text_data[:-1] + ']}'
        elif not text_data.endswith('}') and not text_data.endswith(']'):
            # Try to close the JSON structure
            if '"ticks":[' in text_data and not text_data.endswith(']}'):
                text_data += ']}'
            elif text_data.endswith(','):
                text_data = text_data[:-1] + '}'
            else:
                text_data += '}'
        
        return text_data
        
    except Exception as e:
        logger.error(f"Error cleaning JSON buffer: {e}")
        return str(raw_data) if raw_data else ""

def try_parse_json(text_data):
    """Attempt multiple JSON parsing strategies"""
    
    # Strategy 1: Direct parse
    try:
        return json.loads(text_data)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Clean and parse
    try:
        cleaned = clean_json_buffer(text_data)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Extract what we can with regex
    try:
        # Extract basic fields
        uuid_match = re.search(r'"uuid":"([^"]*)"', text_data)
        balance_match = re.search(r'"account_balance":([0-9.]+)', text_data)
        broker_match = re.search(r'"broker":"([^"]*)"', text_data)
        server_match = re.search(r'"server":"([^"]*)"', text_data)
        
        # Extract tick data
        tick_pattern = r'"symbol":"([^"]*)"[^}]*"bid":([0-9.]+)[^}]*"ask":([0-9.]+)[^}]*"spread":([0-9.]+)[^}]*"volume":([0-9]+)[^}]*"time":([0-9]+)'
        ticks = []
        
        for match in re.finditer(tick_pattern, text_data):
            symbol, bid, ask, spread, volume, tick_time = match.groups()
            if symbol in VALID_SYMBOLS:
                ticks.append({
                    'symbol': symbol,
                    'bid': float(bid),
                    'ask': float(ask),
                    'spread': float(spread),
                    'volume': int(volume),
                    'time': int(tick_time)
                })
        
        if ticks:  # Only return if we found some tick data
            return {
                'uuid': uuid_match.group(1) if uuid_match else 'unknown',
                'account_balance': float(balance_match.group(1)) if balance_match else 0.0,
                'broker': broker_match.group(1) if broker_match else 'Unknown',
                'server': server_match.group(1) if server_match else 'Unknown',
                'timestamp': int(time.time()),
                'ticks': ticks
            }
    
    except Exception as e:
        logger.debug(f"Regex parsing failed: {e}")
    
    return None

def buffer_and_reconstruct(source_ip, raw_data):
    """Buffer incomplete JSON and attempt reconstruction"""
    
    current_time = time.time()
    buffer_info = json_buffers[source_ip]
    
    # Clean old buffers (older than 30 seconds)
    if current_time - buffer_info['last_update'] > 30:
        buffer_info['buffer'] = ''
        buffer_info['attempts'] = 0
    
    # Add new data to buffer
    if isinstance(raw_data, bytes):
        new_data = raw_data.decode('utf-8', errors='ignore')
    else:
        new_data = str(raw_data)
    
    buffer_info['buffer'] += new_data
    buffer_info['last_update'] = current_time
    buffer_info['attempts'] += 1
    
    # Try to parse the accumulated buffer
    parsed_data = try_parse_json(buffer_info['buffer'])
    
    if parsed_data:
        # Success! Clear the buffer
        buffer_info['buffer'] = ''
        buffer_info['attempts'] = 0
        return parsed_data
    
    # If we've tried too many times, try partial parsing
    if buffer_info['attempts'] >= 3:
        logger.warning(f"Multiple parsing attempts failed for {source_ip}, trying partial extraction")
        partial_data = try_parse_json(buffer_info['buffer'])
        
        # Reset buffer either way
        buffer_info['buffer'] = ''
        buffer_info['attempts'] = 0
        
        return partial_data
    
    # Still building buffer
    logger.debug(f"Buffering data from {source_ip}, attempt {buffer_info['attempts']}")
    return None

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """ROBUST receiver with advanced JSON handling"""
    
    source_ip = request.remote_addr
    
    try:
        # Get raw data
        raw_data = request.get_data()
        
        if not raw_data:
            return jsonify({'error': 'No data provided'}), 400
        
        logger.debug(f"Received {len(raw_data)} bytes from {source_ip}")
        
        # First try: Direct JSON parsing
        try:
            data = request.get_json()
            if data:
                logger.debug(f"Direct JSON parse successful from {source_ip}")
        except:
            data = None
        
        # Second try: Buffer and reconstruct
        if not data:
            data = buffer_and_reconstruct(source_ip, raw_data)
        
        # Third try: Manual parsing of raw data
        if not data:
            data = try_parse_json(raw_data)
        
        if not data:
            logger.error(f"All parsing methods failed for {source_ip}")
            return jsonify({'error': 'Could not parse data'}), 400
        
        # Extract data fields
        uuid = data.get('uuid', f'ea_{source_ip}')
        ticks = data.get('ticks', [])
        broker = data.get('broker', 'Unknown')
        balance = data.get('account_balance', 0.0)
        server = data.get('server', 'Unknown')
        
        if not ticks:
            logger.warning(f"No tick data found from {source_ip}")
            return jsonify({'error': 'No tick data'}), 400
        
        # Process ticks
        valid_ticks = 0
        current_time = time.time()
        
        with data_lock:
            for tick in ticks:
                symbol = tick.get('symbol')
                
                # Validate symbol
                if not symbol or symbol not in VALID_SYMBOLS:
                    continue
                
                # Enhanced tick data
                enhanced_tick = {
                    'symbol': symbol,
                    'bid': float(tick.get('bid', 0)),
                    'ask': float(tick.get('ask', 0)),
                    'spread': float(tick.get('spread', 0)),
                    'volume': int(tick.get('volume', 0)),
                    'time': int(tick.get('time', current_time)),
                    'uuid': uuid,
                    'broker': broker,
                    'balance': balance,
                    'server': server,
                    'received_at': current_time
                }
                
                # Store in market data
                symbol_data = market_data_store[symbol]
                symbol_data['ticks'].append(enhanced_tick)
                symbol_data['last_update'] = current_time
                symbol_data['source_uuid'] = uuid
                symbol_data['broker'] = broker
                symbol_data['balance'] = balance
                symbol_data['server'] = server
                
                valid_ticks += 1
        
        logger.info(f"✅ Processed {valid_ticks}/{len(ticks)} ticks from {uuid} ({source_ip})")
        
        return jsonify({
            'status': 'success',
            'processed_ticks': valid_ticks,
            'uuid': uuid,
            'timestamp': current_time
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing market data from {source_ip}: {e}")
        return jsonify({'error': 'Internal processing error'}), 500

@app.route('/market-data/all', methods=['GET'])
def get_all_market_data():
    """Get all current market data - VENOM engine endpoint"""
    
    current_time = time.time()
    all_data = {}
    
    with data_lock:
        for symbol in VALID_SYMBOLS:
            symbol_data = market_data_store[symbol]
            
            # Skip stale data
            if not symbol_data['last_update'] or \
               (current_time - symbol_data['last_update']) > STALE_DATA_THRESHOLD:
                continue
            
            # Get latest tick
            if symbol_data['ticks']:
                latest_tick = symbol_data['ticks'][-1]
                all_data[symbol] = {
                    'bid': latest_tick['bid'],
                    'ask': latest_tick['ask'], 
                    'spread': latest_tick['spread'],
                    'volume': latest_tick['volume'],
                    'time': latest_tick['time'],
                    'uuid': latest_tick['uuid'],
                    'broker': latest_tick['broker'],
                    'last_update': symbol_data['last_update']
                }
    
    return jsonify(all_data), 200

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Enhanced health check"""
    active_symbols = 0
    total_sources = set()
    buffer_status = {}
    
    current_time = time.time()
    
    with data_lock:
        for symbol in VALID_SYMBOLS:
            symbol_data = market_data_store[symbol]
            if symbol_data['last_update'] and \
               (current_time - symbol_data['last_update']) < STALE_DATA_THRESHOLD:
                active_symbols += 1
                if symbol_data['source_uuid']:
                    total_sources.add(symbol_data['source_uuid'])
    
    # Buffer status
    for ip, buffer_info in json_buffers.items():
        if current_time - buffer_info['last_update'] < 60:  # Active buffers
            buffer_status[ip] = {
                'buffer_size': len(buffer_info['buffer']),
                'attempts': buffer_info['attempts'],
                'last_update': buffer_info['last_update']
            }
    
    return jsonify({
        'status': 'healthy',
        'active_symbols': active_symbols,
        'total_sources': len(total_sources),
        'active_buffers': len(buffer_status),
        'buffer_details': buffer_status,
        'timestamp': datetime.now().isoformat(),
        'service': 'robust_market_data_receiver'
    }), 200

@app.route('/venom-feed', methods=['GET'])
def venom_feed():
    """Legacy VENOM feed endpoint"""
    return get_all_market_data()

# Cleanup old buffers periodically
def cleanup_buffers():
    """Clean old buffers every 60 seconds"""
    while True:
        try:
            current_time = time.time()
            expired_ips = []
            
            for ip, buffer_info in json_buffers.items():
                if current_time - buffer_info['last_update'] > 300:  # 5 minutes
                    expired_ips.append(ip)
            
            for ip in expired_ips:
                del json_buffers[ip]
                logger.debug(f"Cleaned expired buffer for {ip}")
            
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in buffer cleanup: {e}")
            time.sleep(60)

if __name__ == '__main__':
    logger.info("🚀 ROBUST MARKET DATA RECEIVER")
    logger.info("✅ Advanced JSON parsing and buffer reconstruction")
    logger.info("🛠️ Future-proof for 1500+ EAs")
    logger.info("📡 Starting on port 8001...")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_buffers, daemon=True)
    cleanup_thread.start()
    
    # Configure Flask for larger payloads
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
    
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)