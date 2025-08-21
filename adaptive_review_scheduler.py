#!/usr/bin/env python3
"""
BITTEN Adaptive Review Scheduler - Smart Review Cadence
Fast patterns (5+ signals/day): Review every 24-48 hours
Medium patterns (1-5/day): Review every 3-5 days  
Slow patterns (<1/day): Review weekly
Ties reviews to signal count not just time
"""

import json
import time
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import logging
import threading
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatternFrequency(Enum):
    FAST = "FAST"          # 5+ signals/day
    MEDIUM = "MEDIUM"      # 1-5 signals/day
    SLOW = "SLOW"          # <1 signal/day
    INACTIVE = "INACTIVE"  # No recent signals

class ReviewPriority(Enum):
    URGENT = "URGENT"      # Immediate review needed
    HIGH = "HIGH"          # Review within 24 hours
    MEDIUM = "MEDIUM"      # Review within 3-5 days
    LOW = "LOW"            # Review within 7 days
    SCHEDULED = "SCHEDULED" # Review at scheduled time

class AdaptiveReviewScheduler:
    """
    Intelligent review scheduling based on pattern activity and performance.
    Adapts review frequency to pattern signal generation rate and risk profile.
    """
    
    def __init__(self, 
                 db_path: str = "/root/HydraX-v2/bitten.db",
                 schedule_file: str = "/root/HydraX-v2/review_schedule.json"):
        self.db_path = db_path
        self.schedule_file = schedule_file
        
        # Frequency thresholds (signals per day)
        self.fast_threshold = 5.0
        self.medium_threshold = 1.0
        
        # Review intervals (hours)
        self.review_intervals = {
            PatternFrequency.FAST: {"min": 24, "max": 48},      # 1-2 days
            PatternFrequency.MEDIUM: {"min": 72, "max": 120},   # 3-5 days
            PatternFrequency.SLOW: {"min": 168, "max": 168},    # 7 days
            PatternFrequency.INACTIVE: {"min": 336, "max": 336} # 14 days
        }
        
        # Risk-based adjustments
        self.high_risk_multiplier = 0.5  # Review 2x more frequently
        self.poor_performance_multiplier = 0.7  # Review more frequently if losing
        
        # Load existing schedule
        self.schedule = self._load_schedule()
        
        # Components for integrated analysis
        self.expectancy_calc = None
        self.quarantine_manager = None
        
        logger.info("AdaptiveReviewScheduler initialized with intelligent cadence")
    
    def _load_schedule(self) -> Dict:
        """Load existing review schedule"""
        try:
            with open(self.schedule_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "pattern_schedules": {},
                "last_updated": int(time.time()),
                "version": "1.0"
            }
        except Exception as e:
            logger.error(f"Error loading schedule: {e}")
            return {"pattern_schedules": {}, "last_updated": int(time.time())}
    
    def _save_schedule(self):
        """Save review schedule to file"""
        try:
            self.schedule["last_updated"] = int(time.time())
            with open(self.schedule_file, 'w') as f:
                json.dump(self.schedule, f, indent=2)
            logger.info(f"Review schedule saved to {self.schedule_file}")
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
    
    def analyze_pattern_frequency(self, pattern_type: str, days_back: int = 7) -> Dict:
        """
        Analyze pattern signal frequency to determine review cadence.
        
        Args:
            pattern_type: Pattern to analyze
            days_back: Days to look back for frequency calculation
        
        Returns:
            Dict with frequency analysis and review recommendations
        """
        try:
            cutoff_time = int(time.time()) - (days_back * 24 * 3600)
            
            # Get recent signals for pattern
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as signal_count,
                           MIN(created_at) as first_signal,
                           MAX(created_at) as last_signal
                    FROM signals 
                    WHERE pattern_type = ? 
                        AND created_at > ?
                """, (pattern_type, cutoff_time))
                
                result = cursor.fetchone()
                signal_count = result[0] if result else 0
                first_signal = result[1] if result else None
                last_signal = result[2] if result else None
            
            if signal_count == 0:
                return {
                    "pattern_type": pattern_type,
                    "frequency_category": PatternFrequency.INACTIVE.value,
                    "signals_per_day": 0.0,
                    "total_signals": 0,
                    "recommendation": "Review bi-weekly due to inactivity"
                }
            
            # Calculate signals per day
            if first_signal and last_signal:
                active_days = max(1, (last_signal - first_signal) / 86400)  # Convert to days
                signals_per_day = signal_count / active_days
            else:
                signals_per_day = signal_count / days_back
            
            # Classify frequency
            if signals_per_day >= self.fast_threshold:
                frequency = PatternFrequency.FAST
            elif signals_per_day >= self.medium_threshold:
                frequency = PatternFrequency.MEDIUM
            elif signals_per_day > 0:
                frequency = PatternFrequency.SLOW
            else:
                frequency = PatternFrequency.INACTIVE
            
            # Calculate recommended review interval
            base_interval = self.review_intervals[frequency]
            recommended_hours = base_interval["min"]
            
            return {
                "pattern_type": pattern_type,
                "frequency_category": frequency.value,
                "signals_per_day": round(signals_per_day, 2),
                "total_signals": signal_count,
                "analysis_period_days": days_back,
                "recommended_review_hours": recommended_hours,
                "recommendation": self._generate_frequency_recommendation(frequency, signals_per_day)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pattern frequency: {e}")
            return {"error": str(e)}
    
    def _generate_frequency_recommendation(self, frequency: PatternFrequency, signals_per_day: float) -> str:
        """Generate human-readable frequency recommendation"""
        if frequency == PatternFrequency.FAST:
            return f"High activity pattern ({signals_per_day:.1f}/day) - Review every 1-2 days"
        elif frequency == PatternFrequency.MEDIUM:
            return f"Medium activity pattern ({signals_per_day:.1f}/day) - Review every 3-5 days"
        elif frequency == PatternFrequency.SLOW:
            return f"Low activity pattern ({signals_per_day:.1f}/day) - Review weekly"
        else:
            return "Inactive pattern - Review bi-weekly for potential reactivation"
    
    def calculate_risk_adjusted_schedule(self, pattern_type: str, frequency_analysis: Dict) -> Dict:
        """
        Calculate risk-adjusted review schedule based on pattern performance.
        High-risk or poor-performing patterns get more frequent reviews.
        """
        try:
            # Get pattern performance data
            performance_data = self._get_pattern_performance(pattern_type)
            
            base_hours = frequency_analysis["recommended_review_hours"]
            adjustment_factors = []
            adjustment_reasons = []
            
            # Risk adjustments
            expectancy = performance_data.get("expectancy", 0)
            win_rate = performance_data.get("win_rate", 0.5)
            sample_size = performance_data.get("sample_size", 0)
            
            # Poor performance adjustment
            if expectancy < -0.02:  # Losing more than 2% expectancy
                adjustment_factors.append(self.poor_performance_multiplier)
                adjustment_reasons.append("Poor expectancy performance")
            
            # Low win rate adjustment
            if win_rate < 0.4:  # Win rate below 40%
                adjustment_factors.append(0.8)
                adjustment_reasons.append("Low win rate")
            
            # Small sample size (needs more data)
            if sample_size < 20:
                adjustment_factors.append(0.9)
                adjustment_reasons.append("Insufficient sample size")
            
            # High volatility patterns (based on confidence variance)
            confidence_variance = performance_data.get("confidence_variance", 0)
            if confidence_variance > 0.1:  # High confidence variance
                adjustment_factors.append(0.8)
                adjustment_reasons.append("High performance volatility")
            
            # Apply adjustments
            final_hours = base_hours
            for factor in adjustment_factors:
                final_hours *= factor
            
            # Ensure reasonable bounds
            min_hours = 12  # At least 12 hours between reviews
            max_hours = 336  # At most 2 weeks
            final_hours = max(min_hours, min(max_hours, final_hours))
            
            # Determine priority
            priority = self._calculate_review_priority(final_hours, expectancy, sample_size)
            
            return {
                "pattern_type": pattern_type,
                "base_review_hours": base_hours,
                "risk_adjusted_hours": round(final_hours, 1),
                "adjustment_factors": adjustment_factors,
                "adjustment_reasons": adjustment_reasons,
                "review_priority": priority.value,
                "performance_context": performance_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted schedule: {e}")
            return {"error": str(e)}
    
    def _get_pattern_performance(self, pattern_type: str, days_back: int = 14) -> Dict:
        """Get pattern performance metrics for risk assessment"""
        try:
            cutoff_time = int(time.time()) - (days_back * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT outcome, pips_result, confidence
                    FROM signals 
                    WHERE pattern_type = ? 
                        AND created_at > ?
                        AND outcome IN ('WIN', 'LOSS')
                """, (pattern_type, cutoff_time))
                
                signals = [dict(row) for row in cursor.fetchall()]
            
            if not signals:
                return {"sample_size": 0}
            
            # Calculate basic metrics
            wins = sum(1 for s in signals if s['outcome'] == 'WIN')
            total = len(signals)
            win_rate = wins / total
            
            # Calculate expectancy
            win_pips = [s['pips_result'] for s in signals if s['outcome'] == 'WIN']
            loss_pips = [abs(s['pips_result']) for s in signals if s['outcome'] == 'LOSS']
            
            avg_win = sum(win_pips) / len(win_pips) if win_pips else 0
            avg_loss = sum(loss_pips) / len(loss_pips) if loss_pips else 0
            
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            
            # Calculate confidence variance
            confidences = [s.get('confidence', 0.5) for s in signals]
            confidence_variance = np.var(confidences) if len(confidences) > 1 else 0
            
            return {
                "sample_size": total,
                "win_rate": win_rate,
                "expectancy": expectancy,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "confidence_variance": confidence_variance
            }
            
        except Exception as e:
            logger.error(f"Error getting pattern performance: {e}")
            return {"sample_size": 0}
    
    def _calculate_review_priority(self, review_hours: float, expectancy: float, sample_size: int) -> ReviewPriority:
        """Calculate review priority based on urgency factors"""
        # Urgent conditions
        if expectancy < -0.05 and sample_size >= 10:  # Significantly losing with decent sample
            return ReviewPriority.URGENT
        
        if review_hours <= 24:
            return ReviewPriority.HIGH
        elif review_hours <= 72:
            return ReviewPriority.MEDIUM
        elif review_hours <= 168:
            return ReviewPriority.LOW
        else:
            return ReviewPriority.SCHEDULED
    
    def update_pattern_schedule(self, pattern_type: str) -> Dict:
        """Update review schedule for a specific pattern"""
        try:
            # Analyze frequency
            frequency_analysis = self.analyze_pattern_frequency(pattern_type)
            
            if "error" in frequency_analysis:
                return frequency_analysis
            
            # Calculate risk-adjusted schedule
            risk_schedule = self.calculate_risk_adjusted_schedule(pattern_type, frequency_analysis)
            
            if "error" in risk_schedule:
                return risk_schedule
            
            # Calculate next review time
            current_time = int(time.time())
            review_hours = risk_schedule["risk_adjusted_hours"]
            next_review = current_time + (review_hours * 3600)
            
            # Update schedule
            if "pattern_schedules" not in self.schedule:
                self.schedule["pattern_schedules"] = {}
            
            self.schedule["pattern_schedules"][pattern_type] = {
                "frequency_analysis": frequency_analysis,
                "risk_schedule": risk_schedule,
                "next_review_timestamp": next_review,
                "next_review_datetime": datetime.fromtimestamp(next_review).isoformat(),
                "last_updated": current_time,
                "review_count": self.schedule["pattern_schedules"].get(pattern_type, {}).get("review_count", 0) + 1
            }
            
            self._save_schedule()
            
            logger.info(f"Updated schedule for {pattern_type}: next review in {review_hours:.1f} hours")
            
            return {
                "pattern_type": pattern_type,
                "schedule_updated": True,
                "next_review_hours": review_hours,
                "next_review_datetime": datetime.fromtimestamp(next_review).isoformat(),
                "priority": risk_schedule["review_priority"]
            }
            
        except Exception as e:
            logger.error(f"Error updating pattern schedule: {e}")
            return {"error": str(e)}
    
    def get_due_reviews(self, lookahead_hours: int = 24) -> List[Dict]:
        """Get patterns due for review within specified timeframe"""
        try:
            current_time = int(time.time())
            cutoff_time = current_time + (lookahead_hours * 3600)
            
            due_reviews = []
            
            for pattern_type, schedule_data in self.schedule.get("pattern_schedules", {}).items():
                next_review = schedule_data.get("next_review_timestamp", 0)
                
                if next_review <= cutoff_time:
                    hours_until_due = (next_review - current_time) / 3600
                    priority = schedule_data.get("risk_schedule", {}).get("review_priority", "MEDIUM")
                    
                    due_reviews.append({
                        "pattern_type": pattern_type,
                        "hours_until_due": round(hours_until_due, 1),
                        "priority": priority,
                        "is_overdue": hours_until_due < 0,
                        "next_review_datetime": schedule_data.get("next_review_datetime"),
                        "frequency_category": schedule_data.get("frequency_analysis", {}).get("frequency_category"),
                        "signals_per_day": schedule_data.get("frequency_analysis", {}).get("signals_per_day", 0)
                    })
            
            # Sort by priority and urgency
            priority_order = {"URGENT": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "SCHEDULED": 1}
            due_reviews.sort(key=lambda x: (priority_order.get(x["priority"], 0), -x["hours_until_due"]), reverse=True)
            
            return due_reviews
            
        except Exception as e:
            logger.error(f"Error getting due reviews: {e}")
            return []
    
    def update_all_pattern_schedules(self) -> Dict:
        """Update schedules for all patterns in the database"""
        try:
            # Get all unique patterns
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT pattern_type, COUNT(*) as signal_count
                    FROM signals 
                    WHERE created_at > ?
                    GROUP BY pattern_type
                    ORDER BY signal_count DESC
                """, (int(time.time()) - (30 * 24 * 3600),))  # Last 30 days
                
                patterns = cursor.fetchall()
            
            update_results = {}
            
            for pattern_type, count in patterns:
                result = self.update_pattern_schedule(pattern_type)
                update_results[pattern_type] = result
            
            summary = {
                "patterns_updated": len(update_results),
                "update_timestamp": int(time.time()),
                "results": update_results,
                "due_reviews": self.get_due_reviews(24)
            }
            
            logger.info(f"Updated schedules for {len(update_results)} patterns")
            return summary
            
        except Exception as e:
            logger.error(f"Error updating all pattern schedules: {e}")
            return {"error": str(e)}
    
    def get_schedule_overview(self) -> Dict:
        """Get overview of current review schedule"""
        try:
            current_time = int(time.time())
            
            # Analyze schedule distribution
            frequency_distribution = defaultdict(int)
            priority_distribution = defaultdict(int)
            overdue_count = 0
            
            for pattern_type, schedule_data in self.schedule.get("pattern_schedules", {}).items():
                # Frequency distribution
                freq_category = schedule_data.get("frequency_analysis", {}).get("frequency_category", "UNKNOWN")
                frequency_distribution[freq_category] += 1
                
                # Priority distribution
                priority = schedule_data.get("risk_schedule", {}).get("review_priority", "UNKNOWN")
                priority_distribution[priority] += 1
                
                # Overdue count
                next_review = schedule_data.get("next_review_timestamp", current_time)
                if next_review < current_time:
                    overdue_count += 1
            
            return {
                "total_patterns_scheduled": len(self.schedule.get("pattern_schedules", {})),
                "frequency_distribution": dict(frequency_distribution),
                "priority_distribution": dict(priority_distribution),
                "overdue_reviews": overdue_count,
                "due_within_24h": len(self.get_due_reviews(24)),
                "last_schedule_update": self.schedule.get("last_updated", 0),
                "generated_at": current_time
            }
            
        except Exception as e:
            logger.error(f"Error getting schedule overview: {e}")
            return {"error": str(e)}
    
    def export_review_schedule_report(self) -> str:
        """Export comprehensive review schedule report"""
        try:
            overview = self.get_schedule_overview()
            due_reviews = self.get_due_reviews(72)  # Next 3 days
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "generator": "AdaptiveReviewScheduler",
                "schedule_overview": overview,
                "due_reviews": due_reviews,
                "schedule_settings": {
                    "frequency_thresholds": {
                        "fast_signals_per_day": self.fast_threshold,
                        "medium_signals_per_day": self.medium_threshold
                    },
                    "review_intervals_hours": {k.value: v for k, v in self.review_intervals.items()},
                    "risk_adjustments": {
                        "high_risk_multiplier": self.high_risk_multiplier,
                        "poor_performance_multiplier": self.poor_performance_multiplier
                    }
                },
                "full_schedule": self.schedule
            }
            
            output_file = f"/root/HydraX-v2/review_schedule_report_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Review schedule report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting schedule report: {e}")
            return ""
    
    def start_background_scheduler(self):
        """Start background thread for automatic schedule updates"""
        def scheduler_worker():
            while True:
                try:
                    # Update schedules every 6 hours
                    time.sleep(6 * 3600)
                    self.update_all_pattern_schedules()
                    logger.info("Background schedule update completed")
                except Exception as e:
                    logger.error(f"Error in background scheduler: {e}")
        
        scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
        scheduler_thread.start()
        logger.info("Background scheduler started")

def main():
    """Run adaptive review scheduler"""
    scheduler = AdaptiveReviewScheduler()
    
    # Update all pattern schedules
    update_result = scheduler.update_all_pattern_schedules()
    
    if "error" in update_result:
        print(f"Error updating schedules: {update_result['error']}")
        return
    
    print("Adaptive Review Schedule Update Complete")
    print(f"Patterns updated: {update_result['patterns_updated']}")
    
    # Show due reviews
    due_reviews = update_result.get('due_reviews', [])
    if due_reviews:
        print(f"\nReviews Due (next 24 hours): {len(due_reviews)}")
        for review in due_reviews[:5]:  # Show top 5
            status = "OVERDUE" if review['is_overdue'] else f"Due in {review['hours_until_due']:.1f}h"
            print(f"  {review['pattern_type']}: {status} ({review['priority']} priority)")
    
    # Show schedule overview
    overview = scheduler.get_schedule_overview()
    print(f"\nSchedule Overview:")
    print(f"  Total patterns: {overview.get('total_patterns_scheduled', 0)}")
    print(f"  Overdue reviews: {overview.get('overdue_reviews', 0)}")
    
    freq_dist = overview.get('frequency_distribution', {})
    print(f"  Frequency distribution: {dict(freq_dist)}")
    
    # Export detailed report
    report_file = scheduler.export_review_schedule_report()
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()