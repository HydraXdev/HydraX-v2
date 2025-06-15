from flask import Flask, request
import os
import json
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        return "⚠️ POST received on root. Try /status instead.", 200
    return "🐾 BITTEN system is live. Awaiting command."

@app.route("/status", methods=["GET", "POST"])
def status():
    return {
        "status": "✅ BITTEN online.",
        "tactical_mode": "🎯 SNIPER",
        "health": "🧠 Stable",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/fire", methods=["POST"])
def fire():
    return {
        "signal": "🚀 FIRE initiated.",
        "action": "⚔️ Strike executed.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/set_mode", methods=["POST"])
def set_mode():
    data = request.json or {}
    mode = data.get("mode", "unknown")
    return {
        "result": f"Tactical mode set to {mode}",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/debug", methods=["POST"])
def debug():
    return {
        "debug": "🛠️ System diagnostics passed.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/ping", methods=["POST"])
def ping():
    return {
        "pong": True,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/rank", methods=["POST"])
def rank():
    return {
        "rank": "🐍 Python Tier 1 Operator",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/kills", methods=["POST"])
def kills():
    return {
        "kills": 14,
        "accuracy": "88%",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/leaderboard", methods=["POST"])
def leaderboard():
    return {
        "top": [
            {"user": "Hydra", "xp": 888},
            {"user": "Bit", "xp": 777}
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/session", methods=["POST"])
def session():
    return {
        "session_id": "HXSN-" + datetime.utcnow().strftime("%H%M%S"),
        "mission": "🛡️ Protect the account. One shot, one win.",
        "status": "Active",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/mission", methods=["POST"])
def mission():
    return {
        "briefing": "🎯 Sniper scalp on XAUUSD @ London Open",
        "reward": "🪙 22 XP",
        "tactical_focus": "🧠 Spread awareness. No late entries.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
