#!/usr/bin/env python3
"""
BITTEN Credit Referral Admin API
Admin endpoints for managing the credit referral system
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Optional

from .credit_referral_system import get_credit_referral_system
from .stripe_credit_manager import get_stripe_credit_manager

logger = logging.getLogger(__name__)

# Create Flask blueprint for admin endpoints
credit_admin_bp = Blueprint('credit_admin', __name__)

def require_admin_auth(func):
    """Decorator to require admin authentication"""
    def wrapper(*args, **kwargs):
        # TODO: Implement proper admin authentication
        # For now, check for admin token in headers
        admin_token = request.headers.get('X-Admin-Token')
        if not admin_token or admin_token != 'BITTEN_ADMIN_2025':  # Replace with secure token
            return jsonify({'error': 'Admin authentication required'}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@credit_admin_bp.route('/admin/credits/stats', methods=['GET'])
@require_admin_auth
def get_admin_stats():
    """Get comprehensive referral system statistics"""
    try:
        referral_system = get_credit_referral_system()
        stats = referral_system.get_admin_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/user/<user_id>', methods=['GET'])
@require_admin_auth
def get_user_credits(user_id: str):
    """Get detailed credit information for a specific user"""
    try:
        referral_system = get_credit_referral_system()
        stats = referral_system.get_referral_stats(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting user credits for {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/apply', methods=['POST'])
@require_admin_auth
def manually_apply_credit():
    """Manually apply credit to a user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        user_id = data.get('user_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Manual admin adjustment')
        
        if not user_id or amount is None:
            return jsonify({'error': 'user_id and amount are required'}), 400
        
        if not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({'error': 'amount must be a positive number'}), 400
        
        credit_manager = get_stripe_credit_manager()
        result = credit_manager.manually_apply_credit(user_id, float(amount), reason)
        
        if result['success']:
            logger.info(f"Admin manually applied ${amount} credit to user {user_id}: {reason}")
            return jsonify({
                'success': True,
                'message': f'Applied ${amount} credit to user {user_id}',
                'result': result
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to apply credit')}), 500
        
    except Exception as e:
        logger.error(f"Error manually applying credit: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/revoke', methods=['POST'])
@require_admin_auth
def revoke_credit():
    """Revoke credit from a user (apply negative credit)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        user_id = data.get('user_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Manual admin revocation')
        
        if not user_id or amount is None:
            return jsonify({'error': 'user_id and amount are required'}), 400
        
        if not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({'error': 'amount must be a positive number'}), 400
        
        # Apply negative credit
        credit_manager = get_stripe_credit_manager()
        result = credit_manager.manually_apply_credit(user_id, -float(amount), f"REVOKE: {reason}")
        
        if result['success']:
            logger.info(f"Admin revoked ${amount} credit from user {user_id}: {reason}")
            return jsonify({
                'success': True,
                'message': f'Revoked ${amount} credit from user {user_id}',
                'result': result
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to revoke credit')}), 500
        
    except Exception as e:
        logger.error(f"Error revoking credit: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/top-referrers', methods=['GET'])
@require_admin_auth
def get_top_referrers():
    """Get top referrers leaderboard"""
    try:
        limit = request.args.get('limit', 25, type=int)
        
        referral_system = get_credit_referral_system()
        stats = referral_system.get_admin_stats()
        
        top_referrers = stats.get('top_referrers', [])[:limit]
        
        return jsonify({
            'success': True,
            'top_referrers': top_referrers,
            'total_credits_issued': stats.get('total_credits_issued', 0),
            'total_referrals': stats.get('total_referrals', 0)
        })
        
    except Exception as e:
        logger.error(f"Error getting top referrers: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/pending', methods=['GET'])
@require_admin_auth
def get_pending_credits():
    """Get all pending credits awaiting payment confirmation"""
    try:
        referral_system = get_credit_referral_system()
        
        # Query pending credits directly from database
        import sqlite3
        with sqlite3.connect(referral_system.db_path) as conn:
            cursor = conn.execute("""
                SELECT referrer_id, referred_user_id, referral_code, credit_amount, created_at
                FROM referral_credits 
                WHERE credited = 0 AND credit_amount > 0
                ORDER BY created_at DESC
            """)
            
            pending_credits = []
            for row in cursor.fetchall():
                pending_credits.append({
                    'referrer_id': row[0],
                    'referred_user_id': row[1],
                    'referral_code': row[2],
                    'credit_amount': row[3],
                    'created_at': row[4]
                })
        
        return jsonify({
            'success': True,
            'pending_credits': pending_credits,
            'total_pending': len(pending_credits),
            'total_pending_amount': sum(c['credit_amount'] for c in pending_credits)
        })
        
    except Exception as e:
        logger.error(f"Error getting pending credits: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/force-confirm', methods=['POST'])
@require_admin_auth
def force_confirm_payment():
    """Force confirm payment for a pending referral credit"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        referred_user_id = data.get('referred_user_id')
        invoice_id = data.get('invoice_id', 'ADMIN_FORCE_CONFIRM')
        
        if not referred_user_id:
            return jsonify({'error': 'referred_user_id is required'}), 400
        
        referral_system = get_credit_referral_system()
        referrer_id = referral_system.confirm_payment_and_apply_credit(referred_user_id, invoice_id)
        
        if referrer_id:
            logger.info(f"Admin force-confirmed credit for {referrer_id} from referred user {referred_user_id}")
            return jsonify({
                'success': True,
                'message': f'Force-confirmed credit for referrer {referrer_id}',
                'referrer_id': referrer_id,
                'referred_user_id': referred_user_id
            })
        else:
            return jsonify({'error': 'No pending credit found for this user'}), 404
        
    except Exception as e:
        logger.error(f"Error force-confirming payment: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/search', methods=['GET'])
@require_admin_auth
def search_credits():
    """Search credit transactions"""
    try:
        user_id = request.args.get('user_id')
        referral_code = request.args.get('referral_code')
        limit = request.args.get('limit', 50, type=int)
        
        referral_system = get_credit_referral_system()
        
        # Build search query
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("(referrer_id = ? OR referred_user_id = ?)")
            params.extend([user_id, user_id])
        
        if referral_code:
            where_conditions.append("referral_code = ?")
            params.append(referral_code)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Query database
        import sqlite3
        with sqlite3.connect(referral_system.db_path) as conn:
            cursor = conn.execute(f"""
                SELECT id, referrer_id, referred_user_id, referral_code, credit_amount, 
                       credited, payment_confirmed, created_at, credited_at, applied_on_invoice_id
                FROM referral_credits 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT ?
            """, params + [limit])
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'id': row[0],
                    'referrer_id': row[1],
                    'referred_user_id': row[2],
                    'referral_code': row[3],
                    'credit_amount': row[4],
                    'credited': bool(row[5]),
                    'payment_confirmed': bool(row[6]),
                    'created_at': row[7],
                    'credited_at': row[8],
                    'applied_on_invoice_id': row[9]
                })
        
        return jsonify({
            'success': True,
            'transactions': transactions,
            'search_params': {
                'user_id': user_id,
                'referral_code': referral_code,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching credits: {e}")
        return jsonify({'error': str(e)}), 500

@credit_admin_bp.route('/admin/credits/export', methods=['GET'])
@require_admin_auth
def export_credits():
    """Export all credit data as CSV"""
    try:
        referral_system = get_credit_referral_system()
        
        import sqlite3
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Referrer ID', 'Referred User ID', 'Referral Code', 
            'Credit Amount', 'Credited', 'Payment Confirmed', 
            'Created At', 'Credited At', 'Invoice ID'
        ])
        
        # Write data
        with sqlite3.connect(referral_system.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, referrer_id, referred_user_id, referral_code, credit_amount, 
                       credited, payment_confirmed, created_at, credited_at, applied_on_invoice_id
                FROM referral_credits 
                ORDER BY created_at DESC
            """)
            
            for row in cursor.fetchall():
                writer.writerow(row)
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=bitten_credits_export.csv'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting credits: {e}")
        return jsonify({'error': str(e)}), 500

# Helper function to register the blueprint
def register_credit_admin_blueprint(app):
    """Register the credit admin blueprint with Flask app"""
    app.register_blueprint(credit_admin_bp, url_prefix='/api')
    logger.info("Credit admin API endpoints registered")