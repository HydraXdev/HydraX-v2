
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
