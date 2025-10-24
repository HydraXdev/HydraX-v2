"""
NORMAN'S NOTEBOOK - Flask API Blueprint
Provides REST API endpoints for journal operations
Created: 2025-10-15
"""

import json
import sqlite3
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request

# Import existing notebook classes
from .normans_notebook import NormansNotebook
from .notebook_mission_integration import NotebookMissionIntegration, get_notebook_data_for_mission

# Create Flask blueprint
notebook_api = Blueprint('notebook_api', __name__, url_prefix='/api/notebook')

# Database path
DB_PATH = '/root/HydraX-v2/bitten.db'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user_id() -> str:
    """Get current user ID from session/token"""
    # TODO: Integrate with existing auth system
    # For now, get from request headers or default to test user
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        # Try to get from session
        from flask import session
        user_id = session.get('user_id', 'wlJ5lafBqRSLwHIUBxJQMr4SBtk1')  # Default test user
    return user_id


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@notebook_api.route('/notes', methods=['POST'])
def create_note():
    """Create a new journal entry"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Validate required fields
        if not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Title and content are required'}), 400

        # Create entry
        notebook = NormansNotebook(user_id=user_id)
        result = notebook.add_user_note(
            title=data['title'],
            content=data['content'],
            category=data.get('category', 'general'),
            tags=data.get('tags', []),
            symbol=data.get('symbol'),
            trade_id=data.get('trade_id')
        )

        # Award XP for note creation
        xp_amount = 25 if data.get('category') == 'strategy' else 10
        # TODO: Integrate with XP system
        # award_xp(user_id, "create_note", xp_amount)

        return jsonify({
            'success': True,
            'note': result,
            'xp_awarded': xp_amount
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/notes', methods=['GET'])
def get_notes():
    """Get all user notes with optional filtering"""
    try:
        user_id = get_current_user_id()

        # Get query parameters
        category = request.args.get('category')
        symbol = request.args.get('symbol')
        trade_id = request.args.get('trade_id')
        pinned_only = request.args.get('pinned') == 'true'
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        notebook = NormansNotebook(user_id=user_id)

        # Build query based on filters
        if trade_id:
            notes = notebook.get_notes_by_trade(trade_id)
        elif symbol:
            notes = notebook.get_notes_by_symbol(symbol)
        else:
            notes = notebook.get_user_notes(
                category=category,
                pinned_only=pinned_only
            )

        # Apply pagination
        total = len(notes)
        notes = notes[offset:offset + limit]

        return jsonify({
            'success': True,
            'notes': notes,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/notes/<entry_id>', methods=['GET'])
def get_note(entry_id):
    """Get a specific note by ID"""
    try:
        user_id = get_current_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM notebook_entries
            WHERE entry_id = ? AND user_id = ?
        ''', [entry_id, user_id])

        note = cursor.fetchone()
        conn.close()

        if not note:
            return jsonify({'error': 'Note not found'}), 404

        # Convert Row to dict
        note_dict = dict(note)

        # Parse JSON fields
        if note_dict.get('tags'):
            note_dict['tags'] = json.loads(note_dict['tags'])

        return jsonify({
            'success': True,
            'note': note_dict
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/notes/<entry_id>', methods=['PUT'])
def update_note(entry_id):
    """Update an existing note"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Verify ownership
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id FROM notebook_entries
            WHERE entry_id = ?
        ''', [entry_id])

        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return jsonify({'error': 'Note not found'}), 404

        if existing['user_id'] != user_id:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403

        # Build update query
        update_fields = []
        params = []

        if 'title' in data:
            update_fields.append('title = ?')
            params.append(data['title'])

        if 'content' in data:
            update_fields.append('content = ?')
            params.append(data['content'])

        if 'category' in data:
            update_fields.append('category = ?')
            params.append(data['category'])

        if 'tags' in data:
            update_fields.append('tags = ?')
            params.append(json.dumps(data['tags']))

        if 'symbol' in data:
            update_fields.append('symbol = ?')
            params.append(data['symbol'])

        if 'pinned' in data:
            update_fields.append('pinned = ?')
            params.append(1 if data['pinned'] else 0)

        # Always update timestamp
        update_fields.append('updated_at = ?')
        params.append(int(time.time()))

        # Add WHERE clause params
        params.append(entry_id)
        params.append(user_id)

        # Execute update
        cursor.execute(f'''
            UPDATE notebook_entries
            SET {', '.join(update_fields)}
            WHERE entry_id = ? AND user_id = ?
        ''', params)

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Note updated successfully'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/notes/<entry_id>', methods=['DELETE'])
def delete_note(entry_id):
    """Delete a note"""
    try:
        user_id = get_current_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify ownership before deleting
        cursor.execute('''
            DELETE FROM notebook_entries
            WHERE entry_id = ? AND user_id = ?
        ''', [entry_id, user_id])

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Note not found or unauthorized'}), 404

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Note deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/notes/<entry_id>/pin', methods=['POST'])
def toggle_pin(entry_id):
    """Pin or unpin a note"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        pinned = data.get('pinned', True)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE notebook_entries
            SET pinned = ?, updated_at = ?
            WHERE entry_id = ? AND user_id = ?
        ''', [1 if pinned else 0, int(time.time()), entry_id, user_id])

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Note not found'}), 404

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'pinned': pinned
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# DASHBOARD & HEALTH ENDPOINTS
# ============================================================================

