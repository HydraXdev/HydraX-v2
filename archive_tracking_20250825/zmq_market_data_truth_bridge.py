#!/usr/bin/env python3
"""
ZMQ Market Data Bridge for Truth Tracker
Consumes ZMQ market data and updates Black Box truth system directly
This fixes the broken market data pipeline for signal completion tracking
"""

import zmq
import json
import time
import logging
import threading
import requests
from datetime import datetime
from typing import Dict, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ZMQMarketDataTruthBridge')

class ZMQMarketDataTruthBridge:
    def __init__(self):
        self.context = zmq.Context()
        self.running = True
        self.market_cache = {}
        self.last_update = {}
        
        # Connect to truth tracker directly
        try:
            from black_box_complete_truth_system import get_truth_system
            self.truth_system = get_truth_system()
            logger.info("✅ Connected to Black Box Truth System")
        except ImportError:
            self.truth_system = None
            logger.error("❌ Could not import Black Box Truth System")
            
    def zmq_market_listener(self):
        """Listen for market data from ZMQ port 5560"""
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect("tcp://127.0.0.1:5560")
        subscriber.subscribe(b'')
        
        logger.info("📡 Connected to ZMQ market data on port 5560")
        
        while self.running:
            try:
                subscriber.setsockopt(zmq.RCVTIMEO, 1000)
                message = subscriber.recv_string()
                
                # Parse market data
                try:
                    data = json.loads(message)
                    self.process_market_tick(data)
                except json.JSONDecodeError:
                    # Skip non-JSON messages
                    continue
                    
            except zmq.error.Again:
                # Timeout, continue
                continue
            except Exception as e:
                logger.error(f"Error processing ZMQ market data: {e}")
                
        subscriber.close()
        
    def process_market_tick(self, data):
        """Process incoming market tick and update cache"""
        try:
            # Handle different data formats
            symbol = None
            bid = ask = None
            
            # Format 1: Direct tick data
            if 'symbol' in data and 'bid' in data:
                symbol = data['symbol']
                bid = float(data['bid'])
                ask = float(data['ask'])
            
            # Format 2: Nested ticks
            elif 'ticks' in data and isinstance(data['ticks'], list):
                for tick in data['ticks']:
                    if 'symbol' in tick and 'bid' in tick:
                        symbol = tick['symbol']
                        bid = float(tick['bid'])
                        ask = float(tick['ask'])
                        break
            
            # Format 3: Symbol-keyed data
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict) and 'bid' in value:
                        symbol = key
                        bid = float(value['bid'])
                        ask = float(value['ask'])
                        break
            
            if symbol and bid and ask:
                # Update cache
                self.market_cache[symbol] = {
                    'bid': bid,
                    'ask': ask,
                    'timestamp': time.time()
                }
                self.last_update[symbol] = time.time()
                
                # Update truth system directly if available
                if self.truth_system:
                    self.update_truth_system_prices()
                    
                logger.debug(f"📊 Updated {symbol}: bid={bid}, ask={ask}")
                
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
            
    def update_truth_system_prices(self):
        """Update truth system with current market prices"""
        if not self.truth_system:
            return
            
        try:
            # Get active signals from truth system
            active_signals = self.truth_system.active_signals.copy()
            
            for signal_id, signal in active_signals.items():
                symbol = signal.symbol
                
                if symbol in self.market_cache:
                    market_data = self.market_cache[symbol]
                    current_price = market_data['ask'] if signal.direction == 'BUY' else market_data['bid']
                    
                    # Update signal prices directly
                    with self.truth_system.lock:
                        if signal_id in self.truth_system.active_signals:
                            signal = self.truth_system.active_signals[signal_id]
                            signal.current_price = current_price
                            
                            # Update max favorable/adverse
                            if signal.direction == 'BUY':
                                if current_price > signal.max_favorable_price:
                                    signal.max_favorable_price = current_price
                                    signal.time_to_max_favorable = int(time.time() - signal.generated_at.timestamp() if hasattr(signal.generated_at, 'timestamp') else 0)
                                if current_price < signal.max_adverse_price or signal.max_adverse_price == 0:
                                    signal.max_adverse_price = current_price
                                    signal.time_to_max_adverse = int(time.time() - signal.generated_at.timestamp() if hasattr(signal.generated_at, 'timestamp') else 0)
                            else:  # SELL
                                if current_price < signal.max_favorable_price or signal.max_favorable_price == 0:
                                    signal.max_favorable_price = current_price
                                    signal.time_to_max_favorable = int(time.time() - signal.generated_at.timestamp() if hasattr(signal.generated_at, 'timestamp') else 0)
                                if current_price > signal.max_adverse_price:
                                    signal.max_adverse_price = current_price
                                    signal.time_to_max_adverse = int(time.time() - signal.generated_at.timestamp() if hasattr(signal.generated_at, 'timestamp') else 0)
                            
                            # Check for SL/TP hits
                            self.check_signal_completion(signal, current_price)
                            
        except Exception as e:
            logger.error(f"Error updating truth system: {e}")
            
    def check_signal_completion(self, signal, current_price):
        """Check if signal hit SL or TP"""
        try:
            if signal.completed:
                return
                
            hit_tp = False
            hit_sl = False
            
            if signal.direction == 'BUY':
                if signal.take_profit > 0 and current_price >= signal.take_profit:
                    hit_tp = True
                if signal.stop_loss > 0 and current_price <= signal.stop_loss:
                    hit_sl = True
            else:  # SELL
                if signal.take_profit > 0 and current_price <= signal.take_profit:
                    hit_tp = True
                if signal.stop_loss > 0 and current_price >= signal.stop_loss:
                    hit_sl = True
            
            if hit_tp or hit_sl:
                outcome = "WIN" if hit_tp else "LOSS"
                exit_type = "TP_HIT" if hit_tp else "SL_HIT"
                exit_price = current_price
                
                # Calculate runtime
                try:
                    if isinstance(signal.generated_at, str):
                        gen_time = datetime.fromisoformat(signal.generated_at)
                    else:
                        gen_time = signal.generated_at
                    runtime = int((datetime.utcnow() - gen_time).total_seconds())
                except:
                    runtime = 0
                
                # Complete the signal
                self.truth_system._complete_signal(signal, outcome, exit_type, exit_price, runtime)
                logger.info(f"🎯 Signal completed: {signal.signal_id} - {outcome} via {exit_type}")
                
        except Exception as e:
            logger.error(f"Error checking signal completion: {e}")
            
    def start_market_data_server(self):
        """Start simple HTTP server to serve market data to legacy systems"""
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        @app.route('/market-data/venom-feed')
        def venom_feed():
            symbol = request.args.get('symbol', '').upper()
            
            if symbol in self.market_cache:
                data = self.market_cache[symbol]
                age = time.time() - data['timestamp']
                
                if age < 30:  # Data less than 30 seconds old
                    return jsonify({
                        'symbol': symbol,
                        'bid': data['bid'],
                        'ask': data['ask'],
                        'timestamp': data['timestamp'],
                        'age_seconds': age
                    })
            
            return jsonify({'error': 'No recent data available'})
        
        @app.route('/health')
        def health():
            return jsonify({
                'status': 'ok',
                'symbols_tracked': len(self.market_cache),
                'last_updates': self.last_update
            })
        
        try:
            app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
            
    def run(self):
        """Start the bridge"""
        logger.info("🚀 Starting ZMQ Market Data Truth Bridge")
        
        try:
            # Start ZMQ listener
            zmq_thread = threading.Thread(target=self.zmq_market_listener)
            zmq_thread.daemon = True
            zmq_thread.start()
            
            # Start HTTP server for legacy compatibility
            http_thread = threading.Thread(target=self.start_market_data_server)
            http_thread.daemon = True
            http_thread.start()
            
            logger.info("✅ ZMQ listener and HTTP server started")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Bridge shutdown requested")
            self.running = False
        finally:
            self.context.term()

if __name__ == "__main__":
    bridge = ZMQMarketDataTruthBridge()
    bridge.run()