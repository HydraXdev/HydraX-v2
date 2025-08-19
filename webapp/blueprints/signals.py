"""
Signal-related endpoints
Handles signal reception, storage, and retrieval
"""

import os
import json
import time
import logging
from flask import Blueprint, request, jsonify, redirect
from webapp.database import SignalOperations, MissionOperations
from webapp.utils import pip_size, calculate_sl_tp, get_bitten_db

logger = logging.getLogger(__name__)

signals_bp = Blueprint('signals', __name__)

@signals_bp.route('/api/signals', methods=['GET', 'POST'])
def api_signals():
    """Handle signal reception and retrieval"""
    try:
        if request.method == 'POST':
            # Receive new signal from Elite Guard
            signal_data = request.get_json()
            
            if not signal_data:
                return jsonify({'error': 'No signal data provided'}), 400
            
            # Extract signal info
            signal_id = signal_data.get('signal_id')
            if not signal_id:
                return jsonify({'error': 'Missing signal_id'}), 400
            
            # Save to database
            try:
                SignalOperations.save_signal(signal_data)
                logger.info(f"✅ Signal saved: {signal_id}")
            except Exception as e:
                logger.error(f"Failed to save signal: {e}")
                return jsonify({'error': 'Database error'}), 500
            
            # Create mission file for legacy compatibility
            mission_dir = '/root/HydraX-v2/missions'
            os.makedirs(mission_dir, exist_ok=True)
            
            mission_file = f'{mission_dir}/{signal_id}.json'
            with open(mission_file, 'w') as f:
                json.dump(signal_data, f, indent=2)
            
            # Log to truth system if available
            try:
                from black_box_complete_truth_system import get_truth_system
                truth_system = get_truth_system()
                signal_data = truth_system.log_signal_generation(signal_data)
                logger.info(f"📊 Truth tracking: Signal {signal_id} logged")
            except Exception as e:
                logger.debug(f"Truth system not available: {e}")
            
            return jsonify({
                'success': True,
                'signal_id': signal_id,
                'message': 'Signal received and stored'
            }), 200
            
        else:  # GET request
            # Retrieve recent signals
            limit = request.args.get('limit', 10, type=int)
            signals = SignalOperations.get_recent_signals(limit)
            
            return jsonify({
                'success': True,
                'signals': signals,
                'count': len(signals)
            }), 200
            
    except Exception as e:
        logger.error(f"Signal API error: {e}")
        return jsonify({'error': str(e)}), 500

# /brief route moved to hud.py blueprint

@signals_bp.route('/api/venom_signals')
def venom_signals():
    """Legacy endpoint for venom signals - now returns Elite Guard signals"""
    try:
        # Get recent signals from database
        signals = SignalOperations.get_recent_signals(20)
        
        # Format for legacy compatibility
        formatted = []
        for sig in signals:
            formatted.append({
                'signal_id': sig['signal_id'],
                'symbol': sig['symbol'],
                'direction': sig['direction'],
                'entry_price': sig['entry'],
                'sl': sig['sl'],
                'tp': sig['tp'],
                'confidence': sig['confidence'],
                'pattern_type': sig.get('pattern_type', 'UNKNOWN'),
                'timestamp': sig['created_at']
            })
        
        return jsonify({
            'signals': formatted,
            'count': len(formatted),
            'source': 'elite_guard'  # Indicate actual source
        }), 200
        
    except Exception as e:
        logger.error(f"Venom signals error: {e}")
        return jsonify({'error': str(e), 'signals': []}), 200