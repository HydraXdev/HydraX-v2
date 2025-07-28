#!/usr/bin/env python3
"""
VENOM Activity Logger - Centralized heartbeat logging system
Logs all VENOM ecosystem activity in JSONL format
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock

class VenomActivityLogger:
    """Centralized logging system for VENOM ecosystem heartbeat monitoring"""
    
    def __init__(self, log_file_path: str = "/root/HydraX-v2/logs/venom_activity.log"):
        self.log_file_path = log_file_path
        self.lock = Lock()
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # Set up standard logging for errors
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Internal method to log events in JSONL format"""
        try:
            with self.lock:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "event_type": event_type,
                    **data
                }
                
                with open(self.log_file_path, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                    
        except Exception as e:
            self.logger.error(f"Failed to log VENOM activity: {e}")
    
    def log_feed_monitor_start(self, container_name: str, status: str = "starting") -> None:
        """Log VenomFeedMonitor startup events"""
        self._log_event("feed_monitor_start", {
            "component": "VenomFeedMonitor",
            "container_name": container_name,
            "status": status,
            "message": f"VenomFeedMonitor started for container {container_name}"
        })
    
    def log_feed_monitor_heartbeat(self, container_name: str, health_status: Dict[str, Any]) -> None:
        """Log VenomFeedMonitor health check heartbeats"""
        self._log_event("feed_monitor_heartbeat", {
            "component": "VenomFeedMonitor", 
            "container_name": container_name,
            "health_status": health_status
        })
    
    def log_venom_signal_generated(self, signal_data: Dict[str, Any]) -> None:
        """Log when VENOM engine generates a signal"""
        self._log_event("venom_signal_generated", {
            "component": "VenomEngine",
            "signal_id": signal_data.get("signal_id"),
            "symbol": signal_data.get("symbol"),
            "direction": signal_data.get("direction"),
            "confidence": signal_data.get("confidence"),
            "signal_type": signal_data.get("signal_type"),
            "quality": signal_data.get("quality"),
            "message": f"VENOM generated {signal_data.get('signal_type', 'signal')} for {signal_data.get('symbol')}"
        })
    
    def log_signal_to_core(self, signal_id: str, core_status: str, additional_data: Optional[Dict[str, Any]] = None) -> None:
        """Log when signal is passed to Core system"""
        log_data = {
            "component": "CoreIntegration",
            "signal_id": signal_id,
            "core_status": core_status,
            "message": f"Signal {signal_id} passed to Core with status: {core_status}"
        }
        
        if additional_data:
            log_data.update(additional_data)
            
        self._log_event("signal_to_core", log_data)
    
    def log_engine_status(self, engine_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log general engine status updates"""
        log_data = {
            "component": engine_name,
            "status": status,
            "message": f"{engine_name} status: {status}"
        }
        
        if details:
            log_data.update(details)
            
        self._log_event("engine_status", log_data)
    
    def log_error(self, component: str, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Log error events in the VENOM ecosystem"""
        log_data = {
            "component": component,
            "error_message": error_message,
            "severity": "error"
        }
        
        if error_details:
            log_data.update(error_details)
            
        self._log_event("error", log_data)

# Global logger instance
venom_logger = VenomActivityLogger()

# Convenience functions for easy import
def log_feed_monitor_start(container_name: str, status: str = "starting") -> None:
    venom_logger.log_feed_monitor_start(container_name, status)

def log_feed_monitor_heartbeat(container_name: str, health_status: Dict[str, Any]) -> None:
    venom_logger.log_feed_monitor_heartbeat(container_name, health_status)

def log_venom_signal_generated(signal_data: Dict[str, Any]) -> None:
    venom_logger.log_venom_signal_generated(signal_data)

def log_signal_to_core(signal_id: str, core_status: str, additional_data: Optional[Dict[str, Any]] = None) -> None:
    venom_logger.log_signal_to_core(signal_id, core_status, additional_data)

def log_engine_status(engine_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    venom_logger.log_engine_status(engine_name, status, details)

def log_error(component: str, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
    venom_logger.log_error(component, error_message, error_details)