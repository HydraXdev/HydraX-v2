"""
Social Learning System for HydraX Education Platform
Military-inspired squad-based learning with mentorship and study groups
"""

from typing import Dict, List, Optional, Tuple, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
import asyncio
from collections import defaultdict
import json
import math


class SquadRank(Enum):
    """Military-inspired squad rankings"""
    RECRUIT = "Recruit"
    PRIVATE = "Private"
    CORPORAL = "Corporal"
    SERGEANT = "Sergeant"
    LIEUTENANT = "Lieutenant"
    CAPTAIN = "Captain"
    MAJOR = "Major"
    COLONEL = "Colonel"
    GENERAL = "General"


class MissionType(Enum):
    """Types of squad missions"""
    RECON = "Reconnaissance"  # Research missions
    ASSAULT = "Assault"  # Difficult challenges
    DEFENSE = "Defense"  # Bug fixing/security
    SUPPORT = "Support"  # Help teammates
    SPEC_OPS = "Special Ops"  # Elite challenges


class SquadRole(Enum):
    """Roles within a squad"""
    LEADER = "Squad Leader"
    TECH_SPECIALIST = "Tech Specialist"
    STRATEGIST = "Strategist"
    SCOUT = "Scout"
    SUPPORT = "Support"


@dataclass
class SquadMember:
    """Individual squad member data"""
    user_id: str
    username: str
    elo_rating: int = 1200
    role: SquadRole = SquadRole.SCOUT
    missions_completed: int = 0
    squad_xp_contributed: int = 0
    commendations: int = 0
    joined_at: datetime = field(default_factory=datetime.now)
    specializations: List[str] = field(default_factory=list)
    availability_hours: List[int] = field(default_factory=lambda: list(range(24)))  # UTC hours
    timezone: str = "UTC"


@dataclass
class Squad:
    """Military squad unit"""
    squad_id: str
    name: str
    motto: str
    leader_id: str
    members: Dict[str, SquadMember] = field(default_factory=dict)
    squad_elo: int = 1200
    total_xp: int = 0
    missions_completed: int = 0
    wars_won: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    specialization: str = "General"  # Python, Security, AI, etc.
    is_recruiting: bool = True
    max_members: int = 6
    achievements: List[str] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    chat_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Mission:
    """Squad mission objectives"""
    mission_id: str
    name: str
    mission_type: MissionType
    description: str
    objectives: List[Dict[str, Any]]
    difficulty_elo: int
    xp_reward: int
    time_limit: timedelta
    required_members: int
    specialization_bonus: Dict[str, float] = field(default_factory=dict)
    completion_criteria: Dict[str, Any] = field(default_factory=dict)
    weakest_link_multiplier: float = 0.8  # Scoring based on weakest performance


@dataclass
class SquadWar:
    """Competitive squad battles"""
    war_id: str
    squad_a_id: str
    squad_b_id: str
    mission: Mission
    start_time: datetime
    end_time: datetime
    squad_a_score: int = 0
    squad_b_score: int = 0
    status: str = "active"  # active, completed
    battle_log: List[Dict[str, Any]] = field(default_factory=list)


