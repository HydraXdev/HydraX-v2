"""
Uncertainty Estimation and Confidence Scoring

This module implements advanced uncertainty quantification methods
for market predictions.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
from sklearn.isotonic import IsotonicRegression
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass

@dataclass
class UncertaintyMetrics:
    """Container for uncertainty metrics."""
    epistemic_uncertainty: float  # Model uncertainty
    aleatoric_uncertainty: float  # Data uncertainty
    total_uncertainty: float
    confidence_score: float
    prediction_interval: Tuple[float, float]
    quantiles: Dict[float, float]

class MCDropout(nn.Module):
    """Monte Carlo Dropout for uncertainty estimation."""
    
    def __init__(self, p: float = 0.1):
        super().__init__()
        self.p = p
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.dropout(x, p=self.p, training=True)

class UncertaintyEstimator:
    """
    Advanced uncertainty estimation for market predictions.
    
    Methods:
    - Monte Carlo Dropout
    - Deep Ensembles
    - Quantile Regression
    - Calibrated Confidence Scores
    """
    
    def __init__(
        self,
        model: nn.Module,
        n_samples: int = 100,
        confidence_levels: List[float] = [0.68, 0.95, 0.99],
        calibration_data: Optional[Tuple[np.ndarray, np.ndarray]] = None
    ):
        self.model = model
        self.n_samples = n_samples
        self.confidence_levels = confidence_levels
        
        # Enable MC Dropout
        self._enable_mc_dropout()
        
        # Calibration
        self.calibrator = None
        if calibration_data is not None:
            self.calibrate(*calibration_data)
    
    def _enable_mc_dropout(self):
        """Enable dropout during inference for MC Dropout."""
        def apply_dropout(module):
            if isinstance(module, nn.Dropout):
                module.train()
        
        self.model.apply(apply_dropout)
    
    def estimate_uncertainty(
        self,
        inputs: torch.Tensor,
        method: str = 'mc_dropout'
    ) -> UncertaintyMetrics:
        """
        Estimate uncertainty using specified method.
        
        Args:
            inputs: Input tensor
            method: Uncertainty estimation method
            
        Returns:
            UncertaintyMetrics object
        """
        if method == 'mc_dropout':
            return self._mc_dropout_uncertainty(inputs)
        elif method == 'ensemble':
            return self._ensemble_uncertainty(inputs)
        elif method == 'quantile':
            return self._quantile_uncertainty(inputs)
        else:
            raise ValueError(f"Unknown uncertainty method: {method}")
    
    def _mc_dropout_uncertainty(self, inputs: torch.Tensor) -> UncertaintyMetrics:
        """Estimate uncertainty using Monte Carlo Dropout."""
        # Run multiple forward passes
        predictions = []
        uncertainties = []
        confidences = []
        
        with torch.no_grad():
            for _ in range(self.n_samples):
                outputs = self.model(inputs)
                predictions.append(outputs['predictions'])
                uncertainties.append(outputs['uncertainty'])
                confidences.append(outputs['confidence'])
        
        # Stack predictions
        predictions = torch.stack(predictions, dim=0)  # (n_samples, batch, pred_horizon)
        uncertainties = torch.stack(uncertainties, dim=0)
        confidences = torch.stack(confidences, dim=0)
        
        # Calculate statistics
        mean_prediction = predictions.mean(dim=0)
        epistemic_uncertainty = predictions.var(dim=0)
        aleatoric_uncertainty = uncertainties.mean(dim=0)
        total_uncertainty = epistemic_uncertainty + aleatoric_uncertainty
        
        # Calculate prediction intervals
        quantiles = {}
        for level in self.confidence_levels:
            lower_q = (1 - level) / 2
            upper_q = 1 - lower_q
            quantiles[level] = {
                'lower': torch.quantile(predictions, lower_q, dim=0),
                'upper': torch.quantile(predictions, upper_q, dim=0)
            }
        
        # Confidence score (inverse of coefficient of variation)
        cv = torch.sqrt(total_uncertainty) / (torch.abs(mean_prediction) + 1e-8)
        confidence_score = 1 / (1 + cv.mean())
        
        # Get 95% prediction interval
        pred_interval = (
            quantiles[0.95]['lower'].cpu().numpy(),
            quantiles[0.95]['upper'].cpu().numpy()
        )
        
        return UncertaintyMetrics(
            epistemic_uncertainty=epistemic_uncertainty.mean().item(),
            aleatoric_uncertainty=aleatoric_uncertainty.mean().item(),
            total_uncertainty=total_uncertainty.mean().item(),
            confidence_score=confidence_score.item(),
            prediction_interval=pred_interval,
            quantiles={k: (v['lower'].cpu().numpy(), v['upper'].cpu().numpy()) 
                      for k, v in quantiles.items()}
        )
    
    def _ensemble_uncertainty(self, inputs: torch.Tensor) -> UncertaintyMetrics:
        """Estimate uncertainty using deep ensembles."""
        # This would require multiple models
        # For now, return MC Dropout estimate
        return self._mc_dropout_uncertainty(inputs)
    
    def _quantile_uncertainty(self, inputs: torch.Tensor) -> UncertaintyMetrics:
        """Estimate uncertainty using quantile regression."""
        # This would require a model trained with quantile loss
        # For now, return MC Dropout estimate
        return self._mc_dropout_uncertainty(inputs)
    
    def calibrate(self, predictions: np.ndarray, targets: np.ndarray):
        """
        Calibrate confidence scores using isotonic regression.
        
        Args:
            predictions: Model predictions
            targets: True values
        """
        # Calculate prediction errors
        errors = np.abs(predictions - targets).mean(axis=1)
        
        # Normalize errors to [0, 1] for confidence scores
        confidence_targets = 1 - (errors - errors.min()) / (errors.max() - errors.min())
        
        # Get model confidence scores
        model_confidences = self._get_confidence_scores(predictions)
        
        # Fit isotonic regression
        self.calibrator = IsotonicRegression(out_of_bounds='clip')
        self.calibrator.fit(model_confidences, confidence_targets)
    
    def _get_confidence_scores(self, predictions: np.ndarray) -> np.ndarray:
        """Extract confidence scores from predictions."""
        # This is a placeholder - actual implementation would depend on model
        return np.random.rand(len(predictions))
    
    def get_calibrated_confidence(self, raw_confidence: float) -> float:
        """Get calibrated confidence score."""
        if self.calibrator is None:
            return raw_confidence
        return float(self.calibrator.predict([raw_confidence])[0])

class AdaptiveUncertaintyEstimator(UncertaintyEstimator):
    """
    Adaptive uncertainty estimator that adjusts based on market conditions.
    """
    
    def __init__(self, *args, market_volatility_window: int = 20, **kwargs):
        super().__init__(*args, **kwargs)
        self.market_volatility_window = market_volatility_window
        self.volatility_history = []
        self.uncertainty_scaling_factor = 1.0
    
    def update_market_conditions(self, returns: np.ndarray):
        """Update uncertainty scaling based on market volatility."""
        # Calculate realized volatility
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        self.volatility_history.append(volatility)
        
        if len(self.volatility_history) > self.market_volatility_window:
            self.volatility_history.pop(0)
        
        # Calculate volatility regime
        if len(self.volatility_history) >= 10:
            current_vol = np.mean(self.volatility_history[-5:])
            historical_vol = np.mean(self.volatility_history)
            
            # Adjust uncertainty scaling
            vol_ratio = current_vol / (historical_vol + 1e-8)
            self.uncertainty_scaling_factor = np.clip(vol_ratio, 0.5, 2.0)
    
    def estimate_uncertainty(
        self,
        inputs: torch.Tensor,
        method: str = 'mc_dropout'
    ) -> UncertaintyMetrics:
        """Estimate uncertainty with market condition adjustment."""
        metrics = super().estimate_uncertainty(inputs, method)
        
        # Scale uncertainties based on market conditions
        metrics.epistemic_uncertainty *= self.uncertainty_scaling_factor
        metrics.aleatoric_uncertainty *= self.uncertainty_scaling_factor
        metrics.total_uncertainty *= self.uncertainty_scaling_factor
        
        # Adjust confidence score
        metrics.confidence_score = metrics.confidence_score / (1 + 0.5 * (self.uncertainty_scaling_factor - 1))
        
        return metrics

class BayesianUncertaintyLayer(nn.Module):
    """
    Bayesian layer for uncertainty estimation.
    Implements variational inference for weight uncertainty.
    """
    
    def __init__(self, in_features: int, out_features: int, prior_std: float = 1.0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        
        # Weight parameters
        self.weight_mu = nn.Parameter(torch.randn(out_features, in_features) * 0.1)
        self.weight_rho = nn.Parameter(torch.randn(out_features, in_features) * -3)
        
        # Bias parameters
        self.bias_mu = nn.Parameter(torch.zeros(out_features))
        self.bias_rho = nn.Parameter(torch.randn(out_features) * -3)
        
        # Prior
        self.prior_std = prior_std
        
        # For KL divergence
        self.kl_loss = 0
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Sample weights and biases
        weight_sigma = torch.log1p(torch.exp(self.weight_rho))
        weight_eps = torch.randn_like(weight_sigma)
        weight = self.weight_mu + weight_sigma * weight_eps
        
        bias_sigma = torch.log1p(torch.exp(self.bias_rho))
        bias_eps = torch.randn_like(bias_sigma)
        bias = self.bias_mu + bias_sigma * bias_eps
        
        # Calculate KL divergence
        self.kl_loss = self._kl_divergence(
            self.weight_mu, weight_sigma,
            self.bias_mu, bias_sigma
        )
        
        return F.linear(x, weight, bias)
    
    def _kl_divergence(
        self,
        weight_mu: torch.Tensor,
        weight_sigma: torch.Tensor,
        bias_mu: torch.Tensor,
        bias_sigma: torch.Tensor
    ) -> torch.Tensor:
        """Calculate KL divergence between posterior and prior."""
        # KL divergence for weights
        kl_weight = 0.5 * torch.sum(
            (weight_sigma / self.prior_std) ** 2 +
            (weight_mu / self.prior_std) ** 2 -
            2 * torch.log(weight_sigma / self.prior_std) - 1
        )
        
        # KL divergence for bias
        kl_bias = 0.5 * torch.sum(
            (bias_sigma / self.prior_std) ** 2 +
            (bias_mu / self.prior_std) ** 2 -
            2 * torch.log(bias_sigma / self.prior_std) - 1
        )
        
        return kl_weight + kl_bias

class ConfidenceScorer:
    """
    Advanced confidence scoring for predictions.
    """
    
    def __init__(self, history_window: int = 100):
        self.history_window = history_window
        self.prediction_history = []
        self.error_history = []
        self.confidence_history = []
    
    def update_history(
        self,
        predictions: np.ndarray,
        targets: np.ndarray,
        confidences: np.ndarray
    ):
        """Update prediction history."""
        errors = np.abs(predictions - targets)
        
        self.prediction_history.extend(predictions.tolist())
        self.error_history.extend(errors.tolist())
        self.confidence_history.extend(confidences.tolist())
        
        # Keep only recent history
        if len(self.prediction_history) > self.history_window:
            self.prediction_history = self.prediction_history[-self.history_window:]
            self.error_history = self.error_history[-self.history_window:]
            self.confidence_history = self.confidence_history[-self.history_window:]
    
    def score_confidence(
        self,
        prediction: float,
        uncertainty: float,
        market_state: Optional[Dict] = None
    ) -> float:
        """
        Calculate calibrated confidence score.
        
        Args:
            prediction: Model prediction
            uncertainty: Prediction uncertainty
            market_state: Optional market indicators
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence from uncertainty
        base_confidence = 1 / (1 + uncertainty)
        
        # Historical performance adjustment
        if len(self.error_history) > 10:
            recent_errors = self.error_history[-20:]
            performance_factor = 1 - (np.mean(recent_errors) / (np.std(self.prediction_history) + 1e-8))
            performance_factor = np.clip(performance_factor, 0, 1)
        else:
            performance_factor = 0.5
        
        # Market state adjustment
        market_factor = 1.0
        if market_state is not None:
            # Adjust based on market conditions
            volatility = market_state.get('volatility', 0.15)
            volume_ratio = market_state.get('volume_ratio', 1.0)
            
            # Lower confidence in high volatility
            market_factor *= np.exp(-2 * (volatility - 0.15))
            
            # Higher confidence with normal volume
            market_factor *= (1 + 0.2 * np.clip(volume_ratio - 1, -1, 1))
            
            market_factor = np.clip(market_factor, 0.5, 1.5)
        
        # Combine factors
        final_confidence = base_confidence * performance_factor * market_factor
        
        # Ensure bounds
        return float(np.clip(final_confidence, 0, 1))
    
    def get_confidence_percentile(self, confidence: float) -> float:
        """Get percentile rank of confidence score."""
        if len(self.confidence_history) < 10:
            return 50.0
        
        return float(stats.percentileofscore(self.confidence_history, confidence))
    
    def plot_calibration_curve(self):
        """Plot confidence calibration curve."""
        if len(self.confidence_history) < 50:
            print("Not enough data for calibration curve")
            return
        
        # Bin confidences and calculate accuracy
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        accuracies = []
        avg_confidences = []
        
        for i in range(n_bins):
            mask = (np.array(self.confidence_history) >= bin_edges[i]) & \
                   (np.array(self.confidence_history) < bin_edges[i + 1])
            
            if np.sum(mask) > 0:
                bin_errors = np.array(self.error_history)[mask]
                bin_confidences = np.array(self.confidence_history)[mask]
                
                # Calculate accuracy (1 - normalized error)
                accuracy = 1 - np.mean(bin_errors) / np.max(self.error_history)
                accuracies.append(accuracy)
                avg_confidences.append(np.mean(bin_confidences))
        
        # Plot
        plt.figure(figsize=(8, 6))
        plt.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
        plt.plot(avg_confidences, accuracies, 'bo-', label='Model calibration')
        plt.xlabel('Average Confidence')
        plt.ylabel('Accuracy')
        plt.title('Confidence Calibration Curve')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

def create_uncertainty_config() -> Dict:
    """Create default uncertainty estimation configuration."""
    return {
        'n_mc_samples': 100,
        'confidence_levels': [0.68, 0.95, 0.99],
        'calibration_samples': 1000,
        'market_volatility_window': 20,
        'history_window': 100,
        'uncertainty_beta': 0.5,
        'prior_std': 1.0
    }