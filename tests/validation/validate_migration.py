#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Migration Validation Script

Validates SQLite → PostgreSQL migration completeness and data integrity.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import sys
import sqlite3
import asyncpg
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime
import json


class MigrationValidator:
    """Validates v1 → v2 migration data integrity"""

    def __init__(
        self,
        sqlite_path: str = "/root/HydraX-v2/bitten.db",
        postgres_dsn: str = "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"
    ):
        self.sqlite_path = sqlite_path
        self.postgres_dsn = postgres_dsn
        self.errors = []
        self.warnings = []

    async def validate_all(self) -> Dict:
        """Run all validation checks"""
        print("🔍 BITTEN v2.0 Migration Validation")
        print("=" * 70)

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "sqlite_path": self.sqlite_path,
            "postgres_dsn": self.postgres_dsn,
            "checks": {}
        }

        # Connect to both databases
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        pg_pool = await asyncpg.create_pool(self.postgres_dsn, min_size=2, max_size=5)

        try:
            # Run validation checks
            results["checks"]["row_counts"] = await self.validate_row_counts(sqlite_conn, pg_pool)
            results["checks"]["signals"] = await self.validate_signals(sqlite_conn, pg_pool)
            results["checks"]["fires"] = await self.validate_fires(sqlite_conn, pg_pool)
            results["checks"]["positions"] = await self.validate_positions(sqlite_conn, pg_pool)
            results["checks"]["ea_instances"] = await self.validate_ea_instances(sqlite_conn, pg_pool)
            results["checks"]["data_integrity"] = await self.validate_data_integrity(sqlite_conn, pg_pool)

            # Overall status
            results["errors"] = self.errors
            results["warnings"] = self.warnings
            results["status"] = "PASS" if len(self.errors) == 0 else "FAIL"

        finally:
            sqlite_conn.close()
            await pg_pool.close()

        return results

    async def validate_row_counts(self, sqlite_conn, pg_pool) -> Dict:
        """Compare row counts between v1 and v2"""
        print("\n📊 Validating Row Counts...")

        tables = ["signals", "fires", "positions", "ea_instances"]
        results = {}

        for table in tables:
            # SQLite count
            cursor = sqlite_conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = cursor.fetchone()[0]

            # PostgreSQL count
            async with pg_pool.acquire() as conn:
                pg_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")

            match = sqlite_count == pg_count
            results[table] = {
                "v1_count": sqlite_count,
                "v2_count": pg_count,
                "match": match,
                "diff": pg_count - sqlite_count
            }

            status = "✅" if match else "❌"
            print(f"  {status} {table}: v1={sqlite_count}, v2={pg_count}")

            if not match:
                self.errors.append(f"{table}: Row count mismatch (v1={sqlite_count}, v2={pg_count})")

        return results

    async def validate_signals(self, sqlite_conn, pg_pool) -> Dict:
        """Validate signal data integrity"""
        print("\n🎯 Validating Signals...")

        results = {"checks": []}

        # Sample 100 random signals
        cursor = sqlite_conn.cursor()
        cursor.execute("""
            SELECT signal_id, symbol, direction, confidence, pattern_type, created_at
            FROM signals
            ORDER BY RANDOM()
            LIMIT 100
        """)

        v1_signals = cursor.fetchall()

        async with pg_pool.acquire() as conn:
            for v1_signal in v1_signals:
                signal_id = v1_signal[0]

                # Fetch from v2
                v2_signal = await conn.fetchrow(
                    "SELECT signal_id, symbol, direction, confidence, pattern_type, created_at FROM signals WHERE signal_id = $1",
                    signal_id
                )

                if not v2_signal:
                    self.errors.append(f"Signal {signal_id} missing in v2")
                    results["checks"].append({
                        "signal_id": signal_id,
                        "status": "missing",
                        "error": "Not found in v2"
                    })
                    continue

                # Validate fields
                checks = {
                    "signal_id": v1_signal[0] == v2_signal["signal_id"],
                    "symbol": v1_signal[1] == v2_signal["symbol"],
                    "direction": v1_signal[2] == v2_signal["direction"],
                    "confidence": abs(v1_signal[3] - v2_signal["confidence"]) < 0.01,
                    "pattern_type": v1_signal[4] == v2_signal["pattern_type"]
                }

                all_match = all(checks.values())

                if not all_match:
                    self.errors.append(f"Signal {signal_id}: Field mismatch")

                results["checks"].append({
                    "signal_id": signal_id,
                    "status": "match" if all_match else "mismatch",
                    "checks": checks
                })

        print(f"  ✅ Validated {len(v1_signals)} signals")
        return results

    async def validate_fires(self, sqlite_conn, pg_pool) -> Dict:
        """Validate fire command data"""
        print("\n🔥 Validating Fires...")

        results = {"checks": []}

        cursor = sqlite_conn.cursor()
        cursor.execute("""
            SELECT fire_id, symbol, direction, status, ticket
            FROM fires
            ORDER BY RANDOM()
            LIMIT 100
        """)

        v1_fires = cursor.fetchall()

        async with pg_pool.acquire() as conn:
            for v1_fire in v1_fires:
                fire_id = v1_fire[0]

                v2_fire = await conn.fetchrow(
                    "SELECT fire_id, symbol, direction, status, ticket FROM fires WHERE fire_id = $1",
                    fire_id
                )

                if not v2_fire:
                    self.errors.append(f"Fire {fire_id} missing in v2")
                    continue

                # Validate critical fields
                status_match = v1_fire[3] == v2_fire["status"]
                ticket_match = (v1_fire[4] is None and v2_fire["ticket"] is None) or (v1_fire[4] == v2_fire["ticket"])

                if not (status_match and ticket_match):
                    self.errors.append(f"Fire {fire_id}: Data mismatch")

                results["checks"].append({
                    "fire_id": fire_id,
                    "status_match": status_match,
                    "ticket_match": ticket_match
                })

        print(f"  ✅ Validated {len(v1_fires)} fires")
        return results

    async def validate_positions(self, sqlite_conn, pg_pool) -> Dict:
        """Validate position tracking data"""
        print("\n📈 Validating Positions...")

        results = {"open_positions": 0, "closed_positions": 0}

        async with pg_pool.acquire() as conn:
            # Count open vs closed
            open_count = await conn.fetchval("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
            closed_count = await conn.fetchval("SELECT COUNT(*) FROM positions WHERE status = 'CLOSED'")

            results["open_positions"] = open_count
            results["closed_positions"] = closed_count

            # Validate critical constraint: ticket must be unique
            duplicate_tickets = await conn.fetch("""
                SELECT ticket, COUNT(*) as count
                FROM positions
                WHERE ticket IS NOT NULL
                GROUP BY ticket
                HAVING COUNT(*) > 1
            """)

            if duplicate_tickets:
                for row in duplicate_tickets:
                    self.errors.append(f"Duplicate ticket in positions: {row['ticket']} ({row['count']} times)")

        print(f"  ✅ Open: {open_count}, Closed: {closed_count}")
        return results

    async def validate_ea_instances(self, sqlite_conn, pg_pool) -> Dict:
        """Validate EA instance tracking"""
        print("\n🤖 Validating EA Instances...")

        results = {}

        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT target_uuid, user_id FROM ea_instances")
        v1_eas = cursor.fetchall()

        async with pg_pool.acquire() as conn:
            for target_uuid, user_id in v1_eas:
                v2_ea = await conn.fetchrow(
                    "SELECT target_uuid, user_id FROM ea_instances WHERE target_uuid = $1",
                    target_uuid
                )

                if not v2_ea:
                    self.warnings.append(f"EA {target_uuid} missing in v2 (may be intentional)")
                elif v2_ea["user_id"] != user_id:
                    self.errors.append(f"EA {target_uuid}: user_id mismatch")

        print(f"  ✅ Validated {len(v1_eas)} EA instances")
        return results

    async def validate_data_integrity(self, sqlite_conn, pg_pool) -> Dict:
        """Validate data integrity constraints"""
        print("\n🔒 Validating Data Integrity...")

        results = {"constraints": []}

        async with pg_pool.acquire() as conn:
            # Check for orphaned fires (no signal)
            orphaned_fires = await conn.fetchval("""
                SELECT COUNT(*)
                FROM fires f
                LEFT JOIN signals s ON f.fire_id LIKE '%' || s.signal_id || '%'
                WHERE s.signal_id IS NULL
            """)

            if orphaned_fires > 0:
                self.warnings.append(f"{orphaned_fires} fires have no matching signal")

            results["constraints"].append({
                "check": "orphaned_fires",
                "count": orphaned_fires,
                "status": "ok" if orphaned_fires == 0 else "warning"
            })

            # Check for invalid confidence values
            invalid_confidence = await conn.fetchval("""
                SELECT COUNT(*)
                FROM signals
                WHERE confidence < 0 OR confidence > 100
            """)

            if invalid_confidence > 0:
                self.errors.append(f"{invalid_confidence} signals have invalid confidence values")

            results["constraints"].append({
                "check": "invalid_confidence",
                "count": invalid_confidence,
                "status": "ok" if invalid_confidence == 0 else "error"
            })

        print(f"  ✅ Integrity checks complete")
        return results

    def print_summary(self, results: Dict):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("📋 MIGRATION VALIDATION SUMMARY")
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

        if results['status'] == 'PASS':
            print("\n✅ MIGRATION VALIDATION PASSED")
        else:
            print("\n❌ MIGRATION VALIDATION FAILED")

        print("=" * 70)


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Validate BITTEN v1 → v2 migration')
    parser.add_argument('--sqlite', default='/root/HydraX-v2/bitten.db', help='v1 SQLite database path')
    parser.add_argument('--postgres', default='postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2',
                        help='v2 PostgreSQL connection string')
    parser.add_argument('--output', help='Output JSON file path')
    args = parser.parse_args()

    validator = MigrationValidator(args.sqlite, args.postgres)

    try:
        results = await validator.validate_all()
        validator.print_summary(results)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to {args.output}")

        # Exit code
        sys.exit(0 if results['status'] == 'PASS' else 1)

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
