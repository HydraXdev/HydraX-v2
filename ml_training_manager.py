#!/usr/bin/env python3
"""
ML Training Manager - Manages weekly model retraining and performance monitoring
Integrates with truth tracking system to collect real signal outcomes
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import schedule
import numpy as np
import pandas as pd

from crypto_ml_scorer import CryptoMLScorer, SignalOutcome, MarketFeatures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MLTrainingManager')

class MLTrainingManager:
    """
    Manages ML model training lifecycle and performance monitoring
    Integrates with existing truth tracking systems
    """
    
    def __init__(self, 
                 truth_tracker_path: str = "/root/HydraX-v2/truth_log.jsonl",
                 ml_scorer: Optional[CryptoMLScorer] = None):
        
        self.truth_tracker_path = Path(truth_tracker_path)
        self.ml_scorer = ml_scorer or CryptoMLScorer()
        
        # Training configuration
        self.config = {
            'retraining_schedule': 'weekly',  # weekly, daily, manual
            'min_new_samples': 50,           # Minimum new samples before retraining
            'performance_window_days': 30,    # Performance evaluation window
            'backup_model_count': 5,         # Number of model backups to keep
            'alert_threshold_drop': 5.0,     # Alert if win rate drops by X%
        }
        
        # Performance tracking
        self.performance_history = []
        self.last_training_check = 0
        self.last_processed_signal = 0
        
        # Initialize
        self._setup_training_schedule()
        self._start_monitoring_threads()
        
        logger.info("🎓 ML Training Manager initialized")
    
    def _setup_training_schedule(self):
        """Setup automatic training schedule"""
        if self.config['retraining_schedule'] == 'weekly':
            # Schedule weekly training on Sunday at 2 AM
            schedule.every().sunday.at("02:00").do(self._scheduled_training)
            logger.info("📅 Scheduled weekly training: Sundays at 2:00 AM")
        elif self.config['retraining_schedule'] == 'daily':
            # Schedule daily training at 3 AM
            schedule.every().day.at("03:00").do(self._scheduled_training)
            logger.info("📅 Scheduled daily training: 3:00 AM")
    
    def _start_monitoring_threads(self):
        """Start background monitoring threads"""
        # Schedule runner thread
        schedule_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        schedule_thread.start()
        
        # Truth tracker monitor thread
        monitor_thread = threading.Thread(target=self._monitor_truth_tracker, daemon=True)
        monitor_thread.start()
        
        # Performance monitor thread
        perf_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        perf_thread.start()
        
        logger.info("🔄 Started monitoring threads")
    
    def _run_scheduler(self):
        """Run the training scheduler"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _scheduled_training(self):
        """Execute scheduled training"""
        try:
            logger.info("🎯 Starting scheduled model training")
            
            # Process new signals from truth tracker
            new_samples = self._process_truth_tracker_signals()
            
            if new_samples >= self.config['min_new_samples']:
                logger.info(f"📊 Found {new_samples} new samples, initiating retraining")
                
                # Perform model retraining
                success = self.ml_scorer.retrain_model()
                
                if success:
                    # Update performance tracking
                    self._update_performance_tracking()
                    
                    # Create model backup
                    self._backup_current_model()
                    
                    logger.info("✅ Scheduled training completed successfully")
                else:
                    logger.warning("❌ Scheduled training failed")
            else:
                logger.info(f"⏸️ Insufficient new samples ({new_samples} < {self.config['min_new_samples']}), skipping training")
                
        except Exception as e:
            logger.error(f"Error in scheduled training: {e}")
    
    def _monitor_truth_tracker(self):
        """Monitor truth tracker for new signal outcomes"""
        while True:
            try:
                # Check for new completed signals every 5 minutes
                new_samples = self._process_truth_tracker_signals()
                
                if new_samples > 0:
                    logger.info(f"📥 Processed {new_samples} new signal outcomes")
                
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Truth tracker monitoring error: {e}")
                time.sleep(600)  # Wait 10 minutes on error
    
    def _process_truth_tracker_signals(self) -> int:
        """Process new signals from truth tracker"""
        try:
            if not self.truth_tracker_path.exists():
                logger.debug("Truth tracker file not found")
                return 0
            
            new_samples = 0
            
            with open(self.truth_tracker_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Skip already processed lines
                        if line_num <= self.last_processed_signal:
                            continue
                        
                        signal_data = json.loads(line.strip())
                        
                        # Check if signal is completed
                        if not signal_data.get('completed', False):
                            continue
                        
                        # Extract required data for ML training
                        outcome_data = self._extract_ml_training_data(signal_data)
                        
                        if outcome_data:
                            # Record outcome for ML training
                            self.ml_scorer.record_signal_outcome(
                                signal_id=outcome_data['signal_id'],
                                features=outcome_data['features'],
                                outcome=outcome_data['outcome'],
                                outcome_data=outcome_data['outcome_data']
                            )
                            
                            new_samples += 1
                        
                        self.last_processed_signal = line_num
                        
                    except Exception as e:
                        logger.debug(f"Error processing truth tracker line {line_num}: {e}")
                        continue
            
            return new_samples
            
        except Exception as e:
            logger.error(f"Error reading truth tracker: {e}")
            return 0
    
    def _extract_ml_training_data(self, signal_data: Dict) -> Optional[Dict]:
        """Extract ML training data from truth tracker signal"""
        try:
            # Check if we have required data
            required_fields = ['signal_id', 'symbol', 'outcome', 'completed_at']
            if not all(field in signal_data for field in required_fields):
                return None
            
            # Determine outcome
            outcome = signal_data['outcome'] in ['WIN_TP', 'WIN']
            
            # Extract or reconstruct market features
            features = self._reconstruct_features(signal_data)
            if not features:
                return None
            
            # Prepare outcome data
            outcome_data = {
                'outcome_type': signal_data.get('outcome', 'unknown'),
                'runtime_minutes': signal_data.get('runtime_seconds', 0) // 60,
                'max_favorable_pips': signal_data.get('max_favorable_pips', 0),
                'max_adverse_pips': signal_data.get('max_adverse_pips', 0),
                'final_pips': self._calculate_final_pips(signal_data),
            }
            
            return {
                'signal_id': signal_data['signal_id'],
                'features': features,
                'outcome': outcome,
                'outcome_data': outcome_data
            }
            
        except Exception as e:
            logger.debug(f"Error extracting ML training data: {e}")
            return None
    
    def _reconstruct_features(self, signal_data: Dict) -> Optional[MarketFeatures]:
        """Reconstruct market features from signal data"""
        try:
            # If features are already stored, use them
            if 'ml_features' in signal_data:
                return MarketFeatures(**signal_data['ml_features'])
            
            # Otherwise, reconstruct basic features from available data
            symbol = signal_data.get('symbol', '')
            base_score = signal_data.get('tcs_score', signal_data.get('confidence', 65.0))
            
            # Create basic features (will be enhanced in future with more data)
            features = MarketFeatures(
                symbol=symbol,
                timestamp=signal_data.get('generated_at', time.time()),
                base_score=base_score,
                
                # Derive basic features from available data
                atr_volatility=self._estimate_volatility_from_signal(signal_data),
                volume_delta=50.0,  # Neutral default
                tf_alignment=self._estimate_tf_alignment(signal_data),
                sentiment_score=50.0,  # Neutral default
                whale_activity=0.0,  # Default
                spread_quality=self._estimate_spread_quality(signal_data),
                correlation_check=50.0,  # Neutral default
                session_bonus=self._calculate_session_bonus(signal_data),
                momentum_strength=50.0,  # Neutral default
                support_resistance=50.0,  # Neutral default
            )
            
            return features
            
        except Exception as e:
            logger.debug(f"Error reconstructing features: {e}")
            return None
    
    def _estimate_volatility_from_signal(self, signal_data: Dict) -> float:
        """Estimate volatility from signal performance"""
        try:
            max_favorable = signal_data.get('max_favorable_pips', 0)
            max_adverse = signal_data.get('max_adverse_pips', 0)
            
            # Higher pip movements indicate higher volatility
            total_movement = abs(max_favorable) + abs(max_adverse)
            
            if total_movement < 10:
                return 25.0  # Low volatility
            elif total_movement < 30:
                return 50.0  # Medium volatility
            elif total_movement < 60:
                return 75.0  # High volatility
            else:
                return 90.0  # Very high volatility
                
        except Exception:
            return 50.0  # Default
    
    def _estimate_tf_alignment(self, signal_data: Dict) -> float:
        """Estimate timeframe alignment from signal quality"""
        base_score = signal_data.get('tcs_score', signal_data.get('confidence', 65.0))
        
        # Higher base scores suggest better timeframe alignment
        if base_score >= 80:
            return 85.0
        elif base_score >= 70:
            return 70.0
        elif base_score >= 60:
            return 55.0
        else:
            return 40.0
    
    def _estimate_spread_quality(self, signal_data: Dict) -> float:
        """Estimate spread quality from signal data"""
        spread = signal_data.get('spread_at_generation', 0)
        
        if spread == 0:
            return 75.0  # Default good quality
        elif spread < 0.0001:
            return 95.0  # Excellent
        elif spread < 0.0005:
            return 80.0  # Good
        elif spread < 0.001:
            return 60.0  # Fair
        else:
            return 40.0  # Poor
    
    def _calculate_session_bonus(self, signal_data: Dict) -> float:
        """Calculate session bonus from signal generation time"""
        try:
            # Try to parse generation time
            gen_time_str = signal_data.get('generated_at', '')
            if isinstance(gen_time_str, str):
                gen_time = datetime.fromisoformat(gen_time_str.replace('Z', '+00:00'))
            else:
                gen_time = datetime.fromtimestamp(float(gen_time_str))
            
            hour = gen_time.hour
            
            # Session bonuses
            if 8 <= hour <= 12:
                return 15.0  # Asian
            elif 13 <= hour <= 17:
                return 20.0  # European
            elif 18 <= hour <= 22:
                return 25.0  # US
            else:
                return 10.0  # Off-peak
                
        except Exception:
            return 15.0  # Default
    
    def _calculate_final_pips(self, signal_data: Dict) -> float:
        """Calculate final pip result"""
        try:
            entry_price = signal_data.get('entry_price', 0)
            exit_price = signal_data.get('exit_price', entry_price)
            direction = signal_data.get('direction', 'BUY')
            
            if entry_price == 0 or exit_price == 0:
                return 0.0
            
            pip_multiplier = 10000 if 'JPY' not in signal_data.get('symbol', '') else 100
            
            if direction == 'BUY':
                pips = (exit_price - entry_price) * pip_multiplier
            else:
                pips = (entry_price - exit_price) * pip_multiplier
            
            return pips
            
        except Exception:
            return 0.0
    
    def _monitor_performance(self):
        """Monitor ML model performance"""
        while True:
            try:
                # Update performance tracking every hour
                self._update_performance_tracking()
                
                # Check for performance degradation
                self._check_performance_alerts()
                
                time.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(1800)  # 30 minutes on error
    
    def _update_performance_tracking(self):
        """Update performance tracking metrics"""
        try:
            # Get recent training data
            training_data = self.ml_scorer._load_training_data()
            
            if len(training_data) < 10:
                return
            
            # Calculate performance over different time windows
            now = time.time()
            windows = {
                '24h': 24 * 3600,
                '7d': 7 * 24 * 3600,
                '30d': 30 * 24 * 3600
            }
            
            performance = {
                'timestamp': now,
                'total_samples': len(training_data),
                'model_stats': self.ml_scorer.get_model_stats()
            }
            
            for window_name, window_seconds in windows.items():
                cutoff_time = now - window_seconds
                recent_data = [d for d in training_data if d.created_at >= cutoff_time]
                
                if recent_data:
                    wins = sum(1 for d in recent_data if d.outcome)
                    total = len(recent_data)
                    win_rate = (wins / total) * 100 if total > 0 else 0
                    
                    performance[f'{window_name}_samples'] = total
                    performance[f'{window_name}_win_rate'] = win_rate
                else:
                    performance[f'{window_name}_samples'] = 0
                    performance[f'{window_name}_win_rate'] = 0
            
            self.performance_history.append(performance)
            
            # Keep only last 30 days of performance history
            cutoff = now - (30 * 24 * 3600)
            self.performance_history = [p for p in self.performance_history if p['timestamp'] >= cutoff]
            
        except Exception as e:
            logger.error(f"Error updating performance tracking: {e}")
    
    def _check_performance_alerts(self):
        """Check for performance degradation alerts"""
        try:
            if len(self.performance_history) < 2:
                return
            
            current = self.performance_history[-1]
            previous = self.performance_history[-2]
            
            # Check for significant win rate drops
            for window in ['24h', '7d', '30d']:
                current_rate = current.get(f'{window}_win_rate', 0)
                previous_rate = previous.get(f'{window}_win_rate', 0)
                
                if previous_rate > 0 and current_rate < previous_rate - self.config['alert_threshold_drop']:
                    logger.warning(f"🚨 Performance Alert: {window} win rate dropped "
                                 f"{previous_rate:.1f}% → {current_rate:.1f}% "
                                 f"({current_rate - previous_rate:+.1f}%)")
                    
                    # Could trigger email alerts, Slack notifications, etc.
                    self._send_performance_alert(window, previous_rate, current_rate)
            
        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")
    
    def _send_performance_alert(self, window: str, old_rate: float, new_rate: float):
        """Send performance degradation alert"""
        # TODO: Implement alert mechanism (email, Slack, etc.)
        alert_msg = f"ML Model Performance Alert: {window} win rate dropped {old_rate:.1f}% → {new_rate:.1f}%"
        logger.warning(alert_msg)
    
    def _backup_current_model(self):
        """Create backup of current model"""
        try:
            # Create backups directory
            backup_dir = Path("/root/HydraX-v2/ml_models/backups")
            backup_dir.mkdir(exist_ok=True)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"crypto_ml_model_backup_{timestamp}.pkl"
            
            # Copy current model
            import shutil
            current_model_path = Path("/root/HydraX-v2/ml_models/crypto_ml_model_v1.0.0.pkl")
            if current_model_path.exists():
                shutil.copy2(current_model_path, backup_path)
                logger.info(f"📦 Model backup created: {backup_path}")
                
                # Clean up old backups
                self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            logger.error(f"Error creating model backup: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path):
        """Clean up old model backups"""
        try:
            backups = list(backup_dir.glob("crypto_ml_model_backup_*.pkl"))
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent backups
            for backup in backups[self.config['backup_model_count']:]:
                backup.unlink()
                logger.debug(f"Removed old backup: {backup.name}")
                
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status and performance"""
        latest_perf = self.performance_history[-1] if self.performance_history else {}
        
        return {
            'ml_scorer_stats': self.ml_scorer.get_model_stats(),
            'last_training_check': datetime.fromtimestamp(self.last_training_check).isoformat() if self.last_training_check else None,
            'last_processed_signal': self.last_processed_signal,
            'performance_history_length': len(self.performance_history),
            'latest_performance': latest_perf,
            'config': self.config,
            'next_scheduled_training': self._get_next_training_time()
        }
    
    def _get_next_training_time(self) -> Optional[str]:
        """Get next scheduled training time"""
        try:
            next_run = schedule.next_run()
            return next_run.isoformat() if next_run else None
        except Exception:
            return None
    
    def force_training(self) -> bool:
        """Force immediate model retraining"""
        try:
            logger.info("🔧 Forcing immediate model retraining")
            
            # Process any new signals
            new_samples = self._process_truth_tracker_signals()
            logger.info(f"Processed {new_samples} new samples before forced training")
            
            # Perform retraining
            success = self.ml_scorer.retrain_model()
            
            if success:
                self._update_performance_tracking()
                self._backup_current_model()
                logger.info("✅ Forced training completed successfully")
            else:
                logger.warning("❌ Forced training failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in forced training: {e}")
            return False

def main():
    """Test the training manager"""
    logger.info("🧪 Testing ML Training Manager")
    
    # Initialize training manager
    manager = MLTrainingManager()
    
    # Show current status
    status = manager.get_training_status()
    print("\n📊 Training Manager Status:")
    print(json.dumps(status, indent=2, default=str))
    
    # Simulate processing some truth tracker data
    print("\n🔄 Processing truth tracker data...")
    new_samples = manager._process_truth_tracker_signals()
    print(f"Processed {new_samples} new samples")
    
    # Show performance history
    if manager.performance_history:
        print("\n📈 Recent Performance:")
        for perf in manager.performance_history[-3:]:
            print(f"  {datetime.fromtimestamp(perf['timestamp'])}: "
                  f"24h: {perf.get('24h_win_rate', 0):.1f}% "
                  f"({perf.get('24h_samples', 0)} samples)")

if __name__ == "__main__":
    main()