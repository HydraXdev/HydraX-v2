"""
TCS Education API Endpoints
Provides educational content and user progress tracking
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tcs_education import TCSEducation

# Create blueprint
tcs_education_bp = Blueprint('tcs_education', __name__)

# Initialize education system
educator = TCSEducation()

# Mock user database (replace with actual database)
user_progress_db = {}

@tcs_education_bp.route('/api/tcs/education', methods=['POST'])
def get_tcs_education():
    """
    Get TCS education content for a specific factor
    """
    try:
        data = request.get_json()
        factor = data.get('factor')
        user_level = data.get('user_level', 1)
        user_id = data.get('user_id')
        
        # Get education content
        if factor == 'tcs_overview':
            content = educator.get_tcs_explanation(user_level)
        else:
            content = educator.get_tcs_explanation(user_level, factor)
        
        # Add visual examples for higher level users
        if user_level >= 5 and 'tcs_score' in data:
            visual_example = educator.get_visual_example(data['tcs_score'])
            content['visual_example'] = visual_example
        
        # Track interaction
        if user_id:
            track_education_interaction(user_id, factor, user_level)
        
        return jsonify(content)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tcs_education_bp.route('/api/tcs/education/breakdown', methods=['POST'])
def explain_score_breakdown():
    """
    Explain a TCS score breakdown
    """
    try:
        data = request.get_json()
        breakdown = data.get('breakdown', {})
        user_level = data.get('user_level', 1)
        
        explanations = educator.get_score_breakdown_explanation(breakdown, user_level)
        
        return jsonify({
            'explanations': explanations,
            'total_score': sum(breakdown.values()),
            'tier': get_tier_for_score(sum(breakdown.values())),
            'improvement_tips': get_improvement_tips(explanations)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tcs_education_bp.route('/api/tcs/education/tutorial', methods=['GET'])
def get_tutorial():
    """
    Get interactive tutorial content
    """
    try:
        user_level = request.args.get('user_level', 1, type=int)
        topic = request.args.get('topic', 'tcs_basics')
        
        tutorial = educator.get_interactive_tutorial(user_level)
        
        # Add specific topic content
        content = educator.generate_education_content(topic, user_level)
        
        return jsonify({
            'tutorial': tutorial,
            'content': content,
            'user_tier': educator._get_user_tier(user_level)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tcs_education_bp.route('/api/tcs/education/progress', methods=['GET'])
def get_user_progress():
    """
    Get user's education progress and unlocks
    """
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Get user progress (mock data for now)
        progress = user_progress_db.get(user_id, {
            'level': 1,
            'factors_viewed': [],
            'tutorials_completed': [],
            'total_interactions': 0,
            'last_active': datetime.now().isoformat()
        })
        
        # Get achievement unlocks
        unlocks = educator.get_achievement_unlocks(progress['level'])
        
        # Find recent unlocks
        recent_unlocks = []
        for unlock in unlocks:
            if unlock['status'] == 'unlocked' and unlock['level'] == progress['level']:
                recent_unlocks.append(unlock)
        
        return jsonify({
            'progress': progress,
            'unlocks': unlocks,
            'recent_unlocks': recent_unlocks,
            'next_unlock': get_next_unlock(progress['level'], unlocks)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tcs_education_bp.route('/api/tcs/education/quiz', methods=['POST'])
def submit_quiz_answer():
    """
    Submit quiz answer and track progress
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        topic = data.get('topic')
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        # Validate answer (simplified for demo)
        is_correct = validate_quiz_answer(topic, question_id, answer)
        
        # Update user progress
        if user_id and is_correct:
            update_user_progress(user_id, 'quiz_completed', {
                'topic': topic,
                'question_id': question_id
            })
        
        return jsonify({
            'correct': is_correct,
            'explanation': get_quiz_explanation(topic, question_id),
            'points_earned': 10 if is_correct else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tcs_education_bp.route('/api/tcs/education/examples', methods=['GET'])
def get_trading_examples():
    """
    Get real trading examples for education
    """
    try:
        user_level = request.args.get('user_level', 1, type=int)
        tcs_range = request.args.get('tcs_range', 'all')
        
        examples = []
        
        # Example trades with different TCS scores
        sample_trades = [
            {
                'id': 1,
                'pair': 'EUR/USD',
                'tcs_score': 96,
                'setup': 'Liquidity grab reversal at key resistance',
                'outcome': '+215 pips',
                'breakdown': {
                    'market_structure': 19,
                    'timeframe_alignment': 15,
                    'momentum': 14,
                    'volatility': 9,
                    'session': 10,
                    'liquidity': 10,
                    'risk_reward': 9,
                    'ai_sentiment': 10
                }
            },
            {
                'id': 2,
                'pair': 'GBP/USD',
                'tcs_score': 87,
                'setup': 'Bull flag breakout during London session',
                'outcome': '+127 pips',
                'breakdown': {
                    'market_structure': 16,
                    'timeframe_alignment': 12,
                    'momentum': 13,
                    'volatility': 8,
                    'session': 9,
                    'liquidity': 8,
                    'risk_reward': 8,
                    'ai_sentiment': 9
                }
            },
            {
                'id': 3,
                'pair': 'USD/JPY',
                'tcs_score': 78,
                'setup': 'Range breakout with momentum',
                'outcome': '+65 pips',
                'breakdown': {
                    'market_structure': 14,
                    'timeframe_alignment': 10,
                    'momentum': 11,
                    'volatility': 7,
                    'session': 8,
                    'liquidity': 7,
                    'risk_reward': 7,
                    'ai_sentiment': 8
                }
            }
        ]
        
        # Filter by TCS range if specified
        if tcs_range == 'hammer':
            examples = [t for t in sample_trades if t['tcs_score'] >= 94]
        elif tcs_range == 'shadow_strike':
            examples = [t for t in sample_trades if 84 <= t['tcs_score'] < 94]
        elif tcs_range == 'scalp':
            examples = [t for t in sample_trades if 75 <= t['tcs_score'] < 84]
        else:
            examples = sample_trades
        
        # Add explanations based on user level
        for example in examples:
            example['explanations'] = educator.get_score_breakdown_explanation(
                example['breakdown'], 
                user_level
            )
        
        return jsonify({
            'examples': examples,
            'total': len(examples),
            'user_can_view_details': user_level >= 5
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions

def track_education_interaction(user_id, factor, level):
    """Track user interaction with education content"""
    if user_id not in user_progress_db:
        user_progress_db[user_id] = {
            'level': level,
            'factors_viewed': [],
            'tutorials_completed': [],
            'total_interactions': 0,
            'last_active': datetime.now().isoformat()
        }
    
    progress = user_progress_db[user_id]
    
    if factor not in progress['factors_viewed']:
        progress['factors_viewed'].append(factor)
    
    progress['total_interactions'] += 1
    progress['last_active'] = datetime.now().isoformat()
    
    # Level up logic (simplified)
    if progress['total_interactions'] % 10 == 0:
        progress['level'] = min(progress['level'] + 1, 100)

def get_tier_for_score(score):
    """Get tier name for a TCS score"""
    if score >= 94:
        return 'hammer'
    elif score >= 84:
        return 'shadow_strike'
    elif score >= 75:
        return 'scalp'
    elif score >= 65:
        return 'watchlist'
    else:
        return 'no_trade'

def get_improvement_tips(explanations):
    """Extract improvement tips from explanations"""
    tips = []
    for exp in explanations:
        if exp['quality'] in ['Poor', 'Weak', 'Fair']:
            tips.append({
                'factor': exp['factor'],
                'tip': exp['improvement_tip'],
                'priority': 'high' if exp['quality'] == 'Poor' else 'medium'
            })
    return tips

def get_next_unlock(current_level, unlocks):
    """Find the next unlock for user"""
    for unlock in unlocks:
        if unlock['status'] == 'locked':
            return unlock
    return None

def validate_quiz_answer(topic, question_id, answer):
    """Validate quiz answer (simplified)"""
    # In real implementation, this would check against a quiz database
    correct_answers = {
        'tcs_overview_1': 2,  # 94+ for Hammer
        'tcs_overview_2': 3,  # 20+ factors
    }
    
    key = f"{topic}_{question_id}"
    return correct_answers.get(key) == answer

def get_quiz_explanation(topic, question_id):
    """Get explanation for quiz question"""
    explanations = {
        'tcs_overview_1': "Hammer trades require a TCS score of 94 or higher, representing elite setups with perfect confluence.",
        'tcs_overview_2': "TCS analyzes 20+ market factors across 8 categories for comprehensive trade analysis."
    }
    
    key = f"{topic}_{question_id}"
    return explanations.get(key, "Keep learning to unlock more insights!")

def update_user_progress(user_id, action, data):
    """Update user progress based on actions"""
    if user_id not in user_progress_db:
        user_progress_db[user_id] = {
            'level': 1,
            'factors_viewed': [],
            'tutorials_completed': [],
            'total_interactions': 0,
            'last_active': datetime.now().isoformat()
        }
    
    progress = user_progress_db[user_id]
    
    if action == 'quiz_completed':
        progress['total_interactions'] += 5  # Bonus for quiz
        if data['topic'] not in progress['tutorials_completed']:
            progress['tutorials_completed'].append(data['topic'])
            progress['level'] = min(progress['level'] + 2, 100)  # Level up bonus
    
    progress['last_active'] = datetime.now().isoformat()

# Example integration with Flask app
def register_education_routes(app):
    """Register education routes with Flask app"""
    app.register_blueprint(tcs_education_bp)

# Standalone test server
if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(tcs_education_bp)
    
    print("TCS Education API running on http://localhost:5000")
    app.run(debug=True, port=5000)