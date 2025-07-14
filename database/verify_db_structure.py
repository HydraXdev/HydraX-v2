#!/usr/bin/env python3
"""
Verify database structure and show some sample data.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "/root/HydraX-v2/data/engagement.db"

def verify_database_structure():
    """Verify the database structure and show sample data"""
    print("🔍 Verifying Database Structure")
    print("=" * 50)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found: {DB_PATH}")
        return
    
    print(f"✅ Database file exists: {DB_PATH}")
    print(f"📁 File size: {os.path.getsize(DB_PATH)} bytes")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tables in database: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"  • {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"    Columns ({len(columns)}):")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = "PK" if col[5] else ""
                not_null = "NOT NULL" if col[3] else "NULL"
                print(f"      - {col_name} ({col_type}) {not_null} {is_pk}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"    Records: {row_count}")
        
        # Show indexes
        print(f"\n🔍 Indexes in database:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        for index in indexes:
            print(f"  • {index[0]}")
        
        # Show some sample data
        print(f"\n📊 Sample Data:")
        
        # Signal fires
        cursor.execute("""
            SELECT user_id, signal_id, timestamp, executed 
            FROM signal_fires 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        signal_fires = cursor.fetchall()
        print(f"  Recent Signal Fires ({len(signal_fires)}):")
        for fire in signal_fires:
            print(f"    - User {fire[0]} fired {fire[1]} at {fire[2]} (executed: {fire[3]})")
        
        # User stats
        cursor.execute("""
            SELECT user_id, total_fires, win_rate, pnl 
            FROM user_stats 
            ORDER BY total_fires DESC 
            LIMIT 5
        """)
        user_stats = cursor.fetchall()
        print(f"  Top Users by Fires ({len(user_stats)}):")
        for stat in user_stats:
            print(f"    - User {stat[0]}: {stat[1]} fires, {stat[2]:.2%} win rate, ${stat[3]:.2f} PnL")
        
        # Signal metrics
        cursor.execute("""
            SELECT signal_id, total_fires, active_users 
            FROM signal_metrics 
            ORDER BY total_fires DESC 
            LIMIT 5
        """)
        signal_metrics = cursor.fetchall()
        print(f"  Top Signals by Fires ({len(signal_metrics)}):")
        for metric in signal_metrics:
            print(f"    - {metric[0]}: {metric[1]} fires, {metric[2]} active users")
        
        conn.close()
        
        print(f"\n✅ Database verification completed successfully!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    verify_database_structure()