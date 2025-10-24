#!/usr/bin/env python3
"""
Complete Firebase UID Migration Script
=======================================
Migrates entire BITTEN system from telegram_id to Firebase UID

CRITICAL TABLES TO MIGRATE:

bitten.db:
1. ea_instances.user_id (telegram_id → firebase_uid)
2. fires.user_id (telegram_id → firebase_uid)
3. missions.user_id (telegram_id → firebase_uid)
4. fire_slots.user_id (telegram_id → firebase_uid)
5. slot_events.user_id (telegram_id → firebase_uid)
6. slot_tracking.user_id (telegram_id → firebase_uid)
7. live_positions.user_id (telegram_id → firebase_uid)
8. position_events.user_id (telegram_id → firebase_uid)
9. position_tracking.user_id (telegram_id → firebase_uid)
10. positions_live.user_id (telegram_id → firebase_uid)
11. xp_events.user_id (telegram_id → firebase_uid)

fire_modes.db:
12. user_fire_modes.user_id (telegram_id → firebase_uid)
13. active_slots.user_id (telegram_id → firebase_uid)
14. fire_mode_history.user_id (telegram_id → firebase_uid)
15. chaingun_inventory.user_id (telegram_id → firebase_uid)
16. chaingun_sessions.user_id (telegram_id → firebase_uid)

Date: October 13, 2025
Author: Claude Code (Sonnet 4.5)
"""

import sqlite3
import sys
from datetime import datetime

def get_user_mapping(conn):
    """Get telegram_id -> firebase_uid mapping"""
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, firebase_uid FROM user_uuid_mapping")
    mapping = {row[0]: row[1] for row in cursor.fetchall()}
    print(f"📊 Loaded {len(mapping)} user mappings from user_uuid_mapping table")
    return mapping

