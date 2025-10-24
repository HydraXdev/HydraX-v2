#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Position Tracking Validation

Validates position data accuracy and synchronization.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import asyncpg
import json
import sys
from datetime import datetime


async def validate_positions():
    """Validate position tracking integrity"""
    print("📈 BITTEN v2.0 Position Validation")
    print("=" * 70)

    pool = await asyncpg.create_pool(
        "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2",
        min_size=2, max_size=5
    )

    errors = []
    warnings = []

    try:
        async with pool.acquire() as conn:
            # Check for duplicate tickets
            print("\n🎫 Checking Duplicate Tickets...")
            duplicates = await conn.fetch("""
                SELECT ticket, COUNT(*) as count
                FROM positions
                WHERE ticket IS NOT NULL
                GROUP BY ticket
                HAVING COUNT(*) > 1
            """)

            for dup in duplicates:
                errors.append(f"Duplicate ticket: {dup['ticket']}")

            # Check for orphaned positions (no fire)
            print("\n🔗 Checking Orphaned Positions...")
            orphaned = await conn.fetchval("""
                SELECT COUNT(*)
                FROM positions p
                WHERE NOT EXISTS (
                    SELECT 1 FROM fires f WHERE f.fire_id = p.fire_id
                )
            """)

            if orphaned > 0:
                warnings.append(f"{orphaned} positions have no matching fire")

            # Check for invalid status
            print("\n🔄 Checking Position Status...")
            invalid_status = await conn.fetch("""
                SELECT position_id, status
                FROM positions
                WHERE status NOT IN ('OPEN', 'CLOSED', 'PENDING')
            """)

            for pos in invalid_status:
                errors.append(f"Invalid status: {pos['position_id']} = {pos['status']}")

            # Check for negative volumes
            print("\n📊 Checking Volume Values...")
            negative_vol = await conn.fetchval("""
                SELECT COUNT(*)
                FROM positions
                WHERE volume <= 0
            """)

            if negative_vol > 0:
                errors.append(f"{negative_vol} positions have invalid volume")

            # Summary
            print("\n" + "=" * 70)
            print(f"Errors: {len(errors)}, Warnings: {len(warnings)}")

            if errors:
                print("\n❌ ERRORS:")
                for error in errors:
                    print(f"  - {error}")

            if warnings:
                print("\n⚠️  WARNINGS:")
                for warning in warnings:
                    print(f"  - {warning}")

            status = "PASS" if len(errors) == 0 else "FAIL"
            print(f"\n{status}")
            print("=" * 70)

            return 0 if status == "PASS" else 1

    finally:
        await pool.close()


if __name__ == "__main__":
    exit_code = asyncio.run(validate_positions())
    sys.exit(exit_code)
