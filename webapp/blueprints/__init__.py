"""
Webapp blueprints module
"""

from .health import health_bp
from .signals import signals_bp
from .fire import fire_bp
from .user import user_bp

__all__ = ['health_bp', 'signals_bp', 'fire_bp', 'user_bp']