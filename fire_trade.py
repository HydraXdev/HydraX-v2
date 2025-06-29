import argparse
import json
import subprocess
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", required=True)
parser.add_argument("--type", required=True)
parser.add_argument("--lot", type=float, required=True)
args = parser.parse_args()

payload = {
    "symbol": args.symbol,
    "type": args.type,
    "lot": args.lot
}

json_string = json.dumps(payload)

cmd = (
    f"sshpass -p 'UJl2Z3k1@KA?6MzDJ*qr1b?@RhREQk&u' "
    f"ssh -tt Administrator@3.145.84.187 "
    f"\"powershell -NoProfile -Command \\\"Set-Content -Path 'C:\\\\HydraBridge\\\\signal.json' -Value '{json_string}'\\\"\""
)

with open("/root/HydraX-v2/trade_debug.log", "a") as f:
    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing command:\\n{cmd}\\n")
    try:
        subprocess.run(cmd, shell=True, check=True)
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Trade injection succeeded.\\n")
    except subprocess.CalledProcessError as e:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Failed: {e}\\n")
