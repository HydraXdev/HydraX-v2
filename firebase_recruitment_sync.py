"""
Firebase Recruitment System Sync
Migrates SQLite referral data to Firestore and handles incremental sync
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirebaseRecruitmentSync:
    """Syncs recruitment data between SQLite and Firestore"""

    def __init__(self, db_path: str = "/root/HydraX-v2/data/referral_system.db"):
        self.db_path = db_path

        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('/root/bitten-firebase-sa.json')
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

        # Collection references
        self.referral_codes_col = self.db.collection('referral_codes')
        self.recruits_col = self.db.collection('recruits')
        self.squad_stats_col = self.db.collection('squad_stats')
        self.referral_rewards_col = self.db.collection('referral_rewards')

    def get_user_callsign(self, user_id: str) -> str:
        """Get user's callsign from their referral code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT code FROM referral_codes WHERE user_id = ? LIMIT 1",
                (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else f"AGENT_{user_id[:6]}"
        finally:
            conn.close()

    def sync_referral_codes(self) -> int:
        """Sync referral codes from SQLite to Firestore"""
        logger.info("Syncing referral codes...")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM referral_codes")
            codes = cursor.fetchall()

            synced = 0
            for row in codes:
                code_data = {
                    'user_id': row['user_id'],
                    'callsign': row['code'],
                    'created_at': firestore.SERVER_TIMESTAMP if not row['created_at'] else datetime.fromisoformat(row['created_at']),
                    'uses_count': row['uses_count'] or 0,
                    'max_uses': row['max_uses'],
                    'is_promo': bool(row['is_promo']),
                    'promo_multiplier': float(row['promo_multiplier'] or 1.0)
                }

                # Use code as document ID for easy lookup
                self.referral_codes_col.document(row['code']).set(code_data, merge=True)
                synced += 1

            logger.info(f"✅ Synced {synced} referral codes")
            return synced

        finally:
            conn.close()

    def sync_recruits(self) -> int:
        """Sync recruits from SQLite to Firestore"""
        logger.info("Syncing recruits...")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM recruits")
            recruits = cursor.fetchall()

            synced = 0
            for row in recruits:
                # Get callsign for this recruit
                callsign = self.get_user_callsign(row['recruit_id'])

                recruit_data = {
                    'referrer_id': row['referrer_id'],
                    'referral_code': row['referral_code'],
                    'callsign': callsign,
                    'joined_at': datetime.fromisoformat(row['joined_at']) if row['joined_at'] else firestore.SERVER_TIMESTAMP,
                    'tier': 'DIRECT' if row['tier'] == 1 else 'SECONDARY' if row['tier'] == 2 else 'TERTIARY',
                    'total_xp_earned': row['total_xp_earned'] or 0,
                    'trades_completed': row['trades_completed'] or 0,
                    'current_rank': row['current_rank'] or 'NIBBLER',
                    'is_active': bool(row['is_active']),
                    'last_activity': datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None
                }

                # Use recruit_id as document ID
                self.recruits_col.document(row['recruit_id']).set(recruit_data, merge=True)
                synced += 1

            logger.info(f"✅ Synced {synced} recruits")
            return synced

        finally:
            conn.close()

    def sync_squad_stats(self) -> int:
        """Sync squad stats from SQLite to Firestore"""
        logger.info("Syncing squad stats...")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM squad_stats")
            stats = cursor.fetchall()

            synced = 0
            for row in stats:
                # Get callsign for this user
                callsign = self.get_user_callsign(row['user_id'])

                stats_data = {
                    'callsign': callsign,
                    'referral_code': row['referral_code'] or callsign,
                    'total_recruits': row['total_recruits'] or 0,
                    'active_recruits': row['active_recruits'] or 0,
                    'total_xp_from_recruits': row['total_xp_earned'] or 0,
                    'squad_rank': row['squad_rank'] or 'LONE_WOLF',
                    'last_recruit_at': datetime.fromisoformat(row['last_recruit_at']) if row['last_recruit_at'] else None,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }

                # Use user_id as document ID
                self.squad_stats_col.document(row['user_id']).set(stats_data, merge=True)
                synced += 1

            logger.info(f"✅ Synced {synced} squad stats")
            return synced

        finally:
            conn.close()

    def sync_referral_rewards(self) -> int:
        """Sync referral rewards from SQLite to Firestore"""
        logger.info("Syncing referral rewards...")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM referral_rewards")
            rewards = cursor.fetchall()

            synced = 0
            for row in rewards:
                reward_data = {
                    'referrer_id': row['referrer_id'],
                    'recruit_id': row['recruit_id'],
                    'reward_type': row['reward_type'],
                    'xp_amount': row['xp_amount'] or 0,
                    'multiplier': float(row['multiplier'] or 1.0),
                    'timestamp': datetime.fromisoformat(row['timestamp']) if row['timestamp'] else firestore.SERVER_TIMESTAMP
                }

                # Auto-generate document ID
                self.referral_rewards_col.add(reward_data)
                synced += 1

            logger.info(f"✅ Synced {synced} referral rewards")
            return synced

        finally:
            conn.close()

    def full_sync(self) -> Dict[str, int]:
        """Perform full sync of all data"""
        logger.info("🚀 Starting full Firebase sync...")

        results = {
            'referral_codes': self.sync_referral_codes(),
            'recruits': self.sync_recruits(),
            'squad_stats': self.sync_squad_stats(),
            'referral_rewards': self.sync_referral_rewards()
        }

        logger.info(f"✅ Full sync complete: {results}")
        return results

    def incremental_sync(self, since_timestamp: Optional[datetime] = None) -> Dict[str, int]:
        """Sync only records updated since timestamp"""
        if not since_timestamp:
            # Default to last 24 hours
            from datetime import timedelta
            since_timestamp = datetime.now() - timedelta(hours=24)

        logger.info(f"🔄 Incremental sync since {since_timestamp}")

        # For now, just do full sync (can optimize later)
        return self.full_sync()

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top recruiters from Firestore"""
        results = (
            self.squad_stats_col
            .order_by('total_xp_from_recruits', direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        leaderboard = []
        rank = 1
        for doc in results:
            data = doc.to_dict()
            data['user_id'] = doc.id
            data['rank'] = rank
            leaderboard.append(data)
            rank += 1

        return leaderboard

    def get_user_squad_stats(self, user_id: str) -> Optional[Dict]:
        """Get squad stats for a specific user"""
        doc = self.squad_stats_col.document(user_id).get()

        if doc.exists:
            data = doc.to_dict()
            data['user_id'] = doc.id
            return data

        return None

    def get_user_recruits(self, user_id: str) -> List[Dict]:
        """Get all recruits for a specific user"""
        results = (
            self.recruits_col
            .where(filter=FieldFilter('referrer_id', '==', user_id))
            .stream()
        )

        recruits = []
        for doc in results:
            data = doc.to_dict()
            data['recruit_id'] = doc.id
            recruits.append(data)

        return recruits


def main():
    """Main execution for migration"""
    sync = FirebaseRecruitmentSync()

    print("=" * 70)
    print("🔥 Firebase Recruitment System Migration")
    print("=" * 70)

    results = sync.full_sync()

    print("\n📊 Migration Results:")
    print(f"  Referral Codes:   {results['referral_codes']}")
    print(f"  Recruits:         {results['recruits']}")
    print(f"  Squad Stats:      {results['squad_stats']}")
    print(f"  Referral Rewards: {results['referral_rewards']}")
    print("\n✅ Migration complete!")

    # Test leaderboard query
    print("\n🏆 Top 5 Recruiters:")
    leaderboard = sync.get_leaderboard(limit=5)
    for i, entry in enumerate(leaderboard, 1):
        print(f"  {i}. {entry.get('callsign', 'Unknown')} - {entry['total_recruits']} recruits, {entry['total_xp_from_recruits']} XP")


if __name__ == "__main__":
    main()
