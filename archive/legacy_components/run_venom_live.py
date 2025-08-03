#!/usr/bin/env python3
"""
Run VENOM v7.0 in live mode to generate trading signals
"""

import sys
import time
import random
from datetime import datetime
import logging

# Add src directory to path
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

from apex_venom_v7_unfiltered import ApexVenomV7Unfiltered
from venom_activity_logger import log_venom_signal_generated, log_engine_status

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_venom_live():
    """Run VENOM in live signal generation mode"""
    logger.info("🐍 Starting VENOM v7.0 LIVE Signal Generation")
    
    # Initialize VENOM
    venom = ApexVenomV7Unfiltered()
    
    # Log engine start
    log_engine_status("VENOM_LIVE", "started", {"pairs": len(venom.trading_pairs)})
    
    logger.info(f"🎯 Monitoring {len(venom.trading_pairs)} currency pairs")
    logger.info("⚡ Target: 25+ signals per day")
    logger.info("📊 Signal Types: RAPID_ASSAULT (1:2) and PRECISION_STRIKE (1:3)")
    
    # Signal generation loop
    signal_count = 0
    try:
        while True:
            # Get current timestamp
            timestamp = datetime.now()
            hour = timestamp.hour
            
            # Get session type
            session = venom.get_session_type(hour)
            logger.info(f"📍 Current Session: {session}")
            
            # Determine how many pairs to scan based on session
            if session == 'OVERLAP':
                pairs_to_scan = random.sample(venom.trading_pairs, k=min(10, len(venom.trading_pairs)))
            elif session in ['LONDON', 'NY']:
                pairs_to_scan = random.sample(venom.trading_pairs, k=min(8, len(venom.trading_pairs)))
            elif session == 'ASIAN':
                pairs_to_scan = random.sample(venom.trading_pairs, k=min(5, len(venom.trading_pairs)))
            else:  # OFF_HOURS
                pairs_to_scan = random.sample(venom.trading_pairs, k=min(3, len(venom.trading_pairs)))
            
            # Scan pairs for signals
            for pair in pairs_to_scan:
                signal = venom.generate_venom_signal(pair, timestamp)
                
                if signal:
                    signal_count += 1
                    logger.info(f"🎯 Signal #{signal_count} Generated!")
                    logger.info(f"   Pair: {signal['symbol']}")
                    logger.info(f"   Type: {signal['signal_type']}")
                    logger.info(f"   Direction: {signal['direction']}")
                    logger.info(f"   Confidence: {signal['confidence']}%")
                    logger.info(f"   Quality: {signal['quality']}")
                    logger.info(f"   Target/Stop: {signal['target_pips']}/{signal['stop_pips']} pips")
                    
                    # Log to VENOM activity log
                    log_venom_signal_generated(signal)
                    
                    # TODO: Send signal to BittenCore for processing
                    # For now, just log it
                    
            # Sleep before next scan
            if session in ['OVERLAP', 'LONDON', 'NY']:
                sleep_time = random.randint(60, 180)  # 1-3 minutes during active sessions
            else:
                sleep_time = random.randint(180, 300)  # 3-5 minutes during quiet sessions
                
            logger.info(f"💤 Sleeping for {sleep_time} seconds before next scan...")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 VENOM Live Signal Generation stopped by user")
        log_engine_status("VENOM_LIVE", "stopped", {"signals_generated": signal_count})
    except Exception as e:
        logger.error(f"❌ Error in VENOM live generation: {str(e)}")
        log_engine_status("VENOM_LIVE", "error", {"error": str(e)})
        raise

if __name__ == "__main__":
    run_venom_live()