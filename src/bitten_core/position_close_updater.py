#!/usr/bin/env python3
"""
Position Close Updater
Updates live_positions table when positions are detected as closed
"""

import sqlite3
import logging
from typing import Set

logger = logging.getLogger(__name__)

def update_closed_positions():
    """
    Check for closed positions and update live_positions table
    This should be called periodically to sync position status
    """
    try:
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        cursor = conn.cursor()
        
        # Get all positions marked as OPEN in live_positions
        cursor.execute("""
            SELECT lp.fire_id, lp.symbol, lp.direction, f.ticket
            FROM live_positions lp
            LEFT JOIN fires f ON lp.fire_id = f.fire_id
            WHERE lp.status = 'OPEN'
            AND lp.user_id = '7176191872'
        """)
        
        open_positions = cursor.fetchall()
        
        if not open_positions:
            return
        
        # Check each position to see if it's actually still open
        # by checking if we're receiving tick updates for it
        for fire_id, symbol, direction, ticket in open_positions:
            if ticket:
                # Check if this ticket exists in position_events as closed
                cursor.execute("""
                    SELECT event_type 
                    FROM position_events 
                    WHERE ticket = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (ticket,))
                
                last_event = cursor.fetchone()
                
                # If last event indicates closure, update live_positions
                if last_event and last_event[0] in ['CLOSED', 'TP_HIT', 'SL_HIT', 'TIMEOUT_CLOSE']:
                    cursor.execute("""
                        UPDATE live_positions
                        SET status = 'CLOSED',
                            last_update = strftime('%s', 'now')
                        WHERE fire_id = ?
                    """, (fire_id,))
                    
                    logger.info(f"Marked position {fire_id} (ticket {ticket}) as CLOSED")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error updating closed positions: {e}")

def check_orphaned_positions():
    """
    Check for positions that have been open too long without updates
    and mark them as likely closed
    """
    try:
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        cursor = conn.cursor()
        
        # Find positions that haven't been updated in over 5 minutes (not 1 hour!)
        # This allows much faster unlocking of the direction gate
        cursor.execute("""
            UPDATE live_positions
            SET status = 'STALE'
            WHERE status = 'OPEN'
            AND last_update < strftime('%s', 'now', '-5 minutes')
        """)
        
        stale_count = cursor.rowcount
        
        if stale_count > 0:
            logger.info(f"Marked {stale_count} stale positions")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking orphaned positions: {e}")

def get_actual_open_tickets() -> Set[int]:
    """
    Get tickets that are actually open by checking recent position events
    """
    try:
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        cursor = conn.cursor()
        
        # Get tickets with recent FILLED events but no close events after
        cursor.execute("""
            WITH latest_events AS (
                SELECT 
                    ticket,
                    event_type,
                    ROW_NUMBER() OVER (PARTITION BY ticket ORDER BY timestamp DESC) as rn
                FROM position_events
                WHERE timestamp > strftime('%s', 'now', '-24 hours')
            )
            SELECT DISTINCT ticket
            FROM latest_events
            WHERE rn = 1 
            AND event_type IN ('FILLED', 'PARTIAL_CLOSE', 'BE_MOVED', 'TRAIL_STARTED')
        """)
        
        open_tickets = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        return open_tickets
        
    except Exception as e:
        logger.error(f"Error getting open tickets: {e}")
        return set()

def sync_position_status():
    """
    Main sync function to update position status based on actual state
    """
    try:
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        cursor = conn.cursor()
        
        # Get actual open tickets
        actual_open = get_actual_open_tickets()
        
        # Get what live_positions thinks is open
        cursor.execute("""
            SELECT fire_id, ticket
            FROM fires f
            JOIN live_positions lp ON f.fire_id = lp.fire_id
            WHERE lp.status = 'OPEN'
        """)
        
        tracked_open = cursor.fetchall()
        
        # Close positions that are no longer open
        for fire_id, ticket in tracked_open:
            if ticket and ticket not in actual_open:
                cursor.execute("""
                    UPDATE live_positions
                    SET status = 'CLOSED',
                        last_update = strftime('%s', 'now')
                    WHERE fire_id = ?
                """, (fire_id,))
                
                logger.info(f"Closed orphaned position {fire_id} (ticket {ticket})")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Position sync complete. Actual open: {len(actual_open)}, Updated closures")
        
    except Exception as e:
        logger.error(f"Error syncing position status: {e}")

if __name__ == "__main__":
    # Run sync when called directly
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Syncing position status...")
    sync_position_status()
    print("Checking orphaned positions...")
    check_orphaned_positions()
    print("Done!")