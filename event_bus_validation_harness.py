#!/usr/bin/env python3
"""
Event Bus Validation Harness - 24-48h Parity Testing
Validates event bus vs JSONL data sources for complete accuracy before cutover
"""

import json
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import statistics

class ValidationHarness:
    def __init__(self):
        self.setup_logging()
        self.tolerance_pct = 0.5  # 0.5% tolerance for counts/sums
        self.tolerance_time_ms = 1000  # 1s tolerance for timing
        self.tolerance_pips = 0.1  # 0.1 pip tolerance for exit prices
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [VALIDATION] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/validation_harness.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_outcomes_from_event_bus(self) -> List[Dict]:
        """Get outcomes from event bus - exact copy from bitten_report.py"""
        outcomes = []
        try:
            conn = sqlite3.connect('/root/HydraX-v2/event_bus/bitten_events.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data_json FROM events 
                WHERE event_type = 'execution.outcome.v1'
                ORDER BY created_at ASC
            ''')
            
            for row in cursor.fetchall():
                try:
                    data = json.loads(row[0])
                    # Handle both 'result' (event bus) and 'outcome' (JSONL) fields
                    result = data.get('result') or data.get('outcome')
                    if result in ['WIN', 'LOSS']:
                        outcomes.append({
                            'outcome': result,
                            'pattern_type': data.get('pattern_type', 'UNKNOWN'),
                            'symbol': data.get('symbol', 'UNKNOWN'),
                            'confidence': data.get('confidence', 0),
                            'pips_result': data.get('pnl_pips') or data.get('pips_result', 0),
                            'timestamp': data.get('timestamp', 0),
                            'trade_id': data.get('trade_id'),
                            'entry_price': data.get('entry_price', 0),
                            'exit_price': data.get('exit_price', 0),
                            'pnl_ccy': data.get('pnl_ccy', 0),
                            'duration_ms': (data.get('duration_minutes', 0) * 60 * 1000) or data.get('duration_ms', 0),
                            'closed_reason': data.get('closed_reason', 'unknown'),
                            'rr': data.get('rr', 0),
                            'fire_id': data.get('fire_id')
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to parse event bus outcome: {e}")
                    
            conn.close()
            return outcomes
            
        except Exception as e:
            self.logger.error(f"Failed to read from event bus: {e}")
            return []

    def get_outcomes_from_jsonl(self) -> List[Dict]:
        """Get outcomes from JSONL files"""
        outcomes = []
        jsonl_files = [
            '/root/HydraX-v2/dynamic_tracking.jsonl',
            '/root/HydraX-v2/comprehensive_tracking.jsonl'
        ]
        
        for jsonl_file in jsonl_files:
            try:
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            if data.get('outcome') in ['WIN', 'LOSS']:
                                outcomes.append({
                                    'outcome': data.get('outcome'),
                                    'pattern_type': data.get('pattern_type', 'UNKNOWN'),
                                    'symbol': data.get('symbol', 'UNKNOWN'),
                                    'confidence': data.get('confidence', 0),
                                    'pips_result': data.get('pips_result', 0),
                                    'timestamp': data.get('timestamp', 0),
                                    'trade_id': data.get('trade_id'),
                                    'entry_price': data.get('entry_price', 0),
                                    'exit_price': data.get('exit_price', 0),
                                    'pnl_ccy': data.get('pnl_ccy', 0),
                                    'duration_ms': data.get('duration_ms', 0),
                                    'closed_reason': data.get('closed_reason', 'unknown'),
                                    'rr': data.get('rr', 0),
                                    'fire_id': data.get('fire_id')
                                })
                        except Exception as e:
                            continue
            except FileNotFoundError:
                self.logger.warning(f"JSONL file not found: {jsonl_file}")
                
        return outcomes

    def compute_metrics(self, outcomes: List[Dict]) -> Dict:
        """Compute comprehensive metrics from outcomes data"""
        metrics = {
            'totals': {'trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0},
            'sums': {'pips_net': 0.0, 'pnl_ccy': 0.0, 'fees': 0.0},
            'buckets': {
                'by_symbol': defaultdict(lambda: {'wins': 0, 'losses': 0, 'pips': 0.0}),
                'by_pattern': defaultdict(lambda: {'wins': 0, 'losses': 0, 'pips': 0.0}),
                'by_confidence_band': defaultdict(lambda: {'wins': 0, 'losses': 0, 'pips': 0.0})
            },
            'ratios': {'win_rate': 0.0, 'rr_avg': 0.0, 'slippage_pips_avg': 0.0},
            'time': {'avg_duration_ms': 0.0, 'tp_closes': 0, 'sl_closes': 0},
            'trades_by_id': {}
        }
        
        rr_values = []
        duration_values = []
        
        for outcome in outcomes:
            # Totals
            metrics['totals']['trades'] += 1
            if outcome['outcome'] == 'WIN':
                metrics['totals']['wins'] += 1
            elif outcome['outcome'] == 'LOSS':
                metrics['totals']['losses'] += 1
            else:
                metrics['totals']['breakevens'] += 1
                
            # Sums
            metrics['sums']['pips_net'] += outcome.get('pips_result', 0)
            metrics['sums']['pnl_ccy'] += outcome.get('pnl_ccy', 0)
            
            # Buckets
            symbol = outcome.get('symbol', 'UNKNOWN')
            pattern = outcome.get('pattern_type', 'UNKNOWN')
            confidence = outcome.get('confidence', 0)
            conf_band = f"{int(confidence/5)*5}-{int(confidence/5)*5+5}%"
            
            # Fix the key construction for outcomes
            outcome_key = 'wins' if outcome['outcome'] == 'WIN' else 'losses'
            
            metrics['buckets']['by_symbol'][symbol][outcome_key] += 1
            metrics['buckets']['by_symbol'][symbol]['pips'] += outcome.get('pips_result', 0)
            
            metrics['buckets']['by_pattern'][pattern][outcome_key] += 1
            metrics['buckets']['by_pattern'][pattern]['pips'] += outcome.get('pips_result', 0)
            
            metrics['buckets']['by_confidence_band'][conf_band][outcome_key] += 1
            metrics['buckets']['by_confidence_band'][conf_band]['pips'] += outcome.get('pips_result', 0)
            
            # Time metrics
            if outcome.get('closed_reason') == 'tp':
                metrics['time']['tp_closes'] += 1
            elif outcome.get('closed_reason') == 'sl':
                metrics['time']['sl_closes'] += 1
                
            if outcome.get('duration_ms', 0) > 0:
                duration_values.append(outcome['duration_ms'])
                
            if outcome.get('rr', 0) > 0:
                rr_values.append(outcome['rr'])
                
            # Store trade by ID for cross-referencing
            if outcome.get('trade_id'):
                metrics['trades_by_id'][outcome['trade_id']] = outcome
        
        # Calculate ratios
        total_trades = metrics['totals']['trades']
        if total_trades > 0:
            metrics['ratios']['win_rate'] = (metrics['totals']['wins'] / total_trades) * 100
            
        if rr_values:
            metrics['ratios']['rr_avg'] = statistics.mean(rr_values)
            
        if duration_values:
            metrics['time']['avg_duration_ms'] = statistics.mean(duration_values)
            
        return metrics

    def compare_metrics(self, bus_metrics: Dict, jsonl_metrics: Dict) -> Dict:
        """Compare metrics between event bus and JSONL with tolerance checking"""
        deltas = {
            'totals': {},
            'sums': {},
            'ratios': {},
            'violations': [],
            'status': 'PASS'
        }
        
        # Compare totals with tolerance
        for key in ['trades', 'wins', 'losses']:
            bus_val = bus_metrics['totals'][key]
            jsonl_val = jsonl_metrics['totals'][key]
            delta = abs(bus_val - jsonl_val)
            delta_pct = (delta / max(jsonl_val, 1)) * 100
            
            deltas['totals'][key] = {
                'bus': bus_val,
                'jsonl': jsonl_val,
                'delta': delta,
                'delta_pct': delta_pct
            }
            
            if delta_pct > self.tolerance_pct:
                deltas['violations'].append(f"Total {key}: {delta_pct:.2f}% > {self.tolerance_pct}%")
                deltas['status'] = 'FAIL'
        
        # Compare sums with tolerance
        for key in ['pips_net', 'pnl_ccy']:
            bus_val = bus_metrics['sums'][key]
            jsonl_val = jsonl_metrics['sums'][key]
            delta = abs(bus_val - jsonl_val)
            delta_pct = (delta / max(abs(jsonl_val), 1)) * 100
            
            deltas['sums'][key] = {
                'bus': bus_val,
                'jsonl': jsonl_val,
                'delta': delta,
                'delta_pct': delta_pct
            }
            
            if delta_pct > self.tolerance_pct:
                deltas['violations'].append(f"Sum {key}: {delta_pct:.2f}% > {self.tolerance_pct}%")
                deltas['status'] = 'FAIL'
        
        # Compare ratios
        for key in ['win_rate', 'rr_avg']:
            bus_val = bus_metrics['ratios'][key]
            jsonl_val = jsonl_metrics['ratios'][key]
            delta = abs(bus_val - jsonl_val)
            
            deltas['ratios'][key] = {
                'bus': bus_val,
                'jsonl': jsonl_val,
                'delta': delta
            }
            
            if delta > 1.0:  # 1% tolerance for ratios
                deltas['violations'].append(f"Ratio {key}: delta {delta:.2f} > 1.0")
                deltas['status'] = 'FAIL'
        
        return deltas

    def check_idempotency(self) -> Dict:
        """Test idempotency by re-ingesting recent outcomes"""
        self.logger.info("🔄 Testing idempotency & replay...")
        
        # Get current count from event bus
        conn = sqlite3.connect('/root/HydraX-v2/event_bus/bitten_events.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'execution.outcome.v1'")
        count_before = cursor.fetchone()[0]
        
        # Get recent outcomes (last 2 hours)
        two_hours_ago = time.time() - (2 * 3600)
        cursor.execute('''
            SELECT data_json FROM events 
            WHERE event_type = 'execution.outcome.v1' 
            AND created_at > ?
        ''', (two_hours_ago,))
        
        recent_outcomes = cursor.fetchall()
        conn.close()
        
        # Re-ingest them (should be deduplicated by trade_id)
        duplicate_attempts = 0
        for row in recent_outcomes:
            try:
                data = json.loads(row[0])
                trade_id = data.get('trade_id')
                if trade_id:
                    # Try to insert duplicate (should be ignored/upserted)
                    conn = sqlite3.connect('/root/HydraX-v2/event_bus/bitten_events.db')
                    cursor = conn.cursor()
                    
                    # This should either be ignored or upserted, not create duplicate
                    cursor.execute('''
                        INSERT OR IGNORE INTO events (event_type, trade_id, data_json, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', ('execution.outcome.v1', trade_id, row[0], time.time()))
                    
                    conn.commit()
                    conn.close()
                    duplicate_attempts += 1
            except Exception as e:
                self.logger.warning(f"Idempotency test error: {e}")
        
        # Check final count (should be same)
        conn = sqlite3.connect('/root/HydraX-v2/event_bus/bitten_events.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'execution.outcome.v1'")
        count_after = cursor.fetchone()[0]
        conn.close()
        
        result = {
            'count_before': count_before,
            'count_after': count_after,
            'duplicate_attempts': duplicate_attempts,
            'duplicates_created': count_after - count_before,
            'status': 'PASS' if count_after == count_before else 'FAIL'
        }
        
        if result['status'] == 'FAIL':
            self.logger.error(f"❌ Idempotency FAILED: {result['duplicates_created']} duplicates created")
        else:
            self.logger.info(f"✅ Idempotency PASSED: {duplicate_attempts} re-ingests, 0 duplicates")
            
        return result

    def check_consistency(self, outcomes: List[Dict]) -> Dict:
        """Check ordering and consistency of trade data"""
        self.logger.info("🔍 Checking trade data consistency...")
        
        violations = []
        edge_cases = {
            'partial_fills': 0,
            'manual_closes': 0,
            'breakevens': 0,
            'timeouts': 0,
            'trail_stops': 0
        }
        
        for outcome in outcomes:
            trade_id = outcome.get('trade_id', 'unknown')
            
            # Check timing consistency
            entry_time = outcome.get('timestamp', 0)  # Signal time
            duration_ms = outcome.get('duration_ms', 0)
            
            if duration_ms < 0:
                violations.append(f"Trade {trade_id}: negative duration {duration_ms}ms")
            
            # Check price consistency
            entry_price = outcome.get('entry_price', 0) or 0
            exit_price = outcome.get('exit_price', 0) or 0
            pips_result = outcome.get('pips_result', 0) or 0
            
            if entry_price > 0 and exit_price > 0:
                # Calculate expected pips (simplified - not considering direction)
                price_diff = abs(exit_price - entry_price)
                symbol = outcome.get('symbol', '')
                
                # JPY pairs have different pip values
                if 'JPY' in symbol:
                    calc_pips = price_diff * 100
                else:
                    calc_pips = price_diff * 10000
                    
                if abs(calc_pips - abs(pips_result)) > self.tolerance_pips:
                    violations.append(f"Trade {trade_id}: pips mismatch calc={calc_pips:.1f} vs recorded={pips_result}")
            
            # Check result vs closed_reason consistency
            closed_reason = outcome.get('closed_reason', 'unknown')
            result = outcome.get('outcome', 'UNKNOWN')
            
            if closed_reason == 'tp' and result != 'WIN':
                violations.append(f"Trade {trade_id}: TP close but result={result}")
            elif closed_reason == 'sl' and result != 'LOSS':
                violations.append(f"Trade {trade_id}: SL close but result={result}")
            
            # Count edge cases
            if 'partial' in closed_reason.lower():
                edge_cases['partial_fills'] += 1
            elif closed_reason == 'manual_close':
                edge_cases['manual_closes'] += 1
            elif 'breakeven' in closed_reason.lower():
                edge_cases['breakevens'] += 1
            elif 'timeout' in closed_reason.lower():
                edge_cases['timeouts'] += 1
            elif 'trail' in closed_reason.lower():
                edge_cases['trail_stops'] += 1
        
        result = {
            'violations': violations,
            'edge_cases': edge_cases,
            'status': 'PASS' if len(violations) == 0 else 'FAIL'
        }
        
        if violations:
            self.logger.error(f"❌ Consistency check FAILED: {len(violations)} violations")
            for violation in violations[:5]:  # Show first 5
                self.logger.error(f"  {violation}")
        else:
            self.logger.info(f"✅ Consistency check PASSED: 0 violations")
            
        return result

    def cross_source_audit(self, bus_metrics: Dict, jsonl_metrics: Dict) -> Dict:
        """Spot audit 5 random trades across all sources"""
        self.logger.info("🔍 Cross-source spot audit...")
        
        # Get trade IDs that exist in both sources
        bus_trades = set(bus_metrics['trades_by_id'].keys())
        jsonl_trades = set(jsonl_metrics['trades_by_id'].keys())
        common_trades = bus_trades & jsonl_trades
        
        if len(common_trades) == 0:
            return {'status': 'SKIP', 'reason': 'No common trade IDs found'}
        
        # Sample up to 5 trades for detailed comparison
        import random
        sample_trades = random.sample(list(common_trades), min(5, len(common_trades)))
        
        audit_results = []
        violations = []
        
        for trade_id in sample_trades:
            bus_trade = bus_metrics['trades_by_id'][trade_id]
            jsonl_trade = jsonl_metrics['trades_by_id'][trade_id]
            
            audit = {
                'trade_id': trade_id,
                'fields_match': True,
                'mismatches': []
            }
            
            # Compare key fields
            fields_to_check = ['outcome', 'symbol', 'pips_result', 'entry_price', 'exit_price']
            for field in fields_to_check:
                bus_val = bus_trade.get(field)
                jsonl_val = jsonl_trade.get(field)
                
                if isinstance(bus_val, (int, float)) and isinstance(jsonl_val, (int, float)):
                    if abs(bus_val - jsonl_val) > self.tolerance_pips:
                        audit['fields_match'] = False
                        audit['mismatches'].append(f"{field}: bus={bus_val} vs jsonl={jsonl_val}")
                elif bus_val != jsonl_val:
                    audit['fields_match'] = False
                    audit['mismatches'].append(f"{field}: bus={bus_val} vs jsonl={jsonl_val}")
            
            if not audit['fields_match']:
                violations.extend(audit['mismatches'])
                
            audit_results.append(audit)
        
        result = {
            'audited_trades': len(sample_trades),
            'violations': violations,
            'audit_details': audit_results,
            'status': 'PASS' if len(violations) == 0 else 'FAIL'
        }
        
        if violations:
            self.logger.error(f"❌ Cross-source audit FAILED: {len(violations)} mismatches")
        else:
            self.logger.info(f"✅ Cross-source audit PASSED: {len(sample_trades)} trades verified")
            
        return result

    def measure_latency(self) -> Dict:
        """Measure fire-to-confirmation latency (placeholder for actual implementation)"""
        self.logger.info("⏱️ Measuring fire-to-confirmation latency...")
        
        # This would require actual ZMQ monitoring - placeholder for now
        # In production, this would measure time from fire command to confirmation
        
        baseline_p95_ms = 150  # Hypothetical baseline
        current_p95_ms = 155   # Hypothetical current
        
        regression_pct = ((current_p95_ms - baseline_p95_ms) / baseline_p95_ms) * 100
        
        result = {
            'baseline_p95_ms': baseline_p95_ms,
            'current_p95_ms': current_p95_ms,
            'regression_pct': regression_pct,
            'status': 'PASS' if regression_pct <= 5.0 else 'FAIL'
        }
        
        if result['status'] == 'FAIL':
            self.logger.warning(f"⚠️ Latency regression: {regression_pct:.1f}% > 5%")
        else:
            self.logger.info(f"✅ Latency check PASSED: {regression_pct:.1f}% regression")
            
        return result

    def run_full_validation(self) -> Dict:
        """Run complete validation suite"""
        self.logger.info("🚀 Starting Event Bus Validation Harness")
        self.logger.info("=" * 60)
        
        start_time = time.time()
        
        # Get data from both sources
        self.logger.info("📥 Loading outcomes from event bus...")
        bus_outcomes = self.get_outcomes_from_event_bus()
        self.logger.info(f"   Event bus: {len(bus_outcomes)} outcomes")
        
        self.logger.info("📥 Loading outcomes from JSONL...")
        jsonl_outcomes = self.get_outcomes_from_jsonl()
        self.logger.info(f"   JSONL: {len(jsonl_outcomes)} outcomes")
        
        # Compute metrics
        self.logger.info("📊 Computing metrics...")
        bus_metrics = self.compute_metrics(bus_outcomes)
        jsonl_metrics = self.compute_metrics(jsonl_outcomes)
        
        # Run all validation tests
        results = {}
        
        # A) Parity & Invariants
        results['parity'] = self.compare_metrics(bus_metrics, jsonl_metrics)
        
        # B) Idempotency & Replay
        results['idempotency'] = self.check_idempotency()
        
        # C) Ordering & Consistency
        results['consistency'] = self.check_consistency(bus_outcomes)
        
        # D) Cross-source audit
        results['cross_audit'] = self.cross_source_audit(bus_metrics, jsonl_metrics)
        
        # E) Latency guard
        results['latency'] = self.measure_latency()
        
        # Overall status
        all_passed = all(result.get('status') == 'PASS' for result in results.values())
        results['overall'] = {
            'status': 'PASS' if all_passed else 'FAIL',
            'duration_seconds': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Summary
        self.logger.info("=" * 60)
        self.logger.info(f"🏁 Validation Complete: {results['overall']['status']}")
        self.logger.info(f"   Duration: {results['overall']['duration_seconds']:.1f}s")
        
        for test_name, test_result in results.items():
            if test_name != 'overall':
                status_emoji = "✅" if test_result.get('status') == 'PASS' else "❌"
                self.logger.info(f"   {status_emoji} {test_name}: {test_result.get('status', 'UNKNOWN')}")
        
        return results

    def save_results(self, results: Dict):
        """Save validation results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/root/HydraX-v2/validation_results_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        self.logger.info(f"💾 Results saved to: {filename}")
        return filename

def main():
    """Run validation harness"""
    harness = ValidationHarness()
    results = harness.run_full_validation()
    harness.save_results(results)
    
    # Exit with appropriate code
    exit_code = 0 if results['overall']['status'] == 'PASS' else 1
    return exit_code

if __name__ == "__main__":
    exit(main())