#!/usr/bin/env python3
import sqlite3
import json
import time

DB = "/root/HydraX-v2/bitten.db"

def pip_size(sym):
    s = sym.upper()
    if s.endswith("JPY"): return 0.01
    if s.startswith("XAU"): return 0.1
    if s.startswith("XAG"): return 0.01
    return 0.0001

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
SELECT mission_id, payload_json
FROM missions
WHERE status='PENDING'
""")
rows = cur.fetchall()

updated = 0
for r in rows:
    try:
        p = json.loads(r["payload_json"] or "{}")
        
        # Handle nested signal structure
        signal = p.get("signal", p)
        
        sym = (signal.get("symbol") or "").upper()
        side = (signal.get("direction") or signal.get("side") or "").upper()
        entry = float(signal.get("entry_price") or signal.get("entry") or 0.0)
        spips = float(signal.get("stop_pips") or signal.get("sl_pips") or 0.0)
        tpips = float(signal.get("target_pips") or signal.get("tp_pips") or 0.0)
        sl_abs = float(signal.get("sl") or 0.0)
        tp_abs = float(signal.get("tp") or 0.0)

        if not sym or not side or (sl_abs > 0 and tp_abs > 0):
            continue  # nothing to do

        if entry <= 0:
            continue  # can't compute without entry

        pip = pip_size(sym)
        if side == "BUY":
            sl = entry - (spips * pip) if spips > 0 else 0.0
            tp = entry + (tpips * pip) if tpips > 0 else 0.0
        elif side == "SELL":
            sl = entry + (spips * pip) if spips > 0 else 0.0
            tp = entry - (tpips * pip) if tpips > 0 else 0.0
        else:
            continue

        if sl > 0 and tp > 0:
            signal["sl"] = round(sl, 6)
            signal["tp"] = round(tp, 6)
            if "signal" in p:
                p["signal"] = signal
            else:
                p["sl"] = round(sl, 6)
                p["tp"] = round(tp, 6)
            cur.execute("UPDATE missions SET payload_json=? WHERE mission_id=?",
                        (json.dumps(p, separators=(',', ':')), r["mission_id"]))
            updated += 1
            print(f"Updated {r['mission_id']}: SL={sl:.5f}, TP={tp:.5f}")
    except Exception as e:
        print(f"Error processing {r['mission_id']}: {e}")
        continue

conn.commit()
print(f"\nTotal missions updated with absolute SL/TP: {updated}")