#!/usr/bin/env python3
"""
Finnhub WebSocket Manager for BITTEN
=====================================
Streams real-time forex ticks from Finnhub to Redis for generator consumption.

Features:
- WebSocket connection to Finnhub (wss://ws.finnhub.io)
- Subscribes to 19 forex pairs (OANDA broker data)
- Publishes ticks to Redis pub/sub channels
- Auto-reconnect on disconnect
- Fallback-ready (generators can use ZMQ if this fails)

Created: October 21, 2025
"""

import websocket
import json
import redis
import time
import logging
from datetime import datetime
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/finnhub_ws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
FINNHUB_API_KEY = 'd3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g'
FINNHUB_WS_URL = f'wss://ws.finnhub.io?token={FINNHUB_API_KEY}'

# 19 Major + Exotic Forex Pairs (as per BITTEN standard)
FOREX_PAIRS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
    'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY', 'EURGBP', 'EURAUD', 'EURNZD',
    'GBPAUD', 'GBPNZD', 'XAUUSD', 'XAGUSD', 'USDCNH'
]

class FinnhubWebSocketManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.ws = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 999  # Infinite retries
        self.reconnect_delay = 5  # seconds
        self.tick_count = 0
        self.last_tick_time = {}
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    def convert_to_finnhub_symbol(self, mt5_symbol):
        """Convert MT5 symbol (EURUSD) to Finnhub format (OANDA:EUR_USD)"""
        if mt5_symbol.startswith('XAU'):
            return 'OANDA:XAU_USD'
        elif mt5_symbol.startswith('XAG'):
            return 'OANDA:XAG_USD'
        else:
            base = mt5_symbol[:3]
            quote = mt5_symbol[3:6]
            return f'OANDA:{base}_{quote}'
    
    def convert_from_finnhub_symbol(self, finnhub_symbol):
        """Convert Finnhub symbol (OANDA:EUR_USD) to MT5 format (EURUSD)"""
        if ':' not in finnhub_symbol:
            return finnhub_symbol
        
        pair = finnhub_symbol.split(':')[1]  # Get EUR_USD part
        return pair.replace('_', '')  # EURUSD
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            if data.get('type') == 'trade' and 'data' in data:
                for trade in data['data']:
                    symbol_mt5 = self.convert_from_finnhub_symbol(trade['s'])
                    
                    # Create tick data structure
                    tick = {
                        'symbol': symbol_mt5,
                        'price': trade['p'],
                        'timestamp': trade['t'],
                        'volume': trade.get('v', 0),
                        'source': 'finnhub',
                        'received_at': int(time.time() * 1000)
                    }
                    
                    # Publish to Redis channel
                    channel = f'market_tick_{symbol_mt5}'
                    self.redis_client.publish(channel, json.dumps(tick))
                    
                    # Also store latest tick in Redis key (for quick access)
                    self.redis_client.setex(
                        f'latest_tick_{symbol_mt5}',
                        60,  # 60 second TTL
                        json.dumps(tick)
                    )
                    
                    # Update stats
                    self.tick_count += 1
                    self.last_tick_time[symbol_mt5] = datetime.now()
                    
                    # Log every 100 ticks
                    if self.tick_count % 100 == 0:
                        logger.info(f"📊 Processed {self.tick_count} ticks | Latest: {symbol_mt5} @ {trade['p']}")
            
            elif data.get('type') == 'ping':
                # Respond to ping
                ws.send(json.dumps({'type': 'pong'}))
                logger.debug("🏓 Pong sent")
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"⚠️ WebSocket error: {error}")
        self.is_connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"⚠️ WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        
        # Attempt reconnection
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"🔄 Reconnecting in {self.reconnect_delay}s (attempt {self.reconnect_attempts})...")
            time.sleep(self.reconnect_delay)
            self.connect()
    
    def on_open(self, ws):
        """Handle WebSocket open - subscribe to all pairs"""
        logger.info("✅ Finnhub WebSocket connected!")
        self.is_connected = True
        self.reconnect_attempts = 0
        
        # Subscribe to all forex pairs
        for pair in FOREX_PAIRS:
            finnhub_symbol = self.convert_to_finnhub_symbol(pair)
            subscribe_msg = json.dumps({
                'type': 'subscribe',
                'symbol': finnhub_symbol
            })
            ws.send(subscribe_msg)
            logger.info(f"📡 Subscribed: {finnhub_symbol} ({pair})")
            time.sleep(0.1)  # Small delay to avoid overwhelming WS
    
    def connect(self):
        """Establish WebSocket connection"""
        try:
            logger.info(f"🔌 Connecting to Finnhub WebSocket...")
            
            websocket.enableTrace(False)  # Disable verbose logging
            self.ws = websocket.WebSocketApp(
                FINNHUB_WS_URL,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # Run WebSocket in separate thread
            self.ws.run_forever()
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.is_connected = False
    
    def start(self):
        """Start the WebSocket manager"""
        logger.info("🚀 Starting Finnhub WebSocket Manager...")
        logger.info(f"📊 Monitoring {len(FOREX_PAIRS)} pairs: {', '.join(FOREX_PAIRS[:5])}...")
        
        # Start connection in main thread
        self.connect()

def main():
    """Main entry point"""
    manager = FinnhubWebSocketManager()
    
    try:
        manager.start()
    except KeyboardInterrupt:
        logger.info("⏹️ Shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
