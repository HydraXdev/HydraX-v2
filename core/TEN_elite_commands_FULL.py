from flask import Flask, request
import os
import json
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "🐾 BITTEN system is live. Awaiting command."

@app.route("/status", methods=["GET", "POST"])
def status():
    return {
        "status": "✅ BITTEN online.",
        "tactical_mode": "🎯 SNIPER",
        "health": "🐾 Stable",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/fire", methods=["POST"])
def fire():
    return {
        "signal": "🚀 FIRE initiated.",
        "action": "⚔️ Strike executed.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/setmode", methods=["POST"])
def set_mode():
    data = request.get_json(silent=True)
    mode = data.get("mode", "UNKNOWN").upper() if data else "UNKNOWN"
    return {
        "confirmation": f"🔁 Tactical Mode is now {mode}",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/debug", methods=["POST"])
def debug():
    return {
        "debug": "🛠 Debugging initialized.",
        "scan": "📡 Running diagnostics...",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/ping", methods=["POST"])
def ping():
    return {"ping": "pong"}

@app.route("/rank", methods=["POST"])
def rank():
    return {
        "rank": "🎖 Sergeant",
        "next_rank": "🎖 Lieutenant (XP: 1200)",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/kills", methods=["POST"])
def kills():
    return {
        "confirmed_kills": "💥 54 trades won",
        "success_rate": "81%",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/leaderboard", methods=["POST"])
def leaderboard():
    return {
        "top_3": [
            {"user": "SniperX", "score": 1289},
            {"user": "FXGhost", "score": 1190},
            {"user": "BitViper", "score": 1145}
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/session", methods=["POST"])
def session():
    return {
        "session_id": "HXSN-" + datetime.utcnow().strftime("%H%M%S"),
        "mission": "🛡 Protect the account. One shot, one win.",
        "status": "Active",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/mission", methods=["POST"])
def mission():
    return {
        "briefing": "🎯 Sniper scalp on XAUUSD @ London Open",
        "reward": "💰 22 XP",
        "tactical_focus": "🧠 Spread awareness. No late entries.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
@app.route("/", methods=["POST"])
def root_fallback():
    return "⚠️ POST to / not supported. Try /status instead.", 200
