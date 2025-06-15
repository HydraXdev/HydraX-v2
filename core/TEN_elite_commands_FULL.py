from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    message = data.get('message')

    if message:
        chat_id = message['chat']['id']
        text = message.get('text', '')

        # Explicit command handling
        if text == '/status':
            reply = "HydraX: All systems fully operational."
        elif text == '/mode':
            reply = "HydraX: Current tactical mode: FULL AUTO."
        elif text == '/start':
            reply = "HydraX: Commander, your system is live and ready."
        else:
            reply = f"Received Clearly: {text}"

        # Explicitly send reply to Telegram
        requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
                      json={'chat_id': chat_id, 'text': reply})

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
