"""
Fire command endpoints - CRITICAL INFRASTRUCTURE
Handles trade execution commands through the fire pipeline
"""

import os
import json
import time
import logging
import subprocess
from flask import Blueprint, request, jsonify
from webapp.database import SignalOperations, MissionOperations, FireOperations, UserOperations
from webapp.utils import get_user_tier, get_signal_class, can_user_fire

logger = logging.getLogger(__name__)

fire_bp = Blueprint('fire', __name__)

@fire_bp.route('/api/fire', methods=['POST'])
def fire_mission():
    """
    Fire a mission - execute trade
    CRITICAL: This is the main trade execution endpoint
    """
    try:
        # Get request data
        data = request.get_json()
        mission_id = data.get('mission_id')
        user_id = request.headers.get('X-User-ID')
        
        if not mission_id:
            return jsonify({'error': 'Missing mission_id', 'success': False}), 400
        
        if not user_id:
            return jsonify({'error': 'Missing user ID', 'success': False}), 400
        
        # Load signal from database
        signal_data = SignalOperations.get_signal(mission_id)
        
        if not signal_data:
            return jsonify({'error': 'Signal not found in database', 'success': False}), 404
        
        # Check tier restrictions for FOMO funnel
        # Try to get pattern_type from payload if available
        pattern_type = ''
        if signal_data.get('payload_json'):
            try:
                payload = json.loads(signal_data['payload_json'])
                pattern_type = payload.get('pattern_type', '')
            except:
                pass
        signal_class = get_signal_class(pattern_type)
        
        if not can_user_fire(user_id, signal_class):
            # User needs to upgrade
            tier = get_user_tier(user_id)
            return jsonify({
                'success': False,
                'error': f'Your {tier} tier cannot fire {signal_class} signals',
                'upgrade_required': True,
                'upgrade_url': '/upgrade',
                'signal_class': signal_class,
                'user_tier': tier
            }), 403
        
        # Create fire record
        fire_id = f"{mission_id}_{int(time.time())}"
        FireOperations.create_fire_record({
            'fire_id': fire_id,
            'mission_id': mission_id,
            'user_id': user_id
        })
        
        # Get user's EA instance for proper routing
        ea_instance = UserOperations.get_user_ea_instance(user_id)
        if not ea_instance:
            logger.warning(f"No EA instance found for user {user_id}")
            target_uuid = 'COMMANDER_DEV_001'  # Default fallback
        else:
            target_uuid = ea_instance['target_uuid']
        
        # Calculate position size based on user balance
        balance = ea_instance['last_balance'] if ea_instance else 1000
        sl_pips = abs(signal_data.get('sl', 0) - signal_data.get('entry', 0)) / 0.0001
        
        # Risk 2% of balance
        risk_amount = balance * 0.02
        
        # Calculate lot size (simplified - would need proper pip value calculation)
        lot_size = round(risk_amount / (sl_pips * 10), 2)  # Simplified calculation
        lot_size = min(lot_size, 0.1)  # Cap at 0.1 lots for safety
        
        # Prepare fire command
        fire_command = {
            'fire_id': fire_id,
            'signal_id': mission_id,
            'user_id': user_id,
            'target_uuid': target_uuid,
            'symbol': signal_data['symbol'],
            'direction': signal_data['direction'],
            'entry': signal_data['entry'],
            'sl': signal_data['sl'],
            'tp': signal_data['tp'],
            'lot': lot_size
        }
        
        # Execute through enqueue_fire.py (the official fire pipeline)
        try:
            result = subprocess.run([
                'python3',
                '/root/HydraX-v2/enqueue_fire.py',
                json.dumps(fire_command)
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logger.info(f"✅ Fire command enqueued: {fire_id}")
                FireOperations.update_fire_status(fire_id, 'SENT')
                
                return jsonify({
                    'success': True,
                    'fire_id': fire_id,
                    'message': 'Trade command sent to execution engine',
                    'lot_size': lot_size,
                    'target_uuid': target_uuid
                }), 200
            else:
                logger.error(f"Fire command failed: {result.stderr}")
                FireOperations.update_fire_status(fire_id, 'FAILED')
                
                return jsonify({
                    'success': False,
                    'error': 'Failed to execute trade command',
                    'details': result.stderr
                }), 500
                
        except subprocess.TimeoutExpired:
            logger.error("Fire command timed out")
            FireOperations.update_fire_status(fire_id, 'TIMEOUT')
            
            return jsonify({
                'success': False,
                'error': 'Trade command timed out'
            }), 500
            
        except Exception as e:
            logger.error(f"Fire execution error: {e}")
            FireOperations.update_fire_status(fire_id, 'ERROR')
            
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Fire endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@fire_bp.route('/api/mission-status/<signal_id>', methods=['GET'])
def mission_status(signal_id):
    """Get status of a mission/signal"""
    try:
        # Try to get mission from database
        mission = MissionOperations.get_mission(signal_id)
        
        if mission:
            return jsonify({
                'success': True,
                'mission_id': mission['mission_id'],
                'status': mission['status'],
                'expires_at': mission['expires_at'],
                'signal_id': mission['signal_id']
            }), 200
        
        # Check if signal exists
        signal = SignalOperations.get_signal(signal_id)
        if signal:
            return jsonify({
                'success': True,
                'signal_id': signal_id,
                'status': 'AVAILABLE',
                'signal': signal
            }), 200
        
        return jsonify({
            'success': False,
            'error': 'Mission/Signal not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Mission status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500