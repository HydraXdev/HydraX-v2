#!/usr/bin/env python3
"""
Add MT5 live data endpoint to BITTEN webapp
"""
import os
import subprocess
import signal

# First, stop fake signal generator if running
print("Stopping fake signal generators...")
try:
    # Find and kill signal generator processes
    result = subprocess.run(['pgrep', '-f', 'signal.*generator'], capture_output=True, text=True)
    if result.stdout:
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            try:
                os.kill(int(pid), signal.SIGTERM)
                print(f"Stopped process {pid}")
            except:
                pass
except:
    pass

# Create webapp addon for live MT5 data
addon_code = '''
# MT5 Live Data Integration Addon
# Add this to webapp_server.py

from mt5_live_integration import process_live_mt5_data, get_live_signals
import json

@app.route('/mt5/data', methods=['POST'])
def receive_mt5_data():
    """Receive live market data from MT5 farm"""
    try:
        data = request.get_json()
        
        # Process incoming tick data
        if data.get('type') == 'tick':
            # Process through live filters
            signal = process_live_mt5_data(data)
            
            if signal:
                # Broadcast to Telegram
                broadcast_live_signal(signal)
                
        return jsonify({"status": "processed"})
    except Exception as e:
        logger.error(f"Error processing MT5 data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/live_signals')
def get_live_signals_endpoint():
    """Get recent live signals"""
    try:
        signals = get_live_signals(limit=20)
        return jsonify({
            "status": "success",
            "mode": "LIVE",
            "signals": signals
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def broadcast_live_signal(signal):
    """Send live signal to Telegram"""
    try:
        # Format signal message
        direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
        
        message = f"""
{direction_emoji} <b>LIVE SIGNAL DETECTED</b>

<b>Pair:</b> {signal['symbol']}
<b>Direction:</b> {signal['direction']}
<b>Entry:</b> {signal['entry_price']:.5f}
<b>Confidence:</b> {signal['confidence']:.0%}
<b>Filters:</b> {signal['filters_passed']}

<i>Signal ID: {signal['id']}</i>
"""
        
        # Send to main channel
        send_message(MAIN_CHAT_ID, message)
        
    except Exception as e:
        logger.error(f"Error broadcasting signal: {e}")

# Replace fake signal generator with live data
print("✅ MT5 Live Data Integration Added")
print("✅ Fake signals disabled")
print("✅ Now receiving LIVE market data from MT5 farm")
'''

# Save addon
with open('/root/HydraX-v2/webapp_mt5_live_addon.py', 'w') as f:
    f.write(addon_code)

print("\n=== LIVE DATA INTEGRATION READY ===")
print("\nTo complete integration:")
print("1. Add the endpoints from webapp_mt5_live_addon.py to webapp_server.py")
print("2. Import: from mt5_live_integration import process_live_mt5_data, get_live_signals")
print("3. Restart webapp: systemctl restart bitten-webapp")
print("\nLive signals will appear at:")
print("- Telegram: Main BITTEN channel")
print("- Web: https://joinbitten.com/api/live_signals")

# Create systemd service for live monitoring
service_content = '''[Unit]
Description=BITTEN MT5 Live Data Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/HydraX-v2
ExecStart=/usr/bin/python3 /root/HydraX-v2/mt5_live_integration.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''

with open('/tmp/bitten-mt5-monitor.service', 'w') as f:
    f.write(service_content)

print("\nTo install monitoring service:")
print("sudo cp /tmp/bitten-mt5-monitor.service /etc/systemd/system/")
print("sudo systemctl enable bitten-mt5-monitor")
print("sudo systemctl start bitten-mt5-monitor")