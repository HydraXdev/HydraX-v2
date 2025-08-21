#!/usr/bin/env python3
"""
BITTEN Confidence Calibrator - Fix Miscalibrated Confidence Scores
Audits: Does 80% confidence actually win 80% of time?
Calculates calibration offsets per bucket (70-75, 75-80, 80-85, 85-90)
If 80% signals only win 62%, adjust future scores down by 18%
"""

import json
import time
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfidenceCalibrator:
    """
    Analyzes and corrects confidence score calibration.
    Ensures predicted confidence matches actual win rates.
    """
    
    def __init__(self, 
                 db_path: str = "/root/HydraX-v2/bitten.db",
                 calibration_file: str = "/root/HydraX-v2/confidence_calibration.json"):
        self.db_path = db_path
        self.calibration_file = calibration_file
        
        # Calibration buckets
        self.confidence_buckets = [
            (0.70, 0.75),  # 70-75%
            (0.75, 0.80),  # 75-80%
            (0.80, 0.85),  # 80-85%
            (0.85, 0.90),  # 85-90%
            (0.90, 0.95),  # 90-95%
            (0.95, 1.00),  # 95-100%
        ]
        
        # Calibration settings
        self.min_signals_per_bucket = 20  # Minimum signals for reliable calibration
        self.calibration_window_days = 30  # Days of data for calibration
        self.confidence_tolerance = 0.05  # ±5% tolerance before correction
        
        # Load existing calibration
        self.calibration_map = self._load_calibration_map()
        
        logger.info("ConfidenceCalibrator initialized with {} buckets".format(len(self.confidence_buckets)))
    
    def _load_calibration_map(self) -> Dict:
        """Load existing calibration map"""
        try:
            with open(self.calibration_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "calibration_offsets": {},
                "last_updated": 0,
                "version": "1.0"
            }
        except Exception as e:
            logger.error(f"Error loading calibration map: {e}")
            return {"calibration_offsets": {}, "last_updated": 0}
    
    def _save_calibration_map(self):
        """Save calibration map to file"""
        try:
            self.calibration_map["last_updated"] = int(time.time())
            with open(self.calibration_file, 'w') as f:
                json.dump(self.calibration_map, f, indent=2)
            logger.info(f"Calibration map saved to {self.calibration_file}")
        except Exception as e:
            logger.error(f"Error saving calibration map: {e}")
    
    def analyze_confidence_calibration(self, days_back: int = None) -> Dict:
        """
        Analyze confidence calibration across all buckets.
        Returns calibration analysis and recommended adjustments.
        """
        days_back = days_back or self.calibration_window_days
        cutoff_time = int(time.time()) - (days_back * 24 * 3600)
        
        try:
            # Get signals with outcomes
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT signal_id, confidence, outcome, pattern_type, 
                           symbol, created_at, pips_result
                    FROM signals 
                    WHERE created_at > ? 
                        AND confidence IS NOT NULL 
                        AND outcome IN ('WIN', 'LOSS')
                        AND confidence >= 0.70
                    ORDER BY created_at DESC
                """, (cutoff_time,))
                
                signals = [dict(row) for row in cursor.fetchall()]
            
            if not signals:
                return {"error": "No signals found for calibration analysis"}
            
            # Analyze each bucket
            bucket_analysis = {}
            overall_stats = {
                "total_signals": len(signals),
                "overall_win_rate": sum(1 for s in signals if s['outcome'] == 'WIN') / len(signals),
                "avg_confidence": sum(s['confidence'] for s in signals) / len(signals)
            }
            
            for bucket_min, bucket_max in self.confidence_buckets:
                bucket_signals = [
                    s for s in signals 
                    if bucket_min <= s['confidence'] < bucket_max
                ]
                
                if len(bucket_signals) >= self.min_signals_per_bucket:
                    analysis = self._analyze_bucket(bucket_signals, bucket_min, bucket_max)
                    bucket_key = f"{bucket_min:.0%}-{bucket_max:.0%}"
                    bucket_analysis[bucket_key] = analysis
            
            # Calculate global calibration metrics
            calibration_metrics = self._calculate_calibration_metrics(signals)
            
            return {
                "analysis_period_days": days_back,
                "overall_statistics": overall_stats,
                "bucket_analysis": bucket_analysis,
                "calibration_metrics": calibration_metrics,
                "calibration_recommendations": self._generate_recommendations(bucket_analysis),
                "calculated_at": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing confidence calibration: {e}")
            return {"error": str(e)}
    
    def _analyze_bucket(self, signals: List[Dict], bucket_min: float, bucket_max: float) -> Dict:
        """Analyze calibration for a specific confidence bucket"""
        total_signals = len(signals)
        wins = sum(1 for s in signals if s['outcome'] == 'WIN')
        actual_win_rate = wins / total_signals
        
        # Expected win rate is the midpoint of the bucket
        expected_win_rate = (bucket_min + bucket_max) / 2
        
        # Calibration error
        calibration_error = actual_win_rate - expected_win_rate
        calibration_error_pct = calibration_error * 100
        
        # Statistical significance
        confidence_interval = self._calculate_confidence_interval(wins, total_signals)
        is_significantly_miscalibrated = not (
            confidence_interval[0] <= expected_win_rate <= confidence_interval[1]
        )
        
        # Performance by pattern type
        pattern_performance = defaultdict(list)
        for signal in signals:
            pattern_performance[signal['pattern_type']].append(signal['outcome'] == 'WIN')
        
        pattern_stats = {}
        for pattern, outcomes in pattern_performance.items():
            if len(outcomes) >= 5:  # Minimum for pattern analysis
                pattern_win_rate = sum(outcomes) / len(outcomes)
                pattern_stats[pattern] = {
                    "count": len(outcomes),
                    "win_rate": pattern_win_rate,
                    "calibration_error": pattern_win_rate - expected_win_rate
                }
        
        # Calculate recommended adjustment
        if abs(calibration_error) > self.confidence_tolerance and is_significantly_miscalibrated:
            recommended_adjustment = -calibration_error  # Negative because we adjust confidence down if win rate is lower
        else:
            recommended_adjustment = 0.0
        
        return {
            "bucket_range": f"{bucket_min:.0%}-{bucket_max:.0%}",
            "total_signals": total_signals,
            "wins": wins,
            "losses": total_signals - wins,
            "actual_win_rate": round(actual_win_rate, 4),
            "expected_win_rate": round(expected_win_rate, 4),
            "calibration_error": round(calibration_error, 4),
            "calibration_error_percentage": round(calibration_error_pct, 1),
            "confidence_interval": confidence_interval,
            "is_significantly_miscalibrated": is_significantly_miscalibrated,
            "recommended_adjustment": round(recommended_adjustment, 4),
            "pattern_performance": pattern_stats
        }
    
    def _calculate_confidence_interval(self, wins: int, total: int, confidence_level: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval for win rate"""
        if total == 0:
            return (0.0, 0.0)
        
        win_rate = wins / total
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin_error = z_score * np.sqrt(win_rate * (1 - win_rate) / total)
        
        lower_bound = max(0.0, win_rate - margin_error)
        upper_bound = min(1.0, win_rate + margin_error)
        
        return (round(lower_bound, 4), round(upper_bound, 4))
    
    def _calculate_calibration_metrics(self, signals: List[Dict]) -> Dict:
        """Calculate overall calibration metrics"""
        # Reliability diagram data
        confidence_values = [s['confidence'] for s in signals]
        outcomes = [1 if s['outcome'] == 'WIN' else 0 for s in signals]
        
        # Bin signals by confidence
        bins = np.linspace(0.7, 1.0, 7)  # 6 bins from 70% to 100%
        bin_indices = np.digitize(confidence_values, bins) - 1
        
        bin_stats = []
        for i in range(len(bins) - 1):
            bin_mask = bin_indices == i
            if np.sum(bin_mask) > 0:
                bin_confidence = np.mean(np.array(confidence_values)[bin_mask])
                bin_accuracy = np.mean(np.array(outcomes)[bin_mask])
                bin_count = np.sum(bin_mask)
                
                bin_stats.append({
                    "bin_center": round(bin_confidence, 3),
                    "accuracy": round(bin_accuracy, 3),
                    "count": int(bin_count),
                    "calibration_error": round(bin_accuracy - bin_confidence, 3)
                })
        
        # Expected Calibration Error (ECE)
        ece = 0.0
        total_samples = len(signals)
        for bin_stat in bin_stats:
            weight = bin_stat["count"] / total_samples
            ece += weight * abs(bin_stat["calibration_error"])
        
        # Overconfidence/Underconfidence
        avg_confidence = np.mean(confidence_values)
        avg_accuracy = np.mean(outcomes)
        overconfidence = avg_confidence - avg_accuracy
        
        return {
            "expected_calibration_error": round(ece, 4),
            "average_confidence": round(avg_confidence, 4),
            "average_accuracy": round(avg_accuracy, 4),
            "overconfidence": round(overconfidence, 4),
            "reliability_diagram": bin_stats,
            "is_well_calibrated": ece < 0.05,  # ECE < 5% is considered well calibrated
            "calibration_quality": "excellent" if ece < 0.02 else "good" if ece < 0.05 else "poor"
        }
    
    def _generate_recommendations(self, bucket_analysis: Dict) -> List[Dict]:
        """Generate calibration recommendations"""
        recommendations = []
        
        for bucket, analysis in bucket_analysis.items():
            if analysis["is_significantly_miscalibrated"]:
                adjustment = analysis["recommended_adjustment"]
                error_pct = analysis["calibration_error_percentage"]
                
                if abs(error_pct) > 10:  # More than 10% error
                    priority = "HIGH"
                elif abs(error_pct) > 5:  # More than 5% error
                    priority = "MEDIUM"
                else:
                    priority = "LOW"
                
                recommendations.append({
                    "bucket": bucket,
                    "priority": priority,
                    "issue": "overconfident" if error_pct < 0 else "underconfident",
                    "error_percentage": error_pct,
                    "recommended_adjustment": adjustment,
                    "description": f"Bucket {bucket} is {abs(error_pct):.1f}% {'overconfident' if error_pct < 0 else 'underconfident'}"
                })
        
        # Sort by priority and error magnitude
        priority_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        recommendations.sort(key=lambda x: (priority_order[x["priority"]], abs(x["error_percentage"])), reverse=True)
        
        return recommendations
    
    def apply_calibration_adjustments(self, recommendations: List[Dict]) -> Dict:
        """Apply calibration adjustments to the calibration map"""
        try:
            adjustments_applied = 0
            
            for rec in recommendations:
                if rec["priority"] in ["HIGH", "MEDIUM"]:
                    bucket = rec["bucket"]
                    adjustment = rec["recommended_adjustment"]
                    
                    # Update calibration map
                    if "calibration_offsets" not in self.calibration_map:
                        self.calibration_map["calibration_offsets"] = {}
                    
                    self.calibration_map["calibration_offsets"][bucket] = adjustment
                    adjustments_applied += 1
                    
                    logger.info(f"Applied calibration adjustment for {bucket}: {adjustment:+.4f}")
            
            # Save calibration map
            if adjustments_applied > 0:
                self._save_calibration_map()
            
            return {
                "adjustments_applied": adjustments_applied,
                "calibration_map_updated": adjustments_applied > 0,
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error applying calibration adjustments: {e}")
            return {"error": str(e)}
    
    def calibrate_confidence(self, confidence: float, pattern_type: str = None) -> float:
        """
        Apply calibration adjustment to a confidence score.
        
        Args:
            confidence: Original confidence score
            pattern_type: Optional pattern type for pattern-specific adjustments
        
        Returns:
            Calibrated confidence score
        """
        try:
            # Find appropriate bucket
            for bucket_min, bucket_max in self.confidence_buckets:
                if bucket_min <= confidence < bucket_max:
                    bucket_key = f"{bucket_min:.0%}-{bucket_max:.0%}"
                    
                    # Get calibration offset
                    offset = self.calibration_map.get("calibration_offsets", {}).get(bucket_key, 0.0)
                    
                    # Apply adjustment
                    calibrated_confidence = confidence + offset
                    
                    # Ensure bounds
                    calibrated_confidence = max(0.0, min(1.0, calibrated_confidence))
                    
                    return calibrated_confidence
            
            # If no bucket found, return original
            return confidence
            
        except Exception as e:
            logger.error(f"Error calibrating confidence: {e}")
            return confidence
    
    def get_calibration_status(self) -> Dict:
        """Get current calibration status"""
        try:
            analysis = self.analyze_confidence_calibration()
            
            if "error" in analysis:
                return analysis
            
            # Summary stats
            bucket_count = len(analysis["bucket_analysis"])
            miscalibrated_buckets = sum(
                1 for bucket in analysis["bucket_analysis"].values()
                if bucket["is_significantly_miscalibrated"]
            )
            
            avg_calibration_error = np.mean([
                abs(bucket["calibration_error"])
                for bucket in analysis["bucket_analysis"].values()
            ])
            
            return {
                "calibration_quality": analysis["calibration_metrics"]["calibration_quality"],
                "expected_calibration_error": analysis["calibration_metrics"]["expected_calibration_error"],
                "buckets_analyzed": bucket_count,
                "miscalibrated_buckets": miscalibrated_buckets,
                "avg_calibration_error": round(avg_calibration_error, 4),
                "overconfidence": analysis["calibration_metrics"]["overconfidence"],
                "recommendations_count": len(analysis["calibration_recommendations"]),
                "last_updated": self.calibration_map.get("last_updated", 0),
                "active_adjustments": len(self.calibration_map.get("calibration_offsets", {}))
            }
            
        except Exception as e:
            logger.error(f"Error getting calibration status: {e}")
            return {"error": str(e)}
    
    def run_calibration_update(self) -> Dict:
        """Run full calibration analysis and update"""
        try:
            logger.info("Starting confidence calibration update...")
            
            # Analyze calibration
            analysis = self.analyze_confidence_calibration()
            if "error" in analysis:
                return analysis
            
            # Apply adjustments
            recommendations = analysis["calibration_recommendations"]
            adjustment_result = self.apply_calibration_adjustments(recommendations)
            
            # Generate summary
            summary = {
                "calibration_update_completed": True,
                "analysis_summary": {
                    "total_signals": analysis["overall_statistics"]["total_signals"],
                    "buckets_analyzed": len(analysis["bucket_analysis"]),
                    "calibration_quality": analysis["calibration_metrics"]["calibration_quality"],
                    "expected_calibration_error": analysis["calibration_metrics"]["expected_calibration_error"]
                },
                "adjustments_summary": adjustment_result,
                "recommendations": recommendations[:5],  # Top 5 recommendations
                "timestamp": int(time.time())
            }
            
            logger.info(f"Calibration update completed. Applied {adjustment_result.get('adjustments_applied', 0)} adjustments.")
            return summary
            
        except Exception as e:
            logger.error(f"Error in calibration update: {e}")
            return {"error": str(e)}
    
    def export_calibration_report(self) -> str:
        """Export comprehensive calibration report"""
        try:
            analysis = self.analyze_confidence_calibration()
            status = self.get_calibration_status()
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "generator": "ConfidenceCalibrator",
                "calibration_analysis": analysis,
                "calibration_status": status,
                "current_calibration_map": self.calibration_map,
                "system_settings": {
                    "confidence_buckets": [f"{b[0]:.0%}-{b[1]:.0%}" for b in self.confidence_buckets],
                    "min_signals_per_bucket": self.min_signals_per_bucket,
                    "calibration_window_days": self.calibration_window_days,
                    "confidence_tolerance": self.confidence_tolerance
                }
            }
            
            output_file = f"/root/HydraX-v2/confidence_calibration_report_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Calibration report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting calibration report: {e}")
            return ""

def main():
    """Run confidence calibration analysis"""
    calibrator = ConfidenceCalibrator()
    
    # Run calibration update
    result = calibrator.run_calibration_update()
    
    if "error" in result:
        print(f"Error in calibration: {result['error']}")
        return
    
    print("Confidence Calibration Analysis Complete")
    print(f"Total signals analyzed: {result['analysis_summary']['total_signals']}")
    print(f"Calibration quality: {result['analysis_summary']['calibration_quality']}")
    print(f"Adjustments applied: {result['adjustments_summary'].get('adjustments_applied', 0)}")
    
    # Show top recommendations
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"\nTop Calibration Issues:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec['bucket']}: {rec['error_percentage']:+.1f}% error ({rec['priority']} priority)")
    
    # Export detailed report
    report_file = calibrator.export_calibration_report()
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()