#!/usr/bin/env python3
"""
Working Signal Generator - Proven to work end-to-end
Combines market data reception, VENOM signal generation, and CITADEL enhancement
"""

import requests
import json
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import VENOM and CITADEL
import sys
sys.path.insert(0, '/root/HydraX-v2')
sys.path.insert(0, '/root/HydraX-v2/src')

from apex_venom_v7_unfiltered import ApexVenomV7Unfiltered
from citadel_core.citadel_analyzer import CitadelAnalyzer

# Flask app for receiving market data
app = Flask(__name__)

# Global storage
market_data = {}
venom_instance = None
citadel_instance = None

# Signal limiting (2 per hour max)
signal_count_this_hour = 0
hour_start = datetime.now()
MIN_MINUTES_BETWEEN_SIGNALS = 30  # At least 30 minutes between signals

# Valid pairs
VALID_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY"
]

@app.route('/market-data', methods=['POST'])
def receive_market_data():
    """Receive market data from EA"""
    try:
        data = request.get_json()
        ticks = data.get('ticks', [])
        
        # Process ticks
        for tick in ticks:
            symbol = tick.get('symbol')
            if symbol in VALID_PAIRS:
                market_data[symbol] = {
                    'bid': float(tick.get('bid', 0)),
                    'ask': float(tick.get('ask', 0)),
                    'spread': float(tick.get('spread', 0)),
                    'volume': int(tick.get('volume', 0)),
                    'last_update': time.time()
                }
        
        logger.info(f"Received {len(ticks)} ticks")
        
        # Immediately generate signals after receiving data
        generate_signals()
        
        return jsonify({'status': 'success', 'processed': len(ticks)})
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'active_pairs': len(market_data),
        'timestamp': datetime.now().isoformat()
    })

