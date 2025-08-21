#!/usr/bin/env python3
"""
BITTEN Pattern Quarantine Manager - Two-Stage Elimination System
Stage 1: QUARANTINE - Demo-only mode for negative EV patterns
Stage 2: KILL - Full elimination after extended negative performance
Prevents killing winners during variance by using graduated approach.
"""

import json
import time
import sqlite3
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import logging
from expectancy_calculator import ExpectancyCalculator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatternStatus(Enum):
    ACTIVE = "ACTIVE"
    QUARANTINE = "QUARANTINE"  # Demo-only mode
    KILLED = "KILLED"          # Fully eliminated
    RECOVERING = "RECOVERING"  # Being monitored for comeback

class QuarantineReason(Enum):
    NEGATIVE_EXPECTANCY = "NEGATIVE_EXPECTANCY"
    SAFETY_VIOLATION = "SAFETY_VIOLATION"
    EXTENDED_LOSSES = "EXTENDED_LOSSES"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"

class PatternQuarantineManager:
    """
    Two-stage pattern elimination system with recovery monitoring.
    Prevents killing profitable patterns during temporary variance.
    """
    
    def __init__(self, 
                 db_path: str = "/root/HydraX-v2/bitten.db",
                 status_file: str = "/root/HydraX-v2/pattern_quarantine_status.json"):
        self.db_path = db_path
        self.status_file = status_file
        self.expectancy_calc = ExpectancyCalculator(db_path)
        
        # Quarantine thresholds
        self.stage1_threshold = 50   # Signals before quarantine consideration
        self.stage2_threshold = 100  # Total signals before kill consideration
        self.recovery_threshold = 30 # Signals to monitor recovery
        
        # Safety limits
        self.safety_zone_pct = 0.05  # ±5% of breakeven
        self.min_confidence_drop = 0.15  # 15% confidence drop triggers review
        
        # Load existing status
        self.pattern_status = self._load_status()
        
        logger.info("PatternQuarantineManager initialized with 2-stage system")
    
    def _load_status(self) -> Dict:
        """Load existing pattern quarantine status"""
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "patterns": {},
                "last_updated": int(time.time()),
                "system_version": "2.0"
            }
        except Exception as e:
            logger.error(f"Error loading status file: {e}")
            return {"patterns": {}, "last_updated": int(time.time())}
    
    def _save_status(self):
        """Save pattern status to file"""
        try:
            self.pattern_status["last_updated"] = int(time.time())
            with open(self.status_file, 'w') as f:
                json.dump(self.pattern_status, f, indent=2)
            logger.info(f"Quarantine status saved to {self.status_file}")
        except Exception as e:
            logger.error(f"Error saving status file: {e}")
    
    def evaluate_pattern(self, pattern_type: str, symbol: str = None) -> Dict:
        """
        Evaluate a pattern for quarantine/elimination status.
        Returns action recommendation and reasoning.
        """
        try:
            # Get expectancy analysis
            expectancy_data = self.expectancy_calc.calculate_expectancy(pattern_type, symbol)
            
            if expectancy_data.get('status') == 'INSUFFICIENT_DATA':
                return {
                    "pattern_type": pattern_type,
                    "symbol": symbol,
                    "action": "MONITOR",
                    "reason": "Insufficient data for evaluation",
                    "current_status": "ACTIVE",
                    "sample_size": expectancy_data.get('sample_size', 0)
                }
            
            pattern_key = f"{pattern_type}_{symbol}" if symbol else pattern_type
            current_status = self._get_current_status(pattern_key)
            
            # Evaluate based on current status
            if current_status == PatternStatus.ACTIVE:
                return self._evaluate_active_pattern(pattern_key, expectancy_data)
            elif current_status == PatternStatus.QUARANTINE:
                return self._evaluate_quarantined_pattern(pattern_key, expectancy_data)
            elif current_status == PatternStatus.KILLED:
                return self._evaluate_killed_pattern(pattern_key, expectancy_data)
            else:  # RECOVERING
                return self._evaluate_recovering_pattern(pattern_key, expectancy_data)
                
        except Exception as e:
            logger.error(f"Error evaluating pattern {pattern_type}: {e}")
            return {
                "pattern_type": pattern_type,
                "action": "ERROR",
                "error": str(e)
            }
    
    def _evaluate_active_pattern(self, pattern_key: str, expectancy_data: Dict) -> Dict:
        """Evaluate active pattern for quarantine"""
        expectancy = expectancy_data.get('expectancy', 0)
        sample_size = expectancy_data.get('sample_size', 0)
        safety_status = expectancy_data.get('safety_status')
        
        # Check if should be quarantined
        should_quarantine = False
        quarantine_reason = None
        
        # Stage 1: Check for quarantine conditions
        if sample_size >= self.stage1_threshold:
            if safety_status == "UNPROFITABLE":
                should_quarantine = True
                quarantine_reason = QuarantineReason.NEGATIVE_EXPECTANCY
            elif expectancy < -self.safety_zone_pct:
                should_quarantine = True
                quarantine_reason = QuarantineReason.SAFETY_VIOLATION
            elif self._check_extended_losses(pattern_key, expectancy_data):
                should_quarantine = True
                quarantine_reason = QuarantineReason.EXTENDED_LOSSES
        
        if should_quarantine:
            self._quarantine_pattern(pattern_key, quarantine_reason, expectancy_data)
            return {
                "pattern_type": pattern_key,
                "action": "QUARANTINE",
                "reason": f"Stage 1: {quarantine_reason.value}",
                "new_status": "QUARANTINE",
                "expectancy": expectancy,
                "sample_size": sample_size,
                "demo_mode": True
            }
        else:
            return {
                "pattern_type": pattern_key,
                "action": "CONTINUE",
                "reason": "Pattern performing within acceptable range",
                "current_status": "ACTIVE",
                "expectancy": expectancy,
                "sample_size": sample_size
            }
    
    def _evaluate_quarantined_pattern(self, pattern_key: str, expectancy_data: Dict) -> Dict:
        """Evaluate quarantined pattern for kill or recovery"""
        expectancy = expectancy_data.get('expectancy', 0)
        sample_size = expectancy_data.get('sample_size', 0)
        safety_status = expectancy_data.get('safety_status')
        
        pattern_info = self.pattern_status["patterns"].get(pattern_key, {})
        quarantine_start = pattern_info.get('quarantine_start', time.time())
        signals_in_quarantine = sample_size - pattern_info.get('signals_at_quarantine', 0)
        
        # Check for recovery
        if safety_status in ["PROFITABLE", "SAFE_ZONE"]:
            if signals_in_quarantine >= self.recovery_threshold:
                self._recover_pattern(pattern_key, expectancy_data)
                return {
                    "pattern_type": pattern_key,
                    "action": "RECOVER",
                    "reason": "Pattern showing positive expectancy in demo mode",
                    "new_status": "ACTIVE",
                    "expectancy": expectancy,
                    "signals_in_quarantine": signals_in_quarantine
                }
        
        # Check for kill condition
        if sample_size >= self.stage2_threshold:
            if safety_status == "UNPROFITABLE":
                self._kill_pattern(pattern_key, expectancy_data)
                return {
                    "pattern_type": pattern_key,
                    "action": "KILL",
                    "reason": "Stage 2: Extended negative performance",
                    "new_status": "KILLED",
                    "expectancy": expectancy,
                    "total_signals": sample_size
                }
        
        return {
            "pattern_type": pattern_key,
            "action": "MONITOR_QUARANTINE",
            "reason": "Pattern in demo mode, monitoring performance",
            "current_status": "QUARANTINE",
            "expectancy": expectancy,
            "signals_in_quarantine": signals_in_quarantine,
            "demo_mode": True
        }
    
    def _evaluate_killed_pattern(self, pattern_key: str, expectancy_data: Dict) -> Dict:
        """Check if killed pattern shows signs of life"""
        expectancy = expectancy_data.get('expectancy', 0)
        safety_status = expectancy_data.get('safety_status')
        
        # Very high bar for revival
        if safety_status == "PROFITABLE" and expectancy > 0.1:  # 10% positive expectancy
            pattern_info = self.pattern_status["patterns"][pattern_key]
            pattern_info['status'] = PatternStatus.RECOVERING.value
            pattern_info['recovery_start'] = int(time.time())
            self._save_status()
            
            return {
                "pattern_type": pattern_key,
                "action": "MONITOR_RECOVERY",
                "reason": "Killed pattern showing strong positive signals",
                "new_status": "RECOVERING",
                "expectancy": expectancy,
                "note": "Pattern moved to recovery monitoring"
            }
        
        return {
            "pattern_type": pattern_key,
            "action": "STAY_KILLED",
            "reason": "Pattern remains unprofitable",
            "current_status": "KILLED",
            "expectancy": expectancy
        }
    
    def _evaluate_recovering_pattern(self, pattern_key: str, expectancy_data: Dict) -> Dict:
        """Evaluate pattern in recovery phase"""
        expectancy = expectancy_data.get('expectancy', 0)
        sample_size = expectancy_data.get('sample_size', 0)
        safety_status = expectancy_data.get('safety_status')
        
        pattern_info = self.pattern_status["patterns"][pattern_key]
        recovery_start = pattern_info.get('recovery_start', time.time())
        signals_since_recovery = sample_size - pattern_info.get('signals_at_recovery', 0)
        
        if signals_since_recovery >= self.recovery_threshold:
            if safety_status in ["PROFITABLE", "SAFE_ZONE"]:
                # Full recovery
                self._recover_pattern(pattern_key, expectancy_data)
                return {
                    "pattern_type": pattern_key,
                    "action": "FULL_RECOVERY",
                    "reason": "Pattern proven profitable after kill status",
                    "new_status": "ACTIVE",
                    "expectancy": expectancy
                }
            else:
                # Back to killed
                pattern_info['status'] = PatternStatus.KILLED.value
                self._save_status()
                return {
                    "pattern_type": pattern_key,
                    "action": "RECOVERY_FAILED",
                    "reason": "Pattern failed recovery monitoring",
                    "new_status": "KILLED",
                    "expectancy": expectancy
                }
        
        return {
            "pattern_type": pattern_key,
            "action": "MONITOR_RECOVERY",
            "reason": "Pattern in recovery monitoring phase",
            "current_status": "RECOVERING",
            "signals_since_recovery": signals_since_recovery
        }
    
    def _quarantine_pattern(self, pattern_key: str, reason: QuarantineReason, expectancy_data: Dict):
        """Move pattern to quarantine (demo-only mode)"""
        if "patterns" not in self.pattern_status:
            self.pattern_status["patterns"] = {}
        
        self.pattern_status["patterns"][pattern_key] = {
            "status": PatternStatus.QUARANTINE.value,
            "quarantine_start": int(time.time()),
            "quarantine_reason": reason.value,
            "signals_at_quarantine": expectancy_data.get('sample_size', 0),
            "expectancy_at_quarantine": expectancy_data.get('expectancy', 0),
            "history": self.pattern_status["patterns"].get(pattern_key, {}).get("history", [])
        }
        
        # Add to history
        self.pattern_status["patterns"][pattern_key]["history"].append({
            "action": "QUARANTINE",
            "timestamp": int(time.time()),
            "reason": reason.value,
            "expectancy": expectancy_data.get('expectancy', 0)
        })
        
        self._save_status()
        logger.warning(f"Pattern {pattern_key} QUARANTINED: {reason.value}")
    
    def _kill_pattern(self, pattern_key: str, expectancy_data: Dict):
        """Fully eliminate pattern"""
        pattern_info = self.pattern_status["patterns"][pattern_key]
        pattern_info["status"] = PatternStatus.KILLED.value
        pattern_info["kill_timestamp"] = int(time.time())
        pattern_info["final_expectancy"] = expectancy_data.get('expectancy', 0)
        pattern_info["total_signals"] = expectancy_data.get('sample_size', 0)
        
        # Add to history
        pattern_info["history"].append({
            "action": "KILL",
            "timestamp": int(time.time()),
            "expectancy": expectancy_data.get('expectancy', 0),
            "total_signals": expectancy_data.get('sample_size', 0)
        })
        
        self._save_status()
        logger.error(f"Pattern {pattern_key} KILLED after Stage 2 evaluation")
    
    def _recover_pattern(self, pattern_key: str, expectancy_data: Dict):
        """Recover pattern to active status"""
        pattern_info = self.pattern_status["patterns"][pattern_key]
        pattern_info["status"] = PatternStatus.ACTIVE.value
        pattern_info["recovery_timestamp"] = int(time.time())
        pattern_info["recovery_expectancy"] = expectancy_data.get('expectancy', 0)
        
        # Add to history
        pattern_info["history"].append({
            "action": "RECOVER",
            "timestamp": int(time.time()),
            "expectancy": expectancy_data.get('expectancy', 0)
        })
        
        self._save_status()
        logger.info(f"Pattern {pattern_key} RECOVERED to active status")
    
    def _get_current_status(self, pattern_key: str) -> PatternStatus:
        """Get current status of pattern"""
        pattern_info = self.pattern_status["patterns"].get(pattern_key, {})
        status_str = pattern_info.get("status", PatternStatus.ACTIVE.value)
        return PatternStatus(status_str)
    
    def _check_extended_losses(self, pattern_key: str, expectancy_data: Dict) -> bool:
        """Check for extended losing streaks"""
        # This would check for consecutive losses or declining performance
        # For now, use trend analysis from expectancy data
        trend_analysis = expectancy_data.get('trend_analysis', {})
        if isinstance(trend_analysis, dict):
            direction = trend_analysis.get('direction')
            magnitude = trend_analysis.get('magnitude', 0)
            return direction == "DECLINING" and magnitude > 0.15  # 15% decline
        return False
    
    def get_all_pattern_statuses(self) -> Dict:
        """Get status of all patterns"""
        return {
            "timestamp": int(time.time()),
            "patterns": self.pattern_status.get("patterns", {}),
            "summary": self._get_status_summary()
        }
    
    def _get_status_summary(self) -> Dict:
        """Get summary statistics"""
        patterns = self.pattern_status.get("patterns", {})
        
        summary = {
            "total_patterns": len(patterns),
            "active": 0,
            "quarantined": 0,
            "killed": 0,
            "recovering": 0
        }
        
        for pattern_info in patterns.values():
            status = pattern_info.get("status", "ACTIVE")
            if status == "ACTIVE":
                summary["active"] += 1
            elif status == "QUARANTINE":
                summary["quarantined"] += 1
            elif status == "KILLED":
                summary["killed"] += 1
            elif status == "RECOVERING":
                summary["recovering"] += 1
        
        return summary
    
    def force_quarantine(self, pattern_type: str, reason: str = "MANUAL_OVERRIDE") -> bool:
        """Manually quarantine a pattern"""
        try:
            pattern_key = pattern_type
            expectancy_data = self.expectancy_calc.calculate_expectancy(pattern_type)
            self._quarantine_pattern(pattern_key, QuarantineReason.MANUAL_OVERRIDE, expectancy_data)
            logger.warning(f"Pattern {pattern_type} manually quarantined: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error forcing quarantine for {pattern_type}: {e}")
            return False
    
    def force_recovery(self, pattern_type: str) -> bool:
        """Manually recover a pattern"""
        try:
            pattern_key = pattern_type
            expectancy_data = self.expectancy_calc.calculate_expectancy(pattern_type)
            self._recover_pattern(pattern_key, expectancy_data)
            logger.info(f"Pattern {pattern_type} manually recovered")
            return True
        except Exception as e:
            logger.error(f"Error forcing recovery for {pattern_type}: {e}")
            return False
    
    def is_pattern_active(self, pattern_type: str, symbol: str = None) -> bool:
        """Check if pattern is active (not quarantined or killed)"""
        pattern_key = f"{pattern_type}_{symbol}" if symbol else pattern_type
        status = self._get_current_status(pattern_key)
        return status == PatternStatus.ACTIVE
    
    def run_full_evaluation(self) -> Dict:
        """Run evaluation on all patterns in database"""
        try:
            # Get all unique patterns from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT pattern_type 
                    FROM signals 
                    WHERE outcome IN ('WIN', 'LOSS')
                """)
                patterns = [row[0] for row in cursor.fetchall()]
            
            results = {}
            for pattern in patterns:
                results[pattern] = self.evaluate_pattern(pattern)
            
            # Generate summary report
            summary_report = {
                "evaluation_timestamp": int(time.time()),
                "patterns_evaluated": len(results),
                "pattern_results": results,
                "system_status": self.get_all_pattern_statuses()
            }
            
            # Save evaluation report
            report_file = f"/root/HydraX-v2/quarantine_evaluation_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(summary_report, f, indent=2)
            
            logger.info(f"Full pattern evaluation completed. Report: {report_file}")
            return summary_report
            
        except Exception as e:
            logger.error(f"Error in full evaluation: {e}")
            return {"error": str(e)}

def main():
    """Run pattern quarantine evaluation"""
    manager = PatternQuarantineManager()
    
    # Run full evaluation
    results = manager.run_full_evaluation()
    
    print(f"Pattern Quarantine Evaluation Complete")
    print(f"Patterns evaluated: {results.get('patterns_evaluated', 0)}")
    
    # Show summary
    summary = results.get('system_status', {}).get('summary', {})
    print(f"\nStatus Summary:")
    print(f"  Active: {summary.get('active', 0)}")
    print(f"  Quarantined: {summary.get('quarantined', 0)}")
    print(f"  Killed: {summary.get('killed', 0)}")
    print(f"  Recovering: {summary.get('recovering', 0)}")
    
    # Show recent actions
    print(f"\nRecent Actions:")
    for pattern, result in results.get('pattern_results', {}).items():
        action = result.get('action')
        if action not in ['CONTINUE', 'MONITOR']:
            print(f"  {pattern}: {action} - {result.get('reason', 'No reason')}")

if __name__ == "__main__":
    main()