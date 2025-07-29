#!/usr/bin/env python3
"""
🔍 Signal Accuracy Monitor Startup Script
Starts the signal accuracy tracker monitoring service in the background
"""

import asyncio
import logging
import sys
import os

# Add paths for imports
sys.path.append('/root/HydraX-v2/src/bitten_core')

from signal_accuracy_tracker import signal_accuracy_tracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/signal_accuracy_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('SignalAccuracyMonitor')

async def main():
    """Start signal accuracy monitoring service"""
    
    print("🔍 Starting Signal Accuracy Tracker Monitor...")
    print("=" * 60)
    
    # Start monitoring service
    await signal_accuracy_tracker.start_monitoring()
    
    logger.info("✅ Signal Accuracy Tracker monitoring started")
    print("✅ Signal Accuracy Tracker monitoring started")
    
    # Show current status
    stats = signal_accuracy_tracker.get_theoretical_performance(24)
    print(f"📊 Current signals being tracked: {stats['total_signals']}")
    print(f"📈 Average TCS score: {stats['avg_tcs']:.1f}%")
    
    print()
    print("🏃 Monitor is now running in background...")
    print("📊 Tracking all signals for theoretical win rate analysis")
    print("🎯 Use this data to correlate TCS scores with actual performance")
    print()
    print("To stop: Press Ctrl+C")
    print("=" * 60)
    
    try:
        # Keep running indefinitely
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            # Log status periodically
            stats = signal_accuracy_tracker.get_theoretical_performance(24)
            if stats['total_signals'] > 0:
                logger.info(f"📊 Tracking {stats['total_signals']} signals, "
                          f"{stats['completed']} completed, "
                          f"win rate: {stats['theoretical_win_rate']:.1%}")
    
    except KeyboardInterrupt:
        logger.info("🛑 Signal accuracy monitor stopped by user")
        print("\n🛑 Signal accuracy monitor stopped")
        
    except Exception as e:
        logger.error(f"❌ Monitor error: {e}")
        print(f"\n❌ Monitor error: {e}")
    
    finally:
        # Stop monitoring
        await signal_accuracy_tracker.stop_monitoring()
        logger.info("🧹 Signal accuracy monitor shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())