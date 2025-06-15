from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

# === Configuration ===
TELEGRAM_TOKEN = "7514837840:AAHpbmpQCOnXeiz-4QRTKehrgPLQiNqAGuo"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

app = Flask(__name__)

# === Helper to send message ===
def send_telegram_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(TELEGRAM_API_URL, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

# === Webhook Handler ===
@app.route("/", methods=["POST"])
def telegram_webhook():
    if request.method == "POST":
        data = request.get_json()

        if data and "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            # Command responses
            if text == "/status":
                send_telegram_message(chat_id, "✅ BITTEN is online and operational.")
            elif text == "/fire":
                send_telegram_message(chat_id, "🚀 FIRE command received. Strike executed.")
            elif text == "/session":
                now = datetime.utcnow().strftime("%H%M%S")
                send_telegram_message(chat_id, f"🛡️ New session started: HXSN-{now}")
            elif text == "/mission":
                send_telegram_message(chat_id, "🎯 Sniper scalp on XAUUSD @ London Open.\n💥 Tactical mission in progress.")

        return jsonify({"ok": True}), 200

# === Fallback for bad methods ===
@app.route("/", methods=["GET"])
def fallback():
    return "🐍 BITTEN system is live. Awaiting command."

# === Start App ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
