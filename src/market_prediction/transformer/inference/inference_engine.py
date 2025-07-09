"""
Real-time Inference Engine for Market Prediction

This module implements an efficient inference engine for real-time market predictions
with uncertainty estimation and confidence scoring.
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from collections import deque
import threading
import queue
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Container for prediction results."""
    timestamp: datetime
    predictions: np.ndarray
    uncertainty: np.ndarray
    confidence: float
    attention_weights: Optional[np.ndarray] = None
    processing_time: float = 0.0
    metadata: Dict = None


class RealTimeBuffer:
    """
    Circular buffer for real-time data streaming.
    Maintains a sliding window of market data.
    """
    
    def __init__(self, window_size: int, n_features: int):
        self.window_size = window_size
        self.n_features = n_features
        self.buffer = deque(maxlen=window_size)
        self.lock = threading.Lock()
    
    def append(self, data: np.ndarray):
        """Add new data point to buffer."""
        with self.lock:
            if len(data.shape) == 1:
                data = data.reshape(1, -1)
            self.buffer.extend(data)
    
    def get_window(self) -> Optional[np.ndarray]:
        """Get current window of data."""
        with self.lock:
            if len(self.buffer) < self.window_size:
                return None
            return np.array(self.buffer)
    
    def clear(self):
        """Clear the buffer."""
        with self.lock:
            self.buffer.clear()


