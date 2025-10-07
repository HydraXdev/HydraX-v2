#!/usr/bin/env python3
"""
Rapid Elimination Analyzer - Identifies patterns to kill (<40% win rate)
Analyzes comprehensive_tracking.jsonl to find poor performing patterns and conditions
"""

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/root/HydraX-v2/rapid_elimination.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class RapidEliminationAnalyzer:
    """Analyzes signal patterns to identify what should be eliminated"""

    def __init__(self, elimination_threshold: float = 40.0):
        self.elimination_threshold = elimination_threshold
        self.tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
        self.kill_list_file = "/root/HydraX-v2/pattern_kill_list.json"

    def load_all_signals(self) -> List[Dict]:
        """Load all signals from tracking file"""
        signals = []
        try:
            with open(self.tracking_file, "r") as f:
                for line in f:
                    if line.strip():
                        signals.append(json.loads(line))
        except FileNotFoundError:
            logger.warning("No tracking file found")
        except Exception as e:
            logger.error(f"Error loading signals: {e}")

        logger.info(f"📊 Loaded {len(signals)} signals for analysis")
        return signals

    def analyze_pattern_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by pattern type"""
        pattern_stats = defaultdict(
            lambda: {
                "total": 0,
                "tp_30min": 0,
                "sl_30min": 0,
                "tp_60min": 0,
                "sl_60min": 0,
                "win_rate_30min": 0.0,
                "win_rate_60min": 0.0,
                "avg_confidence": 0.0,
            }
        )

        for signal in signals:
            pattern = signal.get("pattern_type", "UNKNOWN")
            confidence = signal.get("confidence_score", 0)
            outcome_30 = signal.get("outcome_30min")
            outcome_60 = signal.get("outcome_60min")

            pattern_stats[pattern]["total"] += 1
            pattern_stats[pattern]["avg_confidence"] += confidence

            if outcome_30 == "TP_HIT":
                pattern_stats[pattern]["tp_30min"] += 1
            elif outcome_30 == "SL_HIT":
                pattern_stats[pattern]["sl_30min"] += 1

            if outcome_60 == "TP_HIT":
                pattern_stats[pattern]["tp_60min"] += 1
            elif outcome_60 == "SL_HIT":
                pattern_stats[pattern]["sl_60min"] += 1

        # Calculate win rates and averages
        for pattern, stats in pattern_stats.items():
            if stats["total"] > 0:
                stats["avg_confidence"] = round(stats["avg_confidence"] / stats["total"], 1)

            total_closed_30 = stats["tp_30min"] + stats["sl_30min"]
            if total_closed_30 > 0:
                stats["win_rate_30min"] = round(stats["tp_30min"] / total_closed_30 * 100, 1)

            total_closed_60 = stats["tp_60min"] + stats["sl_60min"]
            if total_closed_60 > 0:
                stats["win_rate_60min"] = round(stats["tp_60min"] / total_closed_60 * 100, 1)

        return dict(pattern_stats)

    def analyze_session_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by trading session"""
        session_stats = defaultdict(
            lambda: {
                "total": 0,
                "tp_30min": 0,
                "sl_30min": 0,
                "tp_60min": 0,
                "sl_60min": 0,
                "win_rate_30min": 0.0,
                "win_rate_60min": 0.0,
            }
        )

        for signal in signals:
            session = signal.get("session", "UNKNOWN")
            outcome_30 = signal.get("outcome_30min")
            outcome_60 = signal.get("outcome_60min")

            session_stats[session]["total"] += 1

            if outcome_30 == "TP_HIT":
                session_stats[session]["tp_30min"] += 1
            elif outcome_30 == "SL_HIT":
                session_stats[session]["sl_30min"] += 1

            if outcome_60 == "TP_HIT":
                session_stats[session]["tp_60min"] += 1
            elif outcome_60 == "SL_HIT":
                session_stats[session]["sl_60min"] += 1

        # Calculate win rates
        for session, stats in session_stats.items():
            total_closed_30 = stats["tp_30min"] + stats["sl_30min"]
            if total_closed_30 > 0:
                stats["win_rate_30min"] = round(stats["tp_30min"] / total_closed_30 * 100, 1)

            total_closed_60 = stats["tp_60min"] + stats["sl_60min"]
            if total_closed_60 > 0:
                stats["win_rate_60min"] = round(stats["tp_60min"] / total_closed_60 * 100, 1)

        return dict(session_stats)

    def analyze_pair_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by currency pair"""
        pair_stats = defaultdict(
            lambda: {
                "total": 0,
                "tp_30min": 0,
                "sl_30min": 0,
                "tp_60min": 0,
                "sl_60min": 0,
                "win_rate_30min": 0.0,
                "win_rate_60min": 0.0,
            }
        )

        for signal in signals:
            pair = signal.get("pair", "UNKNOWN")
            outcome_30 = signal.get("outcome_30min")
            outcome_60 = signal.get("outcome_60min")

            pair_stats[pair]["total"] += 1

            if outcome_30 == "TP_HIT":
                pair_stats[pair]["tp_30min"] += 1
            elif outcome_30 == "SL_HIT":
                pair_stats[pair]["sl_30min"] += 1

            if outcome_60 == "TP_HIT":
                pair_stats[pair]["tp_60min"] += 1
            elif outcome_60 == "SL_HIT":
                pair_stats[pair]["sl_60min"] += 1

        # Calculate win rates
        for pair, stats in pair_stats.items():
            total_closed_30 = stats["tp_30min"] + stats["sl_30min"]
            if total_closed_30 > 0:
                stats["win_rate_30min"] = round(stats["tp_30min"] / total_closed_30 * 100, 1)

            total_closed_60 = stats["tp_60min"] + stats["sl_60min"]
            if total_closed_60 > 0:
                stats["win_rate_60min"] = round(stats["tp_60min"] / total_closed_60 * 100, 1)

        return dict(pair_stats)

    def analyze_confidence_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by confidence ranges"""
        confidence_ranges = {
            "50-60%": [50, 60],
            "60-70%": [60, 70],
            "70-80%": [70, 80],
            "80-90%": [80, 90],
            "90-100%": [90, 100],
        }

        range_stats = defaultdict(
            lambda: {
                "total": 0,
                "tp_30min": 0,
                "sl_30min": 0,
                "tp_60min": 0,
                "sl_60min": 0,
                "win_rate_30min": 0.0,
                "win_rate_60min": 0.0,
            }
        )

        for signal in signals:
            confidence = signal.get("confidence_score", 0)
            outcome_30 = signal.get("outcome_30min")
            outcome_60 = signal.get("outcome_60min")

            # Find which range this confidence falls into
            for range_name, (min_conf, max_conf) in confidence_ranges.items():
                if min_conf <= confidence < max_conf:
                    range_stats[range_name]["total"] += 1

                    if outcome_30 == "TP_HIT":
                        range_stats[range_name]["tp_30min"] += 1
                    elif outcome_30 == "SL_HIT":
                        range_stats[range_name]["sl_30min"] += 1

                    if outcome_60 == "TP_HIT":
                        range_stats[range_name]["tp_60min"] += 1
                    elif outcome_60 == "SL_HIT":
                        range_stats[range_name]["sl_60min"] += 1
                    break

        # Calculate win rates
        for range_name, stats in range_stats.items():
            total_closed_30 = stats["tp_30min"] + stats["sl_30min"]
            if total_closed_30 > 0:
                stats["win_rate_30min"] = round(stats["tp_30min"] / total_closed_30 * 100, 1)

            total_closed_60 = stats["tp_60min"] + stats["sl_60min"]
            if total_closed_60 > 0:
                stats["win_rate_60min"] = round(stats["tp_60min"] / total_closed_60 * 100, 1)

        return dict(range_stats)

    def identify_elimination_candidates(self, analysis: Dict) -> Dict:
        """Identify patterns/conditions that should be eliminated"""
        kill_list = {
            "patterns_to_kill": [],
            "sessions_to_avoid": [],
            "pairs_to_avoid": [],
            "confidence_ranges_to_avoid": [],
            "reasons": [],
        }

        # Check patterns for elimination
        pattern_stats = analysis.get("patterns", {})
        for pattern, stats in pattern_stats.items():
            win_rate_30 = stats.get("win_rate_30min", 0)
            win_rate_60 = stats.get("win_rate_60min", 0)
            total = stats.get("total", 0)

            # Eliminate if win rate is below threshold and we have enough data
            if total >= 10:  # Require at least 10 signals
                if win_rate_30 < self.elimination_threshold:
                    kill_list["patterns_to_kill"].append(
                        {
                            "pattern": pattern,
                            "win_rate_30min": win_rate_30,
                            "win_rate_60min": win_rate_60,
                            "total_signals": total,
                            "reason": f"Win rate {win_rate_30}% below {self.elimination_threshold}% threshold",
                        }
                    )
                    kill_list["reasons"].append(f"KILL PATTERN: {pattern} ({win_rate_30}% win rate)")

        # Check sessions for elimination
        session_stats = analysis.get("sessions", {})
        for session, stats in session_stats.items():
            win_rate_30 = stats.get("win_rate_30min", 0)
            total = stats.get("total", 0)

            if total >= 20 and win_rate_30 < self.elimination_threshold:
                kill_list["sessions_to_avoid"].append(
                    {
                        "session": session,
                        "win_rate_30min": win_rate_30,
                        "total_signals": total,
                        "reason": f"Session performs below {self.elimination_threshold}% threshold",
                    }
                )
                kill_list["reasons"].append(f"AVOID SESSION: {session} ({win_rate_30}% win rate)")

        # Check pairs for elimination
        pair_stats = analysis.get("pairs", {})
        for pair, stats in pair_stats.items():
            win_rate_30 = stats.get("win_rate_30min", 0)
            total = stats.get("total", 0)

            if total >= 15 and win_rate_30 < self.elimination_threshold:
                kill_list["pairs_to_avoid"].append(
                    {
                        "pair": pair,
                        "win_rate_30min": win_rate_30,
                        "total_signals": total,
                        "reason": f"Pair performs below {self.elimination_threshold}% threshold",
                    }
                )
                kill_list["reasons"].append(f"AVOID PAIR: {pair} ({win_rate_30}% win rate)")

        # Check confidence ranges
        confidence_stats = analysis.get("confidence_ranges", {})
        for range_name, stats in confidence_stats.items():
            win_rate_30 = stats.get("win_rate_30min", 0)
            total = stats.get("total", 0)

            if total >= 10 and win_rate_30 < self.elimination_threshold:
                kill_list["confidence_ranges_to_avoid"].append(
                    {
                        "range": range_name,
                        "win_rate_30min": win_rate_30,
                        "total_signals": total,
                        "reason": f"Confidence range performs below {self.elimination_threshold}% threshold",
                    }
                )
                kill_list["reasons"].append(f"AVOID CONFIDENCE: {range_name} ({win_rate_30}% win rate)")

        return kill_list

    def save_kill_list(self, kill_list: Dict):
        """Save elimination candidates to file"""
        try:
            with open(self.kill_list_file, "w") as f:
                json.dump(kill_list, f, indent=2)
            logger.info(f"💾 Kill list saved to {self.kill_list_file}")
        except Exception as e:
            logger.error(f"❌ Error saving kill list: {e}")

    def run_analysis(self) -> Dict:
        """Run complete rapid elimination analysis"""
        logger.info(f"🎯 Starting rapid elimination analysis (threshold: {self.elimination_threshold}%)...")

        # Load all signals
        signals = self.load_all_signals()
        if not signals:
            logger.warning("No signals to analyze")
            return {}

        # Filter to only signals with outcomes
        signals_with_outcomes = [s for s in signals if s.get("outcome_30min") in ["TP_HIT", "SL_HIT"]]

        logger.info(f"📊 Analyzing {len(signals_with_outcomes)} signals with outcomes")

        # Run all analyses
        analysis = {
            "patterns": self.analyze_pattern_performance(signals_with_outcomes),
            "sessions": self.analyze_session_performance(signals_with_outcomes),
            "pairs": self.analyze_pair_performance(signals_with_outcomes),
            "confidence_ranges": self.analyze_confidence_performance(signals_with_outcomes),
            "total_signals": len(signals),
            "signals_with_outcomes": len(signals_with_outcomes),
            "analysis_timestamp": datetime.now().isoformat(),
        }

        # Identify what to eliminate
        kill_list = self.identify_elimination_candidates(analysis)

        # Save kill list
        self.save_kill_list(kill_list)

        # Log key findings
        self.log_analysis_results(analysis, kill_list)

        return {"analysis": analysis, "kill_list": kill_list}

    def log_analysis_results(self, analysis: Dict, kill_list: Dict):
        """Log key analysis results"""
        logger.info("\n" + "=" * 60)
        logger.info("🔥 RAPID ELIMINATION ANALYSIS RESULTS")
        logger.info("=" * 60)

        # Pattern performance summary
        logger.info("\n📊 PATTERN PERFORMANCE:")
        for pattern, stats in analysis["patterns"].items():
            if stats["total"] >= 5:
                logger.info(f"  {pattern}: {stats['win_rate_30min']}% win rate ({stats['total']} signals)")

        # Elimination recommendations
        if kill_list["reasons"]:
            logger.info("\n💀 ELIMINATION RECOMMENDATIONS:")
            for reason in kill_list["reasons"]:
                logger.info(f"  ⚠️  {reason}")
        else:
            logger.info("\n✅ No patterns below elimination threshold found")

        # Top performing patterns
        pattern_stats = analysis["patterns"]
        if pattern_stats:
            top_patterns = sorted(
                [(p, s) for p, s in pattern_stats.items() if s["total"] >= 5],
                key=lambda x: x[1]["win_rate_30min"],
                reverse=True,
            )[:3]

            if top_patterns:
                logger.info("\n🏆 TOP PERFORMING PATTERNS:")
                for pattern, stats in top_patterns:
                    logger.info(f"  ✅ {pattern}: {stats['win_rate_30min']}% win rate ({stats['total']} signals)")

        logger.info("=" * 60 + "\n")


def main():
    """Main function for standalone operation"""
    analyzer = RapidEliminationAnalyzer(elimination_threshold=40.0)

    try:
        results = analyzer.run_analysis()

        if results:
            kill_list = results.get("kill_list", {})
            total_eliminations = (
                len(kill_list.get("patterns_to_kill", []))
                + len(kill_list.get("sessions_to_avoid", []))
                + len(kill_list.get("pairs_to_avoid", []))
                + len(kill_list.get("confidence_ranges_to_avoid", []))
            )

            logger.info(f"🎯 Analysis complete: {total_eliminations} elimination recommendations")
        else:
            logger.warning("No analysis results generated")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
