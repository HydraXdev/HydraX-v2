"""
Notebook Mission Integration
Connects user trading notes with mission briefings for seamless note-taking experience
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from .normans_notebook import NormansNotebook
from .mission_briefing_generator import MissionBriefingGenerator

class NotebookMissionIntegration:
    """Integrates user notes with mission briefings"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.notebook = NormansNotebook(user_id=user_id)
    
    def add_mission_note(self, 
                        mission_id: str,
                        symbol: str,
                        note_content: str,
                        note_type: str = "trade_plan") -> Dict:
        """Add a note related to a specific mission"""
        
        title_map = {
            "trade_plan": f"Trade Plan - {symbol}",
            "analysis": f"Analysis - {symbol}",
            "reminder": f"Reminder - {symbol}",
            "lesson": f"Lesson - {symbol}",
            "review": f"Review - {symbol}"
        }
        
        return self.notebook.add_user_note(
            title=title_map.get(note_type, f"Note - {symbol}"),
            content=note_content,
            category=note_type if note_type in ["strategy", "analysis", "lesson", "goal"] else "general",
            tags=[note_type, "mission", symbol.lower()],
            symbol=symbol,
            trade_id=mission_id
        )
    
    def get_mission_notes(self, mission_id: str) -> List[Dict]:
        """Get all notes for a specific mission"""
        return self.notebook.get_notes_by_trade(mission_id)
    
    def get_symbol_insights(self, symbol: str) -> Dict:
        """Get trading insights for a symbol from user notes"""
        notes = self.notebook.get_notes_by_symbol(symbol)
        
        # Categorize notes
        strategies = [n for n in notes if n.get('category') == 'strategy']
        analyses = [n for n in notes if n.get('category') == 'analysis']
        lessons = [n for n in notes if n.get('category') == 'lesson']
        
        # Extract key insights
        insights = {
            'has_notes': len(notes) > 0,
            'total_notes': len(notes),
            'strategy_notes': len(strategies),
            'analysis_notes': len(analyses),
            'lesson_notes': len(lessons),
            'recent_notes': notes[:3] if notes else [],
            'key_tags': self._extract_common_tags(notes),
            'last_updated': max([n['updated_at'] for n in notes]) if notes else None
        }
        
        # Generate insight summary
        if len(notes) == 0:
            insights['summary'] = f"📝 First time analyzing {symbol} - create your first note!"
        elif len(strategies) > 0:
            insights['summary'] = f"📚 You have {len(strategies)} strategy notes for {symbol}"
        elif len(lessons) > 0:
            insights['summary'] = f"💡 {len(lessons)} lessons learned from {symbol}"
        else:
            insights['summary'] = f"📊 {len(notes)} notes available for {symbol}"
        
        return insights
    
    def create_mission_template(self, symbol: str, mission_type: str) -> Dict:
        """Create a pre-filled note template for a mission"""
        templates = {
            "trade_plan": {
                "title": f"Trade Plan - {symbol}",
                "content": f"""📋 **Trade Plan for {symbol}**

**Entry Strategy:**
- Setup: 
- Trigger: 
- Confirmation: 

**Risk Management:**
- Position Size: 
- Stop Loss: 
- Take Profit 1: 
- Take Profit 2: 

**Why This Trade:**


**Market Context:**
- Trend: 
- Key Levels: 
- News/Events: 

**Trade Management:**
- Break-even move: 
- Partial exit plan: 
- Full exit criteria: 

**Notes:**

---
*Created from mission briefing: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
""",
                "category": "strategy",
                "tags": ["plan", "strategy", symbol.lower(), "mission"]
            },
            
            "quick_analysis": {
                "title": f"Quick Analysis - {symbol}",
                "content": f"""📈 **Quick Analysis for {symbol}**

**Technical View:**
- Price Action: 
- Support/Resistance: 
- Indicators: 

**Fundamental View:**
- News Impact: 
- Economic Calendar: 
- Sentiment: 

**Trading Opportunity:**
- Direction: 
- Timeframe: 
- Risk Level: 

**Key Points:**
- 
- 
- 

**Next Steps:**

---
*Mission analysis: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
""",
                "category": "analysis",
                "tags": ["analysis", "technical", symbol.lower(), "mission"]
            },
            
            "trade_reminder": {
                "title": f"Trade Reminder - {symbol}",
                "content": f"""⚠️ **Trading Reminders for {symbol}**

**Before Entry:**
- [ ] Confirm setup
- [ ] Check risk/reward
- [ ] Set stop loss
- [ ] Calculate position size

**During Trade:**
- [ ] Monitor key levels
- [ ] Watch for exit signals
- [ ] Stay disciplined

**After Trade:**
- [ ] Record results
- [ ] Note lessons learned
- [ ] Update strategy if needed

**Symbol-Specific Notes:**


**Personal Reminders:**

---
*Mission reminder: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
""",
                "category": "reminder",
                "tags": ["reminder", "checklist", symbol.lower(), "mission"]
            }
        }
        
        return templates.get(mission_type, templates["trade_plan"])
    
    def get_notebook_dashboard(self) -> Dict:
        """Get dashboard data for user's notebook"""
        stats = self.notebook.get_notes_stats()
        recent_notes = self.notebook.get_user_notes()[:5]  # Last 5 notes
        pinned_notes = self.notebook.get_user_notes(pinned_only=True)
        
        # Quick access categories
        categories = {
            'strategies': self.notebook.get_user_notes(category='strategy')[:3],
            'analyses': self.notebook.get_user_notes(category='analysis')[:3],
            'lessons': self.notebook.get_user_notes(category='lesson')[:3],
            'goals': self.notebook.get_user_notes(category='goal')[:3]
        }
        
        return {
            'stats': stats,
            'recent_notes': recent_notes,
            'pinned_notes': pinned_notes,
            'categories': categories,
            'templates_available': list(self.notebook.create_quick_note_templates().keys()),
            'notebook_health': self._calculate_notebook_health(stats)
        }
    
    def suggest_note_for_mission(self, symbol: str, mission_data: Dict) -> Dict:
        """Suggest what type of note to create for a mission"""
        existing_notes = self.notebook.get_notes_by_symbol(symbol)
        
        # Analyze what's missing
        has_strategy = any(n.get('category') == 'strategy' for n in existing_notes)
        has_analysis = any(n.get('category') == 'analysis' for n in existing_notes)
        recent_lesson = any(n.get('category') == 'lesson' for n in existing_notes[-3:])
        
        suggestions = []
        
        if not has_strategy:
            suggestions.append({
                'type': 'trade_plan',
                'priority': 'high',
                'reason': f"No trading strategy notes found for {symbol}",
                'template': 'trade_plan'
            })
        
        if not has_analysis:
            suggestions.append({
                'type': 'quick_analysis',
                'priority': 'medium', 
                'reason': f"Create technical analysis for {symbol}",
                'template': 'quick_analysis'
            })
        
        if len(existing_notes) == 0:
            suggestions.append({
                'type': 'trade_reminder',
                'priority': 'medium',
                'reason': f"First time trading {symbol} - set up reminders",
                'template': 'trade_reminder'
            })
        
        # Default suggestion
        if not suggestions:
            suggestions.append({
                'type': 'quick_note',
                'priority': 'low',
                'reason': "Add any thoughts about this trade opportunity",
                'template': 'quick_note'
            })
        
        return {
            'symbol': symbol,
            'suggestions': suggestions,
            'existing_notes_count': len(existing_notes),
            'recommended': suggestions[0] if suggestions else None
        }
    
    def _extract_common_tags(self, notes: List[Dict]) -> List[str]:
        """Extract most common tags from notes"""
        tag_counts = {}
        for note in notes:
            for tag in note.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Return top 5 tags
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _calculate_notebook_health(self, stats: Dict) -> Dict:
        """Calculate notebook usage health metrics"""
        total_notes = stats.get('total_notes', 0)
        notes_this_week = stats.get('notes_this_week', 0)
        categories = stats.get('categories', {})
        
        # Health score calculation
        score = 0
        feedback = []
        
        # Activity score (0-30 points)
        if notes_this_week >= 5:
            score += 30
            feedback.append("📈 Excellent weekly activity!")
        elif notes_this_week >= 2:
            score += 20
            feedback.append("📊 Good weekly activity")
        elif notes_this_week >= 1:
            score += 10
            feedback.append("📝 Some activity this week")
        else:
            feedback.append("⏰ No notes this week - consider daily journaling")
        
        # Diversity score (0-30 points)
        category_count = len(categories)
        if category_count >= 4:
            score += 30
            feedback.append("🎯 Great category diversity!")
        elif category_count >= 2:
            score += 20
            feedback.append("📚 Good category usage")
        elif category_count >= 1:
            score += 10
            feedback.append("📖 Using some categories")
        else:
            feedback.append("📋 Try different note categories")
        
        # Volume score (0-40 points)
        if total_notes >= 50:
            score += 40
            feedback.append("🏆 Dedicated note-taker!")
        elif total_notes >= 20:
            score += 30
            feedback.append("📚 Building good habits")
        elif total_notes >= 10:
            score += 20
            feedback.append("📝 Getting started")
        elif total_notes >= 5:
            score += 10
            feedback.append("🌱 Beginning your journey")
        else:
            feedback.append("🆕 Welcome to note-taking!")
        
        # Health rating
        if score >= 80:
            rating = "Excellent"
            color = "green"
        elif score >= 60:
            rating = "Good"
            color = "blue"
        elif score >= 40:
            rating = "Fair"
            color = "orange"
        else:
            rating = "Needs Improvement"
            color = "red"
        
        return {
            'score': score,
            'rating': rating,
            'color': color,
            'feedback': feedback,
            'suggestions': self._get_health_suggestions(score, stats)
        }
    
    def _get_health_suggestions(self, score: int, stats: Dict) -> List[str]:
        """Get suggestions to improve notebook health"""
        suggestions = []
        
        if stats.get('notes_this_week', 0) < 2:
            suggestions.append("Try to add at least 2 notes per week")
        
        if len(stats.get('categories', {})) < 3:
            suggestions.append("Explore different note categories (strategy, analysis, lessons)")
        
        if stats.get('pinned_notes', 0) == 0:
            suggestions.append("Pin important notes for quick access")
        
        if score < 40:
            suggestions.append("Use note templates to get started quickly")
            suggestions.append("Add notes before and after trades")
        
        return suggestions

# Helper functions for webapp integration
def get_notebook_data_for_mission(user_id: str, symbol: str, mission_id: str) -> Dict:
    """Get all notebook data relevant to a mission"""
    integration = NotebookMissionIntegration(user_id)
    
    return {
        'symbol_insights': integration.get_symbol_insights(symbol),
        'mission_notes': integration.get_mission_notes(mission_id),
        'note_suggestions': integration.suggest_note_for_mission(symbol, {}),
        'quick_templates': {
            'trade_plan': integration.create_mission_template(symbol, 'trade_plan'),
            'analysis': integration.create_mission_template(symbol, 'quick_analysis'),
            'reminder': integration.create_mission_template(symbol, 'trade_reminder')
        }
    }

def create_note_from_mission(user_id: str, mission_id: str, symbol: str, 
                           note_type: str, content: str) -> Dict:
    """Create a note from mission briefing interface"""
    integration = NotebookMissionIntegration(user_id)
    return integration.add_mission_note(mission_id, symbol, content, note_type)