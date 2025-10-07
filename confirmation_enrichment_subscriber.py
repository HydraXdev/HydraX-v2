#!/usr/bin/env python3
"""
Confirmation Enrichment Subscriber
Subscribes to existing confirmation bus and enriches confirmations with slot and account data
"""

import json
import sqlite3
import logging
import time
from datetime import datetime
from typing import Dict, Optional

# Event bus imports
import sys
sys.path.append('/root/HydraX-v2/src')
from event_bus.consumer import EventConsumer
from event_bus.producer import EventProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfirmationEnrichmentSubscriber:
    """Enriches confirmation events with slot and account information"""

    def __init__(self):
        self.consumer = EventConsumer()
        self.producer = EventProducer()
        self.bitten_db_path = "/root/HydraX-v2/bitten.db"
        self.fire_modes_db_path = "/root/HydraX-v2/data/fire_modes.db"

        # Subscribe to raw confirmations from EA
        self.consumer.subscribe_to_schema("execution.confirmation.v1", self.handle_raw_confirmation)

        logger.info("Confirmation Enrichment Subscriber initialized")

    def handle_raw_confirmation(self, event_data: Dict):
        """Handle raw confirmation from EA and enrich with slot/account data"""
        try:
            fire_id = event_data.get('fire_id', '')
            status = event_data.get('status', '').upper()
            ticket = event_data.get('ticket', 0)
            price = event_data.get('price', 0.0)
            message = event_data.get('message', '')

            logger.info(f"📨 Raw confirmation: {fire_id} | Status: {status} | Ticket: {ticket}")

            # Get fire details from database
            enriched_data = self.enrich_confirmation(event_data)

            if enriched_data:
                # Update database with enriched information
                self.update_fire_record(enriched_data)

                # Update slot status
                self.update_slot_status(enriched_data)

                # Publish enriched confirmation
                self.producer.publish_event("execution.confirmation.enriched.v1", enriched_data)

                logger.info(f"✅ Published enriched confirmation for {fire_id}")
            else:
                logger.warning(f"❌ Failed to enrich confirmation for {fire_id}")

        except Exception as e:
            logger.error(f"Error handling confirmation: {e}")

    def enrich_confirmation(self, raw_data: Dict) -> Optional[Dict]:
        """Enrich raw confirmation with slot and account data"""
        try:
            fire_id = raw_data.get('fire_id', '')

            # Get fire details from main database
            conn = sqlite3.connect(self.bitten_db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT f.fire_id, f.mission_id, f.user_id, f.status,
                       s.symbol, s.direction, s.entry_price, s.confidence, s.pattern_type
                FROM fires f
                LEFT JOIN signals s ON f.mission_id = s.signal_id
                WHERE f.fire_id = ?
            """, (fire_id,))

            fire_data = cursor.fetchone()
            if not fire_data:
                logger.warning(f"Fire record not found for {fire_id}")
                conn.close()
                return None

            user_id = fire_data[2]

            # Get user account details
            cursor.execute("""
                SELECT account_login, last_balance, last_equity, broker
                FROM ea_instances
                WHERE user_id = ?
                ORDER BY last_seen DESC
                LIMIT 1
            """, (user_id,))

            account_data = cursor.fetchone()
            conn.close()

            # Get slot information from fire modes database
            slot_info = self.get_slot_info(user_id, fire_id)

            # Build enriched confirmation
            enriched = {
                # Original confirmation data
                'type': 'confirmation',
                'fire_id': fire_id,
                'status': raw_data.get('status', ''),
                'ticket': raw_data.get('ticket', 0),
                'price': raw_data.get('price', 0.0),
                'message': raw_data.get('message', ''),

                # User information
                'user_uuid': user_id,

                # Account enrichment
                'account': {
                    'login': account_data[0] if account_data else 'unknown',
                    'balance': account_data[1] if account_data else 0.0,
                    'equity': account_data[2] if account_data else 0.0,
                    'broker': account_data[3] if account_data else 'unknown'
                } if account_data else {},

                # Slot enrichment
                'slots': slot_info,

                # Trade details
                'trade': {
                    'symbol': fire_data[4] if fire_data[4] else 'unknown',
                    'direction': fire_data[5] if fire_data[5] else 'unknown',
                    'entry_price': fire_data[6] if fire_data[6] else 0.0,
                    'confidence': fire_data[7] if fire_data[7] else 0.0,
                    'pattern_type': fire_data[8] if fire_data[8] else 'unknown'
                },

                # Timestamp
                'enriched_at': int(time.time())
            }

            return enriched

        except Exception as e:
            logger.error(f"Error enriching confirmation: {e}")
            return None

    def get_slot_info(self, user_id: str, fire_id: str) -> Dict:
        """Get slot information for user"""
        try:
            conn = sqlite3.connect(self.fire_modes_db_path)
            cursor = conn.cursor()

            # Get user fire mode settings
            cursor.execute("""
                SELECT current_mode, max_auto_slots, auto_slots_in_use, manual_slots_in_use
                FROM user_fire_modes
                WHERE user_id = ?
            """, (user_id,))

            mode_data = cursor.fetchone()

            # Get slot details for this fire
            cursor.execute("""
                SELECT slot_id, slot_type, status, opened_at
                FROM active_slots
                WHERE user_id = ? AND mission_id LIKE ?
                ORDER BY opened_at DESC
                LIMIT 1
            """, (user_id, f"%{fire_id.split('_')[-3]}%"))  # Extract signal ID from fire_id

            slot_data = cursor.fetchone()

            # Count current open slots
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN slot_type = 'MANUAL' AND status = 'OPEN' THEN 1 END) as manual_open,
                    COUNT(CASE WHEN slot_type = 'AUTO' AND status = 'OPEN' THEN 1 END) as auto_open,
                    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as total_open
                FROM active_slots
                WHERE user_id = ?
            """, (user_id,))

            slot_counts = cursor.fetchone()
            conn.close()

            return {
                'current_mode': mode_data[0] if mode_data else 'MANUAL',
                'limits': {
                    'max_auto': mode_data[1] if mode_data else 0,
                    'auto_in_use': slot_counts[1] if slot_counts else 0,
                    'manual_in_use': slot_counts[0] if slot_counts else 0,
                    'total_in_use': slot_counts[2] if slot_counts else 0
                },
                'this_slot': {
                    'slot_id': slot_data[0] if slot_data else None,
                    'type': slot_data[1] if slot_data else 'MANUAL',
                    'status': slot_data[2] if slot_data else 'UNKNOWN',
                    'opened_at': slot_data[3] if slot_data else None
                } if slot_data else None
            }

        except Exception as e:
            logger.error(f"Error getting slot info: {e}")
            return {}

    def update_fire_record(self, enriched_data: Dict):
        """Update fire record with confirmation details"""
        try:
            conn = sqlite3.connect(self.bitten_db_path)
            cursor = conn.cursor()

            fire_id = enriched_data['fire_id']
            status = enriched_data['status']
            ticket = enriched_data['ticket']
            price = enriched_data['price']

            # Map EA statuses to our database statuses
            status_map = {
                'FILLED': 'FILLED',
                'FAILED': 'FAILED',
                'REJECTED': 'FAILED',
                'ERROR': 'FAILED'
            }
            db_status = status_map.get(status, status)

            cursor.execute("""
                UPDATE fires
                SET status = ?, ticket = ?, price = ?, updated_at = ?
                WHERE fire_id = ?
            """, (db_status, ticket, price, int(time.time()), fire_id))

            conn.commit()
            conn.close()

            logger.info(f"✅ Updated fire record: {fire_id} -> {db_status}")

        except Exception as e:
            logger.error(f"Error updating fire record: {e}")

    def update_slot_status(self, enriched_data: Dict):
        """Update slot status based on confirmation"""
        try:
            conn = sqlite3.connect(self.fire_modes_db_path)
            cursor = conn.cursor()

            fire_id = enriched_data['fire_id']
            status = enriched_data['status']
            user_id = enriched_data['user_uuid']
            ticket = enriched_data['ticket']

            # Extract signal ID from fire_id (format: FIRE_{signal_id}_{user_id}_{timestamp})
            fire_parts = fire_id.split('_')
            if len(fire_parts) >= 4:
                signal_id_part = '_'.join(fire_parts[1:-2])  # Reconstruct signal ID

                if status == 'FILLED' and ticket > 0:
                    # Position opened - mark slot as OPEN and add ticket
                    cursor.execute("""
                        UPDATE active_slots
                        SET status = 'OPEN', ticket = ?, opened_at = ?
                        WHERE user_id = ? AND mission_id LIKE ? AND status = 'ALLOCATED'
                    """, (ticket, int(time.time()), user_id, f"%{signal_id_part}%"))

                    logger.info(f"✅ Slot opened for {fire_id}, ticket {ticket}")

                elif status in ['FAILED', 'REJECTED', 'ERROR']:
                    # Trade failed - release allocated slot
                    cursor.execute("""
                        UPDATE active_slots
                        SET status = 'CLOSED', closed_at = ?
                        WHERE user_id = ? AND mission_id LIKE ? AND status = 'ALLOCATED'
                    """, (int(time.time()), user_id, f"%{signal_id_part}%"))

                    logger.info(f"❌ Slot released for failed fire {fire_id}")

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error updating slot status: {e}")

    def run(self):
        """Run the confirmation enrichment subscriber"""
        logger.info("🚀 Starting Confirmation Enrichment Subscriber...")
        try:
            # Start consuming events
            self.consumer.start()
        except KeyboardInterrupt:
            logger.info("Shutting down confirmation enrichment subscriber...")
        except Exception as e:
            logger.error(f"Fatal error in confirmation enrichment: {e}")
        finally:
            self.consumer.stop()

if __name__ == "__main__":
    subscriber = ConfirmationEnrichmentSubscriber()
    subscriber.run()