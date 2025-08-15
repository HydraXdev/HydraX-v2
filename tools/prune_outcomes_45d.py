# -*- coding: utf-8 -*-
import os, sqlite3, time
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

DB=os.environ.get("BITTEN_DB","/root/HydraX-v2/bitten.db")
TZ=ZoneInfo("America/New_York")

def main():
    now_utc=int(time.time())
    cutoff_utc = now_utc - 45*24*3600
    # outcomes_daily cutoff is 45d in ET (by day granularity)
    today_et = datetime.now(TZ).date()
    cutoff_day = (today_et - timedelta(days=45)).strftime("%Y-%m-%d")
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute("DELETE FROM signal_outcomes WHERE signaled_at < ?", (cutoff_utc,))
    deleted1=cur.rowcount
    cur.execute("DELETE FROM outcomes_daily WHERE day_et < ?", (cutoff_day,))
    deleted2=cur.rowcount
    conn.commit()
    print(f"[PRUNE] signal_outcomes<{cutoff_utc} deleted={deleted1}; outcomes_daily<{cutoff_day} deleted={deleted2}")
    # Weekly VACUUM (Sunday ~03:00 UTC) via env toggle or detect weekday:
    if datetime.utcnow().weekday()==6 and int(datetime.utcnow().strftime("%H"))==3:
        try:
            cur.execute("VACUUM")
            print("[PRUNE] VACUUM done")
        except Exception as e:
            print(f"[PRUNE] VACUUM skipped: {e}")
    conn.close()

if __name__=="__main__":
    main()