#!/usr/bin/env python3
"""
NORMAN'S NOTEBOOK V2 - Story-Integrated Trading Journal
A deeply personal trading journal that parallels Norman's journey from Mississippi
Integrates family wisdom, Bit's guidance, and emotional pattern recognition
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

class NormansNotebookV2:
    """Enhanced story-integrated trade journal with Norman's parallel journey"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.db_path = Path("/root/HydraX-v2/notebook_v2.db")
        self.init_database()
        
        # Story progression milestones
        self.story_chapters = {
            'discovery': {'title': 'The Discovery', 'trades_needed': 0, 'unlocked': True},
            'first_bite': {'title': 'The First Bite', 'trades_needed': 5, 'unlocked': False},
            'finding_bit': {'title': 'Finding Bit', 'trades_needed': 10, 'unlocked': False},
            'fathers_warning': {'title': "Father's Warning", 'trades_needed': 20, 'unlocked': False},
            'mothers_wisdom': {'title': "Mother's Wisdom", 'trades_needed': 30, 'unlocked': False},
            'building_discipline': {'title': 'Building Discipline', 'trades_needed': 50, 'unlocked': False},
            'the_breakthrough': {'title': 'The Breakthrough', 'trades_needed': 75, 'unlocked': False},
            'biting_back': {'title': 'Biting Back', 'trades_needed': 100, 'unlocked': False},
            'the_network': {'title': 'The Network Forms', 'trades_needed': 150, 'unlocked': False},
            'commander': {'title': 'Becoming Commander', 'trades_needed': 200, 'unlocked': False}
        }
        
        # Bit's contextual responses based on emotional state
        self.bit_responses = {
            'excited': ['*chirp chirp* Bit\'s tail swishes eagerly', '*soft purr* Bit rubs against your leg'],
            'anxious': ['*concerned chirp* Bit paws at your hand', '*glitch sound* Bit senses the tension'],
            'angry': ['*warning chirp* Bit\'s eyes glow amber', '*hiss* Bit knows this feeling too well'],
            'confident': ['*happy chirp* Bit jumps on your desk', '*purring intensifies* Bit approves'],
            'defeated': ['*soft chirp* Bit curls up in your lap', '*nuzzle* Bit won\'t leave your side'],
            'focused': ['*quiet chirp* Bit watches silently', '*settled purr* Bit guards your focus']
        }
        
        # Family wisdom quotes
        self.family_wisdom = {
            'father': [
                "The market doesn't give, son. It takes.",
                "It's a zero-sum game. A battlefield.",
                "They don't tell you the rules are rigged.",
                "Every loss is a lesson, if you're brave enough to learn it."
            ],
            'mother': [
                "Some kids are born with lightning inside.",
                "You're just learning where to point it.",
                "The strongest steel goes through the hottest fire.",
                "Your mind is your first weapon. Protect it."
            ],
            'norman': [
                "The market bit me. But Bit helps me bite back.",
                "Patterns in games, patterns in charts. Same eyes, different screen.",
                "Discipline isn't restriction. It's freedom.",
                "We rise together or fall alone."
            ]
        }
    
    def init_database(self):
        """Initialize the notebook database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # User journal entries
        c.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
            entry_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            trade_id TEXT,
            emotion TEXT,
            market_state TEXT,
            entry_text TEXT,
            lessons_learned TEXT,
            pattern_noticed TEXT,
            bit_reaction TEXT,
            family_wisdom TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )''')
        
        # Story progression tracking
        c.execute('''CREATE TABLE IF NOT EXISTS story_progression (
            user_id TEXT PRIMARY KEY,
            current_chapter TEXT,
            total_trades INTEGER DEFAULT 0,
            chapters_unlocked TEXT,
            last_milestone INTEGER,
            emotional_patterns TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )''')
        
        # Trading insights extracted from entries
        c.execute('''CREATE TABLE IF NOT EXISTS extracted_insights (
            insight_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            insight_type TEXT,
            insight_text TEXT,
            frequency INTEGER DEFAULT 1,
            last_seen INTEGER,
            created_at INTEGER
        )''')
        
        conn.commit()
        conn.close()
    
    def create_entry(self, user_id, entry_data):
        """Create a new journal entry"""
        entry_id = f"ENTRY_{user_id}_{int(time.time()*1000)}"
        emotion = entry_data.get('emotion', 'focused')
        
        # Get Bit's reaction based on emotion
        bit_reaction = self._get_bit_reaction(emotion)
        
        # Get contextual family wisdom
        family_wisdom = self._get_contextual_wisdom(entry_data)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO journal_entries 
                    (entry_id, user_id, trade_id, emotion, market_state, 
                     entry_text, lessons_learned, pattern_noticed, 
                     bit_reaction, family_wisdom, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (entry_id, user_id, entry_data.get('trade_id'),
                  emotion, entry_data.get('market_state'),
                  entry_data.get('entry_text'), entry_data.get('lessons_learned'),
                  entry_data.get('pattern_noticed'), bit_reaction, family_wisdom,
                  int(time.time()), int(time.time())))
        
        # Update story progression
        self._update_story_progression(user_id, c)
        
        # Extract insights from entry
        self._extract_insights(user_id, entry_data, c)
        
        conn.commit()
        conn.close()
        
        return {
            'entry_id': entry_id,
            'bit_reaction': bit_reaction,
            'family_wisdom': family_wisdom,
            'chapter_unlocked': self._check_chapter_unlock(user_id)
        }
    
    def _get_bit_reaction(self, emotion):
        """Get Bit's reaction based on emotional state"""
        import random
        reactions = self.bit_responses.get(emotion, self.bit_responses['focused'])
        return random.choice(reactions)
    
    def _get_contextual_wisdom(self, entry_data):
        """Get relevant family wisdom based on context"""
        import random
        
        # Determine which family member's wisdom is most relevant
        if 'loss' in entry_data.get('entry_text', '').lower():
            quotes = self.family_wisdom['father']
        elif 'win' in entry_data.get('entry_text', '').lower():
            quotes = self.family_wisdom['mother']
        else:
            quotes = self.family_wisdom['norman']
        
        return random.choice(quotes)
    
    def _update_story_progression(self, user_id, cursor):
        """Update user's story progression"""
        cursor.execute('SELECT total_trades, chapters_unlocked FROM story_progression WHERE user_id = ?',
                      (user_id,))
        result = cursor.fetchone()
        
        if result:
            total_trades, chapters_unlocked = result
            total_trades += 1
            chapters = json.loads(chapters_unlocked) if chapters_unlocked else []
        else:
            total_trades = 1
            chapters = ['discovery']
            cursor.execute('''INSERT INTO story_progression 
                            (user_id, current_chapter, total_trades, chapters_unlocked, 
                             created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (user_id, 'discovery', 1, json.dumps(chapters),
                          int(time.time()), int(time.time())))
            return
        
        # Check for new chapter unlocks
        for chapter_id, chapter_info in self.story_chapters.items():
            if chapter_id not in chapters and total_trades >= chapter_info['trades_needed']:
                chapters.append(chapter_id)
        
        cursor.execute('''UPDATE story_progression 
                         SET total_trades = ?, chapters_unlocked = ?, updated_at = ?
                         WHERE user_id = ?''',
                      (total_trades, json.dumps(chapters), int(time.time()), user_id))
    
    def _extract_insights(self, user_id, entry_data, cursor):
        """Extract trading insights from journal entry"""
        # Extract patterns mentioned
        if pattern := entry_data.get('pattern_noticed'):
            insight_id = hashlib.md5(f"{user_id}_{pattern}".encode()).hexdigest()
            cursor.execute('''INSERT OR REPLACE INTO extracted_insights
                            (insight_id, user_id, insight_type, insight_text, 
                             frequency, last_seen, created_at)
                            VALUES (?, ?, ?, ?, 
                                   COALESCE((SELECT frequency + 1 FROM extracted_insights 
                                            WHERE insight_id = ?), 1),
                                   ?, ?)''',
                         (insight_id, user_id, 'pattern', pattern,
                          insight_id, int(time.time()), int(time.time())))
    
    def _check_chapter_unlock(self, user_id):
        """Check if a new chapter was unlocked"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT chapters_unlocked, last_milestone FROM story_progression WHERE user_id = ?',
                 (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            chapters = json.loads(result[0]) if result[0] else []
            if len(chapters) > (result[1] or 0):
                return self.story_chapters[chapters[-1]]['title']
        return None
    
    def get_user_notebook(self, user_id):
        """Get complete notebook data for user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get recent entries
        c.execute('''SELECT * FROM journal_entries 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 20''', (user_id,))
        entries = c.fetchall()
        
        # Get story progression
        c.execute('SELECT * FROM story_progression WHERE user_id = ?', (user_id,))
        progression = c.fetchone()
        
        # Get insights
        c.execute('''SELECT * FROM extracted_insights 
                    WHERE user_id = ? 
                    ORDER BY frequency DESC 
                    LIMIT 10''', (user_id,))
        insights = c.fetchall()
        
        conn.close()
        
        return {
            'entries': [self._format_entry(e) for e in entries],
            'progression': self._format_progression(progression) if progression else None,
            'insights': [self._format_insight(i) for i in insights],
            'chapters': self.story_chapters
        }
    
    def _format_entry(self, entry):
        """Format database entry for display"""
        return {
            'id': entry[0],
            'trade_id': entry[2],
            'emotion': entry[3],
            'market_state': entry[4],
            'text': entry[5],
            'lessons': entry[6],
            'pattern': entry[7],
            'bit_reaction': entry[8],
            'family_wisdom': entry[9],
            'timestamp': datetime.fromtimestamp(entry[10]).strftime('%Y-%m-%d %H:%M')
        }
    
    def _format_progression(self, progression):
        """Format story progression for display"""
        return {
            'current_chapter': progression[1],
            'total_trades': progression[2],
            'chapters_unlocked': json.loads(progression[3]) if progression[3] else [],
            'emotional_patterns': json.loads(progression[5]) if progression[5] else {}
        }
    
    def _format_insight(self, insight):
        """Format insight for display"""
        return {
            'type': insight[2],
            'text': insight[3],
            'frequency': insight[4],
            'last_seen': datetime.fromtimestamp(insight[5]).strftime('%Y-%m-%d')
        }

def generate_notebook_ui(user_id):
    """Generate the Norman's Notebook UI"""
    notebook = NormansNotebookV2(user_id)
    data = notebook.get_user_notebook(user_id)
    
    # Determine current emotional state from recent entries
    recent_emotion = 'focused'
    if data['entries']:
        recent_emotion = data['entries'][0]['emotion']
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Norman's Notebook - Journey of a Trader</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background: linear-gradient(135deg, #0A0A0A, #1A0A0A);
            color: #fff;
            font-family: 'Courier New', monospace;
            min-height: 100vh;
            padding: 15px;
            font-size: 16px;
            line-height: 1.8;
            position: relative;
        }}
        
        /* Bit's presence animation */
        @keyframes bitWalk {{
            0% {{ transform: translateX(-100px); }}
            50% {{ transform: translateX(calc(100vw + 100px)); }}
            100% {{ transform: translateX(-100px); }}
        }}
        
        .bit-presence {{
            position: fixed;
            bottom: 20px;
            left: -100px;
            font-size: 30px;
            animation: bitWalk 30s linear infinite;
            opacity: 0.3;
            pointer-events: none;
            z-index: 1;
        }}
        
        .notebook-header {{
            background: rgba(0,0,0,0.8);
            border: 2px solid #8B4513;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            position: relative;
            overflow: hidden;
        }}
        
        .notebook-header::before {{
            content: '📓';
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 40px;
            opacity: 0.2;
        }}
        
        .notebook-title {{
            font-size: 28px;
            color: #FFD700;
            text-align: center;
            margin-bottom: 10px;
            font-family: 'Georgia', serif;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        
        .notebook-subtitle {{
            text-align: center;
            color: #999;
            font-style: italic;
            font-size: 14px;
        }}
        
        /* Story Progression */
        .story-progression {{
            background: linear-gradient(135deg, rgba(139,69,19,0.1), rgba(139,69,19,0.2));
            border: 1px solid #8B4513;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .chapter-timeline {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            padding: 20px 0;
            overflow-x: auto;
        }}
        
        .chapter-timeline::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 2px;
            background: #8B4513;
            z-index: 0;
        }}
        
        .chapter-node {{
            position: relative;
            z-index: 1;
            text-align: center;
            min-width: 80px;
        }}
        
        .chapter-dot {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #333;
            border: 2px solid #8B4513;
            margin: 0 auto 10px;
            position: relative;
        }}
        
        .chapter-dot.unlocked {{
            background: #FFD700;
            box-shadow: 0 0 10px rgba(255,215,0,0.5);
        }}
        
        .chapter-dot.current {{
            background: #FF6600;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 0 10px rgba(255,102,0,0.5); }}
            50% {{ box-shadow: 0 0 20px rgba(255,102,0,0.8); }}
        }}
        
        .chapter-name {{
            font-size: 10px;
            color: #666;
            white-space: nowrap;
        }}
        
        .chapter-name.unlocked {{
            color: #FFD700;
            font-weight: bold;
        }}
        
        /* Entry Form */
        .entry-form {{
            background: rgba(0,0,0,0.5);
            border: 2px solid #8B4513;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        
        .form-title {{
            font-size: 20px;
            color: #FFD700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .emotion-selector {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        @media (min-width: 768px) {{
            .emotion-selector {{
                grid-template-columns: repeat(6, 1fr);
            }}
        }}
        
        .emotion-btn {{
            padding: 10px;
            background: rgba(139,69,19,0.2);
            border: 1px solid #8B4513;
            border-radius: 8px;
            color: #999;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
            text-align: center;
        }}
        
        .emotion-btn:hover {{
            background: rgba(139,69,19,0.4);
            color: #FFD700;
        }}
        
        .emotion-btn.selected {{
            background: #8B4513;
            color: #FFD700;
            border-color: #FFD700;
        }}
        
        .entry-textarea {{
            width: 100%;
            min-height: 150px;
            background: rgba(0,0,0,0.3);
            border: 1px solid #8B4513;
            border-radius: 8px;
            padding: 15px;
            color: #fff;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
            margin-bottom: 15px;
        }}
        
        .entry-textarea:focus {{
            outline: none;
            border-color: #FFD700;
            box-shadow: 0 0 10px rgba(255,215,0,0.2);
        }}
        
        .lesson-input {{
            width: 100%;
            padding: 12px;
            background: rgba(0,0,0,0.3);
            border: 1px solid #8B4513;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        
        .submit-btn {{
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #8B4513, #A0522D);
            border: 2px solid #FFD700;
            border-radius: 10px;
            color: #FFD700;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .submit-btn:hover {{
            background: linear-gradient(135deg, #A0522D, #8B4513);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255,215,0,0.3);
        }}
        
        /* Past Entries */
        .entries-section {{
            margin-bottom: 30px;
        }}
        
        .section-title {{
            font-size: 24px;
            color: #FFD700;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #8B4513;
        }}
        
        .entry-card {{
            background: rgba(0,0,0,0.4);
            border: 1px solid #8B4513;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            position: relative;
            transition: all 0.3s ease;
        }}
        
        .entry-card:hover {{
            background: rgba(139,69,19,0.1);
            border-color: #FFD700;
        }}
        
        .entry-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .entry-date {{
            color: #999;
            font-size: 12px;
        }}
        
        .entry-emotion {{
            padding: 5px 10px;
            background: rgba(139,69,19,0.3);
            border-radius: 15px;
            font-size: 12px;
            color: #FFD700;
        }}
        
        .entry-text {{
            color: #ddd;
            margin-bottom: 15px;
            line-height: 1.6;
        }}
        
        .entry-wisdom {{
            padding: 10px;
            background: rgba(255,215,0,0.05);
            border-left: 3px solid #FFD700;
            color: #FFD700;
            font-style: italic;
            margin-bottom: 10px;
        }}
        
        .bit-reaction {{
            color: #FF6600;
            font-style: italic;
            text-align: right;
            font-size: 14px;
            opacity: 0.8;
        }}
        
        /* Insights Section */
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .insight-card {{
            background: linear-gradient(135deg, rgba(255,215,0,0.05), rgba(255,215,0,0.1));
            border: 1px solid #FFD700;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}
        
        .insight-type {{
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        
        .insight-text {{
            color: #FFD700;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .insight-frequency {{
            font-size: 24px;
            color: #FF6600;
        }}
        
        /* Floating Bit helper */
        .bit-helper {{
            position: fixed;
            bottom: 80px;
            right: 20px;
            background: rgba(0,0,0,0.9);
            border: 2px solid #FF6600;
            border-radius: 10px;
            padding: 15px;
            max-width: 250px;
            display: none;
            z-index: 100;
        }}
        
        .bit-helper.show {{
            display: block;
            animation: slideIn 0.3s ease;
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        .bit-message {{
            color: #FF6600;
            font-style: italic;
            margin-bottom: 10px;
        }}
        
        /* Mobile optimizations */
        @media (max-width: 480px) {{
            body {{
                padding: 10px;
            }}
            
            .notebook-title {{
                font-size: 24px;
            }}
            
            .entry-form {{
                padding: 15px;
            }}
            
            .emotion-selector {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <!-- Bit's presence -->
    <div class="bit-presence">🐈‍⬛</div>
    
    <!-- Header -->
    <div class="notebook-header">
        <h1 class="notebook-title">Norman's Notebook</h1>
        <p class="notebook-subtitle">"Every scar makes you stronger. Every entry teaches you more."</p>
    </div>
    
    <!-- Story Progression -->
    <div class="story-progression">
        <h2 class="section-title">Your Journey</h2>
        <div class="chapter-timeline">
            {''.join([f'''
            <div class="chapter-node">
                <div class="chapter-dot {'unlocked' if chapter_id in (data['progression']['chapters_unlocked'] if data['progression'] else ['discovery']) else ''} {'current' if chapter_id == (data['progression']['current_chapter'] if data['progression'] else 'discovery') else ''}"></div>
                <div class="chapter-name {'unlocked' if chapter_id in (data['progression']['chapters_unlocked'] if data['progression'] else ['discovery']) else ''}">{info['title']}</div>
            </div>
            ''' for chapter_id, info in notebook.story_chapters.items()])}
        </div>
        <p style="text-align: center; color: #999; margin-top: 15px;">
            Trades: {data['progression']['total_trades'] if data['progression'] else 0} | 
            Next Chapter: {next((info['trades_needed'] for chapter_id, info in notebook.story_chapters.items() 
                                if chapter_id not in (data['progression']['chapters_unlocked'] if data['progression'] else ['discovery'])), 'Complete')} trades
        </p>
    </div>
    
    <!-- New Entry Form -->
    <div class="entry-form">
        <div class="form-title">
            <span>✍️</span>
            <span>New Entry</span>
        </div>
        
        <div class="emotion-selector">
            <button class="emotion-btn" data-emotion="excited">😊 Excited</button>
            <button class="emotion-btn selected" data-emotion="focused">🎯 Focused</button>
            <button class="emotion-btn" data-emotion="anxious">😰 Anxious</button>
            <button class="emotion-btn" data-emotion="angry">😤 Angry</button>
            <button class="emotion-btn" data-emotion="confident">💪 Confident</button>
            <button class="emotion-btn" data-emotion="defeated">😔 Defeated</button>
        </div>
        
        <textarea class="entry-textarea" id="entry-text" placeholder="What happened in the market today? What did you see? How did you react?

Remember: The market bites, but we learn to bite back..."></textarea>
        
        <input type="text" class="lesson-input" id="lesson-learned" placeholder="What lesson did you learn? (Optional)">
        
        <input type="text" class="lesson-input" id="pattern-noticed" placeholder="What pattern did you notice? (Optional)">
        
        <button class="submit-btn" onclick="submitEntry()">Add to Notebook</button>
    </div>
    
    <!-- Past Entries -->
    <div class="entries-section">
        <h2 class="section-title">Recent Entries</h2>
        <div id="entries-container">
            {''.join([f'''
            <div class="entry-card">
                <div class="entry-header">
                    <span class="entry-date">{entry['timestamp']}</span>
                    <span class="entry-emotion">{entry['emotion'].title()}</span>
                </div>
                <div class="entry-text">{entry['text']}</div>
                {f'<div class="entry-wisdom">"{entry["family_wisdom"]}"</div>' if entry['family_wisdom'] else ''}
                {f'<div class="bit-reaction">{entry["bit_reaction"]}</div>' if entry['bit_reaction'] else ''}
            </div>
            ''' for entry in data['entries']]) if data['entries'] else '<p style="color: #999; text-align: center;">No entries yet. Start your journey above.</p>'}
        </div>
    </div>
    
    <!-- Insights -->
    {'<div class="entries-section"><h2 class="section-title">Extracted Patterns</h2><div class="insights-grid">' + 
     ''.join([f'<div class="insight-card"><div class="insight-type">{insight["type"]}</div><div class="insight-text">{insight["text"]}</div><div class="insight-frequency">{insight["frequency"]}x</div></div>' 
              for insight in data['insights']]) + '</div></div>' if data['insights'] else ''}
    
    <!-- Bit Helper -->
    <div class="bit-helper" id="bit-helper">
        <div class="bit-message" id="bit-message">*chirp* Remember what your father said...</div>
        <button onclick="closeBitHelper()" style="background: none; border: 1px solid #FF6600; color: #FF6600; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Thanks, Bit</button>
    </div>
    
    <script>
        // Emotion selector
        document.querySelectorAll('.emotion-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.emotion-btn').forEach(b => b.classList.remove('selected'));
                this.classList.add('selected');
                
                // Show Bit's reaction
                const emotion = this.dataset.emotion;
                showBitReaction(emotion);
            }});
        }});
        
        function showBitReaction(emotion) {{
            const reactions = {{
                'excited': '*chirp chirp* Bit shares your excitement!',
                'focused': '*quiet purr* Bit settles beside you.',
                'anxious': '*concerned chirp* Bit paws at your hand.',
                'angry': '*warning chirp* Bit knows this feeling.',
                'confident': '*happy chirp* Bit approves!',
                'defeated': '*soft chirp* Bit won\\'t leave your side.'
            }};
            
            const helper = document.getElementById('bit-helper');
            const message = document.getElementById('bit-message');
            message.textContent = reactions[emotion];
            helper.classList.add('show');
            
            setTimeout(() => {{
                helper.classList.remove('show');
            }}, 3000);
        }}
        
        function closeBitHelper() {{
            document.getElementById('bit-helper').classList.remove('show');
        }}
        
        function submitEntry() {{
            const emotion = document.querySelector('.emotion-btn.selected').dataset.emotion;
            const text = document.getElementById('entry-text').value;
            const lesson = document.getElementById('lesson-learned').value;
            const pattern = document.getElementById('pattern-noticed').value;
            
            if (!text.trim()) {{
                alert('Please write something in your entry.');
                return;
            }}
            
            // Send to backend
            fetch('/api/notebook/entry', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    user_id: '{user_id}',
                    emotion: emotion,
                    entry_text: text,
                    lessons_learned: lesson,
                    pattern_noticed: pattern,
                    market_state: 'live'
                }})
            }})
            .then(res => res.json())
            .then(data => {{
                if (data.success) {{
                    // Show Bit's reaction
                    showBitReaction(emotion);
                    
                    // Clear form
                    document.getElementById('entry-text').value = '';
                    document.getElementById('lesson-learned').value = '';
                    document.getElementById('pattern-noticed').value = '';
                    
                    // Reload after delay
                    setTimeout(() => location.reload(), 2000);
                    
                    // Check for chapter unlock
                    if (data.chapter_unlocked) {{
                        alert('New chapter unlocked: ' + data.chapter_unlocked);
                    }}
                }}
            }})
            .catch(err => console.error('Error submitting entry:', err));
        }}
        
        // Periodically move Bit across screen
        setInterval(() => {{
            const bit = document.querySelector('.bit-presence');
            if (Math.random() > 0.7) {{
                bit.style.animationDuration = (20 + Math.random() * 20) + 's';
            }}
        }}, 10000);
    </script>
</body>
</html>
"""