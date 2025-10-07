#!/usr/bin/env python3
"""
Enhanced Slot Manager with Event Bus Integration
Real-time slot management using enhanced heartbeat position tracking
"""

import sqlite3
import time
import logging
import json
import sys
import threading
from datetime import datetime

# Add src path for imports
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

# Event Bus integration
try:
    from event_bus.consumer import EventConsumer
    from event_bus.producer import EventProducer
    EVENT_BUS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Event Bus not available: {e}")
    EVENT_BUS_AVAILABLE = False

from src.bitten_core.fire_mode_database import FireModeDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSlotManager:
    def __init__(self):
        self.fire_mode_db = FireModeDatabase()
        self.bitten_db_path = "/root/HydraX-v2/bitten.db"
        
        # Event bus components
        if EVENT_BUS_AVAILABLE:
            self.event_consumer = EventConsumer()
            self.event_producer = EventProducer()
        else:
            self.event_consumer = None
            self.event_producer = None
            
        # User slot tracking
        self.user_slots = {}  # user_id -> {used: int, total: int, positions: []}
        
        # Initialize slot data
        self.refresh_user_slots()
        
    def refresh_user_slots(self):
        """Refresh user slot allocation and current usage FROM EA HEARTBEAT (SOURCE OF TRUTH)"""
        logger.info("🔄 Refreshing user slot data from EA heartbeat...")

        conn = sqlite3.connect(self.bitten_db_path)
        cur = conn.cursor()

        # Get EA instance data (updated every second from port 5556 heartbeat)
        cur.execute("""
            SELECT target_uuid, user_id, open_positions
            FROM ea_instances
            WHERE user_id IS NOT NULL
        """)

        ea_instances = cur.fetchall()
        conn.close()

        if not ea_instances:
            logger.warning("⚠️ No EA instances with user_id found")
            return

        for target_uuid, user_id, ea_open_positions in ea_instances:
            # Get user's max slot allocation
            user_mode = self.fire_mode_db.get_user_mode(user_id)
            max_auto_slots = user_mode.get('max_auto_slots', 3)

            # EA heartbeat is source of truth for position count
            used_slots = ea_open_positions if ea_open_positions else 0

            self.user_slots[user_id] = {
                'used': used_slots,
                'total': max_auto_slots,
                'positions': [],  # Don't need details for slot count
                'last_update': int(time.time())
            }

            # Sync fire_modes database with EA reality
            fire_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
            fire_cursor = fire_conn.cursor()
            fire_cursor.execute("""
                UPDATE user_fire_modes
                SET auto_slots_in_use = ?
                WHERE user_id = ?
            """, (used_slots, user_id))
            fire_conn.commit()
            fire_conn.close()

            logger.info(f"✅ User {user_id} ({target_uuid}): {used_slots}/{max_auto_slots} slots (EA TRUTH)")

        logger.info("🎯 Slot sync complete - using EA heartbeat as source of truth")
        
    def handle_position_closed_event(self, event_data):
        """Handle position closure events from enhanced heartbeat"""
        user_id = event_data.get('user_id')
        fire_id = event_data.get('fire_id')
        symbol = event_data.get('symbol')
        
        if not user_id or not fire_id:
            logger.warning("⚠️ Invalid position close event: missing user_id or fire_id")
            return
            
        logger.info(f"🔓 Processing slot release: {fire_id} for user {user_id}")
        
        # Update user slot tracking
        if user_id in self.user_slots:
            self.user_slots[user_id]['used'] = max(0, self.user_slots[user_id]['used'] - 1)
            
            # Remove position from tracking
            self.user_slots[user_id]['positions'] = [
                pos for pos in self.user_slots[user_id]['positions'] 
                if pos.get('fire_id') != fire_id
            ]
            
            self.user_slots[user_id]['last_update'] = int(time.time())
            
            logger.info(f"✅ Released slot for user {user_id}: {self.user_slots[user_id]['used']}/{self.user_slots[user_id]['total']} used")
            
            # Publish slot availability update
            if self.event_producer:
                try:
                    slot_update = {
                        'user_id': user_id,
                        'slots_used': self.user_slots[user_id]['used'],
                        'slots_total': self.user_slots[user_id]['total'],
                        'slots_available': self.user_slots[user_id]['total'] - self.user_slots[user_id]['used'],
                        'released_fire_id': fire_id,
                        'timestamp': int(time.time())
                    }
                    self.event_producer.publish("slot.availability_update.v1", slot_update)
                    logger.info(f"📡 Published slot availability update for user {user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to publish slot update: {e}")
        else:
            logger.warning(f"⚠️ User {user_id} not found in slot tracking")
            
    def handle_position_count_update(self, event_data):
        """Handle real-time position count updates from enhanced heartbeat"""
        target_uuid = event_data.get('target_uuid')
        ea_count = event_data.get('ea_position_count', 0)
        positions = event_data.get('positions', [])
        
        logger.debug(f"📊 Position count update from {target_uuid}: {ea_count} positions")
        
        # Update slot tracking based on actual EA positions
        user_position_counts = {}
        for pos in positions:
            fire_id = pos.get('fire_id', '')
            if fire_id.startswith('TEST_TRACKING_'):
                continue  # Skip test positions
                
            # Get user_id from fire_id or database lookup
            user_id = self.get_user_id_for_fire_id(fire_id)
            if user_id:
                if user_id not in user_position_counts:
                    user_position_counts[user_id] = []
                user_position_counts[user_id].append(pos)
        
        # Update slot tracking with real EA data
        for user_id, user_positions in user_position_counts.items():
            if user_id in self.user_slots:
                self.user_slots[user_id]['used'] = len(user_positions)
                self.user_slots[user_id]['positions'] = user_positions
                self.user_slots[user_id]['last_update'] = int(time.time())
                
                logger.debug(f"🔄 Updated slots for user {user_id}: {len(user_positions)} used")
    
    def get_user_id_for_fire_id(self, fire_id):
        """Get user_id associated with a fire_id"""
        try:
            conn = sqlite3.connect(self.bitten_db_path)
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM fires WHERE fire_id = ?", (fire_id,))
            result = cur.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logger.warning(f"Failed to get user_id for fire_id {fire_id}: {e}")
            return None
    
    def get_user_slot_status(self, user_id):
        """Get current slot status for a user"""
        if user_id not in self.user_slots:
            self.refresh_user_slots()
            
        return self.user_slots.get(user_id, {
            'used': 0,
            'total': 3,
            'positions': [],
            'last_update': int(time.time())
        })
    
    def can_user_fire(self, user_id):
        """Check if user has available slots to fire"""
        slot_status = self.get_user_slot_status(user_id)
        available = slot_status['total'] - slot_status['used']
        
        logger.info(f"🎯 User {user_id} slot check: {slot_status['used']}/{slot_status['total']} used, {available} available")
        
        return available > 0
    
    def start_event_listening(self):
        """Start listening for event bus messages"""
        if not EVENT_BUS_AVAILABLE or not self.event_consumer:
            logger.warning("⚠️ Event bus not available - using periodic refresh only")
            return
            
        logger.info("🎧 Starting event bus listener for slot management...")
        
        # Subscribe to slot-related events
        self.event_consumer.subscribe("slot.position_closed.v1", self.handle_position_closed_event)
        self.event_consumer.subscribe("position.count_update.v1", self.handle_position_count_update)
        
        # Start event processing
        self.event_consumer.start()
        
    def run_periodic_refresh(self):
        """Run periodic slot refresh in background"""
        while True:
            try:
                time.sleep(60)  # Refresh every minute
                self.refresh_user_slots()
            except Exception as e:
                logger.error(f"Periodic refresh error: {e}")
                time.sleep(30)  # Wait longer on error
    
    def run(self):
        """Main run loop"""
        logger.info("🚀 Enhanced Slot Manager starting...")
        
        # Start event bus listening
        if EVENT_BUS_AVAILABLE:
            event_thread = threading.Thread(target=self.start_event_listening, daemon=True)
            event_thread.start()
        
        # Start periodic refresh
        refresh_thread = threading.Thread(target=self.run_periodic_refresh, daemon=True)
        refresh_thread.start()
        
        logger.info("✅ Enhanced Slot Manager running - monitoring user slots in real-time")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(10)
                # Log current slot status every 10 minutes
                if int(time.time()) % 600 == 0:
                    for user_id, slots in self.user_slots.items():
                        logger.info(f"📊 User {user_id}: {slots['used']}/{slots['total']} slots used")
        except KeyboardInterrupt:
            logger.info("🛑 Enhanced Slot Manager shutting down...")

if __name__ == "__main__":
    manager = EnhancedSlotManager()
    manager.run()