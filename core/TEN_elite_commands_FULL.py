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
