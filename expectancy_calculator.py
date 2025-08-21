#!/usr/bin/env python3
"""
BITTEN Expectancy Calculator - Core EV Calculation Engine
Calculates Expected Value = (Win% × AvgWin) - (Loss% × AvgLoss)
Uses rolling windows to prevent variance from killing profitable patterns.
"""

import json
import time
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExpectancyCalculator:
    """
    Core expectancy calculation engine with rolling window analysis.
    Prevents killing winners during normal variance periods.
    """
    
    def __init__(self, db_path: str = "/root/HydraX-v2/bitten.db"):
        self.db_path = db_path
        self.rolling_window_size = 50  # Minimum signals for analysis
        self.extended_window_size = 100  # Extended analysis window
        self.safety_zone_pct = 0.05  # ±5% of breakeven
        
        # Rolling signal storage per pattern
        self.pattern_signals = defaultdict(lambda: deque(maxlen=self.extended_window_size))
        
        # Performance cache
        self.performance_cache = {}
        self.last_cache_update = 0
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("ExpectancyCalculator initialized with safety zone ±{:.1%}".format(self.safety_zone_pct))
    
    def calculate_expectancy(self, pattern_type: str, symbol: str = None, window_size: int = None) -> Dict:
        """
        Calculate Expected Value for a pattern with sophisticated variance protection.
        
        Args:
            pattern_type: Pattern name (LIQUIDITY_SWEEP_REVERSAL, etc.)
            symbol: Optional symbol filter
            window_size: Override default window size
        
        Returns:
            Dict with expectancy metrics and safety recommendations
        """
        try:
            window_size = window_size or self.rolling_window_size
            signals = self._get_pattern_signals(pattern_type, symbol, window_size)
            
            if len(signals) < window_size:
                return {
                    "pattern_type": pattern_type,
                    "symbol": symbol,
                    "expectancy": None,
                    "sample_size": len(signals),
                    "status": "INSUFFICIENT_DATA",
                    "recommendation": "COLLECT_MORE_DATA",
                    "min_required": window_size
                }
            
            # Calculate core metrics
            wins = [s for s in signals if s['outcome'] == 'WIN']
            losses = [s for s in signals if s['outcome'] == 'LOSS']
            
            win_rate = len(wins) / len(signals)
            loss_rate = len(losses) / len(signals)
            
            avg_win = sum(s['pips_result'] for s in wins) / len(wins) if wins else 0
            avg_loss = abs(sum(s['pips_result'] for s in losses)) / len(losses) if losses else 0
            
            # Core expectancy calculation
            expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
            
            # Risk/Reward ratio
            risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
            
            # Safety analysis
            safety_analysis = self._analyze_safety_zone(expectancy)
            
            # Variance analysis
            variance_analysis = self._analyze_variance(signals)
            
            # Trend analysis (improving/declining)
            trend_analysis = self._analyze_trend(signals)
            
            result = {
                "pattern_type": pattern_type,
                "symbol": symbol,
                "expectancy": round(expectancy, 4),
                "win_rate": round(win_rate, 4),
                "loss_rate": round(loss_rate, 4),
                "avg_win_pips": round(avg_win, 2),
                "avg_loss_pips": round(avg_loss, 2),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "sample_size": len(signals),
                "window_size": window_size,
                **safety_analysis,
                **variance_analysis,
                **trend_analysis,
                "calculated_at": int(time.time())
            }
            
            logger.info(f"Calculated expectancy for {pattern_type}: {expectancy:.4f} (Safety: {safety_analysis['safety_status']})")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating expectancy for {pattern_type}: {e}")
            return {
                "pattern_type": pattern_type,
                "expectancy": None,
                "status": "ERROR",
                "error": str(e)
            }
    
    def _get_pattern_signals(self, pattern_type: str, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Get recent signals for pattern analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                SELECT 
                    signal_id,
                    symbol,
                    direction,
                    entry_price,
                    stop_pips,
                    target_pips,
                    confidence,
                    pattern_type,
                    created_at,
                    outcome,
                    pips_result,
                    resolution_time
                FROM signals 
                WHERE pattern_type = ? 
                    AND outcome IN ('WIN', 'LOSS')
                    AND pips_result IS NOT NULL
                """
                
                params = [pattern_type]
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error fetching pattern signals: {e}")
            return []
    
    def _analyze_safety_zone(self, expectancy: float) -> Dict:
        """
        Analyze if pattern is in safety zone (±5% of breakeven).
        Patterns in safety zone should NOT be eliminated due to variance.
        """
        safety_threshold = self.safety_zone_pct
        
        if abs(expectancy) <= safety_threshold:
            return {
                "safety_status": "SAFE_ZONE",
                "safety_recommendation": "DO_NOT_ELIMINATE",
                "safety_reason": f"Within ±{safety_threshold:.1%} of breakeven - likely variance",
                "elimination_risk": "HIGH"
            }
        elif expectancy > safety_threshold:
            return {
                "safety_status": "PROFITABLE",
                "safety_recommendation": "KEEP_ACTIVE",
                "safety_reason": f"Expectancy {expectancy:.4f} > {safety_threshold:.4f}",
                "elimination_risk": "NONE"
            }
        else:  # expectancy < -safety_threshold
            return {
                "safety_status": "UNPROFITABLE",
                "safety_recommendation": "CONSIDER_QUARANTINE",
                "safety_reason": f"Expectancy {expectancy:.4f} < -{safety_threshold:.4f}",
                "elimination_risk": "LOW"
            }
    
    def _analyze_variance(self, signals: List[Dict]) -> Dict:
        """Analyze variance patterns to detect temporary downswings"""
        if len(signals) < 10:
            return {"variance_analysis": "insufficient_data"}
        
        # Calculate rolling expectancy over smaller windows
        window_size = min(20, len(signals) // 3)
        rolling_expectancies = []
        
        for i in range(window_size, len(signals) + 1):
            window_signals = signals[i-window_size:i]
            wins = [s for s in window_signals if s['outcome'] == 'WIN']
            losses = [s for s in window_signals if s['outcome'] == 'LOSS']
            
            if len(window_signals) > 0:
                win_rate = len(wins) / len(window_signals)
                loss_rate = len(losses) / len(window_signals)
                avg_win = sum(s['pips_result'] for s in wins) / len(wins) if wins else 0
                avg_loss = abs(sum(s['pips_result'] for s in losses)) / len(losses) if losses else 0
                expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
                rolling_expectancies.append(expectancy)
        
        if not rolling_expectancies:
            return {"variance_analysis": "insufficient_windows"}
        
        # Calculate variance metrics
        avg_rolling_expectancy = sum(rolling_expectancies) / len(rolling_expectancies)
        variance = sum((x - avg_rolling_expectancy) ** 2 for x in rolling_expectancies) / len(rolling_expectancies)
        volatility = variance ** 0.5
        
        # Detect if current period is unusual
        recent_expectancy = rolling_expectancies[-1] if rolling_expectancies else 0
        z_score = (recent_expectancy - avg_rolling_expectancy) / volatility if volatility > 0 else 0
        
        return {
            "variance_analysis": {
                "rolling_volatility": round(volatility, 4),
                "recent_z_score": round(z_score, 2),
                "is_unusual_period": abs(z_score) > 2.0,
                "variance_recommendation": "WAIT_FOR_NORMALIZATION" if abs(z_score) > 2.0 else "NORMAL_VARIANCE"
            }
        }
    
    def _analyze_trend(self, signals: List[Dict]) -> Dict:
        """Analyze if pattern performance is improving or declining"""
        if len(signals) < 30:
            return {"trend_analysis": "insufficient_data"}
        
        # Split into first half and second half
        mid_point = len(signals) // 2
        first_half = signals[:mid_point]
        second_half = signals[mid_point:]
        
        def calc_simple_expectancy(signal_list):
            if not signal_list:
                return 0
            wins = [s for s in signal_list if s['outcome'] == 'WIN']
            win_rate = len(wins) / len(signal_list)
            return win_rate  # Simplified for trend analysis
        
        first_half_perf = calc_simple_expectancy(first_half)
        second_half_perf = calc_simple_expectancy(second_half)
        
        trend_direction = "IMPROVING" if second_half_perf > first_half_perf else "DECLINING"
        trend_magnitude = abs(second_half_perf - first_half_perf)
        
        return {
            "trend_analysis": {
                "direction": trend_direction,
                "magnitude": round(trend_magnitude, 4),
                "first_half_winrate": round(first_half_perf, 4),
                "second_half_winrate": round(second_half_perf, 4),
                "is_significant": trend_magnitude > 0.1
            }
        }
    
    def get_all_pattern_expectancies(self, min_signals: int = None) -> Dict[str, Dict]:
        """Get expectancy analysis for all patterns"""
        min_signals = min_signals or self.rolling_window_size
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT pattern_type, COUNT(*) as signal_count
                    FROM signals 
                    WHERE outcome IN ('WIN', 'LOSS')
                    GROUP BY pattern_type
                    HAVING COUNT(*) >= ?
                """, (min_signals,))
                
                patterns = cursor.fetchall()
            
            results = {}
            for pattern_type, count in patterns:
                results[pattern_type] = self.calculate_expectancy(pattern_type)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting all pattern expectancies: {e}")
            return {}
    
    def export_expectancy_report(self, output_file: str = None) -> str:
        """Export comprehensive expectancy report"""
        output_file = output_file or f"/root/HydraX-v2/expectancy_report_{int(time.time())}.json"
        
        try:
            all_expectancies = self.get_all_pattern_expectancies()
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "generator": "ExpectancyCalculator",
                "safety_zone_threshold": self.safety_zone_pct,
                "rolling_window_size": self.rolling_window_size,
                "extended_window_size": self.extended_window_size,
                "pattern_analysis": all_expectancies,
                "summary": {
                    "total_patterns_analyzed": len(all_expectancies),
                    "profitable_patterns": len([p for p in all_expectancies.values() if p.get('expectancy', 0) > 0]),
                    "safe_zone_patterns": len([p for p in all_expectancies.values() if p.get('safety_status') == 'SAFE_ZONE']),
                    "unprofitable_patterns": len([p for p in all_expectancies.values() if p.get('expectancy', 0) < -self.safety_zone_pct])
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Expectancy report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting expectancy report: {e}")
            return ""

def main():
    """Run expectancy analysis"""
    calculator = ExpectancyCalculator()
    
    # Generate comprehensive report
    report_file = calculator.export_expectancy_report()
    print(f"Expectancy analysis complete. Report saved to: {report_file}")
    
    # Show quick summary
    expectancies = calculator.get_all_pattern_expectancies()
    print(f"\nQuick Summary ({len(expectancies)} patterns analyzed):")
    for pattern, data in expectancies.items():
        if data.get('expectancy') is not None:
            print(f"  {pattern}: EV={data['expectancy']:.4f}, WR={data['win_rate']:.2%}, Status={data.get('safety_status', 'UNKNOWN')}")

if __name__ == "__main__":
    main()