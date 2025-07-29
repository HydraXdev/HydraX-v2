#!/usr/bin/env python3
"""
Model Training - ML prediction of signal win probability
Trains on truth_log.jsonl to predict WIN/LOSS outcomes
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignalPredictor:
    """ML model for predicting signal win probability"""
    
    def __init__(self, model_path: str = "/root/HydraX-v2/model.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = None
        self.symbol_encoder = None
        self.feature_columns = []
        self.model_metadata = {}
        
    def load_truth_data(self, truth_log_path: str) -> pd.DataFrame:
        """Load truth log data into DataFrame"""
        logger.info(f"Loading truth data from {truth_log_path}")
        
        if not os.path.exists(truth_log_path):
            raise FileNotFoundError(f"Truth log not found: {truth_log_path}")
        
        records = []
        with open(truth_log_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    records.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at line {line_num}: {e}")
                    continue
        
        if not records:
            raise ValueError("No valid records found in truth log")
        
        df = pd.DataFrame(records)
        logger.info(f"Loaded {len(df)} records from truth log")
        return df
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and engineer features from raw data"""
        logger.info("Extracting features...")
        
        # Create feature DataFrame
        features_df = pd.DataFrame()
        
        # Basic features
        features_df['symbol'] = df['symbol'].str.upper()
        features_df['direction'] = df['direction'].str.upper()
        features_df['tcs_score'] = pd.to_numeric(df['tcs_score'], errors='coerce')
        features_df['entry_price'] = pd.to_numeric(df['entry_price'], errors='coerce')
        features_df['stop_loss'] = pd.to_numeric(df['stop_loss'], errors='coerce')
        features_df['take_profit'] = pd.to_numeric(df['take_profit'], errors='coerce')
        
        # Time-based features
        created_timestamps = pd.to_numeric(df['created_at'], errors='coerce')
        features_df['hour'] = pd.to_datetime(created_timestamps, unit='s').dt.hour
        features_df['day_of_week'] = pd.to_datetime(created_timestamps, unit='s').dt.dayofweek
        features_df['is_weekend'] = features_df['day_of_week'].isin([5, 6]).astype(int)
        
        # Trading session features
        features_df['session'] = features_df['hour'].apply(self._get_trading_session)
        
        # Price-based features
        features_df['sl_distance'] = abs(features_df['entry_price'] - features_df['stop_loss'])
        features_df['tp_distance'] = abs(features_df['take_profit'] - features_df['entry_price'])
        features_df['risk_reward_ratio'] = features_df['tp_distance'] / features_df['sl_distance'].replace(0, np.nan)
        
        # Calculate spread (estimate based on pair)
        features_df['estimated_spread'] = features_df['symbol'].apply(self._estimate_spread)
        
        # Volatility proxy (price level)
        features_df['price_level'] = pd.cut(features_df['entry_price'], 
                                          bins=5, labels=['very_low', 'low', 'medium', 'high', 'very_high'])
        
        # Target variable
        features_df['target'] = (df['result'] == 'WIN').astype(int)
        
        # Drop rows with missing critical data
        initial_count = len(features_df)
        features_df = features_df.dropna(subset=['tcs_score', 'hour', 'target'])
        final_count = len(features_df)
        
        if initial_count != final_count:
            logger.info(f"Dropped {initial_count - final_count} rows with missing data")
        
        logger.info(f"Extracted features for {len(features_df)} records")
        return features_df
    
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
        return spread_map.get(symbol, 3.0)  # Default spread
    
    def prepare_features_for_training(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare features for model training"""
        logger.info("Preparing features for training...")
        
        # Select features for training
        feature_columns = [
            'tcs_score', 'hour', 'day_of_week', 'is_weekend',
            'sl_distance', 'tp_distance', 'risk_reward_ratio', 'estimated_spread'
        ]
        
        # Add categorical features
        categorical_features = ['symbol', 'direction', 'session', 'price_level']
        
        # Prepare feature matrix
        X_numeric = df[feature_columns].copy()
        
        # Handle categorical variables
        for cat_feature in categorical_features:
            if cat_feature in df.columns:
                # One-hot encode categorical features
                dummies = pd.get_dummies(df[cat_feature], prefix=cat_feature)
                X_numeric = pd.concat([X_numeric, dummies], axis=1)
        
        # Fill missing values
        X_numeric = X_numeric.fillna(X_numeric.median())
        
        # Get final feature names
        final_feature_columns = list(X_numeric.columns)
        
        # Convert to numpy arrays
        X = X_numeric.values
        y = df['target'].values
        
        logger.info(f"Prepared {X.shape[1]} features for {X.shape[0]} samples")
        return X, y, final_feature_columns
    
    def train_models(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """Train multiple models and select the best one"""
        logger.info("Training multiple models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Define models to try
        models = {
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
            'random_forest': RandomForestClassifier(random_state=42, n_estimators=100),
            'decision_tree': DecisionTreeClassifier(random_state=42, max_depth=10)
        }
        
        # Train and evaluate models
        model_results = {}
        best_score = 0
        best_model_name = None
        
        for name, model in models.items():
            logger.info(f"Training {name}...")
            
            # Use scaled data for logistic regression, raw data for tree-based models
            if name == 'logistic_regression':
                train_X, test_X = X_train_scaled, X_test_scaled
            else:
                train_X, test_X = X_train, X_test
            
            # Train model
            model.fit(train_X, y_train)
            
            # Evaluate
            train_score = model.score(train_X, y_train)
            test_score = model.score(test_X, y_test)
            
            # Cross-validation
            cv_scores = cross_val_score(model, train_X, y_train, cv=5)
            
            # Predictions for detailed metrics
            y_pred = model.predict(test_X)
            y_pred_proba = model.predict_proba(test_X)[:, 1] if hasattr(model, 'predict_proba') else None
            
            model_results[name] = {
                'model': model,
                'train_score': train_score,
                'test_score': test_score,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'auc_score': roc_auc_score(y_test, y_pred_proba) if y_pred_proba is not None else None
            }
            
            logger.info(f"{name}: Train={train_score:.3f}, Test={test_score:.3f}, CV={cv_scores.mean():.3f}±{cv_scores.std():.3f}")
            
            # Select best model based on CV score
            if cv_scores.mean() > best_score:
                best_score = cv_scores.mean()
                best_model_name = name
        
        # Select best model
        best_model_info = model_results[best_model_name]
        self.model = best_model_info['model']
        self.feature_columns = feature_names
        
        logger.info(f"Best model: {best_model_name} (CV Score: {best_score:.3f})")
        
        # Store metadata
        self.model_metadata = {
            'model_type': best_model_name,
            'feature_count': len(feature_names),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'cv_score': best_score,
            'train_score': best_model_info['train_score'],
            'test_score': best_model_info['test_score'],
            'feature_names': feature_names,
            'trained_at': datetime.now().isoformat(),
            'class_distribution': {
                'wins': int(y.sum()),
                'losses': int(len(y) - y.sum()),
                'win_rate': float(y.mean())
            }
        }
        
        return model_results
    
    def save_model(self) -> bool:
        """Save trained model and metadata"""
        try:
            # Ensure directory exists
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create model package
            model_package = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'metadata': self.model_metadata
            }
            
            # Save with joblib
            joblib.dump(model_package, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            
            # Also save metadata as JSON for easy inspection
            metadata_path = self.model_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self) -> bool:
        """Load trained model"""
        try:
            if not self.model_path.exists():
                logger.error(f"Model file not found: {self.model_path}")
                return False
            
            # Load model package
            model_package = joblib.load(self.model_path)
            
            self.model = model_package['model']
            self.scaler = model_package.get('scaler')
            self.feature_columns = model_package['feature_columns']
            self.model_metadata = model_package.get('metadata', {})
            
            logger.info(f"Model loaded from {self.model_path}")
            logger.info(f"Model type: {self.model_metadata.get('model_type', 'unknown')}")
            logger.info(f"CV Score: {self.model_metadata.get('cv_score', 'unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, signal_dict: Dict[str, Any]) -> float:
        """Predict win probability for a signal"""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        try:
            # Convert signal to feature vector
            features = self._signal_to_features(signal_dict)
            
            # Scale if scaler available
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
            logger.error(f"Error predicting signal: {e}")
            return 0.5  # Return neutral probability on error
    
    def _signal_to_features(self, signal_dict: Dict[str, Any]) -> np.ndarray:
        """Convert signal dictionary to feature vector"""
        # Extract basic features
        symbol = signal_dict.get('symbol', 'EURUSD').upper()
        direction = signal_dict.get('direction', 'BUY').upper()
        tcs_score = float(signal_dict.get('tcs_score', signal_dict.get('confidence', 75)))
        
        # Time features
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        session = self._get_trading_session(hour)
        
        # Price features
        entry_price = float(signal_dict.get('entry_price', 1.0))
        stop_loss = float(signal_dict.get('stop_loss', signal_dict.get('sl', entry_price * 0.999)))
        take_profit = float(signal_dict.get('take_profit', signal_dict.get('tp', entry_price * 1.002)))
        
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = abs(take_profit - entry_price)
        risk_reward_ratio = tp_distance / sl_distance if sl_distance > 0 else 2.0
        estimated_spread = self._estimate_spread(symbol)
        
        # Price level (simplified)
        if entry_price < 0.7:
            price_level_encoded = [1, 0, 0, 0, 0]  # very_low
        elif entry_price < 1.2:
            price_level_encoded = [0, 1, 0, 0, 0]  # low
        elif entry_price < 1.5:
            price_level_encoded = [0, 0, 1, 0, 0]  # medium
        elif entry_price < 150:
            price_level_encoded = [0, 0, 0, 1, 0]  # high
        else:
            price_level_encoded = [0, 0, 0, 0, 1]  # very_high
        
        # Build feature vector (must match training feature order)
        # This is a simplified version - in production, should match exact training features
        features = [
            tcs_score, hour, day_of_week, is_weekend,
            sl_distance, tp_distance, risk_reward_ratio, estimated_spread
        ]
        
        # Add one-hot encoded features (simplified for major pairs)
        major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD']
        for pair in major_pairs:
            features.append(1 if symbol == pair else 0)
        
        # Direction
        features.extend([1 if direction == 'BUY' else 0, 1 if direction == 'SELL' else 0])
        
        # Session
        sessions = ['asian', 'london', 'ny', 'overlap']
        for sess in sessions:
            features.append(1 if session == sess else 0)
        
        # Price level
        features.extend(price_level_encoded)
        
        return np.array(features)

def main():
    """Main training script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train signal prediction model')
    parser.add_argument('--truth-log', default='/root/HydraX-v2/truth_log.jsonl',
                       help='Path to truth log file')
    parser.add_argument('--model-path', default='/root/HydraX-v2/model.pkl',
                       help='Path to save trained model')
    parser.add_argument('--test-predict', action='store_true',
                       help='Test prediction after training')
    
    args = parser.parse_args()
    
    try:
        # Initialize predictor
        predictor = SignalPredictor(model_path=args.model_path)
        
        # Load and prepare data
        df = predictor.load_truth_data(args.truth_log)
        features_df = predictor.extract_features(df)
        
        # Check if we have enough data
        if len(features_df) < 50:
            logger.error(f"Insufficient data for training: {len(features_df)} samples (minimum: 50)")
            return
        
        # Prepare training data
        X, y, feature_names = predictor.prepare_features_for_training(features_df)
        
        # Train models
        results = predictor.train_models(X, y, feature_names)
        
        # Save model
        success = predictor.save_model()
        if not success:
            logger.error("Failed to save model")
            return
        
        # Print summary
        metadata = predictor.model_metadata
        print(f"\n🎯 Model Training Complete:")
        print(f"   Model Type: {metadata['model_type']}")
        print(f"   Training Samples: {metadata['training_samples']}")
        print(f"   Features: {metadata['feature_count']}")
        print(f"   CV Score: {metadata['cv_score']:.3f}")
        print(f"   Win Rate in Data: {metadata['class_distribution']['win_rate']:.1%}")
        
        # Test prediction if requested
        if args.test_predict:
            print(f"\n🧪 Testing Prediction:")
            test_signal = {
                'symbol': 'EURUSD',
                'direction': 'BUY',
                'confidence': 75.5,
                'entry_price': 1.16527,
                'stop_loss': 1.16417,
                'take_profit': 1.16747
            }
            
            prob = predictor.predict(test_signal)
            print(f"   Test Signal Win Probability: {prob:.1%}")
        
        logger.info("Training completed successfully")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main()