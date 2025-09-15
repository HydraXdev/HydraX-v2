#!/usr/bin/env python3
"""
Comprehensive Tracking Consolidation Script
Updates all active trackers to use unified logging
Archives obsolete tracking files
"""

import os
import shutil
import subprocess
import time
from datetime import datetime

def create_updated_trackers():
    """Create updated versions of all active trackers"""
    
    # 1. comprehensive_performance_tracker.py update
    comprehensive_performance_content = '''#!/usr/bin/env python3
"""
Comprehensive Performance Tracker
Uses unified logging to /root/HydraX-v2/logs/comprehensive_tracking.jsonl
"""

import zmq
import json
import time
import logging
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent directory for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensivePerformanceTracker:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.stats = defaultdict(lambda: defaultdict(int))
        self.running = False
        
    def process_signal(self, signal_data):
        """Process signal and log using unified function"""
        try:
            # Map signal data to unified format
            trade_data = {
                'signal_id': signal_data.get('signal_id'),
                'pattern': signal_data.get('pattern'),
                'confidence': signal_data.get('confidence'),
                'symbol': signal_data.get('symbol'),
                'direction': signal_data.get('direction'),
                'entry': signal_data.get('entry'),
                'sl': signal_data.get('sl'),
                'tp': signal_data.get('tp'),
                'session': signal_data.get('session'),
                'citadel_score': signal_data.get('citadel_score', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            # Use unified logging
            log_trade(trade_data)
            
            # Update stats
            self.stats['total']['count'] += 1
            self.stats['patterns'][signal_data.get('pattern', 'UNKNOWN')] += 1
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    def run(self):
        """Main tracking loop"""
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5557")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        self.running = True
        logger.info("Performance tracker running with unified logging...")
        
        while self.running:
            try:
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                if message.startswith("ELITE_"):
                    parts = message.split(' ', 1)
                    if len(parts) > 1:
                        signal_data = json.loads(parts[1])
                        self.process_signal(signal_data)
            except zmq.Again:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error: {e}")

if __name__ == "__main__":
    tracker = ComprehensivePerformanceTracker()
    tracker.run()
'''
    
    # 2. true_pattern_tracker.py update
    true_pattern_content = '''#!/usr/bin/env python3
"""
True Pattern Tracker
Uses unified logging to /root/HydraX-v2/logs/comprehensive_tracking.jsonl
"""

import zmq
import json
import time
import logging
import sys
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TruePatternTracker:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.patterns = {}
        
    def track_pattern(self, signal_data):
        """Track pattern using unified logging"""
        try:
            trade_data = {
                'signal_id': signal_data.get('signal_id'),
                'pattern': signal_data.get('pattern'),
                'confidence': signal_data.get('confidence'),
                'symbol': signal_data.get('symbol'),
                'direction': signal_data.get('direction'),
                'entry': signal_data.get('entry'),
                'sl': signal_data.get('sl'),
                'tp': signal_data.get('tp'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Use unified logging
            log_trade(trade_data)
            
            # Track pattern frequency
            pattern = signal_data.get('pattern', 'UNKNOWN')
            self.patterns[pattern] = self.patterns.get(pattern, 0) + 1
            
        except Exception as e:
            logger.error(f"Error tracking pattern: {e}")
    
    def run(self):
        """Main loop"""
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5557")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        logger.info("True pattern tracker running with unified logging...")
        
        while True:
            try:
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                if message.startswith("ELITE_"):
                    parts = message.split(' ', 1)
                    if len(parts) > 1:
                        signal_data = json.loads(parts[1])
                        self.track_pattern(signal_data)
            except zmq.Again:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error: {e}")

if __name__ == "__main__":
    tracker = TruePatternTracker()
    tracker.run()
'''
    
    # 3. live_position_monitor.py update
    live_position_content = '''#!/usr/bin/env python3
"""
Live Position Monitor
Uses unified logging to /root/HydraX-v2/logs/comprehensive_tracking.jsonl
"""

import zmq
import json
import time
import logging
import sys
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LivePositionMonitor:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = None
        self.positions = {}
        
    def monitor_position(self, position_data):
        """Monitor position using unified logging"""
        try:
            trade_data = {
                'ticket': position_data.get('ticket'),
                'symbol': position_data.get('symbol'),
                'direction': position_data.get('type', '').upper(),
                'entry': position_data.get('price_open'),
                'volume': position_data.get('volume'),
                'sl': position_data.get('sl'),
                'tp': position_data.get('tp'),
                'profit': position_data.get('profit'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Use unified logging
            log_trade(trade_data)
            
            # Track position
            ticket = position_data.get('ticket')
            if ticket:
                self.positions[ticket] = position_data
            
        except Exception as e:
            logger.error(f"Error monitoring position: {e}")
    
    def run(self):
        """Main loop"""
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5558")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        logger.info("Live position monitor running with unified logging...")
        
        while True:
            try:
                message = self.subscriber.recv_string(zmq.NOBLOCK)
                data = json.loads(message)
                if 'ticket' in data:
                    self.monitor_position(data)
            except zmq.Again:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error: {e}")

if __name__ == "__main__":
    monitor = LivePositionMonitor()
    monitor.run()
'''
    
    # 4. Simple monitor stubs for less critical monitors
    monitor_stub = '''#!/usr/bin/env python3
"""
{name} - Simplified monitor using unified logging
"""

import sys
import time
import logging
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main monitoring loop"""
    logger.info("{name} running with unified logging...")
    
    # This is a simplified stub - the actual monitoring logic
    # should be integrated based on specific requirements
    
    while True:
        try:
            # Monitor-specific logic would go here
            # When trade data is available, log it:
            # trade_data = {{...}}
            # log_trade(trade_data)
            time.sleep(60)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {{e}}")
            time.sleep(10)

if __name__ == "__main__":
    main()
'''
    
    # Write updated files
    files_to_create = [
        ('comprehensive_performance_tracker_updated.py', comprehensive_performance_content),
        ('true_pattern_tracker_updated.py', true_pattern_content),
        ('tools/live_position_monitor_updated.py', live_position_content),
        ('tools/health_monitor_updated.py', monitor_stub.format(name='Health Monitor')),
        ('persistent_handshake_monitor_updated.py', monitor_stub.format(name='Handshake Monitor')),
        ('heartbeat_monitor_updated.py', monitor_stub.format(name='Heartbeat Monitor'))
    ]
    
    for filename, content in files_to_create:
        filepath = f'/root/HydraX-v2/{filename}'
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Created: {filepath}")
    
    return True

