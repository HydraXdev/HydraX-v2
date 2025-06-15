from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "7514837840:AAHpbmpQCOnXeiz-4QRTKehrgPLQiNqAGuo"
SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        reply = f"✅ Echo: {text}"
        requests.post(SEND_URL, json={"chat_id": chat_id, "text": reply})
    return {"ok": True}, 200

@app.route("/", methods=["GET"])
def home():
    return "🚀 Webhook test server running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
