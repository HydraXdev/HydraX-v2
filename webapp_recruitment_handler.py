"""
WebApp Recruitment Handler - Firebase API Endpoints
Handles recruitment operations via Firestore
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from flask import Blueprint, jsonify, request
from google.cloud.firestore_v1.base_query import FieldFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase (only if not already initialized)
if not firebase_admin._apps:
    cred = credentials.Certificate('/root/bitten-firebase-sa.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Create Flask blueprint
recruitment_bp = Blueprint('recruitment', __name__, url_prefix='/api/recruitment')


class RecruitmentHandler:
    """Handles recruitment operations in Firestore"""

    def __init__(self):
        self.db = db
        self.referral_codes_col = self.db.collection('referral_codes')
        self.recruits_col = self.db.collection('recruits')
        self.squad_stats_col = self.db.collection('squad_stats')
        self.referral_rewards_col = self.db.collection('referral_rewards')

    def get_or_create_referral_code(self, user_id: str, custom_code: Optional[str] = None) -> Dict:
        """Get existing or create new referral code"""

        # Check if user already has a code
        existing = (
            self.referral_codes_col
            .where(filter=FieldFilter('user_id', '==', user_id))
            .limit(1)
            .stream()
        )

        for doc in existing:
            data = doc.to_dict()
            data['code'] = doc.id
            return {'success': True, 'code': data}

        # Generate new code
        if custom_code:
            code = custom_code.upper()
            # Check availability
            if self.referral_codes_col.document(code).get().exists:
                return {'success': False, 'error': 'Code already taken'}
        else:
            # Generate random code
            import secrets
            import string
            chars = string.ascii_uppercase + string.digits
            chars = chars.replace("0", "").replace("O", "").replace("I", "").replace("1", "")
            code = "".join(secrets.choice(chars) for _ in range(8))

        # Create referral code
        code_data = {
            'user_id': user_id,
            'callsign': code,
            'created_at': firestore.SERVER_TIMESTAMP,
            'uses_count': 0,
            'max_uses': None,
            'is_promo': False,
            'promo_multiplier': 1.0
        }

        self.referral_codes_col.document(code).set(code_data)

        # Initialize squad stats
        self.squad_stats_col.document(user_id).set({
            'callsign': code,
            'referral_code': code,
            'total_recruits': 0,
            'active_recruits': 0,
            'total_xp_from_recruits': 0,
            'squad_rank': 'LONE_WOLF',
            'last_recruit_at': None,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        code_data['code'] = code
        return {'success': True, 'code': code_data}

    def use_referral_code(self, recruit_id: str, code: str, username: str, ip_address: str) -> Dict:
        """Process referral code signup"""

        code = code.upper()

        # Get referral code
        code_doc = self.referral_codes_col.document(code).get()
        if not code_doc.exists:
            return {'success': False, 'error': 'Invalid referral code'}

        code_data = code_doc.to_dict()
        referrer_id = code_data['user_id']

        # Check if recruit already signed up
        if self.recruits_col.document(recruit_id).get().exists:
            return {'success': False, 'error': 'Already recruited'}

        # Check if using own code
        if referrer_id == recruit_id:
            return {'success': False, 'error': 'Cannot use own referral code'}

        # Create recruit record
        recruit_data = {
            'referrer_id': referrer_id,
            'referral_code': code,
            'callsign': username or f"AGENT_{recruit_id[:6]}",
            'joined_at': firestore.SERVER_TIMESTAMP,
            'tier': 'DIRECT',
            'total_xp_earned': 0,
            'trades_completed': 0,
            'current_rank': 'NIBBLER',
            'is_active': True,
            'last_activity': firestore.SERVER_TIMESTAMP
        }

        self.recruits_col.document(recruit_id).set(recruit_data)

        # Update referral code uses
        self.referral_codes_col.document(code).update({
            'uses_count': firestore.Increment(1)
        })

        # Update squad stats
        self.squad_stats_col.document(referrer_id).update({
            'total_recruits': firestore.Increment(1),
            'active_recruits': firestore.Increment(1),
            'last_recruit_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        # Log reward
        self.referral_rewards_col.add({
            'referrer_id': referrer_id,
            'recruit_id': recruit_id,
            'reward_type': 'join',
            'xp_amount': 100,
            'multiplier': 1.0,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return {
            'success': True,
            'message': f'Welcome to the squad!',
            'referrer_id': referrer_id,
            'xp_awarded': 100
        }

    def get_squad_stats(self, user_id: str) -> Dict:
        """Get squad statistics for user"""

        stats_doc = self.squad_stats_col.document(user_id).get()
        if not stats_doc.exists:
            return {
                'total_recruits': 0,
                'active_recruits': 0,
                'total_xp_from_recruits': 0,
                'squad_rank': 'LONE_WOLF'
            }

        stats = stats_doc.to_dict()

        # Get recruits list
        recruits = (
            self.recruits_col
            .where(filter=FieldFilter('referrer_id', '==', user_id))
            .order_by('joined_at', direction=firestore.Query.DESCENDING)
            .limit(10)
            .stream()
        )

        recruits_list = []
        for doc in recruits:
            recruit = doc.to_dict()
            recruit['recruit_id'] = doc.id
            recruits_list.append({
                'callsign': recruit.get('callsign', 'Unknown'),
                'rank': recruit.get('current_rank', 'NIBBLER'),
                'xp_contributed': recruit.get('total_xp_earned', 0),
                'joined_at': recruit.get('joined_at')
            })

        return {
            'total_recruits': stats.get('total_recruits', 0),
            'active_recruits': stats.get('active_recruits', 0),
            'total_xp_from_recruits': stats.get('total_xp_from_recruits', 0),
            'squad_rank': stats.get('squad_rank', 'LONE_WOLF'),
            'referral_code': stats.get('referral_code'),
            'recruits': recruits_list
        }

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top recruiters leaderboard"""

        results = (
            self.squad_stats_col
            .order_by('total_xp_from_recruits', direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        leaderboard = []
        rank = 1
        for doc in results:
            stats = doc.to_dict()
            leaderboard.append({
                'rank': rank,
                'user_id': doc.id,
                'callsign': stats.get('callsign', f"AGENT_{doc.id[:6]}"),
                'total_recruits': stats.get('total_recruits', 0),
                'active_recruits': stats.get('active_recruits', 0),
                'total_xp': stats.get('total_xp_from_recruits', 0),
                'squad_rank': stats.get('squad_rank', 'LONE_WOLF')
            })
            rank += 1

        return leaderboard


# Initialize handler
handler = RecruitmentHandler()


# Flask API Endpoints

@recruitment_bp.route('/signup', methods=['POST'])
def signup():
    """Process referral code signup"""
    data = request.get_json()

    recruit_id = data.get('user_id')
    code = data.get('referral_code')
    username = data.get('username')
    ip_address = request.remote_addr

    if not recruit_id or not code:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    result = handler.use_referral_code(recruit_id, code, username, ip_address)

    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@recruitment_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get user's squad stats"""
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    stats = handler.get_squad_stats(user_id)
    return jsonify(stats), 200


@recruitment_bp.route('/generate', methods=['POST'])
def generate_code():
    """Generate referral code for user"""
    data = request.get_json()

    user_id = data.get('user_id')
    custom_code = data.get('custom_code')

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    result = handler.get_or_create_referral_code(user_id, custom_code)

    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@recruitment_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    """Get top recruiters leaderboard"""
    limit = int(request.args.get('limit', 10))

    leaderboard_data = handler.get_leaderboard(limit)
    return jsonify({'leaderboard': leaderboard_data}), 200


# Integration function for existing webapp
def register_recruitment_routes(app):
    """Register recruitment blueprint with Flask app"""
    app.register_blueprint(recruitment_bp)
    logger.info("✅ Recruitment API routes registered")


if __name__ == "__main__":
    # Test handler
    print("Testing Firebase Recruitment Handler...")

    # Test leaderboard
    leaderboard = handler.get_leaderboard(limit=5)
    print(f"\n🏆 Top 5 Recruiters:")
    for entry in leaderboard:
        print(f"  {entry['rank']}. {entry['callsign']} - {entry['total_recruits']} recruits")

    print("\n✅ Handler working correctly!")
