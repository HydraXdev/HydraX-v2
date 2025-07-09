"""
Data Preprocessing Pipeline for Market Time Series

This module provides comprehensive preprocessing for financial time series data,
including normalization, feature engineering, and sequence preparation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
import torch
from torch.utils.data import Dataset, DataLoader
import ta  # Technical Analysis library
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class MarketDataPreprocessor:
    """
    Comprehensive preprocessing pipeline for market data.
    
    Features:
    - Multiple normalization strategies
    - Technical indicator calculation
    - Feature engineering
    - Sequence windowing
    - Missing data handling
    """
    
    def __init__(
        self,
        normalization_method: str = 'robust',
        sequence_length: int = 60,
        prediction_horizon: int = 5,
        feature_config: Optional[Dict] = None
    ):
        self.normalization_method = normalization_method
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.feature_config = feature_config or self._get_default_features()
        
        self.scalers = {}
        self.feature_names = []
        self.is_fitted = False
    
    def _get_default_features(self) -> Dict:
        """Get default feature configuration."""
        return {
            'price_features': ['open', 'high', 'low', 'close', 'volume'],
            'returns': [1, 5, 10, 20],  # Return periods
            'technical_indicators': {
                'momentum': ['rsi', 'stoch', 'williams_r'],
                'trend': ['sma', 'ema', 'macd', 'adx'],
                'volatility': ['bb_bands', 'atr', 'keltner'],
                'volume': ['obv', 'cmf', 'mfi']
            },
            'time_features': ['hour', 'day_of_week', 'month', 'quarter'],
            'market_features': ['spread', 'volume_profile', 'price_levels']
        }
    
    def fit(self, data: pd.DataFrame) -> 'MarketDataPreprocessor':
        """Fit the preprocessor on training data."""
        # Engineer features
        featured_data = self._engineer_features(data)
        
        # Fit scalers for each feature group
        if self.normalization_method == 'standard':
            scaler_class = StandardScaler
        elif self.normalization_method == 'robust':
            scaler_class = RobustScaler
        elif self.normalization_method == 'minmax':
            scaler_class = MinMaxScaler
        else:
            raise ValueError(f"Unknown normalization method: {self.normalization_method}")
        
        # Fit separate scalers for different feature types
        feature_groups = {
            'price': ['open', 'high', 'low', 'close'],
            'volume': ['volume'],
            'returns': [col for col in featured_data.columns if 'return' in col],
            'indicators': [col for col in featured_data.columns if any(
                ind in col for ind in ['rsi', 'macd', 'bb', 'atr', 'stoch']
            )],
            'others': []
        }
        
        # Collect remaining features
        assigned_features = set()
        for group_features in feature_groups.values():
            assigned_features.update(group_features)
        
        feature_groups['others'] = [
            col for col in featured_data.columns 
            if col not in assigned_features
        ]
        
        # Fit scalers
        for group_name, features in feature_groups.items():
            if features:
                self.scalers[group_name] = scaler_class()
                self.scalers[group_name].fit(featured_data[features])
        
        self.feature_names = list(featured_data.columns)
        self.is_fitted = True
        
        return self
    
    def transform(self, data: pd.DataFrame) -> np.ndarray:
        """Transform data using fitted preprocessor."""
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before transform")
        
        # Engineer features
        featured_data = self._engineer_features(data)
        
        # Apply scaling
        scaled_data = featured_data.copy()
        
        for group_name, scaler in self.scalers.items():
            features = [f for f in scaler.feature_names_in_ if f in scaled_data.columns]
            if features:
                scaled_data[features] = scaler.transform(scaled_data[features])
        
        return scaled_data.values
    
    def fit_transform(self, data: pd.DataFrame) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(data).transform(data)
    
    def inverse_transform(self, data: np.ndarray, feature_indices: Optional[List[int]] = None) -> np.ndarray:
        """Inverse transform for specific features."""
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before inverse transform")
        
        if feature_indices is None:
            # Default to price features
            feature_indices = [self.feature_names.index('close')]
        
        # Create a copy to avoid modifying original
        transformed = data.copy()
        
        # Find which scaler contains the target features
        for feature_idx in feature_indices:
            feature_name = self.feature_names[feature_idx]
            
            for group_name, scaler in self.scalers.items():
                if feature_name in scaler.feature_names_in_:
                    # Get the index within the scaler's features
                    scaler_idx = list(scaler.feature_names_in_).index(feature_name)
                    
                    # Inverse transform
                    temp_data = np.zeros((len(data), len(scaler.feature_names_in_)))
                    temp_data[:, scaler_idx] = data[:, feature_idx]
                    inversed = scaler.inverse_transform(temp_data)
                    transformed[:, feature_idx] = inversed[:, scaler_idx]
                    break
        
        return transformed
    
    def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw market data."""
        df = data.copy()
        
        # Calculate returns
        for period in self.feature_config.get('returns', []):
            df[f'return_{period}'] = df['close'].pct_change(period)
        
        # Calculate technical indicators
        tech_config = self.feature_config.get('technical_indicators', {})
        
        # Momentum indicators
        if 'rsi' in tech_config.get('momentum', []):
            df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        
        if 'stoch' in tech_config.get('momentum', []):
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
        
        if 'williams_r' in tech_config.get('momentum', []):
            df['williams_r'] = ta.momentum.WilliamsRIndicator(
                df['high'], df['low'], df['close']
            ).williams_r()
        
        # Trend indicators
        if 'sma' in tech_config.get('trend', []):
            for period in [10, 20, 50]:
                df[f'sma_{period}'] = ta.trend.SMAIndicator(df['close'], period).sma_indicator()
        
        if 'ema' in tech_config.get('trend', []):
            for period in [12, 26]:
                df[f'ema_{period}'] = ta.trend.EMAIndicator(df['close'], period).ema_indicator()
        
        if 'macd' in tech_config.get('trend', []):
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
        
        if 'adx' in tech_config.get('trend', []):
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
        
        # Volatility indicators
        if 'bb_bands' in tech_config.get('volatility', []):
            bb = ta.volatility.BollingerBands(df['close'])
            df['bb_high'] = bb.bollinger_hband()
            df['bb_low'] = bb.bollinger_lband()
            df['bb_width'] = bb.bollinger_wband()
            df['bb_pct'] = bb.bollinger_pband()
        
        if 'atr' in tech_config.get('volatility', []):
            df['atr'] = ta.volatility.AverageTrueRange(
                df['high'], df['low'], df['close']
            ).average_true_range()
        
        # Volume indicators
        if 'obv' in tech_config.get('volume', []):
            df['obv'] = ta.volume.OnBalanceVolumeIndicator(
                df['close'], df['volume']
            ).on_balance_volume()
        
        if 'cmf' in tech_config.get('volume', []):
            df['cmf'] = ta.volume.ChaikinMoneyFlowIndicator(
                df['high'], df['low'], df['close'], df['volume']
            ).chaikin_money_flow()
        
        # Time features
        if 'time' in data.columns or data.index.name == 'time':
            time_index = pd.to_datetime(data.index if data.index.name == 'time' else data['time'])
            
            if 'hour' in self.feature_config.get('time_features', []):
                df['hour_sin'] = np.sin(2 * np.pi * time_index.hour / 24)
                df['hour_cos'] = np.cos(2 * np.pi * time_index.hour / 24)
            
            if 'day_of_week' in self.feature_config.get('time_features', []):
                df['dow_sin'] = np.sin(2 * np.pi * time_index.dayofweek / 7)
                df['dow_cos'] = np.cos(2 * np.pi * time_index.dayofweek / 7)
        
        # Market microstructure features
        if 'spread' in self.feature_config.get('market_features', []):
            df['spread'] = df['high'] - df['low']
            df['spread_pct'] = df['spread'] / df['close']
        
        if 'volume_profile' in self.feature_config.get('market_features', []):
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        if 'price_levels' in self.feature_config.get('market_features', []):
            # Support and resistance levels
            df['distance_to_high'] = df['high'].rolling(20).max() - df['close']
            df['distance_to_low'] = df['close'] - df['low'].rolling(20).min()
        
        # Handle missing values
        df = df.fillna(method='ffill').fillna(0)
        
        # Remove any remaining NaN or inf values
        df = df.replace([np.inf, -np.inf], 0)
        
        return df
    
    def create_sequences(
        self, 
        data: np.ndarray, 
        targets: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences for time series prediction."""
        n_samples = len(data) - self.sequence_length - self.prediction_horizon + 1
        
        if n_samples <= 0:
            raise ValueError("Not enough data for the specified sequence length and prediction horizon")
        
        # Create sequences
        sequences = np.zeros((n_samples, self.sequence_length, data.shape[1]))
        
        for i in range(n_samples):
            sequences[i] = data[i:i + self.sequence_length]
        
        # Create targets if provided
        if targets is not None:
            target_sequences = np.zeros((n_samples, self.prediction_horizon))
            
            for i in range(n_samples):
                start_idx = i + self.sequence_length
                end_idx = start_idx + self.prediction_horizon
                target_sequences[i] = targets[start_idx:end_idx]
            
            return sequences, target_sequences
        
        return sequences, None


class MarketDataset(Dataset):
    """PyTorch dataset for market time series data."""
    
    def __init__(
        self,
        sequences: np.ndarray,
        targets: Optional[np.ndarray] = None,
        augment: bool = False,
        noise_level: float = 0.01
    ):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets) if targets is not None else None
        self.augment = augment
        self.noise_level = noise_level
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Union[Tuple[torch.Tensor, torch.Tensor], torch.Tensor]:
        sequence = self.sequences[idx]
        
        # Apply augmentation if enabled
        if self.augment and np.random.random() > 0.5:
            noise = torch.randn_like(sequence) * self.noise_level
            sequence = sequence + noise
        
        if self.targets is not None:
            return sequence, self.targets[idx]
        
        return sequence


class DataPipeline:
    """Complete data pipeline for market prediction."""
    
    def __init__(
        self,
        preprocessor: MarketDataPreprocessor,
        batch_size: int = 32,
        train_split: float = 0.7,
        val_split: float = 0.15,
        shuffle: bool = False,  # Usually False for time series
        augment_train: bool = True
    ):
        self.preprocessor = preprocessor
        self.batch_size = batch_size
        self.train_split = train_split
        self.val_split = val_split
        self.shuffle = shuffle
        self.augment_train = augment_train
    
    def prepare_data(
        self, 
        data: pd.DataFrame,
        target_column: str = 'close'
    ) -> Dict[str, DataLoader]:
        """Prepare data loaders for training, validation, and testing."""
        # Preprocess data
        processed_data = self.preprocessor.fit_transform(data)
        
        # Get target column index
        target_idx = self.preprocessor.feature_names.index(target_column)
        targets = processed_data[:, target_idx]
        
        # Create sequences
        sequences, target_sequences = self.preprocessor.create_sequences(
            processed_data, targets
        )
        
        # Split data
        n_samples = len(sequences)
        train_size = int(n_samples * self.train_split)
        val_size = int(n_samples * self.val_split)
        
        train_sequences = sequences[:train_size]
        train_targets = target_sequences[:train_size]
        
        val_sequences = sequences[train_size:train_size + val_size]
        val_targets = target_sequences[train_size:train_size + val_size]
        
        test_sequences = sequences[train_size + val_size:]
        test_targets = target_sequences[train_size + val_size:]
        
        # Create datasets
        train_dataset = MarketDataset(
            train_sequences, train_targets, 
            augment=self.augment_train
        )
        val_dataset = MarketDataset(val_sequences, val_targets)
        test_dataset = MarketDataset(test_sequences, test_targets)
        
        # Create data loaders
        dataloaders = {
            'train': DataLoader(
                train_dataset, 
                batch_size=self.batch_size,
                shuffle=self.shuffle
            ),
            'val': DataLoader(
                val_dataset,
                batch_size=self.batch_size,
                shuffle=False
            ),
            'test': DataLoader(
                test_dataset,
                batch_size=self.batch_size,
                shuffle=False
            )
        }
        
        return dataloaders
    
    def prepare_inference_data(self, data: pd.DataFrame) -> torch.Tensor:
        """Prepare data for inference."""
        processed_data = self.preprocessor.transform(data)
        sequences, _ = self.preprocessor.create_sequences(processed_data)
        return torch.FloatTensor(sequences)