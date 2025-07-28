"""Locked Operational Flask Core v2
This module exposes a secure Flask API for the HydraX bot system.
- Binds to 0.0.0.0 on port 5000 by default
- Uses env vars for sensitive values
- Unified JSON response schema
- Hardened input validation
"""

from flask import Flask, request, jsonify
from datetime import datetime
import os
import requests
import json
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

BRIDGE_URL = os.environ.get("BRIDGE_URL") or "http://127.0.0.1:9000"
DEV_API_KEY = os.environ.get("DEV_API_KEY") or "SECRET123"
_default_log = os.path.join(os.path.dirname(__file__), "dev_log.txt")
LOG_FILE = os.environ.get("DEV_LOG_FILE") or _default_log

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

logging.basicConfig(level=logging.INFO)

def _validate_payload(payload, fields):
    for field in fields:
        value = payload.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return False, field
    return True, None

def _log_action(route, payload, result):
    """Append a single log line with timestamp, route, payload and result."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"[{timestamp}] {route} \u2192 {result.upper()} "
                f"{json.dumps(payload, separators=(',', ':'))}\n"
            )
    except Exception:
        # Logging failures should not affect API responses
        pass

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            return jsonify({"ok": True}), 200
        except Exception:
            logging.exception("Error on POST /")
            return jsonify({"ok": True}), 200
    return jsonify({
        "status": "ok",
        "data": {"message": "BITTEN system is live. Awaiting command."},
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200

@app.route("/status", methods=["GET", "POST"])
def status():
    return jsonify({
        "status": "ok",
        "data": {
            "message": "âœ… BITTEN online.",
            "tactical_mode": "ðŸŽ¯ SNIPER",
            "health": "ðŸ§  Stable"
        },
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
    valid, missing = _validate_payload(payload, payload.keys())
    if not valid:
        _log_action("/fire", payload, "error")
        return jsonify({
            "status": "error",
            "data": {"message": f"Missing {missing}"},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 400

    try:
        resp = requests.post(BRIDGE_URL, json=payload)
        resp.raise_for_status()
        try:
            result = resp.json()
        except ValueError:
            result = resp.text
        _log_action("/fire", payload, "ok")
        return jsonify({
            "status": "ok",
            "data": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200
    except requests.RequestException as e:
        _log_action("/fire", payload, "error")
        return jsonify({
            "status": "error",
            "data": {"message": str(e)},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

@app.route("/dev", methods=["POST"])
def dev():
    if request.headers.get("X-Dev-Key") != DEV_API_KEY:
        _log_action("/dev", {}, "error")
        return jsonify({
            "status": "error",
            "data": {"message": "Unauthorized"},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 401

    data = request.get_json(silent=True) or {}
    command = data.get("command")

    if command == "status":
        _log_action("/dev", data, "ok")
        return jsonify({
            "status": "ok",
            "data": {"message": "dev status acknowledged"},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    elif command == "testfire":
        payload = {
            "symbol": data.get("symbol"),
            "volume": data.get("volume"),
            "sl": data.get("sl"),
            "tp": data.get("tp"),
            "comment": data.get("comment"),
            "action": data.get("action")
        }
        valid, missing = _validate_payload(payload, payload.keys())
        if not valid:
            _log_action("/dev", payload, "error")
            return jsonify({
                "status": "error",
                "data": {"message": f"Missing {missing}"},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 400

        try:
            resp = requests.post(BRIDGE_URL, json=payload)
            resp.raise_for_status()
            try:
                result = resp.json()
            except ValueError:
                result = resp.text
            _log_action("/dev", payload, "ok")
            return jsonify({
                "status": "ok",
                "data": result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 200
        except requests.RequestException as e:
            _log_action("/dev", payload, "error")
            return jsonify({
                "status": "error",
                "data": {"message": str(e)},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 500

    elif command == "reload":
        os.system("systemctl restart hydrax || true")
        _log_action("/dev", data, "ok")
        return jsonify({
            "status": "ok",
            "data": {"message": "reloaded"},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    _log_action("/dev", data, "error")
    return jsonify({
        "status": "error",
        "data": {"message": "Unknown command"},
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 400

@app.route("/logs", methods=["GET"])
def logs():
    if request.headers.get("X-Dev-Key") != DEV_API_KEY:
        return jsonify({
            "status": "error",
            "data": {"message": "Unauthorized"},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 401

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f.readlines()]
        last_lines = lines[-50:]
        return jsonify({
            "status": "ok",
            "data": {"logs": last_lines},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200
    except FileNotFoundError:
        return jsonify({
            "status": "error",
            "data": {"message": "Log file not found"},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 404
    except Exception as e:
        return jsonify({
            "status": "error",
            "data": {"message": str(e)},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT") or os.environ.get("FLASK_RUN_PORT") or 5000)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
