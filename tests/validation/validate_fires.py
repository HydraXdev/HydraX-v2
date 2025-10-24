#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Fire Command Validation

Validates fire execution records and status transitions.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import asyncpg
import json
import sys
from typing import Dict
from datetime import datetime


class FireValidator:
    """Validates fire command data integrity"""

    def __init__(self, postgres_dsn: str = "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"):
        self.postgres_dsn = postgres_dsn
        self.errors = []
        self.warnings = []

    async def validate_all(self) -> Dict:
        """Run all fire validation checks"""
        print("🔥 BITTEN v2.0 Fire Validation")
        print("=" * 70)

        pool = await asyncpg.create_pool(self.postgres_dsn, min_size=2, max_size=5)

        try:
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "status_transitions": await self.validate_status_transitions(pool),
                    "ticket_uniqueness": await self.validate_ticket_uniqueness(pool),
                    "orphaned_fires": await self.validate_orphaned_fires(pool),
                    "timeout_handling": await self.validate_timeout_handling(pool),
                    "duplicate_fires": await self.validate_duplicate_fires(pool)
                },
                "errors": self.errors,
                "warnings": self.warnings
            }

            results["status"] = "PASS" if len(self.errors) == 0 else "FAIL"

        finally:
            await pool.close()

        self.print_summary(results)
        return results

    async def validate_status_transitions(self, pool) -> Dict:
        """Validate fire status transitions are valid"""
        print("\n🔄 Validating Status Transitions...")

        async with pool.acquire() as conn:
            # Count by status
            status_counts = await conn.fetch("""
                SELECT status, COUNT(*) as count
                FROM fires
                GROUP BY status
            """)

            # Check for invalid statuses
            valid_statuses = ['SENT', 'FILLED', 'FAILED', 'TIMEOUT', 'CANCELLED']
            for row in status_counts:
                if row['status'] not in valid_statuses:
                    self.errors.append(f"Invalid fire status: {row['status']}")

            print(f"  ✅ Status distribution validated")
            return {"distribution": [dict(s) for s in status_counts]}

    async def validate_ticket_uniqueness(self, pool) -> Dict:
        """Validate MT5 ticket numbers are unique"""
        print("\n🎫 Validating Ticket Uniqueness...")

        async with pool.acquire() as conn:
            duplicates = await conn.fetch("""
                SELECT ticket, COUNT(*) as count
                FROM fires
                WHERE ticket IS NOT NULL
                GROUP BY ticket
                HAVING COUNT(*) > 1
            """)

            for dup in duplicates:
                self.errors.append(f"Duplicate ticket: {dup['ticket']} ({dup['count']} fires)")

            print(f"  ✅ Ticket uniqueness validated")
            return {"duplicate_count": len(duplicates)}

    async def validate_orphaned_fires(self, pool) -> Dict:
        """Check for fires without corresponding signals"""
        print("\n🔗 Validating Fire-Signal Links...")

        async with pool.acquire() as conn:
            orphaned = await conn.fetchval("""
                SELECT COUNT(*)
                FROM fires f
                WHERE NOT EXISTS (
                    SELECT 1 FROM signals s
                    WHERE f.fire_id LIKE '%' || s.signal_id || '%'
                )
            """)

            if orphaned > 0:
                self.warnings.append(f"{orphaned} fires have no matching signal")

            print(f"  ✅ Orphaned fire check complete")
            return {"orphaned_count": orphaned}

    async def validate_timeout_handling(self, pool) -> Dict:
        """Validate timeout logic"""
        print("\n⏱️  Validating Timeout Handling...")

        async with pool.acquire() as conn:
            # Fires older than 30s still in SENT status
            stuck_fires = await conn.fetchval("""
                SELECT COUNT(*)
                FROM fires
                WHERE status = 'SENT'
                AND created_at < NOW() - INTERVAL '30 seconds'
            """)

            if stuck_fires > 0:
                self.warnings.append(f"{stuck_fires} fires stuck in SENT status (>30s)")

            print(f"  ✅ Timeout handling validated")
            return {"stuck_fires": stuck_fires}

    async def validate_duplicate_fires(self, pool) -> Dict:
        """Check for duplicate fire_id"""
        print("\n🔍 Validating Duplicate Prevention...")

        async with pool.acquire() as conn:
            duplicates = await conn.fetch("""
                SELECT fire_id, COUNT(*) as count
                FROM fires
                GROUP BY fire_id
                HAVING COUNT(*) > 1
            """)

            for dup in duplicates:
                self.errors.append(f"Duplicate fire_id: {dup['fire_id']}")

            print(f"  ✅ Duplicate check complete")
            return {"duplicate_count": len(duplicates)}

    def print_summary(self, results: Dict):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print(f"Status: {results['status']}")
        print(f"Errors: {len(results['errors'])}, Warnings: {len(results['warnings'])}")

        if results['errors']:
            print("\n❌ ERRORS:")
            for error in results['errors']:
                print(f"  - {error}")

        if results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in results['warnings']:
                print(f"  - {warning}")

        print("=" * 70)


async def main():
    validator = FireValidator()
    results = await validator.validate_all()

    import sys
    sys.exit(0 if results['status'] == 'PASS' else 1)


if __name__ == "__main__":
    asyncio.run(main())
