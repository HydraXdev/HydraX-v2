#!/usr/bin/env python3
"""
🔒 DATA INTEGRITY ENFORCER - ZERO TOLERANCE FOR FAKE DATA
Permanent enforcement layer that crashes any process attempting to use simulated data
"""

import sys
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

class DataIntegrityEnforcer:
    """Nuclear option data integrity enforcement - crashes on fake data"""
    
    # BANNED PHRASES - INSTANT CRASH IF FOUND
    BANNED_PHRASES = [
        "source\": \"simulated",
        "result_source\": \"synthetic", 
        "confidence\": 110.0",
        "backtest",
        "venom_results.json",
        "source\": \"test_data",
        "source\": \"simulation",
        "fake",
        "synthetic",
        "placeholder",
        "mock_data",
        "71 consecutive losses",
        "losses\": 71",
        "pips\": 1000"
    ]
    
    # BANNED SOURCE VALUES
    BANNED_SOURCES = [
        "simulated", "synthetic", "test_data", "simulation", 
        "fake", "mock", "placeholder", "backtest"
    ]
    
    # SUSPICIOUS PATTERNS
    SUSPICIOUS_PATTERNS = [
        {"confidence": 110.0},  # Impossible confidence
        {"profit": 1000.0, "source": None},  # High profit without source
        {"win_rate": 100.0},  # Perfect win rate
        {"losses": 71},  # Exact fake loss count
        {"pips": 1000}  # Exact fake pip count
    ]
    
    def __init__(self, telegram_bot_token: str = None, alert_user_id: str = "7176191872"):
        self.bot_token = telegram_bot_token or self._get_bot_token()
        self.alert_user_id = alert_user_id
        
    def _get_bot_token(self) -> str:
        """Get bot token from config"""
        try:
            config_path = Path("/root/HydraX-v2/config.json")
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                return config.get("BOT_TOKEN", "")
        except:
            pass
        return ""
    
    def send_critical_alert(self, message: str, data: Dict = None):
        """Send critical alert via Telegram"""
        try:
            if self.bot_token:
                alert_text = f"🚨 **CRITICAL DATA INTEGRITY VIOLATION** 🚨\n\n{message}"
                if data:
                    alert_text += f"\n\nViolating data:\n```json\n{json.dumps(data, indent=2)}\n```"
                    
                requests.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    json={
                        "chat_id": self.alert_user_id,
                        "text": alert_text,
                        "parse_mode": "Markdown"
                    },
                    timeout=5
                )
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def validate_signal_data(self, data: Dict[str, Any], source_context: str = "unknown") -> None:
        """
        NUCLEAR VALIDATION - CRASHES PROCESS IF FAKE DATA DETECTED
        
        Args:
            data: Signal data to validate
            source_context: Context where data originated
            
        Raises:
            SystemExit: IMMEDIATELY if fake data detected
        """
        
        # Convert to string for phrase checking
        data_str = json.dumps(data, indent=2).lower()
        
        # Check for banned phrases
        for banned_phrase in self.BANNED_PHRASES:
            if banned_phrase.lower() in data_str:
                error_msg = f"BANNED PHRASE DETECTED: '{banned_phrase}' in {source_context}"
                self.send_critical_alert(error_msg, data)
                logger.critical(error_msg)
                sys.exit(1)  # NUCLEAR OPTION - CRASH IMMEDIATELY
        
        # Check source field specifically
        source = data.get("source", data.get("result_source", ""))
        if source and str(source).lower() in self.BANNED_SOURCES:
            error_msg = f"BANNED SOURCE DETECTED: '{source}' in {source_context}"
            self.send_critical_alert(error_msg, data)
            logger.critical(error_msg)
            sys.exit(1)  # NUCLEAR OPTION - CRASH IMMEDIATELY
            
        # Check for missing source on important data
        if any(key in data for key in ["profit", "win_rate", "confidence", "signal_id"]):
            if not data.get("source") and not data.get("result_source"):
                error_msg = f"MISSING SOURCE FIELD in critical data from {source_context}"
                self.send_critical_alert(error_msg, data)
                logger.critical(error_msg)
                sys.exit(1)  # NUCLEAR OPTION - CRASH IMMEDIATELY
        
        # Check suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if all(data.get(k) == v for k, v in pattern.items()):
                error_msg = f"SUSPICIOUS PATTERN DETECTED: {pattern} in {source_context}"
                self.send_critical_alert(error_msg, data)
                logger.critical(error_msg)
                sys.exit(1)  # NUCLEAR OPTION - CRASH IMMEDIATELY
    
    def validate_file_content(self, file_path: str) -> None:
        """
        Validate file content for fake data - CRASHES if found
        
        Args:
            file_path: Path to file to validate
            
        Raises:
            SystemExit: IMMEDIATELY if fake data detected
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read().lower()
                
            # Check for banned phrases in file content
            for banned_phrase in self.BANNED_PHRASES:
                if banned_phrase.lower() in content:
                    error_msg = f"BANNED PHRASE IN FILE: '{banned_phrase}' found in {file_path}"
                    self.send_critical_alert(error_msg, {"file": file_path, "phrase": banned_phrase})
                    logger.critical(error_msg)
                    sys.exit(1)  # NUCLEAR OPTION - CRASH IMMEDIATELY
                    
            # If it's a JSON file, validate structure
            if file_path.endswith('.json') or file_path.endswith('.jsonl'):
                try:
                    if file_path.endswith('.jsonl'):
                        # Handle JSONL files line by line
                        with open(file_path, 'r') as f:
                            for line_num, line in enumerate(f, 1):
                                if line.strip():
                                    line_data = json.loads(line)
                                    self.validate_signal_data(line_data, f"{file_path}:line_{line_num}")
                    else:
                        # Handle regular JSON files
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        if isinstance(data, dict):
                            self.validate_signal_data(data, file_path)
                        elif isinstance(data, list):
                            for i, item in enumerate(data):
                                if isinstance(item, dict):
                                    self.validate_signal_data(item, f"{file_path}[{i}]")
                except json.JSONDecodeError:
                    # Not valid JSON, but no fake data detected in content
                    pass
                    
        except FileNotFoundError:
            # File doesn't exist, that's fine
            pass
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")

# GLOBAL ENFORCER INSTANCE
ENFORCER = DataIntegrityEnforcer()

def assert_no_fake_data(data: Dict[str, Any], context: str = "unknown") -> None:
    """
    ASSERT STATEMENT TO CRASH PROCESS ON FAKE DATA
    Use this in any process that handles signal data
    
    Args:
        data: Data to validate
        context: Context for debugging
        
    Raises:
        SystemExit: IMMEDIATELY if fake data detected
    """
    ENFORCER.validate_signal_data(data, context)

def assert_file_integrity(file_path: str) -> None:
    """
    ASSERT STATEMENT TO CRASH PROCESS IF FILE CONTAINS FAKE DATA
    Use this before reading any data files
    
    Args:
        file_path: File to validate
        
    Raises:
        SystemExit: IMMEDIATELY if fake data detected
    """
    ENFORCER.validate_file_content(file_path)

def validate_truth_log_only(data: Dict[str, Any]) -> None:
    """
    Enforce that data comes from truth_log.jsonl ONLY
    
    Args:
        data: Signal data to validate
        
    Raises:
        SystemExit: If data doesn't have truth log source
    """
    source = data.get("source", data.get("result_source", ""))
    valid_sources = ["truth_log.jsonl", "venom_scalp_master", "demo_venom_v8"]
    
    if source not in valid_sources:
        error_msg = f"DATA NOT FROM APPROVED SOURCE: source='{source}' (must be one of {valid_sources})"
        ENFORCER.send_critical_alert(error_msg, data)
        logger.critical(error_msg)
        sys.exit(1)  # NUCLEAR OPTION - CRASH IMMEDIATELY

if __name__ == "__main__":
    # Test the enforcer
    print("🧪 Testing Data Integrity Enforcer...")
    
    # Test valid data
    try:
        valid_data = {
            "signal_id": "VENOM_EURUSD_001", 
            "source": "truth_log.jsonl",
            "profit": 50.0,
            "confidence": 89.5
        }
        assert_no_fake_data(valid_data, "test_valid")
        print("✅ Valid data passed")
    except SystemExit:
        print("❌ Valid data failed - PROBLEM!")
    
    # Test banned phrase (should crash)
    try:
        fake_data = {"source": "simulated", "profit": 100.0}
        assert_no_fake_data(fake_data, "test_fake")
        print("❌ Fake data passed - ENFORCER FAILED!")
    except SystemExit:
        print("✅ Fake data blocked - ENFORCER WORKING!")
    
    print("🔒 Data Integrity Enforcer test complete")