class InferenceEngine:
    """
    High-performance inference engine for real-time market predictions.
    
    Features:
    - Batch inference for efficiency
    - Real-time data streaming
    - Uncertainty quantification
    - Performance monitoring
    - Model versioning
    """
    
    def __init__(
        self,
        model_path: str,
        preprocessor_path: str,
        device: str = 'cuda',
        batch_timeout: float = 0.1,
        max_batch_size: int = 32,
        enable_attention: bool = False
    ):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.batch_timeout = batch_timeout
        self.max_batch_size = max_batch_size
        self.enable_attention = enable_attention
        
        # Load model and preprocessor
        self.model = self._load_model(model_path)
        self.preprocessor = self._load_preprocessor(preprocessor_path)
        
        # Inference state
        self.is_running = False
        self.inference_thread = None
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Performance monitoring
        self.performance_stats = {
            'total_predictions': 0,
            'total_time': 0.0,
            'avg_batch_size': 0.0,
            'avg_processing_time': 0.0
        }
        
        # Model metadata
        self.model_metadata = self._extract_model_metadata(model_path)
        
        logger.info(f"Inference engine initialized on {self.device}")
    
    def _load_model(self, model_path: str) -> nn.Module:
        """Load trained model from checkpoint."""
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Import model architecture
        from ..models.transformer_architecture import MarketTransformer, TemporalTransformer
        
        # Determine model type from config
        config = checkpoint['config']['model']
        if 'temporal' in model_path.lower():
            model = TemporalTransformer(**config)
        else:
            model = MarketTransformer(**config)
        
        # Load weights
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()
        
        # Enable TorchScript for faster inference
        try:
            model = torch.jit.script(model)
            logger.info("Model successfully converted to TorchScript")
        except:
            logger.warning("Failed to convert to TorchScript, using regular model")
        
        return model
    
    def _load_preprocessor(self, preprocessor_path: str) -> object:
        """Load preprocessor from file."""
        import pickle
        with open(preprocessor_path, 'rb') as f:
            return pickle.load(f)
    
    def _extract_model_metadata(self, model_path: str) -> Dict:
        """Extract metadata from model checkpoint."""
        checkpoint = torch.load(model_path, map_location='cpu')
        return {
            'version': checkpoint.get('version', '1.0'),
            'trained_epochs': checkpoint.get('epoch', 0),
            'best_val_loss': checkpoint.get('best_val_loss', None),
            'training_date': checkpoint.get('training_date', None),
            'config': checkpoint.get('config', {})
        }
    
    def start(self):
        """Start the inference engine."""
        if self.is_running:
            logger.warning("Inference engine is already running")
            return
        
        self.is_running = True
        self.inference_thread = threading.Thread(target=self._inference_loop)
        self.inference_thread.start()
        logger.info("Inference engine started")
    
    def stop(self):
        """Stop the inference engine."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.inference_thread:
            self.inference_thread.join()
        logger.info("Inference engine stopped")
    
    def _inference_loop(self):
        """Main inference loop for batch processing."""
        batch_data = []
        batch_metadata = []
        last_batch_time = time.time()
        
        while self.is_running:
            try:
                # Try to get data from queue
                timeout = max(0.001, self.batch_timeout - (time.time() - last_batch_time))
                data, metadata = self.input_queue.get(timeout=timeout)
                
                batch_data.append(data)
                batch_metadata.append(metadata)
                
                # Check if batch is ready
                current_time = time.time()
                batch_ready = (
                    len(batch_data) >= self.max_batch_size or
                    (current_time - last_batch_time) >= self.batch_timeout
                )
                
                if batch_ready and batch_data:
                    # Process batch
                    results = self._process_batch(batch_data, batch_metadata)
                    
                    # Send results
                    for result in results:
                        self.output_queue.put(result)
                    
                    # Reset batch
                    batch_data = []
                    batch_metadata = []
                    last_batch_time = current_time
                    
            except queue.Empty:
                # Process any remaining data
                if batch_data:
                    results = self._process_batch(batch_data, batch_metadata)
                    for result in results:
                        self.output_queue.put(result)
                    batch_data = []
                    batch_metadata = []
                    last_batch_time = time.time()
    
    def _process_batch(
        self, 
        batch_data: List[np.ndarray],
        batch_metadata: List[Dict]
    ) -> List[PredictionResult]:
        """Process a batch of data."""
        start_time = time.time()
        
        try:
            # Stack batch data
            batch_tensor = torch.FloatTensor(np.stack(batch_data)).to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(
                    batch_tensor,
                    return_attention=self.enable_attention
                )
            
            # Convert outputs to numpy
            predictions = outputs['predictions'].cpu().numpy()
            uncertainty = outputs['uncertainty'].cpu().numpy()
            confidence = outputs['confidence'].cpu().numpy()
            
            attention_weights = None
            if self.enable_attention and 'attention_weights' in outputs:
                # Average attention weights across layers and heads
                attention_weights = torch.stack(outputs['attention_weights']).mean(dim=[0, 2]).cpu().numpy()
            
            # Create results
            results = []
            processing_time = (time.time() - start_time) / len(batch_data)
            
            for i in range(len(batch_data)):
                result = PredictionResult(
                    timestamp=datetime.now(),
                    predictions=predictions[i],
                    uncertainty=uncertainty[i],
                    confidence=float(confidence[i]),
                    attention_weights=attention_weights[i] if attention_weights is not None else None,
                    processing_time=processing_time,
                    metadata=batch_metadata[i]
                )
                results.append(result)
            
            # Update performance stats
            self._update_performance_stats(len(batch_data), time.time() - start_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            # Return empty results for failed batch
            return [
                PredictionResult(
                    timestamp=datetime.now(),
                    predictions=np.array([np.nan]),
                    uncertainty=np.array([np.nan]),
                    confidence=0.0,
                    processing_time=0.0,
                    metadata={'error': str(e)}
                )
                for _ in range(len(batch_data))
            ]
    
    def _update_performance_stats(self, batch_size: int, processing_time: float):
        """Update performance statistics."""
        self.performance_stats['total_predictions'] += batch_size
        self.performance_stats['total_time'] += processing_time
        
        # Update running averages
        n = self.performance_stats['total_predictions']
        self.performance_stats['avg_batch_size'] = (
            (self.performance_stats['avg_batch_size'] * (n - batch_size) + batch_size) / n
        )
        self.performance_stats['avg_processing_time'] = (
            self.performance_stats['total_time'] / n
        )
    
    def predict(
        self, 
        data: Union[np.ndarray, pd.DataFrame],
        metadata: Optional[Dict] = None,
        timeout: float = 5.0
    ) -> PredictionResult:
        """
        Make a single prediction.
        
        Args:
            data: Input data (raw or preprocessed)
            metadata: Optional metadata
            timeout: Maximum wait time for result
            
        Returns:
            PredictionResult object
        """
        if not self.is_running:
            raise RuntimeError("Inference engine is not running")
        
        # Preprocess data if needed
        if isinstance(data, pd.DataFrame):
            processed_data = self.preprocessor.transform(data)
            # Create sequence
            sequences, _ = self.preprocessor.create_sequences(processed_data)
            if len(sequences) == 0:
                raise ValueError("Not enough data to create sequence")
            data = sequences[-1]  # Use most recent sequence
        
        # Add to queue
        self.input_queue.put((data, metadata or {}))
        
        # Wait for result
        try:
            result = self.output_queue.get(timeout=timeout)
            return result
        except queue.Empty:
            raise TimeoutError(f"Prediction timeout after {timeout} seconds")
    
    def predict_batch(
        self,
        data_list: List[Union[np.ndarray, pd.DataFrame]],
        metadata_list: Optional[List[Dict]] = None,
        timeout: float = 10.0
    ) -> List[PredictionResult]:
        """Make batch predictions."""
        if not self.is_running:
            raise RuntimeError("Inference engine is not running")
        
        if metadata_list is None:
            metadata_list = [{}] * len(data_list)
        
        # Process and queue all data
        for data, metadata in zip(data_list, metadata_list):
            if isinstance(data, pd.DataFrame):
                processed_data = self.preprocessor.transform(data)
                sequences, _ = self.preprocessor.create_sequences(processed_data)
                if len(sequences) > 0:
                    data = sequences[-1]
            
            self.input_queue.put((data, metadata))
        
        # Collect results
        results = []
        deadline = time.time() + timeout
        
        for _ in range(len(data_list)):
            remaining_time = deadline - time.time()
            if remaining_time <= 0:
                raise TimeoutError("Batch prediction timeout")
            
            try:
                result = self.output_queue.get(timeout=remaining_time)
                results.append(result)
            except queue.Empty:
                raise TimeoutError("Batch prediction timeout")
        
        return results
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics."""
        return self.performance_stats.copy()
    
    def get_model_metadata(self) -> Dict:
        """Get model metadata."""
        return self.model_metadata.copy()