def backup_database(db_path):
    """Create backup before migration"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path

def migrate_table(conn, table_name, uid_mapping, dry_run=True):
    """Migrate a single table from telegram_id to firebase_uid"""
    cursor = conn.cursor()

    # Check if table exists and has user_id column
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    has_user_id = any(col[1] == 'user_id' for col in columns)

    if not has_user_id:
        print(f"⏭️  {table_name}: No user_id column, skipping")
        return 0

    # Count rows with telegram_id
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id IS NOT NULL AND user_id != ''")
    total_rows = cursor.fetchone()[0]

    if total_rows == 0:
        print(f"⏭️  {table_name}: No rows to migrate")
        return 0

    # Migrate each telegram_id to firebase_uid
    migrated = 0
    for telegram_id, firebase_uid in uid_mapping.items():
        if dry_run:
            # Count what would be migrated
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id = ?", (telegram_id,))
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"   [DRY RUN] Would migrate {count} rows: {telegram_id} → {firebase_uid}")
                migrated += count
        else:
            # Actually migrate
            cursor.execute(f"UPDATE {table_name} SET user_id = ? WHERE user_id = ?",
                          (firebase_uid, telegram_id))
            if cursor.rowcount > 0:
                print(f"   ✅ Migrated {cursor.rowcount} rows: {telegram_id} → {firebase_uid}")
                migrated += cursor.rowcount

    if not dry_run and migrated > 0:
        conn.commit()
        print(f"✅ {table_name}: {migrated}/{total_rows} rows migrated")
    elif dry_run and migrated > 0:
        print(f"📊 {table_name}: {migrated}/{total_rows} rows would be migrated")

    return migrated

def verify_migration(conn, table_name, uid_mapping):
    """Verify migration was successful"""
    cursor = conn.cursor()

    # Check if any telegram_ids remain
    telegram_ids = list(uid_mapping.keys())
    placeholders = ','.join('?' * len(telegram_ids))
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id IN ({placeholders})",
                   telegram_ids)
    remaining = cursor.fetchone()[0]

    if remaining > 0:
        print(f"⚠️  {table_name}: {remaining} telegram_id rows still exist!")
        return False

    # Check if firebase_uids now exist
    firebase_uids = list(uid_mapping.values())
    placeholders = ','.join('?' * len(firebase_uids))
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id IN ({placeholders})",
                   firebase_uids)
    migrated = cursor.fetchone()[0]

    print(f"✅ {table_name}: {migrated} rows now use Firebase UID")
    return True

def main():
    # Parse arguments
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    skip_backup = '--skip-backup' in sys.argv

    if dry_run:
        print("=" * 70)
        print("🔍 DRY RUN MODE - No changes will be made")
        print("=" * 70)
    else:
        print("=" * 70)
        print("🚨 LIVE MIGRATION MODE - Databases will be modified!")
        print("=" * 70)

    # Database paths
    databases = {
        'bitten.db': '/root/HydraX-v2/bitten.db',
        'fire_modes.db': '/root/HydraX-v2/data/fire_modes.db'
    }

    # Connect to main database for user mapping
    main_conn = sqlite3.connect(databases['bitten.db'])

    # Get user mapping
    uid_mapping = get_user_mapping(main_conn)

    if not uid_mapping:
        print("❌ No user mappings found in user_uuid_mapping table!")
        print("   Run this first: python3 link_legacy_account.py <firebase_uid> <telegram_id>")
        main_conn.close()
        sys.exit(1)

    print("\n" + "=" * 70)
    print("📋 MIGRATION PLAN")
    print("=" * 70)

    # Tables by database
    db_tables = {
        'bitten.db': [
            'ea_instances',      # MT5 account mappings
            'fires',             # Trade executions
            'missions',          # Signal missions
            'fire_slots',        # Trading slot limits
            'slot_events',       # Slot usage history
            'slot_tracking',     # Current slot status
            'live_positions',    # Open positions
            'position_events',   # Position lifecycle
            'position_tracking', # Position monitoring
            'positions_live',    # Real-time positions
            'xp_events',         # XP award history
        ],
        'fire_modes.db': [
            'user_fire_modes',   # User autofire settings
            'active_slots',      # Active slot tracking
            'fire_mode_history', # Mode change history
            'chaingun_inventory', # Chaingun inventory
            'chaingun_sessions', # Chaingun usage
        ]
    }

    total_migrated = 0
    all_tables_verified = True

    # Migrate each database
    for db_name, db_path in databases.items():
        if db_name == 'bitten.db':
            conn = main_conn
        else:
            # Create backup if needed
            if not dry_run and not skip_backup:
                response = input(f"Create backup of {db_name}? (Y/n): ")
                if response.lower() != 'n':
                    backup_database(db_path)
            conn = sqlite3.connect(db_path)

        print(f"\n{'═' * 70}")
        print(f"🗄️  DATABASE: {db_name}")
        print(f"{'═' * 70}")

        tables = db_tables.get(db_name, [])

        for table in tables:
            print(f"\n{'─' * 70}")
            print(f"📋 Migrating: {table}")
            print(f"{'─' * 70}")
            migrated = migrate_table(conn, table, uid_mapping, dry_run)
            total_migrated += migrated

        if db_name != 'bitten.db':
            conn.close()

    print("\n" + "=" * 70)
    if dry_run:
        print(f"📊 DRY RUN COMPLETE: {total_migrated} rows would be migrated")
        print("\n💡 To perform actual migration, run:")
        print(f"   python3 {sys.argv[0]}")
    else:
        print(f"✅ MIGRATION COMPLETE: {total_migrated} rows migrated")

        # Verify migration
        print("\n" + "=" * 70)
        print("🔍 VERIFYING MIGRATION")
        print("=" * 70)

        for db_name, db_path in databases.items():
            if db_name == 'bitten.db':
                conn = main_conn
            else:
                conn = sqlite3.connect(db_path)

            print(f"\n{'═' * 70}")
            print(f"🗄️  VERIFYING: {db_name}")
            print(f"{'═' * 70}")

            tables = db_tables.get(db_name, [])
            for table in tables:
                if not verify_migration(conn, table, uid_mapping):
                    all_tables_verified = False

            if db_name != 'bitten.db':
                conn.close()

        if all_tables_verified:
            print("\n✅ ALL TABLES VERIFIED - Migration successful!")
        else:
            print("\n⚠️  Some tables failed verification - check logs above")

    main_conn.close()

    print("\n" + "=" * 70)
    print("📝 NEXT STEPS:")
    print("=" * 70)
    print("1. Update backend API endpoints to accept Firebase UID")
    print("2. Update webapp /api/fire endpoint to use Firebase UID")
    print("3. Update StrikeAuthorizationModal to send Firebase UID")
    print("4. Restart all PM2 processes")
    print("5. Test trade execution end-to-end")
    print("=" * 70)

if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Firebase UID Migration Script")
        print("\nUsage:")
        print("  python3 migrate_to_firebase_uid_complete.py [OPTIONS]")
        print("\nOptions:")
        print("  --dry-run, -d     : Preview changes without modifying database")
        print("  --skip-backup     : Skip backup creation (not recommended)")
        print("  --help, -h        : Show this help message")
        print("\nExamples:")
        print("  # Preview migration")
        print("  python3 migrate_to_firebase_uid_complete.py --dry-run")
        print("\n  # Perform migration")
        print("  python3 migrate_to_firebase_uid_complete.py")
        sys.exit(0)

    main()
