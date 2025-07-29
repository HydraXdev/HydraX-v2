#!/usr/bin/env python3
"""
ENGINE TEST NODE - VENOM v7 with Expiry Timer Logic
Validates time-gated signals with MT5 tick triggers
"""

import json
import time
import threading
from datetime import datetime, timedelta
import os
import sys
import logging

# Add current directory to path for imports
sys.path.append('/root/HydraX-v2')

from apex_venom_v7_with_smart_timer import ApexVenomV7WithTimer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EngineTestNode:
    """Engine test node for VENOM v7 with expiry validation"""
    
    def __init__(self):
        self.engine = ApexVenomV7WithTimer()
        self.fire_path = "/mt5drop/engine_test/fire.txt"
        self.result_path = "/mt5drop/engine_test/trade_result.txt"
        self.active_signals = {}
        self.test_results = []
        
        logger.info("🧠 ENGINE TEST NODE INITIALIZED - VENOM v7 with Expiry Timer")
        
    def generate_test_signal(self):
        """Generate a test signal with expiry timer"""
        try:
            # Generate signal using VENOM v7
            import random
            test_pair = random.choice(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'])
            signal = self.engine.generate_venom_signal(test_pair, datetime.now())
            
            if signal:
                # Add expiry timer (convert minutes to seconds for testing)
                timer_minutes = signal.get('timer_minutes', 10)
                expires_in = max(10, int(timer_minutes * 60 / 6))  # Scale down for testing
                
                signal_with_timer = {
                    "symbol": signal.get('pair', 'EURUSD'),
                    "side": signal.get('direction', 'buy').lower(),
                    "lotsize": 0.01,  # Small test size
                    "tp": signal.get('tp_pips', 100),
                    "sl": signal.get('sl_pips', 50),
                    "expires_in": expires_in,
                    "signal_id": f"TEST_{int(time.time())}",
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"📊 Generated signal: {signal_with_timer['symbol']} {signal_with_timer['side'].upper()} (expires in {expires_in}s)")
                return signal_with_timer
                
        except Exception as e:
            logger.error(f"❌ Signal generation error: {e}")
            
        return None
    
    def fire_signal(self, signal):
        """Fire signal to MT5 and start monitoring"""
        try:
            signal_id = signal['signal_id']
            expires_in = signal['expires_in']
            
            # Write signal to fire.txt
            with open(self.fire_path, 'w') as f:
                json.dump(signal, f)
                
            logger.info(f"🔥 SIGNAL FIRED: {signal_id} - expires in {expires_in}s")
            
            # Start monitoring thread
            self.active_signals[signal_id] = {
                'signal': signal,
                'fired_at': time.time(),
                'expires_at': time.time() + expires_in,
                'status': 'active'
            }
            
            # Monitor in background
            threading.Thread(target=self.monitor_signal, args=(signal_id,), daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Signal fire error: {e}")
            return False
    
    def monitor_signal(self, signal_id):
        """Monitor signal for execution or expiry"""
        try:
            signal_data = self.active_signals[signal_id]
            expires_at = signal_data['expires_at']
            
            while time.time() < expires_at:
                # Check for trade result
                if os.path.exists(self.result_path):
                    try:
                        with open(self.result_path, 'r') as f:
                            result = json.load(f)
                            
                        # Signal executed successfully
                        execution_time = time.time() - signal_data['fired_at']
                        
                        logger.info(f"✅ SIGNAL EXECUTED: {signal_id} in {execution_time:.1f}s")
                        
                        signal_data['status'] = 'executed'
                        signal_data['execution_time'] = execution_time
                        signal_data['result'] = result
                        
                        self.test_results.append({
                            'signal_id': signal_id,
                            'status': 'success',
                            'execution_time': execution_time,
                            'expires_in': signal_data['signal']['expires_in'],
                            'result': result
                        })
                        
                        # Clean up result file for next signal
                        os.remove(self.result_path)
                        return
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Result file read error: {e}")
                
                time.sleep(0.5)  # Check every 500ms
            
            # Signal expired
            logger.warning(f"⏰ SIGNAL EXPIRED: {signal_id}")
            
            signal_data['status'] = 'expired'
            self.test_results.append({
                'signal_id': signal_id,
                'status': 'expired',
                'expires_in': signal_data['signal']['expires_in'],
                'reason': 'signal timed out'
            })
            
        except Exception as e:
            logger.error(f"❌ Signal monitoring error: {e}")
    
    def run_test_cycle(self, num_signals=5):
        """Run a complete test cycle"""
        logger.info(f"🚀 STARTING ENGINE TEST CYCLE - {num_signals} signals")
        
        for i in range(num_signals):
            try:
                # Generate signal
                signal = self.generate_test_signal()
                if not signal:
                    logger.warning(f"⚠️ Failed to generate signal {i+1}")
                    continue
                
                # Fire signal
                if self.fire_signal(signal):
                    logger.info(f"📊 Signal {i+1}/{num_signals} fired successfully")
                else:
                    logger.error(f"❌ Failed to fire signal {i+1}")
                
                # Wait between signals
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Test cycle error: {e}")
        
        # Wait for all signals to complete or expire
        logger.info("⏳ Waiting for all signals to complete...")
        time.sleep(30)
        
        # Print results
        self.print_test_results()
    
    def print_test_results(self):
        """Print comprehensive test results"""
        logger.info("📋 TEST RESULTS SUMMARY:")
        logger.info("=" * 50)
        
        executed = [r for r in self.test_results if r['status'] == 'success']
        expired = [r for r in self.test_results if r['status'] == 'expired']
        
        logger.info(f"✅ Executed: {len(executed)}")
        logger.info(f"⏰ Expired: {len(expired)}")
        logger.info(f"📊 Total: {len(self.test_results)}")
        
        if executed:
            avg_execution_time = sum(r['execution_time'] for r in executed) / len(executed)
            logger.info(f"⚡ Average execution time: {avg_execution_time:.1f}s")
        
        # Detailed results
        logger.info("\n📄 DETAILED RESULTS:")
        for result in self.test_results:
            if result['status'] == 'success':
                logger.info(f"  ✅ {result['signal_id']}: EXECUTED in {result['execution_time']:.1f}s")
            else:
                logger.info(f"  ⏰ {result['signal_id']}: EXPIRED after {result['expires_in']}s")

def main():
    """Main engine test function"""
    try:
        logger.info("🧠 LAUNCHING ENGINE TEST NODE - VENOM v7")
        
        # Initialize engine test node
        engine_node = EngineTestNode()
        
        # Run test cycle
        engine_node.run_test_cycle(num_signals=3)
        
        logger.info("🎯 ENGINE TEST COMPLETE")
        
    except Exception as e:
        logger.error(f"❌ Engine test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())