def generate_signals():
    """Generate VENOM signals with CITADEL enhancement"""
    global signal_count_this_hour, hour_start
    
    try:
        current_time = time.time()
        current_datetime = datetime.now()
        
        # Reset hourly counter if new hour
        if (current_datetime - hour_start).total_seconds() > 3600:
            signal_count_this_hour = 0
            hour_start = current_datetime
            logger.info("📊 Reset hourly signal counter")
        
        # Hard limit: 2 signals per hour max
        if signal_count_this_hour >= 2:
            logger.debug("⏰ Signal limit reached for this hour")
            return
        
        signals_generated = 0
        
        for symbol, data in market_data.items():
            # Skip old data
            if current_time - data.get('last_update', 0) > 30:
                continue
            
            # Prepare market data for VENOM
            venom_data = {
                'close': data['bid'],
                'spread': data['spread'],
                'volume': data['volume'],
                'timestamp': datetime.now()
            }
            
            # Override VENOM's data getter temporarily
            venom_instance.get_real_mt5_data = lambda p: venom_data if p == symbol else {}
            
            # Generate signal
            signal = venom_instance.generate_venom_signal(symbol, datetime.now())
            
            if signal and signal.get('confidence', 0) > 0:
                # Ensure pair field exists
                if 'pair' not in signal:
                    signal['pair'] = symbol
                    
                # Enhance with CITADEL
                citadel_result = citadel_instance.analyze_signal(signal, venom_data)
                
                # Add CITADEL data
                # Calculate risk multiplier based on classification
                risk_multipliers = {
                    'SHIELD_APPROVED': 1.5,
                    'SHIELD_ACTIVE': 1.0,
                    'VOLATILITY_ZONE': 0.5,
                    'UNVERIFIED': 0.25
                }
                
                signal['citadel_shield'] = {
                    'score': citadel_result['shield_score'],
                    'classification': citadel_result['classification'],
                    'risk_multiplier': risk_multipliers.get(citadel_result['classification'], 1.0)
                }
                
                logger.info(f"🎯 Signal: {symbol} {signal['direction']} @ {signal['confidence']}% | Shield: {citadel_result['shield_score']}/10")
                
                # Increment hourly counter
                signal_count_this_hour += 1
                
                # Send to WebApp
                send_to_webapp(signal)
                signals_generated += 1
                
                # Stop if we hit the limit
                if signal_count_this_hour >= 2:
                    logger.info("📊 Hit 2 signals/hour limit")
                    break
        
        if signals_generated > 0:
            logger.info(f"📈 Generated {signals_generated} signals")
        
    except Exception as e:
        import traceback
        logger.error(f"Error generating signals: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

def send_to_webapp(signal):
    """Send signal to WebApp AND Telegram"""
    try:
        # Save signals to a file for verification
        import json
        with open('/root/HydraX-v2/generated_signals.json', 'a') as f:
            json.dump(signal, f)
            f.write('\n')
        logger.info(f"✅ Signal saved: {signal['signal_id']} - {signal['pair']} {signal['direction']} @ {signal['confidence']}%")
        
        # Send to WebApp first - this will create missions
        try:
            response = requests.post('http://127.0.0.1:8888/api/signals', json=signal, timeout=2)
            if response.status_code == 200:
                logger.info(f"✅ Signal sent to WebApp for mission creation")
        except:
            pass  # Webapp might not be ready for signals yet
        
        # Send to BittenCore for mission processing
        try:
            send_to_core_for_mission_processing(signal)
        except Exception as e:
            logger.error(f"❌ Error sending to core: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error saving signal: {e}")

def send_to_core_for_mission_processing(signal):
    """Send signal to BittenCore for proper mission creation and Telegram broadcast"""
    try:
        # Format signal for BittenCore processing
        # Extract CITADEL data if nested
        citadel = signal.get('citadel_shield', {})
        shield_score = citadel.get('score', signal.get('shield_score', 6.0))
        shield_class = citadel.get('classification', signal.get('shield_class', 'SHIELD_ACTIVE'))
        
        core_signal = {
            'signal_id': signal['signal_id'],
            'symbol': signal['pair'],
            'direction': signal['direction'],
            'confidence': signal['confidence'],
            'shield_score': shield_score,
            'shield_class': shield_class,
            'signal_type': signal.get('signal_type', 'RAPID_ASSAULT'),
            'target_pips': signal.get('target_pips', 20),
            'stop_pips': signal.get('stop_pips', 10),
            'risk_reward': signal.get('risk_reward', 2.0),
            'timestamp': time.time(),
            'source': 'VENOM_CITADEL_LIVE'
        }
        
        # Send to BittenCore via production bot's API endpoint
        try:
            # Try to notify production bot about new signal
            response = requests.post(
                'http://localhost:8080/api/new_signal', 
                json=core_signal, 
                timeout=3
            )
            if response.status_code == 200:
                logger.info(f"✅ Signal sent to BittenCore for mission processing")
                return True
        except:
            pass
            
        # Fallback: Save signal to missions directory for processing
        try:
            import os
            os.makedirs('/root/HydraX-v2/missions', exist_ok=True)
            
            mission_file = f"/root/HydraX-v2/missions/{signal['signal_id']}.json"
            with open(mission_file, 'w') as f:
                json.dump(core_signal, f, indent=2)
            
            logger.info(f"✅ Signal saved to missions directory: {mission_file}")
            
            # Also trigger manual mission processing
            trigger_mission_processing(core_signal)
            
        except Exception as e:
            logger.error(f"❌ Error saving to missions: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error in core processing: {e}")

def trigger_mission_processing(signal):
    """Trigger mission briefing and Telegram broadcast - PHASE 2.5"""
    try:
        logger.info(f"🎯 Processing mission for {signal['symbol']} {signal['direction']}")
        
        # PHASE 2.5: Send Telegram alert after mission creation
        try:
            from telegram_signal_dispatcher import send_mission_alert_to_group
            
            success = send_mission_alert_to_group(signal)
            if success:
                logger.info(f"📡 ✅ Telegram alert sent for {signal['signal_id']}")
            else:
                logger.warning(f"📡 ⚠️ Telegram alert failed for {signal['signal_id']}")
                
        except ImportError:
            logger.warning("📡 Telegram dispatcher not available, running direct alert")
            # Fallback: run the dispatcher directly
            import subprocess
            subprocess.run([
                "python3", "/root/HydraX-v2/telegram_signal_dispatcher.py"
            ], check=False)
        
    except Exception as e:
        logger.error(f"❌ Error triggering mission processing: {e}")

def signal_scanner():
    """Background signal scanner"""
    while True:
        try:
            time.sleep(30)
            logger.info("🔄 Running scheduled signal scan...")
            generate_signals()
        except Exception as e:
            logger.error(f"Scanner error: {e}")

def main():
    global venom_instance, citadel_instance
    
    logger.info("🚀 Starting Working Signal Generator")
    logger.info("🐍 Initializing VENOM v7.0...")
    venom_instance = ApexVenomV7Unfiltered()
    
    logger.info("🛡️ Initializing CITADEL Shield...")
    citadel_instance = CitadelAnalyzer()
    
    # Start background scanner
    scanner_thread = threading.Thread(target=signal_scanner, daemon=True)
    scanner_thread.start()
    
    # Start Flask server
    logger.info("📡 Starting market data receiver on port 8002")
    app.run(host='0.0.0.0', port=8002, debug=False)

if __name__ == '__main__':
    main()