class StreamingInferenceEngine(InferenceEngine):
    """
    Extended inference engine for streaming data sources.
    """
    
    def __init__(self, *args, buffer_size: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get feature dimension from model config
        n_features = self.model_metadata['config']['model']['input_dim']
        sequence_length = self.model_metadata['config']['data']['sequence_length']
        
        # Initialize streaming buffer
        self.buffer = RealTimeBuffer(sequence_length, n_features)
        self.stream_thread = None
        self.stream_callbacks = []
    
    def add_stream_callback(self, callback):
        """Add callback for streaming predictions."""
        self.stream_callbacks.append(callback)
    
    def stream_data(self, data_point: Union[np.ndarray, Dict]):
        """Add new data point to stream."""
        # Convert to numpy array if needed
        if isinstance(data_point, dict):
            # Assume dict contains feature values
            data_array = np.array(list(data_point.values()))
        else:
            data_array = np.array(data_point)
        
        # Add to buffer
        self.buffer.append(data_array)
        
        # Check if we have enough data for prediction
        window = self.buffer.get_window()
        if window is not None:
            # Make prediction
            result = self.predict(window)
            
            # Call callbacks
            for callback in self.stream_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Error in stream callback: {e}")
    
    def clear_buffer(self):
        """Clear the streaming buffer."""
        self.buffer.clear()


class ModelVersionManager:
    """
    Manages multiple model versions for A/B testing and gradual rollouts.
    """
    
    def __init__(self, models_dir: str):
        self.models_dir = Path(models_dir)
        self.engines = {}
        self.active_version = None
        self.version_weights = {}
    
    def load_version(self, version: str, model_path: str, preprocessor_path: str):
        """Load a model version."""
        engine = InferenceEngine(model_path, preprocessor_path)
        engine.start()
        self.engines[version] = engine
        
        if self.active_version is None:
            self.active_version = version
        
        logger.info(f"Loaded model version: {version}")
    
    def set_active_version(self, version: str):
        """Set the active model version."""
        if version not in self.engines:
            raise ValueError(f"Version {version} not loaded")
        self.active_version = version
    
    def set_version_weights(self, weights: Dict[str, float]):
        """Set weights for weighted ensemble prediction."""
        total = sum(weights.values())
        self.version_weights = {k: v/total for k, v in weights.items()}
    
    def predict(self, data: Union[np.ndarray, pd.DataFrame]) -> PredictionResult:
        """Make prediction using active version or ensemble."""
        if not self.version_weights:
            # Use single active version
            return self.engines[self.active_version].predict(data)
        else:
            # Weighted ensemble
            results = []
            weights = []
            
            for version, weight in self.version_weights.items():
                if version in self.engines:
                    result = self.engines[version].predict(data)
                    results.append(result)
                    weights.append(weight)
            
            # Combine predictions
            predictions = np.average(
                [r.predictions for r in results],
                weights=weights,
                axis=0
            )
            
            # Combine uncertainties (weighted average of variances)
            uncertainty = np.average(
                [r.uncertainty for r in results],
                weights=weights,
                axis=0
            )
            
            # Combine confidence (weighted average)
            confidence = np.average(
                [r.confidence for r in results],
                weights=weights
            )
            
            return PredictionResult(
                timestamp=datetime.now(),
                predictions=predictions,
                uncertainty=uncertainty,
                confidence=confidence,
                metadata={'ensemble_versions': list(self.version_weights.keys())}
            )
    
    def shutdown(self):
        """Shutdown all engines."""
        for engine in self.engines.values():
            engine.stop()


def create_inference_config() -> Dict:
    """Create default inference configuration."""
    return {
        'model_path': 'checkpoints/best_model.pt',
        'preprocessor_path': 'checkpoints/preprocessor.pkl',
        'device': 'cuda',
        'batch_timeout': 0.1,
        'max_batch_size': 32,
        'enable_attention': False,
        'streaming': {
            'buffer_size': 100,
            'update_frequency': 1.0
        }
    }