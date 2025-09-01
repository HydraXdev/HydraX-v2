#!/usr/bin/env python3
"""
Immediate Position Close Detection
Detects when positions close and immediately updates live_positions table
"""

import sqlite3
import logging
import time
from typing import Set, Dict

logger = logging.getLogger(__name__)

class PositionCloseDetector:
    """Detects position closes immediately from tick data"""
    
    def __init__(self):
        self.known_open_tickets: Set[int] = set()
        self.last_check = 0
        self.db_path = "/root/HydraX-v2/bitten.db"
        
        # Load currently open positions on startup
        self._load_open_positions()
    
    def _load_open_positions(self):
        """Load currently open positions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all OPEN positions with tickets
            cursor.execute("""
                SELECT f.ticket
                FROM fires f
                JOIN live_positions lp ON f.fire_id = lp.fire_id
                WHERE lp.status = 'OPEN'
                AND f.ticket IS NOT NULL
                AND f.ticket > 0
            """)
            
            self.known_open_tickets = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            logger.info(f"Loaded {len(self.known_open_tickets)} open positions")
            
        except Exception as e:
            logger.error(f"Error loading open positions: {e}")
    
    def check_position_close(self, current_tickets: Set[int]):
        """
        Check if any positions have closed by comparing current tickets with known open
        
        Args:
            current_tickets: Set of ticket numbers currently open from tick data
        """
        try:
            # Find tickets that were open but are no longer in current tickets
            closed_tickets = self.known_open_tickets - current_tickets
            
            if closed_tickets:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for ticket in closed_tickets:
                    # Update live_positions to mark as CLOSED
                    cursor.execute("""
                        UPDATE live_positions
                        SET status = 'CLOSED',
                            last_update = ?
                        WHERE fire_id IN (
                            SELECT fire_id FROM fires WHERE ticket = ?
                        )
                    """, (int(time.time()), ticket))
                    
                    if cursor.rowcount > 0:
                        logger.info(f"✅ Position {ticket} CLOSED - direction gate unlocked")
                
                conn.commit()
                conn.close()
                
                # Update our known open tickets
                self.known_open_tickets = current_tickets.copy()
                
                return closed_tickets
            
            # Also check for new positions
            new_tickets = current_tickets - self.known_open_tickets
            if new_tickets:
                self.known_open_tickets.update(new_tickets)
                logger.debug(f"New positions opened: {new_tickets}")
            
            return set()
            
        except Exception as e:
            logger.error(f"Error checking position closes: {e}")
            return set()
    
    def process_tick_data(self, tick_data: Dict):
        """
        Process tick data to detect position closes
        
        Args:
            tick_data: Dictionary containing tick information
        """
        try:
            # Extract position ticket if present
            if 'ticket' in tick_data:
                ticket = tick_data.get('ticket')
                if ticket and ticket > 0:
                    # Single position update
                    if tick_data.get('status') in ['CLOSED', 'TP_HIT', 'SL_HIT']:
                        self.check_position_close(self.known_open_tickets - {ticket})
                    else:
                        self.known_open_tickets.add(ticket)
            
            # Check if we have bulk position data
            elif 'positions' in tick_data:
                current_tickets = set()
                for pos in tick_data.get('positions', []):
                    ticket = pos.get('ticket')
                    if ticket and ticket > 0:
                        current_tickets.add(ticket)
                
                # Check for closes
                self.check_position_close(current_tickets)
            
            # Periodically reload from database to stay in sync
            if time.time() - self.last_check > 30:
                self._load_open_positions()
                self.last_check = time.time()
                
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")

# Singleton instance
_detector = None

def get_detector() -> PositionCloseDetector:
    """Get singleton detector instance"""
    global _detector
    if _detector is None:
        _detector = PositionCloseDetector()
    return _detector

def detect_position_closes(tick_data: Dict):
    """
    Main entry point for position close detection
    
    Args:
        tick_data: Tick data from telemetry
    """
    detector = get_detector()
    detector.process_tick_data(tick_data)