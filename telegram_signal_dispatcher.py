#!/usr/bin/env python3
"""
PHASE 2.5: Telegram Signal Dispatcher
Sends mission alerts to group AFTER mission creation
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_mission_alert_to_group(mission_data):
    """
    Phase 2.5: Send formatted mission alert to Telegram group
    This happens AFTER mission creation but BEFORE user fires
    """
    try:
        # Extract mission details
        symbol = mission_data['symbol']
        direction = mission_data['direction']
        signal_id = mission_data['signal_id']
        confidence = mission_data['confidence']
        signal_type = mission_data.get('signal_type', 'RAPID_ASSAULT')
        
        # Extract CITADEL score (fallback to 7.5 if not available)
        citadel_score = mission_data.get('shield_score', 7.5)
        
        # Determine alert format and button based on signal type
        if signal_type == 'SNIPER_OPS' or confidence >= 85:
            # SNIPER OPS format with CITADEL shield symbol
            alert_message = f"⚡ SNIPER OPS ⚡ [{confidence}%]\n🛡️ {symbol} ELITE ACCESS [CITADEL: {citadel_score}/10]"
            button_text = "VIEW INTEL"
        else:
            # RAPID ASSAULT format with CITADEL shield symbol
            alert_message = f"🔫 RAPID ASSAULT [{confidence}%]\n🛡️ {symbol} STRIKE 💥 [CITADEL: {citadel_score}/10]"
            button_text = "MISSION BRIEF"

        # Send to group chat with inline button
        bot_token = "7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w"
        group_chat_id = "-1002581996861"  # BITTEN group chat
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": group_chat_id,
            "text": alert_message,
            "reply_markup": {
                "inline_keyboard": [[{
                    "text": button_text,
                    "url": f"https://joinbitten.com/hud?signal={signal_id}"
                }]]
            },
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Mission alert sent to group: {symbol} {direction}")
            return True
        else:
            logger.error(f"❌ Failed to send mission alert: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending mission alert: {e}")
        return False

def process_new_mission(mission_file_path):
    """
    Process a new mission file and send alert
    This is called after mission creation
    """
    try:
        with open(mission_file_path, 'r') as f:
            mission_data = json.load(f)
        
        logger.info(f"📋 Processing mission: {mission_data['signal_id']}")
        
        # Send alert to group
        success = send_mission_alert_to_group(mission_data)
        
        if success:
            # Mark mission as alerted
            mission_data['telegram_alerted'] = True
            mission_data['alert_time'] = datetime.now().isoformat()
            
            with open(mission_file_path, 'w') as f:
                json.dump(mission_data, f, indent=2)
                
        return success
        
    except Exception as e:
        logger.error(f"❌ Error processing mission file: {e}")
        return False

if __name__ == '__main__':
    # Test with a sample mission
    # Test SNIPER OPS mission
    sniper_mission = {
        'signal_id': 'VENOM_UNFILTERED_EURUSD_SNIPER',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'confidence': 92,
        'shield_score': 9.2,
        'shield_class': 'SHIELD_APPROVED',
        'signal_type': 'SNIPER_OPS',
        'target_pips': 40,
        'stop_pips': 15,
        'risk_reward': 2.7
    }
    
    # Test RAPID ASSAULT mission
    rapid_mission = {
        'signal_id': 'VENOM_UNFILTERED_GBPUSD_RAPID',
        'symbol': 'GBPUSD',
        'direction': 'SELL',
        'confidence': 76,
        'shield_score': 7.3,
        'shield_class': 'SHIELD_ACTIVE',
        'signal_type': 'RAPID_ASSAULT',
        'target_pips': 20,
        'stop_pips': 10,
        'risk_reward': 2.0
    }
    
    logger.info("🧪 Testing mission alert system...")
    
    # Test SNIPER OPS alert
    logger.info("Testing SNIPER OPS alert...")
    success1 = send_mission_alert_to_group(sniper_mission)
    
    if success1:
        logger.info("✅ SNIPER OPS alert sent successfully!")
    else:
        logger.error("❌ SNIPER OPS alert failed!")
        
    import time
    time.sleep(2)  # Brief pause between tests
    
    # Test RAPID ASSAULT alert
    logger.info("Testing RAPID ASSAULT alert...")
    success2 = send_mission_alert_to_group(rapid_mission)
    
    if success2:
        logger.info("✅ RAPID ASSAULT alert sent successfully!")
    else:
        logger.error("❌ RAPID ASSAULT alert failed!")
        
    if success1 and success2:
        logger.info("🎯 All CITADEL-enhanced alerts sent successfully!")