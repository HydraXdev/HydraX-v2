#!/usr/bin/env python3
"""
🛡️ CITADEL Adaptive TCS Throttling System
Implements pressure release mechanism to prevent signal droughts over 90 minutes

Features:
- Monitors truth_log.jsonl for last successful signal timestamp
- Dynamically lowers TCS threshold based on drought duration
- 5-tier threshold decay system (82.0 → 79.5 → 77.0 → 74.5 → RESET)
- Integrates with citadel_state.json for live config sync
- Comprehensive logging to citadel_throttle.log
- API endpoint for real-time status monitoring
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CITADEL_THROTTLE - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TCSThresholdConfig:
    """Configuration for TCS threshold levels"""
    baseline: float = 70.0  # TESTING - Lowered from 82.0
    tier_1: float = 67.5  # >20 minutes [TESTING]
    tier_2: float = 65.0  # >35 minutes [TESTING]
    tier_3: float = 62.5  # >50 minutes [TESTING]
    reset_after_minutes: int = 90
    
@dataclass
class AdaptiveThrottleState:
    """Current state of adaptive throttling system"""
    current_tcs: float
    last_signal_timestamp: Optional[float]
    threshold_changed_at: float
    minutes_since_signal: float
    tier_level: int
    reason_code: str
    next_decay_in_minutes: Optional[float]
    pressure_override_active: bool

class CitadelAdaptiveThrottle:
    """CITADEL Adaptive TCS Throttling System"""
    
    def __init__(self, 
                 truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl",
                 citadel_state_path: str = "/root/HydraX-v2/citadel_state.json",
                 throttle_log_path: str = "/root/HydraX-v2/citadel_throttle.log",
                 commander_user_id: str = "7176191872"):
        
        self.truth_log_path = Path(truth_log_path)
        self.citadel_state_path = Path(citadel_state_path)
        self.throttle_log_path = Path(throttle_log_path)
        self.commander_user_id = commander_user_id
        
        # Configuration
        self.config = TCSThresholdConfig()
        
        # Current state
        self.current_state = AdaptiveThrottleState(
            current_tcs=self.config.baseline,
            last_signal_timestamp=None,
            threshold_changed_at=time.time(),
            minutes_since_signal=0.0,
            tier_level=0,
            reason_code="BASELINE",
            next_decay_in_minutes=None,
            pressure_override_active=False
        )
        
        # Monitoring control
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 30  # Check every 30 seconds
        
        # TCS decay schedule (minutes since last signal → TCS threshold)
        self.decay_schedule = [
            (0, self.config.baseline, "BASELINE"),
            (20, self.config.tier_1, "TIER_1_PRESSURE_RELEASE"),
            (35, self.config.tier_2, "TIER_2_ENHANCED_HUNTING"),
            (50, self.config.tier_3, "TIER_3_AGGRESSIVE_SEEKING"),
            (90, self.config.baseline, "TIER_4_PRESSURE_OVERRIDE_RESET")
        ]
        
        # Initialize logging
        self._setup_throttle_logging()
        
        # Load initial state
        self._initialize_state()
        
        logger.info("🛡️ CITADEL Adaptive TCS Throttling System initialized")
        logger.info(f"📁 Truth log: {self.truth_log_path}")
        logger.info(f"📁 Citadel state: {self.citadel_state_path}")
        logger.info(f"📁 Throttle log: {self.throttle_log_path}")
    
    def _setup_throttle_logging(self):
        """Setup dedicated throttle logging"""
        # Create throttle-specific logger
        self.throttle_logger = logging.getLogger('citadel_throttle')
        self.throttle_logger.setLevel(logging.INFO)
        
        # Create file handler for throttle log
        file_handler = logging.FileHandler(self.throttle_log_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        if not self.throttle_logger.handlers:
            self.throttle_logger.addHandler(file_handler)
    
    def _initialize_state(self):
        """Initialize throttle state from existing data"""
        try:
            # Find last signal from truth log
            last_signal_time = self._get_last_signal_timestamp()
            
            if last_signal_time:
                self.current_state.last_signal_timestamp = last_signal_time
                self.current_state.minutes_since_signal = (time.time() - last_signal_time) / 60
                
                # Determine current TCS level based on time elapsed
                self._update_tcs_threshold()
                
                self.throttle_logger.info(f"INIT - Last signal: {datetime.fromtimestamp(last_signal_time).isoformat()}, Minutes ago: {self.current_state.minutes_since_signal:.1f}, TCS: {self.current_state.current_tcs}")
            else:
                self.throttle_logger.info("INIT - No signals found in truth log, using baseline TCS")
                
        except Exception as e:
            logger.error(f"❌ Initialization error: {e}")
            self.throttle_logger.error(f"INIT_ERROR - {e}")
    
    def _get_last_signal_timestamp(self) -> Optional[float]:
        """Get timestamp of last successful signal from truth log"""
        if not self.truth_log_path.exists():
            return None
        
        try:
            last_timestamp = None
            
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        
                        # Look for completed signals (with result or status)
                        if ('result' in record or 'status' in record):
                            timestamp_str = record.get('timestamp')
                            
                            if timestamp_str:
                                # Handle different timestamp formats
                                if isinstance(timestamp_str, str):
                                    if timestamp_str.endswith('+00:00'):
                                        # ISO format with timezone
                                        dt = datetime.fromisoformat(timestamp_str.replace('+00:00', '+00:00'))
                                        timestamp = dt.timestamp()
                                    else:
                                        # Try parsing as ISO format
                                        dt = datetime.fromisoformat(timestamp_str)
                                        timestamp = dt.timestamp()
                                else:
                                    # Already a timestamp
                                    timestamp = float(timestamp_str)
                                
                                if last_timestamp is None or timestamp > last_timestamp:
                                    last_timestamp = timestamp
                                    
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        continue
            
            return last_timestamp
            
        except Exception as e:
            logger.error(f"❌ Error reading truth log: {e}")
            return None
    
    def _update_tcs_threshold(self):
        """Update TCS threshold based on time since last signal"""
        if self.current_state.last_signal_timestamp is None:
            return
        
        # Calculate minutes since last signal
        minutes_elapsed = (time.time() - self.current_state.last_signal_timestamp) / 60
        self.current_state.minutes_since_signal = minutes_elapsed
        
        # Find appropriate threshold tier
        new_tcs = self.config.baseline
        new_tier = 0
        new_reason = "BASELINE"
        next_decay_minutes = None
        pressure_override = False
        
        for i, (threshold_minutes, tcs_value, reason) in enumerate(self.decay_schedule):
            if minutes_elapsed >= threshold_minutes:
                new_tcs = tcs_value
                new_tier = i
                new_reason = reason
                
                # Handle pressure override reset
                if threshold_minutes == self.config.reset_after_minutes:
                    pressure_override = True
                    # Reset last signal timestamp to trigger new baseline
                    self.current_state.last_signal_timestamp = time.time()
                    minutes_elapsed = 0
                    self.current_state.minutes_since_signal = 0
                    new_tcs = self.config.baseline
                    new_tier = 0
                    new_reason = "PRESSURE_OVERRIDE_RESET"
                    break
                    
                # Calculate next decay time
                if i + 1 < len(self.decay_schedule):
                    next_threshold_minutes = self.decay_schedule[i + 1][0]
                    next_decay_minutes = next_threshold_minutes - minutes_elapsed
                    if next_decay_minutes < 0:
                        next_decay_minutes = None
        
        # Check if threshold changed
        if abs(new_tcs - self.current_state.current_tcs) > 0.1 or new_reason != self.current_state.reason_code:
            old_tcs = self.current_state.current_tcs
            old_reason = self.current_state.reason_code
            
            # Update state
            self.current_state.current_tcs = new_tcs
            self.current_state.tier_level = new_tier
            self.current_state.reason_code = new_reason
            self.current_state.threshold_changed_at = time.time()
            self.current_state.next_decay_in_minutes = next_decay_minutes
            self.current_state.pressure_override_active = pressure_override
            
            # Log threshold change
            self.throttle_logger.info(f"TCS_CHANGE - {old_tcs:.1f} → {new_tcs:.1f} | Reason: {old_reason} → {new_reason} | Minutes: {minutes_elapsed:.1f} | Tier: {new_tier}")
            
            # Update citadel state
            self._update_citadel_state()
            
            # Send pressure override alert if applicable
            if pressure_override:
                self._send_pressure_override_alert()
                
            logger.info(f"🎯 TCS threshold updated: {old_tcs:.1f} → {new_tcs:.1f} ({new_reason})")
        
        else:
            # Update next decay time even if threshold didn't change
            self.current_state.next_decay_in_minutes = next_decay_minutes
    
    def _update_citadel_state(self):
        """Update citadel_state.json with current TCS threshold"""
        try:
            # Load existing citadel state
            citadel_data = {}
            if self.citadel_state_path.exists():
                with open(self.citadel_state_path, 'r') as f:
                    citadel_data = json.load(f)
            
            # Ensure global section exists
            if 'global' not in citadel_data:
                citadel_data['global'] = {}
            
            # Update adaptive throttle section
            citadel_data['global']['adaptive_throttle'] = {
                'tcs_threshold': self.current_state.current_tcs,
                'tier_level': self.current_state.tier_level,
                'reason_code': self.current_state.reason_code,
                'last_signal_timestamp': self.current_state.last_signal_timestamp,
                'minutes_since_signal': self.current_state.minutes_since_signal,
                'threshold_changed_at': self.current_state.threshold_changed_at,
                'next_decay_in_minutes': self.current_state.next_decay_in_minutes,
                'pressure_override_active': self.current_state.pressure_override_active,
                'updated_at': time.time()
            }
            
            # Save updated state
            with open(self.citadel_state_path, 'w') as f:
                json.dump(citadel_data, f, indent=2)
                
            self.throttle_logger.info(f"CITADEL_UPDATE - TCS: {self.current_state.current_tcs} | Tier: {self.current_state.tier_level} | Reason: {self.current_state.reason_code}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update citadel state: {e}")
            self.throttle_logger.error(f"CITADEL_UPDATE_ERROR - {e}")
    
    def _send_pressure_override_alert(self):
        """Send Telegram alert for pressure override activation"""
        try:
            # Load bot token
            bot_token = self._load_bot_token()
            if not bot_token:
                logger.warning("⚠️ No bot token - skipping pressure override alert")
                return
            
            message = (
                "🚨 **CITADEL PRESSURE OVERRIDE ACTIVATED** 🚨\n\n"
                f"Signal drought exceeded 90 minutes\n"
                f"TCS threshold RESET to {self.config.baseline}%\n"
                f"Pressure release system engaged\n\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"Last signal: {self.current_state.minutes_since_signal:.1f} minutes ago"
            )
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': self.commander_user_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("📱 Pressure override alert sent successfully")
                self.throttle_logger.info("ALERT_SENT - Pressure override notification delivered")
            else:
                logger.error(f"❌ Pressure override alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send pressure override alert: {e}")
    
    def _load_bot_token(self) -> Optional[str]:
        """Load Telegram bot token"""
        try:
            import sys
            sys.path.append('/root/HydraX-v2')
            from config_loader import get_bot_token
            return get_bot_token()
        except Exception:
            return None
    
    def on_signal_completed(self, signal_id: str, timestamp: Optional[float] = None):
        """Handle notification of completed signal"""
        if timestamp is None:
            timestamp = time.time()
            
        # Reset to baseline immediately
        old_tcs = self.current_state.current_tcs
        old_reason = self.current_state.reason_code
        
        self.current_state.current_tcs = self.config.baseline
        self.current_state.last_signal_timestamp = timestamp
        self.current_state.minutes_since_signal = 0.0
        self.current_state.tier_level = 0
        self.current_state.reason_code = "SIGNAL_RESET"
        self.current_state.threshold_changed_at = time.time()
        self.current_state.next_decay_in_minutes = 20.0  # Next decay in 20 minutes
        self.current_state.pressure_override_active = False
        
        # Log reset
        self.throttle_logger.info(f"SIGNAL_RESET - {old_tcs:.1f} → {self.config.baseline} | Signal: {signal_id} | Reason: {old_reason} → SIGNAL_RESET")
        
        # Update citadel state
        self._update_citadel_state()
        
        logger.info(f"✅ TCS reset to baseline after signal completion: {signal_id}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current throttle system status"""
        return {
            "tcs_threshold": self.current_state.current_tcs,
            "tier_level": self.current_state.tier_level,
            "reason_code": self.current_state.reason_code,
            "last_signal_timestamp": self.current_state.last_signal_timestamp,
            "last_signal_time": datetime.fromtimestamp(self.current_state.last_signal_timestamp).isoformat() if self.current_state.last_signal_timestamp else None,
            "minutes_since_signal": self.current_state.minutes_since_signal,
            "threshold_changed_at": self.current_state.threshold_changed_at,
            "next_decay_in_minutes": self.current_state.next_decay_in_minutes,
            "pressure_override_active": self.current_state.pressure_override_active,
            "monitoring_active": self.monitoring_active,
            "baseline_tcs": self.config.baseline,
            "system_status": "OPERATIONAL"
        }
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🛡️ CITADEL adaptive throttle monitoring started")
        self.throttle_logger.info("MONITORING_STARTED - Adaptive throttle monitoring active")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("🛡️ CITADEL adaptive throttle monitoring stopped")
        self.throttle_logger.info("MONITORING_STOPPED - Adaptive throttle monitoring disabled")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Check for new signals and update TCS threshold
                current_last_signal = self._get_last_signal_timestamp()
                
                # If we found a new signal, reset threshold
                if (current_last_signal and 
                    (self.current_state.last_signal_timestamp is None or 
                     current_last_signal > self.current_state.last_signal_timestamp)):
                    
                    self.current_state.last_signal_timestamp = current_last_signal
                    self.on_signal_completed(f"AUTO_DETECTED_{int(current_last_signal)}", current_last_signal)
                
                # Update TCS threshold based on elapsed time
                self._update_tcs_threshold()
                
                # Sleep for monitoring interval
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")
                self.throttle_logger.error(f"MONITORING_ERROR - {e}")
                time.sleep(60)  # Sleep longer on error

# Global instance
adaptive_throttle = CitadelAdaptiveThrottle()

def get_adaptive_throttle() -> CitadelAdaptiveThrottle:
    """Get the global adaptive throttle instance"""
    return adaptive_throttle

def get_current_tcs_threshold() -> float:
    """Get current TCS threshold for external systems"""
    return adaptive_throttle.current_state.current_tcs

if __name__ == "__main__":
    """Test the adaptive throttle system"""
    print("🧪 Testing CITADEL Adaptive TCS Throttling System")
    
    # Initialize system
    throttle = CitadelAdaptiveThrottle()
    
    # Start monitoring
    throttle.start_monitoring()
    
    try:
        # Run for 60 seconds
        print("⏱️ Running for 60 seconds...")
        time.sleep(60)
        
        # Get status
        status = throttle.get_current_status()
        print(f"📊 Current status: {json.dumps(status, indent=2)}")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        throttle.stop_monitoring()
    
    print("✅ Test complete")