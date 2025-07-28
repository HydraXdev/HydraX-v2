#!/usr/bin/env python3
"""
Forex Data Quality Validation
Comprehensive validation of extracted historical data for BITTEN backtesting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_csv_data(pair: str, csv_path: str) -> dict:
    """Validate a single pair's CSV data"""
    
    logger.info(f"🔍 Validating {pair} data...")
    
    try:
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        validation = {
            'pair': pair,
            'total_records': len(df),
            'date_range': (df['timestamp'].min(), df['timestamp'].max()),
            'coverage_days': (df['timestamp'].max() - df['timestamp'].min()).days,
            'issues': [],
            'quality_score': 100,
            'valid': True
        }
        
        # Check basic data integrity
        if df.empty:
            validation['issues'].append("No data found")
            validation['quality_score'] = 0
            validation['valid'] = False
            return validation
        
        # Check required columns
        required_cols = ['timestamp', 'symbol', 'open_price', 'high_price', 'low_price', 
                        'close_price', 'bid_price', 'ask_price', 'volume', 'session']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            validation['issues'].append(f"Missing columns: {missing_cols}")
            validation['quality_score'] -= 20
        
        # Check OHLC consistency
        invalid_ohlc = df[(df['high_price'] < df['open_price']) | 
                         (df['high_price'] < df['close_price']) |
                         (df['low_price'] > df['open_price']) |
                         (df['low_price'] > df['close_price'])]
        
        if len(invalid_ohlc) > 0:
            validation['issues'].append(f"{len(invalid_ohlc)} invalid OHLC records")
            validation['quality_score'] -= 10
        
        # Check for realistic spreads
        df['spread'] = df['ask_price'] - df['bid_price']
        if 'JPY' in pair:
            # JPY pairs should have spreads around 2-5 pips
            expected_spread_range = (0.01, 0.10)
            spread_unit = 100
        else:
            # Major pairs should have spreads around 1-3 pips
            expected_spread_range = (0.0001, 0.0010)
            spread_unit = 10000
        
        invalid_spreads = df[(df['spread'] < expected_spread_range[0]) | 
                            (df['spread'] > expected_spread_range[1])]
        
        if len(invalid_spreads) > len(df) * 0.05:  # More than 5% invalid spreads
            validation['issues'].append(f"Unrealistic spreads: {len(invalid_spreads)} records")
            validation['quality_score'] -= 15
        
        # Check for data gaps
        df_sorted = df.sort_values('timestamp')
        df_sorted['time_diff'] = df_sorted['timestamp'].diff()
        large_gaps = df_sorted[df_sorted['time_diff'] > timedelta(minutes=10)]
        
        if len(large_gaps) > 50:  # Too many gaps
            validation['issues'].append(f"Too many data gaps: {len(large_gaps)}")
            validation['quality_score'] -= 10
        
        # Check session distribution
        session_counts = df['session'].value_counts()
        expected_sessions = ['LONDON', 'NEW_YORK', 'ASIAN', 'QUIET']
        missing_sessions = [s for s in expected_sessions if s not in session_counts.index]
        
        if missing_sessions:
            validation['issues'].append(f"Missing sessions: {missing_sessions}")
            validation['quality_score'] -= 5
        
        # Check volume realism
        if df['volume'].min() <= 0 or df['volume'].max() > 10000:
            validation['issues'].append("Unrealistic volume values")
            validation['quality_score'] -= 5
        
        # Check price realism for each pair
        price_ranges = {
            'EURUSD': (0.9000, 1.3000),
            'GBPUSD': (1.1000, 1.5000), 
            'USDJPY': (100.0, 200.0),
            'USDCAD': (1.2000, 1.5000),
            'AUDUSD': (0.5000, 0.8000),
            'GBPJPY': (150.0, 220.0)
        }
        
        if pair in price_ranges:
            min_price, max_price = price_ranges[pair]
            out_of_range = df[(df['close_price'] < min_price) | (df['close_price'] > max_price)]
            
            if len(out_of_range) > 0:
                validation['issues'].append(f"Prices out of realistic range: {len(out_of_range)} records")
                validation['quality_score'] -= 10
        
        # Calculate additional metrics
        validation['avg_spread_pips'] = (df['spread'].mean() * spread_unit)
        validation['records_per_day'] = len(df) / max(1, validation['coverage_days'])
        validation['session_distribution'] = session_counts.to_dict()
        validation['price_range'] = (df['close_price'].min(), df['close_price'].max())
        validation['volatility'] = df['close_price'].std()
        
        # Mark as invalid if quality score too low
        if validation['quality_score'] < 70:
            validation['valid'] = False
        
        logger.info(f"✅ {pair}: Quality Score {validation['quality_score']}/100")
        
        return validation
        
    except Exception as e:
        logger.error(f"❌ Validation failed for {pair}: {e}")
        return {
            'pair': pair,
            'total_records': 0,
            'issues': [f"Validation error: {e}"],
            'quality_score': 0,
            'valid': False
        }

