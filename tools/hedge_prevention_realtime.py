#!/usr/bin/env python3
"""
Real-time Hedge Prevention System
Ensures only one direction can be open at a time per symbol
Monitors position closures and immediately allows opposite direction
"""

import json
import zmq
import time
import redis
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Set, Optional

class HedgePreventionSystem:
    def __init__(self):
        # Redis for real-time state management
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
        
        # Database
        self.db_path = "/root/HydraX-v2/bitten.db"
        
        # Track current direction per symbol per user
        # Format: user:symbol -> direction (BUY/SELL/NONE)
        self.direction_locks = {}
        
        # Pending trades waiting for opposite direction to close
        self.pending_queue = []  # List of trades waiting
        
        # ZMQ for position updates
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5558")  # Confirmation listener port
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        print("🛡️ HEDGE PREVENTION SYSTEM STARTED")
        print("   One direction per symbol enforced")
        print("   Real-time position monitoring active")
        
        # Initialize current state from database
        self._initialize_state()
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_positions)
        self.monitor_thread.start()
        
    def _initialize_state(self):
        """Load current open positions from database"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Get all open positions
        cur.execute("""
            SELECT f.user_id, s.symbol, s.direction, f.fire_id, f.created_at
            FROM fires f
            JOIN missions m ON f.mission_id = m.mission_id
            JOIN signals s ON m.signal_id = s.signal_id
            WHERE f.status = 'FILLED'
            AND (f.closed_at IS NULL OR f.closed_at = 0)
            ORDER BY f.created_at DESC
        """)
        
        positions = cur.fetchall()
        conn.close()
        
        # Set direction locks for each symbol
        for user_id, symbol, direction, fire_id, created_at in positions:
            key = f"{user_id}:{symbol}"
            if key not in self.direction_locks:
                self.direction_locks[key] = direction
                print(f"   Initialized: {symbol} locked to {direction} for user {user_id}")
                
                # Store in Redis for persistence
                self.redis_client.hset("hedge:locks", key, direction)
                self.redis_client.hset(f"hedge:position:{key}", "fire_id", fire_id)
                self.redis_client.hset(f"hedge:position:{key}", "direction", direction)
                self.redis_client.hset(f"hedge:position:{key}", "opened_at", created_at)
        
        print(f"   Loaded {len(self.direction_locks)} active direction locks")
        
    def can_open_position(self, user_id: str, symbol: str, direction: str) -> tuple[bool, str]:
        """
        Check if a new position can be opened
        Returns (allowed, reason)
        """
        key = f"{user_id}:{symbol}"
        
        # Check Redis for current lock (real-time state)
        current_direction = self.redis_client.hget("hedge:locks", key)
        
        if not current_direction or current_direction == "NONE":
            # No position open, allow trade
            return True, "No existing position"
            
        if current_direction == direction:
            # Same direction, allow adding to position
            return True, f"Same direction ({direction})"
            
        # Opposite direction exists - BLOCK
        existing_fire_id = self.redis_client.hget(f"hedge:position:{key}", "fire_id")
        return False, f"Opposite {current_direction} position exists (fire_id: {existing_fire_id})"
    
    def register_new_position(self, user_id: str, symbol: str, direction: str, fire_id: str):
        """Register a new position opening"""
        key = f"{user_id}:{symbol}"
        
        # Set direction lock
        self.redis_client.hset("hedge:locks", key, direction)
        self.redis_client.hset(f"hedge:position:{key}", "fire_id", fire_id)
        self.redis_client.hset(f"hedge:position:{key}", "direction", direction) 
        self.redis_client.hset(f"hedge:position:{key}", "opened_at", int(time.time()))
        
        self.direction_locks[key] = direction
        print(f"🔒 LOCKED: {symbol} to {direction} for user {user_id} (fire_id: {fire_id})")
        
    def release_position(self, user_id: str, symbol: str, fire_id: str = None):
        """Release a position lock when closed"""
        key = f"{user_id}:{symbol}"
        
        # Clear the lock
        self.redis_client.hdel("hedge:locks", key)
        self.redis_client.delete(f"hedge:position:{key}")
        
        if key in self.direction_locks:
            old_direction = self.direction_locks[key]
            del self.direction_locks[key]
            print(f"🔓 UNLOCKED: {symbol} (was {old_direction}) for user {user_id}")
            
            # Check if any pending opposite direction trades can now execute
            self._process_pending_trades(user_id, symbol)
    
    def _process_pending_trades(self, user_id: str, symbol: str):
        """Check if any pending trades can now execute"""
        # This would integrate with the queue system to release held trades
        key = f"{user_id}:{symbol}"
        pending_key = f"hedge:pending:{key}"
        
        # Check for pending opposite direction trades
        pending = self.redis_client.lrange(pending_key, 0, -1)
        if pending:
            # Process the first pending trade
            trade_data = json.loads(pending[0])
            print(f"⚡ RELEASING PENDING: {trade_data['direction']} trade for {symbol}")
            
            # Remove from pending and trigger execution
            self.redis_client.lpop(pending_key)
            
            # Send signal to execute the trade
            # This would connect to the fire queue
            self._execute_pending_trade(trade_data)
    
    def _execute_pending_trade(self, trade_data):
        """Execute a previously blocked trade"""
        # Push to the fire queue
        context = zmq.Context()
        push = context.socket(zmq.PUSH)
        push.connect("ipc:///tmp/bitten_cmdqueue")
        push.send_json(trade_data)
        push.close()
        context.term()
        
    def _monitor_positions(self):
        """Monitor for position closures in real-time"""
        while self.running:
            try:
                # Check database for closed positions every 2 seconds
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                
                # Find positions that were open but are now closed
                for key in list(self.direction_locks.keys()):
                    user_id, symbol = key.split(":")
                    
                    # Check if position is still open
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM fires f
                        JOIN missions m ON f.mission_id = m.mission_id
                        JOIN signals s ON m.signal_id = s.signal_id
                        WHERE f.user_id = ? 
                        AND s.symbol = ?
                        AND f.status = 'FILLED'
                        AND (f.closed_at IS NULL OR f.closed_at = 0)
                    """, (user_id, symbol))
                    
                    open_count = cur.fetchone()[0]
                    
                    if open_count == 0:
                        # Position closed! Release the lock
                        self.release_position(user_id, symbol)
                
                conn.close()
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
    
    def get_status(self) -> dict:
        """Get current hedge prevention status"""
        return {
            "active_locks": len(self.direction_locks),
            "locks": dict(self.direction_locks),
            "pending_trades": self.redis_client.llen("hedge:pending:*")
        }

# Global instance
_hedge_system = None

def get_hedge_system():
    """Get or create the hedge prevention system"""
    global _hedge_system
    if _hedge_system is None:
        _hedge_system = HedgePreventionSystem()
    return _hedge_system

def check_hedge(user_id: str, symbol: str, direction: str) -> tuple[bool, str]:
    """
    Check if a trade would violate hedge prevention rules
    Returns (allowed, reason)
    """
    system = get_hedge_system()
    return system.can_open_position(user_id, symbol, direction)

def register_position(user_id: str, symbol: str, direction: str, fire_id: str):
    """Register a new position opening"""
    system = get_hedge_system()
    system.register_new_position(user_id, symbol, direction, fire_id)

def release_position(user_id: str, symbol: str, fire_id: str = None):
    """Release a position when closed"""
    system = get_hedge_system()
    system.release_position(user_id, symbol, fire_id)

if __name__ == "__main__":
    # Run as standalone service
    system = HedgePreventionSystem()
    print("\n📊 Hedge Prevention Status:")
    status = system.get_status()
    print(f"   Active locks: {status['active_locks']}")
    for key, direction in status['locks'].items():
        print(f"   {key}: {direction}")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nShutting down hedge prevention system...")
        system.running = False