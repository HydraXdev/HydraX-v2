"""
Model Versioning and Update System

This module implements a comprehensive model versioning system with
automated updates, A/B testing, and performance tracking.
"""

import os
import json
import shutil
import hashlib
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from dataclasses import dataclass, asdict
import git
import mlflow
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()


@dataclass
class ModelVersion:
    """Model version metadata."""
    version_id: str
    model_hash: str
    created_at: datetime
    trained_epochs: int
    training_config: Dict
    performance_metrics: Dict
    deployment_status: str  # 'staging', 'production', 'archived'
    notes: Optional[str] = None
    parent_version: Optional[str] = None


@dataclass
class UpdatePolicy:
    """Policy for automated model updates."""
    min_improvement: float = 0.01  # Minimum performance improvement
    min_samples: int = 1000  # Minimum evaluation samples
    max_degradation: float = 0.05  # Maximum allowed degradation
    rollback_threshold: float = 0.1  # Threshold for automatic rollback
    update_frequency: timedelta = timedelta(days=7)
    a_b_test_duration: timedelta = timedelta(days=3)
    a_b_test_traffic_split: float = 0.1  # Traffic percentage for new model


class ModelVersionTable(Base):
    """SQLAlchemy model for version tracking."""
    __tablename__ = 'model_versions'
    
    version_id = Column(String, primary_key=True)
    model_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    trained_epochs = Column(Integer, nullable=False)
    training_config = Column(String, nullable=False)  # JSON
    performance_metrics = Column(String, nullable=False)  # JSON
    deployment_status = Column(String, nullable=False)
    notes = Column(String)
    parent_version = Column(String)
    
    # Performance tracking
    production_mae = Column(Float)
    production_rmse = Column(Float)
    production_samples = Column(Integer, default=0)
    last_evaluated = Column(DateTime)


