#!/usr/bin/env python3
"""
Start ZMQ Infrastructure for HydraX
Manages ZMQ receiver and integrates with existing VENOM pipeline
"""

import os
import sys
import time
import subprocess
import signal
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ZMQInfrastructure')

class ZMQInfrastructureManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        
        # ZMQ configuration
        self.zmq_endpoint = os.environ.get('ZMQ_ENDPOINT', 'tcp://192.168.1.100:5555')
        self.mt5_host = os.environ.get('MT5_HOST', '192.168.1.100')
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        
    def check_dependencies(self):
        """Check required dependencies"""
        try:
            import zmq
            import flask
            import cachetools
            logger.info("✅ All dependencies available")
            return True
        except ImportError as e:
            logger.error(f"❌ Missing dependency: {e}")
            logger.info("Install with: pip install pyzmq flask cachetools")
            return False
            
    def stop_old_services(self):
        """Stop old HTTP-based services"""
        logger.info("Stopping old HTTP-based services...")
        
        # Kill old market data receiver
        try:
            subprocess.run(['pkill', '-f', 'market_data_receiver'], check=False)
            logger.info("✅ Stopped old market data receiver")
        except:
            pass
            
        # Kill old streaming receiver
        try:
            subprocess.run(['pkill', '-f', 'market_data_receiver_streaming'], check=False)
            logger.info("✅ Stopped old streaming receiver")
        except:
            pass
            
        time.sleep(2)
        
    def start_zmq_receiver(self):
        """Start ZMQ market data receiver"""
        logger.info(f"Starting ZMQ receiver connected to {self.zmq_endpoint}...")
        
        env = os.environ.copy()
        env['ZMQ_ENDPOINT'] = self.zmq_endpoint
        
        process = subprocess.Popen(
            [sys.executable, 'zmq_market_data_receiver.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes['zmq_receiver'] = process
        logger.info(f"✅ ZMQ receiver started (PID: {process.pid})")
        
        # Wait for startup
        time.sleep(3)
        
        # Check if running
        if process.poll() is None:
            logger.info("✅ ZMQ receiver is running")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ ZMQ receiver failed to start: {stderr}")
            return False
            
    def restart_venom_stream(self):
        """Restart VENOM stream to use new data source"""
        logger.info("Restarting VENOM stream pipeline...")
        
        # Kill existing VENOM stream
        try:
            subprocess.run(['pkill', '-f', 'venom_stream_pipeline'], check=False)
            time.sleep(2)
        except:
            pass
            
        # Start VENOM stream
        process = subprocess.Popen(
            [sys.executable, 'venom_stream_pipeline.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes['venom_stream'] = process
        logger.info(f"✅ VENOM stream started (PID: {process.pid})")
        
        return process.poll() is None
        
    def check_data_flow(self):
        """Verify data is flowing through the system"""
        import requests
        
        logger.info("Checking data flow...")
        time.sleep(5)  # Give system time to receive data
        
        try:
            # Check health endpoint
            resp = requests.get('http://localhost:8001/market-data/health', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('active_symbols', 0) > 0:
                    logger.info(f"✅ Data flowing: {data['active_symbols']} active symbols")
                    return True
                else:
                    logger.warning("⚠️ No active symbols yet")
            else:
                logger.error(f"❌ Health check failed: {resp.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Cannot verify data flow: {e}")
            
        return False
        
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            
            for name, process in self.processes.items():
                if process.poll() is not None:
                    logger.error(f"❌ {name} crashed - restarting...")
                    
                    if name == 'zmq_receiver':
                        self.start_zmq_receiver()
                    elif name == 'venom_stream':
                        self.restart_venom_stream()
                        
    def run(self):
        """Main execution"""
        logger.info("=" * 60)
        logger.info("Starting ZMQ Infrastructure for HydraX")
        logger.info("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
            
        # Stop old services
        self.stop_old_services()
        
        # Start ZMQ receiver
        if not self.start_zmq_receiver():
            return False
            
        # Restart VENOM stream
        if not self.restart_venom_stream():
            logger.warning("VENOM stream failed to start")
            
        # Check data flow
        if self.check_data_flow():
            logger.info("🚀 ZMQ infrastructure is operational!")
        else:
            logger.warning("⚠️ Data flow not yet established")
            
        # Monitor processes
        logger.info("Monitoring processes... Press Ctrl+C to stop")
        self.monitor_processes()
        
        return True
        
    def shutdown(self):
        """Shutdown all processes"""
        self.running = False
        
        logger.info("Shutting down ZMQ infrastructure...")
        
        for name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                
        logger.info("✅ Shutdown complete")


if __name__ == '__main__':
    # Configuration hints
    print("\nZMQ Infrastructure Configuration:")
    print("-" * 40)
    print("Set these environment variables:")
    print(f"  ZMQ_ENDPOINT - ZMQ publisher address (default: tcp://192.168.1.100:5555)")
    print(f"  MT5_HOST - MT5 server IP address")
    print("\nExample:")
    print("  export ZMQ_ENDPOINT=tcp://192.168.1.100:5555")
    print("  python3 start_zmq_infrastructure.py")
    print("-" * 40)
    print()
    
    manager = ZMQInfrastructureManager()
    success = manager.run()
    
    sys.exit(0 if success else 1)