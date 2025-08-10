#!/usr/bin/env python3
"""
🚨 ELITE GUARD SIGNAL TIMEOUT SYSTEM
Emergency timeout monitoring for 2-hour signal closure
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict
import threading

logger = logging.getLogger('SignalTimeout')

def monitor_signal_timeout(signal: Dict):
    """Monitor signal timeout and auto-close after 2 hours"""
    try:
        signal_id = signal['signal_id']
        generated_at = datetime.fromisoformat(signal.get('generated_at', datetime.now().isoformat()))
        
        # Calculate timeout points
        expires_at = generated_at + timedelta(seconds=7200)  # 2 hours
        hard_close_at = generated_at + timedelta(seconds=7500)  # 2h5m
        
        logger.info(f"⏰ Timeout monitoring started for {signal_id}")
        logger.info(f"   Generated: {generated_at}")
        logger.info(f"   Expires: {expires_at}")
        logger.info(f"   Hard close: {hard_close_at}")
        
        # Sleep until 2-hour timeout
        timeout_seconds = (expires_at - datetime.now()).total_seconds()
        if timeout_seconds > 0:
            logger.info(f"⏳ Waiting {timeout_seconds:.0f}s until timeout for {signal_id}")
            time.sleep(timeout_seconds)
            
            # Check if signal is positive, close it
            logger.info(f"⏰ 2-hour timeout reached for {signal_id} - checking for positive close")
            attempt_positive_close(signal)
            
            # Sleep until hard close (5 more minutes)
            hard_close_seconds = (hard_close_at - datetime.now()).total_seconds()
            if hard_close_seconds > 0:
                logger.info(f"⏳ Waiting {hard_close_seconds:.0f}s until hard close for {signal_id}")
                time.sleep(hard_close_seconds)
                
            # Force close signal
            logger.info(f"🔒 Hard close (2h5m) reached for {signal_id} - force closing")
            force_close_signal(signal)
        else:
            logger.warning(f"⚠️ Signal {signal_id} already expired, force closing immediately")
            force_close_signal(signal)
            
    except Exception as e:
        logger.error(f"❌ Error monitoring signal timeout: {e}")
        
def attempt_positive_close(signal: Dict):
    """Attempt to close signal if it's in positive territory"""
    try:
        signal_id = signal['signal_id']
        logger.info(f"💚 Attempting positive close check for {signal_id}")
        
        # TODO: Implement current price check vs entry price
        # For now, just mark as attempted
        
        attempt_entry = {
            'signal_id': signal_id,
            'action': 'positive_close_attempt',
            'attempted_at': datetime.now().isoformat(),
            'runtime_hours': 2.0,
            'note': 'System attempted positive close at 2-hour mark'
        }
        
        with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
            f.write(json.dumps(attempt_entry) + '\n')
            
        logger.info(f"💚 Positive close attempt logged for {signal_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in positive close attempt: {e}")
        
def force_close_signal(signal: Dict):
    """Force close signal after 2h5m regardless of outcome"""
    try:
        signal_id = signal['signal_id']
        
        # Update truth log with timeout closure
        timeout_entry = {
            'signal_id': signal_id,
            'status': 'timeout_closed',
            'completed': True,
            'outcome': 'timeout',
            'completed_at': datetime.now().isoformat(),
            'runtime_seconds': 7500,  # 2h5m
            'runtime_hours': 2.083,
            'exit_type': 'timeout',
            'pips_result': 0,  # Unknown at timeout
            'timeout_reason': 'automatic_closure_after_2h5m'
        }
        
        with open('/root/HydraX-v2/truth_log.jsonl', 'a') as f:
            f.write(json.dumps(timeout_entry) + '\n')
            
        logger.info(f"🔒 Signal {signal_id} force-closed due to timeout")
        logger.info(f"   Runtime: 2h5m (7500 seconds)")
        logger.info(f"   Outcome: TIMEOUT")
        
    except Exception as e:
        logger.error(f"❌ Error force closing signal: {e}")

def start_timeout_monitor(signal: Dict):
    """Start timeout monitoring thread for a signal"""
    try:
        timeout_thread = threading.Thread(
            target=monitor_signal_timeout, 
            args=(signal,), 
            daemon=True,
            name=f"TimeoutMonitor_{signal['signal_id']}"
        )
        timeout_thread.start()
        
        logger.info(f"🕒 Timeout monitor thread started for {signal['signal_id']}")
        
    except Exception as e:
        logger.error(f"❌ Error starting timeout monitor: {e}")

if __name__ == "__main__":
    # Test the timeout system
    test_signal = {
        'signal_id': 'TEST_TIMEOUT_12345',
        'pair': 'EURUSD',
        'direction': 'BUY',
        'generated_at': datetime.now().isoformat()
    }
    
    print("🧪 Testing signal timeout system...")
    start_timeout_monitor(test_signal)
    
    # Keep main thread alive for testing
    time.sleep(10)
    print("✅ Test completed - timeout monitor is running")