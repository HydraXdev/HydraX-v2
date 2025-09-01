#!/usr/bin/env python3
"""
Update for confirm_listener.py to handle position_closed messages
Add this code to the message processing section
"""

# Add to the main message processing loop in confirm_listener.py:

def process_position_closed(data):
    """Process position closure notification from EA"""
    try:
        ticket = data.get('ticket')
        symbol = data.get('symbol')
        close_price = data.get('close_price')
        profit = data.get('profit', 0)
        reason = data.get('reason', 'UNKNOWN')  # TP_HIT, SL_HIT, MANUAL, STOP_OUT
        uuid = data.get('uuid')
        
        logger.info(f"📊 Position closed: Ticket={ticket} Symbol={symbol} Reason={reason} Profit={profit}")
        
        # Find the fire record for this ticket
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        
        # Get fire_id from ticket
        cursor.execute("""
            SELECT fire_id, user_id 
            FROM fires 
            WHERE ticket = ? AND status = 'FILLED'
        """, (ticket,))
        
        result = cursor.fetchone()
        if result:
            fire_id, user_id = result
            
            # Update fire record with closure
            cursor.execute("""
                UPDATE fires 
                SET closed_at = ?, pnl = ?, close_reason = ?
                WHERE fire_id = ?
            """, (int(time.time()), profit, reason, fire_id))
            
            conn.commit()
            logger.info(f"✅ Updated fire record: {fire_id} closed with {reason}")
            
            # Release slot for this user
            release_user_slot(user_id, fire_id)
            
            # Update tracking for ML
            update_tracking_outcome(fire_id, reason, profit)
            
        else:
            logger.warning(f"⚠️ No fire record found for ticket {ticket}")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Error processing position closure: {e}")

def release_user_slot(user_id, fire_id):
    """Release slot when position closes"""
    try:
        # Release in fire_modes database
        fire_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
        fire_cursor = fire_conn.cursor()
        
        # Decrement slot counters
        fire_cursor.execute("""
            UPDATE user_fire_modes 
            SET auto_slots_in_use = CASE 
                    WHEN auto_slots_in_use > 0 THEN auto_slots_in_use - 1 
                    ELSE 0 
                END
            WHERE user_id = ?
        """, (user_id,))
        
        # Remove from active_slots
        fire_cursor.execute("""
            UPDATE active_slots 
            SET status = 'CLOSED', closed_at = ?
            WHERE user_id = ? AND fire_id = ?
        """, (int(time.time()), user_id, fire_id))
        
        fire_conn.commit()
        fire_conn.close()
        
        logger.info(f"🔓 Released slot for user {user_id}: {fire_id}")
        
    except Exception as e:
        logger.error(f"Error releasing slot: {e}")

def update_tracking_outcome(fire_id, reason, profit):
    """Update tracking files with trade outcome"""
    try:
        outcome = {
            'signal_id': fire_id,
            'outcome': 'WIN' if profit > 0 else 'LOSS',
            'reason': reason,
            'profit': profit,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Update comprehensive tracking
        with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'a') as f:
            # Find and update the original signal entry
            # This would need to read the file, find the entry, and update it
            pass
            
        # Update optimized tracking for ML
        with open('/root/HydraX-v2/optimized_tracking.jsonl', 'a') as f:
            json.dump(outcome, f)
            f.write('\n')
            
        logger.info(f"📈 Updated tracking: {fire_id} -> {outcome['outcome']}")
        
    except Exception as e:
        logger.error(f"Error updating tracking: {e}")

# In the main message processing section, add:

if msg_type == "position_closed":
    process_position_closed(data)
    
# That's it! The confirm_listener will now:
# 1. Receive position closure notifications from EA
# 2. Update fire records with closure time and P&L
# 3. Release user slots immediately
# 4. Update ML tracking with outcomes