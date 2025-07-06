"""
BITTEN Onboarding Data Models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum

class OnboardingState(Enum):
    """Enumeration of all onboarding states"""
    FIRST_CONTACT = "first_contact"
    MARKET_WARFARE_INTRO = "market_warfare_intro"
    KNOWLEDGE_SOURCE = "knowledge_source"
    TRAINING_SETUP = "training_setup"
    FIRST_MISSION = "first_mission"
    PATH_FORWARD = "path_forward"
    THEATER_SELECTION = "theater_selection"
    OATH_OF_ENLISTMENT = "oath_of_enlistment"
    SECURE_LINK = "secure_link"
    CALLSIGN_CREATION = "callsign_creation"
    OPERATIONAL_INTERFACE = "operational_interface"
    CORE_MANEUVERS = "core_maneuvers"
    FIELD_MANUAL = "field_manual"
    PERSONAL_RECORD = "personal_record"
    COMPLETE = "complete"

@dataclass
class OnboardingSession:
    """Session data for tracking onboarding progress"""
    user_id: str
    telegram_id: int
    current_state: str
    state_data: Dict[str, Any]
    started_at: datetime
    last_activity: datetime
    completed_states: List[str]
    has_experience: bool = False
    knowledge_source: str = ""
    selected_theater: str = ""
    callsign: str = ""
    broker_linked: bool = False
    notifications: Dict[str, bool] = None
    variant: str = "standard"
    is_paused: bool = False
    skipped_states: List[str] = None
    
    def __post_init__(self):
        if self.notifications is None:
            self.notifications = {}
        if self.skipped_states is None:
            self.skipped_states = []