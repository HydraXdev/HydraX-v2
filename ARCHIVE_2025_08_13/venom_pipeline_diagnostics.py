#!/usr/bin/env python3
"""
🔍 BITTEN VENOM PIPELINE DIAGNOSTICS
Run a complete scan of the following:
1. VENOM stream process status
2. Truth log activity (last 10 entries)
3. CITADEL throttle and lockdown status
4. Market data injector + receiver health
5. Signal generation rate over past 6 hours
"""

from subprocess import run, PIPE
import json
import os
from datetime import datetime

def run_bash(cmd):
    result = run(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    return result.stdout.strip() or result.stderr.strip()

# 1. VENOM PROCESS STATUS
venom_status = run_bash("ps aux | grep venom_stream_pipeline.py | grep -v grep")

# 2. TRUTH LOG ENTRIES
truth_log_tail = run_bash("tail -n 10 /root/HydraX-v2/truth_log.jsonl")

# 3. CITADEL STATE CHECK
citadel_state = run_bash("cat /root/HydraX-v2/citadel_state.json")

# 4. MARKET DATA CHECK
market_data_raw = run_bash("curl -s http://localhost:8001/market-data/all?fast=true")
try:
    market_data = json.loads(market_data_raw)
    last_ticks = {k: v.get('timestamp', 'MISSING') for k, v in market_data.items()}
except:
    last_ticks = {"error": market_data_raw}

# 5. SIGNAL COUNT LAST 6 HOURS
mission_dir = "/root/HydraX-v2/missions/"
cutoff = datetime.now().timestamp() - (6 * 3600)
signal_count = 0

if os.path.exists(mission_dir):
    for f in os.listdir(mission_dir):
        path = os.path.join(mission_dir, f)
        if f.endswith(".json") and os.path.isfile(path):
            if os.path.getmtime(path) > cutoff:
                signal_count += 1
else:
    signal_count = "Directory not found"

# OUTPUT
report = {
    "VENOM Process": venom_status or "❌ VENOM not running",
    "Recent Truth Log": truth_log_tail,
    "Citadel State": citadel_state[:1000],  # partial for length
    "Market Data Timestamps": last_ticks,
    "Signal Count (last 6h)": signal_count
}
print(json.dumps(report, indent=2))