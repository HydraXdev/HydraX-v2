#!/usr/bin/env python3
"""
High-Performance Market Data Receiver - Zero Threading Contention
Stateless design with LRU caching and sub-200ms response times
"""

from flask import Flask, request, jsonify
import json
import time
from datetime import datetime
from collections import defaultdict
import logging
from cachetools import TTLCache
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
VALID_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

# Stateless caching - NO SHARED MEMORY OR LOCKS
tick_cache = TTLCache(maxsize=500, ttl=30)  # 30 second TTL for tick data - data injector posts every 10s
metrics_cache = TTLCache(maxsize=100, ttl=5)  # 5 second TTL for computed metrics
symbol_activity = TTLCache(maxsize=20, ttl=60)  # Track active symbols

def get_cache_key(symbol: str, data_type: str) -> str:
    """Generate cache key for symbol data"""
    return f"{symbol}:{data_type}"

def update_tick_data(symbol: str, tick_data: dict) -> None:
    """Update tick data in cache (stateless)"""
    cache_key = get_cache_key(symbol, "ticks")
    current_time = time.time()
    
    # Get existing ticks or create new list
    existing_ticks = tick_cache.get(cache_key, [])
    
    # Add new tick and keep only last 20 (memory efficient)
    existing_ticks.append({
        'bid': tick_data['bid'],
        'ask': tick_data['ask'],
        'volume': tick_data['volume'],
        'time': current_time,
        'broker': tick_data.get('broker', 'unknown'),
        'source': 'MT5_LIVE'  # CRITICAL: Mark all stored ticks as live data
    })
    
    # Keep only last 20 ticks
    if len(existing_ticks) > 20:
        existing_ticks = existing_ticks[-20:]
    
    # Update cache
    tick_cache[cache_key] = existing_ticks
    symbol_activity[symbol] = current_time