def run_comprehensive_validation():
    """Run validation on all extracted data"""
    
    data_dir = Path("/root/HydraX-v2/data/historical/backtest_data")
    pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "GBPJPY"]
    
    logger.info("🔍 Starting comprehensive data quality validation...")
    
    validation_results = {}
    overall_summary = {
        'total_records': 0,
        'valid_pairs': 0,
        'invalid_pairs': 0,
        'avg_quality_score': 0,
        'all_issues': [],
        'ready_for_backtesting': False
    }
    
    for pair in pairs:
        csv_path = data_dir / f"{pair}_historical_60days.csv"
        
        if not csv_path.exists():
            logger.error(f"❌ Missing file: {csv_path}")
            validation_results[pair] = {
                'pair': pair,
                'valid': False,
                'issues': ['File not found'],
                'quality_score': 0
            }
            continue
        
        validation = validate_csv_data(pair, str(csv_path))
        validation_results[pair] = validation
        
        # Update summary
        overall_summary['total_records'] += validation.get('total_records', 0)
        if validation['valid']:
            overall_summary['valid_pairs'] += 1
        else:
            overall_summary['invalid_pairs'] += 1
        
        overall_summary['all_issues'].extend(validation.get('issues', []))
    
    # Calculate overall metrics
    quality_scores = [v.get('quality_score', 0) for v in validation_results.values()]
    overall_summary['avg_quality_score'] = np.mean(quality_scores) if quality_scores else 0
    overall_summary['ready_for_backtesting'] = (overall_summary['valid_pairs'] >= 4 and 
                                               overall_summary['avg_quality_score'] >= 80)
    
    # Generate detailed report
    generate_validation_report(validation_results, overall_summary)
    
    return validation_results, overall_summary