def create_archive_script():
    """Create script to archive obsolete files"""
    
    archive_script = '''#!/bin/bash
# Archive obsolete tracking files
# Created: ''' + datetime.now().isoformat() + '''

echo "🗂️ Archiving obsolete tracking files..."

# Create archive directory
mkdir -p /root/HydraX-v2/archive_tracking_$(date +%Y%m%d)

# List of obsolete files to archive
FILES_TO_ARCHIVE=(
    "bitten_monitor.py"
    "citadel_protection_monitor.py"
    "clean_truth_writer.py"
    "convergence_tracker.py"
    "core_truth_integration.py"
    "dynamic_outcome_tracker.py"
    "elite_guard_signal_outcome.py"
    "monitor_candles.py"
    "monitor_signal_modes.py"
    "monitor_zmq_system.py"
    "mt5_instance_tracker.py"
    "network_latency_monitor.py"
    "outcome_tracker.py"
    "pattern_success_tracker.py"
    "position_tracker.py"
    "post_mortem_tracking_monitor.py"
    "production_monitor.py"
    "realtime_balance_tracker.py"
    "signal_outcome_monitor.py"
    "signal_truth_tracker.py"
    "simple_truth_tracker.py"
    "system_monitor.py"
    "trade_history_tracker.py"
    "truth_cli.py"
    "truth_dashboard_integration.py"
    "truth_log_query.py"
    "truth_position_integration.py"
    "truth_tracker.py"
    "webapp_truth_direct.py"
    "zmq_data_monitor.py"
    "zmq_market_data_truth_bridge.py"
    "zmq_trade_tracker.py"
    "zmq_truth_tracker_integration.py"
)

# Check for running processes before archiving
echo "⚠️ Checking for running processes..."
for file in "${FILES_TO_ARCHIVE[@]}"; do
    if pgrep -f "$file" > /dev/null; then
        echo "❌ WARNING: $file has running process. Skipping..."
    else
        if [ -f "/root/HydraX-v2/$file" ]; then
            mv "/root/HydraX-v2/$file" "/root/HydraX-v2/archive_tracking_$(date +%Y%m%d)/"
            echo "✅ Archived: $file"
        fi
    fi
done

echo "📊 Archive complete. Files moved to: /root/HydraX-v2/archive_tracking_$(date +%Y%m%d)/"
echo "⚠️ Remember to update any imports or dependencies in remaining files."
'''
    
    script_path = '/root/HydraX-v2/archive_obsolete_trackers.sh'
    with open(script_path, 'w') as f:
        f.write(archive_script)
    os.chmod(script_path, 0o755)
    print(f"✅ Created archive script: {script_path}")
    return script_path

