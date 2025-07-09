"""
Example Usage of the Transformer Market Prediction System

This script demonstrates various use cases of the market prediction model.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
from pathlib import Path

# Import the main system
from main import MarketPredictionSystem, create_default_config


def download_sample_data(symbol='AAPL', period='2y'):
    """Download sample market data for demonstration."""
    print(f"Downloading {symbol} data...")
    
    # Download data using yfinance
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period)
    
    # Rename columns to match expected format
    data = data.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    # Add timestamp column
    data['timestamp'] = data.index
    
    # Save to CSV
    data.to_csv('sample_data.csv', index=False)
    print(f"Saved {len(data)} rows to sample_data.csv")
    
    return data


def example_1_basic_training():
    """Example 1: Basic model training and evaluation."""
    print("\n=== Example 1: Basic Training ===")
    
    # Download sample data
    data = download_sample_data('SPY', '2y')
    
    # Create configuration
    config = create_default_config()
    
    # Modify for faster demo
    config['model']['d_model'] = 256
    config['model']['n_layers'] = 4
    config['training']['n_epochs'] = 20
    config['training']['batch_size'] = 16
    
    # Save config
    with open('demo_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Initialize system
    system = MarketPredictionSystem('demo_config.json')
    
    # Prepare data
    dataloaders = system.prepare_data('sample_data.csv')
    
    # Train model
    system.train(dataloaders)
    
    # Evaluate
    test_metrics = system.evaluate(dataloaders['test'])
    
    print(f"\nTest Results:")
    print(f"MAE: {test_metrics['mae']:.4f}")
    print(f"RMSE: {test_metrics['rmse']:.4f}")
    print(f"Calibration Error: {test_metrics['avg_calibration_error']:.4f}")
    print(f"Average Confidence: {test_metrics['avg_confidence_score']:.2%}")
    
    return system


def example_2_real_time_prediction():
    """Example 2: Real-time prediction with streaming data."""
    print("\n=== Example 2: Real-time Prediction ===")
    
    # Load pre-trained model (use system from example 1 or load checkpoint)
    config = json.load(open('demo_config.json'))
    config['inference']['streaming']['enabled'] = True
    
    system = MarketPredictionSystem('demo_config.json')
    system.setup_inference()
    
    # Simulate streaming data
    data = pd.read_csv('sample_data.csv', parse_dates=['timestamp'])
    
    # Use last 100 days for streaming simulation
    streaming_data = data.tail(100)
    
    predictions = []
    confidences = []
    
    print("Simulating real-time predictions...")
    
    # Stream through data
    for i in range(60, len(streaming_data)):
        # Get window of data
        window = streaming_data.iloc[i-60:i]
        
        # Make prediction
        result = system.predict(window)
        
        predictions.append(result['predictions'][0])  # Next day prediction
        confidences.append(result['calibrated_confidence'])
        
        # Print every 10th prediction
        if i % 10 == 0:
            print(f"Step {i}: Prediction={result['predictions'][0]:.2f}, "
                  f"Confidence={result['calibrated_confidence']:.2%}")
    
    # Plot results
    plt.figure(figsize=(12, 6))
    
    plt.subplot(2, 1, 1)
    plt.plot(streaming_data['close'].values[60:], label='Actual', alpha=0.7)
    plt.plot(predictions, label='Predictions', alpha=0.7)
    plt.legend()
    plt.title('Real-time Predictions')
    plt.ylabel('Price')
    
    plt.subplot(2, 1, 2)
    plt.plot(confidences)
    plt.title('Prediction Confidence')
    plt.ylabel('Confidence')
    plt.xlabel('Time Step')
    
    plt.tight_layout()
    plt.savefig('realtime_predictions.png')
    print("Saved plot to realtime_predictions.png")


def example_3_uncertainty_analysis():
    """Example 3: Uncertainty estimation and confidence intervals."""
    print("\n=== Example 3: Uncertainty Analysis ===")
    
    # Load system
    system = MarketPredictionSystem('demo_config.json')
    system.setup_inference()
    
    # Load recent data
    data = pd.read_csv('sample_data.csv', parse_dates=['timestamp'])
    recent_data = data.tail(60)
    
    # Make prediction with uncertainty
    result = system.predict(recent_data)
    
    print(f"\nPrediction Results:")
    print(f"Point Predictions: {result['predictions']}")
    print(f"Uncertainty (std): {np.sqrt(result['uncertainty'])}")
    print(f"Raw Confidence: {result['raw_confidence']:.2%}")
    print(f"Calibrated Confidence: {result['calibrated_confidence']:.2%}")
    
    # Plot prediction intervals
    horizon = len(result['predictions'])
    x = np.arange(1, horizon + 1)
    
    plt.figure(figsize=(10, 6))
    
    # Plot predictions with uncertainty bands
    predictions = result['predictions']
    uncertainty = np.sqrt(result['uncertainty'])
    
    plt.plot(x, predictions, 'b-', label='Predictions', linewidth=2)
    plt.fill_between(x, 
                     predictions - 2*uncertainty,
                     predictions + 2*uncertainty,
                     alpha=0.3, label='95% Confidence Interval')
    plt.fill_between(x,
                     predictions - uncertainty,
                     predictions + uncertainty,
                     alpha=0.5, label='68% Confidence Interval')
    
    plt.xlabel('Days Ahead')
    plt.ylabel('Predicted Price')
    plt.title('Predictions with Uncertainty Bands')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('uncertainty_analysis.png')
    print("\nSaved uncertainty plot to uncertainty_analysis.png")


def example_4_backtest_analysis():
    """Example 4: Comprehensive backtesting."""
    print("\n=== Example 4: Backtest Analysis ===")
    
    # Load system
    system = MarketPredictionSystem('demo_config.json')
    
    # Load full dataset
    data = pd.read_csv('sample_data.csv', parse_dates=['timestamp'], index_col='timestamp')
    
    # Run backtest on last 6 months
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    backtest_results = system.backtest(data, start_date=start_date)
    
    print(f"\nBacktest Results:")
    print(f"MAE: {backtest_results['mae']:.4f}")
    print(f"RMSE: {backtest_results['rmse']:.4f}")
    print(f"Direction Accuracy: {backtest_results['direction_accuracy']:.2%}")
    print(f"Confidence Correlation: {backtest_results['confidence_correlation']:.3f}")
    print(f"Average Confidence: {backtest_results['avg_confidence']:.2%}")
    print(f"Total Predictions: {backtest_results['n_predictions']}")
    
    # Save detailed results
    with open('backtest_results.json', 'w') as f:
        json.dump(backtest_results, f, indent=2)


def example_5_model_comparison():
    """Example 5: Compare different model configurations."""
    print("\n=== Example 5: Model Comparison ===")
    
    # Download data if not exists
    if not Path('sample_data.csv').exists():
        download_sample_data('QQQ', '2y')
    
    # Configuration variations
    configs = {
        'small': {
            'd_model': 128,
            'n_heads': 4,
            'n_layers': 2,
            'd_ff': 512
        },
        'medium': {
            'd_model': 256,
            'n_heads': 8,
            'n_layers': 4,
            'd_ff': 1024
        },
        'large': {
            'd_model': 512,
            'n_heads': 8,
            'n_layers': 6,
            'd_ff': 2048
        }
    }
    
    results = {}
    
    for name, model_config in configs.items():
        print(f"\nTraining {name} model...")
        
        # Create config
        config = create_default_config()
        config['model'].update(model_config)
        config['training']['n_epochs'] = 10  # Reduced for demo
        
        # Save config
        config_path = f'config_{name}.json'
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Train and evaluate
        system = MarketPredictionSystem(config_path)
        dataloaders = system.prepare_data('sample_data.csv')
        
        system.train(dataloaders)
        metrics = system.evaluate(dataloaders['test'])
        
        results[name] = {
            'mae': metrics['mae'],
            'rmse': metrics['rmse'],
            'params': sum(p.numel() for p in system.model.parameters())
        }
        
        print(f"{name} - MAE: {metrics['mae']:.4f}, "
              f"Params: {results[name]['params']:,}")
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    
    names = list(results.keys())
    maes = [results[n]['mae'] for n in names]
    params = [results[n]['params'] for n in names]
    
    plt.subplot(1, 2, 1)
    plt.bar(names, maes)
    plt.title('Model Performance (MAE)')
    plt.ylabel('MAE')
    
    plt.subplot(1, 2, 2)
    plt.bar(names, params)
    plt.title('Model Size')
    plt.ylabel('Parameters')
    
    plt.tight_layout()
    plt.savefig('model_comparison.png')
    print("\nSaved comparison to model_comparison.png")


def example_6_attention_visualization():
    """Example 6: Visualize attention patterns."""
    print("\n=== Example 6: Attention Visualization ===")
    
    # Enable attention in config
    config = json.load(open('demo_config.json'))
    config['inference']['enable_attention'] = True
    
    # Save updated config
    with open('demo_config_attention.json', 'w') as f:
        json.dump(config, f)
    
    # Load system with attention enabled
    system = MarketPredictionSystem('demo_config_attention.json')
    system.setup_inference()
    
    # Get sample data
    data = pd.read_csv('sample_data.csv', parse_dates=['timestamp'])
    sample = data.tail(60)
    
    # Get prediction with attention
    from inference.inference_engine import InferenceEngine
    
    # Make raw model call to get attention weights
    if system.model is None:
        system.build_model()
    
    # Prepare input
    processed = system.preprocessor.transform(sample)
    sequences, _ = system.preprocessor.create_sequences(processed)
    input_tensor = torch.FloatTensor(sequences[-1:]).to(system.device)
    
    # Get model output with attention
    with torch.no_grad():
        outputs = system.model(input_tensor, return_attention=True)
    
    if 'attention_weights' in outputs:
        # Average attention across layers and heads
        attention = torch.stack(outputs['attention_weights']).mean(dim=[0, 2])
        attention = attention.squeeze().cpu().numpy()
        
        # Plot attention heatmap
        plt.figure(figsize=(12, 8))
        plt.imshow(attention, cmap='hot', interpolation='nearest')
        plt.colorbar()
        plt.title('Attention Weights Heatmap')
        plt.xlabel('Input Time Steps')
        plt.ylabel('Output Time Steps')
        plt.tight_layout()
        plt.savefig('attention_heatmap.png')
        print("Saved attention visualization to attention_heatmap.png")
    else:
        print("Attention weights not available")


def example_7_feature_importance():
    """Example 7: Analyze feature importance."""
    print("\n=== Example 7: Feature Importance Analysis ===")
    
    # This would require training multiple models with feature ablation
    # or using techniques like SHAP values
    
    # For demonstration, we'll show how to access feature names
    system = MarketPredictionSystem('demo_config.json')
    data = pd.read_csv('sample_data.csv', parse_dates=['timestamp'])
    
    # Prepare data to get feature names
    system.prepare_data('sample_data.csv')
    
    if system.preprocessor:
        feature_names = system.preprocessor.feature_names
        print(f"\nTotal features: {len(feature_names)}")
        print("\nFeature categories:")
        
        # Group features by type
        price_features = [f for f in feature_names if any(p in f for p in ['open', 'high', 'low', 'close'])]
        technical_features = [f for f in feature_names if any(t in f for t in ['rsi', 'macd', 'bb', 'sma', 'ema'])]
        volume_features = [f for f in feature_names if 'volume' in f or 'obv' in f]
        time_features = [f for f in feature_names if any(t in f for t in ['hour', 'dow', 'month'])]
        
        print(f"Price features: {len(price_features)}")
        print(f"Technical indicators: {len(technical_features)}")
        print(f"Volume features: {len(volume_features)}")
        print(f"Time features: {len(time_features)}")
        
        print("\nSample features:")
        for feature in feature_names[:10]:
            print(f"  - {feature}")


def main():
    """Run all examples."""
    print("Market Prediction Transformer - Example Usage")
    print("=" * 50)
    
    # Create output directory
    Path('outputs').mkdir(exist_ok=True)
    
    # Run examples
    try:
        # Basic training
        system = example_1_basic_training()
        
        # Real-time prediction
        example_2_real_time_prediction()
        
        # Uncertainty analysis
        example_3_uncertainty_analysis()
        
        # Backtesting
        example_4_backtest_analysis()
        
        # Model comparison (optional - takes longer)
        # example_5_model_comparison()
        
        # Attention visualization
        example_6_attention_visualization()
        
        # Feature importance
        example_7_feature_importance()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("Check the generated files for results.")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()