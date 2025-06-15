from flask import Flask, request, jsonify
from datetime import datetime
import os
import requests

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "ðŸ¾ BITTEN system is live. Awaiting command."

@app.route("/status", methods=["GET", "POST"])
def status():
    return jsonify({
        "status": "âœ… BITTEN online.",
        "tactical_mode": "ðŸŽ¯ SNIPER",
        "health": "ðŸ§  Stable",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200

@app.route("/fire", methods=["POST"])
def fire():
    payload = {
        "symbol": "XAUUSD",
        "volume": 0.10,
        "sl": 1975.00,
        "tp": 1990.00,
        "comment": "HydraX Commander",
        "action": "buy"
    }
    try:
        resp = requests.post("http://127.0.0.1:9000", json=payload)
        resp.raise_for_status()
        return jsonify({"status": "success", "response": resp.text}), 200
    except requests.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