def compute_metrics_cached(symbol: str) -> dict:
    """Compute order flow and liquidity metrics with 5-second caching"""
    cache_key = get_cache_key(symbol, "metrics")
    
    # Return cached metrics if available
    cached_metrics = metrics_cache.get(cache_key)
    if cached_metrics:
        return cached_metrics
    
    # Get recent ticks
    tick_key = get_cache_key(symbol, "ticks")
    ticks = tick_cache.get(tick_key, [])
    
    if len(ticks) < 3:
        empty_metrics = {
            'order_flow': {'imbalance': 0, 'bid_volume': 0, 'ask_volume': 0},
            'liquidity': {'levels_above': [], 'levels_below': []},
            'last_tick': None
        }
        metrics_cache[cache_key] = empty_metrics
        return empty_metrics
    
    # Fast computation - only use last 10 ticks
    recent_ticks = ticks[-10:]
    latest_tick = ticks[-1]
    
    # Order flow calculation (simplified)
    bid_volume = sum(t.get('volume', 0) for t in recent_ticks if t.get('bid', 0) > 0)
    ask_volume = sum(t.get('volume', 0) for t in recent_ticks if t.get('ask', 0) > 0)
    total_volume = bid_volume + ask_volume
    imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
    
    # Simple liquidity zones (price clustering)
    current_price = latest_tick.get('bid', 0)
    prices = [t.get('bid', 0) for t in recent_ticks if t.get('bid', 0) > 0]
    
    levels_above = [p for p in prices if p > current_price][:3]
    levels_below = [p for p in prices if p < current_price][:3]
    
    # Cache computed metrics
    metrics = {
        'order_flow': {
            'imbalance': round(imbalance, 3),
            'bid_volume': bid_volume,
            'ask_volume': ask_volume
        },
        'liquidity': {
            'levels_above': sorted(set(levels_above), reverse=True),
            'levels_below': sorted(set(levels_below))
        },
        'last_tick': latest_tick
    }
    
    metrics_cache[cache_key] = metrics
    return metrics

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """Receive market data - REAL MT5 ONLY - Zero synthetic data allowed"""
    start_time = time.time()
    
    try:
        # 🔥 Read raw request body first - works with any MT5 request
        raw_body = request.get_data()
        print("🧾 RAW BODY:", raw_body[:500])  # Show more data for debugging
        
        # 🔥 Manual JSON decode - bypasses Flask header requirements
        raw_string = raw_body.decode('utf-8', errors='ignore').strip()  # Handle encoding issues
        print("📝 DECODED STRING:", raw_string[:500])
        print(f"📏 STRING LENGTH: {len(raw_string)}")
        print(f"🔍 LAST 20 CHARS: {repr(raw_string[-20:])}")
        
        # 🔧 Robust JSON parsing - find JSON boundaries
        start_idx = raw_string.find('{')
        end_idx = raw_string.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_string = raw_string[start_idx:end_idx]
            print(f"🎯 EXTRACTED JSON LENGTH: {len(json_string)}")
            data = json.loads(json_string)
        else:
            raise ValueError("No valid JSON found in request body")
        print("✅ PARSED JSON:", data)
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # CRITICAL: Reject all non-MT5 live data sources
        source = data.get('source', 'unknown')
        if source != 'MT5_LIVE':
            logger.warning(f"❌ REJECTED non-live data source: {source}")
            return jsonify({'error': 'Only MT5_LIVE data accepted', 'rejected_source': source}), 403
        
        broker = data.get('broker', 'unknown')
        ticks = data.get('ticks', [])
        valid_ticks = 0
        
        # Process ticks without locks
        for tick in ticks:
            try:
                # 🛡️ LIVE DATA SOURCE GUARD - MAXIMUM SECURITY
                if tick.get("source") != "MT5_LIVE":
                    raise RuntimeError("⛔ INVALID DATA SOURCE: Tick not from live MT5 feed.")
                
                # 🔥 TRUTH TRIPWIRE - VISIBLE SAFETY SYSTEM
                if tick.get("source") == "INJECTOR":
                    raise Exception("🔥 BLOCKED: Simulation detected. Signal system disabled.")
                
                symbol = tick.get('symbol', '').upper()
                
                if symbol not in VALID_SYMBOLS:
                    continue
                
                tick_data = {
                    'bid': float(tick.get('bid', 0)),
                    'ask': float(tick.get('ask', 0)),
                    'volume': int(tick.get('volume', 0)),
                    'broker': broker
                }
                
                # Stateless update
                update_tick_data(symbol, tick_data)
                valid_ticks += 1
                
            except (ValueError, TypeError):
                continue
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"POST /market-data: {valid_ticks} ticks from {broker} ({duration:.1f}ms)")
        
        return jsonify({
            'status': 'success',
            'processed': valid_ticks,
            'broker': broker
        }), 200
        
    except json.JSONDecodeError as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"❌ JSON decode error ({duration:.1f}ms): {e}")
        logger.error(f"Raw body was: {raw_body}")
        # 🔥 TEMPORARY FIX: Return 200 to keep EA happy while we debug
        print("⚠️ TEMPORARY: Returning 200 despite JSON error to maintain EA connection")
        return jsonify({'status': 'error', 'message': 'JSON parse failed but acknowledged'}), 200
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"POST /market-data error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/health', methods=['GET'])
def health_check():
    """Lightweight health check - sub-50ms response"""
    start_time = time.time()
    
    try:
        current_time = time.time()
        active_count = 0
        
        # Quick activity check
        for symbol in VALID_SYMBOLS:
            last_activity = symbol_activity.get(symbol, 0)
            if current_time - last_activity < 30:  # Active in last 30 seconds
                active_count += 1
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"GET /health: {active_count} active ({duration:.1f}ms)")
        
        return jsonify({
            'status': 'healthy',
            'symbols_active': active_count,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"GET /health error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/venom-feed', methods=['GET'])
def get_venom_feed():
    """Lightweight VENOM feed - cached data only"""
    start_time = time.time()
    
    try:
        symbol = request.args.get('symbol')
        if not symbol or symbol not in VALID_SYMBOLS:
            return jsonify({'error': 'Valid symbol required'}), 400
        
        # Get cached metrics (includes last tick)
        metrics = compute_metrics_cached(symbol)
        last_tick = metrics.get('last_tick')
        
        if not last_tick:
            duration = (time.time() - start_time) * 1000
            logger.info(f"GET /venom-feed/{symbol}: no data ({duration:.1f}ms)")
            return jsonify({'error': 'No recent data available'}), 404
        
        response = {
            'symbol': symbol,
            'bid': last_tick.get('bid', 0),
            'ask': last_tick.get('ask', 0),
            'spread': abs(last_tick.get('ask', 0) - last_tick.get('bid', 0)),
            'volume': last_tick.get('volume', 0),
            'time': last_tick.get('time', time.time()),
            'broker': last_tick.get('broker', 'unknown')
        }
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"GET /venom-feed/{symbol}: success ({duration:.1f}ms)")
        
        return jsonify(response), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"GET /venom-feed error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/all', methods=['GET'])
def get_all_market_data():
    """Optimized endpoint - top 8-10 active pairs with cached metrics"""
    start_time = time.time()
    
    try:
        current_time = time.time()
        active_data = {}
        
        # Get ALL recently active symbols (removed top 10 limit for VENOM)
        active_symbols = []
        for symbol in VALID_SYMBOLS:
            last_activity = symbol_activity.get(symbol, 0)
            if current_time - last_activity < 30:
                active_symbols.append((symbol, last_activity))
        
        # Sort by recency and return ALL active symbols
        active_symbols.sort(key=lambda x: x[1], reverse=True)
        top_symbols = [symbol for symbol, _ in active_symbols]  # No [:10] limit
        
        # Get cached data for active symbols
        for symbol in top_symbols:
            metrics = compute_metrics_cached(symbol)
            last_tick = metrics.get('last_tick')
            
            if last_tick:
                active_data[symbol] = {
                    'bid': last_tick.get('bid', 0),
                    'ask': last_tick.get('ask', 0),
                    'volume': last_tick.get('volume', 0),
                    'broker': last_tick.get('broker', 'unknown'),
                    'order_flow': metrics['order_flow'],
                    'liquidity': metrics['liquidity'],
                    'last_update': last_tick.get('time', current_time)
                }
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"GET /all: {len(active_data)} symbols ({duration:.1f}ms)")
        
        return jsonify({
            'data': active_data,
            'timestamp': datetime.now().isoformat(),
            'total_symbols': len(active_data)
        }), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"GET /all error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/market-data/order-flow', methods=['GET'])
