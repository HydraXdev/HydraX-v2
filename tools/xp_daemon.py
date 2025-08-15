#!/usr/bin/env python3
import os, time, sqlite3, uuid, collections
DB=os.environ.get("BITTEN_DB","/root/HydraX-v2/bitten.db")
INTERVAL=int(os.environ.get("XP_INTERVAL_SEC","30"))
# Rules: variety bonus + streak bonus
VARIETY_BONUS=5    # per new pattern type seen today
STREAK_BONUS =3    # per 3-in-a-row of same type

def rows(q, args=()):
    conn=sqlite3.connect(DB); conn.row_factory=lambda c,r:{d[0]:r[i] for i,d in enumerate(c.description)}
    try:
        for x in conn.execute(q, args): yield x
    finally:
        conn.close()

def exec_(q, args=()):
    conn=sqlite3.connect(DB)
    try:
        conn.execute(q, args); conn.commit()
    finally:
        conn.close()

def main():
    print(f"[XP Daemon] Starting... DB={DB}, Interval={INTERVAL}s")
    last_checked=0
    while True:
        now=int(time.time())
        try:
            # Look at recently FILLED fires and award XP once per fire_id
            recent=list(rows("""
            SELECT f.fire_id, f.user_id, s.pattern_type, f.created_at
            FROM fires f
            LEFT JOIN missions m ON m.mission_id=f.mission_id
            LEFT JOIN signals s ON s.signal_id=m.signal_id
            WHERE f.status='FILLED' AND f.created_at>?
            ORDER BY f.created_at ASC
            """,(now-86400,)))
            
            # Build per-user stats for variety & streaks
            per_user=collections.defaultdict(list)
            for r in recent: 
                if r['user_id']:
                    per_user[r['user_id']].append(r)
                    
            for uid, lst in per_user.items():
                # variety bonus: count distinct pattern_type today
                kinds=sorted(set(x['pattern_type'] for x in lst if x['pattern_type']))
                for k in kinds:
                    exec_("INSERT OR IGNORE INTO xp_events(event_id,user_id,pattern_type,delta,reason,created_at) VALUES (?,?,?,?,?,?)",
                          (f"var:{uid}:{k}:{now//3600}", uid, k, VARIETY_BONUS, "variety_daily", now))
                # simple streaks: every 3 in a row same type
                for i in range(2,len(lst)):
                    if lst[i]['pattern_type']==lst[i-1]['pattern_type']==lst[i-2]['pattern_type']:
                        exec_("INSERT OR IGNORE INTO xp_events(event_id,user_id,pattern_type,delta,reason,created_at) VALUES (?,?,?,?,?,?)",
                              (f"streak:{uid}:{lst[i]['pattern_type']}:{i}:{now//3600}", uid, lst[i]['pattern_type'], STREAK_BONUS, "streak_triple", now))
        except Exception as e:
            print(f"[XP Daemon] Error: {e}")
            
        last_checked=now
        time.sleep(INTERVAL)

if __name__=="__main__":
    main()