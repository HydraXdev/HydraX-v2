#!/usr/bin/env python3
"""
EA Position Query System - Direct communication with EA to get current open positions
This allows us to compare what we think is open vs what's actually open
"""

import zmq
import json
import time
import logging
import sqlite3
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EAPositionQuery:
    def __init__(self):
        self.context = zmq.Context()
        self.command_socket = None
        self.response_timeout = 5000  # 5 seconds
        
    def connect_to_ea(self, target_uuid: str = "COMMANDER_DEV_001"):
        """Connect to EA for direct queries"""
        try:
            self.command_socket = self.context.socket(zmq.REQ)
            self.command_socket.setsockopt(zmq.RCVTIMEO, self.response_timeout)
            self.command_socket.connect("tcp://134.199.204.67:5555")  # Command router
            logger.info(f"Connected to EA {target_uuid}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to EA: {e}")
            return False
    
    def query_open_positions(self, target_uuid: str = "COMMANDER_DEV_001") -> Optional[List[Dict]]:
        """Query EA for all currently open positions"""
        if not self.command_socket:
            if not self.connect_to_ea(target_uuid):
                return None
        
        try:
            # Send position query command
            query_command = {
                "type": "query_positions",
                "target_uuid": target_uuid,
                "request_id": f"pos_query_{int(time.time())}"
            }
            
            logger.debug(f"Sending position query to {target_uuid}")
            self.command_socket.send_json(query_command)
            
            # Wait for response
            response = self.command_socket.recv_json()
            
            if response.get('type') == 'position_list':
                positions = response.get('positions', [])
                logger.info(f"EA {target_uuid} reports {len(positions)} open positions")
                return positions
            else:
                logger.warning(f"Unexpected response type: {response.get('type')}")
                return None
                
        except zmq.Again:
            logger.warning(f"Timeout waiting for position query response from {target_uuid}")
            return None
        except Exception as e:
            logger.error(f"Error querying positions: {e}")
            return None
    
    def compare_with_tracked_positions(self, user_id: str) -> Dict:
        """Compare EA positions with our tracked positions"""
        # Get what we think is open
        bitten_conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        bitten_cur = bitten_conn.cursor()
        
        bitten_cur.execute("""
            SELECT f.fire_id, f.ticket, f.mission_id, s.symbol
            FROM fires f
            JOIN missions m ON f.mission_id = m.mission_id  
            JOIN signals s ON m.signal_id = s.signal_id
            WHERE f.user_id = ? 
            AND f.status IN ('FILLED', 'CONFIRMED')
            AND f.ticket IS NOT NULL 
            AND f.ticket > 0
        """, (user_id,))
        
        tracked_positions = bitten_cur.fetchall()
        bitten_conn.close()
        
        # Get what EA says is actually open
        ea_positions = self.query_open_positions()
        
        if ea_positions is None:
            logger.warning("Could not get EA position data for comparison")
            return {'error': 'EA communication failed'}
        
        # Convert to sets for comparison
        tracked_tickets = {row[1] for row in tracked_positions if row[1]}  # ticket numbers
        ea_tickets = {pos.get('ticket') for pos in ea_positions}
        
        # Find discrepancies
        orphaned_in_db = tracked_tickets - ea_tickets  # We think it's open, but EA doesn't
        orphaned_in_ea = ea_tickets - tracked_tickets  # EA has it open, but we don't track it
        
        result = {
            'user_id': user_id,
            'tracked_count': len(tracked_tickets),
            'ea_count': len(ea_tickets),
            'orphaned_in_db': list(orphaned_in_db),  # These should be closed
            'orphaned_in_ea': list(orphaned_in_ea),   # These might need tracking
            'matched': len(tracked_tickets & ea_tickets)
        }
        
        logger.info(f"Position comparison for {user_id}: {result['tracked_count']} tracked, "
                   f"{result['ea_count']} actual, {len(orphaned_in_db)} orphaned")
        
        return result
    
    def close_orphaned_positions(self, comparison_result: Dict) -> int:
        """Close positions that we track but EA doesn't have"""
        orphaned_tickets = comparison_result.get('orphaned_in_db', [])
        user_id = comparison_result.get('user_id')
        
        if not orphaned_tickets:
            return 0
        
        logger.info(f"Closing {len(orphaned_tickets)} orphaned positions for {user_id}")
        
        # Import fire mode database
        import sys
        sys.path.append('/root/HydraX-v2/src')
        from src.bitten_core.fire_mode_database import FireModeDatabase
        fire_db = FireModeDatabase()
        
        bitten_conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        bitten_cur = bitten_conn.cursor()
        
        closed_count = 0
        
        for ticket in orphaned_tickets:
            try:
                # Get fire details
                bitten_cur.execute("""
                    SELECT f.fire_id, f.mission_id, f.user_id
                    FROM fires f
                    WHERE f.ticket = ? AND f.user_id = ?
                """, (ticket, user_id))
                
                fire_result = bitten_cur.fetchone()
                
                if fire_result:
                    fire_id, mission_id, user_id = fire_result
                    
                    # Mark fire as closed
                    bitten_cur.execute("""
                        UPDATE fires 
                        SET status = 'CLOSED_EA_SYNC', updated_at = ?
                        WHERE fire_id = ?
                    """, (int(time.time()), fire_id))
                    
                    # Release slot
                    if fire_db.release_slot(user_id, mission_id):
                        logger.info(f"✅ Closed orphaned position: {fire_id} (ticket {ticket})")
                        closed_count += 1
                    else:
                        logger.warning(f"⚠️ Could not release slot for {fire_id}")
                        
            except Exception as e:
                logger.error(f"❌ Error closing orphaned position {ticket}: {e}")
        
        bitten_conn.commit()
        bitten_conn.close()
        
        return closed_count
    
    def sync_user_positions(self, user_id: str) -> Dict:
        """Complete position sync for a user"""
        logger.info(f"🔄 Syncing positions for user {user_id}")
        
        comparison = self.compare_with_tracked_positions(user_id)
        
        if 'error' in comparison:
            return comparison
        
        closed_count = self.close_orphaned_positions(comparison)
        
        return {
            **comparison,
            'slots_released': closed_count,
            'sync_timestamp': time.time()
        }
    
    def close(self):
        """Close ZMQ connections"""
        if self.command_socket:
            self.command_socket.close()
        self.context.term()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='EA Position Query and Sync')
    parser.add_argument('--user-id', type=str, help='Sync positions for specific user')
    parser.add_argument('--query-only', action='store_true', help='Only query, do not sync')
    
    args = parser.parse_args()
    
    query_system = EAPositionQuery()
    
    try:
        if args.user_id:
            if args.query_only:
                result = query_system.compare_with_tracked_positions(args.user_id)
                print(json.dumps(result, indent=2))
            else:
                result = query_system.sync_user_positions(args.user_id)
                print(f"Sync complete: {result['slots_released']} slots released")
        else:
            positions = query_system.query_open_positions()
            if positions:
                print(f"EA reports {len(positions)} open positions")
                for pos in positions:
                    print(f"  - Ticket {pos.get('ticket')}: {pos.get('symbol')} {pos.get('volume')} lots")
            else:
                print("Could not retrieve position data")
    finally:
        query_system.close()