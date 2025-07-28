"""
Main Script for Market Prediction Transformer

This script provides the complete pipeline for training, inference,
and deployment of the transformer-based market prediction model.
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import torch
from typing import Dict, Optional

# Import custom modules
from models.transformer_architecture import MarketTransformer, TemporalTransformer
from models.attention_mechanisms import (
    LocalAttention, DilatedAttention, CrossTimeScaleAttention,
    PatternMatchingAttention, HierarchicalAttention
)
from data.preprocessing import MarketDataPreprocessor, DataPipeline
from training.train import MarketPredictionTrainer, create_training_config
from inference.inference_engine import (
    InferenceEngine, StreamingInferenceEngine, ModelVersionManager
)
from utils.uncertainty_estimation import (
    UncertaintyEstimator, AdaptiveUncertaintyEstimator, ConfidenceScorer
)
from utils.model_versioning import (
    ModelVersionManager as VersionManager,
    AutomatedModelUpdater
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketPredictionSystem:
    """
    Complete market prediction system with all components integrated.
    """
    
    def __init__(self, config_path: str):
        """Initialize the system with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.device = torch.device(
            self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        )
        
        # Initialize components
        self.preprocessor = None
        self.model = None
        self.trainer = None
        self.inference_engine = None
        self.version_manager = None
        self.uncertainty_estimator = None
        self.confidence_scorer = None
        
        logger.info(f"Market Prediction System initialized on {self.device}")
    
    def build_model(self) -> torch.nn.Module:
        """Build the transformer model based on configuration."""
        model_config = self.config['model']
        model_type = model_config.get('type', 'standard')
        
        if model_type == 'temporal':
            model = TemporalTransformer(
                input_dim=model_config['input_dim'],
                d_model=model_config['d_model'],
                n_heads=model_config['n_heads'],
                n_layers=model_config['n_layers'],
                d_ff=model_config['d_ff'],
                max_seq_len=model_config['max_seq_len'],
                n_outputs=model_config['n_outputs'],
                dropout=model_config['dropout'],
                kernel_sizes=model_config.get('kernel_sizes', [3, 5, 7])
            )
        else:
            model = MarketTransformer(
                input_dim=model_config['input_dim'],
                d_model=model_config['d_model'],
                n_heads=model_config['n_heads'],
                n_layers=model_config['n_layers'],
                d_ff=model_config['d_ff'],
                max_seq_len=model_config['max_seq_len'],
                n_outputs=model_config['n_outputs'],
                dropout=model_config['dropout']
            )
        
        # Add custom attention mechanisms if specified
        if 'attention_types' in model_config:
            self._add_custom_attention(model, model_config['attention_types'])
        
        self.model = model.to(self.device)
        logger.info(f"Built {model_type} transformer model")
        
        return model
    
    def _add_custom_attention(self, model: torch.nn.Module, attention_types: list):
        """Add custom attention mechanisms to the model."""
        # This would require modifying the model architecture
        # For now, just log the requested attention types
        logger.info(f"Requested attention types: {attention_types}")
    
    def prepare_data(self, data_path: str) -> Dict:
        """Prepare data for training and validation."""
        # Load data
        data = pd.read_csv(data_path, parse_dates=['timestamp'], index_col='timestamp')
        logger.info(f"Loaded data with shape: {data.shape}")
        
        # Initialize preprocessor
        self.preprocessor = MarketDataPreprocessor(
            normalization_method=self.config['data']['normalization_method'],
            sequence_length=self.config['data']['sequence_length'],
            prediction_horizon=self.config['data']['prediction_horizon'],
            feature_config=self.config['data'].get('features')
        )
        
        # Create data pipeline
        pipeline = DataPipeline(
            preprocessor=self.preprocessor,
            batch_size=self.config['training']['batch_size'],
            train_split=self.config['data']['train_split'],
            val_split=self.config['data']['val_split'],
            augment_train=self.config['data'].get('augment', True)
        )
        
        # Prepare data loaders
        dataloaders = pipeline.prepare_data(
            data,
            target_column=self.config['data'].get('target_column', 'close')
        )
        
        logger.info(f"Prepared data loaders - Train: {len(dataloaders['train'])}, "
                   f"Val: {len(dataloaders['val'])}, Test: {len(dataloaders['test'])}")
        
        return dataloaders
    
    def train(self, dataloaders: Dict):
        """Train the model."""
        if self.model is None:
            self.build_model()
        
        # Initialize trainer
        self.trainer = MarketPredictionTrainer(
            model=self.model,
            device=self.device,
            config=self.config['training'],
            use_wandb=self.config.get('use_wandb', True)
        )
        
        # Train model
        self.trainer.train(
            train_loader=dataloaders['train'],
            val_loader=dataloaders['val'],
            n_epochs=self.config['training']['n_epochs'],
            patience=self.config['training']['patience']
        )
        
        # Save preprocessor
        import pickle
        preprocessor_path = Path(self.config['checkpoint_dir']) / 'preprocessor.pkl'
        with open(preprocessor_path, 'wb') as f:
            pickle.dump(self.preprocessor, f)
        
        logger.info("Training completed")
    
    def evaluate(self, test_loader: torch.utils.data.DataLoader) -> Dict:
        """Evaluate the model on test data."""
        if self.trainer is None:
            raise ValueError("Model must be trained before evaluation")
        
        # Evaluate
        test_metrics = self.trainer.validate(test_loader)
        
        logger.info(f"Test metrics: {test_metrics}")
        
        # Additional evaluation with uncertainty
        self.uncertainty_estimator = UncertaintyEstimator(
            model=self.model,
            n_samples=self.config['uncertainty']['n_mc_samples']
        )
        
        all_uncertainties = []
        for batch_data, batch_targets in test_loader:
            batch_data = batch_data.to(self.device)
            
            uncertainty_metrics = self.uncertainty_estimator.estimate_uncertainty(
                batch_data,
                method='mc_dropout'
            )
            all_uncertainties.append(uncertainty_metrics)
        
        # Aggregate uncertainty metrics
        avg_epistemic = np.mean([u.epistemic_uncertainty for u in all_uncertainties])
        avg_aleatoric = np.mean([u.aleatoric_uncertainty for u in all_uncertainties])
        avg_confidence = np.mean([u.confidence_score for u in all_uncertainties])
        
        test_metrics.update({
            'avg_epistemic_uncertainty': avg_epistemic,
            'avg_aleatoric_uncertainty': avg_aleatoric,
            'avg_confidence_score': avg_confidence
        })
        
        return test_metrics
    
    def setup_inference(self):
        """Setup inference engine for deployment."""
        model_path = Path(self.config['checkpoint_dir']) / 'best_model.pt'
        preprocessor_path = Path(self.config['checkpoint_dir']) / 'preprocessor.pkl'
        
        # Initialize inference engine
        if self.config['inference'].get('streaming', False):
            self.inference_engine = StreamingInferenceEngine(
                model_path=str(model_path),
                preprocessor_path=str(preprocessor_path),
                device=self.config['inference']['device'],
                batch_timeout=self.config['inference']['batch_timeout'],
                max_batch_size=self.config['inference']['max_batch_size'],
                enable_attention=self.config['inference'].get('enable_attention', False),
                buffer_size=self.config['inference']['streaming']['buffer_size']
            )
        else:
            self.inference_engine = InferenceEngine(
                model_path=str(model_path),
                preprocessor_path=str(preprocessor_path),
                device=self.config['inference']['device'],
                batch_timeout=self.config['inference']['batch_timeout'],
                max_batch_size=self.config['inference']['max_batch_size'],
                enable_attention=self.config['inference'].get('enable_attention', False)
            )
        
        # Start engine
        self.inference_engine.start()
        
        # Initialize confidence scorer
        self.confidence_scorer = ConfidenceScorer(
            history_window=self.config['uncertainty']['history_window']
        )
        
        logger.info("Inference engine setup completed")
    
    def setup_versioning(self):
        """Setup model versioning system."""
        self.version_manager = VersionManager(
            models_dir=self.config['versioning']['models_dir'],
            db_url=self.config['versioning']['db_url'],
            use_mlflow=self.config['versioning']['use_mlflow'],
            use_git=self.config['versioning']['use_git']
        )
        
        # Register current model if trained
        if self.model is not None and self.trainer is not None:
            version_id = self.version_manager.register_model(
                model=self.model,
                training_config=self.config,
                performance_metrics=self.trainer.training_history['val_metrics'][-1],
                preprocessor=self.preprocessor,
                notes="Initial version"
            )
            
            # Promote to production if first model
            if self.version_manager.production_version is None:
                self.version_manager.promote_to_production(version_id, force=True)
            
            logger.info(f"Registered model version: {version_id}")
    
    def predict(self, data: pd.DataFrame) -> Dict:
        """Make predictions on new data."""
        if self.inference_engine is None:
            self.setup_inference()
        
        # Make prediction
        result = self.inference_engine.predict(data)
        
        # Get market state for confidence adjustment
        market_state = self._calculate_market_state(data)
        
        # Calculate calibrated confidence
        calibrated_confidence = self.confidence_scorer.score_confidence(
            prediction=float(result.predictions.mean()),
            uncertainty=float(result.uncertainty.mean()),
            market_state=market_state
        )
        
        return {
            'predictions': result.predictions,
            'uncertainty': result.uncertainty,
            'raw_confidence': result.confidence,
            'calibrated_confidence': calibrated_confidence,
            'prediction_interval': result.prediction_interval,
            'processing_time': result.processing_time,
            'market_state': market_state
        }
    
    def _calculate_market_state(self, data: pd.DataFrame) -> Dict:
        """Calculate current market state indicators."""
        # Calculate volatility
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        
        # Calculate volume ratio
        volume_ma = data['volume'].rolling(20).mean()
        volume_ratio = data['volume'].iloc[-1] / volume_ma.iloc[-1]
        
        # Calculate trend strength
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean()
        trend_strength = (sma_20.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1]
        
        return {
            'volatility': volatility,
            'volume_ratio': volume_ratio,
            'trend_strength': trend_strength,
            'last_price': data['close'].iloc[-1]
        }
    
    def backtest(self, data: pd.DataFrame, start_date: Optional[str] = None) -> Dict:
        """Run backtest on historical data."""
        if self.inference_engine is None:
            self.setup_inference()
        
        # Filter data by start date if provided
        if start_date:
            data = data[data.index >= start_date]
        
        predictions = []
        targets = []
        confidences = []
        
        # Sliding window prediction
        window_size = self.config['data']['sequence_length']
        
        for i in range(window_size, len(data) - self.config['data']['prediction_horizon']):
            window_data = data.iloc[i-window_size:i]
            
            # Predict
            result = self.predict(window_data)
            
            # Store results
            predictions.append(result['predictions'])
            targets.append(data['close'].iloc[i:i+self.config['data']['prediction_horizon']].values)
            confidences.append(result['calibrated_confidence'])
        
        # Calculate backtest metrics
        predictions = np.array(predictions)
        targets = np.array(targets)
        confidences = np.array(confidences)
        
        mae = np.mean(np.abs(predictions - targets))
        rmse = np.sqrt(np.mean((predictions - targets) ** 2))
        
        # Direction accuracy
        pred_direction = np.sign(predictions[:, -1] - data['close'].iloc[window_size-1:-self.config['data']['prediction_horizon']].values)
        true_direction = np.sign(targets[:, -1] - data['close'].iloc[window_size-1:-self.config['data']['prediction_horizon']].values)
        direction_accuracy = np.mean(pred_direction == true_direction)
        
        # Confidence correlation
        errors = np.abs(predictions - targets).mean(axis=1)
        confidence_correlation = np.corrcoef(errors, confidences)[0, 1]
        
        return {
            'mae': mae,
            'rmse': rmse,
            'direction_accuracy': direction_accuracy,
            'confidence_correlation': confidence_correlation,
            'avg_confidence': np.mean(confidences),
            'n_predictions': len(predictions)
        }
    
    def shutdown(self):
        """Shutdown all system components."""
        if self.inference_engine is not None:
            self.inference_engine.stop()
        
        logger.info("System shutdown completed")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Market Prediction Transformer System')
    parser.add_argument('--config', type=str, required=True, help='Path to configuration file')
    parser.add_argument('--mode', type=str, choices=['train', 'evaluate', 'predict', 'backtest', 'serve'],
                       required=True, help='Operation mode')
    parser.add_argument('--data', type=str, help='Path to data file')
    parser.add_argument('--model', type=str, help='Path to model checkpoint')
    parser.add_argument('--output', type=str, help='Output path for results')
    
    args = parser.parse_args()
    
    # Initialize system
    system = MarketPredictionSystem(args.config)
    
    try:
        if args.mode == 'train':
            # Train model
            dataloaders = system.prepare_data(args.data)
            system.train(dataloaders)
            
            # Evaluate on test set
            test_metrics = system.evaluate(dataloaders['test'])
            
            # Setup versioning
            system.setup_versioning()
            
            # Save results
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(test_metrics, f, indent=2)
        
        elif args.mode == 'evaluate':
            # Load model and evaluate
            system.trainer = MarketPredictionTrainer(
                model=system.build_model(),
                device=system.device,
                config=system.config['training']
            )
            system.trainer.load_checkpoint(args.model)
            
            dataloaders = system.prepare_data(args.data)
            test_metrics = system.evaluate(dataloaders['test'])
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(test_metrics, f, indent=2)
        
        elif args.mode == 'predict':
            # Make predictions on new data
            system.setup_inference()
            
            data = pd.read_csv(args.data, parse_dates=['timestamp'], index_col='timestamp')
            predictions = system.predict(data)
            
            if args.output:
                np.save(args.output, predictions['predictions'])
                
                # Save full results
                results = {
                    'predictions': predictions['predictions'].tolist(),
                    'uncertainty': predictions['uncertainty'].tolist(),
                    'confidence': float(predictions['calibrated_confidence']),
                    'market_state': predictions['market_state']
                }
                
                with open(args.output.replace('.npy', '_full.json'), 'w') as f:
                    json.dump(results, f, indent=2)
        
        elif args.mode == 'backtest':
            # Run backtest
            data = pd.read_csv(args.data, parse_dates=['timestamp'], index_col='timestamp')
            backtest_results = system.backtest(data)
            
            logger.info(f"Backtest results: {backtest_results}")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(backtest_results, f, indent=2)
        
        elif args.mode == 'serve':
            # Start inference server
            system.setup_inference()
            system.setup_versioning()
            
            logger.info("Inference server started. Press Ctrl+C to stop.")
            
            try:
                # Keep running
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
    
    finally:
        system.shutdown()

