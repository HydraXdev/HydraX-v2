#!/usr/bin/env python3
"""
Unified Tracking Bridge - Single source of truth for all ML systems
Syncs data between optimized_tracking.jsonl and comprehensive_tracking.jsonl
"""

import json
import time
import os
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedTrackingBridge:
    def __init__(self):
        self.primary_file = "/root/HydraX-v2/optimized_tracking.jsonl"
        self.secondary_files = [
            "/root/HydraX-v2/comprehensive_tracking.jsonl",
            "/root/HydraX-v2/logs/comprehensive_tracking.jsonl",
            "/root/HydraX-v2/truth_log.jsonl"
        ]
        
        # Ensure all directories exist
        for file_path in self.secondary_files:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    def sync_files(self):
        """Sync primary file to all secondary locations"""
        if not os.path.exists(self.primary_file):
            logger.warning(f"Primary file {self.primary_file} does not exist")
            return
        
        # Read primary file
        with open(self.primary_file, 'r') as f:
            primary_lines = f.readlines()
        
        # Sync to secondary files
        for secondary_file in self.secondary_files:
            try:
                # Read existing secondary content
                existing_lines = []
                if os.path.exists(secondary_file):
                    with open(secondary_file, 'r') as f:
                        existing_lines = f.readlines()
                
                # Find new lines
                new_lines = primary_lines[len(existing_lines):]
                
                if new_lines:
                    # Append new lines
                    with open(secondary_file, 'a') as f:
                        f.writelines(new_lines)
                    logger.info(f"Synced {len(new_lines)} new entries to {secondary_file}")
                    
            except Exception as e:
                logger.error(f"Error syncing to {secondary_file}: {e}")
    
    def monitor_and_sync(self):
        """Monitor primary file and sync changes"""
        logger.info("Starting Unified Tracking Bridge...")
        logger.info(f"Primary: {self.primary_file}")
        logger.info(f"Secondaries: {self.secondary_files}")
        
        last_size = 0
        
        while True:
            try:
                # Check if primary file has grown
                if os.path.exists(self.primary_file):
                    current_size = os.path.getsize(self.primary_file)
                    if current_size > last_size:
                        self.sync_files()
                        last_size = current_size
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                logger.info("Bridge shutdown requested")
                break
            except Exception as e:
                logger.error(f"Bridge error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bridge = UnifiedTrackingBridge()
    bridge.monitor_and_sync()