@notebook_api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get notebook dashboard data"""
    try:
        user_id = get_current_user_id()
        integration = NotebookMissionIntegration(user_id)

        dashboard_data = integration.get_notebook_dashboard()

        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/health', methods=['GET'])
def get_health():
    """Get notebook health score"""
    try:
        user_id = get_current_user_id()
        integration = NotebookMissionIntegration(user_id)

        dashboard = integration.get_notebook_dashboard()
        health = dashboard.get('notebook_health', {})

        return jsonify({
            'success': True,
            'health': health
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STORY PROGRESSION ENDPOINTS
# ============================================================================

@notebook_api.route('/story', methods=['GET'])
def get_story_progression():
    """Get user's story progression"""
    try:
        user_id = get_current_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM story_progression
            WHERE user_id = ?
        ''', [user_id])

        progress = cursor.fetchone()
        conn.close()

        if not progress:
            # Initialize story progression
            return jsonify({
                'success': True,
                'story': {
                    'current_chapter': 'discovery',
                    'total_trades': 0,
                    'chapters_unlocked': ['discovery'],
                    'next_unlock_at': 5
                }
            }), 200

        progress_dict = dict(progress)
        progress_dict['chapters_unlocked'] = json.loads(progress_dict.get('chapters_unlocked', '[]'))

        return jsonify({
            'success': True,
            'story': progress_dict
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@notebook_api.route('/templates', methods=['GET'])
def list_templates():
    """List available note templates"""
    try:
        templates = [
            {'id': 'trade_plan', 'name': 'Trade Plan', 'category': 'strategy'},
            {'id': 'quick_analysis', 'name': 'Quick Analysis', 'category': 'analysis'},
            {'id': 'trade_reminder', 'name': 'Trade Reminder', 'category': 'reminder'}
        ]

        return jsonify({
            'success': True,
            'templates': templates
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/templates/<template_type>', methods=['GET'])
def get_template(template_type):
    """Get a specific template"""
    try:
        user_id = get_current_user_id()
        symbol = request.args.get('symbol', 'EURUSD')

        integration = NotebookMissionIntegration(user_id)
        template = integration.create_mission_template(symbol, template_type)

        return jsonify({
            'success': True,
            'template': template
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MISSION INTEGRATION ENDPOINTS
# ============================================================================

@notebook_api.route('/mission/note', methods=['POST'])
def create_mission_note():
    """Create a note linked to a mission"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        required = ['mission_id', 'symbol', 'content']
        if not all(k in data for k in required):
            return jsonify({'error': f'Required fields: {required}'}), 400

        integration = NotebookMissionIntegration(user_id)
        result = integration.add_mission_note(
            mission_id=data['mission_id'],
            symbol=data['symbol'],
            note_content=data['content'],
            note_type=data.get('note_type', 'trade_plan')
        )

        return jsonify({
            'success': True,
            'note': result
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/insights/<symbol>', methods=['GET'])
def get_symbol_insights(symbol):
    """Get insights for a specific symbol"""
    try:
        user_id = get_current_user_id()
        integration = NotebookMissionIntegration(user_id)

        insights = integration.get_symbol_insights(symbol)

        return jsonify({
            'success': True,
            'insights': insights
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notebook_api.route('/mission/<mission_id>/data', methods=['GET'])
def get_mission_notebook_data(mission_id):
    """Get all notebook data for a mission"""
    try:
        user_id = get_current_user_id()
        symbol = request.args.get('symbol', 'EURUSD')

        data = get_notebook_data_for_mission(user_id, symbol, mission_id)

        return jsonify({
            'success': True,
            'data': data
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SEARCH ENDPOINT
# ============================================================================

@notebook_api.route('/search', methods=['GET'])
def search_notes():
    """Search notes by content, title, or tags"""
    try:
        user_id = get_current_user_id()
        query = request.args.get('q', '').strip()

        if not query:
            return jsonify({'error': 'Search query required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Search in title, content, and tags
        cursor.execute('''
            SELECT * FROM notebook_entries
            WHERE user_id = ?
            AND (
                title LIKE ?
                OR content LIKE ?
                OR tags LIKE ?
            )
            ORDER BY created_at DESC
            LIMIT 50
        ''', [user_id, f'%{query}%', f'%{query}%', f'%{query}%'])

        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Parse JSON fields
        for note in notes:
            if note.get('tags'):
                note['tags'] = json.loads(note['tags'])

        return jsonify({
            'success': True,
            'query': query,
            'results': notes,
            'count': len(notes)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@notebook_api.route('/stats', methods=['GET'])
def get_stats():
    """Get user's notebook statistics"""
    try:
        user_id = get_current_user_id()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Total notes
        cursor.execute('SELECT COUNT(*) as count FROM notebook_entries WHERE user_id = ?', [user_id])
        total_notes = cursor.fetchone()['count']

        # Notes by category
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM notebook_entries
            WHERE user_id = ?
            GROUP BY category
        ''', [user_id])
        by_category = {row['category']: row['count'] for row in cursor.fetchall()}

        # Notes this week
        week_ago = int(time.time()) - (7 * 24 * 60 * 60)
        cursor.execute('''
            SELECT COUNT(*) as count FROM notebook_entries
            WHERE user_id = ? AND created_at > ?
        ''', [user_id, week_ago])
        notes_this_week = cursor.fetchone()['count']

        # Unique symbols tracked
        cursor.execute('''
            SELECT COUNT(DISTINCT symbol) as count
            FROM notebook_entries
            WHERE user_id = ? AND symbol IS NOT NULL
        ''', [user_id])
        symbols_tracked = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_notes': total_notes,
                'notes_this_week': notes_this_week,
                'by_category': by_category,
                'symbols_tracked': symbols_tracked
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# END OF API
# ============================================================================