def create_default_config() -> Dict:
    """Create default configuration file."""
    config = {
        'device': 'cuda',
        'model': {
            'type': 'temporal',  # 'standard' or 'temporal'
            'input_dim': 50,
            'd_model': 512,
            'n_heads': 8,
            'n_layers': 6,
            'd_ff': 2048,
            'max_seq_len': 100,
            'n_outputs': 5,
            'dropout': 0.1,
            'kernel_sizes': [3, 5, 7],
            'attention_types': ['local', 'dilated', 'cross_scale']
        },
        'data': {
            'sequence_length': 60,
            'prediction_horizon': 5,
            'normalization_method': 'robust',
            'train_split': 0.7,
            'val_split': 0.15,
            'target_column': 'close',
            'augment': True,
            'features': {
                'price_features': ['open', 'high', 'low', 'close', 'volume'],
                'returns': [1, 5, 10, 20],
                'technical_indicators': {
                    'momentum': ['rsi', 'stoch', 'williams_r'],
                    'trend': ['sma', 'ema', 'macd', 'adx'],
                    'volatility': ['bb_bands', 'atr'],
                    'volume': ['obv', 'cmf']
                },
                'time_features': ['hour', 'day_of_week'],
                'market_features': ['spread', 'volume_profile', 'price_levels']
            }
        },
        'training': {
            'batch_size': 32,
            'n_epochs': 100,
            'patience': 20,
            'gradient_clip': 1.0,
            'uncertainty_beta': 0.5,
            'optimizer': {
                'type': 'adamw',
                'lr': 1e-4,
                'weight_decay': 0.01
            },
            'scheduler': {
                'type': 'reduce_on_plateau',
                'factor': 0.5,
                'patience': 10,
                'min_lr': 1e-7
            }
        },
        'inference': {
            'device': 'cuda',
            'batch_timeout': 0.1,
            'max_batch_size': 32,
            'enable_attention': False,
            'streaming': {
                'enabled': True,
                'buffer_size': 100,
                'update_frequency': 1.0
            }
        },
        'uncertainty': {
            'n_mc_samples': 100,
            'confidence_levels': [0.68, 0.95, 0.99],
            'history_window': 100,
            'market_volatility_window': 20
        },
        'versioning': {
            'models_dir': 'models',
            'db_url': 'sqlite:///model_versions.db',
            'use_mlflow': True,
            'use_git': True
        },
        'checkpoint_dir': 'checkpoints',
        'use_wandb': True,
        'wandb_project': 'market-transformer'
    }
    
    return config

if __name__ == '__main__':
    # Create default config if requested
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--create-config':
        config = create_default_config()
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("Created default configuration file: config.json")
    else:
        main()