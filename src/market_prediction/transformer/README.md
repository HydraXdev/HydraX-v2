# Transformer-based Market Prediction Model

A sophisticated deep learning system for financial market prediction using transformer architecture with attention mechanisms, uncertainty estimation, and automated model versioning.

## Features

### 1. **Advanced Transformer Architecture**
- Custom transformer model optimized for time series prediction
- Multiple attention mechanisms:
  - Local attention for short-term patterns
  - Dilated attention for multi-scale temporal features
  - Cross-time-scale attention for micro and macro patterns
  - Pattern matching attention with learnable templates
  - Hierarchical attention for market regime detection

### 2. **Comprehensive Data Pipeline**
- Automated feature engineering with 50+ technical indicators
- Robust data preprocessing with multiple normalization methods
- Support for streaming real-time data
- Data augmentation for improved generalization

### 3. **Uncertainty Quantification**
- Monte Carlo Dropout for epistemic uncertainty
- Probabilistic predictions with confidence intervals
- Adaptive uncertainty scaling based on market conditions
- Calibrated confidence scores

### 4. **Production-Ready Inference**
- High-performance batch inference engine
- Real-time streaming predictions
- TorchScript optimization for faster inference
- Automatic model versioning and A/B testing

### 5. **Model Management**
- Automated version control with Git integration
- MLflow experiment tracking
- A/B testing framework
- Automatic rollback on performance degradation
- Continuous learning with automated updates

## Installation

```bash
# Clone the repository
cd /root/HydraX-v2/src/market_prediction/transformer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Create Configuration

```bash
python main.py --create-config
```

This creates a default `config.json` file. Modify it according to your needs.

### 2. Prepare Your Data

Expected data format (CSV with columns):
- `timestamp`: DateTime index
- `open`, `high`, `low`, `close`: Price data
- `volume`: Trading volume

### 3. Train the Model

```bash
python main.py --config config.json --mode train --data path/to/your/data.csv
```

### 4. Make Predictions

```bash
python main.py --config config.json --mode predict --data path/to/new_data.csv --output predictions.npy
```

### 5. Run Backtest

```bash
python main.py --config config.json --mode backtest --data path/to/historical_data.csv --output backtest_results.json
```

### 6. Start Inference Server

```bash
python main.py --config config.json --mode serve
```

## Configuration Guide

### Model Configuration

```json
{
  "model": {
    "type": "temporal",  // "standard" or "temporal"
    "input_dim": 50,     // Number of features after preprocessing
    "d_model": 512,      // Transformer dimension
    "n_heads": 8,        // Number of attention heads
    "n_layers": 6,       // Number of transformer layers
    "d_ff": 2048,        // Feed-forward dimension
    "max_seq_len": 100,  // Maximum sequence length
    "n_outputs": 5,      // Prediction horizon
    "dropout": 0.1       // Dropout rate
  }
}
```

### Data Configuration

```json
{
  "data": {
    "sequence_length": 60,      // Input sequence length
    "prediction_horizon": 5,    // How many steps to predict
    "normalization_method": "robust",  // "standard", "robust", or "minmax"
    "train_split": 0.7,
    "val_split": 0.15,
    "features": {
      "technical_indicators": {
        "momentum": ["rsi", "stoch", "williams_r"],
        "trend": ["sma", "ema", "macd", "adx"],
        "volatility": ["bb_bands", "atr"],
        "volume": ["obv", "cmf"]
      }
    }
  }
}
```

## Usage Examples

### Training with Custom Configuration

```python
from main import MarketPredictionSystem

# Initialize system
system = MarketPredictionSystem('config.json')

# Load and prepare data
dataloaders = system.prepare_data('market_data.csv')

# Train model
system.train(dataloaders)

# Evaluate
metrics = system.evaluate(dataloaders['test'])
print(f"Test MAE: {metrics['mae']:.4f}")
```

### Real-time Predictions

```python
# Setup streaming inference
system.setup_inference()

