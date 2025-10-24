"""
NORMAN'S NOTEBOOK - FastAPI Router
REST API endpoints for journal operations
Created: 2025-10-15
"""

import json
import sqlite3
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field

# Import existing notebook classes
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.bitten_core.normans_notebook import NormansNotebook
from src.bitten_core.notebook_mission_integration import (
    NotebookMissionIntegration,
    get_notebook_data_for_mission
)

# Create FastAPI router
router = APIRouter(prefix="/api/notebook", tags=["notebook"])

# Database path
DB_PATH = '/root/HydraX-v2/bitten.db'


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class NoteCreate(BaseModel):
    """Model for creating a note"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []
    symbol: Optional[str] = None
    trade_id: Optional[str] = None


class NoteUpdate(BaseModel):
    """Model for updating a note"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    symbol: Optional[str] = None
    pinned: Optional[bool] = None


class PinUpdate(BaseModel):
    """Model for pinning/unpinning"""
    pinned: bool = True


class MissionNoteCreate(BaseModel):
    """Model for creating mission-linked note"""
    mission_id: str
    symbol: str
    content: str
    note_type: Optional[str] = "trade_plan"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """Get user ID from header or use default test user"""
    if x_user_id:
        return x_user_id
    # Default to Commander user for testing
    return "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.post("/notes", status_code=201)