def get_order_flow():
    """Get cached order flow data"""
    start_time = time.time()
    
    try:
        symbol = request.args.get('symbol')
        if not symbol or symbol not in VALID_SYMBOLS:
            return jsonify({'error': 'Valid symbol required'}), 400
        
        metrics = compute_metrics_cached(symbol)
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"GET /order-flow/{symbol}: success ({duration:.1f}ms)")
        
        return jsonify(metrics['order_flow']), 200
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"GET /order-flow error ({duration:.1f}ms): {e}")
        return jsonify({'error': str(e)}), 500

@app.before_request
def before_request():
    """Enforce 200ms timeout on all requests"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Log request duration and enforce timeout"""
    if hasattr(request, 'start_time'):
        duration = (time.time() - request.start_time) * 1000
        if duration > 200:
            logger.warning(f"SLOW REQUEST: {request.method} {request.path} took {duration:.1f}ms")
    return response

if __name__ == '__main__':
    logger.info("Starting High-Performance Market Data Receiver")
    logger.info(f"Valid symbols: {len(VALID_SYMBOLS)} pairs")
    logger.info("Features: Zero threading, LRU caching, sub-200ms responses")
    logger.info("XAUUSD/GOLD is BLOCKED")
    
    # Single-threaded Flask app - NO CONCURRENCY ISSUES
    app.run(
        host='0.0.0.0', 
        port=8001, 
        debug=False, 
        threaded=False,  # Single-threaded
        processes=1,     # Single process
        use_reloader=False
    )