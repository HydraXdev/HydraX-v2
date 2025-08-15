#!/usr/bin/env python3
"""
Live Position Monitor - Real-time tracking of open positions
Updates database with current prices and P&L
Sends alerts when positions approach TP/SL
"""

import json
import zmq
import time
import redis
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("POSITION_MONITOR")

class LivePositionMonitor:
    def __init__(self):
        # ZMQ for market data
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5560")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Redis for real-time updates
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
        
        # Database
        self.db_path = "/root/HydraX-v2/bitten.db"
        
        # Track open positions
        self.open_positions = {}  # fire_id -> position data
        self.last_reload = time.time()
        
        logger.info("📊 Live Position Monitor started")
        logger.info("   Tracking open positions with real-time P&L")
        
        # Create position tracking table if needed
        self._ensure_tables()
        
        # Load initial positions
        self.reload_open_positions()
        
    def _ensure_tables(self):
        """Ensure position tracking tables exist"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Create live positions table for real-time tracking
        cur.execute("""
            CREATE TABLE IF NOT EXISTS live_positions (
                fire_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL,
                sl REAL,
                tp REAL,
                lot_size REAL,
                current_pips REAL,
                current_pnl REAL,
                max_pips REAL,
                min_pips REAL,
                duration_seconds INTEGER,
                last_update INTEGER,
                status TEXT DEFAULT 'OPEN'
            )
        """)
        
        # Create position events table for tracking important moments
        cur.execute("""
            CREATE TABLE IF NOT EXISTS position_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fire_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,  -- OPENED, NEAR_TP, NEAR_SL, CLOSED_TP, CLOSED_SL, CLOSED_MANUAL
                event_data TEXT,
                created_at INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
        
    def reload_open_positions(self):
        """Load all open positions from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get open trades from fires table
        open_fires = cur.execute("""
            SELECT f.*, m.payload_json
            FROM fires f
            LEFT JOIN missions m ON f.mission_id = m.mission_id
            WHERE f.status = 'FILLED' 
            AND NOT EXISTS (
                SELECT 1 FROM signal_outcomes s 
                WHERE s.signal_id = f.mission_id 
                AND s.outcome IN ('TP_HIT', 'SL_HIT', 'TIMEOUT')
            )
            ORDER BY f.created_at DESC
        """).fetchall()
        
        self.open_positions = {}
        
        for fire in open_fires:
            # Parse mission payload
            payload = {}
            if fire['payload_json']:
                try:
                    payload = json.loads(fire['payload_json'])
                except:
                    continue
            
            position = {
                'fire_id': fire['fire_id'],
                'user_id': fire['user_id'],
                'mission_id': fire['mission_id'],
                'symbol': payload.get('symbol', 'UNKNOWN'),
                'direction': payload.get('direction', 'UNKNOWN'),
                'entry_price': float(payload.get('entry_price', 0) or fire['price'] or 0),
                'sl': float(payload.get('sl', 0) or payload.get('stop_loss', 0)),
                'tp': float(payload.get('tp', 0) or payload.get('take_profit', 0)),
                'lot_size': float(payload.get('lot_size', 0.01)),
                'ticket': fire['ticket'],
                'opened_at': fire['created_at'],
                'max_pips': 0,
                'min_pips': 0,
                'last_price': 0
            }
            
            # Only track if we have valid data
            if position['symbol'] != 'UNKNOWN' and position['entry_price'] > 0:
                self.open_positions[fire['fire_id']] = position
                
                # Store in live positions table
                self._update_live_position(position)
        
        conn.close()
        logger.info(f"   Loaded {len(self.open_positions)} open positions")
        
    def _update_live_position(self, position: Dict, current_price: float = 0):
        """Update live position in database"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Calculate current metrics
        if current_price > 0:
            pips = self._calculate_pips(position, current_price)
            pnl = self._calculate_pnl(position, current_price, pips)
            
            # Update max/min
            position['max_pips'] = max(position.get('max_pips', pips), pips)
            position['min_pips'] = min(position.get('min_pips', pips), pips)
        else:
            pips = 0
            pnl = 0
        
        # Calculate duration
        duration = int(time.time() - position['opened_at']) if position.get('opened_at') else 0
        
        # Upsert into live positions
        cur.execute("""
            INSERT OR REPLACE INTO live_positions (
                fire_id, user_id, symbol, direction, entry_price,
                current_price, sl, tp, lot_size, current_pips,
                current_pnl, max_pips, min_pips, duration_seconds,
                last_update, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position['fire_id'], position['user_id'], position['symbol'],
            position['direction'], position['entry_price'], current_price,
            position['sl'], position['tp'], position['lot_size'],
            pips, pnl, position.get('max_pips', 0), position.get('min_pips', 0),
            duration, int(time.time()), 'OPEN'
        ))
        
        conn.commit()
        conn.close()
        
        # Also update Redis for real-time access
        self.redis_client.setex(
            f"position:{position['fire_id']}",
            60,  # 60 second TTL
            json.dumps({
                'symbol': position['symbol'],
                'direction': position['direction'],
                'entry': position['entry_price'],
                'current': current_price,
                'pips': pips,
                'pnl': pnl,
                'sl': position['sl'],
                'tp': position['tp']
            })
        )
        
    def _calculate_pips(self, position: Dict, current_price: float) -> float:
        """Calculate current pips for position"""
        if not position['entry_price'] or not current_price:
            return 0
            
        pip_size = self._get_pip_size(position['symbol'])
        
        if position['direction'] == 'BUY':
            return (current_price - position['entry_price']) / pip_size
        else:
            return (position['entry_price'] - current_price) / pip_size
            
    def _calculate_pnl(self, position: Dict, current_price: float, pips: float) -> float:
        """Calculate current P&L in USD"""
        pip_value = self._get_pip_value(position['symbol'], position['lot_size'])
        return pips * pip_value
        
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        s = symbol.upper()
        if s.endswith("JPY"):
            return 0.01
        elif s.startswith("XAU"):
            return 0.1
        elif s.startswith("XAG"):
            return 0.01
        else:
            return 0.0001
            
    def _get_pip_value(self, symbol: str, lot_size: float) -> float:
        """Get pip value in USD"""
        if symbol.endswith("JPY"):
            pip_value_per_lot = 1000 / 147  # Approximate
        elif symbol.startswith("XAU"):
            pip_value_per_lot = 10
        else:
            pip_value_per_lot = 10
            
        return pip_value_per_lot * lot_size
        
    def check_alerts(self, position: Dict, current_price: float):
        """Check if position needs alerts (near TP/SL)"""
        if not position['sl'] or not position['tp']:
            return
            
        # Calculate distances
        if position['direction'] == 'BUY':
            sl_distance = abs(current_price - position['sl'])
            tp_distance = abs(position['tp'] - current_price)
        else:
            sl_distance = abs(position['sl'] - current_price)
            tp_distance = abs(current_price - position['tp'])
            
        pip_size = self._get_pip_size(position['symbol'])
        sl_pips = sl_distance / pip_size
        tp_pips = tp_distance / pip_size
        
        # Alert if within 5 pips of TP/SL
        if tp_pips <= 5:
            self._send_alert(position, 'NEAR_TP', current_price)
        elif sl_pips <= 5:
            self._send_alert(position, 'NEAR_SL', current_price)
            
    def _send_alert(self, position: Dict, alert_type: str, current_price: float):
        """Send alert to user via Redis pub/sub"""
        alert = {
            'type': alert_type,
            'fire_id': position['fire_id'],
            'user_id': position['user_id'],
            'symbol': position['symbol'],
            'current_price': current_price,
            'target': position['tp'] if 'TP' in alert_type else position['sl'],
            'timestamp': time.time()
        }
        
        # Publish to user's alert channel
        self.redis_client.publish(f"alerts:{position['user_id']}", json.dumps(alert))
        
        # Log event
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO position_events (fire_id, user_id, event_type, event_data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (position['fire_id'], position['user_id'], alert_type, json.dumps(alert), int(time.time())))
        conn.commit()
        conn.close()
        
    def process_tick(self, symbol: str, bid: float, ask: float):
        """Process incoming tick data"""
        # Use mid price
        current_price = (bid + ask) / 2
        
        # Update all positions for this symbol
        updates = 0
        for fire_id, position in self.open_positions.items():
            if position['symbol'] == symbol:
                position['last_price'] = current_price
                self._update_live_position(position, current_price)
                self.check_alerts(position, current_price)
                updates += 1
                
        if updates > 0:
            logger.debug(f"Updated {updates} positions for {symbol} @ {current_price:.5f}")
            
    def run(self):
        """Main loop"""
        logger.info("Starting main loop...")
        
        while True:
            try:
                # Reload positions every 30 seconds
                if time.time() - self.last_reload > 30:
                    self.reload_open_positions()
                    self.last_reload = time.time()
                
                # Check for market data with timeout
                if self.subscriber.poll(100):  # 100ms timeout
                    message = self.subscriber.recv_string(zmq.NOBLOCK)
                    
                    # Parse tick data
                    if message.startswith("TICK "):
                        try:
                            tick_json = message[5:]
                            tick = json.loads(tick_json)
                            
                            symbol = tick.get('symbol')
                            bid = float(tick.get('bid', 0))
                            ask = float(tick.get('ask', 0))
                            
                            if symbol and bid > 0 and ask > 0:
                                self.process_tick(symbol, bid, ask)
                                
                                # Store latest tick in Redis
                                self.redis_client.setex(
                                    f"tick:{symbol}",
                                    10,
                                    json.dumps({'bid': bid, 'ask': ask, 'time': time.time()})
                                )
                        except Exception as e:
                            logger.debug(f"Error processing tick: {e}")
                            
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(1)
                
if __name__ == "__main__":
    monitor = LivePositionMonitor()
    monitor.run()