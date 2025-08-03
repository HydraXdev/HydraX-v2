#!/usr/bin/env python3
"""
🎛️ BITTEN VENOM v8 Dynamic Signal Governor
Throttle Controller for Real-time TCS/ML Threshold Adjustment

Governor States:
1. Cruise Mode – Default stable operation (TCS ≥ 70, ML ≥ 0.65) [TESTING]
2. Nitrous Mode – High-frequency burst mode (TCS ≥ 75, ML ≥ 0.60)
3. Throttle Hold – Market stagnation response (TCS reduces to 76%)
4. Lockdown – Loss protection mode (TCS +3, pause 30min)
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import requests
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - THROTTLE - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GovernorState(Enum):
    CRUISE = "cruise"
    NITROUS = "nitrous"
    THROTTLE_HOLD = "throttle_hold"
    LOCKDOWN = "lockdown"

@dataclass
class ThrottleSettings:
    """Current throttle configuration"""
    tcs_threshold: float
    ml_threshold: float
    governor_state: str
    state_entered_at: float
    next_evaluation: float
    signals_fired_count: int
    consecutive_losses: int
    last_signal_time: float

@dataclass
class SignalRecord:
    """Individual signal tracking record"""
    signal_id: str
    timestamp: float
    symbol: str
    direction: str
    tcs_score: float
    ml_score: float
    result: Optional[str] = None  # "win", "loss", or None (pending)
    pips: Optional[float] = None

class VenomThrottleController:
    """Dynamic Signal Governor for VENOM v8 Stream Pipeline"""
    
    def __init__(self, 
                 citadel_state_path: str = "/root/HydraX-v2/citadel_state.json",
                 truth_log_path: str = "/root/HydraX-v2/truth_log.jsonl",
                 commander_user_id: str = "7176191872"):
        
        self.citadel_state_path = Path(citadel_state_path)
        self.truth_log_path = Path(truth_log_path)
        self.commander_user_id = commander_user_id
        
        # Signal tracking buffers
        self.recent_signals = deque(maxlen=100)  # Last 100 signals
        self.signal_history = deque(maxlen=500)  # Extended history
        
        # State management
        self.current_settings = self._load_default_settings()
        self.last_telegram_alert = 0
        self.telegram_throttle_window = 3600  # 1 hour between routine alerts
        self.is_running = False
        self.evaluation_thread = None
        
        # Load bot token
        self.bot_token = self._load_bot_token()
        
        # Initialize from existing state
        self._load_existing_state()
        
        logger.info("🎛️ VENOM Throttle Controller initialized")
        
    def _load_default_settings(self) -> ThrottleSettings:
        """Load default cruise mode settings"""
        return ThrottleSettings(
            tcs_threshold=79.0,  # Increased from 70.0 to reduce signal rate
            ml_threshold=0.65,
            governor_state=GovernorState.CRUISE.value,
            state_entered_at=time.time(),
            next_evaluation=time.time() + 60,
            signals_fired_count=0,
            consecutive_losses=0,
            last_signal_time=0
        )
    
    def _load_bot_token(self) -> Optional[str]:
        """Load Telegram bot token"""
        try:
            import sys
            sys.path.append('/root/HydraX-v2')
            from config_loader import get_bot_token
            return get_bot_token()
        except Exception as e:
            logger.warning(f"⚠️ Could not load bot token: {e}")
            return None
    
    def _load_existing_state(self):
        """Load existing throttle state and signal history"""
        # Load citadel state if exists
        if self.citadel_state_path.exists():
            try:
                with open(self.citadel_state_path, 'r') as f:
                    state_data = json.load(f)
                    
                # Extract throttle settings if present
                if 'throttle_controller' in state_data:
                    tc_data = state_data['throttle_controller']
                    self.current_settings = ThrottleSettings(**tc_data)
                    logger.info(f"📊 Loaded existing state: {self.current_settings.governor_state}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load existing state: {e}")
        
        # Load recent signals from truth log
        self._load_signal_history()
    
    def _load_signal_history(self):
        """Load recent signal history from truth log"""
        if not self.truth_log_path.exists():
            return
            
        try:
            cutoff_time = time.time() - 7200  # Last 2 hours
            
            with open(self.truth_log_path, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        timestamp = record.get('timestamp', 0)
                        if isinstance(timestamp, (int, float)) and timestamp > cutoff_time:
                            signal_record = SignalRecord(
                                signal_id=record.get('signal_id', ''),
                                timestamp=record.get('timestamp', 0),
                                symbol=record.get('symbol', ''),
                                direction=record.get('direction', ''),
                                tcs_score=record.get('tcs_score', 0),
                                ml_score=record.get('ml_score', 0),
                                result=record.get('result'),
                                pips=record.get('pips')
                            )
                            self.signal_history.append(signal_record)
                    except (json.JSONDecodeError, KeyError):
                        continue
                        
            logger.info(f"📚 Loaded {len(self.signal_history)} recent signals from truth log")
            
        except Exception as e:
            logger.error(f"❌ Failed to load signal history: {e}")
    
    def _save_citadel_state(self):
        """Save current throttle settings to citadel state"""
        try:
            # Load existing citadel state
            state_data = {}
            if self.citadel_state_path.exists():
                with open(self.citadel_state_path, 'r') as f:
                    state_data = json.load(f)
            
            # Update throttle controller section
            state_data['throttle_controller'] = asdict(self.current_settings)
            state_data['last_updated'] = time.time()
            
            # Save updated state
            with open(self.citadel_state_path, 'w') as f:
                json.dump(state_data, f, indent=2)
                
            logger.debug(f"💾 Saved throttle state: {self.current_settings.governor_state}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save citadel state: {e}")
    
    def add_signal(self, signal_id: str, symbol: str, direction: str, 
                   tcs_score: float, ml_score: float):
        """Record a new signal firing"""
        signal_record = SignalRecord(
            signal_id=signal_id,
            timestamp=time.time(),
            symbol=symbol,
            direction=direction,
            tcs_score=tcs_score,
            ml_score=ml_score
        )
        
        self.recent_signals.append(signal_record)
        self.signal_history.append(signal_record)
        
        # Update settings
        self.current_settings.signals_fired_count += 1
        self.current_settings.last_signal_time = time.time()
        
        logger.info(f"📡 Signal recorded: {signal_id} ({symbol} {direction}) TCS:{tcs_score:.1f}")
        
        # Immediate evaluation for potential mode changes
        self._evaluate_immediate_triggers()
    
    def update_signal_result(self, signal_id: str, result: str, pips: Optional[float] = None):
        """Update signal result (win/loss)"""
        # Update in recent signals
        for signal in self.recent_signals:
            if signal.signal_id == signal_id:
                signal.result = result
                signal.pips = pips
                break
        
        # Update in history
        for signal in self.signal_history:
            if signal.signal_id == signal_id:
                signal.result = result
                signal.pips = pips
                break
        
        logger.info(f"📊 Signal result updated: {signal_id} → {result} ({pips} pips)")
        
        # Check for consecutive losses
        self._check_consecutive_losses()
    
    def _evaluate_immediate_triggers(self):
        """Check for immediate state changes (Nitrous/Lockdown triggers)"""
        current_time = time.time()
        
        # Check for Nitrous Mode trigger (3+ strong signals in <2 min)
        if self.current_settings.governor_state != GovernorState.NITROUS.value:
            recent_strong_signals = [
                s for s in self.recent_signals 
                if (current_time - s.timestamp) < 120 and s.tcs_score >= 85
            ]
            
            if len(recent_strong_signals) >= 3:
                self._transition_to_nitrous()
    
    def _check_consecutive_losses(self):
        """Check for consecutive losses triggering lockdown"""
        recent_results = []
        
        # Get last 5 signal results
        for signal in reversed(list(self.recent_signals)):
            if signal.result:
                recent_results.append(signal.result)
                if len(recent_results) >= 5:
                    break
        
        # Count consecutive losses from the end
        consecutive_losses = 0
        for result in recent_results:
            if result == "loss":
                consecutive_losses += 1
            else:
                break
        
        self.current_settings.consecutive_losses = consecutive_losses
        
        # Trigger lockdown on 3+ consecutive losses
        if (consecutive_losses >= 3 and 
            self.current_settings.governor_state != GovernorState.LOCKDOWN.value):
            self._transition_to_lockdown()
    
    def _transition_to_nitrous(self):
        """Enter Nitrous Mode for high-frequency burst"""
        old_state = self.current_settings.governor_state
        
        self.current_settings.governor_state = GovernorState.NITROUS.value
        self.current_settings.tcs_threshold = 75.0
        self.current_settings.ml_threshold = 0.60
        self.current_settings.state_entered_at = time.time()
        self.current_settings.next_evaluation = time.time() + 120  # 2 min burst
        
        self._save_citadel_state()
        
        message = f"🚀 **NITROUS MODE ACTIVATED**\n\nTCS Threshold: {self.current_settings.tcs_threshold}%\nML Threshold: {self.current_settings.ml_threshold}\n\nHigh-frequency burst mode engaged for 2 minutes."
        
        logger.info(f"🚀 NITROUS MODE: {old_state} → nitrous (TCS: 75%, ML: 0.60)")
        self._send_telegram_alert(message, force=True)
    
    def _transition_to_lockdown(self):
        """Enter Lockdown Mode after consecutive losses"""
        old_state = self.current_settings.governor_state
        
        self.current_settings.governor_state = GovernorState.LOCKDOWN.value
        self.current_settings.tcs_threshold = min(self.current_settings.tcs_threshold + 3, 95)
        self.current_settings.ml_threshold = min(self.current_settings.ml_threshold + 0.05, 0.85)
        self.current_settings.state_entered_at = time.time()
        self.current_settings.next_evaluation = time.time() + 1800  # 30 min lockdown
        
        self._save_citadel_state()
        
        message = f"🔒 **LOCKDOWN MODE ACTIVATED**\n\n{self.current_settings.consecutive_losses} consecutive losses detected.\n\nTCS Threshold: {self.current_settings.tcs_threshold}%\nML Threshold: {self.current_settings.ml_threshold}\n\nSignal firing paused for 30 minutes."
        
        logger.warning(f"🔒 LOCKDOWN MODE: {old_state} → lockdown (TCS: {self.current_settings.tcs_threshold}%, 30min pause)")
        self._send_telegram_alert(message, force=True)
    
    def _transition_to_throttle_hold(self):
        """Enter Throttle Hold Mode during market stagnation"""
        old_state = self.current_settings.governor_state
        
        self.current_settings.governor_state = GovernorState.THROTTLE_HOLD.value
        # TCS will be reduced gradually in periodic evaluation
        self.current_settings.state_entered_at = time.time()
        self.current_settings.next_evaluation = time.time() + 300  # 5 min intervals
        
        self._save_citadel_state()
        
        message = f"⏸️ **THROTTLE HOLD MODE**\n\nNo signals for 20+ minutes.\nGradually reducing TCS threshold to increase signal frequency.\n\nCurrent TCS: {self.current_settings.tcs_threshold}%"
        
        logger.info(f"⏸️ THROTTLE HOLD: {old_state} → throttle_hold")
        self._send_telegram_alert(message)
    
    def _transition_to_cruise(self):
        """Return to stable Cruise Mode"""
        old_state = self.current_settings.governor_state
        
        self.current_settings.governor_state = GovernorState.CRUISE.value
        self.current_settings.tcs_threshold = 79.0  # Increased from 70.0 to reduce signal rate
        self.current_settings.ml_threshold = 0.65
        self.current_settings.state_entered_at = time.time()
        self.current_settings.next_evaluation = time.time() + 60
        self.current_settings.consecutive_losses = 0  # Reset on cruise
        
        self._save_citadel_state()
        
        message = f"⚡ **CRUISE MODE RESTORED**\n\nSystem returned to stable operation.\n\nTCS Threshold: {self.current_settings.tcs_threshold}%\nML Threshold: {self.current_settings.ml_threshold}"
        
        logger.info(f"⚡ CRUISE MODE: {old_state} → cruise (TCS: 70%, ML: 0.65) [TESTING]")
        self._send_telegram_alert(message)
    
    def periodic_evaluation(self):
        """Periodic evaluation of system state (every 60s)"""
        current_time = time.time()
        
        if current_time < self.current_settings.next_evaluation:
            return
        
        logger.debug(f"🔄 Periodic evaluation: {self.current_settings.governor_state}")
        
        # State-specific evaluation logic
        if self.current_settings.governor_state == GovernorState.NITROUS.value:
            self._evaluate_nitrous_mode()
        elif self.current_settings.governor_state == GovernorState.THROTTLE_HOLD.value:
            self._evaluate_throttle_hold()
        elif self.current_settings.governor_state == GovernorState.LOCKDOWN.value:
            self._evaluate_lockdown()
        elif self.current_settings.governor_state == GovernorState.CRUISE.value:
            self._evaluate_cruise_mode()
        
        # Schedule next evaluation
        self.current_settings.next_evaluation = current_time + 60
    
    def _evaluate_cruise_mode(self):
        """Evaluate Cruise Mode for potential transitions"""
        current_time = time.time()
        
        # Check for market stagnation (no signals in 20+ min)
        time_since_last_signal = current_time - self.current_settings.last_signal_time
        
        if time_since_last_signal > 1200:  # 20 minutes
            self._transition_to_throttle_hold()
    
    def _evaluate_nitrous_mode(self):
        """Evaluate Nitrous Mode duration"""
        current_time = time.time()
        time_in_mode = current_time - self.current_settings.state_entered_at
        
        # Return to cruise after 2 minutes
        if time_in_mode > 120:
            self._transition_to_cruise()
    
    def _evaluate_throttle_hold(self):
        """Evaluate Throttle Hold Mode and adjust TCS"""
        current_time = time.time()
        time_in_mode = current_time - self.current_settings.state_entered_at
        
        # Check if we've had recent signals (exit condition)
        if current_time - self.current_settings.last_signal_time < 300:  # Signal in last 5 min
            self._transition_to_cruise()
            return
        
        # Reduce TCS every 5 minutes, minimum 76%
        intervals_passed = int(time_in_mode / 300)  # 5-minute intervals
        new_tcs = max(82.0 - (intervals_passed * 1.5), 76.0)
        
        if new_tcs != self.current_settings.tcs_threshold:
            old_tcs = self.current_settings.tcs_threshold
            self.current_settings.tcs_threshold = new_tcs
            self._save_citadel_state()
            
            logger.info(f"📉 TCS reduced: {old_tcs}% → {new_tcs}%")
            
            if new_tcs <= 76.0:
                message = f"📉 **TCS MINIMUM REACHED**\n\nTCS threshold reduced to minimum: {new_tcs}%\nIncreasing signal sensitivity to maximum."
                self._send_telegram_alert(message)
    
    def _evaluate_lockdown(self):
        """Evaluate Lockdown Mode duration"""
        current_time = time.time()
        time_in_mode = current_time - self.current_settings.state_entered_at
        
        # Exit lockdown after 30 minutes
        if time_in_mode > 1800:
            self._transition_to_cruise()
    
    def _send_telegram_alert(self, message: str, force: bool = False):
        """Send Telegram alert with throttling"""
        if not self.bot_token:
            logger.warning("⚠️ No bot token - skipping Telegram alert")
            return
        
        current_time = time.time()
        
        # Check throttling (unless forced)
        if not force and (current_time - self.last_telegram_alert) < self.telegram_throttle_window:
            logger.debug("📱 Telegram alert throttled")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.commander_user_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("📱 Telegram alert sent successfully")
                self.last_telegram_alert = current_time
            else:
                logger.error(f"❌ Telegram alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram alert: {e}")
    
    def get_current_thresholds(self) -> Tuple[float, float]:
        """Get current TCS and ML thresholds"""
        return self.current_settings.tcs_threshold, self.current_settings.ml_threshold
    
    def should_fire_signal(self, tcs_score: float, ml_score: float) -> bool:
        """Determine if signal should fire based on current thresholds"""
        # Always block during lockdown
        if self.current_settings.governor_state == GovernorState.LOCKDOWN.value:
            return False
        
        return (tcs_score >= self.current_settings.tcs_threshold and 
                ml_score >= self.current_settings.ml_threshold)
    
    def get_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        current_time = time.time()
        
        # Calculate signal rates
        recent_signals_1h = [
            s for s in self.recent_signals 
            if (current_time - s.timestamp) < 3600
        ]
        
        recent_signals_5m = [
            s for s in self.recent_signals 
            if (current_time - s.timestamp) < 300
        ]
        
        # Calculate win rate
        recent_results = [s for s in recent_signals_1h if s.result]
        win_rate = 0
        if recent_results:
            wins = len([s for s in recent_results if s.result == "win"])
            win_rate = (wins / len(recent_results)) * 100
        
        return {
            "governor_state": self.current_settings.governor_state,
            "tcs_threshold": self.current_settings.tcs_threshold,
            "ml_threshold": self.current_settings.ml_threshold,
            "time_in_current_state": current_time - self.current_settings.state_entered_at,
            "signals_last_hour": len(recent_signals_1h),
            "signals_last_5min": len(recent_signals_5m),
            "signals_per_hour": len(recent_signals_1h),
            "win_rate_1h": round(win_rate, 1),
            "consecutive_losses": self.current_settings.consecutive_losses,
            "last_signal_ago": current_time - self.current_settings.last_signal_time if self.current_settings.last_signal_time > 0 else None,
            "next_evaluation_in": max(0, self.current_settings.next_evaluation - current_time),
            "total_signals_fired": self.current_settings.signals_fired_count,
            "is_firing_blocked": self.current_settings.governor_state == GovernorState.LOCKDOWN.value
        }
    
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.evaluation_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.evaluation_thread.start()
        
        logger.info("🎛️ Throttle Controller monitoring started")
    
    def stop_monitoring(self):
        """Stop the background monitoring"""
        self.is_running = False
        if self.evaluation_thread:
            self.evaluation_thread.join(timeout=5)
        
        logger.info("🎛️ Throttle Controller monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                self.periodic_evaluation()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")
                time.sleep(30)
    
    def commander_override(self, new_state: str, duration_minutes: Optional[int] = None):
        """Manual commander override of governor state"""
        if new_state not in [state.value for state in GovernorState]:
            raise ValueError(f"Invalid state: {new_state}")
        
        old_state = self.current_settings.governor_state
        
        # Apply override
        if new_state == GovernorState.CRUISE.value:
            self._transition_to_cruise()
        elif new_state == GovernorState.NITROUS.value:
            self._transition_to_nitrous()
        elif new_state == GovernorState.THROTTLE_HOLD.value:
            self._transition_to_throttle_hold()
        elif new_state == GovernorState.LOCKDOWN.value:
            self._transition_to_lockdown()
        
        # Set duration if specified
        if duration_minutes:
            self.current_settings.next_evaluation = time.time() + (duration_minutes * 60)
        
        message = f"👑 **COMMANDER OVERRIDE**\n\nState changed: {old_state} → {new_state}\nDuration: {duration_minutes or 'indefinite'} minutes\n\nManual control activated."
        
        logger.warning(f"👑 COMMANDER OVERRIDE: {old_state} → {new_state} ({duration_minutes}min)")
        self._send_telegram_alert(message, force=True)

# Global throttle controller instance
throttle_controller = VenomThrottleController()

def get_throttle_controller() -> VenomThrottleController:
    """Get the global throttle controller instance"""
    return throttle_controller