from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='/root/HydraX-v2/.env')

app = Flask(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

@app.route('/status', methods=['GET', 'POST'])
def status():
    if request.method == 'GET':
        return "HydraX webhook live", 200

    try:
        data = request.get_json(force=True)
        msg = data.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip().lower()

        print("[HydraX] Command received:", text)

        reply = {
            "/status": "HydraX operational. Systems normal.",
            "/start": "Commander, HydraX is online.",
            "/mode": "Current mode: SNIPER."
        }.get(text, f"Command not recognized: {text}")

        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply}
        )
        print(f"[Telegram] {response.status_code} - {response.text}")

    except Exception as e:
        print("[HydraX] ERROR:", str(e))

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