async def create_note(
    note: NoteCreate,
    user_id: str = Header(None, alias="X-User-Id")
):
    """Create a new journal entry"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"  # Default test user

        notebook = NormansNotebook(user_id=user_id)
        result = notebook.add_user_note(
            title=note.title,
            content=note.content,
            category=note.category,
            tags=note.tags,
            symbol=note.symbol,
            trade_id=note.trade_id
        )

        # Award XP
        xp_amount = 25 if note.category == 'strategy' else 10

        return {
            "success": True,
            "note": result,
            "xp_awarded": xp_amount
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes")
async def get_notes(
    user_id: str = Header(None, alias="X-User-Id"),
    category: Optional[str] = None,
    symbol: Optional[str] = None,
    trade_id: Optional[str] = None,
    pinned: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get user notes with optional filtering"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        notebook = NormansNotebook(user_id=user_id)

        # Get notes based on filters
        if trade_id:
            notes = notebook.get_notes_by_trade(trade_id)
        elif symbol:
            notes = notebook.get_notes_by_symbol(symbol)
        else:
            notes = notebook.get_user_notes(
                category=category,
                pinned_only=pinned or False
            )

        # Apply pagination
        total = len(notes)
        notes = notes[offset:offset + limit]

        return {
            "success": True,
            "notes": notes,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{entry_id}")
async def get_note(
    entry_id: str,
    user_id: str = Header(None, alias="X-User-Id")
):
    """Get a specific note by ID"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM notebook_entries
            WHERE entry_id = ? AND user_id = ?
        ''', [entry_id, user_id])

        note = cursor.fetchone()
        conn.close()

        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        note_dict = dict(note)
        if note_dict.get('tags'):
            note_dict['tags'] = json.loads(note_dict['tags'])

        return {
            "success": True,
            "note": note_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notes/{entry_id}")
async def update_note(
    entry_id: str,
    note: NoteUpdate,
    user_id: str = Header(None, alias="X-User-Id")
):
    """Update an existing note"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify ownership
        cursor.execute('''
            SELECT user_id FROM notebook_entries WHERE entry_id = ?
        ''', [entry_id])

        existing = cursor.fetchone()
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Note not found")

        if existing['user_id'] != user_id:
            conn.close()
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Build update query
        update_fields = []
        params = []

        if note.title is not None:
            update_fields.append('title = ?')
            params.append(note.title)

        if note.content is not None:
            update_fields.append('content = ?')
            params.append(note.content)

        if note.category is not None:
            update_fields.append('category = ?')
            params.append(note.category)

        if note.tags is not None:
            update_fields.append('tags = ?')
            params.append(json.dumps(note.tags))

        if note.symbol is not None:
            update_fields.append('symbol = ?')
            params.append(note.symbol)

        if note.pinned is not None:
            update_fields.append('pinned = ?')
            params.append(1 if note.pinned else 0)

        # Always update timestamp
        update_fields.append('updated_at = ?')
        params.append(int(time.time()))

        params.extend([entry_id, user_id])

        cursor.execute(f'''
            UPDATE notebook_entries
            SET {', '.join(update_fields)}
            WHERE entry_id = ? AND user_id = ?
        ''', params)

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Note updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{entry_id}")
async def delete_note(
    entry_id: str,
    user_id: str = Header(None, alias="X-User-Id")
):
    """Delete a note"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM notebook_entries
            WHERE entry_id = ? AND user_id = ?
        ''', [entry_id, user_id])

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Note not found or unauthorized")

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Note deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{entry_id}/pin")
async def toggle_pin(
    entry_id: str,
    pin_data: PinUpdate,
    user_id: str = Header(None, alias="X-User-Id")
):
    """Pin or unpin a note"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE notebook_entries
            SET pinned = ?, updated_at = ?
            WHERE entry_id = ? AND user_id = ?
        ''', [1 if pin_data.pinned else 0, int(time.time()), entry_id, user_id])

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Note not found")

        conn.commit()
        conn.close()

        return {
            "success": True,
            "pinned": pin_data.pinned
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD & HEALTH ENDPOINTS
# ============================================================================

@router.get("/dashboard")
async def get_dashboard(user_id: str = Header(None, alias="X-User-Id")):
    """Get notebook dashboard data"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        integration = NotebookMissionIntegration(user_id)
        dashboard_data = integration.get_notebook_dashboard()

        return {
            "success": True,
            "dashboard": dashboard_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_health(user_id: str = Header(None, alias="X-User-Id")):
    """Get notebook health score"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        integration = NotebookMissionIntegration(user_id)
        dashboard = integration.get_notebook_dashboard()
        health = dashboard.get('notebook_health', {})

        return {
            "success": True,
            "health": health
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@router.get("/templates")
async def list_templates():
    """List available note templates"""
    try:
        templates = [
            {'id': 'trade_plan', 'name': 'Trade Plan', 'category': 'strategy'},
            {'id': 'quick_analysis', 'name': 'Quick Analysis', 'category': 'analysis'},
            {'id': 'trade_reminder', 'name': 'Trade Reminder', 'category': 'reminder'}
        ]

        return {
            "success": True,
            "templates": templates
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_type}")
async def get_template(
    template_type: str,
    symbol: str = Query("EURUSD"),
    user_id: str = Header(None, alias="X-User-Id")
):
    """Get a specific template"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        integration = NotebookMissionIntegration(user_id)
        template = integration.create_mission_template(symbol, template_type)

        return {
            "success": True,
            "template": template
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MISSION INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/mission/note", status_code=201)
async def create_mission_note(
    note: MissionNoteCreate,
    user_id: str = Header(None, alias="X-User-Id")
):
    """Create a note linked to a mission"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        integration = NotebookMissionIntegration(user_id)
        result = integration.add_mission_note(
            mission_id=note.mission_id,
            symbol=note.symbol,
            note_content=note.content,
            note_type=note.note_type
        )

        return {
            "success": True,
            "note": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/{symbol}")
async def get_symbol_insights(
    symbol: str,
    user_id: str = Header(None, alias="X-User-Id")
):
    """Get insights for a specific symbol"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        integration = NotebookMissionIntegration(user_id)
        insights = integration.get_symbol_insights(symbol)

        return {
            "success": True,
            "insights": insights
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mission/{mission_id}/data")
async def get_mission_notebook_data(
    mission_id: str,
    symbol: str = Query("EURUSD"),
    user_id: str = Header(None, alias="X-User-Id")
):
    """Get all notebook data for a mission"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        data = get_notebook_data_for_mission(user_id, symbol, mission_id)

        return {
            "success": True,
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SEARCH & STATS ENDPOINTS
# ============================================================================

@router.get("/search")
async def search_notes(
    q: str = Query(..., min_length=1),
    user_id: str = Header(None, alias="X-User-Id")
):
    """Search notes by content, title, or tags"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

        conn = get_db_connection()
        cursor = conn.cursor()

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
        ''', [user_id, f'%{q}%', f'%{q}%', f'%{q}%'])

        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Parse JSON fields
        for note in notes:
            if note.get('tags'):
                note['tags'] = json.loads(note['tags'])

        return {
            "success": True,
            "query": q,
            "results": notes,
            "count": len(notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(user_id: str = Header(None, alias="X-User-Id")):
    """Get user's notebook statistics"""
    try:
        if not user_id:
            user_id = "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"

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

        return {
            "success": True,
            "stats": {
                "total_notes": total_notes,
                "notes_this_week": notes_this_week,
                "by_category": by_category,
                "symbols_tracked": symbols_tracked
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# END OF API
# ============================================================================
