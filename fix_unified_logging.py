#!/usr/bin/env python3
"""
Fix unified logging integration for Elite Guard and Grokkeeper
Ensures all signals are logged with complete metrics
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timedelta
import pytz

# Add parent directory for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

def patch_elite_guard():
    """Add unified logging to Elite Guard"""
    
    patch_code = '''
# Add this at the top of elite_guard_with_citadel.py after imports:
import sys
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

# Replace the publish_signal method (around line 1500) with:
def publish_signal(self, signal_data):
    """Publish signal and log to unified tracking"""
    try:
        # Calculate additional metrics for unified logging
        symbol = signal_data.get('symbol', '')
        pip_multiplier = 100 if 'JPY' in symbol else (1 if symbol == 'XAUUSD' else 10000)
        
        entry = float(signal_data.get('entry', 0))
        sl = float(signal_data.get('sl', 0))
        tp = float(signal_data.get('tp', 0))
        
        sl_pips = abs(entry - sl) * pip_multiplier
        tp_pips = abs(tp - entry) * pip_multiplier
        
        # Prepare comprehensive trade data
        trade_data = {
            'signal_id': signal_data.get('signal_id'),
            'pattern': signal_data.get('pattern'),
            'confidence': signal_data.get('confidence'),
            'symbol': symbol,
            'direction': signal_data.get('direction'),
            'entry': entry,
            'sl': sl,
            'tp': tp,
            'sl_pips': sl_pips,
            'tp_pips': tp_pips,
            'lot_size': signal_data.get('lot_size', 0.01),
            'session': signal_data.get('session', self.get_current_session()),
            'citadel_score': signal_data.get('citadel_score', 0),
            'rsi': signal_data.get('rsi', 50),
            'volume_ratio': signal_data.get('volume_ratio', 1.0),
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'executed': signal_data.get('confidence', 0) >= 85
        }
        
        # Log to unified tracking
        log_trade(trade_data)
        
        # Also publish to ZMQ for real-time systems
        if self.publisher:
            signal_msg = json.dumps(signal_data)
            self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
            
    except Exception as e:
        print(f"Error in publish_signal: {e}")

# Add helper method for session detection:
def get_current_session(self):
    """Get current trading session"""
    hour = datetime.now(pytz.UTC).hour
    if 22 <= hour or hour < 7:
        return "ASIAN"
    elif 7 <= hour < 12:
        return "LONDON"
    elif 12 <= hour < 17:
        return "NEWYORK"
    else:
        return "OVERLAP"
'''
    
    print("Elite Guard Patch Instructions:")
    print("=" * 60)
    print(patch_code)
    print("=" * 60)
    
    # Save patch file
    with open('/root/HydraX-v2/elite_guard_unified_patch.txt', 'w') as f:
        f.write(patch_code)
    
    print("\n✅ Patch saved to: /root/HydraX-v2/elite_guard_unified_patch.txt")

def create_grokkeeper_reader():
    """Create Grokkeeper integration with unified log"""
    
    grokkeeper_code = '''#!/usr/bin/env python3
"""
Grokkeeper ML Integration with Unified Logging
Reads from comprehensive_tracking.jsonl for ML analysis
"""

import pandas as pd
import numpy as np
import json
import zmq
import time
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrokkeeperML:
    def __init__(self):
        self.log_file = "/root/HydraX-v2/logs/comprehensive_tracking.jsonl"
        self.model_file = "/root/HydraX-v2/grokkeeper_model.pkl"
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://*:5565")  # ML predictions port
        
        self.model = None
        self.last_train_time = None
        self.min_samples = 100
        
    def load_data(self):
        """Load data from unified log"""
        data = []
        
        if not os.path.exists(self.log_file):
            logger.warning(f"Log file not found: {self.log_file}")
            return pd.DataFrame()
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
        
        return pd.DataFrame(data)
    
    def prepare_features(self, df):
        """Prepare features for ML"""
        
        if df.empty:
            return None, None
        
        # Feature engineering
        features = pd.DataFrame()
        
        # Numeric features
        features['confidence'] = df['confidence'].fillna(0)
        features['shield_score'] = df['shield_score'].fillna(0)
        features['rsi'] = df['rsi'].fillna(50)
        features['volume_ratio'] = df['volume_ratio'].fillna(1.0)
        features['sl_pips'] = df['sl_pips'].fillna(10)
        features['tp_pips'] = df['tp_pips'].fillna(15)
        features['risk_reward'] = (features['tp_pips'] / features['sl_pips'].replace(0, 1))
        
        # Categorical encoding
        features['pattern_encoded'] = pd.Categorical(df['pattern'].fillna('UNKNOWN')).codes
        features['session_encoded'] = pd.Categorical(df['session'].fillna('OVERLAP')).codes
        features['direction_encoded'] = df['direction'].map({'BUY': 1, 'SELL': -1}).fillna(0)
        
        # Time features
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        features['hour'] = df['timestamp'].dt.hour.fillna(12)
        features['day_of_week'] = df['timestamp'].dt.dayofweek.fillna(0)
        
        # Target variable
        target = df['win'].fillna(False).astype(int)
        
        # Remove any infinite values
        features.replace([np.inf, -np.inf], np.nan, inplace=True)
        features.fillna(0, inplace=True)
        
        return features, target
    
    def train_model(self, force=False):
        """Train ML model on historical data"""
        
        # Check if we need to retrain
        if not force and self.last_train_time:
            if datetime.now() - self.last_train_time < timedelta(hours=1):
                logger.info("Model recently trained, skipping...")
                return False
        
        # Load data
        df = self.load_data()
        
        if len(df) < self.min_samples:
            logger.warning(f"Not enough samples for training: {len(df)} < {self.min_samples}")
            return False
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        if X is None or len(X) < self.min_samples:
            logger.warning("Not enough valid features for training")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        logger.info(f"Model trained - Train: {train_score:.2%}, Test: {test_score:.2%}")
        
        # Save model
        joblib.dump(self.model, self.model_file)
        self.last_train_time = datetime.now()
        
        # Feature importance
        importances = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"Top features:\\n{importances.head()}")
        
        return True
    
    def predict_signal(self, signal_data):
        """Predict outcome for a signal"""
        
        if self.model is None:
            # Try to load existing model
            if os.path.exists(self.model_file):
                self.model = joblib.load(self.model_file)
            else:
                logger.warning("No model available for prediction")
                return None
        
        # Prepare single signal features
        df = pd.DataFrame([signal_data])
        X, _ = self.prepare_features(df)
        
        if X is None or X.empty:
            return None
        
        # Predict
        try:
            win_probability = self.model.predict_proba(X)[0][1]
            prediction = {
                'signal_id': signal_data.get('signal_id'),
                'win_probability': float(win_probability),
                'recommended': win_probability > 0.65,
                'confidence_boost': max(0, (win_probability - 0.5) * 20),
                'ml_score': float(win_probability)
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def publish_prediction(self, prediction):
        """Publish ML prediction via ZMQ"""
        
        if prediction and self.publisher:
            msg = json.dumps(prediction)
            self.publisher.send_string(f"ML_PREDICTION {msg}")
            logger.info(f"Published prediction: {prediction['signal_id']} - {prediction['win_probability']:.2%}")
    
    def run(self):
        """Main loop"""
        
        logger.info("🤖 Grokkeeper ML starting...")
        
        # Initial training
        self.train_model(force=True)
        
        # Subscribe to signals
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect("tcp://localhost:5557")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "ELITE_")
        
        last_retrain = time.time()
        
        while True:
            try:
                # Check for new signals
                try:
                    message = subscriber.recv_string(zmq.NOBLOCK)
                    
                    if message.startswith("ELITE_"):
                        parts = message.split(' ', 1)
                        if len(parts) > 1:
                            signal_data = json.loads(parts[1])
                            
                            # Make prediction
                            prediction = self.predict_signal(signal_data)
                            
                            if prediction:
                                self.publish_prediction(prediction)
                                
                except zmq.Again:
                    pass
                
                # Periodic retraining
                if time.time() - last_retrain > 3600:  # Every hour
                    if self.train_model():
                        last_retrain = time.time()
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(1)
        
        # Cleanup
        subscriber.close()
        self.publisher.close()
        self.context.term()
        logger.info("Grokkeeper ML stopped")

if __name__ == "__main__":
    grokkeeper = GrokkeeperML()
    grokkeeper.run()
'''
    
    # Save Grokkeeper code
    with open('/root/HydraX-v2/grokkeeper_unified.py', 'w') as f:
        f.write(grokkeeper_code)
    
    os.chmod('/root/HydraX-v2/grokkeeper_unified.py', 0o755)
    print("✅ Created: /root/HydraX-v2/grokkeeper_unified.py")
    
    return grokkeeper_code

def create_test_script():
    """Create test script for London session simulation"""
    
    test_script = '''#!/usr/bin/env python3
"""
London Session Simulation Test
Generates 5-10 signals per hour with complete metrics
"""

import sys
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

import random
import time
import json
import zmq
from datetime import datetime, timedelta
import pytz

def generate_london_signal():
    """Generate realistic London session signal"""
    
    patterns = [
        ('ORDER_BLOCK_BOUNCE', 0.3),
        ('FAIR_VALUE_GAP_FILL', 0.25),
        ('LIQUIDITY_SWEEP_REVERSAL', 0.25),
        ('VCB_BREAKOUT', 0.1),
        ('SWEEP_RETURN', 0.1)
    ]
    
    pairs = [
        ('EURUSD', 1.09, 0.0001),
        ('GBPUSD', 1.27, 0.0001),
        ('USDJPY', 150.0, 0.01),
        ('EURJPY', 163.0, 0.01),
        ('GBPJPY', 190.0, 0.01),
        ('AUDUSD', 0.65, 0.0001),
        ('USDCAD', 1.36, 0.0001),
        ('XAUUSD', 2650.0, 0.1)
    ]
    
    # Select pattern based on weights
    pattern = random.choices([p[0] for p in patterns], weights=[p[1] for p in patterns])[0]
    
    # Select pair
    pair_info = random.choice(pairs)
    symbol = pair_info[0]
    base_price = pair_info[1] + random.uniform(-pair_info[2]*10, pair_info[2]*10)
    
    # Direction
    direction = random.choice(['BUY', 'SELL'])
    
    # Calculate SL and TP
    pip_size = pair_info[2]
    sl_pips = random.uniform(8, 20)
    tp_pips = sl_pips * random.uniform(1.5, 2.5)  # 1.5-2.5 RR
    
    if direction == 'BUY':
        sl_price = base_price - (sl_pips * pip_size)
        tp_price = base_price + (tp_pips * pip_size)
    else:
        sl_price = base_price + (sl_pips * pip_size)
        tp_price = base_price - (tp_pips * pip_size)
    
    # Calculate metrics
    confidence = random.gauss(82, 8)  # Mean 82%, std 8%
    confidence = max(70, min(95, confidence))
    
    rsi = random.gauss(50, 15)
    rsi = max(20, min(80, rsi))
    
    volume_ratio = random.gauss(1.2, 0.3)
    volume_ratio = max(0.5, min(2.5, volume_ratio))
    
    # Citadel score based on pattern and metrics
    citadel_base = {'ORDER_BLOCK_BOUNCE': 7, 'FAIR_VALUE_GAP_FILL': 6,
                   'LIQUIDITY_SWEEP_REVERSAL': 8, 'VCB_BREAKOUT': 5, 'SWEEP_RETURN': 6}
    citadel_score = citadel_base.get(pattern, 5) + random.uniform(-1, 2)
    citadel_score = max(0, min(10, citadel_score))
    
    # Simulate outcome (based on confidence)
    win_chance = confidence / 100 * 0.7  # 70% of confidence
    outcome = 'WIN' if random.random() < win_chance else 'LOSS'
    
    signal = {
        'signal_id': f'ELITE_GUARD_{symbol}_{int(time.time()*1000)}',
        'pattern': pattern,
        'confidence': confidence,
        'symbol': symbol,
        'direction': direction,
        'entry': base_price,
        'sl': sl_price,
        'tp': tp_price,
        'sl_pips': sl_pips,
        'tp_pips': tp_pips,
        'lot_size': round(random.uniform(0.01, 0.5), 2),
        'rsi': rsi,
        'volume_ratio': volume_ratio,
        'shield_score': citadel_score,
        'citadel_score': citadel_score,
        'session': 'LONDON',
        'timestamp': datetime.now(pytz.UTC).isoformat(),
        'executed': confidence >= 85,
        'user_id': '7176191872',
        'outcome': outcome if random.random() < 0.3 else None,  # 30% have immediate outcome
        'pips': tp_pips if outcome == 'WIN' else -sl_pips if outcome else None
    }
    
    return signal

def simulate_london_session(duration_minutes=60, signals_per_hour=7):
    """Simulate London session with realistic signal flow"""
    
    print(f"🌍 Starting London Session Simulation")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Target: {signals_per_hour} signals/hour")
    print("=" * 60)
    
    # Setup ZMQ publisher (optional)
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5566")  # Test port
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    signal_interval = 3600 / signals_per_hour
    
    stats = {
        'total': 0,
        'wins': 0,
        'losses': 0,
        'executed': 0,
        'patterns': {}
    }
    
    while time.time() < end_time:
        # Generate signal
        signal = generate_london_signal()
        
        # Log to unified tracking
        log_trade(signal)
        
        # Publish to ZMQ
        publisher.send_string(f"ELITE_GUARD_SIGNAL {json.dumps(signal)}")
        
        # Update stats
        stats['total'] += 1
        pattern = signal['pattern']
        stats['patterns'][pattern] = stats['patterns'].get(pattern, 0) + 1
        
        if signal.get('outcome') == 'WIN':
            stats['wins'] += 1
        elif signal.get('outcome') == 'LOSS':
            stats['losses'] += 1
        
        if signal.get('executed'):
            stats['executed'] += 1
        
        # Display
        status = "🔥 EXEC" if signal['executed'] else "📊 TRACK"
        outcome_str = f" → {signal.get('outcome', 'PENDING')}"
        print(f"{datetime.now().strftime('%H:%M:%S')} | {status} | {signal['symbol']:7} | "
              f"{signal['pattern'][:15]:15} | {signal['confidence']:.1f}% | "
              f"Shield: {signal['shield_score']:.1f}{outcome_str}")
        
        # Wait for next signal
        time.sleep(signal_interval + random.uniform(-5, 5))
    
    # Summary
    elapsed = (time.time() - start_time) / 60
    print("\\n" + "=" * 60)
    print("📊 SIMULATION COMPLETE")
    print(f"Duration: {elapsed:.1f} minutes")
    print(f"Total signals: {stats['total']}")
    print(f"Signals/hour: {stats['total'] / (elapsed/60):.1f}")
    print(f"Executed: {stats['executed']} ({stats['executed']/stats['total']*100:.1f}%)")
    
    if stats['wins'] + stats['losses'] > 0:
        win_rate = stats['wins'] / (stats['wins'] + stats['losses']) * 100
        print(f"Win rate: {win_rate:.1f}%")
    
    print("\\nPattern distribution:")
    for pattern, count in stats['patterns'].items():
        print(f"  {pattern}: {count} ({count/stats['total']*100:.1f}%)")
    
    print(f"\\n✅ All signals logged to: /root/HydraX-v2/logs/comprehensive_tracking.jsonl")
    
    # Cleanup
    publisher.close()
    context.term()

if __name__ == "__main__":
    # Run 10-minute test
    simulate_london_session(duration_minutes=10, signals_per_hour=8)
'''
    
    # Save test script
    with open('/root/HydraX-v2/test_london_session.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('/root/HydraX-v2/test_london_session.py', 0o755)
    print("✅ Created: /root/HydraX-v2/test_london_session.py")

def main():
    """Main execution"""
    print("🔧 FIXING UNIFIED LOGGING SYSTEM")
    print("=" * 60)
    
    # 1. Create Elite Guard patch
    print("\n1️⃣ Creating Elite Guard patch...")
    patch_elite_guard()
    
    # 2. Create Grokkeeper integration
    print("\n2️⃣ Creating Grokkeeper ML integration...")
    create_grokkeeper_reader()
    
    # 3. Create test script
    print("\n3️⃣ Creating London session test script...")
    create_test_script()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY OF FIXES")
    print("=" * 60)
    
    print("""