# Stream data point
new_data = {
    'open': 100.5,
    'high': 101.2,
    'low': 99.8,
    'close': 100.9,
    'volume': 1000000
}

# For streaming engine
if hasattr(system.inference_engine, 'stream_data'):
    system.inference_engine.stream_data(new_data)
```

### Uncertainty Estimation

```python
# Make prediction with uncertainty
result = system.predict(data_df)

print(f"Prediction: {result['predictions']}")
print(f"Uncertainty: {result['uncertainty']}")
print(f"Confidence: {result['calibrated_confidence']:.2%}")
print(f"95% Interval: {result['prediction_interval']}")
```

### Model Versioning

```python
# Setup versioning
system.setup_versioning()

# Register new model version
version_id = system.version_manager.register_model(
    model=trained_model,
    training_config=config,
    performance_metrics=metrics,
    preprocessor=preprocessor,
    notes="Improved feature engineering"
)

# Start A/B test
system.version_manager.start_ab_test(
    challenger_version=version_id,
    traffic_split=0.1  # 10% traffic to new model
)

# Check A/B test results
results = system.version_manager.get_ab_test_results()
```

## Architecture Details

### Transformer Architecture

The model uses a modified transformer architecture optimized for time series:

1. **Input Projection**: Projects features to model dimension
2. **Positional Encoding**: Sinusoidal encoding for temporal awareness
3. **Transformer Blocks**: Multi-head attention + feed-forward networks
4. **Output Heads**:
   - Prediction head: Point predictions
   - Uncertainty head: Variance estimation
   - Confidence head: Confidence scoring

### Attention Mechanisms

- **Standard Multi-Head Attention**: For general pattern recognition
- **Local Attention**: Focuses on nearby time steps for momentum
- **Dilated Attention**: Captures patterns at multiple time scales
- **Cross-Time-Scale Attention**: Integrates micro and macro patterns

### Loss Functions

- **Probabilistic Loss**: Negative log-likelihood with uncertainty
- **MSE/MAE**: For point prediction accuracy
- **Calibration Loss**: For uncertainty calibration

## Performance Optimization

### Training Optimization

- Mixed precision training with automatic mixed precision (AMP)
- Gradient accumulation for larger effective batch sizes
- Learning rate scheduling with warm restarts
- Early stopping with patience

### Inference Optimization

- TorchScript compilation for faster inference
- Batch processing with timeout
- GPU utilization optimization
- Caching for repeated predictions

## Monitoring and Debugging

### Training Monitoring

- Weights & Biases integration for experiment tracking
- Real-time loss and metric visualization
- Attention weight visualization
- Gradient flow monitoring

### Production Monitoring

- Performance metrics tracking
- Prediction confidence distribution
- Model version performance comparison
- Automatic alerts on degradation

## Best Practices

1. **Data Quality**
   - Ensure data is cleaned and gaps are handled
   - Use at least 2 years of historical data for training
   - Include multiple timeframes if available

2. **Feature Engineering**
   - Start with default features and add domain-specific ones
   - Monitor feature importance
   - Remove highly correlated features

3. **Model Selection**
   - Use temporal transformer for complex patterns
   - Start with smaller models and scale up
   - Monitor overfitting with validation metrics

4. **Deployment**
   - Always use A/B testing for new models
   - Set conservative rollback thresholds
   - Monitor real-time performance metrics

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Reduce batch size
   - Decrease model dimensions
   - Use gradient accumulation

2. **Poor Predictions**
   - Check data preprocessing
   - Verify feature engineering
   - Adjust sequence length

3. **Slow Inference**
   - Enable TorchScript
   - Reduce model complexity
   - Use batch inference

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is part of the HydraX-v2 system.

## Citation

If you use this model in your research, please cite:

```bibtex
@software{transformer_market_prediction,
  title={Transformer-based Market Prediction Model},
  author={HydraX Team},
  year={2025},
  url={https://github.com/HydraX/market-prediction}
}
```