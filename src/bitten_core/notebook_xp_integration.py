"""
Norman's Notebook XP Integration
Rewards journaling activity and pairs entries with executed signals for growth tracking
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from .normans_notebook import NormansNotebook
from .xp_integration import XPIntegrationManager
from .user_registry_manager import UserRegistryManager

logger = logging.getLogger(__name__)

class JournalXPReward(Enum):
    """XP rewards for different journal activities"""
    BASIC_ENTRY = 2           # Basic journal entry
    STRUCTURED_TEMPLATE = 5   # Using structured template
    SIGNAL_PAIRED = 8         # Entry paired with executed signal
    WEEKLY_REVIEW = 10        # Weekly review completion
    MILESTONE_ENTRY = 15      # Special milestone entry

@dataclass
class SignalExecutionHistory:
    """Represents an executed signal for pairing with journal entries"""
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    executed_at: datetime
    closed_at: Optional[datetime]
    tcs_score: float
    status: str  # 'open', 'closed_win', 'closed_loss'
    result: Optional[str]  # 'success', 'failure'

@dataclass
class NotebookMilestone:
    """Notebook achievement milestones"""
    id: str
    name: str
    description: str
    entries_required: int
    xp_reward: int
    badge_id: Optional[str] = None
    passive_benefit: Optional[str] = None

class NotebookXPIntegration:
    """Enhanced Norman's Notebook with XP rewards and signal pairing"""
    
    def __init__(self, user_id: str, xp_manager: XPIntegrationManager):
        self.user_id = user_id
        self.xp_manager = xp_manager
        self.notebook = NormansNotebook(user_id=user_id)
        self.registry_manager = UserRegistryManager()
        
        # Initialize milestone system
        self.milestones = self._initialize_milestones()
        self.user_milestones_file = f"data/notebook_milestones_{user_id}.json"
        self.user_milestones = self._load_user_milestones()
        
        # Signal history for pairing
        self.signal_history_file = f"data/signal_history_{user_id}.json"
        self.signal_history = self._load_signal_history()
    
    def _initialize_milestones(self) -> List[NotebookMilestone]:
        """Initialize notebook milestone system"""
        return [
            NotebookMilestone(
                id="first_reflection",
                name="First Reflection",
                description="Write your first journal entry",
                entries_required=1,
                xp_reward=5,
                badge_id="reflector_rookie"
            ),
            NotebookMilestone(
                id="habitual_journaler",
                name="Habitual Journaler", 
                description="Complete 10 journal entries",
                entries_required=10,
                xp_reward=25,
                badge_id="journal_keeper"
            ),
            NotebookMilestone(
                id="tactical_reflector",
                name="🧠 Tactical Reflector",
                description="Complete 25 journal entries",
                entries_required=25,
                xp_reward=50,
                badge_id="tactical_reflector"
            ),
            NotebookMilestone(
                id="trading_philosopher",
                name="Trading Philosopher",
                description="Complete 50 journal entries",
                entries_required=50,
                xp_reward=100,
                badge_id="trading_philosopher",
                passive_benefit="Insight Mode: +2 XP for every fire + journal combo"
            ),
            NotebookMilestone(
                id="norman_disciple",
                name="Norman's Disciple",
                description="Complete 100 journal entries",
                entries_required=100,
                xp_reward=200,
                badge_id="norman_disciple",
                passive_benefit="Norman's Wisdom: Unlock private journal pages"
            )
        ]
    
    def _load_user_milestones(self) -> Dict[str, bool]:
        """Load user's achieved milestones"""
        try:
            if os.path.exists(self.user_milestones_file):
                with open(self.user_milestones_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading user milestones: {e}")
        return {}
    
    def _save_user_milestones(self):
        """Save user's achieved milestones"""
        try:
            os.makedirs(os.path.dirname(self.user_milestones_file), exist_ok=True)
            with open(self.user_milestones_file, 'w') as f:
                json.dump(self.user_milestones, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user milestones: {e}")
    
    def _load_signal_history(self) -> List[SignalExecutionHistory]:
        """Load user's signal execution history"""
        try:
            if os.path.exists(self.signal_history_file):
                with open(self.signal_history_file, 'r') as f:
                    data = json.load(f)
                    return [self._dict_to_signal_history(item) for item in data]
        except Exception as e:
            logger.error(f"Error loading signal history: {e}")
        return []
    
    def _save_signal_history(self):
        """Save user's signal execution history"""
        try:
            os.makedirs(os.path.dirname(self.signal_history_file), exist_ok=True)
            data = [self._signal_history_to_dict(signal) for signal in self.signal_history]
            with open(self.signal_history_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving signal history: {e}")
    
    def _dict_to_signal_history(self, data: Dict) -> SignalExecutionHistory:
        """Convert dict to SignalExecutionHistory"""
        return SignalExecutionHistory(
            signal_id=data['signal_id'],
            symbol=data['symbol'],
            direction=data['direction'],
            entry_price=data['entry_price'],
            exit_price=data.get('exit_price'),
            pnl=data.get('pnl'),
            executed_at=datetime.fromisoformat(data['executed_at']),
            closed_at=datetime.fromisoformat(data['closed_at']) if data.get('closed_at') else None,
            tcs_score=data['tcs_score'],
            status=data['status'],
            result=data.get('result')
        )
    
    def _signal_history_to_dict(self, signal: SignalExecutionHistory) -> Dict:
        """Convert SignalExecutionHistory to dict"""
        return {
            'signal_id': signal.signal_id,
            'symbol': signal.symbol,
            'direction': signal.direction,
            'entry_price': signal.entry_price,
            'exit_price': signal.exit_price,
            'pnl': signal.pnl,
            'executed_at': signal.executed_at.isoformat(),
            'closed_at': signal.closed_at.isoformat() if signal.closed_at else None,
            'tcs_score': signal.tcs_score,
            'status': signal.status,
            'result': signal.result
        }
    
    def record_signal_execution(self, 
                              signal_id: str,
                              symbol: str,
                              direction: str,
                              entry_price: float,
                              tcs_score: float) -> bool:
        """Record a signal execution for potential pairing"""
        try:
            signal_history = SignalExecutionHistory(
                signal_id=signal_id,
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                exit_price=None,
                pnl=None,
                executed_at=datetime.now(),
                closed_at=None,
                tcs_score=tcs_score,
                status='open',
                result=None
            )
            
            self.signal_history.append(signal_history)
            # Keep only last 50 signals
            self.signal_history = self.signal_history[-50:]
            self._save_signal_history()
            
            logger.info(f"Recorded signal execution {signal_id} for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error recording signal execution: {e}")
            return False
    
    def update_signal_result(self, 
                           signal_id: str,
                           exit_price: float,
                           pnl: float,
                           result: str) -> bool:
        """Update signal result when trade closes"""
        try:
            for signal in self.signal_history:
                if signal.signal_id == signal_id:
                    signal.exit_price = exit_price
                    signal.pnl = pnl
                    signal.closed_at = datetime.now()
                    signal.status = 'closed_win' if result == 'success' else 'closed_loss'
                    signal.result = result
                    break
            
            self._save_signal_history()
            logger.info(f"Updated signal result {signal_id} for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating signal result: {e}")
            return False
    
    def get_recent_executed_signals(self, days: int = 7) -> List[SignalExecutionHistory]:
        """Get recent executed signals for pairing with journal entries"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            signal for signal in self.signal_history
            if signal.executed_at >= cutoff_date
        ]
    
    def add_journal_entry_with_xp(self,
                                 title: str,
                                 content: str,
                                 category: str = "general",
                                 entry_type: str = "basic",
                                 linked_signal_id: Optional[str] = None,
                                 trade_result: Optional[str] = None,
                                 confidence: Optional[float] = None) -> Dict[str, Any]:
        """Add journal entry and award appropriate XP"""
        
        # Determine XP reward based on entry type
        xp_reward = JournalXPReward.BASIC_ENTRY.value
        xp_reason = "Journal entry"
        
        if entry_type == "structured_template":
            xp_reward = JournalXPReward.STRUCTURED_TEMPLATE.value
            xp_reason = "Structured journal template"
        elif entry_type == "signal_paired" and linked_signal_id:
            xp_reward = JournalXPReward.SIGNAL_PAIRED.value
            xp_reason = "Trade reflection with signal pairing"
        elif entry_type == "weekly_review":
            xp_reward = JournalXPReward.WEEKLY_REVIEW.value
            xp_reason = "Weekly trading review"
        elif entry_type == "milestone":
            xp_reward = JournalXPReward.MILESTONE_ENTRY.value
            xp_reason = "Milestone journal entry"
        
        # Check for insight mode passive benefit
        if self._has_insight_mode_passive() and linked_signal_id:
            xp_reward += 2
            xp_reason += " (+2 Insight Mode bonus)"
        
        # Add the journal entry
        tags = ["journal", category]
        if linked_signal_id:
            tags.extend(["trade_review", "signal_paired"])
        
        entry_data = {
            "linked_signal_id": linked_signal_id,
            "trade_result": trade_result,
            "confidence": confidence,
            "entry_type": entry_type,
            "xp_earned": xp_reward
        }
        
        # Add to Norman's Notebook
        result = self.notebook.add_user_note(
            title=title,
            content=content,
            category=category,
            tags=tags,
            **entry_data
        )
        
        # Award XP through XP Integration Manager
        actual_xp = self.xp_manager.award_xp_with_multipliers(
            self.user_id,
            xp_reward,
            xp_reason,
            f"Journal entry: {title[:50]}..."
        )
        
        # Log XP award in user registry if needed
        self._log_xp_award(actual_xp, xp_reason, linked_signal_id)
        
        # Check for milestone achievements
        milestone_result = self._check_milestone_achievements()
        
        # Update result with XP info
        result.update({
            "xp_earned": actual_xp,
            "xp_reason": xp_reason,
            "milestone_achieved": milestone_result
        })
        
        logger.info(f"Added journal entry for user {self.user_id}, awarded {actual_xp} XP")
        return result
    
    def _has_insight_mode_passive(self) -> bool:
        """Check if user has unlocked Insight Mode passive benefit"""
        return self.user_milestones.get("trading_philosopher", False)
    
    def _log_xp_award(self, xp_amount: int, reason: str, signal_id: Optional[str] = None):
        """Log XP award for audit purposes"""
        try:
            log_file = f"data/xp_log_{self.user_id}.json"
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "amount": xp_amount,
                "reason": reason,
                "source": "notebook",
                "signal_id": signal_id
            }
            
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            
            logs.append(log_entry)
            # Keep only last 100 logs
            logs = logs[-100:]
            
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging XP award: {e}")
    
    def _check_milestone_achievements(self) -> Optional[Dict]:
        """Check and award milestone achievements"""
        current_entry_count = len(self.notebook.get_user_notes())
        
        for milestone in self.milestones:
            if (current_entry_count >= milestone.entries_required and 
                not self.user_milestones.get(milestone.id, False)):
                
                # Mark milestone as achieved
                self.user_milestones[milestone.id] = True
                self._save_user_milestones()
                
                # Award milestone XP
                milestone_xp = self.xp_manager.award_xp_with_multipliers(
                    self.user_id,
                    milestone.xp_reward,
                    f"Milestone: {milestone.name}",
                    milestone.description
                )
                
                logger.info(f"User {self.user_id} achieved milestone: {milestone.name}")
                
                return {
                    "milestone": milestone,
                    "xp_awarded": milestone_xp,
                    "achievement_unlocked": True
                }
        
        return None
    
    def get_signal_pairing_suggestions(self) -> List[Dict]:
        """Get recent signals that could be paired with journal entries"""
        recent_signals = self.get_recent_executed_signals(days=7)
        suggestions = []
        
        for signal in recent_signals:
            # Check if already paired with journal entry
            existing_entries = self.notebook.get_user_notes()
            already_paired = any(
                entry.get('linked_signal_id') == signal.signal_id 
                for entry in existing_entries
            )
            
            if not already_paired:
                suggestion = {
                    "signal_id": signal.signal_id,
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "executed_at": signal.executed_at.isoformat(),
                    "status": signal.status,
                    "pnl": signal.pnl,
                    "tcs_score": signal.tcs_score,
                    "suggested_template": self._suggest_template_for_signal(signal)
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_template_for_signal(self, signal: SignalExecutionHistory) -> str:
        """Suggest appropriate journal template for signal"""
        if signal.status == 'open':
            return "trade_plan"
        elif signal.result == 'success':
            return "success_review"
        elif signal.result == 'failure':
            return "lesson_learned"
        else:
            return "trade_analysis"
    
    def get_notebook_xp_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive notebook XP dashboard"""
        entries = self.notebook.get_user_notes()
        total_entries = len(entries)
        
        # Calculate XP earned from journaling
        total_notebook_xp = sum(
            entry.get('xp_earned', 0) for entry in entries
        )
        
        # Get milestone progress
        next_milestone = None
        for milestone in self.milestones:
            if not self.user_milestones.get(milestone.id, False):
                next_milestone = {
                    "name": milestone.name,
                    "description": milestone.description,
                    "progress": total_entries,
                    "required": milestone.entries_required,
                    "percentage": min(100, (total_entries / milestone.entries_required) * 100),
                    "xp_reward": milestone.xp_reward
                }
                break
        
        # Get recent activity
        recent_entries = entries[-5:] if entries else []
        
        # Get pairing suggestions
        pairing_suggestions = self.get_signal_pairing_suggestions()
        
        return {
            "total_entries": total_entries,
            "total_xp_earned": total_notebook_xp,
            "milestones_achieved": len([m for m in self.user_milestones.values() if m]),
            "next_milestone": next_milestone,
            "recent_entries": recent_entries,
            "pairing_suggestions": pairing_suggestions,
            "insight_mode_active": self._has_insight_mode_passive(),
            "weekly_streak": self._calculate_weekly_streak(),
            "favorite_categories": self._get_favorite_categories(entries)
        }
    
    def _calculate_weekly_streak(self) -> int:
        """Calculate weekly journaling streak"""
        entries = self.notebook.get_user_notes()
        if not entries:
            return 0
        
        # Group entries by week
        weeks_with_entries = set()
        for entry in entries:
            if 'created_at' in entry:
                try:
                    entry_date = datetime.fromisoformat(entry['created_at'])
                    week_key = entry_date.strftime("%Y-W%U")
                    weeks_with_entries.add(week_key)
                except:
                    continue
        
        # Calculate consecutive weeks from current week backwards
        current_week = datetime.now().strftime("%Y-W%U")
        streak = 0
        
        if current_week in weeks_with_entries:
            streak = 1
            # Count backwards
            current_date = datetime.now()
            while True:
                current_date -= timedelta(weeks=1)
                week_key = current_date.strftime("%Y-W%U")
                if week_key in weeks_with_entries:
                    streak += 1
                else:
                    break
        
        return streak
    
    def _get_favorite_categories(self, entries: List[Dict]) -> List[Dict]:
        """Get user's favorite journal categories"""
        category_counts = {}
        for entry in entries:
            category = entry.get('category', 'general')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sort by usage count
        sorted_categories = sorted(
            category_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {"category": cat, "count": count}
            for cat, count in sorted_categories[:3]
        ]

# Helper functions for integration with existing systems
def create_notebook_xp_integration(user_id: str) -> NotebookXPIntegration:
    """Create notebook XP integration instance"""
    xp_manager = XPIntegrationManager()
    return NotebookXPIntegration(user_id, xp_manager)

def award_journal_xp(user_id: str, 
                    entry_type: str = "basic",
                    linked_signal_id: Optional[str] = None) -> int:
    """Quick function to award journal XP"""
    integration = create_notebook_xp_integration(user_id)
    xp_amount = JournalXPReward.BASIC_ENTRY.value
    
    if entry_type == "structured_template":
        xp_amount = JournalXPReward.STRUCTURED_TEMPLATE.value
    elif entry_type == "signal_paired":
        xp_amount = JournalXPReward.SIGNAL_PAIRED.value
    elif entry_type == "weekly_review":
        xp_amount = JournalXPReward.WEEKLY_REVIEW.value
    
    return integration.xp_manager.award_xp_with_multipliers(
        user_id,
        xp_amount,
        f"Journal entry ({entry_type})",
        f"Signal: {linked_signal_id}" if linked_signal_id else ""
    )