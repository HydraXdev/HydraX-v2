#!/usr/bin/env python3
"""
Quick Start Script for BITTEN Live Signals
This starts the existing signal flow system with proper webapp integration
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_signals():
    """Start the signal system using existing components"""
    logger.info("Starting BITTEN Signal System...")
    
    try:
        # Import and start the complete signal flow v3 (latest version)
        from src.bitten_core.complete_signal_flow_v3 import main as signal_main
        
        logger.info("Using Complete Signal Flow v3...")
        
        # The existing system should handle everything:
        # - Signal generation
        # - Telegram alerts with webapp buttons
        # - Trade tracking
        # - Mission briefings
        
        await signal_main()
        
    except ImportError:
        logger.warning("V3 not available, trying V2...")
        
        try:
            from src.bitten_core.complete_signal_flow_v2 import SignalFlow
            
            signal_flow = SignalFlow()
            logger.info("Starting Signal Flow v2...")
            
            # Start the flow
            await signal_flow.run()
            
        except ImportError:
            logger.warning("V2 not available, trying V1...")
            
            from src.bitten_core.complete_signal_flow import CompleteSignalFlow
            
            flow = CompleteSignalFlow()
            logger.info("Starting Signal Flow v1...")
            
            # Start monitoring
            await flow.start_live_monitoring()
    
    except Exception as e:
        logger.error(f"Failed to start signal system: {e}")
        
        # Fallback to simple signal start
        logger.info("Trying simple signal start...")
        
        from src.bitten_core.advanced_signal_integration import AdvancedSignalIntegration
        from src.bitten_core.tradermade_client import TraderMadeClient
        
        # Initialize components
        integration = AdvancedSignalIntegration()
        market_client = TraderMadeClient()
        
        # Start monitoring
        await integration.start_monitoring()


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════╗
    ║    BITTEN SIGNALS - STARTING NOW! 🚀     ║
    ╚══════════════════════════════════════════╝
    
    Starting live signal generation...
    Signals will appear in your Telegram chat.
    
    Press Ctrl+C to stop.
    """)
    
    try:
        asyncio.run(start_signals())
    except KeyboardInterrupt:
        logger.info("\nSignal system stopped by user")
    except Exception as e:
        logger.error(f"Signal system error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()