#!/usr/bin/env python3
"""
Database Consolidation Script
Merges multiple SQLite databases into single consolidated database
"""

import sqlite3
import os
import shutil
from datetime import datetime

def consolidate_databases():
    """Consolidate multiple SQLite databases into single production database"""
    
    # Source databases
    databases = [
        '/root/HydraX-v2/data/bitten_xp.db',
        '/root/HydraX-v2/bitten_profiles.db', 
        '/root/HydraX-v2/data/live_performance.db',
        '/root/HydraX-v2/data/engagement.db',
        '/root/HydraX-v2/data/live_market.db',
        '/root/HydraX-v2/data/mt5_instances.db',
        '/root/HydraX-v2/data/trades/trades.db',
        '/root/HydraX-v2/bitten/data/personality_bot.db',
        '/root/HydraX-v2/data/visitor_analytics.db',
        '/root/HydraX-v2/data/standalone_referral.db',
        '/root/HydraX-v2/data/referral_system.db',
        '/root/HydraX-v2/data/ally_codes.db'
    ]
    
    # Target consolidated database
    target_db = '/root/HydraX-v2/data/bitten_production.db'
    
    # Create backup directory
    backup_dir = '/root/HydraX-v2/data/backup_original_dbs'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create consolidated database
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    print(f"🔄 Creating consolidated database: {target_db}")
    
    # Process each source database
    for db_path in databases:
        if os.path.exists(db_path):
            print(f"📂 Processing: {db_path}")
            
            # Backup original
            backup_path = os.path.join(backup_dir, os.path.basename(db_path))
            shutil.copy2(db_path, backup_path)
            print(f"📋 Backed up to: {backup_path}")
            
            # Open source database separately to avoid locking issues
            db_name = os.path.basename(db_path).replace('.db', '').replace('-', '_')
            source_conn = sqlite3.connect(db_path)
            source_cursor = source_conn.cursor()
            
            # Get all tables from source
            source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = source_cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if table_name == 'sqlite_sequence':
                    continue
                    
                # Get table schema
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table_name}'")
                schema = source_cursor.fetchone()
                
                if schema and schema[0]:
                    # Create table in consolidated database (with prefix to avoid conflicts)
                    new_table_name = f"{db_name}_{table_name}"
                    new_schema = schema[0].replace(f"CREATE TABLE {table_name}", f"CREATE TABLE IF NOT EXISTS {new_table_name}")
                    cursor.execute(new_schema)
                    
                    # Get all data from source table
                    source_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = source_cursor.fetchall()
                    
                    if rows:
                        # Get column count for placeholders
                        source_cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = source_cursor.fetchall()
                        placeholders = ','.join(['?'] * len(columns))
                        
                        # Insert data into consolidated database
                        cursor.executemany(f"INSERT OR IGNORE INTO {new_table_name} VALUES ({placeholders})", rows)
                        rows_copied = len(rows)
                    else:
                        rows_copied = 0
                    
                    print(f"  ✅ {table_name} -> {new_table_name}: {rows_copied} rows")
            
            # Close source database connection
            source_conn.close()
            
        else:
            print(f"❌ Database not found: {db_path}")
    
    # Create consolidated views for easy access
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS consolidated_users AS 
    SELECT * FROM bitten_profiles_users 
    UNION ALL 
    SELECT * FROM bitten_xp_users WHERE user_id NOT IN (SELECT user_id FROM bitten_profiles_users)
    """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS consolidated_trades AS
    SELECT * FROM trades_trades
    UNION ALL
    SELECT * FROM live_performance_trades WHERE trade_id NOT IN (SELECT trade_id FROM trades_trades)
    """)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"✅ Database consolidation complete!")
    print(f"📍 Consolidated database: {target_db}")
    print(f"📍 Original databases backed up to: {backup_dir}")
    
    # Get file sizes
    original_size = sum(os.path.getsize(db) for db in databases if os.path.exists(db))
    consolidated_size = os.path.getsize(target_db)
    
    print(f"📊 Original total size: {original_size / 1024 / 1024:.1f} MB")
    print(f"📊 Consolidated size: {consolidated_size / 1024 / 1024:.1f} MB")
    print(f"📊 Space efficiency: {(1 - consolidated_size/original_size)*100:.1f}% reduction")

if __name__ == "__main__":
    consolidate_databases()