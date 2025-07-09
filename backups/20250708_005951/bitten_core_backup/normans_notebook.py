"""
Norman's Notebook - A personal trade journal for growth and self-discovery
Inspired by the journey from dreamer to disciplined trader
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
from collections import defaultdict, Counter
import statistics

class NormansNotebook:
    """A deeply personal trade journal that tracks emotions, patterns, and growth"""
    
    def __init__(self, journal_path: str = "data/normans_journal.json"):
        self.journal_path = journal_path
        self.entries = []
        self.scars = []  # Memorable losses that taught lessons
        self.breakthroughs = []  # Moments of clarity and success
        self.load_journal()
        
        # Emotional keywords for mood detection
        self.emotion_keywords = {
            'excited': ['excited', 'pumped', 'thrilled', 'euphoric', 'moon', 'lambo'],
            'fearful': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'panic'],
            'greedy': ['greedy', 'more', 'double down', 'all in', 'yolo', 'leverage'],
            'confident': ['confident', 'sure', 'certain', 'know', 'obvious', 'easy'],
            'doubtful': ['doubt', 'unsure', 'maybe', 'uncertain', 'questioning'],
            'frustrated': ['frustrated', 'angry', 'pissed', 'stupid', 'hate', 'annoyed'],
            'calm': ['calm', 'patient', 'steady', 'disciplined', 'controlled', 'focused'],
            'regretful': ['regret', 'should have', 'wish', 'mistake', 'wrong', 'failed'],
            'hopeful': ['hope', 'optimistic', 'believe', 'turn around', 'recover'],
            'defeated': ['defeated', 'quit', 'done', 'over', 'lost everything', 'wiped out']
        }
        
        # Pattern templates for common mistakes and successes
        self.pattern_templates = {
            'revenge_trading': ['revenge', 'get back', 'recover losses', 'double down after loss'],
            'fomo': ['fomo', 'missing out', 'everyone else', 'late to the party', 'chase'],
            'overconfidence': ['easy money', 'cant lose', 'guaranteed', 'sure thing'],
            'panic_selling': ['panic sold', 'scared out', 'weak hands', 'shaken out'],
            'diamond_hands': ['held strong', 'conviction', 'stuck to plan', 'trusted analysis'],
            'cut_losses': ['cut losses', 'stopped out', 'risk management', 'protected capital'],
            'took_profits': ['took profits', 'secured gains', 'didnt get greedy', 'sold into strength']
        }
    
    def load_journal(self):
        """Load existing journal entries"""
        if os.path.exists(self.journal_path):
            with open(self.journal_path, 'r') as f:
                data = json.load(f)
                self.entries = data.get('entries', [])
                self.scars = data.get('scars', [])
                self.breakthroughs = data.get('breakthroughs', [])
    
    def save_journal(self):
        """Save journal to disk"""
        os.makedirs(os.path.dirname(self.journal_path), exist_ok=True)
        with open(self.journal_path, 'w') as f:
            json.dump({
                'entries': self.entries,
                'scars': self.scars,
                'breakthroughs': self.breakthroughs
            }, f, indent=2)
    
    def add_entry(self, 
                  trade_id: Optional[str] = None,
                  phase: str = 'general',  # 'before', 'during', 'after', 'general'
                  note: str = "",
                  symbol: Optional[str] = None,
                  pnl: Optional[float] = None):
        """Add a journal entry with automatic mood detection"""
        
        mood = self.detect_mood(note)
        patterns = self.detect_patterns(note)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': trade_id,
            'phase': phase,
            'note': note,
            'symbol': symbol,
            'pnl': pnl,
            'mood': mood,
            'patterns': patterns
        }
        
        self.entries.append(entry)
        
        # Check if this is a scar (memorable loss)
        if pnl and pnl < -100 and phase == 'after':
            self._check_for_scar(entry)
        
        # Check if this is a breakthrough
        if pnl and pnl > 500 and phase == 'after':
            self._check_for_breakthrough(entry)
        
        self.save_journal()
        return entry
    
    def detect_mood(self, text: str) -> Dict[str, float]:
        """Detect emotional state from journal text"""
        text_lower = text.lower()
        mood_scores = defaultdict(float)
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    mood_scores[emotion] += 1
        
        # Normalize scores
        total = sum(mood_scores.values())
        if total > 0:
            mood_scores = {k: v/total for k, v in mood_scores.items()}
        
        return dict(mood_scores)
    
    def detect_patterns(self, text: str) -> List[str]:
        """Detect behavioral patterns from journal text"""
        text_lower = text.lower()
        detected_patterns = []
        
        for pattern, indicators in self.pattern_templates.items():
            for indicator in indicators:
                if indicator in text_lower:
                    detected_patterns.append(pattern)
                    break
        
        return detected_patterns
    
    def _check_for_scar(self, entry: Dict):
        """Check if a loss is significant enough to be a 'scar'"""
        if abs(entry['pnl']) > 100:  # Significant loss
            lesson_prompt = f"What lesson did you learn from this {entry['pnl']:.2f} loss?"
            
            scar = {
                'timestamp': entry['timestamp'],
                'symbol': entry['symbol'],
                'loss': entry['pnl'],
                'note': entry['note'],
                'lesson': lesson_prompt,  # To be filled by user
                'healed': False  # Becomes true when similar situation handled better
            }
            
            self.scars.append(scar)
    
    def _check_for_breakthrough(self, entry: Dict):
        """Check if a win represents a breakthrough moment"""
        if entry['pnl'] > 500:  # Significant win
            breakthrough = {
                'timestamp': entry['timestamp'],
                'symbol': entry['symbol'],
                'gain': entry['pnl'],
                'note': entry['note'],
                'key_insight': "What made this trade different?",  # To be filled
                'replicated': 0  # Track if lesson was successfully repeated
            }
            
            self.breakthroughs.append(breakthrough)
    
    def get_weekly_review(self) -> str:
        """Generate a weekly review in Norman's voice"""
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_entries = [e for e in self.entries 
                         if datetime.fromisoformat(e['timestamp']) > one_week_ago]
        
        if not recent_entries:
            return "📓 Empty week in the notebook. Sometimes silence speaks volumes..."
        
        # Analyze the week
        total_pnl = sum(e.get('pnl', 0) for e in recent_entries if e.get('pnl'))
        mood_counter = Counter()
        pattern_counter = Counter()
        
        for entry in recent_entries:
            for mood, score in entry.get('mood', {}).items():
                mood_counter[mood] += score
            for pattern in entry.get('patterns', []):
                pattern_counter[pattern] += 1
        
        # Find dominant mood and patterns
        dominant_mood = mood_counter.most_common(1)[0][0] if mood_counter else 'neutral'
        common_patterns = pattern_counter.most_common(3)
        
        # Generate review in Norman's voice
        review = f"""
📓 **Norman's Weekly Reflection**
*{datetime.now().strftime('%B %d, %Y')}*

This week's journey: {'profitable' if total_pnl > 0 else 'challenging'}
P&L: ${total_pnl:,.2f}

**Emotional Landscape:**
The dominant feeling was {dominant_mood}. """
        
        if dominant_mood in ['excited', 'greedy']:
            review += "Remember: The market humbles those who forget humility."
        elif dominant_mood in ['fearful', 'defeated']:
            review += "Fear is natural, but don't let it paralyze you. Every master was once a disaster."
        elif dominant_mood == 'calm':
            review += "This is the way. Calm seas make skilled sailors."
        
        if common_patterns:
            review += "\n\n**Patterns I Noticed:**\n"
            for pattern, count in common_patterns:
                if pattern == 'revenge_trading':
                    review += f"- Revenge trading appeared {count} times. The market doesn't care about your ego.\n"
                elif pattern == 'fomo':
                    review += f"- FOMO struck {count} times. There's always another bus coming.\n"
                elif pattern == 'diamond_hands':
                    review += f"- Showed conviction {count} times. Trust your analysis, but verify with price action.\n"
                elif pattern == 'cut_losses':
                    review += f"- Cut losses {count} times. Live to trade another day.\n"
        
        # Add scar check
        recent_scars = [s for s in self.scars if not s['healed']]
        if recent_scars:
            review += f"\n\n**Scars Still Healing:**\n"
            review += f"You carry {len(recent_scars)} lessons from past battles. Have you truly learned?\n"
        
        # Add personalized advice based on patterns
        review += "\n\n**This Week's Medicine:**\n"
        if 'revenge_trading' in [p[0] for p in common_patterns]:
            review += "- When you feel the urge for revenge, step away. The market will be there tomorrow.\n"
        if 'fomo' in [p[0] for p in common_patterns]:
            review += "- Write down 3 reasons before entering any trade. FOMO isn't one of them.\n"
        if total_pnl < -1000:
            review += "- Consider reducing position sizes. Survival first, profits second.\n"
        if total_pnl > 2000:
            review += "- Success is dangerous. Stay humble, stay hungry, stay disciplined.\n"
        
        review += "\n*Remember: I'm not trying to get rich. I'm trying to get right.*"
        
        return review
    
    def find_repeated_mistakes(self, min_occurrences: int = 3) -> Dict[str, List[Dict]]:
        """Find patterns that keep repeating"""
        pattern_entries = defaultdict(list)
        
        for entry in self.entries:
            for pattern in entry.get('patterns', []):
                if pattern in ['revenge_trading', 'fomo', 'overconfidence', 'panic_selling']:
                    pattern_entries[pattern].append(entry)
        
        # Filter to repeated patterns
        repeated = {k: v for k, v in pattern_entries.items() if len(v) >= min_occurrences}
        
        return repeated
    
    def get_growth_trajectory(self) -> Dict[str, any]:
        """Analyze growth over time"""
        if len(self.entries) < 10:
            return {"status": "Too early to tell. Keep journaling."}
        
        # Split entries into early and recent
        midpoint = len(self.entries) // 2
        early_entries = self.entries[:midpoint]
        recent_entries = self.entries[midpoint:]
        
        # Compare emotional states
        early_moods = Counter()
        recent_moods = Counter()
        
        for entry in early_entries:
            for mood, score in entry.get('mood', {}).items():
                early_moods[mood] += score
                
        for entry in recent_entries:
            for mood, score in entry.get('mood', {}).items():
                recent_moods[mood] += score
        
        # Normalize
        early_total = sum(early_moods.values())
        recent_total = sum(recent_moods.values())
        
        if early_total > 0:
            early_moods = {k: v/early_total for k, v in early_moods.items()}
        if recent_total > 0:
            recent_moods = {k: v/recent_total for k, v in recent_moods.items()}
        
        # Calculate improvement metrics
        calm_increase = recent_moods.get('calm', 0) - early_moods.get('calm', 0)
        fear_decrease = early_moods.get('fearful', 0) - recent_moods.get('fearful', 0)
        greed_decrease = early_moods.get('greedy', 0) - recent_moods.get('greedy', 0)
        
        return {
            'early_emotional_state': dict(early_moods),
            'recent_emotional_state': dict(recent_moods),
            'calm_increase': calm_increase,
            'fear_decrease': fear_decrease,
            'greed_decrease': greed_decrease,
            'trajectory': 'improving' if calm_increase > 0.1 else 'work in progress',
            'breakthrough_count': len(self.breakthroughs),
            'unhealed_scars': len([s for s in self.scars if not s['healed']])
        }
    
    def add_trade_reflection(self, trade_id: str, reflection: str):
        """Add a reflection after a trade is closed"""
        entry = self.add_entry(
            trade_id=trade_id,
            phase='after',
            note=reflection
        )
        
        # Check if this reflection shows growth from past scars
        for scar in self.scars:
            if not scar['healed'] and scar['symbol'] in reflection:
                # Look for signs of learning
                if any(phrase in reflection.lower() for phrase in 
                       ['learned from', 'remembered', 'different this time', 'applied lesson']):
                    scar['healed'] = True
                    scar['healing_date'] = datetime.now().isoformat()
        
        return entry
    
    def get_symbol_history(self, symbol: str) -> List[Dict]:
        """Get all journal entries for a specific symbol"""
        return [e for e in self.entries if e.get('symbol') == symbol]
    
    def get_emotional_chart_data(self) -> Dict[str, List]:
        """Get data for plotting emotional journey over time"""
        if not self.entries:
            return {}
        
        # Group by date
        daily_moods = defaultdict(lambda: defaultdict(float))
        
        for entry in self.entries:
            date = datetime.fromisoformat(entry['timestamp']).date()
            for mood, score in entry.get('mood', {}).items():
                daily_moods[date][mood] += score
        
        # Convert to chart format
        dates = sorted(daily_moods.keys())
        mood_series = defaultdict(list)
        
        for date in dates:
            day_total = sum(daily_moods[date].values())
            for mood in self.emotion_keywords.keys():
                if day_total > 0:
                    mood_series[mood].append(daily_moods[date][mood] / day_total)
                else:
                    mood_series[mood].append(0)
        
        return {
            'dates': [d.isoformat() for d in dates],
            'series': dict(mood_series)
        }
    
    def generate_mantra(self) -> str:
        """Generate a personalized mantra based on patterns"""
        repeated_mistakes = self.find_repeated_mistakes()
        
        if 'revenge_trading' in repeated_mistakes:
            return "The market owes me nothing. I owe myself discipline."
        elif 'fomo' in repeated_mistakes:
            return "There's always another trade. Patience is my edge."
        elif 'overconfidence' in repeated_mistakes:
            return "Humility before profits. The market is always the teacher."
        elif len(self.scars) > 5:
            return "My scars are my teachers. Each loss brings wisdom."
        elif len(self.breakthroughs) > 3:
            return "Trust the process. My breakthroughs show the way."
        else:
            return "One trade at a time. One lesson at a time. This is my journey."


