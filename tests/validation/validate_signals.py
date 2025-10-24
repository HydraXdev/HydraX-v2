#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Signal Data Validation

Validates signal generation integrity and pattern detection accuracy.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import asyncio
import asyncpg
import json
from typing import Dict, List
from datetime import datetime, timedelta


class SignalValidator:
    """Validates signal data integrity"""

    def __init__(self, postgres_dsn: str = "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"):
        self.postgres_dsn = postgres_dsn
        self.errors = []
        self.warnings = []

    async def validate_all(self) -> Dict:
        """Run all signal validation checks"""
        print("🎯 BITTEN v2.0 Signal Validation")
        print("=" * 70)

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }

        pool = await asyncpg.create_pool(self.postgres_dsn, min_size=2, max_size=5)

        try:
            results["checks"]["pattern_distribution"] = await self.validate_pattern_distribution(pool)
            results["checks"]["confidence_ranges"] = await self.validate_confidence_ranges(pool)
            results["checks"]["required_fields"] = await self.validate_required_fields(pool)
            results["checks"]["rate_limits"] = await self.validate_rate_limits(pool)
            results["checks"]["duplicate_detection"] = await self.validate_duplicates(pool)
            results["checks"]["expiry_logic"] = await self.validate_expiry_logic(pool)

            results["errors"] = self.errors
            results["warnings"] = self.warnings
            results["status"] = "PASS" if len(self.errors) == 0 else "FAIL"

        finally:
            await pool.close()

        return results

    async def validate_pattern_distribution(self, pool) -> Dict:
        """Validate pattern type distribution"""
        print("\n📊 Validating Pattern Distribution...")

        async with pool.acquire() as conn:
            patterns = await conn.fetch("""
                SELECT pattern_type, COUNT(*) as count
                FROM signals
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY pattern_type
                ORDER BY count DESC
            """)

            expected_patterns = [
                'LIQUIDITY_SWEEP_REVERSAL',
                'ORDER_BLOCK_BOUNCE',
                'FAIR_VALUE_GAP_FILL',
                'VCB_BREAKOUT',
                'SWEEP_RETURN'
            ]

            found_patterns = [p['pattern_type'] for p in patterns]

            # Check for unexpected patterns
            for pattern in found_patterns:
                if pattern not in expected_patterns:
                    self.warnings.append(f"Unexpected pattern type: {pattern}")

            # Check for missing patterns (might be normal if low volume)
            for pattern in expected_patterns:
                if pattern not in found_patterns:
                    self.warnings.append(f"Pattern type not found in last 7 days: {pattern}")

            print(f"  ✅ Found {len(patterns)} pattern types")

            return {
                "patterns": [dict(p) for p in patterns],
                "expected": expected_patterns,
                "found": found_patterns
            }

    async def validate_confidence_ranges(self, pool) -> Dict:
        """Validate confidence scores are within valid ranges"""
        print("\n📈 Validating Confidence Ranges...")

        async with pool.acquire() as conn:
            # Check for out-of-range confidence
            invalid_confidence = await conn.fetch("""
                SELECT signal_id, confidence
                FROM signals
                WHERE confidence < 0 OR confidence > 100
                LIMIT 10
            """)

            if invalid_confidence:
                for sig in invalid_confidence:
                    self.errors.append(f"Signal {sig['signal_id']}: Invalid confidence {sig['confidence']}")

            # Check distribution by buckets
            buckets = await conn.fetch("""
                SELECT
                    CASE
                        WHEN confidence >= 90 THEN '90-100'
                        WHEN confidence >= 80 THEN '80-90'
                        WHEN confidence >= 70 THEN '70-80'
                        WHEN confidence >= 60 THEN '60-70'
                        ELSE '<60'
                    END as bucket,
                    COUNT(*) as count
                FROM signals
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY bucket
                ORDER BY bucket DESC
            """)

            print(f"  ✅ Confidence distribution validated")

            return {
                "invalid_count": len(invalid_confidence),
                "distribution": [dict(b) for b in buckets]
            }

    async def validate_required_fields(self, pool) -> Dict:
        """Validate all required fields are present"""
        print("\n🔍 Validating Required Fields...")

        async with pool.acquire() as conn:
            # Check for NULL values in required fields
            null_checks = await conn.fetch("""
                SELECT
                    SUM(CASE WHEN symbol IS NULL THEN 1 ELSE 0 END) as null_symbol,
                    SUM(CASE WHEN direction IS NULL THEN 1 ELSE 0 END) as null_direction,
                    SUM(CASE WHEN entry_price IS NULL THEN 1 ELSE 0 END) as null_entry_price,
                    SUM(CASE WHEN sl_pips IS NULL THEN 1 ELSE 0 END) as null_sl_pips,
                    SUM(CASE WHEN tp_pips IS NULL THEN 1 ELSE 0 END) as null_tp_pips,
                    SUM(CASE WHEN confidence IS NULL THEN 1 ELSE 0 END) as null_confidence,
                    SUM(CASE WHEN pattern_type IS NULL THEN 1 ELSE 0 END) as null_pattern_type
                FROM signals
            """)

            null_result = dict(null_checks[0])

            for field, count in null_result.items():
                if count > 0:
                    self.errors.append(f"{count} signals have NULL {field.replace('null_', '')}")

            print(f"  ✅ Required field check complete")

            return null_result

    async def validate_rate_limits(self, pool) -> Dict:
        """Validate signal generation rate limits"""
        print("\n⏱️  Validating Rate Limits...")

        async with pool.acquire() as conn:
            # Check for excessive signal generation (>10 signals/hour per symbol)
            high_rate_symbols = await conn.fetch("""
                SELECT
                    symbol,
                    COUNT(*) as count,
                    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/3600 as hours
                FROM signals
                WHERE created_at > NOW() - INTERVAL '1 hour'
                GROUP BY symbol
                HAVING COUNT(*) > 10
            """)

            for symbol_data in high_rate_symbols:
                rate = symbol_data['count'] / max(symbol_data['hours'], 0.1)
                self.warnings.append(
                    f"High signal rate for {symbol_data['symbol']}: {symbol_data['count']} in {symbol_data['hours']:.1f}h ({rate:.1f}/hr)"
                )

            print(f"  ✅ Rate limit check complete")

            return {
                "high_rate_symbols": [dict(s) for s in high_rate_symbols]
            }

    async def validate_duplicates(self, pool) -> Dict:
        """Check for duplicate signal IDs"""
        print("\n🔄 Validating Duplicate Detection...")

        async with pool.acquire() as conn:
            # Check for duplicate signal_ids
            duplicates = await conn.fetch("""
                SELECT signal_id, COUNT(*) as count
                FROM signals
                GROUP BY signal_id
                HAVING COUNT(*) > 1
            """)

            if duplicates:
                for dup in duplicates:
                    self.errors.append(f"Duplicate signal_id: {dup['signal_id']} ({dup['count']} times)")

            print(f"  ✅ Duplicate check complete")

            return {
                "duplicate_count": len(duplicates),
                "duplicates": [dict(d) for d in duplicates]
            }

    async def validate_expiry_logic(self, pool) -> Dict:
        """Validate signal expiry timestamps"""
        print("\n⏰ Validating Expiry Logic...")

        async with pool.acquire() as conn:
            # Check for signals with expires_at in the past but status still ACTIVE
            expired_active = await conn.fetch("""
                SELECT signal_id, created_at, expires_at, status
                FROM signals
                WHERE expires_at < NOW()
                AND status = 'ACTIVE'
                LIMIT 10
            """)

            if expired_active:
                for sig in expired_active:
                    self.warnings.append(
                        f"Signal {sig['signal_id']} expired but still ACTIVE"
                    )

            # Check for invalid expiry times (expires_at before created_at)
            invalid_expiry = await conn.fetch("""
                SELECT signal_id, created_at, expires_at
                FROM signals
                WHERE expires_at < created_at
                LIMIT 10
            """)

            if invalid_expiry:
                for sig in invalid_expiry:
                    self.errors.append(
                        f"Signal {sig['signal_id']}: expires_at before created_at"
                    )

            print(f"  ✅ Expiry logic validated")

            return {
                "expired_active_count": len(expired_active),
                "invalid_expiry_count": len(invalid_expiry)
            }

    def print_summary(self, results: Dict):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("📋 SIGNAL VALIDATION SUMMARY")
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
            print("\n✅ SIGNAL VALIDATION PASSED")
        else:
            print("\n❌ SIGNAL VALIDATION FAILED")

        print("=" * 70)


async def main():
    """Main execution"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Validate BITTEN v2 signal data')
    parser.add_argument('--postgres', default='postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2',
                        help='PostgreSQL connection string')
    parser.add_argument('--output', help='Output JSON file path')
    args = parser.parse_args()

    validator = SignalValidator(args.postgres)

    try:
        results = await validator.validate_all()
        validator.print_summary(results)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to {args.output}")

        sys.exit(0 if results['status'] == 'PASS' else 1)

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
