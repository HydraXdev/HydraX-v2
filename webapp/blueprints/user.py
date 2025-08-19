"""
User-related endpoints
War room, stats, notebooks, etc.
"""

import os
import json
import time
import logging
from flask import Blueprint, request, jsonify, render_template_string
from webapp.database import UserOperations, FireOperations, SignalOperations
from webapp.utils import get_user_tier, get_user_balance

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/me')
def war_room():
    """User's personal war room - simplified version"""
    try:
        # Get user_id from various sources
        user_id = request.args.get('user_id')
        if not user_id:
            user_id = request.cookies.get('user_id')
        if not user_id:
            user_id = '7176191872'  # Default to commander
        
        # Get user data
        user_data = UserOperations.get_user(user_id)
        if not user_data:
            # Create default user
            user_data = {'user_id': user_id, 'tier': 'COMMANDER' if user_id == '7176191872' else 'GRUNT', 'xp': 0}
        
        # Get EA instance data
        ea_data = UserOperations.get_user_ea_instance(user_id)
        
        # Get recent fires
        try:
            recent_fires = FireOperations.get_user_fires(user_id, 5)
        except:
            recent_fires = []
        
        # Simple HTML template (would be moved to file in full refactor)
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>BITTEN War Room</title>
            <style>
                body {{ 
                    background: #0a0a0a; 
                    color: #00ff00; 
                    font-family: monospace;
                    padding: 20px;
                }}
                h1 {{ color: #ff0000; }}
                .stats {{ 
                    background: #1a1a1a; 
                    padding: 15px; 
                    margin: 10px 0;
                    border: 1px solid #00ff00;
                }}
                .fire-record {{
                    background: #0f0f0f;
                    padding: 10px;
                    margin: 5px 0;
                    border-left: 3px solid #ff0000;
                }}
            </style>
        </head>
        <body>
            <h1>🎯 BITTEN WAR ROOM</h1>
            <div class="stats">
                <h2>OPERATIVE: {user_id}</h2>
                <p>TIER: {user_data.get('tier', 'GRUNT')}</p>
                <p>XP: {user_data.get('xp', 0)}</p>
                <p>AUTO MODE: {'ENABLED' if user_id == '7176191872' else 'DISABLED'}</p>
            </div>
            
            <div class="stats">
                <h2>💰 ACCOUNT STATUS</h2>
                <p>BALANCE: ${ea_data.get('last_balance', 0) if ea_data else 0:.2f}</p>
                <p>EQUITY: ${ea_data.get('last_equity', 0) if ea_data else 0:.2f}</p>
                <p>BROKER: {ea_data.get('broker', 'NOT CONNECTED') if ea_data else 'NOT CONNECTED'}</p>
            </div>
            
            <div class="stats">
                <h2>🔫 RECENT FIRES</h2>
                {''.join([f'<div class="fire-record">Mission: {f.get("mission_id")} | Status: {f.get("status")} | Ticket: {f.get("ticket", "N/A")}</div>' for f in recent_fires]) if recent_fires else '<p>No recent fires</p>'}
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/brief" style="color: #00ff00;">📋 View Latest Signals</a> | 
                <a href="/hud" style="color: #00ff00;">🎯 Mission HUD</a> | 
                <a href="/tiers" style="color: #00ff00;">⬆️ Upgrade Tier</a>
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(html)
        
    except Exception as e:
        logger.error(f"War room error: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/api/account', methods=['GET'])
def api_account():
    """Get user account data via API"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Get user data
        user_data = UserOperations.get_user(user_id)
        ea_data = UserOperations.get_user_ea_instance(user_id)
        
        return jsonify({
            'success': True,
            'user': user_data or {'user_id': user_id, 'tier': 'GRUNT'},
            'ea_instance': ea_data,
            'balance': ea_data['last_balance'] if ea_data else 0,
            'equity': ea_data['last_equity'] if ea_data else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Account API error: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/api/user/<user_id>/stats', methods=['GET'])
def user_stats(user_id):
    """Get user statistics"""
    try:
        # Get user data
        user_data = UserOperations.get_user(user_id)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Get fire statistics
        fires = FireOperations.get_user_fires(user_id, 100)
        
        # Calculate stats
        total_fires = len(fires)
        successful_fires = sum(1 for f in fires if f.get('status') == 'FILLED')
        failed_fires = sum(1 for f in fires if f.get('status') == 'FAILED')
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'tier': user_data.get('tier', 'GRUNT'),
            'xp': user_data.get('xp', 0),
            'stats': {
                'total_fires': total_fires,
                'successful_fires': successful_fires,
                'failed_fires': failed_fires,
                'success_rate': (successful_fires / total_fires * 100) if total_fires > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"User stats error: {e}")
        return jsonify({'error': str(e)}), 500