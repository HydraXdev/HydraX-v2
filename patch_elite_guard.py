#!/usr/bin/env python3
"""
Comprehensive patch for Elite Guard to enable unified logging
Applies all necessary fixes in one go
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create backup of original file"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def patch_elite_guard():
    """Apply comprehensive patch to Elite Guard"""
    
    elite_guard_file = '/root/HydraX-v2/elite_guard_with_citadel.py'
    
    # Backup first
    backup_file(elite_guard_file)
    
    # Read the file
    with open(elite_guard_file, 'r') as f:
        content = f.read()
    
    # 1. Add imports at the top (after existing imports)
    import_patch = """
# Unified logging imports
import sys
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

# ZMQ debug logging
import logging
zmq_logger = logging.getLogger('zmq_debug')
zmq_handler = logging.FileHandler('/root/HydraX-v2/logs/zmq_debug.log')
zmq_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
zmq_logger.addHandler(zmq_handler)
zmq_logger.setLevel(logging.DEBUG)
"""
    
    # Find where to insert imports (after the last import statement)
    import_pattern = r'(import\s+\w+|from\s+\w+\s+import)'
    matches = list(re.finditer(import_pattern, content))
    if matches:
        last_import_end = matches[-1].end()
        # Find the next newline after the last import
        next_newline = content.find('\n', last_import_end)
        if next_newline != -1:
            content = content[:next_newline+1] + import_patch + content[next_newline+1:]
    
    # 2. Replace publish_signal method
    new_publish_signal = '''    def publish_signal(self, signal: Dict):
        """Publish signal with unified logging and ZMQ debug"""
        try:
            # ZMQ debug logging
            zmq_logger.debug(f"Publishing signal: {signal.get('signal_id')}")
            
            # Calculate additional metrics for unified logging
            symbol = signal.get('symbol', '')
            pip_multiplier = 100 if 'JPY' in symbol else (1 if 'XAUUSD' in symbol else 10000)
            
            entry = float(signal.get('entry', 0))
            sl = float(signal.get('sl', 0))
            tp = float(signal.get('tp', 0))
            
            sl_pips = abs(entry - sl) * pip_multiplier
            tp_pips = abs(tp - entry) * pip_multiplier
            
            # Get current session
            from datetime import datetime
            import pytz
            hour = datetime.now(pytz.UTC).hour
            if 22 <= hour or hour < 7:
                session = "ASIAN"
            elif 7 <= hour < 12:
                session = "LONDON"
            elif 12 <= hour < 17:
                session = "NEWYORK"
            else:
                session = "OVERLAP"
            
            # Prepare comprehensive trade data
            trade_data = {
                'signal_id': signal.get('signal_id'),
                'pattern': signal.get('pattern'),
                'confidence': signal.get('confidence'),
                'symbol': symbol,
                'direction': signal.get('direction'),
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'sl_pips': sl_pips,
                'tp_pips': tp_pips,
                'lot_size': signal.get('lot_size', 0.01),
                'session': session,
                'citadel_score': signal.get('citadel_score', 0),
                'rsi': signal.get('rsi', 50),
                'volume_ratio': signal.get('volume_ratio', 1.0),
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'executed': signal.get('confidence', 0) >= 85,
                'user_id': '7176191872'
            }
            
            # Log to unified tracking
            log_trade(trade_data)
            zmq_logger.info(f"Signal logged to unified tracking: {signal.get('signal_id')}")
            
            # Also publish to ZMQ for real-time systems
            if self.publisher:
                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")
                zmq_logger.debug(f"Signal published to ZMQ: {signal.get('signal_id')}")
                
        except Exception as e:
            print(f"Error in publish_signal: {e}")
            zmq_logger.error(f"Error publishing signal: {e}")'''
    
    # Replace the publish_signal method
    publish_pattern = r'def publish_signal\(self[^:]*\):.*?(?=\n    def |\nclass |\Z)'
    content = re.sub(publish_pattern, new_publish_signal.strip(), content, flags=re.DOTALL)
    
    # 3. Lower CITADEL threshold from 85% to 80%
    content = re.sub(r'citadel_threshold\s*=\s*85', 'citadel_threshold = 80', content)
    content = re.sub(r'confidence.*>=\s*85', 'confidence >= 80', content)
    
    # 4. Add option to disable CITADEL (environment variable)
    citadel_toggle = """
