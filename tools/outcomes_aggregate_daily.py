# -*- coding: utf-8 -*-
import os, sqlite3, statistics, time, json
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # py3.8 fallback if installed

DB=os.environ.get("BITTEN_DB","/root/HydraX-v2/bitten.db")
TZ = ZoneInfo("America/New_York")

def et_day_bounds(day_et_str=None):
    now_et=datetime.now(TZ)
    if day_et_str:
        y,m,d=map(int,day_et_str.split("-"))
        day_dt = datetime(y,m,d,0,0,0,tzinfo=TZ)
    else:
        # default: yesterday ET
        today_et = datetime(now_et.year, now_et.month, now_et.day, tzinfo=TZ)
        day_dt = today_et - timedelta(days=1)
    start_utc = int(day_dt.astimezone(timezone.utc).timestamp())
    end_utc   = int((day_dt + timedelta(days=1)).astimezone(timezone.utc).timestamp())
    return day_dt.strftime("%Y-%m-%d"), start_utc, end_utc

def fetch_rows(conn, start_utc, end_utc):
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    cur.execute("""
      SELECT pattern_class, confidence, signaled_at, resolved_at, outcome
      FROM signal_outcomes
      WHERE signaled_at >= ? AND signaled_at < ?
    """,(start_utc,end_utc))
    return [dict(r) for r in cur.fetchall()]

def median_or_none(values):
    vals=[v for v in values if v is not None]
    if not vals: return None
    try: return float(statistics.median(vals))
    except: return None

def summarize(rows):
    # overall + by class
    for_class = {"ALL": []}
    for r in rows:
        pc=(r.get("pattern_class") or "RAPID").upper()
        for_class.setdefault(pc, []).append(r)
        for_class["ALL"].append(r)
    out={}
    for k, lst in for_class.items():
        count=len(lst)
        tp=sum(1 for r in lst if (r.get("outcome") or "").upper()=="TP")
        sl=sum(1 for r in lst if (r.get("outcome") or "").upper()=="SL")
        expired=sum(1 for r in lst if (r.get("outcome") or "").upper()=="EXPIRED")
        denom=tp+sl
        win_rate = (tp/denom) if denom>0 else 0.0
        confs=[(r.get("confidence") if r.get("confidence") is not None else None) for r in lst]
        # lifespan for resolved only
        lifesp=[]
        for r in lst:
            sa=r.get("signaled_at"); ra=r.get("resolved_at")
            if sa and ra and ra>=sa:
                lifesp.append((ra-sa)/60.0)
        out[k]={
            "count":count, "tp":tp, "sl":sl, "expired":expired,
            "win_rate":win_rate,
            "median_conf": median_or_none(confs),
            "median_lifespan_min": median_or_none(lifesp),
        }
    return out

def upsert_daily(conn, day_et, stats):
    cur=conn.cursor()
    for pc, s in stats.items():
        cur.execute("""
            INSERT INTO outcomes_daily(day_et,pattern_class,count,tp,sl,expired,win_rate,median_conf,median_lifespan_min)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(day_et,pattern_class) DO UPDATE SET
              count=excluded.count, tp=excluded.tp, sl=excluded.sl, expired=excluded.expired,
              win_rate=excluded.win_rate, median_conf=excluded.median_conf,
              median_lifespan_min=excluded.median_lifespan_min
        """,(day_et, pc, s["count"], s["tp"], s["sl"], s["expired"],
             s["win_rate"], s["median_conf"], s["median_lifespan_min"]))
    conn.commit()

def main():
    day_str=os.environ.get("AGG_DAY_ET")  # optional 'YYYY-MM-DD'
    day_et, start_utc, end_utc = et_day_bounds(day_str)
    conn=sqlite3.connect(DB)
    rows=fetch_rows(conn,start_utc,end_utc)
    stats=summarize(rows)
    upsert_daily(conn, day_et, stats)
    print(f"[DAILY-AGG] day={day_et} rows={len(rows)} ALL={stats.get('ALL')}")
if __name__=="__main__":
    main()