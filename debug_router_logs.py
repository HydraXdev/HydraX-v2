#!/usr/bin/env python3
import sqlite3
import time

def check_router_state():
    # Check database for EA instances
    conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT target_uuid, user_id, last_seen, (strftime('%s','now') - last_seen) as age
        FROM ea_instances 
        ORDER BY last_seen DESC
    """)
    
    print("=== EA INSTANCES ===")
    for row in cursor.fetchall():
        uuid, user_id, last_seen, age = row
        print(f"{uuid}: user_id={user_id}, age={age}s")
    
    # Check recent fire records
    cursor.execute("""
        SELECT fire_id, user_id, status, created_at
        FROM fires 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    print("\n=== RECENT FIRES ===")
    for row in cursor.fetchall():
        fire_id, user_id, status, created_at = row
        age = int(time.time()) - created_at
        print(f"{fire_id}: user={user_id}, status={status}, age={age}s")
    
    conn.close()

if __name__ == "__main__":
    check_router_state()