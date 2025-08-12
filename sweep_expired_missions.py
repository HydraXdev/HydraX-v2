#!/usr/bin/env python3
import sqlite3
import time
import os

db = os.getenv("BITTEN_DB", "/root/HydraX-v2/bitten.db")
now = int(time.time())

with sqlite3.connect(db) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE missions SET status='TIMEOUT' WHERE status='PENDING' AND expires_at<?",
        (now,)
    )
    updated = cursor.rowcount
    conn.commit()
    
    if updated > 0:
        print(f"✅ Marked {updated} expired missions as TIMEOUT")