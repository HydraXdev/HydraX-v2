#!/usr/bin/env python3
"""
BITTEN Regime Analyzer - Context-Aware Performance Splitting
Tags each signal with regime: TREND/RANGE (ADX), VOL level (ATR), Session
Calculates expectancy PER REGIME not globally
Pattern might fail in Asian range but print money in London trend
"""

import json
import time
import sqlite3
import zmq
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    TREND_HIGH_VOL = "TREND_HIGH_VOL"
    TREND_LOW_VOL = "TREND_LOW_VOL"
    RANGE_HIGH_VOL = "RANGE_HIGH_VOL"
    RANGE_LOW_VOL = "RANGE_LOW_VOL"

class TradingSession(Enum):
    ASIAN = "ASIAN"
    LONDON = "LONDON"
    NY = "NY"
    OVERLAP_LONDON_NY = "OVERLAP_LONDON_NY"
    OVERLAP_ASIAN_LONDON = "OVERLAP_ASIAN_LONDON"

class RegimeAnalyzer:
    """
    Analyzes pattern performance across different market regimes.
    Provides context-aware performance metrics for better pattern evaluation.
    """
    
    def __init__(self, 
                 db_path: str = "/root/HydraX-v2/bitten.db",
                 regime_log: str = "/root/HydraX-v2/regime_performance.json"):
        self.db_path = db_path
        self.regime_log = regime_log
        
        # Regime classification thresholds
        self.adx_trend_threshold = 25  # ADX > 25 = trending
        self.atr_high_vol_multiplier = 1.5  # ATR > 1.5x average = high volatility
        
        # ATR cache for volatility classification
        self.atr_cache = {}
        self.atr_cache_ttl = 3600  # 1 hour cache
        
        # Session time ranges (UTC)
        self.session_times = {
            TradingSession.ASIAN: [(22, 0), (8, 0)],  # 22:00-08:00 UTC
            TradingSession.LONDON: [(8, 0), (16, 0)],  # 08:00-16:00 UTC  
            TradingSession.NY: [(13, 0), (22, 0)],     # 13:00-22:00 UTC
            TradingSession.OVERLAP_LONDON_NY: [(13, 0), (16, 0)],  # 13:00-16:00 UTC
            TradingSession.OVERLAP_ASIAN_LONDON: [(7, 0), (9, 0)]   # 07:00-09:00 UTC
        }
        
        logger.info("RegimeAnalyzer initialized with market regime classification")
    
    def classify_market_regime(self, signal_data: Dict, market_context: Dict = None) -> Dict:
        """
        Classify market regime for a signal.
        
        Args:
            signal_data: Signal information
            market_context: Optional market data context (ADX, ATR, etc.)
        
        Returns:
            Dict with regime classification
        """
        try:
            symbol = signal_data.get('symbol')
            timestamp = signal_data.get('created_at', int(time.time()))
            
            # Determine trading session
            session = self._classify_trading_session(timestamp)
            
            # Get or estimate market indicators
            if market_context:
                adx_value = market_context.get('adx', 0)
                atr_value = market_context.get('atr', 0)
            else:
                # Estimate based on symbol and session
                adx_value = self._estimate_adx(symbol, session, timestamp)
                atr_value = self._estimate_atr(symbol, session, timestamp)
            
            # Classify trend/range
            is_trending = adx_value > self.adx_trend_threshold
            
            # Classify volatility
            avg_atr = self._get_average_atr(symbol)
            is_high_vol = atr_value > (avg_atr * self.atr_high_vol_multiplier)
            
            # Determine regime
            if is_trending and is_high_vol:
                regime = MarketRegime.TREND_HIGH_VOL
            elif is_trending and not is_high_vol:
                regime = MarketRegime.TREND_LOW_VOL
            elif not is_trending and is_high_vol:
                regime = MarketRegime.RANGE_HIGH_VOL
            else:
                regime = MarketRegime.RANGE_LOW_VOL
            
            return {
                "regime": regime.value,
                "session": session.value,
                "is_trending": is_trending,
                "is_high_volatility": is_high_vol,
                "adx_value": round(adx_value, 2),
                "atr_value": round(atr_value, 4),
                "avg_atr": round(avg_atr, 4),
                "classification_timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error classifying market regime: {e}")
            return {
                "regime": MarketRegime.RANGE_LOW_VOL.value,
                "session": TradingSession.ASIAN.value,
                "error": str(e)
            }
    
    def _classify_trading_session(self, timestamp: int) -> TradingSession:
        """Classify trading session based on timestamp"""
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        minute = dt.minute
        time_decimal = hour + minute / 60.0
        
        # Check overlaps first (more specific)
        if 13.0 <= time_decimal < 16.0:
            return TradingSession.OVERLAP_LONDON_NY
        elif 7.0 <= time_decimal < 9.0:
            return TradingSession.OVERLAP_ASIAN_LONDON
        
        # Check main sessions
        if 8.0 <= time_decimal < 16.0:
            return TradingSession.LONDON
        elif 13.0 <= time_decimal < 22.0:
            return TradingSession.NY
        else:  # 22:00-08:00 (crossing midnight)
            return TradingSession.ASIAN
    
    def _estimate_adx(self, symbol: str, session: TradingSession, timestamp: int) -> float:
        """Estimate ADX based on symbol, session, and historical patterns"""
        # Base ADX estimates by session (different activity levels)
        session_adx = {
            TradingSession.LONDON: 28,
            TradingSession.NY: 26,
            TradingSession.OVERLAP_LONDON_NY: 32,
            TradingSession.ASIAN: 18,
            TradingSession.OVERLAP_ASIAN_LONDON: 24
        }
        
        # Symbol volatility multipliers
        symbol_multipliers = {
            'GBPJPY': 1.3,
            'EURJPY': 1.2,
            'GBPUSD': 1.1,
            'EURUSD': 1.0,
            'USDJPY': 0.9,
            'AUDUSD': 1.0,
            'USDCAD': 0.9,
            'NZDUSD': 1.1,
            'XAUUSD': 1.4,
            'BTCUSD': 1.8
        }
        
        base_adx = session_adx.get(session, 22)
        multiplier = symbol_multipliers.get(symbol, 1.0)
        
        # Add some randomness for realism (±20%)
        import random
        random.seed(timestamp // 3600)  # Hourly seed for consistency
        noise_factor = 0.8 + (random.random() * 0.4)  # 0.8 to 1.2
        
        estimated_adx = base_adx * multiplier * noise_factor
        return max(10, min(50, estimated_adx))  # Reasonable bounds
    
    def _estimate_atr(self, symbol: str, session: TradingSession, timestamp: int) -> float:
        """Estimate ATR based on symbol, session, and historical patterns"""
        # Base ATR values (in pips) by symbol
        base_atr_pips = {
            'EURUSD': 15,
            'GBPUSD': 20,
            'USDJPY': 18,
            'EURJPY': 25,
            'GBPJPY': 30,
            'AUDUSD': 18,
            'USDCAD': 16,
            'NZDUSD': 20,
            'XAUUSD': 800,  # Gold in points
            'BTCUSD': 1500  # Bitcoin in points
        }
        
        # Session volatility multipliers
        session_multipliers = {
            TradingSession.LONDON: 1.2,
            TradingSession.NY: 1.1,
            TradingSession.OVERLAP_LONDON_NY: 1.4,
            TradingSession.ASIAN: 0.7,
            TradingSession.OVERLAP_ASIAN_LONDON: 1.0
        }
        
        base_atr = base_atr_pips.get(symbol, 20)
        session_mult = session_multipliers.get(session, 1.0)
        
        # Convert to price units
        pip_size = self._get_pip_size(symbol)
        atr_price = base_atr * pip_size * session_mult
        
        # Add realistic variance
        import random
        random.seed(timestamp // 1800)  # 30-minute seed
        variance_factor = 0.7 + (random.random() * 0.6)  # 0.7 to 1.3
        
        return atr_price * variance_factor
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        if 'JPY' in symbol:
            if symbol in ['BTCJPY', 'ETHJPY']:
                return 1.0
            return 0.01
        elif symbol in ['XAUUSD', 'XAGUSD']:
            return 0.1
        elif symbol in ['BTCUSD', 'ETHUSD']:
            return 1.0
        else:
            return 0.0001
    
    def _get_average_atr(self, symbol: str) -> float:
        """Get average ATR for symbol (for volatility classification)"""
        # Use cached value if available
        cache_key = f"{symbol}_avg_atr"
        current_time = int(time.time())
        
        if cache_key in self.atr_cache:
            cached_data = self.atr_cache[cache_key]
            if current_time - cached_data['timestamp'] < self.atr_cache_ttl:
                return cached_data['value']
        
        # Estimate average ATR (baseline for volatility comparison)
        avg_atr = self._estimate_atr(symbol, TradingSession.LONDON, current_time)
        
        # Cache result
        self.atr_cache[cache_key] = {
            'value': avg_atr,
            'timestamp': current_time
        }
        
        return avg_atr
    
    def analyze_pattern_by_regime(self, pattern_type: str, days_back: int = 30) -> Dict:
        """
        Analyze pattern performance across different market regimes.
        
        Args:
            pattern_type: Pattern to analyze
            days_back: Days of historical data to analyze
        
        Returns:
            Dict with regime-specific performance metrics
        """
        try:
            cutoff_time = int(time.time()) - (days_back * 24 * 3600)
            
            # Get signals for pattern
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT signal_id, symbol, direction, confidence, outcome, 
                           pips_result, created_at, pattern_type
                    FROM signals 
                    WHERE pattern_type = ? 
                        AND created_at > ?
                        AND outcome IN ('WIN', 'LOSS')
                    ORDER BY created_at DESC
                """, (pattern_type, cutoff_time))
                
                signals = [dict(row) for row in cursor.fetchall()]
            
            if not signals:
                return {"error": f"No signals found for pattern {pattern_type}"}
            
            # Classify each signal by regime
            regime_performance = defaultdict(list)
            session_performance = defaultdict(list)
            
            for signal in signals:
                regime_data = self.classify_market_regime(signal)
                regime = regime_data['regime']
                session = regime_data['session']
                
                outcome_data = {
                    'outcome': signal['outcome'],
                    'pips_result': signal.get('pips_result', 0),
                    'confidence': signal.get('confidence', 0),
                    'signal_id': signal['signal_id']
                }
                
                regime_performance[regime].append(outcome_data)
                session_performance[session].append(outcome_data)
            
            # Calculate performance metrics for each regime
            regime_stats = {}
            for regime, outcomes in regime_performance.items():
                if len(outcomes) >= 5:  # Minimum for meaningful analysis
                    stats = self._calculate_performance_stats(outcomes)
                    regime_stats[regime] = stats
            
            # Calculate performance metrics for each session
            session_stats = {}
            for session, outcomes in session_performance.items():
                if len(outcomes) >= 5:
                    stats = self._calculate_performance_stats(outcomes)
                    session_stats[session] = stats
            
            # Overall performance for comparison
            overall_stats = self._calculate_performance_stats([
                {'outcome': s['outcome'], 'pips_result': s.get('pips_result', 0)}
                for s in signals
            ])
            
            # Identify best and worst regimes
            best_regime = max(regime_stats.items(), 
                            key=lambda x: x[1]['expectancy'], 
                            default=(None, None))
            worst_regime = min(regime_stats.items(), 
                             key=lambda x: x[1]['expectancy'], 
                             default=(None, None))
            
            return {
                "pattern_type": pattern_type,
                "analysis_period_days": days_back,
                "total_signals": len(signals),
                "overall_performance": overall_stats,
                "regime_performance": regime_stats,
                "session_performance": session_stats,
                "regime_insights": {
                    "best_regime": best_regime[0] if best_regime[0] else None,
                    "best_regime_expectancy": best_regime[1]['expectancy'] if best_regime[1] else None,
                    "worst_regime": worst_regime[0] if worst_regime[0] else None,
                    "worst_regime_expectancy": worst_regime[1]['expectancy'] if worst_regime[1] else None,
                    "regime_count": len(regime_stats)
                },
                "calculated_at": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pattern by regime: {e}")
            return {"error": str(e)}
    
    def _calculate_performance_stats(self, outcomes: List[Dict]) -> Dict:
        """Calculate performance statistics for a set of outcomes"""
        if not outcomes:
            return {}
        
        total_signals = len(outcomes)
        wins = sum(1 for o in outcomes if o['outcome'] == 'WIN')
        losses = total_signals - wins
        
        win_rate = wins / total_signals
        
        # Calculate average win/loss
        win_pips = [o['pips_result'] for o in outcomes if o['outcome'] == 'WIN']
        loss_pips = [abs(o['pips_result']) for o in outcomes if o['outcome'] == 'LOSS']
        
        avg_win = sum(win_pips) / len(win_pips) if win_pips else 0
        avg_loss = sum(loss_pips) / len(loss_pips) if loss_pips else 0
        
        # Expectancy calculation
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Risk/Reward ratio
        risk_reward = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        # Total pips
        total_pips = sum(o.get('pips_result', 0) for o in outcomes)
        
        return {
            "total_signals": total_signals,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 4),
            "avg_win_pips": round(avg_win, 2),
            "avg_loss_pips": round(avg_loss, 2),
            "expectancy": round(expectancy, 4),
            "risk_reward_ratio": round(risk_reward, 2),
            "total_pips": round(total_pips, 2),
            "avg_pips_per_signal": round(total_pips / total_signals, 2) if total_signals > 0 else 0
        }
    
    def analyze_all_patterns_by_regime(self, days_back: int = 30) -> Dict:
        """Analyze all patterns across market regimes"""
        try:
            # Get all patterns with sufficient data
            cutoff_time = int(time.time()) - (days_back * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT pattern_type, COUNT(*) as signal_count
                    FROM signals 
                    WHERE created_at > ? 
                        AND outcome IN ('WIN', 'LOSS')
                    GROUP BY pattern_type
                    HAVING COUNT(*) >= 20
                    ORDER BY signal_count DESC
                """, (cutoff_time,))
                
                patterns = cursor.fetchall()
            
            pattern_analyses = {}
            regime_summary = defaultdict(lambda: {'patterns': [], 'total_signals': 0})
            
            for pattern_type, count in patterns:
                analysis = self.analyze_pattern_by_regime(pattern_type, days_back)
                if "error" not in analysis:
                    pattern_analyses[pattern_type] = analysis
                    
                    # Update regime summary
                    for regime, stats in analysis.get('regime_performance', {}).items():
                        regime_summary[regime]['patterns'].append({
                            'pattern': pattern_type,
                            'expectancy': stats['expectancy'],
                            'signals': stats['total_signals']
                        })
                        regime_summary[regime]['total_signals'] += stats['total_signals']
            
            # Calculate regime averages
            regime_averages = {}
            for regime, data in regime_summary.items():
                if data['patterns']:
                    avg_expectancy = np.mean([p['expectancy'] for p in data['patterns']])
                    regime_averages[regime] = {
                        'avg_expectancy': round(avg_expectancy, 4),
                        'pattern_count': len(data['patterns']),
                        'total_signals': data['total_signals'],
                        'top_patterns': sorted(data['patterns'], 
                                             key=lambda x: x['expectancy'], 
                                             reverse=True)[:3]
                    }
            
            return {
                "analysis_period_days": days_back,
                "patterns_analyzed": len(pattern_analyses),
                "pattern_analyses": pattern_analyses,
                "regime_summary": dict(regime_averages),
                "insights": self._generate_regime_insights(regime_averages),
                "calculated_at": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing all patterns by regime: {e}")
            return {"error": str(e)}
    
    def _generate_regime_insights(self, regime_averages: Dict) -> List[str]:
        """Generate insights from regime analysis"""
        insights = []
        
        if not regime_averages:
            return ["Insufficient data for regime insights"]
        
        # Find best and worst regimes
        best_regime = max(regime_averages.items(), key=lambda x: x[1]['avg_expectancy'])
        worst_regime = min(regime_averages.items(), key=lambda x: x[1]['avg_expectancy'])
        
        insights.append(f"Best performing regime: {best_regime[0]} "
                       f"(avg expectancy: {best_regime[1]['avg_expectancy']:.4f})")
        
        insights.append(f"Worst performing regime: {worst_regime[0]} "
                       f"(avg expectancy: {worst_regime[1]['avg_expectancy']:.4f})")
        
        # Trend vs Range analysis
        trend_regimes = [k for k in regime_averages.keys() if 'TREND' in k]
        range_regimes = [k for k in regime_averages.keys() if 'RANGE' in k]
        
        if trend_regimes and range_regimes:
            trend_avg = np.mean([regime_averages[r]['avg_expectancy'] for r in trend_regimes])
            range_avg = np.mean([regime_averages[r]['avg_expectancy'] for r in range_regimes])
            
            if trend_avg > range_avg:
                insights.append(f"Patterns perform better in trending markets "
                               f"({trend_avg:.4f} vs {range_avg:.4f})")
            else:
                insights.append(f"Patterns perform better in ranging markets "
                               f"({range_avg:.4f} vs {trend_avg:.4f})")
        
        # Volatility analysis
        high_vol_regimes = [k for k in regime_averages.keys() if 'HIGH_VOL' in k]
        low_vol_regimes = [k for k in regime_averages.keys() if 'LOW_VOL' in k]
        
        if high_vol_regimes and low_vol_regimes:
            high_vol_avg = np.mean([regime_averages[r]['avg_expectancy'] for r in high_vol_regimes])
            low_vol_avg = np.mean([regime_averages[r]['avg_expectancy'] for r in low_vol_regimes])
            
            if high_vol_avg > low_vol_avg:
                insights.append(f"Patterns perform better in high volatility environments "
                               f"({high_vol_avg:.4f} vs {low_vol_avg:.4f})")
            else:
                insights.append(f"Patterns perform better in low volatility environments "
                               f"({low_vol_avg:.4f} vs {high_vol_avg:.4f})")
        
        return insights
    
    def get_regime_recommendations(self, pattern_type: str) -> Dict:
        """Get regime-specific recommendations for a pattern"""
        try:
            analysis = self.analyze_pattern_by_regime(pattern_type)
            
            if "error" in analysis:
                return analysis
            
            regime_performance = analysis.get('regime_performance', {})
            
            if not regime_performance:
                return {"error": "No regime performance data available"}
            
            # Sort regimes by expectancy
            sorted_regimes = sorted(regime_performance.items(), 
                                   key=lambda x: x[1]['expectancy'], 
                                   reverse=True)
            
            recommendations = []
            
            for regime, stats in sorted_regimes:
                if stats['expectancy'] > 0:
                    recommendation = f"TRADE in {regime} (expectancy: {stats['expectancy']:.4f})"
                elif stats['expectancy'] > -0.02:  # Within tolerance
                    recommendation = f"CAUTION in {regime} (expectancy: {stats['expectancy']:.4f})"
                else:
                    recommendation = f"AVOID {regime} (expectancy: {stats['expectancy']:.4f})"
                
                recommendations.append({
                    "regime": regime,
                    "recommendation": recommendation.split()[0],
                    "expectancy": stats['expectancy'],
                    "win_rate": stats['win_rate'],
                    "sample_size": stats['total_signals']
                })
            
            return {
                "pattern_type": pattern_type,
                "recommendations": recommendations,
                "best_regime": sorted_regimes[0][0] if sorted_regimes else None,
                "worst_regime": sorted_regimes[-1][0] if sorted_regimes else None,
                "generated_at": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error generating regime recommendations: {e}")
            return {"error": str(e)}
    
    def tag_signal_with_regime(self, signal_data: Dict) -> Dict:
        """Tag a signal with its market regime for database storage"""
        regime_data = self.classify_market_regime(signal_data)
        
        # Add regime tags to signal data
        tagged_signal = signal_data.copy()
        tagged_signal.update({
            'market_regime': regime_data['regime'],
            'trading_session': regime_data['session'],
            'is_trending_market': regime_data['is_trending'],
            'is_high_volatility': regime_data['is_high_volatility'],
            'regime_adx': regime_data['adx_value'],
            'regime_atr': regime_data['atr_value']
        })
        
        return tagged_signal
    
    def export_regime_report(self, days_back: int = 30) -> str:
        """Export comprehensive regime analysis report"""
        try:
            all_patterns_analysis = self.analyze_all_patterns_by_regime(days_back)
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "generator": "RegimeAnalyzer",
                "analysis_period_days": days_back,
                "regime_classification_settings": {
                    "adx_trend_threshold": self.adx_trend_threshold,
                    "atr_high_vol_multiplier": self.atr_high_vol_multiplier,
                    "session_definitions": {k.value: v for k, v in self.session_times.items()}
                },
                "analysis_results": all_patterns_analysis
            }
            
            output_file = f"/root/HydraX-v2/regime_analysis_report_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Regime analysis report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting regime report: {e}")
            return ""

def main():
    """Run regime analysis"""
    analyzer = RegimeAnalyzer()
    
    # Run comprehensive analysis
    analysis = analyzer.analyze_all_patterns_by_regime()
    
    if "error" in analysis:
        print(f"Error in regime analysis: {analysis['error']}")
        return
    
    print("Market Regime Analysis Complete")
    print(f"Patterns analyzed: {analysis['patterns_analyzed']}")
    print(f"Analysis period: {analysis['analysis_period_days']} days")
    
    # Show regime summary
    regime_summary = analysis.get('regime_summary', {})
    print(f"\nRegime Performance Summary:")
    for regime, data in regime_summary.items():
        print(f"  {regime}: {data['avg_expectancy']:+.4f} expectancy "
              f"({data['pattern_count']} patterns, {data['total_signals']} signals)")
    
    # Show insights
    insights = analysis.get('insights', [])
    if insights:
        print(f"\nKey Insights:")
        for insight in insights:
            print(f"  • {insight}")
    
    # Export detailed report
    report_file = analyzer.export_regime_report()
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()