def create_ml_preprocessing_script():
    """Create preprocessing script for ML"""
    
    ml_script = '''#!/usr/bin/env python3
"""
ML Preprocessing Script for Comprehensive Tracking Data
Prepares data from comprehensive_tracking.jsonl for Grokkeeper's ML models
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import sys

def load_tracking_data(filepath='/root/HydraX-v2/logs/comprehensive_tracking.jsonl'):
    """Load JSONL tracking data into DataFrame"""
    data = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return pd.DataFrame()
    
    return pd.DataFrame(data)

def preprocess_for_ml(df):
    """Preprocess data for ML models"""
    
    if df.empty:
        print("❌ No data to preprocess")
        return df
    
    # Handle missing values
    numeric_cols = ['confidence', 'entry_price', 'sl_price', 'tp_price', 
                   'lot_size', 'pips', 'rsi', 'volume', 'shield_score',
                   'risk_pct', 'balance', 'equity', 'expectancy', 'ml_score']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col].fillna(df[col].median() if not df[col].isna().all() else 0, inplace=True)
    
    # Convert categorical to numeric
    if 'direction' in df.columns:
        df['direction_encoded'] = df['direction'].map({'BUY': 1, 'SELL': -1}).fillna(0)
    
    if 'pattern' in df.columns:
        df['pattern_encoded'] = pd.Categorical(df['pattern']).codes
    
    if 'session' in df.columns:
        session_map = {'ASIAN': 0, 'LONDON': 1, 'NEWYORK': 2, 'SYDNEY': 3, 'OVERLAP': 4}
        df['session_encoded'] = df['session'].map(session_map).fillna(0)
    
    # Convert win/loss to binary
    if 'win' in df.columns:
        df['win_binary'] = df['win'].astype(float).fillna(0.5)  # 0.5 for unknown outcomes
    
    # Calculate derived features
    if 'entry_price' in df.columns and 'sl_price' in df.columns:
        df['risk_pips'] = abs(df['entry_price'] - df['sl_price']) * 10000
    
    if 'tp_price' in df.columns and 'entry_price' in df.columns:
        df['reward_pips'] = abs(df['tp_price'] - df['entry_price']) * 10000
    
    if 'risk_pips' in df.columns and 'reward_pips' in df.columns:
        df['risk_reward_ratio'] = df['reward_pips'] / df['risk_pips'].replace(0, 1)
    
    # Handle timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # Remove NaN and infinity values
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    # Select features for ML
    ml_features = [
        'confidence', 'shield_score', 'risk_reward_ratio',
        'direction_encoded', 'pattern_encoded', 'session_encoded',
        'hour', 'day_of_week', 'rsi', 'volume',
        'win_binary'  # Target variable
    ]
    
    available_features = [f for f in ml_features if f in df.columns]
    ml_df = df[available_features].copy()
    
    # Final cleanup
    ml_df.dropna(inplace=True)
    
    return ml_df

def generate_ml_report(df):
    """Generate ML-ready report"""
    
    print("📊 ML Preprocessing Report")
    print("=" * 50)
    print(f"Total records: {len(df)}")
    
    if 'win_binary' in df.columns:
        win_rate = df['win_binary'].mean()
        print(f"Win rate: {win_rate:.2%}")
    
    if 'pattern_encoded' in df.columns:
        print(f"Unique patterns: {df['pattern_encoded'].nunique()}")
    
    if 'confidence' in df.columns:
        print(f"Avg confidence: {df['confidence'].mean():.1f}")
    
    if 'shield_score' in df.columns:
        print(f"Avg shield score: {df['shield_score'].mean():.1f}")
    
    print("\\nFeature statistics:")
    print(df.describe())
    
    # Save preprocessed data
    output_file = '/root/HydraX-v2/logs/ml_preprocessed_data.csv'
    df.to_csv(output_file, index=False)
    print(f"\\n✅ Preprocessed data saved to: {output_file}")
    
    return df

def main():
    """Main preprocessing pipeline"""
    print("🤖 Starting ML preprocessing...")
    
    # Load data
    df = load_tracking_data()
    
    if df.empty:
        print("❌ No data found to preprocess")
        return
    
    print(f"✅ Loaded {len(df)} records")
    
    # Preprocess
    ml_df = preprocess_for_ml(df)
    
    # Generate report
    generate_ml_report(ml_df)
    
    print("\\n✅ ML preprocessing complete!")
    
    return ml_df

if __name__ == "__main__":
    main()
'''
    
    script_path = '/root/HydraX-v2/ml_preprocessing.py'
    with open(script_path, 'w') as f:
        f.write(ml_script)
    os.chmod(script_path, 0o755)
    print(f"✅ Created ML preprocessing script: {script_path}")
    return script_path

