#!/usr/bin/env python3
"""
ML Integration Example - How to integrate Crypto ML Scorer with Elite Guard
Demonstrates the integration points and expected performance improvements
"""

import json
import time
import logging
from typing import Dict, Optional, Tuple, Any
from crypto_ml_scorer import get_crypto_ml_scorer, MarketFeatures

logger = logging.getLogger('MLIntegration')

class MLEnhancedEliteGuard:
    """
    Example integration of ML Scorer with Elite Guard signals
    Shows how to enhance SMC pattern signals with ML predictions
    """
    
    def __init__(self):
        self.ml_scorer = get_crypto_ml_scorer()
        self.performance_tracker = {
            'base_signals': {'total': 0, 'wins': 0, 'win_rate': 0.0},
            'ml_enhanced': {'total': 0, 'wins': 0, 'win_rate': 0.0},
            'improvement': 0.0
        }
        
        logger.info("🔗 ML Enhanced Elite Guard initialized")
    
    def process_smc_signal(self, smc_signal: Dict) -> Tuple[Dict, Dict]:
        """
        Process SMC signal through ML scorer
        
        Args:
            smc_signal: Original SMC pattern signal from Elite Guard
            
        Returns:
            (enhanced_signal, ml_metadata)
        """
        try:
            # Extract signal details
            symbol = smc_signal.get('symbol', 'UNKNOWN')
            base_score = smc_signal.get('confidence', 65.0)
            pattern = smc_signal.get('pattern', 'unknown')
            
            # Update ML scorer with latest market data if available
            if 'market_data' in smc_signal:
                self.ml_scorer.update_market_data(symbol, smc_signal['market_data'])
            
            # Get timeframe data for TF alignment
            timeframe_data = smc_signal.get('timeframe_data', None)
            
            # Enhance signal with ML scoring
            enhanced_score, ml_metadata = self.ml_scorer.enhance_signal_score(
                symbol=symbol,
                base_score=base_score,
                timeframe_data=timeframe_data
            )
            
            # Create enhanced signal
            enhanced_signal = smc_signal.copy()
            enhanced_signal.update({
                'original_confidence': base_score,
                'confidence': enhanced_score,
                'ml_enhanced': True,
                'ml_improvement': enhanced_score - base_score,
                'ml_status': ml_metadata.get('status', 'unknown')
            })
            
            logger.info(f"🎯 Enhanced {pattern} signal for {symbol}: "
                       f"{base_score:.1f} → {enhanced_score:.1f} "
                       f"({enhanced_score - base_score:+.1f})")
            
            return enhanced_signal, ml_metadata
            
        except Exception as e:
            logger.error(f"Error processing SMC signal: {e}")
            # Return original signal on error
            return smc_signal, {"status": "error", "error": str(e)}
    
    def record_signal_outcome(self, signal_id: str, outcome_data: Dict):
        """Record signal outcome for ML training"""
        try:
            # Extract outcome
            outcome = outcome_data.get('outcome') == 'WIN'
            
            # Get original features if available
            if 'ml_metadata' in outcome_data and 'features' in outcome_data['ml_metadata']:
                features_dict = outcome_data['ml_metadata']['features']
                features = MarketFeatures(**features_dict)
                
                # Record for ML training
                self.ml_scorer.record_signal_outcome(
                    signal_id=signal_id,
                    features=features,
                    outcome=outcome,
                    outcome_data=outcome_data
                )
                
                # Update performance tracking
                was_ml_enhanced = outcome_data.get('was_ml_enhanced', False)
                
                if was_ml_enhanced:
                    self.performance_tracker['ml_enhanced']['total'] += 1
                    if outcome:
                        self.performance_tracker['ml_enhanced']['wins'] += 1
                else:
                    self.performance_tracker['base_signals']['total'] += 1
                    if outcome:
                        self.performance_tracker['base_signals']['wins'] += 1
                
                # Update win rates
                self._update_win_rates()
                
                logger.info(f"📊 Recorded outcome for {signal_id}: {'WIN' if outcome else 'LOSS'}")
                
        except Exception as e:
            logger.error(f"Error recording signal outcome: {e}")
    
    def _update_win_rates(self):
        """Update win rate calculations"""
        # Base signals win rate
        base_total = self.performance_tracker['base_signals']['total']
        if base_total > 0:
            base_wins = self.performance_tracker['base_signals']['wins']
            self.performance_tracker['base_signals']['win_rate'] = (base_wins / base_total) * 100
        
        # ML enhanced win rate
        ml_total = self.performance_tracker['ml_enhanced']['total']
        if ml_total > 0:
            ml_wins = self.performance_tracker['ml_enhanced']['wins']
            self.performance_tracker['ml_enhanced']['win_rate'] = (ml_wins / ml_total) * 100
        
        # Calculate improvement
        base_rate = self.performance_tracker['base_signals']['win_rate']
        ml_rate = self.performance_tracker['ml_enhanced']['win_rate']
        self.performance_tracker['improvement'] = ml_rate - base_rate
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get ML enhancement performance report"""
        return {
            'performance_tracker': self.performance_tracker,
            'ml_model_stats': self.ml_scorer.get_model_stats(),
            'timestamp': time.time(),
            'status': 'operational' if self.ml_scorer.model else 'training'
        }

# Example usage functions for integration

def elite_guard_ml_integration_example():
    """Example of how to integrate ML scorer with Elite Guard"""
    
    print("🔗 Elite Guard ML Integration Example")
    print("=" * 50)
    
    # Initialize ML enhanced system
    enhanced_guard = MLEnhancedEliteGuard()
    
    # Simulate SMC signals from Elite Guard
    example_signals = [
        {
            'signal_id': 'EG_001',
            'symbol': 'BTCUSD',
            'pattern': 'LIQUIDITY_SWEEP_REVERSAL',
            'direction': 'BUY',
            'confidence': 72.5,
            'entry_price': 45000,
            'stop_loss': 44500,
            'take_profit': 46000,
            'market_data': {
                'bid': 45000,
                'ask': 45010,
                'spread': 0.0002,
                'volume': 5000,
                'timestamp': time.time()
            },
            'timeframe_data': {
                'M1': [
                    {'open': 44900, 'high': 45100, 'low': 44850, 'close': 45000, 'time': time.time()-180},
                    {'open': 45000, 'high': 45050, 'low': 44950, 'close': 45020, 'time': time.time()-120},
                    {'open': 45020, 'high': 45080, 'low': 45000, 'close': 45030, 'time': time.time()-60}
                ]
            }
        },
        {
            'signal_id': 'EG_002',
            'symbol': 'ETHUSD',
            'pattern': 'ORDER_BLOCK_BOUNCE',
            'direction': 'SELL',
            'confidence': 68.0,
            'entry_price': 3200,
            'stop_loss': 3250,
            'take_profit': 3100,
            'market_data': {
                'bid': 3199,
                'ask': 3201,
                'spread': 0.0006,
                'volume': 2000,
                'timestamp': time.time()
            }
        }
    ]
    
    # Process signals through ML enhancement
    enhanced_signals = []
    for signal in example_signals:
        enhanced_signal, ml_metadata = enhanced_guard.process_smc_signal(signal)
        enhanced_signals.append((enhanced_signal, ml_metadata))
        
        print(f"\n📊 Signal {signal['signal_id']} ({signal['symbol']}):")
        print(f"  Pattern: {signal['pattern']}")
        print(f"  Base Score: {signal['confidence']:.1f}")
        print(f"  Enhanced Score: {enhanced_signal['confidence']:.1f}")
        print(f"  Improvement: {enhanced_signal['ml_improvement']:+.1f}")
        print(f"  ML Status: {ml_metadata['status']}")
        
        if 'features' in ml_metadata:
            features = ml_metadata['features']
            print(f"  Key Features:")
            print(f"    ATR Volatility: {features['atr_volatility']:.1f}")
            print(f"    Volume Delta: {features['volume_delta']:.1f}")
            print(f"    TF Alignment: {features['tf_alignment']:.1f}")
            print(f"    Session Bonus: {features['session_bonus']:.1f}")
    
    # Simulate outcomes and record them
    print(f"\n📈 Recording Simulated Outcomes:")
    for i, (signal, ml_metadata) in enumerate(enhanced_signals):
        # Simulate random outcome (in real system, this comes from truth tracker)
        import random
        outcome = random.choice(['WIN', 'LOSS'])
        
        outcome_data = {
            'outcome': outcome,
            'outcome_type': 'WIN_TP' if outcome == 'WIN' else 'LOSS_SL',
            'runtime_minutes': random.randint(30, 240),
            'max_favorable_pips': random.uniform(5, 25),
            'max_adverse_pips': random.uniform(-15, -5),
            'final_pips': random.uniform(8, 20) if outcome == 'WIN' else random.uniform(-12, -8),
            'was_ml_enhanced': True,
            'ml_metadata': ml_metadata
        }
        
        enhanced_guard.record_signal_outcome(signal['signal_id'], outcome_data)
        print(f"  {signal['signal_id']}: {outcome}")
    
    # Show performance report
    print(f"\n🎯 Performance Report:")
    report = enhanced_guard.get_performance_report()
    perf = report['performance_tracker']
    
    print(f"  Base Signals: {perf['base_signals']['total']} total, "
          f"{perf['base_signals']['win_rate']:.1f}% win rate")
    print(f"  ML Enhanced: {perf['ml_enhanced']['total']} total, "
          f"{perf['ml_enhanced']['win_rate']:.1f}% win rate")
    print(f"  Improvement: {perf['improvement']:+.1f}%")
    
    print(f"\n🤖 ML Model Status:")
    stats = report['ml_model_stats']
    print(f"  Model Available: {stats['model_available']}")
    print(f"  Training Samples: {stats['sample_count']}")
    print(f"  Avg Prediction Time: {stats['avg_prediction_time_ms']:.2f}ms")
    print(f"  Cache Size: {stats['cache_size']}")

def integration_code_example():
    """Show code example for integrating with existing Elite Guard"""
    
    print("\n💻 Integration Code Example:")
    print("=" * 40)
    
    code_example = '''
# In elite_guard_with_citadel.py - Add ML enhancement

from crypto_ml_scorer import get_crypto_ml_scorer

class EliteGuardWithCitadel:
    def __init__(self):
        # ... existing initialization ...
        self.ml_scorer = get_crypto_ml_scorer()
    
    def generate_pattern_signal(self, pattern_signal):
        """Enhanced pattern signal generation with ML scoring"""
        
        # Original SMC pattern detection
        base_confidence = pattern_signal.confidence
        
        # Update ML scorer with latest market data
        if self.tick_data[pattern_signal.pair]:
            latest_tick = list(self.tick_data[pattern_signal.pair])[-1]
            self.ml_scorer.update_market_data(pattern_signal.pair, latest_tick)
        
        # Prepare timeframe data
        timeframe_data = {
            'M1': list(self.m1_data[pattern_signal.pair])[-10:],
            'M5': list(self.m5_data[pattern_signal.pair])[-10:],
            'M15': list(self.m15_data[pattern_signal.pair])[-10:]
        }
        
        # Enhance with ML scoring
        enhanced_score, ml_metadata = self.ml_scorer.enhance_signal_score(
            symbol=pattern_signal.pair,
            base_score=base_confidence,
            timeframe_data=timeframe_data
        )
        
        # Update signal with ML enhancement
        pattern_signal.confidence = enhanced_score
        pattern_signal.ml_enhanced = True
        pattern_signal.ml_metadata = ml_metadata
        
        return pattern_signal
    
    def record_signal_outcome(self, signal_id, outcome_data):
        """Record outcome for ML training"""
        if hasattr(self, 'ml_scorer') and 'ml_metadata' in outcome_data:
            features_dict = outcome_data['ml_metadata']['features']
            features = MarketFeatures(**features_dict)
            
            outcome = outcome_data['outcome'] == 'WIN'
            
            self.ml_scorer.record_signal_outcome(
                signal_id=signal_id,
                features=features,
                outcome=outcome,
                outcome_data=outcome_data
            )
'''
    
    print(code_example)

if __name__ == "__main__":
    elite_guard_ml_integration_example()
    integration_code_example()