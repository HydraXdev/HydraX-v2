3from flask import Flask, request
import os
import json
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def root_fallback():
    if request.method == "GET":
        return "🚦 BITTEN system is live. Awaiting command.", 200
    elif request.method == "POST":
        return "✅ POST to root received from Telegram.", 200

@app.route("/status", methods=["GET", "POST"])
def status():
    return {
        "status": "✅ BITTEN online.",
        "tactical_mode": "🎯 SNIPER",
        "health": "💓 Stable",
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
    data = request.json
    mode = data.get("mode", "SNIPER")
    return {
        "message": f"🎛️ Tactical mode updated to {mode}.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/debug", methods=["POST"])
def debug():
    return {
        "debug": "🧠 All systems green.",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/ping", methods=["GET", "POST"])
def ping():
    return "🏓 pong", 200

@app.route("/rank", methods=["POST"])
def rank():
    return {
        "rank": "🪖 Elite Operative",
        "xp": 9284,
        "level": "Apex",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/kills", methods=["POST"])
def kills():
    return {
        "total_kills": 74,
        "last_hit": "🎯 XAUUSD scalp @ 3:15 PM",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/leaderboard", methods=["POST"])
def leaderboard():
    return {
        "top_trader": "🧠 Bit the Cat",
        "score": 9944,
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
