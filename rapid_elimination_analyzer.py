#!/usr/bin/env python3
"""
Rapid Elimination Analyzer - Identifies patterns to kill (<40% win rate)
Analyzes comprehensive_tracking.jsonl to find poor performing patterns and conditions
"""

import json
import logging
import sys
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/rapid_elimination.log'),
        logging.StreamHandler(sys.stdout)
    ]
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
            with open(self.tracking_file, 'r') as f:
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
        pattern_stats = defaultdict(lambda: {
            'total': 0, 'tp_30min': 0, 'sl_30min': 0, 'tp_60min': 0, 'sl_60min': 0,
            'win_rate_30min': 0.0, 'win_rate_60min': 0.0, 'avg_confidence': 0.0
        })
        
        for signal in signals:
            pattern = signal.get('pattern_type', 'UNKNOWN')
            confidence = signal.get('confidence_score', 0)
            outcome_30 = signal.get('outcome_30min')
            outcome_60 = signal.get('outcome_60min')
            
            pattern_stats[pattern]['total'] += 1
            pattern_stats[pattern]['avg_confidence'] += confidence
            
            if outcome_30 == 'TP_HIT':
                pattern_stats[pattern]['tp_30min'] += 1
            elif outcome_30 == 'SL_HIT':
                pattern_stats[pattern]['sl_30min'] += 1
                
            if outcome_60 == 'TP_HIT':
                pattern_stats[pattern]['tp_60min'] += 1
            elif outcome_60 == 'SL_HIT':
                pattern_stats[pattern]['sl_60min'] += 1
                
        # Calculate win rates and averages
        for pattern, stats in pattern_stats.items():
            if stats['total'] > 0:
                stats['avg_confidence'] = round(stats['avg_confidence'] / stats['total'], 1)
                
            total_closed_30 = stats['tp_30min'] + stats['sl_30min']
            if total_closed_30 > 0:
                stats['win_rate_30min'] = round(stats['tp_30min'] / total_closed_30 * 100, 1)
                
            total_closed_60 = stats['tp_60min'] + stats['sl_60min']
            if total_closed_60 > 0:
                stats['win_rate_60min'] = round(stats['tp_60min'] / total_closed_60 * 100, 1)
                
        return dict(pattern_stats)
        
    def analyze_session_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by trading session"""
        session_stats = defaultdict(lambda: {
            'total': 0, 'tp_30min': 0, 'sl_30min': 0, 'tp_60min': 0, 'sl_60min': 0,
            'win_rate_30min': 0.0, 'win_rate_60min': 0.0
        })
        
        for signal in signals:
            session = signal.get('session', 'UNKNOWN')
            outcome_30 = signal.get('outcome_30min')
            outcome_60 = signal.get('outcome_60min')
            
            session_stats[session]['total'] += 1
            
            if outcome_30 == 'TP_HIT':
                session_stats[session]['tp_30min'] += 1
            elif outcome_30 == 'SL_HIT':
                session_stats[session]['sl_30min'] += 1
                
            if outcome_60 == 'TP_HIT':
                session_stats[session]['tp_60min'] += 1
            elif outcome_60 == 'SL_HIT':
                session_stats[session]['sl_60min'] += 1
                
        # Calculate win rates
        for session, stats in session_stats.items():
            total_closed_30 = stats['tp_30min'] + stats['sl_30min']
            if total_closed_30 > 0:
                stats['win_rate_30min'] = round(stats['tp_30min'] / total_closed_30 * 100, 1)
                
            total_closed_60 = stats['tp_60min'] + stats['sl_60min']
            if total_closed_60 > 0:
                stats['win_rate_60min'] = round(stats['tp_60min'] / total_closed_60 * 100, 1)
                
        return dict(session_stats)
        
    def analyze_pair_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by currency pair"""
        pair_stats = defaultdict(lambda: {
            'total': 0, 'tp_30min': 0, 'sl_30min': 0, 'tp_60min': 0, 'sl_60min': 0,
            'win_rate_30min': 0.0, 'win_rate_60min': 0.0
        })
        
        for signal in signals:
            pair = signal.get('pair', 'UNKNOWN')
            outcome_30 = signal.get('outcome_30min')
            outcome_60 = signal.get('outcome_60min')
            
            pair_stats[pair]['total'] += 1
            
            if outcome_30 == 'TP_HIT':
                pair_stats[pair]['tp_30min'] += 1
            elif outcome_30 == 'SL_HIT':
                pair_stats[pair]['sl_30min'] += 1
                
            if outcome_60 == 'TP_HIT':
                pair_stats[pair]['tp_60min'] += 1
            elif outcome_60 == 'SL_HIT':
                pair_stats[pair]['sl_60min'] += 1
                
        # Calculate win rates
        for pair, stats in pair_stats.items():
            total_closed_30 = stats['tp_30min'] + stats['sl_30min']
            if total_closed_30 > 0:
                stats['win_rate_30min'] = round(stats['tp_30min'] / total_closed_30 * 100, 1)
                
            total_closed_60 = stats['tp_60min'] + stats['sl_60min']
            if total_closed_60 > 0:
                stats['win_rate_60min'] = round(stats['tp_60min'] / total_closed_60 * 100, 1)
                
        return dict(pair_stats)
        
    def analyze_confidence_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by confidence ranges"""
        confidence_ranges = {
            '50-60%': [50, 60], '60-70%': [60, 70], '70-80%': [70, 80], 
            '80-90%': [80, 90], '90-100%': [90, 100]
        }
        
        range_stats = defaultdict(lambda: {
            'total': 0, 'tp_30min': 0, 'sl_30min': 0, 'tp_60min': 0, 'sl_60min': 0,
            'win_rate_30min': 0.0, 'win_rate_60min': 0.0
        })
        
        for signal in signals:
            confidence = signal.get('confidence_score', 0)
            outcome_30 = signal.get('outcome_30min')
            outcome_60 = signal.get('outcome_60min')
            
            # Find which range this confidence falls into
            for range_name, (min_conf, max_conf) in confidence_ranges.items():
                if min_conf <= confidence < max_conf:
                    range_stats[range_name]['total'] += 1
                    
                    if outcome_30 == 'TP_HIT':
                        range_stats[range_name]['tp_30min'] += 1
                    elif outcome_30 == 'SL_HIT':
                        range_stats[range_name]['sl_30min'] += 1
                        
                    if outcome_60 == 'TP_HIT':
                        range_stats[range_name]['tp_60min'] += 1
                    elif outcome_60 == 'SL_HIT':
                        range_stats[range_name]['sl_60min'] += 1
                    break
                    
        # Calculate win rates
        for range_name, stats in range_stats.items():
            total_closed_30 = stats['tp_30min'] + stats['sl_30min']
            if total_closed_30 > 0:
                stats['win_rate_30min'] = round(stats['tp_30min'] / total_closed_30 * 100, 1)
                
            total_closed_60 = stats['tp_60min'] + stats['sl_60min']
            if total_closed_60 > 0:
                stats['win_rate_60min'] = round(stats['tp_60min'] / total_closed_60 * 100, 1)
                
        return dict(range_stats)
        
    def identify_elimination_candidates(self, analysis: Dict) -> Dict:
        """Identify patterns/conditions that should be eliminated"""
        kill_list = {
            'patterns_to_kill': [],
            'sessions_to_avoid': [],
            'pairs_to_avoid': [],
            'confidence_ranges_to_avoid': [],
            'reasons': []
        }
        
        # Check patterns for elimination
        pattern_stats = analysis.get('patterns', {})
        for pattern, stats in pattern_stats.items():
            win_rate_30 = stats.get('win_rate_30min', 0)
            win_rate_60 = stats.get('win_rate_60min', 0)
            total = stats.get('total', 0)
            
            # Eliminate if win rate is below threshold and we have enough data
            if total >= 10:  # Require at least 10 signals
                if win_rate_30 < self.elimination_threshold:
                    kill_list['patterns_to_kill'].append({
                        'pattern': pattern,
                        'win_rate_30min': win_rate_30,
                        'win_rate_60min': win_rate_60,
                        'total_signals': total,
                        'reason': f'Win rate {win_rate_30}% below {self.elimination_threshold}% threshold'
                    })
                    kill_list['reasons'].append(f"KILL PATTERN: {pattern} ({win_rate_30}% win rate)")
                    
        # Check sessions for elimination
        session_stats = analysis.get('sessions', {})
        for session, stats in session_stats.items():
            win_rate_30 = stats.get('win_rate_30min', 0)
            total = stats.get('total', 0)
            
            if total >= 20 and win_rate_30 < self.elimination_threshold:
                kill_list['sessions_to_avoid'].append({
                    'session': session,
                    'win_rate_30min': win_rate_30,
                    'total_signals': total,
                    'reason': f'Session performs below {self.elimination_threshold}% threshold'
                })
                kill_list['reasons'].append(f"AVOID SESSION: {session} ({win_rate_30}% win rate)")
                
        # Check pairs for elimination
        pair_stats = analysis.get('pairs', {})
        for pair, stats in pair_stats.items():
            win_rate_30 = stats.get('win_rate_30min', 0)
            total = stats.get('total', 0)
            
            if total >= 15 and win_rate_30 < self.elimination_threshold:
                kill_list['pairs_to_avoid'].append({
                    'pair': pair,
                    'win_rate_30min': win_rate_30,
                    'total_signals': total,
                    'reason': f'Pair performs below {self.elimination_threshold}% threshold'
                })
                kill_list['reasons'].append(f"AVOID PAIR: {pair} ({win_rate_30}% win rate)")
                
        # Check confidence ranges
        confidence_stats = analysis.get('confidence_ranges', {})
        for range_name, stats in confidence_stats.items():
            win_rate_30 = stats.get('win_rate_30min', 0)
            total = stats.get('total', 0)
            
            if total >= 10 and win_rate_30 < self.elimination_threshold:
                kill_list['confidence_ranges_to_avoid'].append({
                    'range': range_name,
                    'win_rate_30min': win_rate_30,
                    'total_signals': total,
                    'reason': f'Confidence range performs below {self.elimination_threshold}% threshold'
                })
                kill_list['reasons'].append(f"AVOID CONFIDENCE: {range_name} ({win_rate_30}% win rate)")
                
        return kill_list
        
    def save_kill_list(self, kill_list: Dict):\n        \"\"\"Save elimination candidates to file\"\"\"\n        try:\n            with open(self.kill_list_file, 'w') as f:\n                json.dump(kill_list, f, indent=2)\n            logger.info(f\"💾 Kill list saved to {self.kill_list_file}\")\n        except Exception as e:\n            logger.error(f\"❌ Error saving kill list: {e}\")\n            \n    def run_analysis(self) -> Dict:\n        \"\"\"Run complete rapid elimination analysis\"\"\"\n        logger.info(f\"🎯 Starting rapid elimination analysis (threshold: {self.elimination_threshold}%)...\")\n        \n        # Load all signals\n        signals = self.load_all_signals()\n        if not signals:\n            logger.warning(\"No signals to analyze\")\n            return {}\n            \n        # Filter to only signals with outcomes\n        signals_with_outcomes = [\n            s for s in signals \n            if s.get('outcome_30min') in ['TP_HIT', 'SL_HIT']\n        ]\n        \n        logger.info(f\"📊 Analyzing {len(signals_with_outcomes)} signals with outcomes\")\n        \n        # Run all analyses\n        analysis = {\n            'patterns': self.analyze_pattern_performance(signals_with_outcomes),\n            'sessions': self.analyze_session_performance(signals_with_outcomes),\n            'pairs': self.analyze_pair_performance(signals_with_outcomes),\n            'confidence_ranges': self.analyze_confidence_performance(signals_with_outcomes),\n            'total_signals': len(signals),\n            'signals_with_outcomes': len(signals_with_outcomes),\n            'analysis_timestamp': datetime.now().isoformat()\n        }\n        \n        # Identify what to eliminate\n        kill_list = self.identify_elimination_candidates(analysis)\n        \n        # Save kill list\n        self.save_kill_list(kill_list)\n        \n        # Log key findings\n        self.log_analysis_results(analysis, kill_list)\n        \n        return {\n            'analysis': analysis,\n            'kill_list': kill_list\n        }\n        \n    def log_analysis_results(self, analysis: Dict, kill_list: Dict):\n        \"\"\"Log key analysis results\"\"\"\n        logger.info(\"\\n\" + \"=\"*60)\n        logger.info(\"🔥 RAPID ELIMINATION ANALYSIS RESULTS\")\n        logger.info(\"=\"*60)\n        \n        # Pattern performance summary\n        logger.info(\"\\n📊 PATTERN PERFORMANCE:\")\n        for pattern, stats in analysis['patterns'].items():\n            if stats['total'] >= 5:\n                logger.info(f\"  {pattern}: {stats['win_rate_30min']}% win rate ({stats['total']} signals)\")\n                \n        # Elimination recommendations\n        if kill_list['reasons']:\n            logger.info(\"\\n💀 ELIMINATION RECOMMENDATIONS:\")\n            for reason in kill_list['reasons']:\n                logger.info(f\"  ⚠️  {reason}\")\n        else:\n            logger.info(\"\\n✅ No patterns below elimination threshold found\")\n            \n        # Top performing patterns\n        pattern_stats = analysis['patterns']\n        if pattern_stats:\n            top_patterns = sorted(\n                [(p, s) for p, s in pattern_stats.items() if s['total'] >= 5],\n                key=lambda x: x[1]['win_rate_30min'],\n                reverse=True\n            )[:3]\n            \n            if top_patterns:\n                logger.info(\"\\n🏆 TOP PERFORMING PATTERNS:\")\n                for pattern, stats in top_patterns:\n                    logger.info(f\"  ✅ {pattern}: {stats['win_rate_30min']}% win rate ({stats['total']} signals)\")\n                    \n        logger.info(\"=\"*60 + \"\\n\")\n\ndef main():\n    \"\"\"Main function for standalone operation\"\"\"\n    analyzer = RapidEliminationAnalyzer(elimination_threshold=40.0)\n    \n    try:\n        results = analyzer.run_analysis()\n        \n        if results:\n            kill_list = results.get('kill_list', {})\n            total_eliminations = (\n                len(kill_list.get('patterns_to_kill', [])) +\n                len(kill_list.get('sessions_to_avoid', [])) +\n                len(kill_list.get('pairs_to_avoid', [])) +\n                len(kill_list.get('confidence_ranges_to_avoid', []))\n            )\n            \n            logger.info(f\"🎯 Analysis complete: {total_eliminations} elimination recommendations\")\n        else:\n            logger.warning(\"No analysis results generated\")\n            \n    except Exception as e:\n        logger.error(f\"❌ Analysis failed: {e}\")\n        raise\n\nif __name__ == \"__main__\":\n    main()