def create_elite_guard_update():
    """Create patch for elite_guard_with_citadel.py"""
    
    patch_content = '''# Elite Guard Unified Logging Patch
# Add this import at the top of elite_guard_with_citadel.py:
import sys
sys.path.insert(0, '/root/HydraX-v2')
from comprehensive_tracking_layer import log_trade

# Replace any logging to truth_log.jsonl with:
def log_signal_unified(self, signal_data):
    """Log signal using unified tracking"""
    trade_data = {
        'signal_id': signal_data.get('signal_id'),
        'pattern': signal_data.get('pattern'),
        'confidence': signal_data.get('confidence'),
        'symbol': signal_data.get('symbol'),
        'direction': signal_data.get('direction'),
        'entry': signal_data.get('entry'),
        'sl': signal_data.get('sl'),
        'tp': signal_data.get('tp'),
        'session': signal_data.get('session'),
        'citadel_score': signal_data.get('citadel_score', 0),
        'timestamp': datetime.now().isoformat()
    }
    log_trade(trade_data)

# Use this function instead of direct file writes
'''
    
    patch_path = '/root/HydraX-v2/elite_guard_logging_patch.txt'
    with open(patch_path, 'w') as f:
        f.write(patch_content)
    print(f"✅ Created Elite Guard patch instructions: {patch_path}")
    return patch_path

def main():
    """Main consolidation process"""
    print("🚀 Starting tracking consolidation...")
    print("=" * 60)
    
    # Create updated trackers
    print("\\n📝 Creating updated tracker files...")
    create_updated_trackers()
    
    # Create archive script
    print("\\n🗂️ Creating archive script...")
    archive_script = create_archive_script()
    
    # Create ML preprocessing script
    print("\\n🤖 Creating ML preprocessing script...")
    ml_script = create_ml_preprocessing_script()
    
    # Create elite guard patch
    print("\\n🎯 Creating Elite Guard patch...")
    patch_file = create_elite_guard_update()
    
    print("\\n" + "=" * 60)
    print("✅ CONSOLIDATION COMPLETE!")
    print("\\nNext steps:")
    print("1. Stop current tracker processes: pm2 stop all")
    print("2. Run archive script: bash " + archive_script)
    print("3. Replace tracker files with updated versions")
    print("4. Apply Elite Guard patch (see " + patch_file + ")")
    print("5. Restart processes with updated files")
    print("6. Run ML preprocessing: python3 " + ml_script)
    print("\\n📊 All logging will now go to: /root/HydraX-v2/logs/comprehensive_tracking.jsonl")

if __name__ == "__main__":
    main()