PROBLEMS IDENTIFIED:
1. ❌ Elite Guard still using old truth_log.jsonl (not unified log)
2. ❌ Only 3 test entries in unified log (no real signals)
3. ❌ CITADEL blocking signals (85% confidence threshold)
4. ❌ Grokkeeper using its own model, not unified data
5. ❌ No ZMQ debug logging configured

SOLUTIONS PROVIDED:
1. ✅ Elite Guard patch to use log_trade() function
2. ✅ Grokkeeper ML integration with unified log
3. ✅ Test script for London session (5-10 signals/hour)
4. ✅ Complete metrics in all signals

NEXT STEPS:
1. Apply Elite Guard patch:
   - Edit /root/HydraX-v2/elite_guard_with_citadel.py
   - Add the code from /root/HydraX-v2/elite_guard_unified_patch.txt
   
2. Restart Elite Guard:
   pm2 restart elite_guard
   
3. Start new Grokkeeper (optional):
   pm2 start /root/HydraX-v2/grokkeeper_unified.py --name grokkeeper_ml
   
4. Run test to verify:
   python3 /root/HydraX-v2/test_london_session.py
   
5. Check unified log:
   tail -f /root/HydraX-v2/logs/comprehensive_tracking.jsonl
""")
    
    # Check current PM2 status
    print("\n📊 CURRENT PM2 STATUS:")
    os.system("pm2 list | grep -E 'elite_guard|comprehensive_tracker|perf_tracker|grokkeeper' | head -4")

if __name__ == "__main__":
    main()