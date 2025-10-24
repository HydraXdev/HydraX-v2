#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Nightly Reconciliation Script

Cross-checks PostgreSQL ↔ Firestore data consistency.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import asyncpg
import firebase_admin
from firebase_admin import credentials, firestore
import json
import sys
from datetime import datetime, timedelta


class ReconciliationJob:
    """Nightly PostgreSQL ↔ Firestore reconciliation"""

    def __init__(
        self,
        postgres_dsn: str = "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2",
        firebase_creds: str = "/root/HydraX-v2/firestore/bitten-firebase-sa.json"
    ):
        self.postgres_dsn = postgres_dsn
        self.firebase_creds = firebase_creds
        self.errors = []
        self.warnings = []

    async def run(self) -> Dict:
        """Execute nightly reconciliation"""
        print("🌙 BITTEN v2.0 Nightly Reconciliation")
        print(f"⏰ {datetime.utcnow().isoformat()}")
        print("=" * 70)

        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.firebase_creds)
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        pg_pool = await asyncpg.create_pool(self.postgres_dsn, min_size=2, max_size=5)

        try:
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {}
            }

            # Reconcile last 24 hours
            results["checks"]["signals"] = await self.reconcile_signals(pg_pool, db)
            results["checks"]["outcomes"] = await self.reconcile_outcomes(pg_pool, db)
            results["checks"]["user_stats"] = await self.reconcile_user_stats(pg_pool, db)

            results["errors"] = self.errors
            results["warnings"] = self.warnings
            results["status"] = "PASS" if len(self.errors) == 0 else "FAIL"

        finally:
            await pg_pool.close()

        self.print_summary(results)
        return results

    async def reconcile_signals(self, pg_pool, firestore_db) -> Dict:
        """Reconcile signal counts"""
        print("\n🎯 Reconciling Signals (Last 24h)...")

        yesterday = datetime.utcnow() - timedelta(hours=24)

        async with pg_pool.acquire() as conn:
            pg_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM signals
                WHERE created_at > $1
            """, yesterday)

        # Firestore count
        signals_ref = firestore_db.collection('signals')
        fs_docs = signals_ref.where('created_at', '>', yesterday).stream()
        fs_count = sum(1 for _ in fs_docs)

        match = pg_count == fs_count

        if not match:
            self.warnings.append(
                f"Signal count mismatch: PostgreSQL={pg_count}, Firestore={fs_count}"
            )

        print(f"  PostgreSQL: {pg_count}")
        print(f"  Firestore:  {fs_count}")
        print(f"  {'✅ Match' if match else '⚠️  Mismatch'}")

        return {
            "postgres_count": pg_count,
            "firestore_count": fs_count,
            "match": match,
            "diff": abs(pg_count - fs_count)
        }

    async def reconcile_outcomes(self, pg_pool, firestore_db) -> Dict:
        """Reconcile signal outcomes"""
        print("\n📊 Reconciling Signal Outcomes (Last 24h)...")

        yesterday = datetime.utcnow() - timedelta(hours=24)

        async with pg_pool.acquire() as conn:
            pg_outcomes = await conn.fetch("""
                SELECT outcome, COUNT(*) as count
                FROM signal_outcomes
                WHERE completed_at > $1
                GROUP BY outcome
            """, yesterday)

        pg_stats = {row['outcome']: row['count'] for row in pg_outcomes}

        # Firestore outcomes
        outcomes_ref = firestore_db.collection('signal_outcomes')
        fs_docs = outcomes_ref.where('completed_at', '>', yesterday).stream()

        fs_stats = {}
        for doc in fs_docs:
            data = doc.to_dict()
            outcome = data.get('outcome', 'UNKNOWN')
            fs_stats[outcome] = fs_stats.get(outcome, 0) + 1

        # Compare
        all_outcomes = set(list(pg_stats.keys()) + list(fs_stats.keys()))

        for outcome in all_outcomes:
            pg_val = pg_stats.get(outcome, 0)
            fs_val = fs_stats.get(outcome, 0)

            if pg_val != fs_val:
                self.warnings.append(
                    f"Outcome mismatch for {outcome}: PG={pg_val}, FS={fs_val}"
                )

        print(f"  PostgreSQL: {sum(pg_stats.values())} outcomes")
        print(f"  Firestore:  {sum(fs_stats.values())} outcomes")

        return {
            "postgres": pg_stats,
            "firestore": fs_stats
        }

    async def reconcile_user_stats(self, pg_pool, firestore_db) -> Dict:
        """Reconcile user statistics"""
        print("\n👤 Reconciling User Stats...")

        async with pg_pool.acquire() as conn:
            # Sample 10 random users
            users = await conn.fetch("""
                SELECT DISTINCT user_id
                FROM fires
                ORDER BY RANDOM()
                LIMIT 10
            """)

            mismatches = 0

            for user_row in users:
                user_id = user_row['user_id']

                # PostgreSQL count
                pg_fire_count = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM fires
                    WHERE user_id = $1
                """, user_id)

                # Firestore count
                user_doc = firestore_db.collection('users').document(user_id).get()

                if user_doc.exists:
                    fs_fire_count = user_doc.to_dict().get('total_fires', 0)

                    if pg_fire_count != fs_fire_count:
                        self.warnings.append(
                            f"User {user_id}: PG fires={pg_fire_count}, FS fires={fs_fire_count}"
                        )
                        mismatches += 1

            print(f"  Checked {len(users)} users")
            print(f"  Mismatches: {mismatches}")

            return {
                "users_checked": len(users),
                "mismatches": mismatches
            }

    def print_summary(self, results: Dict):
        """Print reconciliation summary"""
        print("\n" + "=" * 70)
        print("📋 RECONCILIATION SUMMARY")
        print("=" * 70)

        print(f"\nStatus: {results['status']}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Warnings: {len(results['warnings'])}")

        if results['errors']:
            print("\n❌ ERRORS:")
            for error in results['errors']:
                print(f"  - {error}")

        if results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in results['warnings']:
                print(f"  - {warning}")

        print("\n" + "=" * 70)


async def main():
    """Main execution"""
    job = ReconciliationJob()

    try:
        results = await job.run()

        # Save results
        output_file = f"/tmp/reconciliation_{datetime.utcnow().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n📄 Results saved to {output_file}")

        sys.exit(0 if results['status'] == 'PASS' else 1)

    except Exception as e:
        print(f"\n❌ Reconciliation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
