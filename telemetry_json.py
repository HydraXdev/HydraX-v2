# telemetry_json.py
import json, time, os

class JSONLogger:
    def __init__(self, path="/root/HydraX-v2/ultimate_core_crypto.jsonl"):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
    def log_signal(self, payload: dict):
        payload = dict(payload)
        payload.setdefault("ts", time.time())
        with open(self.path, "a") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")