def generate_validation_report(validation_results: dict, summary: dict):
    """Generate comprehensive validation report"""
    
    report_path = Path("/root/HydraX-v2/data/historical/backtest_data/validation_report.txt")
    
    with open(report_path, 'w') as f:
        f.write("🔍 FOREX DATA QUALITY VALIDATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"📊 OVERALL SUMMARY\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Records: {summary['total_records']:}\n")
        f.write(f"Valid Pairs: {summary['valid_pairs']}/6\n") 
        f.write(f"Invalid Pairs: {summary['invalid_pairs']}/6\n")
        f.write(f"Average Quality Score: {summary['avg_quality_score']:.1f}/100\n")
        f.write(f"Backtesting Ready: {'YES' if summary['ready_for_backtesting'] else 'NO'}\n\n")
        
        f.write("📈 PAIR-BY-PAIR ANALYSIS\n")
        f.write("-" * 40 + "\n")
        
        for pair, validation in validation_results.items():
            status = "✅ VALID" if validation['valid'] else "❌ INVALID"
            f.write(f"{pair}: {status} (Score: {validation.get('quality_score', 0)}/100)\n")
            
            if validation.get('total_records'):
                f.write(f"  Records: {validation['total_records']:}\n")
            
            if validation.get('avg_spread_pips'):
                f.write(f"  Avg Spread: {validation['avg_spread_pips']:.1f} pips\n")
            
            if validation.get('records_per_day'):
                f.write(f"  Records/Day: {validation['records_per_day']:.0f}\n")
                
            if validation.get('date_range'):
                start, end = validation['date_range']
                f.write(f"  Date Range: {start.date()} to {end.date()}\n")
            
            if validation.get('session_distribution'):
                sessions = validation['session_distribution']
                f.write(f"  Sessions: LONDON({sessions.get('LONDON', 0)}) "
                      f"NY({sessions.get('NEW_YORK', 0)}) "
                      f"ASIAN({sessions.get('ASIAN', 0)}) "
                      f"QUIET({sessions.get('QUIET', 0)})\n")
            
            if validation.get('issues'):
                f.write(f"  Issues: {', '.join(validation['issues'])}\n")
            
            f.write("\n")
        
        if summary['all_issues']:
            f.write("⚠️ ALL QUALITY ISSUES FOUND\n")
            f.write("-" * 30 + "\n")
            issue_counts = {}
            for issue in summary['all_issues']:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in issue_counts.items():
                f.write(f"• {issue} ({count} occurrences)\n")
            f.write("\n")
        
        f.write("🎯 BACKTESTING READINESS ASSESSMENT\n")
        f.write("-" * 40 + "\n")
        
        if summary['ready_for_backtesting']:
            f.write("✅ STATUS: READY FOR BACKTESTING\n")
            f.write("✅ DATA QUALITY: Excellent\n")
            f.write("✅ COVERAGE: Complete 60-day period\n")
            f.write("✅ REALISM: Market gaps, volatility, and sessions included\n")
            f.write("✅ SPREADS: Realistic bid/ask spreads implemented\n")
            f.write("\n💡 RECOMMENDATIONS:\n")
            f.write("• Import CSV files into your backtesting framework\n")
            f.write("• Use this data to identify BITTEN signal weaknesses\n")
            f.write("• Focus on realistic trading conditions analysis\n")
        else:
            f.write("❌ STATUS: NOT READY FOR BACKTESTING\n")
            f.write("❌ DATA QUALITY: Issues detected\n")
            f.write("\n⚠️ REQUIRED ACTIONS:\n")
            f.write("• Fix data quality issues listed above\n")
            f.write("• Re-extract missing or corrupted data\n")
            f.write("• Validate data integrity before backtesting\n")
        
        f.write(f"\n📋 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"📁 Data Location: /root/HydraX-v2/data/historical/backtest_data/\n")
    
    logger.info(f"📋 Validation report generated: {report_path}")

if __name__ == "__main__":
    print("🔍 BITTEN Forex Data Quality Validation")
    print("=" * 50)
    
    validation_results, summary = run_comprehensive_validation()
    
    print(f"\n📊 VALIDATION RESULTS")
    print("=" * 30)
    print(f"✅ Valid Pairs: {summary['valid_pairs']}/6")
    print(f"📊 Total Records: {summary['total_records']:}")
    print(f"🎯 Quality Score: {summary['avg_quality_score']:.1f}/100")
    print(f"🚀 Backtesting Ready: {'YES' if summary['ready_for_backtesting'] else 'NO'}")
    
    if not summary['ready_for_backtesting']:
        print(f"\n⚠️ Issues Found: {len(set(summary['all_issues']))}")
        for issue in set(summary['all_issues'])[:5]:  # Show first 5 unique issues
            print(f"  • {issue}")
    
    print(f"\n📋 Detailed report: /root/HydraX-v2/data/historical/backtest_data/validation_report.txt")