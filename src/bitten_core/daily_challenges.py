"""
Daily Challenges System for BITTEN
Provides daily XP challenges and weekly events
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import json
import random
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ChallengeType(Enum):
    """Types of daily challenges"""
    PERFECT_EXIT = "perfect_exit"          # Exit within 2 pips of TP
    PATIENCE_PAYS = "patience_pays"        # Wait full cooldown
    SQUAD_SUPPORT = "squad_support"        # Trade same pair as squad
    EARLY_BIRD = "early_bird"              # Trade before 8 AM
    NIGHT_OWL = "night_owl"                # Trade after 10 PM
    WINNING_STREAK = "winning_streak"      # 3 wins in a row
    RISK_DISCIPLINE = "risk_discipline"    # Use exactly 2% risk
    QUICK_TRIGGER = "quick_trigger"        # Execute within 1 min
    PROFIT_TARGET = "profit_target"        # Hit daily profit goal
    MULTI_PAIR = "multi_pair"              # Trade 3 different pairs


class EventType(Enum):
    """Types of weekly events"""
    ELITE_HOURS = "elite_hours"            # 2x XP during specific hours
    SQUAD_WARS = "squad_wars"              # Squad competition
    PERFECT_WEEK = "perfect_week"          # No losing trades all week
    RECRUITMENT_DRIVE = "recruitment_drive" # Bonus XP for recruiting


@dataclass
class Challenge:
    """Daily challenge definition"""
    challenge_id: str
    type: ChallengeType
    name: str
    description: str
    xp_reward: int
    requirement: Dict[str, Any]
    tier_required: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if challenge has expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


@dataclass
class ChallengeProgress:
    """Track user's progress on a challenge"""
    user_id: str
    challenge_id: str
    challenge_type: ChallengeType
    started_at: datetime
    progress: int = 0
    target: int = 1
    completed: bool = False
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage"""
        if self.target == 0:
            return 100.0
        return min(100.0, (self.progress / self.target) * 100)


@dataclass
class WeeklyEvent:
    """Weekly event definition"""
    event_id: str
    type: EventType
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    config: Dict[str, Any]
    active: bool = True


class DailyChallengeManager:
    """Manages daily challenges and weekly events"""
    
    # Challenge templates
    CHALLENGE_TEMPLATES = {
        ChallengeType.PERFECT_EXIT: {
            "name": "Perfect Exit",
            "description": "Exit a trade within 2 pips of your TP",
            "xp_reward": 500,
            "requirement": {"max_deviation_pips": 2}
        },
        ChallengeType.PATIENCE_PAYS: {
            "name": "Patience Pays",
            "description": "Wait the full cooldown before taking next trade",
            "xp_reward": 300,
            "requirement": {"wait_full_cooldown": True}
        },
        ChallengeType.SQUAD_SUPPORT: {
            "name": "Squad Support",
            "description": "Trade the same pair as one of your squad members",
            "xp_reward": 200,
            "requirement": {"match_squad_pair": True}
        },
        ChallengeType.EARLY_BIRD: {
            "name": "Early Bird",
            "description": "Execute a trade before 8 AM your time",
            "xp_reward": 250,
            "requirement": {"before_hour": 8}
        },
        ChallengeType.NIGHT_OWL: {
            "name": "Night Owl",
            "description": "Execute a trade after 10 PM your time",
            "xp_reward": 250,
            "requirement": {"after_hour": 22}
        },
        ChallengeType.WINNING_STREAK: {
            "name": "Hot Streak",
            "description": "Win 3 trades in a row",
            "xp_reward": 750,
            "requirement": {"consecutive_wins": 3}
        },
        ChallengeType.RISK_DISCIPLINE: {
            "name": "Risk Discipline",
            "description": "Use exactly 2% risk on all trades today",
            "xp_reward": 400,
            "requirement": {"exact_risk": 2.0}
        },
        ChallengeType.QUICK_TRIGGER: {
            "name": "Quick Trigger",
            "description": "Execute trade within 1 minute of signal",
            "xp_reward": 350,
            "requirement": {"max_execution_seconds": 60}
        },
        ChallengeType.PROFIT_TARGET: {
            "name": "Daily Target",
            "description": "Achieve $100+ profit today",
            "xp_reward": 600,
            "requirement": {"min_profit": 100}
        },
        ChallengeType.MULTI_PAIR: {
            "name": "Diversified",
            "description": "Trade 3 different currency pairs today",
            "xp_reward": 400,
            "requirement": {"unique_pairs": 3}
        }
    }
    
    def __init__(self, data_dir: str = "data/challenges"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Active challenges by user
        self.user_challenges: Dict[str, List[Challenge]] = {}
        
        # Challenge progress tracking
        self.user_progress: Dict[str, List[ChallengeProgress]] = {}
        
        # Active weekly events
        self.weekly_events: List[WeeklyEvent] = []
        
        # Load existing data
        self._load_challenge_data()
        
        # Generate today's challenges if needed
        self._ensure_daily_challenges()
    
    def get_user_challenges(self, user_id: str, user_tier: str) -> List[Dict[str, Any]]:
        """Get active challenges for a user"""
        # Generate challenges if not exists
        if user_id not in self.user_challenges:
            self._generate_user_challenges(user_id)
        
        challenges = []
        for challenge in self.user_challenges.get(user_id, []):
            if challenge.is_expired():
                continue
            
            # Check tier requirement
            if challenge.tier_required:
                if not self._meets_tier_requirement(user_tier, challenge.tier_required):
                    continue
            
            # Get progress
            progress = self._get_challenge_progress(user_id, challenge.challenge_id)
            
            challenge_data = {
                "challenge_id": challenge.challenge_id,
                "type": challenge.type.value,
                "name": challenge.name,
                "description": challenge.description,
                "xp_reward": challenge.xp_reward,
                "progress": progress.progress if progress else 0,
                "target": progress.target if progress else 1,
                "progress_percent": progress.progress_percent if progress else 0,
                "completed": progress.completed if progress else False,
                "expires_at": challenge.expires_at.isoformat() if challenge.expires_at else None
            }
            
            challenges.append(challenge_data)
        
        return challenges
    
    def track_trade_action(
        self,
        user_id: str,
        action_type: str,
        trade_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Track trade actions for challenge progress"""
        completed_challenges = []
        
        # Get user's active challenges
        if user_id not in self.user_challenges:
            return completed_challenges
        
        for challenge in self.user_challenges[user_id]:
            if challenge.is_expired():
                continue
            
            progress = self._get_or_create_progress(user_id, challenge)
            if progress.completed:
                continue
            
            # Check challenge requirements
            updated = False
            
            if challenge.type == ChallengeType.PERFECT_EXIT and action_type == "trade_closed":
                deviation = trade_data.get("tp_deviation_pips", float('inf'))
                if deviation <= challenge.requirement["max_deviation_pips"]:
                    progress.progress = 1
                    updated = True
            
            elif challenge.type == ChallengeType.PATIENCE_PAYS and action_type == "trade_opened":
                if trade_data.get("waited_full_cooldown", False):
                    progress.progress = 1
                    updated = True
            
            elif challenge.type == ChallengeType.SQUAD_SUPPORT and action_type == "trade_opened":
                if trade_data.get("matches_squad_pair", False):
                    progress.progress = 1
                    updated = True
            
            elif challenge.type == ChallengeType.EARLY_BIRD and action_type == "trade_opened":
                hour = datetime.now().hour
                if hour < challenge.requirement["before_hour"]:
                    progress.progress = 1
                    updated = True
            
            elif challenge.type == ChallengeType.NIGHT_OWL and action_type == "trade_opened":
                hour = datetime.now().hour
                if hour >= challenge.requirement["after_hour"]:
                    progress.progress = 1
                    updated = True
            
            elif challenge.type == ChallengeType.WINNING_STREAK and action_type == "trade_closed":
                if trade_data.get("is_win", False):
                    progress.metadata["current_streak"] = progress.metadata.get("current_streak", 0) + 1
                    progress.progress = progress.metadata["current_streak"]
                    progress.target = challenge.requirement["consecutive_wins"]
                    updated = True
                else:
                    progress.metadata["current_streak"] = 0
                    progress.progress = 0
                    updated = True
            
            elif challenge.type == ChallengeType.RISK_DISCIPLINE and action_type == "trade_opened":
                risk_percent = trade_data.get("risk_percent", 0)
                if risk_percent == challenge.requirement["exact_risk"]:
                    progress.metadata["correct_risks"] = progress.metadata.get("correct_risks", 0) + 1
                    progress.progress = progress.metadata["correct_risks"]
                    progress.target = 3  # Need 3 trades with exact risk
                    updated = True
            
            elif challenge.type == ChallengeType.QUICK_TRIGGER and action_type == "trade_opened":
                execution_time = trade_data.get("execution_seconds", float('inf'))
                if execution_time <= challenge.requirement["max_execution_seconds"]:
                    progress.progress = 1
                    updated = True
            
            elif challenge.type == ChallengeType.PROFIT_TARGET and action_type == "daily_summary":
                daily_profit = trade_data.get("daily_profit", 0)
                if daily_profit >= challenge.requirement["min_profit"]:
                    progress.progress = 1
                    updated = True
            
            elif challenge.type == ChallengeType.MULTI_PAIR and action_type == "trade_opened":
                pair = trade_data.get("pair")
                if pair:
                    pairs_traded = progress.metadata.get("pairs_traded", [])
                    if pair not in pairs_traded:
                        pairs_traded.append(pair)
                        progress.metadata["pairs_traded"] = pairs_traded
                        progress.progress = len(pairs_traded)
                        progress.target = challenge.requirement["unique_pairs"]
                        updated = True
            
            # Check if completed
            if updated and progress.progress >= progress.target and not progress.completed:
                progress.completed = True
                progress.completed_at = datetime.now()
                
                completed_challenges.append({
                    "challenge_id": challenge.challenge_id,
                    "name": challenge.name,
                    "xp_reward": challenge.xp_reward
                })
                
                logger.info(f"User {user_id} completed challenge {challenge.name}")
            
            if updated:
                self._save_progress(user_id)
        
        return completed_challenges
    
    def create_weekly_event(
        self,
        event_type: EventType,
        name: str,
        description: str,
        duration_hours: int,
        config: Dict[str, Any]
    ) -> WeeklyEvent:
        """Create a new weekly event"""
        event = WeeklyEvent(
            event_id=f"{event_type.value}_{datetime.now().timestamp()}",
            type=event_type,
            name=name,
            description=description,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=duration_hours),
            config=config
        )
        
        self.weekly_events.append(event)
        self._save_events()
        
        logger.info(f"Created weekly event: {name}")
        return event
    
    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get currently active weekly events"""
        active = []
        now = datetime.now()
        
        for event in self.weekly_events:
            if event.start_time <= now <= event.end_time and event.active:
                active.append({
                    "event_id": event.event_id,
                    "type": event.type.value,
                    "name": event.name,
                    "description": event.description,
                    "ends_in": str(event.end_time - now),
                    "config": event.config
                })
        
        return active
    
    def check_event_bonus(self, event_type: EventType) -> Optional[float]:
        """Check if an event bonus is active"""
        now = datetime.now()
        
        for event in self.weekly_events:
            if event.type == event_type and event.start_time <= now <= event.end_time and event.active:
                if event_type == EventType.ELITE_HOURS:
                    # Check if current hour is elite hour
                    elite_hours = event.config.get("hours", [6, 7, 8])
                    if now.hour in elite_hours:
                        return event.config.get("multiplier", 2.0)
                
                elif event_type == EventType.RECRUITMENT_DRIVE:
                    return event.config.get("bonus_multiplier", 1.5)
        
        return None
    
    def _generate_user_challenges(self, user_id: str) -> None:
        """Generate daily challenges for a user"""
        # Select 3 random challenges
        challenge_types = list(self.CHALLENGE_TEMPLATES.keys())
        selected_types = random.sample(challenge_types, min(3, len(challenge_types)))
        
        challenges = []
        expires_at = datetime.combine(
            datetime.now().date() + timedelta(days=1),
            time(0, 0)
        )
        
        for challenge_type in selected_types:
            template = self.CHALLENGE_TEMPLATES[challenge_type]
            
            challenge = Challenge(
                challenge_id=f"{user_id}_{challenge_type.value}_{datetime.now().date()}",
                type=challenge_type,
                name=template["name"],
                description=template["description"],
                xp_reward=template["xp_reward"],
                requirement=template["requirement"],
                expires_at=expires_at
            )
            
            challenges.append(challenge)
        
        self.user_challenges[user_id] = challenges
        self._save_challenges(user_id)
    
    def _get_challenge_progress(
        self, 
        user_id: str, 
        challenge_id: str
    ) -> Optional[ChallengeProgress]:
        """Get progress for a specific challenge"""
        if user_id not in self.user_progress:
            return None
        
        for progress in self.user_progress[user_id]:
            if progress.challenge_id == challenge_id:
                return progress
        
        return None
    
    def _get_or_create_progress(
        self,
        user_id: str,
        challenge: Challenge
    ) -> ChallengeProgress:
        """Get or create progress tracking for a challenge"""
        # Initialize user progress if needed
        if user_id not in self.user_progress:
            self.user_progress[user_id] = []
        
        # Find existing progress
        for progress in self.user_progress[user_id]:
            if progress.challenge_id == challenge.challenge_id:
                return progress
        
        # Create new progress
        progress = ChallengeProgress(
            user_id=user_id,
            challenge_id=challenge.challenge_id,
            challenge_type=challenge.type,
            started_at=datetime.now()
        )
        
        self.user_progress[user_id].append(progress)
        return progress
    
    def _meets_tier_requirement(self, user_tier: str, required_tier: str) -> bool:
        """Check if user meets tier requirement"""
        tier_hierarchy = ["NIBBLER", "FANG", "COMMANDER", "APEX"]
        try:
            user_index = tier_hierarchy.index(user_tier)
            required_index = tier_hierarchy.index(required_tier)
            return user_index >= required_index
        except ValueError:
            return True
    
    def _ensure_daily_challenges(self) -> None:
        """Ensure all users have daily challenges"""
        # This would be called by a scheduler at midnight
        # For now, just clean up expired challenges
        for user_id in list(self.user_challenges.keys()):
            active_challenges = [
                c for c in self.user_challenges[user_id] 
                if not c.is_expired()
            ]
            
            if not active_challenges:
                # Generate new challenges
                self._generate_user_challenges(user_id)
    
    def _save_challenges(self, user_id: str) -> None:
        """Save user challenges to file"""
        if user_id not in self.user_challenges:
            return
        
        challenges_file = self.data_dir / f"user_{user_id}_challenges.json"
        
        data = []
        for challenge in self.user_challenges[user_id]:
            data.append({
                "challenge_id": challenge.challenge_id,
                "type": challenge.type.value,
                "name": challenge.name,
                "description": challenge.description,
                "xp_reward": challenge.xp_reward,
                "requirement": challenge.requirement,
                "tier_required": challenge.tier_required,
                "expires_at": challenge.expires_at.isoformat() if challenge.expires_at else None
            })
        
        with open(challenges_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_progress(self, user_id: str) -> None:
        """Save user progress to file"""
        if user_id not in self.user_progress:
            return
        
        progress_file = self.data_dir / f"user_{user_id}_progress.json"
        
        data = []
        for progress in self.user_progress[user_id]:
            data.append({
                "challenge_id": progress.challenge_id,
                "challenge_type": progress.challenge_type.value,
                "started_at": progress.started_at.isoformat(),
                "progress": progress.progress,
                "target": progress.target,
                "completed": progress.completed,
                "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                "metadata": progress.metadata
            })
        
        with open(progress_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_events(self) -> None:
        """Save weekly events to file"""
        events_file = self.data_dir / "weekly_events.json"
        
        data = []
        for event in self.weekly_events:
            data.append({
                "event_id": event.event_id,
                "type": event.type.value,
                "name": event.name,
                "description": event.description,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "config": event.config,
                "active": event.active
            })
        
        with open(events_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_challenge_data(self) -> None:
        """Load all challenge data from files"""
        # Load user challenges
        for challenges_file in self.data_dir.glob("user_*_challenges.json"):
            try:
                user_id = challenges_file.stem.replace("user_", "").replace("_challenges", "")
                
                with open(challenges_file, 'r') as f:
                    data = json.load(f)
                
                challenges = []
                for item in data:
                    challenge = Challenge(
                        challenge_id=item["challenge_id"],
                        type=ChallengeType(item["type"]),
                        name=item["name"],
                        description=item["description"],
                        xp_reward=item["xp_reward"],
                        requirement=item["requirement"],
                        tier_required=item.get("tier_required"),
                        expires_at=datetime.fromisoformat(item["expires_at"]) if item["expires_at"] else None
                    )
                    challenges.append(challenge)
                
                self.user_challenges[user_id] = challenges
                
            except Exception as e:
                logger.error(f"Error loading challenges file {challenges_file}: {e}")
        
        # Load progress
        for progress_file in self.data_dir.glob("user_*_progress.json"):
            try:
                user_id = progress_file.stem.replace("user_", "").replace("_progress", "")
                
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                
                progress_list = []
                for item in data:
                    progress = ChallengeProgress(
                        user_id=user_id,
                        challenge_id=item["challenge_id"],
                        challenge_type=ChallengeType(item["challenge_type"]),
                        started_at=datetime.fromisoformat(item["started_at"]),
                        progress=item["progress"],
                        target=item["target"],
                        completed=item["completed"],
                        completed_at=datetime.fromisoformat(item["completed_at"]) if item["completed_at"] else None,
                        metadata=item["metadata"]
                    )
                    progress_list.append(progress)
                
                self.user_progress[user_id] = progress_list
                
            except Exception as e:
                logger.error(f"Error loading progress file {progress_file}: {e}")
        
        # Load events
        events_file = self.data_dir / "weekly_events.json"
        if events_file.exists():
            try:
                with open(events_file, 'r') as f:
                    data = json.load(f)
                
                for item in data:
                    event = WeeklyEvent(
                        event_id=item["event_id"],
                        type=EventType(item["type"]),
                        name=item["name"],
                        description=item["description"],
                        start_time=datetime.fromisoformat(item["start_time"]),
                        end_time=datetime.fromisoformat(item["end_time"]),
                        config=item["config"],
                        active=item["active"]
                    )
                    self.weekly_events.append(event)
                    
            except Exception as e:
                logger.error(f"Error loading events: {e}")


# Example usage
if __name__ == "__main__":
    manager = DailyChallengeManager()
    
    # Get user challenges
    user_id = "test_user"
    challenges = manager.get_user_challenges(user_id, "FANG")
    print(f"User challenges: {len(challenges)}")
    for challenge in challenges:
        print(f"- {challenge['name']}: {challenge['progress']}/{challenge['target']}")
    
    # Track a trade action
    completed = manager.track_trade_action(
        user_id,
        "trade_opened",
        {"execution_seconds": 45}
    )
    
    if completed:
        print(f"Completed challenges: {completed}")
    
    # Create a weekly event
    event = manager.create_weekly_event(
        EventType.ELITE_HOURS,
        "Morning Elite Hours",
        "2x XP between 6-8 AM",
        duration_hours=48,
        config={"hours": [6, 7, 8], "multiplier": 2.0}
    )
    
    # Check active events
    active_events = manager.get_active_events()
    print(f"Active events: {active_events}")