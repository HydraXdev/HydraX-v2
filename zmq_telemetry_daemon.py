#!/usr/bin/env python3
"""
ZMQ Telemetry Receiver Daemon
Receives and processes telemetry from EA
"""

# ┌──────────────────────────────────────────────────────────────┐
# │ BITTEN ZMQ SYSTEM - DO NOT FALL BACK TO FILE/HTTP ROUTES    │
# │ Persistent ZMQ architecture is required                      │
# │ EA v7 connects directly via libzmq.dll to 134.199.204.67    │
# │ All command, telemetry, and feedback must use ZMQ sockets   │
# └──────────────────────────────────────────────────────────────┘

import signal
import sys
import time
from zmq_telemetry_service import TelemetryIngestionService, integrate_with_xp_system, integrate_with_risk_system

class TelemetryDaemon:
    def __init__(self):
        self.service = TelemetryIngestionService()
        self.running = True
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutting down telemetry daemon...")
        self.running = False
        
    def run(self):
        """Run the telemetry daemon"""
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Set up integrations
        xp_callback = integrate_with_xp_system()
        if xp_callback:
            self.service.set_xp_callback(xp_callback)
            
        risk_callback = integrate_with_risk_system()
        if risk_callback:
            self.service.set_risk_callback(risk_callback)
        
        try:
            self.service.start()
            print("✅ Telemetry receiver started successfully")
            print("📡 Monitoring port 5556 for telemetry and trade results")
            
            # Keep running and log stats
            while self.running:
                time.sleep(5)
                stats = self.service.get_stats()
                if stats['last_update']:
                    print(f"\r📊 Telemetry: {stats['telemetry_received']} | "
                          f"Trades: {stats['trade_results_received']} | "
                          f"Active users: {stats['active_users_count']}", end='', flush=True)
                    
        except Exception as e:
            print(f"\nDaemon error: {e}")
        finally:
            self.service.stop()
            print("\n✅ Telemetry daemon stopped")

if __name__ == "__main__":
    daemon = TelemetryDaemon()
    daemon.run()