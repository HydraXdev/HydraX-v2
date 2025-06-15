from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "🐾 BITTEN system is live. Awaiting command."

@app.route("/status", methods=["GET", "POST"])
def status():
    return jsonify({
        "status": "✅ BITTEN online.",
        "tactical_mode": "🎯 SNIPER",
        "health": "🧠 Stable",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
