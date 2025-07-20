#!/usr/bin/env python3
"""
Production wrapper for Commander Throne using Gunicorn
"""

from commander_throne import app, socketio

if __name__ == '__main__':
    # This file is meant to be run with gunicorn
    # Example: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8899 commander_throne_production:app
    pass