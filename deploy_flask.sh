#!/bin/bash

echo "🚀 Starting HydraX Flask App Deployment..."

apt update && apt install -y python3-pip
pip3 install flask python-dotenv

echo "➡️  Current Directory: $(pwd)"
echo "➡️  Files:"
ls -l

echo "🔧 Running Flask app: TEN_elite_commands_FULL.py"
nohup python3 TEN_elite_commands_FULL.py &

echo "✅ Deployment complete. Flask is now running in the background."
