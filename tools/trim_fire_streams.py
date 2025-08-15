#!/usr/bin/env python3
import os, redis

REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

cur = 0
keys = []
trimmed = 0

print("Scanning for fire.* streams to trim...")
while True:
    cur, batch = r.scan(cur, match="fire.*", count=500)
    for k in batch:
        try:
            before = r.xlen(k)
            r.xtrim(k, maxlen=100000, approximate=True)
            after = r.xlen(k)
            if before != after:
                print(f"Trimmed {k}: {before} → {after}")
                trimmed += 1
        except Exception as e:
            print(f"Error trimming {k}: {e}")
    if cur == 0:
        break

print(f"Per-EA fire stream trim complete. Trimmed {trimmed} streams.")