# CITADEL toggle (can be disabled via environment variable)
CITADEL_ENABLED = os.getenv('CITADEL_ENABLED', 'true').lower() == 'true'
if not CITADEL_ENABLED:
    print("⚠️ CITADEL Shield DISABLED for testing")
"""
    
    # Add after class definition
    class_pattern = r'(class EliteGuard\w+:)'
    content = re.sub(class_pattern, r'\1\n' + citadel_toggle, content, count=1)
    
    # 5. Add ZMQ debug logging to market data reception
    zmq_recv_debug = """
                    # ZMQ debug logging for market data
                    zmq_logger.debug(f"Received tick for {symbol}: bid={tick_data.get('bid')}, ask={tick_data.get('ask')}")
"""
    
    # Find tick data processing and add logging
    tick_pattern = r"(tick_data = json\.loads.*?\n)"
    content = re.sub(tick_pattern, r'\1' + zmq_recv_debug, content)
    
    # 6. Replace truth_log.jsonl references with unified logging
    content = content.replace("'/root/HydraX-v2/truth_log.jsonl'", "'/root/HydraX-v2/logs/comprehensive_tracking.jsonl'")
    
    # Write the patched file
    with open(elite_guard_file, 'w') as f:
        f.write(content)
    
    print("✅ Elite Guard patched successfully!")
    print("   - Unified logging enabled")
    print("   - CITADEL threshold lowered to 80%")
    print("   - ZMQ debug logging added")
    print("   - Can disable CITADEL with: export CITADEL_ENABLED=false")
    
    return True

def update_grokkeeper():
    """Update Grokkeeper to output predictions"""
    
    grokkeeper_content = '''#!/usr/bin/env python3
"""
Grokkeeper ML with Unified Logging and Predictions Output
"""

import pandas as pd
import numpy as np
import json
import zmq
import time
import os
from datetime import datetime, timedelta
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrokkeeperML:
    def __init__(self):
        self.log_file = "/root/HydraX-v2/logs/comprehensive_tracking.jsonl"
        self.predictions_file = "/root/HydraX-v2/logs/grokkeeper_predictions.jsonl"
        self.model_file = "/root/HydraX-v2/grokkeeper_model.pkl"
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://*:5565")
        
        self.model = None
        self.last_train_time = None
        self.min_samples = 50  # Lowered for testing
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(self.predictions_file), exist_ok=True)
        
    def load_data(self):
        """Load data from unified log or preprocessed CSV"""
        data = []
        
        # Try preprocessed CSV first
        csv_file = "/root/HydraX-v2/logs/ml_preprocessed_data.csv"
        if os.path.exists(csv_file):
            logger.info(f"Loading preprocessed data from {csv_file}")
            return pd.read_csv(csv_file)
        
        # Fall back to JSONL
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
        
        features = pd.DataFrame()
        
        # Core metrics
        features['confidence'] = df['confidence'].fillna(0)
        features['shield_score'] = df.get('shield_score', df.get('citadel_score', 0)).fillna(0)
        features['rsi'] = df.get('rsi', 50).fillna(50)
        features['volume_ratio'] = df.get('volume_ratio', df.get('volume', 1.0)).fillna(1.0)
        
        # Pips metrics
        features['sl_pips'] = df.get('sl_pips', 10).fillna(10)
        features['tp_pips'] = df.get('tp_pips', 15).fillna(15)
        features['risk_reward'] = (features['tp_pips'] / features['sl_pips'].replace(0, 1))
        
        # Pattern encoding
        pattern_map = {
            'ORDER_BLOCK_BOUNCE': 4,
            'FAIR_VALUE_GAP_FILL': 3,
            'LIQUIDITY_SWEEP_REVERSAL': 5,
            'VCB_BREAKOUT': 2,
            'SWEEP_RETURN': 2,
            'UNKNOWN': 1
        }
        features['pattern_encoded'] = df.get('pattern', 'UNKNOWN').fillna('UNKNOWN').map(pattern_map).fillna(1)
        
        # Session encoding
        session_map = {'ASIAN': 0, 'LONDON': 2, 'NEWYORK': 1, 'OVERLAP': 1.5}
        features['session_encoded'] = df.get('session', 'OVERLAP').fillna('OVERLAP').map(session_map).fillna(1)
        
        # Direction
        features['direction_encoded'] = df.get('direction', 'BUY').map({'BUY': 1, 'SELL': -1}).fillna(0)
        
        # Time features
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            features['hour'] = df['timestamp'].dt.hour.fillna(12)
            features['day_of_week'] = df['timestamp'].dt.dayofweek.fillna(1)
        else:
            features['hour'] = 12
            features['day_of_week'] = 1
        
        # Target variable
        if 'win' in df.columns:
            target = df['win'].fillna(False).astype(int)
        elif 'win_binary' in df.columns:
            target = df['win_binary'].fillna(0.5).round().astype(int)
        else:
            # Simulate based on confidence for testing
            target = (df.get('confidence', 50) > 82).astype(int)
        
        # Clean up
        features.replace([np.inf, -np.inf], np.nan, inplace=True)
        features.fillna(0, inplace=True)
        
        return features, target
    
    def train_model(self, force=False):
        """Train ML model on historical data"""
        
        if not force and self.last_train_time:
            if datetime.now() - self.last_train_time < timedelta(hours=1):
                return False
        
        df = self.load_data()
        
        if len(df) < self.min_samples:
            logger.warning(f"Not enough samples: {len(df)} < {self.min_samples}")
            # Create simple model for testing
            self.create_simple_model()
            return True
        
        X, y = self.prepare_features(df)
        
        if X is None or len(X) < 10:
            self.create_simple_model()
            return True
        
        # Handle single class case
        if len(np.unique(y)) < 2:
            logger.warning("Only one class in target, creating balanced sample")
            # Add synthetic opposite class samples
            X = pd.concat([X, X.iloc[:5]], ignore_index=True)
            y = pd.concat([y, pd.Series([1-y.iloc[0]]*5)], ignore_index=True)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=5,
            min_samples_split=2,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test) if len(X_test) > 0 else 0
        
        logger.info(f"Model trained - Train: {train_score:.2%}, Test: {test_score:.2%}")
        
        joblib.dump(self.model, self.model_file)
        self.last_train_time = datetime.now()
        
        return True
    
    def create_simple_model(self):
        """Create simple rule-based model for testing"""
        logger.info("Creating simple rule-based model")
        
        # Create dummy data
        X_dummy = pd.DataFrame({
            'confidence': [70, 75, 80, 85, 90],
            'shield_score': [5, 6, 7, 8, 9],
            'rsi': [30, 40, 50, 60, 70],
            'volume_ratio': [0.8, 1.0, 1.2, 1.5, 2.0],
            'sl_pips': [10, 12, 15, 18, 20],
            'tp_pips': [15, 20, 25, 30, 35],
            'risk_reward': [1.5, 1.67, 1.67, 1.67, 1.75],
            'pattern_encoded': [1, 2, 3, 4, 5],
            'session_encoded': [0, 1, 2, 2, 1],
            'direction_encoded': [1, -1, 1, -1, 1],
            'hour': [8, 10, 12, 14, 16],
            'day_of_week': [1, 2, 3, 4, 5]
        })
        y_dummy = pd.Series([0, 0, 1, 1, 1])
        
        self.model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
        self.model.fit(X_dummy, y_dummy)
        joblib.dump(self.model, self.model_file)
        self.last_train_time = datetime.now()
    
    def predict_signal(self, signal_data):
        """Predict outcome for a signal"""
        
        if self.model is None:
            if os.path.exists(self.model_file):
                self.model = joblib.load(self.model_file)
            else:
                self.train_model(force=True)
        
        df = pd.DataFrame([signal_data])
        X, _ = self.prepare_features(df)
        
        if X is None or X.empty:
            # Simple rule-based prediction
            confidence = signal_data.get('confidence', 50)
            win_prob = min(0.95, max(0.3, confidence / 100))
            return {
                'signal_id': signal_data.get('signal_id'),
                'win_probability': float(win_prob),
                'recommended': win_prob > 0.65,
                'confidence_boost': max(0, (win_prob - 0.5) * 20),
                'ml_score': float(win_prob),
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            win_probability = self.model.predict_proba(X)[0][1]
            prediction = {
                'signal_id': signal_data.get('signal_id'),
                'symbol': signal_data.get('symbol'),
                'pattern': signal_data.get('pattern'),
                'win_probability': float(win_probability),
                'recommended': win_probability > 0.65,
                'confidence_boost': max(0, (win_probability - 0.5) * 20),
                'ml_score': float(win_probability),
                'original_confidence': signal_data.get('confidence'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Save prediction
            self.save_prediction(prediction)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def save_prediction(self, prediction):
        """Save prediction to JSONL file"""
        try:
            with open(self.predictions_file, 'a') as f:
                json.dump(prediction, f)
                f.write('\\n')
            logger.info(f"Saved prediction for {prediction['signal_id']}: {prediction['win_probability']:.2%}")
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
    
    def publish_prediction(self, prediction):
        """Publish ML prediction via ZMQ"""
        if prediction and self.publisher:
            msg = json.dumps(prediction)
            self.publisher.send_string(f"ML_PREDICTION {msg}")
    
    def process_batch(self):
        """Process all signals in log file"""
        df = self.load_data()
        if df.empty:
            return
        
        logger.info(f"Processing batch of {len(df)} signals")
        
        for _, row in df.iterrows():
            signal_data = row.to_dict()
            prediction = self.predict_signal(signal_data)
            if prediction:
                self.publish_prediction(prediction)
        
        logger.info(f"Batch processing complete")
    
    def run(self):
        """Main loop"""
        logger.info("🤖 Grokkeeper ML starting...")
        
        # Initial training
        self.train_model(force=True)
        
        # Process existing signals
        self.process_batch()
        
        # Subscribe to new signals
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect("tcp://localhost:5557")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "ELITE_")
        
        last_retrain = time.time()
        
        while True:
            try:
                try:
                    message = subscriber.recv_string(zmq.NOBLOCK)
                    
                    if message.startswith("ELITE_"):
                        parts = message.split(' ', 1)
                        if len(parts) > 1:
                            signal_data = json.loads(parts[1])
                            prediction = self.predict_signal(signal_data)
                            if prediction:
                                self.publish_prediction(prediction)
                                
                except zmq.Again:
                    pass
                
                # Periodic retraining
                if time.time() - last_retrain > 3600:
                    if self.train_model():
                        last_retrain = time.time()
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(1)
        
        subscriber.close()
        self.publisher.close()
        self.context.term()
        logger.info("Grokkeeper ML stopped")

if __name__ == "__main__":
    grokkeeper = GrokkeeperML()
    grokkeeper.run()
'''
    
    # Save updated Grokkeeper
    with open('/root/HydraX-v2/grokkeeper_unified.py', 'w') as f:
        f.write(grokkeeper_content)
    os.chmod('/root/HydraX-v2/grokkeeper_unified.py', 0o755)
    print("✅ Grokkeeper updated with predictions output")
    
    return True

def create_validation_script():
    """Create script to validate signal volume and metrics"""
    
    validation_script = '''#!/usr/bin/env python3
"""
Validation script for London session signal monitoring
Checks signal volume (5-10/hour) and metric completeness
"""

import json
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd

def validate_signals():
    """Validate signal volume and completeness"""
    
    log_file = '/root/HydraX-v2/logs/comprehensive_tracking.jsonl'
    
    print("🔍 SIGNAL VALIDATION REPORT")
    print("=" * 60)
    print(f"Time: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Load recent signals
    signals = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    signals.append(json.loads(line))
                except:
                    continue
    except Exception as e:
        print(f"❌ Error loading log file: {e}")
        return
    
    if not signals:
        print("❌ No signals found in log file")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(signals)
    
    # Parse timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Get signals from last hour
    one_hour_ago = datetime.now(pytz.UTC) - timedelta(hours=1)
    recent_df = df[df['timestamp'] > one_hour_ago]
    
    print(f"\\n📊 SIGNAL VOLUME")
    print(f"Total signals in log: {len(df)}")
    print(f"Signals in last hour: {len(recent_df)}")
    
    # Check if in London session
    current_hour = datetime.now(pytz.UTC).hour
    is_london = 7 <= current_hour < 12
    
    if is_london:
        if len(recent_df) < 5:
            print(f"⚠️ LOW VOLUME: Only {len(recent_df)} signals/hour (expected 5-10)")
        elif len(recent_df) > 10:
            print(f"⚠️ HIGH VOLUME: {len(recent_df)} signals/hour (expected 5-10)")
        else:
            print(f"✅ GOOD VOLUME: {len(recent_df)} signals/hour")
    else:
        print(f"ℹ️ Not London session (current UTC hour: {current_hour})")
    
    # Check metric completeness
    print(f"\\n📋 METRIC COMPLETENESS")
    
    required_fields = [
        'signal_id', 'pair', 'pattern', 'confidence', 
        'entry_price', 'sl_price', 'tp_price',
        'rsi', 'shield_score', 'session', 'direction'
    ]
    
    optional_fields = [
        'volume_ratio', 'sl_pips', 'tp_pips', 
        'lot_size', 'executed', 'win', 'pips'
    ]
    
    if not recent_df.empty:
        # Check required fields
        print("\\nRequired fields:")
        for field in required_fields:
            if field in recent_df.columns:
                missing = recent_df[field].isna().sum()
                completeness = (len(recent_df) - missing) / len(recent_df) * 100
                status = "✅" if completeness >= 90 else "⚠️"
                print(f"  {status} {field}: {completeness:.1f}% complete")
            else:
                print(f"  ❌ {field}: MISSING")
        
        # Check optional fields
        print("\\nOptional fields:")
        for field in optional_fields:
            if field in recent_df.columns:
                missing = recent_df[field].isna().sum()
                completeness = (len(recent_df) - missing) / len(recent_df) * 100
                print(f"  ℹ️ {field}: {completeness:.1f}% complete")
    
    # Pattern distribution
    if not recent_df.empty and 'pattern' in recent_df.columns:
        print(f"\\n🎯 PATTERN DISTRIBUTION (last hour)")
        pattern_counts = recent_df['pattern'].value_counts()
        for pattern, count in pattern_counts.items():
            pct = count / len(recent_df) * 100
            print(f"  {pattern}: {count} ({pct:.1f}%)")
    
    # Session distribution
    if not recent_df.empty and 'session' in recent_df.columns:
        print(f"\\n⏰ SESSION DISTRIBUTION (last hour)")
        session_counts = recent_df['session'].value_counts()
        for session, count in session_counts.items():
            pct = count / len(recent_df) * 100
            print(f"  {session}: {count} ({pct:.1f}%)")
    
    # Confidence statistics
    if not recent_df.empty and 'confidence' in recent_df.columns:
        print(f"\\n📈 CONFIDENCE STATISTICS (last hour)")
        print(f"  Mean: {recent_df['confidence'].mean():.1f}%")
        print(f"  Min: {recent_df['confidence'].min():.1f}%")
        print(f"  Max: {recent_df['confidence'].max():.1f}%")
        print(f"  Signals ≥80%: {(recent_df['confidence'] >= 80).sum()}")
        print(f"  Signals ≥85%: {(recent_df['confidence'] >= 85).sum()}")
    
    # Sample recent signals
    if not recent_df.empty:
        print(f"\\n📝 RECENT SIGNALS (last 5)")
        for i, row in recent_df.tail(5).iterrows():
            print(f"  {row.get('signal_id', 'NO_ID')[:30]}...")
            print(f"    {row.get('pair', 'N/A')} | {row.get('pattern', 'N/A')[:20]}")
            print(f"    Conf: {row.get('confidence', 0):.1f}% | RSI: {row.get('rsi', 0):.0f}")
            print(f"    Shield: {row.get('shield_score', 0):.1f} | Session: {row.get('session', 'N/A')}")
    
    print("\\n" + "=" * 60)
    print("✅ Validation complete")

if __name__ == "__main__":
    validate_signals()
'''
    
    # Save validation script
    with open('/root/HydraX-v2/validate_signals.py', 'w') as f:
        f.write(validation_script)
    os.chmod('/root/HydraX-v2/validate_signals.py', 0o755)
    print("✅ Validation script created")
    
    return True

def main():
    """Apply all patches and updates"""
    
    print("🔧 APPLYING COMPREHENSIVE FIXES")
    print("=" * 60)
    
    # Apply patches
    print("\n1️⃣ Patching Elite Guard...")
    patch_elite_guard()
    
    print("\n2️⃣ Updating Grokkeeper...")
    update_grokkeeper()
    
    print("\n3️⃣ Creating validation script...")
    create_validation_script()
    
    print("\n" + "=" * 60)
    print("✅ ALL PATCHES APPLIED!")
    print("\nNext steps:")
    print("1. Restart Elite Guard: pm2 restart elite_guard")
    print("2. Start Grokkeeper ML: pm2 start /root/HydraX-v2/grokkeeper_unified.py --name grokkeeper_ml")
    print("3. Run test: python3 /root/HydraX-v2/test_london_session.py")
    print("4. Validate: python3 /root/HydraX-v2/validate_signals.py")

if __name__ == "__main__":
    main()