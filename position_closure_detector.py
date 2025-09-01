#!/usr/bin/env python3
"""
Position Closure Detection Service
Monitors telemetry to detect when positions close and releases slots
"""

import zmq
import json
import time
import sqlite3
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/position_closure.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PositionClosure')

class PositionClosureDetector:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.open_positions = {}  # ticket -> fire_id mapping
        self.db_path = '/root/HydraX-v2/bitten.db'
        
        # Load current open positions from database
        self.load_open_positions()
        
    def load_open_positions(self):
        """Load all filled positions that might still be open"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all filled fires that aren't marked as closed
            cursor.execute("""
                SELECT fire_id, ticket, mission_id, user_id 
                FROM fires 
                WHERE status = 'FILLED' 
                AND ticket > 0
                AND (closed_at IS NULL OR closed_at = 0)
            """)
            
            for row in cursor.fetchall():
                fire_id, ticket, mission_id, user_id = row
                self.open_positions[str(ticket)] = {
                    'fire_id': fire_id,
                    'mission_id': mission_id,
                    'user_id': user_id,
                    'ticket': ticket
                }
            
            conn.close()
            logger.info(f"Loaded {len(self.open_positions)} potentially open positions")
            
        except Exception as e:
            logger.error(f"Error loading open positions: {e}")
    
    def release_slot(self, user_id):
        """Release a slot for the user"""
        try:
            # Update fire_modes database slot tracking
            import sqlite3
            fire_modes_db = '/root/HydraX-v2/data/fire_modes.db'
            
            try:
                conn = sqlite3.connect(fire_modes_db)
                cursor = conn.cursor()
                
                # Get current slot usage
                cursor.execute("""
                    SELECT slots_in_use, auto_slots_in_use 
                    FROM user_fire_modes 
                    WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if result:
                    slots_in_use, auto_slots = result
                    if slots_in_use > 0:
                        # Decrement slot counters
                        cursor.execute("""
                            UPDATE user_fire_modes 
                            SET slots_in_use = slots_in_use - 1,
                                auto_slots_in_use = CASE 
                                    WHEN auto_slots_in_use > 0 THEN auto_slots_in_use - 1 
                                    ELSE 0 
                                END
                            WHERE user_id = ?
                        """, (user_id,))
                        
                        # Also remove from active_slots table
                        cursor.execute("""
                            DELETE FROM active_slots 
                            WHERE user_id = ? 
                            AND fire_id IN (
                                SELECT fire_id FROM active_slots 
                                WHERE user_id = ? 
                                LIMIT 1
                            )
                        """, (user_id, user_id))
                        
                        conn.commit()
                        logger.info(f"Released slot for user {user_id}: {slots_in_use} -> {slots_in_use - 1}")
                        return True
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.error(f"Error releasing slot: {e}")
            return False
    
    def mark_position_closed(self, ticket, outcome, pnl=0):
        """Mark position as closed in database"""
        try:
            ticket_str = str(ticket)
            if ticket_str not in self.open_positions:
                return  # Not tracking this position
            
            position_info = self.open_positions[ticket_str]
            fire_id = position_info['fire_id']
            user_id = position_info['user_id']
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update the fire record
            cursor.execute("""
                UPDATE fires 
                SET status = ?, closed_at = ?, pnl = ?
                WHERE fire_id = ?
            """, (outcome, int(time.time()), pnl, fire_id))
            
            # ALSO update live_positions table to mark as CLOSED
            cursor.execute("""
                UPDATE live_positions 
                SET status = 'CLOSED', 
                    last_update = ?
                WHERE fire_id = ?
            """, (int(time.time()), fire_id))
            
            conn.commit()
            conn.close()
            
            # Release slot for this user
            self.release_slot(user_id)
            
            # Remove from tracking
            del self.open_positions[ticket_str]
            
            logger.info(f"Position {ticket} closed: {outcome} (PnL: {pnl}) - Fire: {fire_id}")
            
        except Exception as e:
            logger.error(f"Error marking position closed: {e}")
    
    def process_telemetry(self, data):
        """Process telemetry data to detect closures"""
        try:
            # Check if this is position data
            if 'positions' in data:
                # Get list of currently open tickets from telemetry
                open_tickets = set()
                for position in data.get('positions', []):
                    ticket = position.get('ticket')
                    if ticket:
                        open_tickets.add(str(ticket))
                
                # Check for closed positions (in our tracking but not in telemetry)
                for tracked_ticket in list(self.open_positions.keys()):
                    if tracked_ticket not in open_tickets:
                        # Position has closed
                        self.mark_position_closed(tracked_ticket, 'CLOSED_DETECTED')
            
            # Also process individual position updates
            elif 'ticket' in data and 'profit' in data:
                ticket = str(data['ticket'])
                if ticket in self.open_positions:
                    # Check if position is closing
                    if data.get('status') in ['CLOSED', 'TP_HIT', 'SL_HIT']:
                        outcome = data.get('status', 'CLOSED')
                        pnl = data.get('profit', 0)
                        self.mark_position_closed(ticket, outcome, pnl)
                        
        except Exception as e:
            logger.error(f"Error processing telemetry: {e}")
    
    def run(self):
        """Main monitoring loop"""
        # Subscribe to telemetry
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5560")  # Telemetry stream
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        
        logger.info("Position closure detector running...")
        logger.info(f"Monitoring {len(self.open_positions)} positions")
        
        last_check = time.time()
        
        while True:
            try:
                # Try to receive telemetry
                try:
                    message = self.subscriber.recv_string()
                    # Parse the message
                    if message.startswith('TICK '):
                        # Extract JSON from tick message
                        json_str = message[5:]
                        data = json.loads(json_str)
                        self.process_telemetry(data)
                    else:
                        data = json.loads(message)
                        self.process_telemetry(data)
                        
                except zmq.Again:
                    pass  # Timeout is normal
                
                # Every 30 seconds, log status
                if time.time() - last_check > 30:
                    logger.info(f"Still monitoring {len(self.open_positions)} open positions")
                    last_check = time.time()
                    
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(1)
        
        # Cleanup
        self.subscriber.close()
        self.context.term()
        logger.info("Position closure detector stopped")

if __name__ == "__main__":
    detector = PositionClosureDetector()
    detector.run()