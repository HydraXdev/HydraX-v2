"""
Firestore Mirror Job
Mirrors PostgreSQL data to Firestore for real-time web access
"""
import logging
import time
from typing import Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor
import firebase_admin
from firebase_admin import credentials, firestore

from ..config import (
    DATABASE_URL,
    FIREBASE_CREDENTIALS_PATH,
    FIRESTORE_CONFIG,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS
)

logger = logging.getLogger(__name__)


class FirestoreMirror:
    """Mirrors PostgreSQL data to Firestore"""

    def __init__(self):
        self.db = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()
            logger.info("Firebase initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")
            raise

    def _get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def _mirror_users(self):
        """Mirror user data to Firestore"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, balance, equity, tier, fire_mode,
                       bitmode_enabled, wins, losses, win_rate, total_pips,
                       updated_at
                FROM users
                WHERE updated_at > %s
                ORDER BY updated_at DESC
                LIMIT %s
            """, (
                int(time.time()) - 7200,  # Last 2 hours
                FIRESTORE_CONFIG['batch_size']
            ))

            users = cursor.fetchall()
            cursor.close()
            conn.close()

            if not users:
                logger.info("No users to mirror")
                return

            # Batch write to Firestore
            batch = self.db.batch()
            batch_count = 0

            for user in users:
                user_ref = self.db.collection(
                    FIRESTORE_CONFIG['collections']['users']
                ).document(user['user_id'])

                user_data = {
                    'balance': float(user['balance'] or 0),
                    'equity': float(user['equity'] or 0),
                    'tier': user['tier'] or 'RECRUIT',
                    'fire_mode': user['fire_mode'] or 'MANUAL',
                    'bitmode_enabled': bool(user['bitmode_enabled']),
                    'wins': int(user['wins'] or 0),
                    'losses': int(user['losses'] or 0),
                    'win_rate': float(user['win_rate'] or 0),
                    'total_pips': float(user['total_pips'] or 0),
                    'last_updated': firestore.SERVER_TIMESTAMP
                }

                batch.set(user_ref, user_data, merge=True)
                batch_count += 1

                # Commit batch every 500 writes
                if batch_count >= FIRESTORE_CONFIG['batch_size']:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0

            # Commit remaining
            if batch_count > 0:
                batch.commit()

            logger.info(f"Mirrored {len(users)} users to Firestore")

        except Exception as e:
            logger.error(f"Error mirroring users: {e}")

    def _mirror_signals(self):
        """Mirror active signals to Firestore"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT signal_id, symbol, direction, entry_price,
                       sl_price, tp_price, confidence, pattern_type,
                       signal_type, created_at, expires_at, status
                FROM signals
                WHERE status = 'ACTIVE'
                  AND created_at > %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (
                int(time.time()) - 86400,  # Last 24 hours
                FIRESTORE_CONFIG['batch_size']
            ))

            signals = cursor.fetchall()
            cursor.close()
            conn.close()

            if not signals:
                logger.info("No signals to mirror")
                return

            # Batch write
            batch = self.db.batch()
            batch_count = 0

            for signal in signals:
                signal_ref = self.db.collection(
                    FIRESTORE_CONFIG['collections']['signals']
                ).document(signal['signal_id'])

                signal_data = {
                    'symbol': signal['symbol'],
                    'direction': signal['direction'],
                    'entry_price': float(signal['entry_price'] or 0),
                    'sl_price': float(signal['sl_price'] or 0),
                    'tp_price': float(signal['tp_price'] or 0),
                    'confidence': float(signal['confidence'] or 0),
                    'pattern_type': signal['pattern_type'] or '',
                    'signal_type': signal['signal_type'] or '',
                    'status': signal['status'] or 'ACTIVE',
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'expires_at': int(signal['expires_at'] or 0)
                }

                batch.set(signal_ref, signal_data, merge=True)
                batch_count += 1

                if batch_count >= FIRESTORE_CONFIG['batch_size']:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0

            if batch_count > 0:
                batch.commit()

            logger.info(f"Mirrored {len(signals)} signals to Firestore")

        except Exception as e:
            logger.error(f"Error mirroring signals: {e}")

    def _mirror_positions(self):
        """Mirror open positions to Firestore"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT position_id, user_id, symbol, ticket, status,
                       open_price, current_price, profit, lot_size,
                       created_at
                FROM positions
                WHERE status = 'OPEN'
                ORDER BY created_at DESC
                LIMIT %s
            """, (FIRESTORE_CONFIG['batch_size'],))

            positions = cursor.fetchall()
            cursor.close()
            conn.close()

            if not positions:
                logger.info("No positions to mirror")
                return

            # Batch write
            batch = self.db.batch()
            batch_count = 0

            for position in positions:
                position_ref = self.db.collection(
                    FIRESTORE_CONFIG['collections']['positions']
                ).document(str(position['position_id']))

                position_data = {
                    'user_id': position['user_id'],
                    'symbol': position['symbol'],
                    'ticket': int(position['ticket'] or 0),
                    'status': position['status'] or 'OPEN',
                    'open_price': float(position['open_price'] or 0),
                    'current_price': float(position['current_price'] or 0),
                    'profit': float(position['profit'] or 0),
                    'lot_size': float(position['lot_size'] or 0),
                    'created_at': firestore.SERVER_TIMESTAMP
                }

                batch.set(position_ref, position_data, merge=True)
                batch_count += 1

                if batch_count >= FIRESTORE_CONFIG['batch_size']:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0

            if batch_count > 0:
                batch.commit()

            logger.info(f"Mirrored {len(positions)} positions to Firestore")

        except Exception as e:
            logger.error(f"Error mirroring positions: {e}")

    def run(self):
        """Run Firestore mirror job"""
        logger.info("Running Firestore Mirror...")

        try:
            self._mirror_users()
            self._mirror_signals()
            self._mirror_positions()

            logger.info("Firestore mirror complete")

        except Exception as e:
            logger.error(f"Error in Firestore mirror: {e}")


# Job entry point
def run_firestore_mirror():
    """Run Firestore mirror job"""
    mirror = FirestoreMirror()
    mirror.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_firestore_mirror()