class TradingLessonExtractor:
    """Extract and summarize lessons from journal entries"""
    
    def __init__(self, notebook: NormansNotebook):
        self.notebook = notebook
    
    def extract_winning_patterns(self) -> List[Dict]:
        """Find what works from profitable trades"""
        profitable_entries = [e for e in self.notebook.entries 
                            if e.get('pnl', 0) > 100]
        
        winning_patterns = defaultdict(list)
        
        for entry in profitable_entries:
            for pattern in entry.get('patterns', []):
                if pattern in ['diamond_hands', 'cut_losses', 'took_profits']:
                    winning_patterns[pattern].append({
                        'date': entry['timestamp'],
                        'pnl': entry['pnl'],
                        'note': entry['note']
                    })
        
        return dict(winning_patterns)
    
    def create_rules_from_scars(self) -> List[str]:
        """Generate trading rules from painful lessons"""
        rules = []
        
        for scar in self.notebook.scars:
            if scar['loss'] < -500:
                rules.append(f"Never risk more than {abs(scar['loss'])/10:.0f} on a single trade")
            
            if 'fomo' in scar['note'].lower():
                rules.append("If you feel FOMO, wait 24 hours before entering")
            
            if 'revenge' in scar['note'].lower():
                rules.append("After a loss, take a break. No trades for at least 2 hours")
            
            if 'averaged down' in scar['note'].lower():
                rules.append("Set a stop loss and honor it. No averaging down without a plan")
        
        return list(set(rules))  # Remove duplicates
    
    def summarize_journey(self) -> str:
        """Create a narrative summary of the trading journey"""
        total_entries = len(self.notebook.entries)
        total_scars = len(self.notebook.scars)
        healed_scars = len([s for s in self.notebook.scars if s['healed']])
        total_breakthroughs = len(self.notebook.breakthroughs)
        
        trajectory = self.notebook.get_growth_trajectory()
        
        summary = f"""
📖 **The Story So Far**

{total_entries} journal entries tell the tale of transformation.

**The Battles:**
- {total_scars} scars earned in the arena
- {healed_scars} wounds that became wisdom
- {total_breakthroughs} breakthrough moments of clarity

**The Evolution:**
"""
        
        if trajectory.get('trajectory') == 'improving':
            summary += "You're becoming the trader you were meant to be. "
            summary += f"Calmness increased by {trajectory['calm_increase']*100:.0f}%. "
            summary += f"Fear decreased by {trajectory['fear_decrease']*100:.0f}%.\n"
        else:
            summary += "The journey continues. Every master was once a disaster. "
            summary += "Keep showing up, keep learning, keep growing.\n"
        
        # Add current state
        recent_moods = trajectory.get('recent_emotional_state', {})
        if recent_moods:
            dominant = max(recent_moods.items(), key=lambda x: x[1])
            summary += f"\n**Current State:** {dominant[0].title()}\n"
        
        # Add personalized message
        if total_scars > 10:
            summary += "\nYou've been battle-tested. Each scar is a badge of honor, a lesson learned."
        elif total_breakthroughs > 5:
            summary += "\nYour breakthroughs light the path forward. Trust what you've learned."
        else:
            summary += "\nYou're still early in the journey. Be patient with yourself."
        
        summary += "\n\n*Remember: Trading is not about being right. It's about being profitable.*"
        
        return summary