class ModelVersionManager:
    """
    Comprehensive model version management system.
    
    Features:
    - Version tracking with Git integration
    - Automated performance monitoring
    - A/B testing framework
    - Rollback capabilities
    - MLflow integration
    """
    
    def __init__(
        self,
        models_dir: str,
        db_url: str = "sqlite:///model_versions.db",
        use_mlflow: bool = True,
        use_git: bool = True
    ):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Database setup
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # MLflow setup
        self.use_mlflow = use_mlflow
        if use_mlflow:
            mlflow.set_tracking_uri(str(self.models_dir / "mlruns"))
            mlflow.set_experiment("market_prediction")
        
        # Git setup
        self.use_git = use_git
        if use_git:
            try:
                self.repo = git.Repo(self.models_dir)
            except git.InvalidGitRepositoryError:
                self.repo = git.Repo.init(self.models_dir)
        
        # Current versions
        self.production_version = self._get_production_version()
        self.staging_versions = self._get_staging_versions()
        
        # Update policy
        self.update_policy = UpdatePolicy()
        
        # Performance tracking
        self.performance_buffer = {
            'predictions': [],
            'targets': [],
            'timestamps': []
        }
    
    def _get_production_version(self) -> Optional[str]:
        """Get current production model version."""
        session = self.Session()
        try:
            result = session.query(ModelVersionTable).filter_by(
                deployment_status='production'
            ).first()
            return result.version_id if result else None
        finally:
            session.close()
    
    def _get_staging_versions(self) -> List[str]:
        """Get staging model versions."""
        session = self.Session()
        try:
            results = session.query(ModelVersionTable).filter_by(
                deployment_status='staging'
            ).all()
            return [r.version_id for r in results]
        finally:
            session.close()
    
    def register_model(
        self,
        model: nn.Module,
        training_config: Dict,
        performance_metrics: Dict,
        preprocessor: Any,
        notes: Optional[str] = None,
        parent_version: Optional[str] = None
    ) -> str:
        """
        Register a new model version.
        
        Args:
            model: Trained model
            training_config: Training configuration
            performance_metrics: Validation metrics
            preprocessor: Data preprocessor
            notes: Optional notes about the version
            parent_version: Parent model version (for incremental training)
            
        Returns:
            Version ID
        """
        # Generate version ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_hash = self._compute_model_hash(model)
        version_id = f"v_{timestamp}_{model_hash[:8]}"
        
        # Create version directory
        version_dir = self.models_dir / version_id
        version_dir.mkdir(exist_ok=True)
        
        # Save model and preprocessor
        model_path = version_dir / "model.pt"
        preprocessor_path = version_dir / "preprocessor.pkl"
        
        torch.save({
            'model_state_dict': model.state_dict(),
            'training_config': training_config,
            'performance_metrics': performance_metrics,
            'version': version_id,
            'created_at': datetime.now().isoformat()
        }, model_path)
        
        with open(preprocessor_path, 'wb') as f:
            pickle.dump(preprocessor, f)
        
        # Save configuration
        config_path = version_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({
                'version_id': version_id,
                'model_hash': model_hash,
                'created_at': datetime.now().isoformat(),
                'training_config': training_config,
                'performance_metrics': performance_metrics,
                'notes': notes,
                'parent_version': parent_version
            }, f, indent=2)
        
        # Create version record
        version = ModelVersion(
            version_id=version_id,
            model_hash=model_hash,
            created_at=datetime.now(),
            trained_epochs=training_config.get('epochs', 0),
            training_config=training_config,
            performance_metrics=performance_metrics,
            deployment_status='staging',
            notes=notes,
            parent_version=parent_version
        )
        
        # Save to database
        session = self.Session()
        try:
            db_version = ModelVersionTable(
                version_id=version_id,
                model_hash=model_hash,
                created_at=version.created_at,
                trained_epochs=version.trained_epochs,
                training_config=json.dumps(training_config),
                performance_metrics=json.dumps(performance_metrics),
                deployment_status='staging',
                notes=notes,
                parent_version=parent_version
            )
            session.add(db_version)
            session.commit()
        finally:
            session.close()
        
        # MLflow tracking
        if self.use_mlflow:
            with mlflow.start_run(run_name=version_id):
                mlflow.log_params(training_config)
                mlflow.log_metrics(performance_metrics)
                mlflow.pytorch.log_model(model, "model")
                if notes:
                    mlflow.set_tag("notes", notes)
        
        # Git commit
        if self.use_git:
            self.repo.index.add([str(version_dir)])
            self.repo.index.commit(f"Add model version {version_id}")
        
        logger.info(f"Registered model version: {version_id}")
        return version_id
    
    def _compute_model_hash(self, model: nn.Module) -> str:
        """Compute hash of model weights."""
        hasher = hashlib.sha256()
        for param in model.parameters():
            hasher.update(param.data.cpu().numpy().tobytes())
        return hasher.hexdigest()
    
    def promote_to_production(
        self,
        version_id: str,
        force: bool = False
    ) -> bool:
        """
        Promote a model version to production.
        
        Args:
            version_id: Version to promote
            force: Force promotion without checks
            
        Returns:
            Success status
        """
        session = self.Session()
        try:
            # Get version
            version = session.query(ModelVersionTable).filter_by(
                version_id=version_id
            ).first()
            
            if not version:
                logger.error(f"Version {version_id} not found")
                return False
            
            if version.deployment_status != 'staging' and not force:
                logger.error(f"Version {version_id} is not in staging")
                return False
            
            # Performance check
            if not force and not self._check_promotion_criteria(version_id):
                logger.warning(f"Version {version_id} does not meet promotion criteria")
                return False
            
            # Archive current production version
            current_prod = session.query(ModelVersionTable).filter_by(
                deployment_status='production'
            ).first()
            
            if current_prod:
                current_prod.deployment_status = 'archived'
                logger.info(f"Archived previous production version: {current_prod.version_id}")
            
            # Promote new version
            version.deployment_status = 'production'
            session.commit()
            
            self.production_version = version_id
            logger.info(f"Promoted {version_id} to production")
            
            return True
            
        finally:
            session.close()
    
    def _check_promotion_criteria(self, version_id: str) -> bool:
        """Check if version meets promotion criteria."""
        session = self.Session()
        try:
            version = session.query(ModelVersionTable).filter_by(
                version_id=version_id
            ).first()
            
            if not version.production_samples or version.production_samples < self.update_policy.min_samples:
                logger.info(f"Insufficient evaluation samples: {version.production_samples}")
                return False
            
            # Compare with current production
            current_prod = session.query(ModelVersionTable).filter_by(
                deployment_status='production'
            ).first()
            
            if current_prod and current_prod.production_mae:
                improvement = (current_prod.production_mae - version.production_mae) / current_prod.production_mae
                
                if improvement < self.update_policy.min_improvement:
                    logger.info(f"Insufficient improvement: {improvement:.2%}")
                    return False
                
                if version.production_mae > current_prod.production_mae * (1 + self.update_policy.max_degradation):
                    logger.warning(f"Performance degradation exceeds threshold")
                    return False
            
            return True
            
        finally:
            session.close()
    
    def rollback(self, target_version: Optional[str] = None) -> bool:
        """
        Rollback to a previous version.
        
        Args:
            target_version: Specific version to rollback to (or previous production)
            
        Returns:
            Success status
        """
        session = self.Session()
        try:
            if target_version:
                # Rollback to specific version
                target = session.query(ModelVersionTable).filter_by(
                    version_id=target_version
                ).first()
            else:
                # Rollback to previous production version
                target = session.query(ModelVersionTable).filter_by(
                    deployment_status='archived'
                ).order_by(ModelVersionTable.last_evaluated.desc()).first()
            
            if not target:
                logger.error("No version available for rollback")
                return False
            
            # Current production to staging
            current_prod = session.query(ModelVersionTable).filter_by(
                deployment_status='production'
            ).first()
            
            if current_prod:
                current_prod.deployment_status = 'staging'
            
            # Target to production
            target.deployment_status = 'production'
            session.commit()
            
            self.production_version = target.version_id
            logger.info(f"Rolled back to version: {target.version_id}")
            
            return True
            
        finally:
            session.close()
    
    def update_performance_metrics(
        self,
        version_id: str,
        predictions: np.ndarray,
        targets: np.ndarray
    ):
        """Update real-time performance metrics for a version."""
        session = self.Session()
        try:
            version = session.query(ModelVersionTable).filter_by(
                version_id=version_id
            ).first()
            
            if not version:
                return
            
            # Calculate metrics
            mae = np.mean(np.abs(predictions - targets))
            rmse = np.sqrt(np.mean((predictions - targets) ** 2))
            
            # Update running average
            if version.production_samples > 0:
                alpha = min(0.1, 100 / version.production_samples)  # Exponential moving average
                version.production_mae = (1 - alpha) * version.production_mae + alpha * mae
                version.production_rmse = (1 - alpha) * version.production_rmse + alpha * rmse
            else:
                version.production_mae = mae
                version.production_rmse = rmse
            
            version.production_samples += len(predictions)
            version.last_evaluated = datetime.now()
            
            session.commit()
            
            # Check for automatic rollback
            if version_id == self.production_version:
                self._check_rollback_criteria(version)
                
        finally:
            session.close()
    
    def _check_rollback_criteria(self, version: ModelVersionTable):
        """Check if automatic rollback is needed."""
        session = self.Session()
        try:
            # Get previous production version
            prev_prod = session.query(ModelVersionTable).filter(
                ModelVersionTable.deployment_status == 'archived',
                ModelVersionTable.production_mae.isnot(None)
            ).order_by(ModelVersionTable.last_evaluated.desc()).first()
            
            if prev_prod and prev_prod.production_mae:
                degradation = (version.production_mae - prev_prod.production_mae) / prev_prod.production_mae
                
                if degradation > self.update_policy.rollback_threshold:
                    logger.warning(f"Performance degradation {degradation:.2%} exceeds rollback threshold")
                    self.rollback()
                    
        finally:
            session.close()
    
    def start_ab_test(
        self,
        challenger_version: str,
        traffic_split: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Start A/B test between production and challenger.
        
        Args:
            challenger_version: Version to test
            traffic_split: Traffic percentage for challenger
            
        Returns:
            Traffic split configuration
        """
        if traffic_split is None:
            traffic_split = self.update_policy.a_b_test_traffic_split
        
        session = self.Session()
        try:
            # Ensure challenger is in staging
            challenger = session.query(ModelVersionTable).filter_by(
                version_id=challenger_version
            ).first()
            
            if not challenger or challenger.deployment_status != 'staging':
                raise ValueError(f"Invalid challenger version: {challenger_version}")
            
            # Create A/B test configuration
            ab_config = {
                'production': self.production_version,
                'challenger': challenger_version,
                'traffic_split': {
                    self.production_version: 1 - traffic_split,
                    challenger_version: traffic_split
                },
                'start_time': datetime.now().isoformat(),
                'end_time': (datetime.now() + self.update_policy.a_b_test_duration).isoformat()
            }
            
            # Save configuration
            config_path = self.models_dir / "ab_test_config.json"
            with open(config_path, 'w') as f:
                json.dump(ab_config, f, indent=2)
            
            logger.info(f"Started A/B test: {self.production_version} vs {challenger_version}")
            return ab_config['traffic_split']
            
        finally:
            session.close()
    
    def get_ab_test_results(self) -> Optional[Dict]:
        """Get current A/B test results."""
        config_path = self.models_dir / "ab_test_config.json"
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            ab_config = json.load(f)
        
        # Check if test is still active
        end_time = datetime.fromisoformat(ab_config['end_time'])
        if datetime.now() < end_time:
            status = 'active'
        else:
            status = 'completed'
        
        session = self.Session()
        try:
            results = {'status': status, 'config': ab_config, 'metrics': {}}
            
            for version in [ab_config['production'], ab_config['challenger']]:
                version_data = session.query(ModelVersionTable).filter_by(
                    version_id=version
                ).first()
                
                if version_data:
                    results['metrics'][version] = {
                        'mae': version_data.production_mae,
                        'rmse': version_data.production_rmse,
                        'samples': version_data.production_samples
                    }
            
            # Calculate winner if completed
            if status == 'completed' and len(results['metrics']) == 2:
                prod_mae = results['metrics'][ab_config['production']]['mae']
                chal_mae = results['metrics'][ab_config['challenger']]['mae']
                
                if chal_mae < prod_mae * (1 - self.update_policy.min_improvement):
                    results['winner'] = ab_config['challenger']
                else:
                    results['winner'] = ab_config['production']
            
            return results
            
        finally:
            session.close()
    
    def cleanup_old_versions(self, keep_last_n: int = 10):
        """Clean up old archived versions."""
        session = self.Session()
        try:
            # Get archived versions sorted by date
            archived = session.query(ModelVersionTable).filter_by(
                deployment_status='archived'
            ).order_by(ModelVersionTable.created_at.desc()).all()
            
            # Keep last N versions
            to_delete = archived[keep_last_n:]
            
            for version in to_delete:
                # Delete files
                version_dir = self.models_dir / version.version_id
                if version_dir.exists():
                    shutil.rmtree(version_dir)
                
                # Delete from database
                session.delete(version)
                logger.info(f"Deleted old version: {version.version_id}")
            
            session.commit()
            
        finally:
            session.close()
    
    def export_version_history(self) -> pd.DataFrame:
        """Export version history as DataFrame."""
        session = self.Session()
        try:
            versions = session.query(ModelVersionTable).all()
            
            data = []
            for v in versions:
                data.append({
                    'version_id': v.version_id,
                    'created_at': v.created_at,
                    'deployment_status': v.deployment_status,
                    'trained_epochs': v.trained_epochs,
                    'production_mae': v.production_mae,
                    'production_rmse': v.production_rmse,
                    'production_samples': v.production_samples,
                    'last_evaluated': v.last_evaluated,
                    'parent_version': v.parent_version
                })
            
            return pd.DataFrame(data)
            
        finally:
            session.close()


class AutomatedModelUpdater:
    """
    Automated model update system with continuous learning.
    """
    
    def __init__(
        self,
        version_manager: ModelVersionManager,
        data_source: Any,
        update_schedule: str = 'weekly'
    ):
        self.version_manager = version_manager
        self.data_source = data_source
        self.update_schedule = update_schedule
        
        # Training configuration
        self.base_training_config = {
            'epochs': 50,
            'batch_size': 32,
            'learning_rate': 1e-4,
            'early_stopping_patience': 10
        }
    
    def check_for_updates(self) -> bool:
        """Check if model update is needed."""
        # Get last update time
        current_version = self.version_manager.production_version
        if not current_version:
            return True
        
        session = self.version_manager.Session()
        try:
            version = session.query(ModelVersionTable).filter_by(
                version_id=current_version
            ).first()
            
            if not version:
                return True
            
            # Check update frequency
            time_since_update = datetime.now() - version.created_at
            
            if self.update_schedule == 'daily':
                return time_since_update > timedelta(days=1)
            elif self.update_schedule == 'weekly':
                return time_since_update > timedelta(days=7)
            elif self.update_schedule == 'monthly':
                return time_since_update > timedelta(days=30)
            
            return False
            
        finally:
            session.close()
    
    def perform_update(self) -> Optional[str]:
        """Perform automated model update."""
        logger.info("Starting automated model update")
        
        # Get latest data
        training_data = self.data_source.get_latest_data()
        
        if len(training_data) < 1000:
            logger.warning("Insufficient data for update")
            return None
        
        # Load current production model as starting point
        current_model = self._load_production_model()
        
        # Incremental training
        from ..training.train import MarketPredictionTrainer, create_training_config
        
        config = create_training_config()
        config.update(self.base_training_config)
        
        trainer = MarketPredictionTrainer(
            model=current_model,
            device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
            config=config,
            use_wandb=False
        )
        
        # Train model
        # ... (training logic)
        
        # Register new version
        new_version = self.version_manager.register_model(
            model=current_model,
            training_config=config,
            performance_metrics={'mae': 0.01, 'rmse': 0.02},  # Example metrics
            preprocessor=None,  # Load from current version
            notes="Automated update",
            parent_version=self.version_manager.production_version
        )
        
        # Start A/B test
        self.version_manager.start_ab_test(new_version)
        
        logger.info(f"Created new version: {new_version}")
        return new_version
    
    def _load_production_model(self) -> nn.Module:
        """Load current production model."""
        version_dir = self.version_manager.models_dir / self.version_manager.production_version
        model_path = version_dir / "model.pt"
        
        checkpoint = torch.load(model_path)
        
        # Import model architecture
        from ..models.transformer_architecture import MarketTransformer
        
        model = MarketTransformer(**checkpoint['training_config']['model'])
        model.load_state_dict(checkpoint['model_state_dict'])
        
        return model


def create_versioning_config() -> Dict:
    """Create default versioning configuration."""
    return {
        'models_dir': 'models',
        'db_url': 'sqlite:///model_versions.db',
        'use_mlflow': True,
        'use_git': True,
        'update_policy': {
            'min_improvement': 0.01,
            'min_samples': 1000,
            'max_degradation': 0.05,
            'rollback_threshold': 0.1,
            'update_frequency_days': 7,
            'ab_test_duration_days': 3,
            'ab_test_traffic_split': 0.1
        },
        'cleanup': {
            'keep_last_n_versions': 10,
            'cleanup_frequency_days': 30
        }
    }