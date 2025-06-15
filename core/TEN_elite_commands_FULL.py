"""Locked Operational Flask Core v1
This module exposes a simple Flask API used by the HydraX bot system.
It binds to 0.0.0.0 on port 5000 by default so the service can be reliably
restarted via ``pkill -f TEN_elite_commands_FULL.py && python3 TEN_elite_commands_FULL.py``.
"""

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
    data = request.get_json(silent=True) or {}
    payload = {
        "symbol": data.get("symbol"),
        "volume": data.get("volume"),
        "sl": data.get("sl"),
        "tp": data.get("tp"),
        "comment": data.get("comment"),
        "action": data.get("action")
    }

    if not all(payload.values()):
        return jsonify({"status": "error", "message": "Missing trade parameters"}), 400

    try:
        resp = requests.post("http://127.0.0.1:9000", json=payload)
        resp.raise_for_status()
        try:
            result = resp.json()
        except ValueError:
            result = resp.text
        return jsonify({"status": "success", "result": result}), 200
    except requests.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/dev", methods=["POST"])
def dev():
    if request.headers.get("X-Dev-Key") != "SECRET123":
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    command = data.get("command")

    if command == "status":
        return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}), 200
    elif command == "testfire":
        payload = {
            "symbol": data.get("symbol"),
            "volume": data.get("volume"),
            "sl": data.get("sl"),
            "tp": data.get("tp"),
            "comment": data.get("comment"),
            "action": data.get("action")
        }

        if not all(payload.values()):
            return jsonify({"status": "error", "message": "Missing trade parameters"}), 400

        try:
            resp = requests.post("http://127.0.0.1:9000", json=payload)
            resp.raise_for_status()
            try:
                result = resp.json()
            except ValueError:
                result = resp.text
            return jsonify({"status": "success", "result": result}), 200
        except requests.RequestException as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    elif command == "reload":
        os.system("systemctl restart hydrax || true")
        return jsonify({"status": "reloaded"}), 200
    else:
        return jsonify({"status": "error", "message": "Unknown command"}), 400

if __name__ == "__main__":
    # Bind to 0.0.0.0 on port 5000 unless overridden by the PORT env variable.
    default_port = 5000
    port_str = os.environ.get("PORT") or os.environ.get("FLASK_RUN_PORT")
    try:
        port = int(port_str) if port_str else default_port
    except (TypeError, ValueError):
        port = default_port

    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

"""
Sample curl tests (replace 127.0.0.1 if accessing remotely):

    curl http://127.0.0.1:5000/status

    curl -X POST http://127.0.0.1:5000/fire \
         -H "Content-Type: application/json" \
         -d '{"symbol":"XAUUSD","volume":1,"sl":2330,"tp":2340,"comment":"test","action":"buy"}'

    curl -X POST http://127.0.0.1:5000/dev \
         -H "X-Dev-Key: SECRET123" \
         -H "Content-Type: application/json" \
         -d '{"command":"status"}'
"""

