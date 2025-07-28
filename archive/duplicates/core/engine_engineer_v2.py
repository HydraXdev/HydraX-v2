import json
import os
from datetime import datetime

class EngineEngineer:
    def __init__(self, config_path="./logs/config.json", log_path="./logs/fire_log.json", mission_dir="./missions/"):
        self.config_path = config_path
        self.log_path = log_path
        self.mission_dir = mission_dir
        self.load_config()
        self.load_logs()

    def load_config(self):
        try:
            with open(self.config_path) as f:
                self.config = json.load(f)
        except:
            self.config = {}

    def load_logs(self):
        try:
            with open(self.log_path) as f:
                self.logs = json.load(f)
        except:
            self.logs = []

    def status(self):
        return {
            "config_loaded": bool(self.config),
            "logs_loaded": len(self.logs),
            "missions_tracked": len(self.get_all_missions())
        }

    def last_trade(self, user_id):
        trades = [t for t in self.logs if t["user_id"] == user_id]
        return trades[-1] if trades else None

    def restart_engine(self):
        # Placeholder for future restart logic
        return "Restart command dispatched (stub)"

    def get_all_missions(self):
        if not os.path.exists(self.mission_dir):
            return []
        missions = []
        for filename in os.listdir(self.mission_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.mission_dir, filename)) as f:
                        mission = json.load(f)
                        missions.append(mission)
                except:
                    continue
        return missions

    def get_user_missions(self, user_id):
        return [m for m in self.get_all_missions() if m.get("user_id") == user_id]

    def get_expired_missions(self):
        now_ts = int(datetime.utcnow().timestamp())
        return [m for m in self.get_all_missions() if m.get("expires_timestamp", 0) < now_ts]

    def get_active_missions(self):
        now_ts = int(datetime.utcnow().timestamp())
        return [m for m in self.get_all_missions() if m.get("expires_timestamp", 0) >= now_ts]

    def user_mission_summary(self, user_id):
        active = [m for m in self.get_user_missions(user_id) if m["status"] == "pending"]
        expired = [m for m in self.get_user_missions(user_id) if m["status"] == "pending" and m["expires_timestamp"] < int(datetime.utcnow().timestamp())]
        fired = [m for m in self.get_user_missions(user_id) if m["status"] == "fired"]
        return {
            "user_id": user_id,
            "active_missions": len(active),
            "expired_missions": len(expired),
            "fired_missions": len(fired)
        }