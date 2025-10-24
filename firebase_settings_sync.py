#!/usr/bin/env python3
"""
Firebase Settings Sync Service
Syncs user_settings from Firebase Firestore to backend fire_modes.db
Allows frontend UI changes to control backend autofire behavior
"""

import os
import sys
import time
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("ERROR: firebase-admin not installed. Run: pip install firebase-admin")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class FirebaseSettingsSync:
    """Syncs Firebase user_settings to backend fire_modes.db"""

    def __init__(self, service_account_path: str = None):
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            # Try to find service account JSON
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
            else:
                # Try common locations
                possible_paths = [
                    '/root/bitten-firebase-sa.json',
                    '/root/HydraX-v2/bitten-firebase-sa.json',
                    '/root/firebase-service-account.json'
                ]
                cred = None
                for path in possible_paths:
                    if os.path.exists(path):
                        cred = credentials.Certificate(path)
                        logger.info(f"Found service account at: {path}")
                        break

                if not cred:
                    logger.error("ERROR: Firebase service account JSON not found")
                    logger.error("Please create one at: /root/bitten-firebase-sa.json")
                    logger.error("OR set GOOGLE_APPLICATION_CREDENTIALS environment variable")
                    sys.exit(1)

            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.backend_db_path = '/root/HydraX-v2/data/fire_modes.db'

        logger.info("✅ Firebase Settings Sync initialized")

    def sync_user_settings(self, firebase_uid: str) -> bool:
        """Sync settings for one user from Firebase to backend database"""
        try:
            # Get Firebase user_settings document
            doc_ref = self.db.collection('user_settings').document(firebase_uid)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"No settings found in Firebase for UID: {firebase_uid}")
                return False

            settings = doc.to_dict()

            # Get Firebase autofire_settings document
            autofire_ref = self.db.collection('autofire_settings').document(firebase_uid)
            autofire_doc = autofire_ref.get()
            autofire_settings = autofire_doc.to_dict() if autofire_doc.exists else {}

            # Use Firebase UID directly as user_id (no more Telegram ID mapping)
            user_id = firebase_uid

            # Update backend database
            conn = sqlite3.connect(self.backend_db_path)
            cursor = conn.cursor()

            # Map fire mode settings
            fire_mode_map = {
                'safe': 'SELECT',      # SAFE mode = no autofire
                'semi': 'SEMI_AUTO',   # SEMI mode = manual approval
                'full_auto': 'AUTO'    # FULL_AUTO mode = autofire
            }

            firebase_mode = settings.get('fireMode', 'semi')
            backend_mode = fire_mode_map.get(firebase_mode, 'SEMI_AUTO')

            # Get risk percentage (default 2%)
            risk_pct = settings.get('riskPct', 2.0) / 100.0  # Convert 2 → 0.02

            # Get trailing stop (default False)
            trailing_stop = settings.get('trailingStop', False)

            # Get autofire risk mode (MODERATE = 0.5x, AGGRESSIVE = 1.0x)
            risk_mode = autofire_settings.get('riskMode', 'MODERATE')
            autofire_risk_multiplier = 0.5 if risk_mode == 'MODERATE' else 1.0

            # Get confidence range
            confidence_min = autofire_settings.get('confidenceMin', 80)
            confidence_max = autofire_settings.get('confidenceMax', 89)

            # Get auto slots
            auto_slots = autofire_settings.get('autoSlots', 3)

            # Update or insert user settings
            cursor.execute("""
                INSERT INTO user_fire_modes (
                    user_id,
                    current_mode,
                    risk_per_trade,
                    auto_fire_enabled,
                    auto_fire_min_confidence,
                    auto_fire_max_confidence,
                    max_auto_slots,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    current_mode = excluded.current_mode,
                    risk_per_trade = excluded.risk_per_trade,
                    auto_fire_enabled = excluded.auto_fire_enabled,
                    auto_fire_min_confidence = excluded.auto_fire_min_confidence,
                    auto_fire_max_confidence = excluded.auto_fire_max_confidence,
                    max_auto_slots = excluded.max_auto_slots,
                    updated_at = excluded.updated_at
            """, (
                user_id,  # Firebase UID
                backend_mode,
                risk_pct * autofire_risk_multiplier,  # Apply multiplier here
                1 if backend_mode == 'AUTO' else 0,
                confidence_min,
                confidence_max,
                auto_slots,
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            logger.info(f"✅ Synced settings for user {user_id}:")
            logger.info(f"   Firebase Mode: {firebase_mode} → Backend Mode: {backend_mode}")
            logger.info(f"   Manual Risk: {risk_pct * 100}%")
            logger.info(f"   Autofire Risk Mode: {risk_mode} ({autofire_risk_multiplier}x)")
            logger.info(f"   Effective Autofire Risk: {risk_pct * autofire_risk_multiplier * 100}%")
            logger.info(f"   Confidence Range: {confidence_min}-{confidence_max}%")
            logger.info(f"   Auto Slots: {auto_slots}")
            logger.info(f"   Trailing Stop: {trailing_stop}")

            return True

        except Exception as e:
            logger.error(f"Error syncing settings for {firebase_uid}: {e}")
            return False

    def resolve_firebase_uid_to_telegram_id(self, firebase_uid: str) -> Optional[str]:
        """Map Firebase UID to Telegram ID using user_uuid_mapping table"""
        try:
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT telegram_id FROM user_uuid_mapping
                WHERE firebase_uid = ?
            """, (firebase_uid,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0]
            else:
                logger.warning(f"No mapping found for Firebase UID: {firebase_uid}")
                return None

        except Exception as e:
            logger.error(f"Error resolving Firebase UID: {e}")
            return None

    def watch_all_users(self, poll_interval: int = 30):
        """Watch all users' settings and sync on changes"""
        logger.info(f"👁️  Starting settings watch (poll every {poll_interval}s)")

        # Keep track of last known states for both collections
        last_user_settings = {}
        last_autofire_settings = {}

        while True:
            try:
                # Get all user_settings documents
                settings_ref = self.db.collection('user_settings')
                docs = settings_ref.stream()

                changed_users = set()

                for doc in docs:
                    firebase_uid = doc.id
                    current_state = doc.to_dict()

                    # Check if changed
                    if firebase_uid not in last_user_settings or last_user_settings[firebase_uid] != current_state:
                        logger.info(f"🔄 User settings changed for {firebase_uid}")
                        last_user_settings[firebase_uid] = current_state
                        changed_users.add(firebase_uid)

                # Get all autofire_settings documents
                autofire_ref = self.db.collection('autofire_settings')
                autofire_docs = autofire_ref.stream()

                for doc in autofire_docs:
                    firebase_uid = doc.id
                    current_state = doc.to_dict()

                    # Check if changed
                    if firebase_uid not in last_autofire_settings or last_autofire_settings[firebase_uid] != current_state:
                        logger.info(f"🔄 Autofire settings changed for {firebase_uid}")
                        last_autofire_settings[firebase_uid] = current_state
                        changed_users.add(firebase_uid)

                # Sync all users with changed settings
                for firebase_uid in changed_users:
                    self.sync_user_settings(firebase_uid)

                time.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("⏹️  Stopping settings sync...")
                break
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                time.sleep(5)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Sync Firebase settings to backend')
    parser.add_argument('--service-account', help='Path to Firebase service account JSON')
    parser.add_argument('--uid', help='Sync specific Firebase UID (one-time sync)')
    parser.add_argument('--watch', action='store_true', help='Watch all users continuously')
    parser.add_argument('--poll-interval', type=int, default=30, help='Poll interval in seconds (default: 30)')

    args = parser.parse_args()

    sync = FirebaseSettingsSync(service_account_path=args.service_account)

    if args.uid:
        # One-time sync
        success = sync.sync_user_settings(args.uid)
        sys.exit(0 if success else 1)
    elif args.watch:
        # Continuous watch
        sync.watch_all_users(poll_interval=args.poll_interval)
    else:
        print("ERROR: Must specify --uid or --watch")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
