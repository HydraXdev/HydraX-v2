"""
Training Script for Market Prediction Transformer

This module implements the training loop with validation, early stopping,
and model checkpointing.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import ReduceLROnPlateau, CosineAnnealingWarmRestarts
import numpy as np
from typing import Dict, Tuple, Optional, List
import os
import json
from datetime import datetime
import wandb
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


class ProbabilisticLoss(nn.Module):
    """Custom loss function for probabilistic predictions with uncertainty."""
    
    def __init__(self, beta: float = 0.5):
        super().__init__()
        self.beta = beta
    
    def forward(
        self, 
        predictions: torch.Tensor,
        uncertainty: torch.Tensor,
        targets: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute negative log-likelihood for Gaussian distribution.
        
        Args:
            predictions: Mean predictions
            uncertainty: Predicted variance
            targets: True values
        """
        # Add small epsilon to avoid log(0)
        uncertainty = uncertainty + 1e-6
        
        # Negative log-likelihood
        nll = 0.5 * (torch.log(uncertainty) + (targets - predictions) ** 2 / uncertainty)
        
        # Add regularization term to prevent uncertainty collapse
        reg_term = self.beta * torch.log(uncertainty)
        
        return (nll - reg_term).mean()


class MarketPredictionTrainer:
    """Trainer class for market prediction transformer."""
    
    def __init__(
        self,
        model: nn.Module,
        device: torch.device,
        config: Dict,
        use_wandb: bool = True
    ):
        self.model = model.to(device)
        self.device = device
        self.config = config
        self.use_wandb = use_wandb
        
        # Initialize optimizers and schedulers
        self.optimizer = self._get_optimizer()
        self.scheduler = self._get_scheduler()
        
        # Loss functions
        self.prediction_loss = ProbabilisticLoss(beta=config.get('uncertainty_beta', 0.5))
        self.mse_loss = nn.MSELoss()
        self.mae_loss = nn.L1Loss()
        
        # Training state
        self.current_epoch = 0
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_metrics': [],
            'val_metrics': []
        }
        
        # Create checkpoint directory
        self.checkpoint_dir = Path(config.get('checkpoint_dir', 'checkpoints'))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize wandb if requested
        if self.use_wandb:
            wandb.init(
                project=config.get('wandb_project', 'market-transformer'),
                config=config,
                name=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
    
    def _get_optimizer(self) -> optim.Optimizer:
        """Get optimizer based on config."""
        opt_config = self.config.get('optimizer', {})
        opt_type = opt_config.get('type', 'adam')
        
        if opt_type == 'adam':
            return optim.Adam(
                self.model.parameters(),
                lr=opt_config.get('lr', 1e-4),
                betas=opt_config.get('betas', (0.9, 0.999)),
                weight_decay=opt_config.get('weight_decay', 1e-5)
            )
        elif opt_type == 'adamw':
            return optim.AdamW(
                self.model.parameters(),
                lr=opt_config.get('lr', 1e-4),
                weight_decay=opt_config.get('weight_decay', 0.01)
            )
        elif opt_type == 'sgd':
            return optim.SGD(
                self.model.parameters(),
                lr=opt_config.get('lr', 0.01),
                momentum=opt_config.get('momentum', 0.9),
                weight_decay=opt_config.get('weight_decay', 1e-5)
            )
        else:
            raise ValueError(f"Unknown optimizer type: {opt_type}")
    
    def _get_scheduler(self) -> Optional[object]:
        """Get learning rate scheduler based on config."""
        sched_config = self.config.get('scheduler', {})
        sched_type = sched_config.get('type', 'reduce_on_plateau')
        
        if sched_type == 'reduce_on_plateau':
            return ReduceLROnPlateau(
                self.optimizer,
                mode='min',
                factor=sched_config.get('factor', 0.5),
                patience=sched_config.get('patience', 10),
                min_lr=sched_config.get('min_lr', 1e-7)
            )
        elif sched_type == 'cosine_annealing':
            return CosineAnnealingWarmRestarts(
                self.optimizer,
                T_0=sched_config.get('T_0', 10),
                T_mult=sched_config.get('T_mult', 2)
            )
        elif sched_type == 'none':
            return None
        else:
            raise ValueError(f"Unknown scheduler type: {sched_type}")
    
    def train_epoch(self, train_loader: DataLoader) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        total_pred_loss = 0.0
        total_mse = 0.0
        total_mae = 0.0
        n_batches = 0
        
        with tqdm(train_loader, desc=f"Training Epoch {self.current_epoch}") as pbar:
            for batch_idx, (sequences, targets) in enumerate(pbar):
                sequences = sequences.to(self.device)
                targets = targets.to(self.device)
                
                # Forward pass
                self.optimizer.zero_grad()
                outputs = self.model(sequences)
                
                # Compute losses
                pred_loss = self.prediction_loss(
                    outputs['predictions'],
                    outputs['uncertainty'],
                    targets
                )
                
                # Additional metrics
                with torch.no_grad():
                    mse = self.mse_loss(outputs['predictions'], targets)
                    mae = self.mae_loss(outputs['predictions'], targets)
                
                # Total loss
                loss = pred_loss
                
                # Backward pass
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 
                    self.config.get('gradient_clip', 1.0)
                )
                
                self.optimizer.step()
                
                # Update statistics
                total_loss += loss.item()
                total_pred_loss += pred_loss.item()
                total_mse += mse.item()
                total_mae += mae.item()
                n_batches += 1
                
                # Update progress bar
                pbar.set_postfix({
                    'loss': f"{loss.item():.4f}",
                    'mse': f"{mse.item():.4f}",
                    'mae': f"{mae.item():.4f}"
                })
                
                # Log to wandb
                if self.use_wandb and batch_idx % 10 == 0:
                    wandb.log({
                        'train/batch_loss': loss.item(),
                        'train/batch_mse': mse.item(),
                        'train/batch_mae': mae.item(),
                        'train/learning_rate': self.optimizer.param_groups[0]['lr']
                    })
        
        metrics = {
            'loss': total_loss / n_batches,
            'pred_loss': total_pred_loss / n_batches,
            'mse': total_mse / n_batches,
            'mae': total_mae / n_batches,
            'rmse': np.sqrt(total_mse / n_batches)
        }
        
        return metrics
    
    def validate(self, val_loader: DataLoader) -> Dict[str, float]:
        """Validate the model."""
        self.model.eval()
        total_loss = 0.0
        total_pred_loss = 0.0
        total_mse = 0.0
        total_mae = 0.0
        all_predictions = []
        all_targets = []
        all_uncertainties = []
        all_confidences = []
        n_batches = 0
        
        with torch.no_grad():
            with tqdm(val_loader, desc="Validation") as pbar:
                for sequences, targets in pbar:
                    sequences = sequences.to(self.device)
                    targets = targets.to(self.device)
                    
                    # Forward pass
                    outputs = self.model(sequences)
                    
                    # Compute losses
                    pred_loss = self.prediction_loss(
                        outputs['predictions'],
                        outputs['uncertainty'],
                        targets
                    )
                    mse = self.mse_loss(outputs['predictions'], targets)
                    mae = self.mae_loss(outputs['predictions'], targets)
                    
                    # Total loss
                    loss = pred_loss
                    
                    # Update statistics
                    total_loss += loss.item()
                    total_pred_loss += pred_loss.item()
                    total_mse += mse.item()
                    total_mae += mae.item()
                    n_batches += 1
                    
                    # Collect predictions for analysis
                    all_predictions.append(outputs['predictions'].cpu())
                    all_targets.append(targets.cpu())
                    all_uncertainties.append(outputs['uncertainty'].cpu())
                    all_confidences.append(outputs['confidence'].cpu())
                    
                    # Update progress bar
                    pbar.set_postfix({
                        'loss': f"{loss.item():.4f}",
                        'mse': f"{mse.item():.4f}",
                        'mae': f"{mae.item():.4f}"
                    })
        
        # Concatenate all predictions
        all_predictions = torch.cat(all_predictions, dim=0)
        all_targets = torch.cat(all_targets, dim=0)
        all_uncertainties = torch.cat(all_uncertainties, dim=0)
        all_confidences = torch.cat(all_confidences, dim=0)
        
        # Calculate additional metrics
        metrics = {
            'loss': total_loss / n_batches,
            'pred_loss': total_pred_loss / n_batches,
            'mse': total_mse / n_batches,
            'mae': total_mae / n_batches,
            'rmse': np.sqrt(total_mse / n_batches)
        }
        
        # Calculate uncertainty calibration metrics
        calibration_metrics = self._calculate_calibration_metrics(
            all_predictions, all_targets, all_uncertainties
        )
        metrics.update(calibration_metrics)
        
        # Calculate confidence correlation
        prediction_errors = torch.abs(all_predictions - all_targets).mean(dim=1)
        confidence_correlation = torch.corrcoef(
            torch.stack([prediction_errors, all_confidences.squeeze()])
        )[0, 1].item()
        metrics['confidence_correlation'] = confidence_correlation
        
        return metrics
    
    def _calculate_calibration_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        uncertainties: torch.Tensor
    ) -> Dict[str, float]:
        """Calculate uncertainty calibration metrics."""
        # Standard deviations from uncertainties
        std_devs = torch.sqrt(uncertainties)
        
        # Z-scores
        z_scores = (targets - predictions) / std_devs
        
        # Check what percentage fall within confidence intervals
        within_1_std = (torch.abs(z_scores) <= 1).float().mean().item()
        within_2_std = (torch.abs(z_scores) <= 2).float().mean().item()
        within_3_std = (torch.abs(z_scores) <= 3).float().mean().item()
        
        # Expected percentages for normal distribution
        expected_1_std = 0.6827
        expected_2_std = 0.9545
        expected_3_std = 0.9973
        
        # Calibration errors
        calibration_error_1 = abs(within_1_std - expected_1_std)
        calibration_error_2 = abs(within_2_std - expected_2_std)
        calibration_error_3 = abs(within_3_std - expected_3_std)
        
        return {
            'within_1_std': within_1_std,
            'within_2_std': within_2_std,
            'within_3_std': within_3_std,
            'calibration_error_1': calibration_error_1,
            'calibration_error_2': calibration_error_2,
            'calibration_error_3': calibration_error_3,
            'avg_calibration_error': (calibration_error_1 + calibration_error_2 + calibration_error_3) / 3
        }
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        n_epochs: int,
        patience: int = 20
    ):
        """Complete training loop."""
        print(f"Starting training for {n_epochs} epochs...")
        
        for epoch in range(n_epochs):
            self.current_epoch = epoch + 1
            
            # Train
            train_metrics = self.train_epoch(train_loader)
            self.training_history['train_loss'].append(train_metrics['loss'])
            self.training_history['train_metrics'].append(train_metrics)
            
            # Validate
            val_metrics = self.validate(val_loader)
            self.training_history['val_loss'].append(val_metrics['loss'])
            self.training_history['val_metrics'].append(val_metrics)
            
            # Log metrics
            print(f"\nEpoch {self.current_epoch} Summary:")
            print(f"Train Loss: {train_metrics['loss']:.4f}, Val Loss: {val_metrics['loss']:.4f}")
            print(f"Train RMSE: {train_metrics['rmse']:.4f}, Val RMSE: {val_metrics['rmse']:.4f}")
            print(f"Calibration Error: {val_metrics['avg_calibration_error']:.4f}")
            
            if self.use_wandb:
                wandb.log({
                    'epoch': self.current_epoch,
                    'train/epoch_loss': train_metrics['loss'],
                    'train/epoch_rmse': train_metrics['rmse'],
                    'val/epoch_loss': val_metrics['loss'],
                    'val/epoch_rmse': val_metrics['rmse'],
                    'val/calibration_error': val_metrics['avg_calibration_error'],
                    'val/confidence_correlation': val_metrics['confidence_correlation']
                })
            
            # Learning rate scheduling
            if self.scheduler is not None:
                if isinstance(self.scheduler, ReduceLROnPlateau):
                    self.scheduler.step(val_metrics['loss'])
                else:
                    self.scheduler.step()
            
            # Early stopping and checkpointing
            if val_metrics['loss'] < self.best_val_loss:
                self.best_val_loss = val_metrics['loss']
                self.patience_counter = 0
                self._save_checkpoint(is_best=True)
                print("✓ New best model saved!")
            else:
                self.patience_counter += 1
                if self.patience_counter >= patience:
                    print(f"\nEarly stopping triggered after {patience} epochs without improvement.")
                    break
            
            # Regular checkpoint
            if self.current_epoch % self.config.get('checkpoint_frequency', 10) == 0:
                self._save_checkpoint(is_best=False)
        
        print("\nTraining completed!")
        self._plot_training_history()
        
        if self.use_wandb:
            wandb.finish()
    
    def _save_checkpoint(self, is_best: bool = False):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': self.current_epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            'best_val_loss': self.best_val_loss,
            'training_history': self.training_history,
            'config': self.config
        }
        
        if is_best:
            path = self.checkpoint_dir / 'best_model.pt'
        else:
            path = self.checkpoint_dir / f'checkpoint_epoch_{self.current_epoch}.pt'
        
        torch.save(checkpoint, path)
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load model from checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        if self.scheduler and checkpoint['scheduler_state_dict']:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        self.current_epoch = checkpoint['epoch']
        self.best_val_loss = checkpoint['best_val_loss']
        self.training_history = checkpoint['training_history']
        
        print(f"Loaded checkpoint from epoch {self.current_epoch}")
    
    def _plot_training_history(self):
        """Plot training history."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Loss curves
        axes[0, 0].plot(self.training_history['train_loss'], label='Train')
        axes[0, 0].plot(self.training_history['val_loss'], label='Validation')
        axes[0, 0].set_title('Loss History')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # RMSE curves
        train_rmse = [m['rmse'] for m in self.training_history['train_metrics']]
        val_rmse = [m['rmse'] for m in self.training_history['val_metrics']]
        axes[0, 1].plot(train_rmse, label='Train')
        axes[0, 1].plot(val_rmse, label='Validation')
        axes[0, 1].set_title('RMSE History')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('RMSE')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # Calibration error
        cal_errors = [m['avg_calibration_error'] for m in self.training_history['val_metrics']]
        axes[1, 0].plot(cal_errors)
        axes[1, 0].set_title('Calibration Error History')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Average Calibration Error')
        axes[1, 0].grid(True)
        
        # Confidence correlation
        conf_corr = [m['confidence_correlation'] for m in self.training_history['val_metrics']]
        axes[1, 1].plot(conf_corr)
        axes[1, 1].set_title('Confidence Correlation History')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('Correlation')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(self.checkpoint_dir / 'training_history.png', dpi=300)
        plt.close()


def create_training_config() -> Dict:
    """Create default training configuration."""
    return {
        'model': {
            'input_dim': 50,  # Number of features
            'd_model': 512,
            'n_heads': 8,
            'n_layers': 6,
            'd_ff': 2048,
            'max_seq_len': 100,
            'n_outputs': 5,  # Prediction horizon
            'dropout': 0.1
        },
        'training': {
            'batch_size': 32,
            'n_epochs': 100,
            'patience': 20,
            'gradient_clip': 1.0,
            'uncertainty_beta': 0.5
        },
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
        },
        'data': {
            'sequence_length': 60,
            'prediction_horizon': 5,
            'normalization_method': 'robust',
            'train_split': 0.7,
            'val_split': 0.15
        },
        'checkpoint_dir': 'checkpoints',
        'checkpoint_frequency': 10,
        'wandb_project': 'market-transformer',
        'use_wandb': True
    }