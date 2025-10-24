"""
Reconciliation Job
Compares PostgreSQL vs Firestore data and reports discrepancies
"""
import logging
import time
from typing import Dict, List, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
import firebase_admin
from firebase_admin import credentials, firestore

from ..config import (
    DATABASE_URL,
    FIREBASE_CREDENTIALS_PATH,
    FIRESTORE_CONFIG
)

logger = logging.getLogger(__name__)


class Reconciliation:
    """Reconciles PostgreSQL and Firestore data"""

    def __init__(self):
        self.db = None
        self._initialize_firebase()
        self.discrepancies = []

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()
            logger.info("Firebase initialized for reconciliation")

        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")
            raise

    def _get_db_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    def _reconcile_users(self) -> Tuple[int, int, int]:
        """Reconcile user data between PostgreSQL and Firestore"""
        try:
            # Get PostgreSQL users
            conn = self._get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, balance, equity, tier, fire_mode, bitmode_enabled
                FROM users
                WHERE updated_at > %s
            """, (int(time.time()) - 86400,))  # Last 24 hours

            pg_users = {u['user_id']: dict(u) for u in cursor.fetchall()}
            cursor.close()
            conn.close()

            # Get Firestore users
            fs_users_ref = self.db.collection(FIRESTORE_CONFIG['collections']['users'])
            fs_users = {}

            for user_id in pg_users.keys():
                doc = fs_users_ref.document(user_id).get()
                if doc.exists:
                    fs_users[user_id] = doc.to_dict()

            # Compare
            missing_in_fs = 0
            mismatched = 0
            corrected = 0

            for user_id, pg_data in pg_users.items():
                if user_id not in fs_users:
                    # Missing in Firestore
                    missing_in_fs += 1
                    self.discrepancies.append({
                        'type': 'user',
                        'issue': 'missing_in_firestore',
                        'user_id': user_id
                    })

                    # Auto-correct: Create in Firestore
                    try:
                        fs_users_ref.document(user_id).set({
                            'balance': float(pg_data['balance'] or 0),
                            'equity': float(pg_data['equity'] or 0),
                            'tier': pg_data['tier'] or 'RECRUIT',
                            'fire_mode': pg_data['fire_mode'] or 'MANUAL',
                            'bitmode_enabled': bool(pg_data['bitmode_enabled']),
                            'last_updated': firestore.SERVER_TIMESTAMP
                        })
                        corrected += 1
                        logger.info(f"Created missing user {user_id} in Firestore")
                    except Exception as e:
                        logger.error(f"Failed to create user {user_id}: {e}")

                else:
                    # Check for mismatches
                    fs_data = fs_users[user_id]

                    # Compare critical fields
                    if (abs(float(fs_data.get('balance', 0)) - float(pg_data['balance'] or 0)) > 0.01 or
                        fs_data.get('tier') != pg_data['tier'] or
                        fs_data.get('fire_mode') != pg_data['fire_mode']):

                        mismatched += 1
                        self.discrepancies.append({
                            'type': 'user',
                            'issue': 'data_mismatch',
                            'user_id': user_id,
                            'pg_balance': pg_data['balance'],
                            'fs_balance': fs_data.get('balance')
                        })

                        # Auto-correct: Update Firestore
                        try:
                            fs_users_ref.document(user_id).update({
                                'balance': float(pg_data['balance'] or 0),
                                'equity': float(pg_data['equity'] or 0),
                                'tier': pg_data['tier'] or 'RECRUIT',
                                'fire_mode': pg_data['fire_mode'] or 'MANUAL',
                                'last_updated': firestore.SERVER_TIMESTAMP
                            })
                            corrected += 1
                            logger.info(f"Corrected user {user_id} data in Firestore")
                        except Exception as e:
                            logger.error(f"Failed to correct user {user_id}: {e}")

            logger.info(
                f"User reconciliation: {missing_in_fs} missing, "
                f"{mismatched} mismatched, {corrected} corrected"
            )

            return missing_in_fs, mismatched, corrected

        except Exception as e:
            logger.error(f"Error reconciling users: {e}")
            return 0, 0, 0

    def _reconcile_signals(self) -> Tuple[int, int, int]:
        """Reconcile signal data"""
        try:
            # Get PostgreSQL signals
            conn = self._get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT signal_id, symbol, direction, confidence, status
                FROM signals
                WHERE status = 'ACTIVE'
                  AND created_at > %s
            """, (int(time.time()) - 86400,))

            pg_signals = {s['signal_id']: dict(s) for s in cursor.fetchall()}
            cursor.close()
            conn.close()

            # Get Firestore signals
            fs_signals_ref = self.db.collection(FIRESTORE_CONFIG['collections']['signals'])
            fs_signals = {}

            for signal_id in pg_signals.keys():
                doc = fs_signals_ref.document(signal_id).get()
                if doc.exists:
                    fs_signals[signal_id] = doc.to_dict()

            # Compare
            missing_in_fs = 0
            mismatched = 0
            corrected = 0

            for signal_id, pg_data in pg_signals.items():
                if signal_id not in fs_signals:
                    missing_in_fs += 1
                    self.discrepancies.append({
                        'type': 'signal',
                        'issue': 'missing_in_firestore',
                        'signal_id': signal_id
                    })

                    # Auto-correct: Create in Firestore
                    try:
                        fs_signals_ref.document(signal_id).set({
                            'symbol': pg_data['symbol'],
                            'direction': pg_data['direction'],
                            'confidence': float(pg_data['confidence'] or 0),
                            'status': pg_data['status'],
                            'created_at': firestore.SERVER_TIMESTAMP
                        })
                        corrected += 1
                        logger.info(f"Created missing signal {signal_id} in Firestore")
                    except Exception as e:
                        logger.error(f"Failed to create signal {signal_id}: {e}")

                else:
                    # Check status mismatch
                    fs_data = fs_signals[signal_id]
                    if fs_data.get('status') != pg_data['status']:
                        mismatched += 1

                        # Auto-correct
                        try:
                            fs_signals_ref.document(signal_id).update({
                                'status': pg_data['status']
                            })
                            corrected += 1
                        except Exception as e:
                            logger.error(f"Failed to update signal {signal_id}: {e}")

            logger.info(
                f"Signal reconciliation: {missing_in_fs} missing, "
                f"{mismatched} mismatched, {corrected} corrected"
            )

            return missing_in_fs, mismatched, corrected

        except Exception as e:
            logger.error(f"Error reconciling signals: {e}")
            return 0, 0, 0

    def _save_reconciliation_report(self):
        """Save reconciliation report to PostgreSQL"""
        try:
            if not self.discrepancies:
                logger.info("No discrepancies to report")
                return

            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Save discrepancies
            for disc in self.discrepancies:
                cursor.execute("""
                    INSERT INTO reconciliation_reports
                    (report_type, issue_type, details, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    disc.get('type', 'unknown'),
                    disc.get('issue', 'unknown'),
                    str(disc),
                    int(time.time())
                ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Saved {len(self.discrepancies)} discrepancies to report")

        except Exception as e:
            logger.error(f"Error saving reconciliation report: {e}")

    def run(self):
        """Run reconciliation job"""
        logger.info("Running Nightly Reconciliation...")

        try:
            total_missing = 0
            total_mismatched = 0
            total_corrected = 0

            # Reconcile users
            missing, mismatched, corrected = self._reconcile_users()
            total_missing += missing
            total_mismatched += mismatched
            total_corrected += corrected

            # Reconcile signals
            missing, mismatched, corrected = self._reconcile_signals()
            total_missing += missing
            total_mismatched += mismatched
            total_corrected += corrected

            # Save report
            self._save_reconciliation_report()

            logger.info(
                f"Reconciliation complete: "
                f"{total_missing} missing, {total_mismatched} mismatched, "
                f"{total_corrected} auto-corrected"
            )

            # Alert on critical issues
            if total_missing > 100 or total_mismatched > 100:
                logger.warning(
                    f"CRITICAL: High discrepancy count detected! "
                    f"Missing: {total_missing}, Mismatched: {total_mismatched}"
                )

        except Exception as e:
            logger.error(f"Error in reconciliation: {e}")


# Job entry point
def run_reconciliation():
    """Run reconciliation job"""
    reconciliation = Reconciliation()
    reconciliation.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_reconciliation()
