#!/usr/bin/env python3
"""
Test script for APEX Telegram Connector
"""

import asyncio
import logging
from apex_telegram_connector import ApexTelegramConnector, Config

# Set up test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_signal_parsing():
    """Test signal parsing functionality"""
    logger.info("Testing signal parsing...")
    
    connector = ApexTelegramConnector()
    
    # Test signal line
    test_line = "2025-07-14 12:39:41,362 - APEX v5.0 LIVE - INFO - 🎯 SIGNAL #1: EURUSD SELL TCS:76%"
    
    signal = connector.parse_signal_line(test_line)
    if signal:
        logger.info(f"Successfully parsed signal: {signal}")
        
        # Test urgency level
        urgency = connector.get_urgency_level(signal['tcs_score'])
        logger.info(f"Urgency level: {urgency}")
        
        # Test mission generation (using fallback)
        try:
            from src.bitten_core.mission_briefing_generator_v5 import generate_mission
        except ImportError:
            try:
                from bitten_core.mission_briefing_generator_v5 import generate_mission
            except ImportError:
                # Use fallback
                import time
                import json
                from datetime import datetime, timedelta
                from pathlib import Path
                
                def generate_mission(signal, user_id):
                    mission_id = f"{user_id}_{int(time.time())}"
                    mission = {
                        "mission_id": mission_id,
                        "user_id": user_id,
                        "symbol": signal["symbol"],
                        "type": signal["type"],
                        "tp": signal["tp"],
                        "sl": signal["sl"],
                        "tcs": signal["tcs_score"],
                        "risk": 1.5,
                        "account_balance": 2913.25,
                        "lot_size": 0.12,
                        "timestamp": datetime.utcnow().isoformat(),
                        "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                        "status": "pending"
                    }
                    
                    # Create missions directory
                    missions_dir = Path("./missions")
                    missions_dir.mkdir(exist_ok=True)
                    
                    # Save mission file
                    mission_file = missions_dir / f"{mission_id}.json"
                    with open(mission_file, "w") as f:
                        json.dump(mission, f, indent=2)
                    
                    return mission
        
        # Generate test mission
        mission = generate_mission(signal, Config.CHAT_ID)
        logger.info(f"Generated mission: {mission['mission_id']}")
        
        # Test message formatting
        message = connector.format_telegram_message(signal, mission, urgency)
        logger.info(f"Formatted message:\n{message}")
        
        return True
    else:
        logger.error("Failed to parse signal")
        return False

async def test_cooldown():
    """Test cooldown mechanism"""
    logger.info("Testing cooldown mechanism...")
    
    connector = ApexTelegramConnector()
    
    signal_key = "EURUSD_sell_76"
    
    # First check should return True
    result1 = connector.should_send_signal(signal_key)
    logger.info(f"First check: {result1}")
    
    # Second check should return False (cooldown active)
    result2 = connector.should_send_signal(signal_key)
    logger.info(f"Second check: {result2}")
    
    return result1 and not result2

def test_configuration():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    logger.info(f"Bot token configured: {Config.BOT_TOKEN is not None}")
    logger.info(f"Chat ID: {Config.CHAT_ID}")
    logger.info(f"Log file: {Config.LOG_FILE}")
    logger.info(f"WebApp URL: {Config.WEBAPP_URL}")
    logger.info(f"Cooldown: {Config.COOLDOWN_SECONDS}s")
    
    return True

async def main():
    """Run all tests"""
    logger.info("Starting APEX Telegram Connector Tests...")
    
    tests = [
        ("Configuration", test_configuration),
        ("Signal Parsing", test_signal_parsing),
        ("Cooldown", test_cooldown),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Print results
    logger.info("\n" + "="*50)
    logger.info("TEST RESULTS")
    logger.info("="*50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    logger.info(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())