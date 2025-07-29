#!/usr/bin/env python3
"""
CITADEL ML Filter - Machine Learning prediction filter for signal quality
Uses trained model.pkl to predict win probability and block weak signals
"""

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import joblib
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CitadelMLFilter:
    """ML-based signal filtering using trained prediction model"""
    
    def __init__(self,
                 model_path: str = "/root/HydraX-v2/model.pkl",
                 citadel_state_path: str = "/root/HydraX-v2/citadel_state.json",
                 suppressed_log_path: str = "/root/HydraX-v2/logs/suppressed_signals.log"):
        
        self.model_path = Path(model_path)
        self.citadel_state_path = Path(citadel_state_path)
        self.suppressed_log_path = Path(suppressed_log_path)
        
        # Default configuration
        self.default_min_probability = 0.65  # 65% minimum win probability
        self.enable_logging = True
        
        # Model components
        self.model = None
        self.scaler = None
        self.feature_columns = []
        self.model_metadata = {}
        self.last_model_load = 0
        
        # Initialize
        self.load_model()
        self._ensure_log_directory()
        
        logger.info("CITADEL ML Filter initialized")
    
    def _ensure_log_directory(self):
        """Ensure suppressed signals log directory exists"""
        try:
            self.suppressed_log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating log directory: {e}")
    
    def load_model(self) -> bool:
        """Load trained model with automatic reloading"""
        try:
            if not self.model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                return False
            
            # Check if model file has been updated
            model_mtime = self.model_path.stat().st_mtime
            if model_mtime <= self.last_model_load:
                return True  # Model already loaded and up-to-date
            
            # Load model package
            logger.info(f"Loading ML model: {self.model_path}")
            model_package = joblib.load(self.model_path)
            
            self.model = model_package['model']
            self.scaler = model_package.get('scaler')
            self.feature_columns = model_package['feature_columns']
            self.model_metadata = model_package.get('metadata', {})
            self.last_model_load = model_mtime
            
            model_type = self.model_metadata.get('model_type', 'unknown')
            cv_score = self.model_metadata.get('cv_score', 0)
            feature_count = len(self.feature_columns)
            
            logger.info(f"✅ Model loaded: {model_type}, CV Score: {cv_score:.3f}, Features: {feature_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
            return False
    
    def get_ml_config(self) -> Dict[str, Any]:
        """Get ML filter configuration from citadel_state.json"""
        try:
            if self.citadel_state_path.exists():
                with open(self.citadel_state_path, 'r') as f:
                    state = json.load(f)
                    
                global_config = state.get('global', {})
                ml_config = global_config.get('ml_filter', {})
                
                return {
                    'enabled': ml_config.get('enabled', True),
                    'min_acceptable_probability': ml_config.get('min_acceptable_probability', self.default_min_probability),
                    'log_suppressed': ml_config.get('log_suppressed', self.enable_logging),
                    'model_override': ml_config.get('model_override', False)
                }
            else:
                return {
                    'enabled': True,
                    'min_acceptable_probability': self.default_min_probability,
                    'log_suppressed': self.enable_logging,
                    'model_override': False
                }
                
        except Exception as e:
            logger.error(f"Error reading ML config: {e}")
            return {
                'enabled': True,
                'min_acceptable_probability': self.default_min_probability,
                'log_suppressed': self.enable_logging,
                'model_override': False
            }
    
    def signal_to_features(self, signal_dict: Dict[str, Any]) -> Optional[np.ndarray]:
        """Convert signal dictionary to feature vector for prediction"""
        try:
            # Extract basic signal features
            symbol = signal_dict.get('symbol', signal_dict.get('pair', 'EURUSD')).upper()
            direction = signal_dict.get('direction', 'BUY').upper()
            
            # TCS/Confidence score
            tcs_score = float(signal_dict.get('tcs_score', 
                            signal_dict.get('confidence', 
                            signal_dict.get('score', 75))))
            
            # Price features
            entry_price = float(signal_dict.get('entry_price', 1.0))
            stop_loss = float(signal_dict.get('stop_loss', 
                            signal_dict.get('sl', entry_price * 0.999)))
            take_profit = float(signal_dict.get('take_profit', 
                              signal_dict.get('tp', entry_price * 1.002)))
            
            # Calculate derived features
            sl_distance = abs(entry_price - stop_loss)
            tp_distance = abs(take_profit - entry_price)
            risk_reward_ratio = tp_distance / sl_distance if sl_distance > 0 else 2.0
            
            # Time features
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Session detection
            session = self._get_trading_session(hour)
            
            # Spread estimation
            estimated_spread = self._estimate_spread(symbol)
            
            # Build base feature vector
            features = [
                tcs_score, hour, day_of_week, is_weekend,
                sl_distance, tp_distance, risk_reward_ratio, estimated_spread
            ]
            
            # Add symbol one-hot encoding (simplified for major pairs)
            major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD']
            for pair in major_pairs:
                features.append(1 if symbol == pair else 0)
            
            # Add direction encoding
            features.extend([1 if direction == 'BUY' else 0, 1 if direction == 'SELL' else 0])
            
            # Add session encoding
            sessions = ['asian', 'london', 'ny', 'overlap']
            for sess in sessions:
                features.append(1 if session == sess else 0)
            
            # Add price level encoding (simplified)
            if entry_price < 0.7:
                price_level = [1, 0, 0, 0, 0]  # very_low
            elif entry_price < 1.2:
                price_level = [0, 1, 0, 0, 0]  # low
            elif entry_price < 1.5:
                price_level = [0, 0, 1, 0, 0]  # medium
            elif entry_price < 150:
                price_level = [0, 0, 0, 1, 0]  # high
            else:
                price_level = [0, 0, 0, 0, 1]  # very_high
            
            features.extend(price_level)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error converting signal to features: {e}")
            return None
    
    def _get_trading_session(self, hour: int) -> str:
        """Determine trading session based on hour (UTC)"""
        if 0 <= hour < 8:
            return 'asian'
        elif 8 <= hour < 16:
            return 'london'
        elif 16 <= hour < 22:
            return 'ny'
        else:
            return 'overlap'
    
    def _estimate_spread(self, symbol: str) -> float:
        """Estimate typical spread for symbol"""
        spread_map = {
            'EURUSD': 1.5, 'GBPUSD': 2.0, 'USDJPY': 1.5, 'USDCAD': 2.5,
            'AUDUSD': 2.0, 'NZDUSD': 3.0, 'USDCHF': 2.5, 'EURGBP': 2.5,
            'EURJPY': 2.5, 'GBPJPY': 3.5, 'XAUUSD': 5.0, 'GBPNZD': 4.0,
            'GBPAUD': 4.0, 'EURAUD': 3.5, 'GBPCHF': 3.5
        }
        return spread_map.get(symbol, 3.0)
    
    def predict_win_probability(self, signal_dict: Dict[str, Any]) -> Optional[float]:
        """Predict win probability for a signal"""
        try:
            # Ensure model is loaded and up-to-date
            if not self.load_model():
                logger.warning("Model not available for prediction")
                return None
            
            # Convert signal to features
            features = self.signal_to_features(signal_dict)
            if features is None:
                return None
            
            # Scale features if scaler available
            if self.scaler is not None:
                features = self.scaler.transform([features])
            else:
                features = np.array([features])
            
            # Get prediction probability
            if hasattr(self.model, 'predict_proba'):
                prob = self.model.predict_proba(features)[0][1]  # Probability of WIN
            else:
                # Fallback for models without predict_proba
                prediction = self.model.predict(features)[0]
                prob = float(prediction)
            
            return float(prob)
            
        except Exception as e:
            logger.error(f"Error predicting win probability: {e}")
            return None
    
    def log_suppressed_signal(self, signal_dict: Dict[str, Any], win_probability: float, 
                            min_threshold: float):
        """Log suppressed signal to file"""
        try:
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'signal_id': signal_dict.get('signal_id', 'unknown'),
                'symbol': signal_dict.get('symbol', signal_dict.get('pair', 'unknown')),
                'direction': signal_dict.get('direction', 'unknown'),
                'tcs_score': signal_dict.get('tcs_score', signal_dict.get('confidence', 0)),
                'predicted_win_probability': round(win_probability, 4),
                'min_threshold': min_threshold,
                'reason': 'ml_filter_suppressed'
            }
            
            # Append to suppressed signals log
            with open(self.suppressed_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
        except Exception as e:
            logger.error(f"Error logging suppressed signal: {e}")
    
    def filter_signal(self, signal_dict: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Filter signal using ML prediction
        
        Returns:
            Tuple[bool, Dict]: (should_allow_signal, filter_info)
        """
        try:
            # Get ML filter configuration
            ml_config = self.get_ml_config()
            
            # Check if ML filter is enabled
            if not ml_config['enabled']:
                return True, {
                    'ml_filter_enabled': False,
                    'filter_result': 'disabled'
                }
            
            # Check for model override (emergency bypass)
            if ml_config['model_override']:
                return True, {
                    'ml_filter_enabled': True,
                    'filter_result': 'override_bypass'
                }
            
            # Get minimum acceptable probability
            min_probability = ml_config['min_acceptable_probability']
            
            # Predict win probability
            win_probability = self.predict_win_probability(signal_dict)
            
            if win_probability is None:
                # Model prediction failed, allow signal through
                logger.warning("ML prediction failed - allowing signal through")
                return True, {
                    'ml_filter_enabled': True,
                    'filter_result': 'prediction_failed',
                    'min_threshold': min_probability
                }
            
            # Check if signal meets minimum probability threshold
            should_allow = win_probability >= min_probability
            
            if not should_allow:
                # Log suppressed signal if enabled
                if ml_config['log_suppressed']:
                    self.log_suppressed_signal(signal_dict, win_probability, min_probability)
                
                logger.info(f"🚫 ML FILTER SUPPRESSED: {signal_dict.get('symbol', 'unknown')} "
                          f"- Probability: {win_probability:.3f} < {min_probability:.3f}")
            
            return should_allow, {
                'ml_filter_enabled': True,
                'filter_result': 'allowed' if should_allow else 'suppressed',
                'predicted_win_probability': round(win_probability, 4),
                'min_threshold': min_probability,
                'model_type': self.model_metadata.get('model_type', 'unknown'),
                'model_accuracy': self.model_metadata.get('cv_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Error in ML filter: {e}")
            # On error, allow signal through to prevent blocking legitimate signals
            return True, {
                'ml_filter_enabled': True,
                'filter_result': 'error',
                'error': str(e)
            }
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get ML filter statistics"""
        try:
            stats = {
                'model_loaded': self.model is not None,
                'model_path': str(self.model_path),
                'model_exists': self.model_path.exists(),
                'suppressed_log_path': str(self.suppressed_log_path),
                'config': self.get_ml_config()
            }
            
            if self.model is not None:
                stats.update({
                    'model_type': self.model_metadata.get('model_type', 'unknown'),
                    'model_accuracy': self.model_metadata.get('cv_score', 0),
                    'feature_count': len(self.feature_columns),
                    'training_samples': self.model_metadata.get('training_samples', 0),
                    'trained_at': self.model_metadata.get('trained_at', 'unknown')
                })
            
            # Count suppressed signals if log exists
            if self.suppressed_log_path.exists():
                try:
                    with open(self.suppressed_log_path, 'r') as f:
                        suppressed_count = sum(1 for line in f if line.strip())
                    stats['total_suppressed_signals'] = suppressed_count
                except:
                    stats['total_suppressed_signals'] = 0
            else:
                stats['total_suppressed_signals'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting filter stats: {e}")
            return {'error': str(e)}

def main():
    """Test the ML filter"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CITADEL ML Filter')
    parser.add_argument('--test', action='store_true', help='Test with sample signal')
    parser.add_argument('--stats', action='store_true', help='Show filter statistics')
    parser.add_argument('--config', action='store_true', help='Show current configuration')
    
    args = parser.parse_args()
    
    try:
        filter_engine = CitadelMLFilter()
        
        if args.stats:
            # Show statistics
            stats = filter_engine.get_filter_stats()
            print("\n🤖 CITADEL ML Filter Statistics:")
            print(f"   Model loaded: {stats.get('model_loaded', False)}")
            print(f"   Model exists: {stats.get('model_exists', False)}")
            print(f"   Model type: {stats.get('model_type', 'unknown')}")
            print(f"   Model accuracy: {stats.get('model_accuracy', 0):.3f}")
            print(f"   Total suppressed: {stats.get('total_suppressed_signals', 0)}")
            
        elif args.config:
            # Show configuration
            config = filter_engine.get_ml_config()
            print("\n⚙️ ML Filter Configuration:")
            print(f"   Enabled: {config.get('enabled', False)}")
            print(f"   Min probability: {config.get('min_acceptable_probability', 0):.3f}")
            print(f"   Log suppressed: {config.get('log_suppressed', False)}")
            print(f"   Model override: {config.get('model_override', False)}")
            
        elif args.test:
            # Test with sample signal
            test_signal = {
                'signal_id': 'TEST_EURUSD_001',
                'symbol': 'EURUSD',
                'direction': 'BUY',
                'confidence': 75.5,
                'entry_price': 1.16527,
                'stop_loss': 1.16417,
                'take_profit': 1.16747
            }
            
            print("\n🧪 Testing ML Filter with sample signal:")
            print(f"   Signal: {test_signal['symbol']} {test_signal['direction']}")
            print(f"   Confidence: {test_signal['confidence']}")
            
            should_allow, filter_info = filter_engine.filter_signal(test_signal)
            
            print(f"\n📊 Filter Result:")
            print(f"   Allowed: {should_allow}")
            print(f"   Predicted probability: {filter_info.get('predicted_win_probability', 'N/A')}")
            print(f"   Min threshold: {filter_info.get('min_threshold', 'N/A')}")
            print(f"   Filter result: {filter_info.get('filter_result', 'unknown')}")
            
        else:
            print("Use --test, --stats, or --config to interact with the ML filter")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()