# Integration functions for the broader system
def create_journal_entry_from_trade(trade_data: Dict, notebook: NormansNotebook):
    """Automatically create journal entries from trade data"""
    
    # Entry when position opened
    if trade_data.get('status') == 'open':
        notebook.add_entry(
            trade_id=trade_data['id'],
            phase='before',
            symbol=trade_data['symbol'],
            note=f"Opened position in {trade_data['symbol']}. "
                 f"Risk: ${trade_data.get('risk', 0):.2f}"
        )
    
    # Entry when position closed
    elif trade_data.get('status') == 'closed':
        pnl = trade_data.get('pnl', 0)
        notebook.add_entry(
            trade_id=trade_data['id'],
            phase='after',
            symbol=trade_data['symbol'],
            pnl=pnl,
            note=f"Closed {trade_data['symbol']}. "
                 f"P&L: ${pnl:.2f}. "
                 f"{'Profit' if pnl > 0 else 'Loss'} of {abs(pnl/trade_data.get('entry_price', 1)*100):.1f}%"
        )


def get_journal_insights_for_symbol(symbol: str, notebook: NormansNotebook) -> Dict:
    """Get historical insights for a symbol from journal"""
    history = notebook.get_symbol_history(symbol)
    
    if not history:
        return {
            'has_history': False,
            'message': f"First time trading {symbol}. Make it count."
        }
    
    # Analyze past experiences
    total_pnl = sum(e.get('pnl', 0) for e in history if e.get('pnl'))
    moods = Counter()
    patterns = Counter()
    
    for entry in history:
        for mood, score in entry.get('mood', {}).items():
            moods[mood] += score
        for pattern in entry.get('patterns', []):
            patterns[pattern] += 1
    
    insights = {
        'has_history': True,
        'trade_count': len(history),
        'total_pnl': total_pnl,
        'dominant_mood': moods.most_common(1)[0][0] if moods else 'neutral',
        'common_patterns': [p[0] for p in patterns.most_common(3)],
        'last_experience': history[-1]['note'] if history else None
    }
    
    # Generate wisdom
    if total_pnl < -500:
        insights['warning'] = f"{symbol} has been your nemesis. Different approach needed."
    elif total_pnl > 1000:
        insights['confidence'] = f"{symbol} has treated you well. Stay disciplined."
    
    if 'revenge_trading' in insights['common_patterns']:
        insights['caution'] = "You've revenge traded this before. Stay calm."
    
    return insights