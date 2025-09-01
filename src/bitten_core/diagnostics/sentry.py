#!/usr/bin/env python3
"""
Diagnostic sentry for runtime guards and safety checks
Monitors for violations and can auto-disable features if issues detected
"""

import json
import time
import toml
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)

# Load rollout configuration
CONFIG_PATH = Path("/root/HydraX-v2/config/rollout.toml")
ROLLOUT_CONFIG = toml.load(CONFIG_PATH) if CONFIG_PATH.exists() else {}

@dataclass
class Violation:
    """Record of a safety violation"""
    timestamp: float
    ticket: int
    violation_type: str
    details: Dict
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL

class DiagnosticSentry:
    """
    Runtime safety monitor that detects and responds to violations
    """
    
    def __init__(self):
        self.violations: deque = deque(maxlen=100)  # Recent violations
        self.violation_counts: Dict[str, int] = {}  # Type -> count
        self.auto_disable_threshold = ROLLOUT_CONFIG.get("AUTO_DISABLE_THRESHOLD", 2)
        self.alert_partial_min_r = ROLLOUT_CONFIG.get("ALERT_PARTIAL_MIN_R", 1.25)
        self.alert_be_min_r = ROLLOUT_CONFIG.get("ALERT_BE_MIN_R", 1.25)
        self.feature_enabled = True
        self.bad_exit_streak = 0
        
    def check_partial_milestone(self, ticket: int, current_r: float, 
                               milestone: str) -> bool:
        """
        Check if partial close is happening at appropriate R level
        
        Returns:
            True if OK, False if violation detected
        """
        if current_r < self.alert_partial_min_r:
            violation = Violation(
                timestamp=time.time(),
                ticket=ticket,
                violation_type="PREMATURE_PARTIAL",
                details={
                    "current_r": current_r,
                    "min_r": self.alert_partial_min_r,
                    "milestone": milestone
                },
                severity="HIGH"
            )
            
            self._record_violation(violation)
            logger.error(f"🚨 PREMATURE PARTIAL: Ticket {ticket} at {current_r:.2f}R < {self.alert_partial_min_r}R minimum")
            
            # Alert via Telegram
            self._send_alert(f"⚠️ PREMATURE PARTIAL DETECTED\nTicket: {ticket}\nR: {current_r:.2f}\nExpected: >{self.alert_partial_min_r}")
            
            return False
        
        return True
    
    def check_be_milestone(self, ticket: int, current_r: float, 
                          tp1_done: bool) -> bool:
        """
        Check if BE move is happening at appropriate time
        
        Returns:
            True if OK, False if violation detected
        """
        # BE should only happen after TP1
        if not tp1_done:
            violation = Violation(
                timestamp=time.time(),
                ticket=ticket,
                violation_type="PREMATURE_BE",
                details={
                    "current_r": current_r,
                    "tp1_done": tp1_done
                },
                severity="HIGH"
            )
            
            self._record_violation(violation)
            logger.error(f"🚨 PREMATURE BE: Ticket {ticket} BE move before TP1")
            
            self._send_alert(f"⚠️ PREMATURE BE DETECTED\nTicket: {ticket}\nBE moved before TP1 hit")
            
            return False
        
        if current_r < self.alert_be_min_r:
            violation = Violation(
                timestamp=time.time(),
                ticket=ticket,
                violation_type="LOW_R_BE",
                details={
                    "current_r": current_r,
                    "min_r": self.alert_be_min_r
                },
                severity="MEDIUM"
            )
            
            self._record_violation(violation)
            logger.warning(f"⚠️ LOW R BE: Ticket {ticket} BE at {current_r:.2f}R")
            
            return False
        
        return True
    
    def check_trail_milestone(self, ticket: int, tp1_done: bool) -> bool:
        """
        Check if trailing is starting at appropriate time
        
        Returns:
            True if OK, False if violation detected
        """
        if not tp1_done:
            violation = Violation(
                timestamp=time.time(),
                ticket=ticket,
                violation_type="PREMATURE_TRAIL",
                details={
                    "tp1_done": tp1_done
                },
                severity="HIGH"
            )
            
            self._record_violation(violation)
            logger.error(f"🚨 PREMATURE TRAIL: Ticket {ticket} trailing before TP1")
            
            self._send_alert(f"⚠️ PREMATURE TRAIL DETECTED\nTicket: {ticket}\nTrailing activated before TP1")
            
            return False
        
        return True
    
    def check_bad_exit(self, ticket: int, exit_r: float) -> bool:
        """
        Check if exit happened at very low R (potential issue)
        
        Returns:
            True if OK, False if bad exit detected
        """
        if exit_r < 0.2:
            self.bad_exit_streak += 1
            
            violation = Violation(
                timestamp=time.time(),
                ticket=ticket,
                violation_type="BAD_EXIT",
                details={
                    "exit_r": exit_r,
                    "streak": self.bad_exit_streak
                },
                severity="CRITICAL" if self.bad_exit_streak >= self.auto_disable_threshold else "HIGH"
            )
            
            self._record_violation(violation)
            logger.error(f"🚨 BAD EXIT: Ticket {ticket} closed at {exit_r:.2f}R (streak: {self.bad_exit_streak})")
            
            # Auto-disable if too many bad exits
            if self.bad_exit_streak >= self.auto_disable_threshold:
                self._auto_disable_feature()
            
            return False
        else:
            # Reset streak on good exit
            if exit_r > 0.5:
                self.bad_exit_streak = 0
        
        return True
    
    def check_command_error(self, ticket: int, cmd_type: str, 
                          error_code: str, details: Dict) -> bool:
        """
        Check command execution errors
        """
        violation = Violation(
            timestamp=time.time(),
            ticket=ticket,
            violation_type="COMMAND_ERROR",
            details={
                "cmd_type": cmd_type,
                "error_code": error_code,
                **details
            },
            severity="MEDIUM"
        )
        
        self._record_violation(violation)
        logger.warning(f"Command error for {ticket}: {cmd_type} failed with {error_code}")
        
        return False
    
    def _record_violation(self, violation: Violation):
        """Record a violation and update counts"""
        self.violations.append(violation)
        
        # Update counts
        if violation.violation_type not in self.violation_counts:
            self.violation_counts[violation.violation_type] = 0
        self.violation_counts[violation.violation_type] += 1
        
        # Log to file for analysis
        self._log_violation(violation)
    
    def _log_violation(self, violation: Violation):
        """Log violation to file for later analysis"""
        log_path = Path("/root/HydraX-v2/logs/violations.jsonl")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(log_path, 'a') as f:
                log_entry = {
                    "timestamp": violation.timestamp,
                    "ticket": violation.ticket,
                    "type": violation.violation_type,
                    "severity": violation.severity,
                    "details": violation.details
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log violation: {e}")
    
    def _send_alert(self, message: str):
        """Send alert via Telegram or logging"""
        # For now just log critically
        logger.critical(f"SENTRY ALERT: {message}")
        
        # TODO: Integrate with Telegram bot for real alerts
    
    def _auto_disable_feature(self):
        """Auto-disable hybrid feature due to violations"""
        logger.critical("🚨🚨🚨 AUTO-DISABLING HYBRID FEATURE DUE TO VIOLATIONS 🚨🚨🚨")
        
        # Update rollout config
        try:
            config = toml.load(CONFIG_PATH) if CONFIG_PATH.exists() else {}
            config["FEATURE_HYBRID_ENABLED"] = False
            
            with open(CONFIG_PATH, 'w') as f:
                toml.dump(config, f)
            
            self.feature_enabled = False
            
            self._send_alert(
                "🚨 HYBRID FEATURE AUTO-DISABLED\n"
                f"Reason: {self.bad_exit_streak} bad exits in a row\n"
                "Manual intervention required to re-enable"
            )
            
        except Exception as e:
            logger.error(f"Failed to auto-disable feature: {e}")
    
    def get_violation_summary(self) -> Dict:
        """Get summary of recent violations"""
        summary = {
            "total_violations": len(self.violations),
            "by_type": self.violation_counts.copy(),
            "bad_exit_streak": self.bad_exit_streak,
            "feature_enabled": self.feature_enabled,
            "recent_violations": []
        }
        
        # Add last 10 violations
        for v in list(self.violations)[-10:]:
            summary["recent_violations"].append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v.timestamp)),
                "ticket": v.ticket,
                "type": v.violation_type,
                "severity": v.severity
            })
        
        return summary
    
    def reset_violations(self):
        """Reset violation tracking (for testing)"""
        self.violations.clear()
        self.violation_counts.clear()
        self.bad_exit_streak = 0
        logger.info("Sentry violations reset")

# Singleton instance
sentry = DiagnosticSentry()