class SquadSystem:
    """
    Military-inspired squad system for collaborative learning
    """
    
    def __init__(self):
        self.squads: Dict[str, Squad] = {}
        self.members_to_squads: Dict[str, str] = {}  # user_id -> squad_id
        self.active_missions: Dict[str, List[Mission]] = {}  # squad_id -> missions
        self.squad_wars: Dict[str, SquadWar] = {}
        self.matchmaking_queue: List[Tuple[str, int]] = []  # (squad_id, elo)
        self.squad_achievements = self._init_achievements()
        
    def _init_achievements(self) -> Dict[str, Dict[str, Any]]:
        """Initialize squad achievement definitions"""
        return {
            "first_blood": {
                "name": "First Blood",
                "description": "Complete your first squad mission",
                "xp": 100,
                "badge": "🎯"
            },
            "band_of_brothers": {
                "name": "Band of Brothers",
                "description": "Complete 10 missions without losing a member",
                "xp": 500,
                "badge": "🤝"
            },
            "elite_force": {
                "name": "Elite Force",
                "description": "Achieve squad ELO rating of 1800+",
                "xp": 1000,
                "badge": "⭐"
            },
            "war_machine": {
                "name": "War Machine",
                "description": "Win 10 squad wars",
                "xp": 750,
                "badge": "🏆"
            },
            "perfect_sync": {
                "name": "Perfect Synchronization",
                "description": "Complete a mission with all members scoring 95%+",
                "xp": 600,
                "badge": "🎖️"
            }
        }
    
    def create_squad(self, leader_id: str, username: str, squad_name: str, 
                    motto: str, specialization: str = "General") -> Squad:
        """Form a new squad"""
        squad_id = f"squad_{leader_id}_{datetime.now().timestamp()}"
        
        leader = SquadMember(
            user_id=leader_id,
            username=username,
            role=SquadRole.LEADER,
            specializations=[specialization]
        )
        
        squad = Squad(
            squad_id=squad_id,
            name=squad_name,
            motto=motto,
            leader_id=leader_id,
            members={leader_id: leader},
            specialization=specialization
        )
        
        self.squads[squad_id] = squad
        self.members_to_squads[leader_id] = squad_id
        
        # Welcome message in squad chat
        self._add_squad_chat(squad_id, "SYSTEM", 
                           f"Squad {squad_name} formed! {motto}")
        
        return squad
    
    def join_squad_matchmaking(self, user_id: str, username: str, 
                              elo_rating: int, specializations: List[str],
                              timezone: str = "UTC") -> Optional[Squad]:
        """Skill-based matchmaking for squad placement"""
        member = SquadMember(
            user_id=user_id,
            username=username,
            elo_rating=elo_rating,
            specializations=specializations,
            timezone=timezone
        )
        
        # Find compatible squads
        compatible_squads = []
        for squad_id, squad in self.squads.items():
            if not squad.is_recruiting or len(squad.members) >= squad.max_members:
                continue
                
            # Check ELO compatibility (within 200 points)
            avg_squad_elo = sum(m.elo_rating for m in squad.members.values()) / len(squad.members)
            if abs(avg_squad_elo - elo_rating) > 200:
                continue
            
            # Check specialization match
            if squad.specialization in specializations or squad.specialization == "General":
                compatibility_score = self._calculate_compatibility(member, squad)
                compatible_squads.append((squad_id, compatibility_score))
        
        if not compatible_squads:
            return None
        
        # Join best matching squad
        compatible_squads.sort(key=lambda x: x[1], reverse=True)
        best_squad_id = compatible_squads[0][0]
        
        return self.join_squad(user_id, member, best_squad_id)
    
    def _calculate_compatibility(self, member: SquadMember, squad: Squad) -> float:
        """Calculate compatibility score for matchmaking"""
        score = 0.0
        
        # ELO similarity (40%)
        avg_squad_elo = sum(m.elo_rating for m in squad.members.values()) / len(squad.members)
        elo_diff = abs(avg_squad_elo - member.elo_rating)
        score += (1 - elo_diff / 500) * 0.4
        
        # Specialization match (30%)
        if squad.specialization in member.specializations:
            score += 0.3
        elif squad.specialization == "General":
            score += 0.15
        
        # Timezone compatibility (20%)
        squad_timezones = [m.timezone for m in squad.members.values()]
        if member.timezone in squad_timezones:
            score += 0.2
        else:
            # Check for overlapping active hours
            overlap = self._calculate_timezone_overlap(member, squad)
            score += overlap * 0.2
        
        # Squad size balance (10%)
        size_ratio = len(squad.members) / squad.max_members
        score += (1 - size_ratio) * 0.1
        
        return score
    
    def _calculate_timezone_overlap(self, member: SquadMember, squad: Squad) -> float:
        """Calculate overlapping active hours between member and squad"""
        squad_active_hours = set()
        for m in squad.members.values():
            squad_active_hours.update(m.availability_hours)
        
        member_hours = set(member.availability_hours)
        overlap = len(squad_active_hours.intersection(member_hours))
        
        return overlap / 24.0
    
    def join_squad(self, user_id: str, member: SquadMember, squad_id: str) -> Optional[Squad]:
        """Join an existing squad"""
        if squad_id not in self.squads:
            return None
            
        squad = self.squads[squad_id]
        if len(squad.members) >= squad.max_members:
            return None
        
        # Assign role based on squad needs
        member.role = self._assign_role(squad)
        
        squad.members[user_id] = member
        self.members_to_squads[user_id] = squad_id
        
        # Update squad ELO
        self._update_squad_elo(squad_id)
        
        # Announce in squad chat
        self._add_squad_chat(squad_id, "SYSTEM", 
                           f"{member.username} joined the squad as {member.role.value}!")
        
        return squad
    
    def _assign_role(self, squad: Squad) -> SquadRole:
        """Assign role based on squad composition"""
        current_roles = [m.role for m in squad.members.values()]
        
        # Priority order for balanced squad
        role_priority = [
            SquadRole.TECH_SPECIALIST,
            SquadRole.STRATEGIST,
            SquadRole.SUPPORT,
            SquadRole.SCOUT
        ]
        
        for role in role_priority:
            if role not in current_roles:
                return role
        
        return SquadRole.SCOUT  # Default role
    
    def create_mission(self, mission_type: MissionType, difficulty_elo: int,
                      specialization: str = "General") -> Mission:
        """Generate a new squad mission"""
        mission_id = f"mission_{datetime.now().timestamp()}"
        
        # Mission templates based on type
        templates = {
            MissionType.RECON: {
                "name": "Code Reconnaissance",
                "description": "Scout and analyze target codebase vulnerabilities",
                "objectives": [
                    {"task": "Identify security flaws", "weight": 0.4},
                    {"task": "Document findings", "weight": 0.3},
                    {"task": "Propose fixes", "weight": 0.3}
                ],
                "time_limit": timedelta(hours=2),
                "required_members": 3
            },
            MissionType.ASSAULT: {
                "name": "Algorithm Assault",
                "description": "Tackle complex algorithmic challenges as a unit",
                "objectives": [
                    {"task": "Solve core algorithm", "weight": 0.5},
                    {"task": "Optimize solution", "weight": 0.3},
                    {"task": "Test edge cases", "weight": 0.2}
                ],
                "time_limit": timedelta(hours=3),
                "required_members": 4
            },
            MissionType.DEFENSE: {
                "name": "Codebase Defense",
                "description": "Fortify code against bugs and vulnerabilities",
                "objectives": [
                    {"task": "Fix critical bugs", "weight": 0.4},
                    {"task": "Add test coverage", "weight": 0.3},
                    {"task": "Refactor weak points", "weight": 0.3}
                ],
                "time_limit": timedelta(hours=2.5),
                "required_members": 3
            },
            MissionType.SUPPORT: {
                "name": "Squad Support Operation",
                "description": "Help squad members overcome their weaknesses",
                "objectives": [
                    {"task": "Mentor struggling member", "weight": 0.4},
                    {"task": "Create learning resources", "weight": 0.3},
                    {"task": "Conduct code review", "weight": 0.3}
                ],
                "time_limit": timedelta(hours=1.5),
                "required_members": 2
            },
            MissionType.SPEC_OPS: {
                "name": "Special Operations",
                "description": "Elite challenge requiring perfect coordination",
                "objectives": [
                    {"task": "Complete elite challenge", "weight": 0.6},
                    {"task": "Achieve time bonus", "weight": 0.2},
                    {"task": "No member failures", "weight": 0.2}
                ],
                "time_limit": timedelta(hours=4),
                "required_members": 5
            }
        }
        
        template = templates[mission_type]
        
        # Calculate XP based on difficulty and type
        base_xp = {
            MissionType.RECON: 200,
            MissionType.ASSAULT: 300,
            MissionType.DEFENSE: 250,
            MissionType.SUPPORT: 150,
            MissionType.SPEC_OPS: 500
        }
        
        xp_reward = int(base_xp[mission_type] * (difficulty_elo / 1200))
        
        mission = Mission(
            mission_id=mission_id,
            name=template["name"],
            mission_type=mission_type,
            description=template["description"],
            objectives=template["objectives"],
            difficulty_elo=difficulty_elo,
            xp_reward=xp_reward,
            time_limit=template["time_limit"],
            required_members=template["required_members"],
            specialization_bonus={specialization: 1.2} if specialization != "General" else {}
        )
        
        return mission
    
    def assign_mission(self, squad_id: str, mission: Mission) -> bool:
        """Assign a mission to a squad"""
        if squad_id not in self.squads:
            return False
            
        squad = self.squads[squad_id]
        
        # Check if squad meets requirements
        if len(squad.members) < mission.required_members:
            return False
        
        # Check if squad ELO is appropriate (within 300 points)
        if abs(squad.squad_elo - mission.difficulty_elo) > 300:
            return False
        
        if squad_id not in self.active_missions:
            self.active_missions[squad_id] = []
        
        self.active_missions[squad_id].append(mission)
        
        # Notify squad
        self._add_squad_chat(squad_id, "COMMAND", 
                           f"New mission assigned: {mission.name}")
        self._add_squad_chat(squad_id, "COMMAND", 
                           f"Difficulty: {mission.difficulty_elo} | Time limit: {mission.time_limit}")
        
        return True
    
    def complete_mission(self, squad_id: str, mission_id: str, 
                        member_scores: Dict[str, float]) -> Dict[str, Any]:
        """Complete a mission with weakest-link scoring"""
        if squad_id not in self.squads or squad_id not in self.active_missions:
            return {"success": False, "error": "Invalid squad or no active missions"}
        
        squad = self.squads[squad_id]
        mission = None
        
        for m in self.active_missions[squad_id]:
            if m.mission_id == mission_id:
                mission = m
                break
        
        if not mission:
            return {"success": False, "error": "Mission not found"}
        
        # Calculate weakest-link score
        min_score = min(member_scores.values())
        avg_score = sum(member_scores.values()) / len(member_scores)
        
        # Final score heavily weights the weakest performance
        final_score = (min_score * mission.weakest_link_multiplier + 
                      avg_score * (1 - mission.weakest_link_multiplier))
        
        # Calculate rewards
        xp_earned = int(mission.xp_reward * final_score)
        
        # Apply specialization bonus
        if squad.specialization in mission.specialization_bonus:
            xp_earned = int(xp_earned * mission.specialization_bonus[squad.specialization])
        
        # Update squad stats
        squad.missions_completed += 1
        squad.total_xp += xp_earned
        
        # Update member stats
        for user_id, score in member_scores.items():
            if user_id in squad.members:
                member = squad.members[user_id]
                member.missions_completed += 1
                member.squad_xp_contributed += int(xp_earned / len(member_scores))
                
                # Commendations for high performers who helped weak links
                if score > 0.9 and min_score > 0.7:
                    member.commendations += 1
        
        # Update squad ELO based on performance
        elo_change = self._calculate_elo_change(squad.squad_elo, mission.difficulty_elo, 
                                               final_score > 0.7)
        squad.squad_elo += elo_change
        
        # Check for achievements
        new_achievements = self._check_squad_achievements(squad, mission, member_scores)
        
        # Remove completed mission
        self.active_missions[squad_id].remove(mission)
        
        # Squad chat announcement
        self._add_squad_chat(squad_id, "COMMAND", 
                           f"Mission complete! Score: {final_score:.1%} | XP: {xp_earned}")
        
        if min_score < 0.5:
            weakest_member = min(member_scores.items(), key=lambda x: x[1])
            self._add_squad_chat(squad_id, "COMMAND", 
                               f"Focus on helping {squad.members[weakest_member[0]].username} improve!")
        
        return {
            "success": True,
            "final_score": final_score,
            "xp_earned": xp_earned,
            "elo_change": elo_change,
            "new_achievements": new_achievements,
            "weakest_link": min_score,
            "average_score": avg_score
        }
    
    def start_squad_war(self, squad_a_id: str, squad_b_id: str, 
                       mission: Mission) -> Optional[SquadWar]:
        """Initiate competitive squad battle"""
        if squad_a_id not in self.squads or squad_b_id not in self.squads:
            return None
        
        war_id = f"war_{datetime.now().timestamp()}"
        
        war = SquadWar(
            war_id=war_id,
            squad_a_id=squad_a_id,
            squad_b_id=squad_b_id,
            mission=mission,
            start_time=datetime.now(),
            end_time=datetime.now() + mission.time_limit
        )
        
        self.squad_wars[war_id] = war
        
        # Notify both squads
        squad_a = self.squads[squad_a_id]
        squad_b = self.squads[squad_b_id]
        
        self._add_squad_chat(squad_a_id, "COMMAND", 
                           f"WAR DECLARED! Enemy: {squad_b.name}")
        self._add_squad_chat(squad_b_id, "COMMAND", 
                           f"WAR DECLARED! Enemy: {squad_a.name}")
        
        return war
    
    def update_war_progress(self, war_id: str, squad_id: str, 
                           progress: Dict[str, Any]) -> bool:
        """Update squad war progress"""
        if war_id not in self.squad_wars:
            return False
        
        war = self.squad_wars[war_id]
        
        # Calculate score based on objectives completed
        score = 0
        for obj in war.mission.objectives:
            if obj["task"] in progress:
                score += progress[obj["task"]] * obj["weight"] * 100
        
        if squad_id == war.squad_a_id:
            war.squad_a_score = int(score)
        elif squad_id == war.squad_b_id:
            war.squad_b_score = int(score)
        else:
            return False
        
        # Log battle event
        war.battle_log.append({
            "timestamp": datetime.now(),
            "squad_id": squad_id,
            "event": f"Progress update: {score:.0f} points",
            "details": progress
        })
        
        # Check if war is complete
        if datetime.now() >= war.end_time:
            self._complete_war(war_id)
        
        return True
    
    def _complete_war(self, war_id: str):
        """Complete a squad war and determine winner"""
        war = self.squad_wars[war_id]
        war.status = "completed"
        
        squad_a = self.squads[war.squad_a_id]
        squad_b = self.squads[war.squad_b_id]
        
        # Determine winner
        if war.squad_a_score > war.squad_b_score:
            winner = squad_a
            loser = squad_b
            winner_id = war.squad_a_id
            loser_id = war.squad_b_id
        elif war.squad_b_score > war.squad_a_score:
            winner = squad_b
            loser = squad_a
            winner_id = war.squad_b_id
            loser_id = war.squad_a_id
        else:
            # Draw
            self._add_squad_chat(war.squad_a_id, "COMMAND", 
                               f"War ended in a draw! Honor maintained.")
            self._add_squad_chat(war.squad_b_id, "COMMAND", 
                               f"War ended in a draw! Honor maintained.")
            return
        
        # Update stats
        winner.wars_won += 1
        
        # Update ELO
        winner_elo_change = self._calculate_elo_change(winner.squad_elo, loser.squad_elo, True)
        loser_elo_change = self._calculate_elo_change(loser.squad_elo, winner.squad_elo, False)
        
        winner.squad_elo += winner_elo_change
        loser.squad_elo += loser_elo_change
        
        # XP rewards
        winner_xp = war.mission.xp_reward
        loser_xp = int(war.mission.xp_reward * 0.3)  # Consolation XP
        
        winner.total_xp += winner_xp
        loser.total_xp += loser_xp
        
        # Announce results
        self._add_squad_chat(winner_id, "COMMAND", 
                           f"VICTORY! Defeated {loser.name} | +{winner_xp} XP | ELO: +{winner_elo_change}")
        self._add_squad_chat(loser_id, "COMMAND", 
                           f"DEFEAT! Lost to {winner.name} | +{loser_xp} XP | ELO: {loser_elo_change}")
    
    def _calculate_elo_change(self, player_elo: int, opponent_elo: int, won: bool) -> int:
        """Calculate ELO rating change"""
        k_factor = 32  # Standard K-factor
        
        expected_score = 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))
        actual_score = 1 if won else 0
        
        return int(k_factor * (actual_score - expected_score))
    
    def _update_squad_elo(self, squad_id: str):
        """Update squad's collective ELO rating"""
        squad = self.squads[squad_id]
        if not squad.members:
            return
        
        # Average member ELO with slight bonus for coordination
        avg_elo = sum(m.elo_rating for m in squad.members.values()) / len(squad.members)
        coordination_bonus = min(50, len(squad.members) * 10)  # Up to 50 point bonus
        
        squad.squad_elo = int(avg_elo + coordination_bonus)
    
    def _check_squad_achievements(self, squad: Squad, mission: Mission,
                                 member_scores: Dict[str, float]) -> List[str]:
        """Check for new squad achievements"""
        new_achievements = []
        
        # First Blood
        if squad.missions_completed == 1 and "first_blood" not in squad.achievements:
            squad.achievements.append("first_blood")
            new_achievements.append("first_blood")
        
        # Perfect Sync
        if all(score >= 0.95 for score in member_scores.values()) and \
           "perfect_sync" not in squad.achievements:
            squad.achievements.append("perfect_sync")
            new_achievements.append("perfect_sync")
        
        # Elite Force
        if squad.squad_elo >= 1800 and "elite_force" not in squad.achievements:
            squad.achievements.append("elite_force")
            new_achievements.append("elite_force")
        
        # War Machine
        if squad.wars_won >= 10 and "war_machine" not in squad.achievements:
            squad.achievements.append("war_machine")
            new_achievements.append("war_machine")
        
        return new_achievements
    
    def _add_squad_chat(self, squad_id: str, sender: str, message: str):
        """Add message to squad chat"""
        if squad_id not in self.squads:
            return
        
        self.squads[squad_id].chat_history.append({
            "timestamp": datetime.now(),
            "sender": sender,
            "message": message
        })
        
        # Keep last 100 messages
        if len(self.squads[squad_id].chat_history) > 100:
            self.squads[squad_id].chat_history = self.squads[squad_id].chat_history[-100:]
    
    def send_squad_message(self, squad_id: str, user_id: str, message: str) -> bool:
        """Send a message to squad chat"""
        if squad_id not in self.squads or user_id not in self.squads[squad_id].members:
            return False
        
        username = self.squads[squad_id].members[user_id].username
        self._add_squad_chat(squad_id, username, message)
        
        return True
    
    def get_squad_leaderboard(self, specialization: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get squad rankings"""
        squads = list(self.squads.values())
        
        if specialization:
            squads = [s for s in squads if s.specialization == specialization]
        
        # Sort by ELO rating
        squads.sort(key=lambda s: s.squad_elo, reverse=True)
        
        leaderboard = []
        for i, squad in enumerate(squads[:50]):  # Top 50
            leaderboard.append({
                "rank": i + 1,
                "squad_id": squad.squad_id,
                "name": squad.name,
                "elo": squad.squad_elo,
                "members": len(squad.members),
                "wars_won": squad.wars_won,
                "total_xp": squad.total_xp,
                "specialization": squad.specialization
            })
        
        return leaderboard


@dataclass
class MentorProfile:
    """Mentor profile and stats"""
    user_id: str
    username: str
    skills: List[str]
    skill_levels: Dict[str, int]  # skill -> level (1-10)
    timezone: str
    availability: List[Dict[str, Any]]  # Available time slots
    languages: List[str]
    personality_tags: List[str]  # patient, strict, encouraging, etc.
    sessions_completed: int = 0
    rating: float = 0.0
    total_ratings: int = 0
    mentees: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    teaching_style: str = "balanced"  # drill-sergeant, supportive, balanced
    max_mentees: int = 5


@dataclass
class MenteeProfile:
    """Mentee profile for matching"""
    user_id: str
    username: str
    learning_goals: List[str]
    current_skills: Dict[str, int]
    timezone: str
    availability: List[Dict[str, Any]]
    preferred_languages: List[str]
    learning_style: str  # visual, hands-on, theoretical
    personality_preferences: List[str]
    current_mentor_id: Optional[str] = None


@dataclass
class MentorshipSession:
    """Individual mentorship session"""
    session_id: str
    mentor_id: str
    mentee_id: str
    scheduled_time: datetime
    duration: timedelta
    topic: str
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    goals: List[str] = field(default_factory=list)
    notes: str = ""
    mentee_feedback: Optional[Dict[str, Any]] = None
    mentor_feedback: Optional[Dict[str, Any]] = None


class MentorshipProgram:
    """
    Military-style mentorship program with advanced matching
    """
    
    def __init__(self):
        self.mentors: Dict[str, MentorProfile] = {}
        self.mentees: Dict[str, MenteeProfile] = {}
        self.active_relationships: Dict[str, List[str]] = {}  # mentor_id -> mentee_ids
        self.sessions: Dict[str, MentorshipSession] = {}
        self.session_history: Dict[str, List[str]] = defaultdict(list)  # user_id -> session_ids
        self.mentor_rewards = self._init_mentor_rewards()
        
    def _init_mentor_rewards(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mentor reward tiers"""
        return {
            "bronze_instructor": {
                "sessions_required": 10,
                "rating_required": 4.0,
                "xp_bonus": 200,
                "title": "Bronze Instructor"
            },
            "silver_instructor": {
                "sessions_required": 25,
                "rating_required": 4.3,
                "xp_bonus": 500,
                "title": "Silver Instructor"
            },
            "gold_instructor": {
                "sessions_required": 50,
                "rating_required": 4.5,
                "xp_bonus": 1000,
                "title": "Gold Instructor"
            },
            "master_instructor": {
                "sessions_required": 100,
                "rating_required": 4.7,
                "xp_bonus": 2000,
                "title": "Master Instructor"
            }
        }
    
    def register_mentor(self, user_id: str, username: str, skills: List[str],
                       skill_levels: Dict[str, int], timezone: str,
                       personality_tags: List[str], teaching_style: str = "balanced") -> MentorProfile:
        """Register as a mentor"""
        mentor = MentorProfile(
            user_id=user_id,
            username=username,
            skills=skills,
            skill_levels=skill_levels,
            timezone=timezone,
            availability=[],
            languages=["English"],  # Default
            personality_tags=personality_tags,
            teaching_style=teaching_style
        )
        
        self.mentors[user_id] = mentor
        self.active_relationships[user_id] = []
        
        return mentor
    
    def register_mentee(self, user_id: str, username: str, learning_goals: List[str],
                       current_skills: Dict[str, int], timezone: str,
                       learning_style: str, personality_preferences: List[str]) -> MenteeProfile:
        """Register as a mentee seeking guidance"""
        mentee = MenteeProfile(
            user_id=user_id,
            username=username,
            learning_goals=learning_goals,
            current_skills=current_skills,
            timezone=timezone,
            availability=[],
            preferred_languages=["English"],
            learning_style=learning_style,
            personality_preferences=personality_preferences
        )
        
        self.mentees[user_id] = mentee
        
        return mentee
    
    def find_mentor_match(self, mentee_id: str) -> List[Tuple[str, float]]:
        """Find compatible mentors using multi-factor matching"""
        if mentee_id not in self.mentees:
            return []
        
        mentee = self.mentees[mentee_id]
        compatible_mentors = []
        
        for mentor_id, mentor in self.mentors.items():
            # Skip if mentor is at capacity
            if len(self.active_relationships.get(mentor_id, [])) >= mentor.max_mentees:
                continue
            
            # Calculate compatibility score
            score = self._calculate_mentor_compatibility(mentor, mentee)
            
            if score > 0.5:  # Minimum compatibility threshold
                compatible_mentors.append((mentor_id, score))
        
        # Sort by compatibility score
        compatible_mentors.sort(key=lambda x: x[1], reverse=True)
        
        return compatible_mentors[:10]  # Return top 10 matches
    
    def _calculate_mentor_compatibility(self, mentor: MentorProfile, 
                                      mentee: MenteeProfile) -> float:
        """Calculate compatibility score between mentor and mentee"""
        score = 0.0
        
        # Skill match (35%)
        skill_overlap = set(mentor.skills).intersection(set(mentee.learning_goals))
        if skill_overlap:
            # Check skill level difference (mentor should be significantly better)
            avg_level_diff = 0
            for skill in skill_overlap:
                mentor_level = mentor.skill_levels.get(skill, 0)
                mentee_level = mentee.current_skills.get(skill, 0)
                if mentor_level > mentee_level + 2:  # At least 2 levels higher
                    avg_level_diff += (mentor_level - mentee_level) / 10
            
            score += min(0.35, avg_level_diff / len(skill_overlap))
        
        # Timezone compatibility (25%)
        if mentor.timezone == mentee.timezone:
            score += 0.25
        else:
            # Calculate time difference
            time_diff = abs(self._get_timezone_offset(mentor.timezone) - 
                          self._get_timezone_offset(mentee.timezone))
            if time_diff <= 3:
                score += 0.15
            elif time_diff <= 6:
                score += 0.05
        
        # Personality match (20%)
        personality_match = set(mentor.personality_tags).intersection(
            set(mentee.personality_preferences))
        score += (len(personality_match) / max(len(mentee.personality_preferences), 1)) * 0.2
        
        # Teaching style match (10%)
        style_compatibility = {
            ("drill-sergeant", "hands-on"): 0.8,
            ("supportive", "visual"): 0.9,
            ("balanced", "theoretical"): 0.7,
            ("balanced", "visual"): 0.8,
            ("balanced", "hands-on"): 0.8,
            ("supportive", "theoretical"): 0.6,
            ("drill-sergeant", "theoretical"): 0.5
        }
        
        style_score = style_compatibility.get(
            (mentor.teaching_style, mentee.learning_style), 0.5)
        score += style_score * 0.1
        
        # Rating bonus (10%)
        if mentor.rating > 0:
            score += (mentor.rating / 5.0) * 0.1
        
        return score
    
    def _get_timezone_offset(self, timezone: str) -> int:
        """Get timezone offset from UTC (simplified)"""
        # Simplified timezone mapping
        offsets = {
            "UTC": 0, "EST": -5, "CST": -6, "MST": -7, "PST": -8,
            "CET": 1, "EET": 2, "JST": 9, "AEST": 10
        }
        return offsets.get(timezone, 0)
    
    def establish_mentorship(self, mentor_id: str, mentee_id: str) -> bool:
        """Establish a mentor-mentee relationship"""
        if mentor_id not in self.mentors or mentee_id not in self.mentees:
            return False
        
        mentor = self.mentors[mentor_id]
        mentee = self.mentees[mentee_id]
        
        # Check capacity
        if len(self.active_relationships.get(mentor_id, [])) >= mentor.max_mentees:
            return False
        
        # Check if mentee already has a mentor
        if mentee.current_mentor_id:
            return False
        
        # Establish relationship
        if mentor_id not in self.active_relationships:
            self.active_relationships[mentor_id] = []
        
        self.active_relationships[mentor_id].append(mentee_id)
        mentee.current_mentor_id = mentor_id
        mentor.mentees.append(mentee_id)
        
        # Send welcome notification
        self._send_notification(mentor_id, 
                              f"New mentee assigned: {mentee.username}")
        self._send_notification(mentee_id, 
                              f"Mentor assigned: {mentor.username}")
        
        return True
    
    def schedule_session(self, mentor_id: str, mentee_id: str,
                        scheduled_time: datetime, duration: timedelta,
                        topic: str, goals: List[str]) -> Optional[MentorshipSession]:
        """Schedule a mentorship session"""
        # Verify relationship exists
        if mentor_id not in self.active_relationships or \
           mentee_id not in self.active_relationships[mentor_id]:
            return None
        
        session_id = f"session_{datetime.now().timestamp()}"
        
        session = MentorshipSession(
            session_id=session_id,
            mentor_id=mentor_id,
            mentee_id=mentee_id,
            scheduled_time=scheduled_time,
            duration=duration,
            topic=topic,
            goals=goals
        )
        
        self.sessions[session_id] = session
        self.session_history[mentor_id].append(session_id)
        self.session_history[mentee_id].append(session_id)
        
        # Set reminders
        self._schedule_reminder(mentor_id, session_id, scheduled_time - timedelta(hours=1))
        self._schedule_reminder(mentee_id, session_id, scheduled_time - timedelta(hours=1))
        
        return session
    
    def complete_session(self, session_id: str, mentor_notes: str,
                        mentee_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a mentorship session"""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        session.status = "completed"
        session.notes = mentor_notes
        session.mentee_feedback = mentee_feedback
        
        # Update mentor stats
        mentor = self.mentors[session.mentor_id]
        mentor.sessions_completed += 1
        
        # Update rating
        if "rating" in mentee_feedback:
            old_total = mentor.rating * mentor.total_ratings
            mentor.total_ratings += 1
            mentor.rating = (old_total + mentee_feedback["rating"]) / mentor.total_ratings
        
        # Check for mentor rewards
        rewards_earned = self._check_mentor_rewards(mentor)
        
        # Track progress for mentee
        mentee = self.mentees[session.mentee_id]
        progress = self._track_mentee_progress(mentee, session)
        
        return {
            "success": True,
            "mentor_stats": {
                "sessions_completed": mentor.sessions_completed,
                "current_rating": mentor.rating,
                "rewards_earned": rewards_earned
            },
            "mentee_progress": progress
        }
    
    def _check_mentor_rewards(self, mentor: MentorProfile) -> List[str]:
        """Check if mentor earned new rewards"""
        rewards_earned = []
        
        for reward_id, requirements in self.mentor_rewards.items():
            if mentor.sessions_completed >= requirements["sessions_required"] and \
               mentor.rating >= requirements["rating_required"]:
                if reward_id not in mentor.specializations:
                    mentor.specializations.append(reward_id)
                    rewards_earned.append(requirements["title"])
        
        return rewards_earned
    
    def _track_mentee_progress(self, mentee: MenteeProfile, 
                              session: MentorshipSession) -> Dict[str, Any]:
        """Track mentee's learning progress"""
        progress = {
            "session_topic": session.topic,
            "goals_addressed": session.goals,
            "total_sessions": len([s for s in self.session_history[mentee.user_id]
                                 if self.sessions[s].status == "completed"])
        }
        
        # Update skill levels based on session topic
        if session.topic in mentee.current_skills:
            # Increment skill level (simplified)
            mentee.current_skills[session.topic] = min(10, 
                                                      mentee.current_skills[session.topic] + 0.2)
            progress["skill_improvement"] = {
                session.topic: mentee.current_skills[session.topic]
            }
        
        return progress
    
    def get_mentor_leaderboard(self, skill: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get top mentors by rating and sessions"""
        mentors = list(self.mentors.values())
        
        if skill:
            mentors = [m for m in mentors if skill in m.skills]
        
        # Sort by composite score (rating * sessions^0.5)
        mentors.sort(key=lambda m: m.rating * (m.sessions_completed ** 0.5), reverse=True)
        
        leaderboard = []
        for i, mentor in enumerate(mentors[:20]):
            leaderboard.append({
                "rank": i + 1,
                "mentor_id": mentor.user_id,
                "username": mentor.username,
                "rating": mentor.rating,
                "sessions": mentor.sessions_completed,
                "specializations": mentor.specializations,
                "active_mentees": len([m for m in mentor.mentees 
                                     if m in self.active_relationships.get(mentor.user_id, [])])
            })
        
        return leaderboard
    
    def _send_notification(self, user_id: str, message: str):
        """Send notification to user (placeholder)"""
        # In real implementation, this would integrate with notification system
        print(f"Notification to {user_id}: {message}")
    
    def _schedule_reminder(self, user_id: str, session_id: str, reminder_time: datetime):
        """Schedule session reminder (placeholder)"""
        # In real implementation, this would integrate with scheduling system
        pass


@dataclass
class StudyGroup:
    """Topic-focused study group"""
    group_id: str
    name: str
    topic: str
    description: str
    creator_id: str
    moderators: List[str]
    members: Dict[str, Dict[str, Any]]  # user_id -> member info
    max_members: int = 20
    is_public: bool = True
    required_level: int = 0  # Minimum skill level
    scheduled_sessions: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    total_study_hours: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    discussion_threads: List[Dict[str, Any]] = field(default_factory=list)


class StudyGroups:
    """
    Study group system for collaborative learning
    """
    
    def __init__(self):
        self.groups: Dict[str, StudyGroup] = {}
        self.user_groups: Dict[str, List[str]] = defaultdict(list)  # user_id -> group_ids
        self.group_achievements = self._init_group_achievements()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session info
        
    def _init_group_achievements(self) -> Dict[str, Dict[str, Any]]:
        """Initialize study group achievements"""
        return {
            "study_marathon": {
                "name": "Study Marathon",
                "description": "Complete 24 hours of group study",
                "requirement": {"study_hours": 24},
                "xp": 500
            },
            "knowledge_fortress": {
                "name": "Knowledge Fortress",
                "description": "Maintain 20+ active members",
                "requirement": {"active_members": 20},
                "xp": 750
            },
            "resource_arsenal": {
                "name": "Resource Arsenal",
                "description": "Share 50+ quality resources",
                "requirement": {"resources": 50},
                "xp": 600
            },
            "discussion_commander": {
                "name": "Discussion Commander",
                "description": "Host 100+ discussion threads",
                "requirement": {"discussions": 100},
                "xp": 800
            }
        }
    
    def create_group(self, creator_id: str, name: str, topic: str,
                    description: str, is_public: bool = True,
                    required_level: int = 0) -> StudyGroup:
        """Create a new study group"""
        group_id = f"group_{datetime.now().timestamp()}"
        
        group = StudyGroup(
            group_id=group_id,
            name=name,
            topic=topic,
            description=description,
            creator_id=creator_id,
            moderators=[creator_id],
            members={creator_id: {
                "joined_at": datetime.now(),
                "contributions": 0,
                "study_hours": 0.0,
                "last_active": datetime.now()
            }},
            is_public=is_public,
            required_level=required_level
        )
        
        self.groups[group_id] = group
        self.user_groups[creator_id].append(group_id)
        
        # Create welcome thread
        self._create_discussion_thread(group_id, creator_id, 
                                     "Welcome to " + name,
                                     f"Welcome soldiers! Our mission: Master {topic}. {description}")
        
        return group
    
    def join_group(self, user_id: str, group_id: str, user_level: int) -> bool:
        """Join a study group"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        # Check requirements
        if len(group.members) >= group.max_members:
            return False
        
        if user_level < group.required_level:
            return False
        
        if user_id in group.members:
            return False
        
        # Add member
        group.members[user_id] = {
            "joined_at": datetime.now(),
            "contributions": 0,
            "study_hours": 0.0,
            "last_active": datetime.now()
        }
        
        self.user_groups[user_id].append(group_id)
        group.last_activity = datetime.now()
        
        return True
    
    def schedule_study_session(self, group_id: str, organizer_id: str,
                             title: str, start_time: datetime,
                             duration: timedelta, topics: List[str]) -> Optional[str]:
        """Schedule a group study session"""
        if group_id not in self.groups:
            return None
        
        group = self.groups[group_id]
        
        # Check if organizer is a member
        if organizer_id not in group.members:
            return None
        
        session_id = f"session_{datetime.now().timestamp()}"
        
        session = {
            "session_id": session_id,
            "title": title,
            "organizer_id": organizer_id,
            "start_time": start_time,
            "duration": duration,
            "topics": topics,
            "registered_members": [organizer_id],
            "status": "scheduled"
        }
        
        group.scheduled_sessions.append(session)
        
        # Sort sessions by start time
        group.scheduled_sessions.sort(key=lambda s: s["start_time"])
        
        return session_id
    
    def start_study_session(self, group_id: str, session_id: str) -> bool:
        """Start a scheduled study session"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        # Find session
        session = None
        for s in group.scheduled_sessions:
            if s["session_id"] == session_id:
                session = s
                break
        
        if not session or session["status"] != "scheduled":
            return False
        
        # Start session
        session["status"] = "active"
        session["actual_start"] = datetime.now()
        
        self.active_sessions[session_id] = {
            "group_id": group_id,
            "session": session,
            "active_members": set(session["registered_members"]),
            "contributions": defaultdict(int)
        }
        
        return True
    
    def end_study_session(self, session_id: str) -> Dict[str, Any]:
        """End an active study session"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session_info = self.active_sessions[session_id]
        group = self.groups[session_info["group_id"]]
        session = session_info["session"]
        
        # Calculate duration
        actual_duration = datetime.now() - session["actual_start"]
        hours_studied = actual_duration.total_seconds() / 3600
        
        # Update member stats
        for member_id in session_info["active_members"]:
            if member_id in group.members:
                group.members[member_id]["study_hours"] += hours_studied
                group.members[member_id]["last_active"] = datetime.now()
        
        # Update group stats
        group.total_study_hours += hours_studied * len(session_info["active_members"])
        
        # Mark session as completed
        session["status"] = "completed"
        session["actual_duration"] = actual_duration
        
        # Check achievements
        new_achievements = self._check_group_achievements(group)
        
        # Clean up
        del self.active_sessions[session_id]
        
        return {
            "success": True,
            "hours_studied": hours_studied,
            "participants": len(session_info["active_members"]),
            "new_achievements": new_achievements
        }
    
    def share_resource(self, group_id: str, user_id: str,
                      title: str, url: str, resource_type: str,
                      description: str) -> bool:
        """Share a learning resource with the group"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        if user_id not in group.members:
            return False
        
        resource = {
            "resource_id": f"res_{datetime.now().timestamp()}",
            "title": title,
            "url": url,
            "type": resource_type,  # article, video, tutorial, etc.
            "description": description,
            "shared_by": user_id,
            "shared_at": datetime.now(),
            "upvotes": 0,
            "views": 0
        }
        
        group.resources.append(resource)
        group.members[user_id]["contributions"] += 1
        group.last_activity = datetime.now()
        
        return True
    
    def _create_discussion_thread(self, group_id: str, author_id: str,
                                title: str, content: str) -> Optional[str]:
        """Create a discussion thread"""
        if group_id not in self.groups:
            return None
        
        group = self.groups[group_id]
        
        thread_id = f"thread_{datetime.now().timestamp()}"
        
        thread = {
            "thread_id": thread_id,
            "title": title,
            "author_id": author_id,
            "content": content,
            "created_at": datetime.now(),
            "replies": [],
            "pinned": False,
            "locked": False
        }
        
        group.discussion_threads.append(thread)
        group.last_activity = datetime.now()
        
        return thread_id
    
    def add_thread_reply(self, group_id: str, thread_id: str,
                        user_id: str, content: str) -> bool:
        """Add a reply to a discussion thread"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        # Find thread
        thread = None
        for t in group.discussion_threads:
            if t["thread_id"] == thread_id:
                thread = t
                break
        
        if not thread or thread["locked"]:
            return False
        
        if user_id not in group.members:
            return False
        
        reply = {
            "reply_id": f"reply_{datetime.now().timestamp()}",
            "author_id": user_id,
            "content": content,
            "created_at": datetime.now(),
            "upvotes": 0
        }
        
        thread["replies"].append(reply)
        group.members[user_id]["contributions"] += 1
        group.last_activity = datetime.now()
        
        return True
    
    def moderate_discussion(self, group_id: str, moderator_id: str,
                          thread_id: str, action: str) -> bool:
        """Moderate a discussion thread"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        # Check if user is a moderator
        if moderator_id not in group.moderators:
            return False
        
        # Find thread
        thread = None
        for t in group.discussion_threads:
            if t["thread_id"] == thread_id:
                thread = t
                break
        
        if not thread:
            return False
        
        if action == "pin":
            thread["pinned"] = True
        elif action == "unpin":
            thread["pinned"] = False
        elif action == "lock":
            thread["locked"] = True
        elif action == "unlock":
            thread["locked"] = False
        elif action == "delete":
            group.discussion_threads.remove(thread)
        
        return True
    
    def _check_group_achievements(self, group: StudyGroup) -> List[str]:
        """Check for new group achievements"""
        new_achievements = []
        
        for achievement_id, requirements in self.group_achievements.items():
            if achievement_id in group.achievements:
                continue
            
            # Check requirements
            met = True
            for key, value in requirements["requirement"].items():
                if key == "study_hours" and group.total_study_hours < value:
                    met = False
                elif key == "active_members":
                    active_count = sum(1 for m in group.members.values()
                                     if (datetime.now() - m["last_active"]).days < 7)
                    if active_count < value:
                        met = False
                elif key == "resources" and len(group.resources) < value:
                    met = False
                elif key == "discussions" and len(group.discussion_threads) < value:
                    met = False
            
            if met:
                group.achievements.append(achievement_id)
                new_achievements.append(requirements["name"])
        
        return new_achievements
    
    def get_recommended_groups(self, user_id: str, user_skills: List[str],
                             user_level: int) -> List[Dict[str, Any]]:
        """Get recommended study groups for a user"""
        recommendations = []
        
        for group_id, group in self.groups.items():
            # Skip groups user is already in
            if user_id in group.members:
                continue
            
            # Skip full groups
            if len(group.members) >= group.max_members:
                continue
            
            # Skip groups above user level
            if user_level < group.required_level:
                continue
            
            # Calculate relevance score
            score = 0.0
            
            # Topic relevance
            if group.topic in user_skills:
                score += 0.5
            
            # Activity level
            days_inactive = (datetime.now() - group.last_activity).days
            if days_inactive < 1:
                score += 0.3
            elif days_inactive < 7:
                score += 0.1
            
            # Size preference (not too small, not too large)
            size_ratio = len(group.members) / group.max_members
            if 0.3 <= size_ratio <= 0.8:
                score += 0.2
            
            if score > 0:
                recommendations.append({
                    "group_id": group_id,
                    "name": group.name,
                    "topic": group.topic,
                    "members": len(group.members),
                    "activity_score": score,
                    "last_active": group.last_activity
                })
        
        # Sort by score
        recommendations.sort(key=lambda r: r["activity_score"], reverse=True)
        
        return recommendations[:10]


class SocialLearningIntegration:
    """
    Integration layer for social learning with existing systems
    """
    
    def __init__(self, xp_system=None, achievement_system=None):
        self.squad_system = SquadSystem()
        self.mentorship_program = MentorshipProgram()
        self.study_groups = StudyGroups()
        self.xp_system = xp_system
        self.achievement_system = achievement_system
        
    def award_squad_xp(self, squad_id: str, xp_amount: int):
        """Award XP to all squad members"""
        squad = self.squad_system.squads.get(squad_id)
        if not squad:
            return
        
        # Distribute XP based on contribution
        for member in squad.members.values():
            member_xp = int(xp_amount * (member.squad_xp_contributed / max(squad.total_xp, 1)))
            if self.xp_system:
                self.xp_system.add_experience(member.user_id, member_xp, 
                                            f"Squad mission: {squad.name}")
    
    def check_social_achievements(self, user_id: str) -> List[str]:
        """Check for social learning achievements"""
        achievements = []
        
        # Squad achievements
        if user_id in self.squad_system.members_to_squads:
            squad_id = self.squad_system.members_to_squads[user_id]
            squad = self.squad_system.squads[squad_id]
            
            if self.achievement_system:
                # Team player achievement
                if len(squad.members) >= 5:
                    self.achievement_system.unlock_achievement(user_id, "team_player")
                    achievements.append("team_player")
                
                # War hero achievement
                if squad.wars_won >= 5:
                    self.achievement_system.unlock_achievement(user_id, "war_hero")
                    achievements.append("war_hero")
        
        # Mentorship achievements
        if user_id in self.mentorship_program.mentors:
            mentor = self.mentorship_program.mentors[user_id]
            
            if self.achievement_system:
                # Guiding light achievement
                if mentor.sessions_completed >= 10:
                    self.achievement_system.unlock_achievement(user_id, "guiding_light")
                    achievements.append("guiding_light")
        
        return achievements
    
    def get_user_social_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive social learning stats for a user"""
        stats = {
            "squad": None,
            "mentorship": None,
            "study_groups": [],
            "social_rank": "Lone Wolf"
        }
        
        # Squad stats
        if user_id in self.squad_system.members_to_squads:
            squad_id = self.squad_system.members_to_squads[user_id]
            squad = self.squad_system.squads[squad_id]
            member = squad.members[user_id]
            
            stats["squad"] = {
                "name": squad.name,
                "role": member.role.value,
                "missions_completed": member.missions_completed,
                "commendations": member.commendations,
                "squad_elo": squad.squad_elo
            }
        
        # Mentorship stats
        if user_id in self.mentorship_program.mentors:
            mentor = self.mentorship_program.mentors[user_id]
            stats["mentorship"] = {
                "role": "Mentor",
                "sessions": mentor.sessions_completed,
                "rating": mentor.rating,
                "active_mentees": len(mentor.mentees)
            }
        elif user_id in self.mentorship_program.mentees:
            mentee = self.mentorship_program.mentees[user_id]
            stats["mentorship"] = {
                "role": "Mentee",
                "current_mentor": mentee.current_mentor_id,
                "sessions_attended": len(self.mentorship_program.session_history.get(user_id, []))
            }
        
        # Study group stats
        for group_id in self.study_groups.user_groups.get(user_id, []):
            group = self.study_groups.groups[group_id]
            member_info = group.members.get(user_id, {})
            
            stats["study_groups"].append({
                "name": group.name,
                "topic": group.topic,
                "study_hours": member_info.get("study_hours", 0),
                "contributions": member_info.get("contributions", 0)
            })
        
        # Calculate social rank
        total_engagement = 0
        if stats["squad"]:
            total_engagement += stats["squad"]["missions_completed"] * 10
        if stats["mentorship"]:
            if stats["mentorship"]["role"] == "Mentor":
                total_engagement += stats["mentorship"]["sessions"] * 15
            else:
                total_engagement += stats["mentorship"]["sessions_attended"] * 5
        for group in stats["study_groups"]:
            total_engagement += group["study_hours"] * 2
        
        # Assign rank based on engagement
        if total_engagement >= 1000:
            stats["social_rank"] = "Community General"
        elif total_engagement >= 500:
            stats["social_rank"] = "Squad Commander"
        elif total_engagement >= 200:
            stats["social_rank"] = "Team Sergeant"
        elif total_engagement >= 50:
            stats["social_rank"] = "Active Recruit"
        elif total_engagement > 0:
            stats["social_rank"] = "Fresh Recruit"
        
        return stats