#!/usr/bin/env python3
"""
Slot Reconciliation Utility
Reconciles active_slots table with actual tier limits and provides cleanup options
"""

import sqlite3
import sys

sys.path.append("/root/HydraX-v2")

from src.bitten_core.fire_mode_database import fire_mode_db


def print_header(title):
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)


def check_slot_overflows():
    """Check for users with more open slots than their tier allows"""
    print_header("SLOT OVERFLOW DETECTION")

    conn = sqlite3.connect("/root/HydraX-v2/data/fire_modes.db")
    cursor = conn.cursor()

    # Get all users with open slots
    cursor.execute(
        """
        SELECT ufm.user_id, subscription_tier,
               COUNT(CASE WHEN slot_type = 'MANUAL' AND status = 'OPEN' THEN 1 END) as open_manual,
               COUNT(CASE WHEN slot_type = 'AUTO' AND status = 'OPEN' THEN 1 END) as open_auto,
               COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as total_open
        FROM user_fire_modes ufm
        LEFT JOIN active_slots asa ON ufm.user_id = asa.user_id
        GROUP BY ufm.user_id, subscription_tier
        HAVING total_open > 0
    """
    )

    users = cursor.fetchall()
    overflows = []

    for user_id, tier, open_manual, open_auto, total_open in users:
        tier_limits = fire_mode_db.get_tier_slot_limits(tier or "NIBBLER")

        manual_overflow = max(0, open_manual - tier_limits["manual"])
        auto_overflow = max(0, open_auto - tier_limits["auto"])
        total_overflow = max(0, total_open - tier_limits["total"])

        if manual_overflow > 0 or auto_overflow > 0 or total_overflow > 0:
            overflows.append(
                {
                    "user_id": user_id,
                    "tier": tier,
                    "open_manual": open_manual,
                    "open_auto": open_auto,
                    "total_open": total_open,
                    "manual_overflow": manual_overflow,
                    "auto_overflow": auto_overflow,
                    "total_overflow": total_overflow,
                    "limits": tier_limits,
                }
            )

            print(f"❌ USER {user_id} ({tier}):")
            print(f"   Open slots: {open_manual} manual + {open_auto} auto = {total_open} total")
            print(
                f"   Tier limits: {tier_limits['manual']} manual + {tier_limits['auto']} auto = {tier_limits['total']} total"
            )
            print(f"   Overflow: {manual_overflow} manual + {auto_overflow} auto = {total_overflow} total")

    if not overflows:
        print("✅ No slot overflows detected")

    conn.close()
    return overflows


def cleanup_old_slots(dry_run=True):
    """Clean up old closed slots to reduce database size"""
    print_header("OLD SLOT CLEANUP")

    conn = sqlite3.connect("/root/HydraX-v2/data/fire_modes.db")
    cursor = conn.cursor()

    # Count closed slots older than 7 days
    cursor.execute(
        """
        SELECT COUNT(*) FROM active_slots
        WHERE status = 'CLOSED'
        AND closed_at < datetime('now', '-7 days')
    """
    )
    old_closed_count = cursor.fetchone()[0]

    print(f"Old closed slots (>7 days): {old_closed_count}")

    if old_closed_count > 0:
        if not dry_run:
            cursor.execute(
                """
                DELETE FROM active_slots
                WHERE status = 'CLOSED'
                AND closed_at < datetime('now', '-7 days')
            """
            )
            conn.commit()
            print(f"✅ Deleted {old_closed_count} old closed slots")
        else:
            print(f"📋 Would delete {old_closed_count} old closed slots (dry run)")

    conn.close()


def suggest_slot_limits():
    """Suggest appropriate slot limits based on current usage"""
    print_header("SLOT LIMIT SUGGESTIONS")

    conn = sqlite3.connect("/root/HydraX-v2/data/fire_modes.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT daily_usage.user_id, subscription_tier,
               MAX(manual_open) as max_manual_used,
               MAX(auto_open) as max_auto_used,
               MAX(total_open) as max_total_used
        FROM (
            SELECT ufm.user_id, subscription_tier,
                   COUNT(CASE WHEN slot_type = 'MANUAL' AND status = 'OPEN' THEN 1 END) as manual_open,
                   COUNT(CASE WHEN slot_type = 'AUTO' AND status = 'OPEN' THEN 1 END) as auto_open,
                   COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as total_open
            FROM user_fire_modes ufm
            LEFT JOIN active_slots asa ON ufm.user_id = asa.user_id
            GROUP BY ufm.user_id, subscription_tier, DATE(asa.opened_at)
        ) daily_usage
        GROUP BY daily_usage.user_id, subscription_tier
    """
    )

    for user_id, tier, max_manual, max_auto, max_total in cursor.fetchall():
        if max_total > 0:
            tier_limits = fire_mode_db.get_tier_slot_limits(tier or "NIBBLER")
            print(f"User {user_id} ({tier}):")
            print(f"   Historical max usage: {max_manual} manual + {max_auto} auto = {max_total} total")
            print(
                f"   Current tier limits: {tier_limits['manual']} manual + {tier_limits['auto']} auto = {tier_limits['total']} total"
            )

            if max_total > tier_limits["total"]:
                print(f"   💡 Suggestion: Consider upgrading tier or adjusting limits")

    conn.close()


def main():
    print("🔧 BITTEN SLOT RECONCILIATION UTILITY")
    print("This tool helps identify and resolve slot tracking issues")

    # Check for overflows
    overflows = check_slot_overflows()

    # Suggest limits based on usage
    suggest_slot_limits()

    # Cleanup old slots (dry run)
    cleanup_old_slots(dry_run=True)

    print_header("RECOMMENDATIONS")

    if overflows:
        print("❌ Slot overflows detected - Consider:")
        print("   1. Manually close excess positions")
        print("   2. Upgrade user tiers if usage is legitimate")
        print("   3. Adjust tier limits if current limits are too restrictive")
    else:
        print("✅ No immediate slot issues detected")

    print("\n📋 To clean up old closed slots, run:")
    print("   python3 reconcile_slots.py --cleanup")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup_old_slots(dry_run=False)
    else:
        main()
