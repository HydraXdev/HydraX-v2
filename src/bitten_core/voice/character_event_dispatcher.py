#!/usr/bin/env python3
"""
🎭 BITTEN CHARACTER EVENT DISPATCHER
Routes trade events to appropriate BITTEN Protocol personalities
Ensures each character handles their specialty instead of one character doing everything
"""

import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

class TradeEventType(Enum):
    """Trade event types for character routing"""
    MISSION_BRIEFING = "mission_briefing"
    FIRE_CONFIRMATION = "fire_confirmation" 
    EXECUTION_SUCCESS = "execution_success"
    EXECUTION_FAILURE = "execution_failure"
    TAKE_PROFIT_HIT = "take_profit_hit"
    STOP_LOSS_HIT = "stop_loss_hit"
    TIMEOUT_WARNING = "timeout_warning"
    SYSTEM_STATUS = "system_status"
    RISK_WARNING = "risk_warning"
    MARKET_ANALYSIS = "market_analysis"
    PRECISION_TRADE = "precision_trade"
    RECRUITMENT = "recruitment"

class CharacterEventDispatcher:
    """
    Routes trade events to appropriate BITTEN Protocol characters
    Each character handles their area of expertise
    """
    
    def __init__(self):
        # Character event routing map
        self.event_routing = {
            TradeEventType.MISSION_BRIEFING: ["ATHENA"],  # Strategic command
            TradeEventType.FIRE_CONFIRMATION: ["ATHENA", "BIT"],  # Command + system core
            TradeEventType.EXECUTION_SUCCESS: ["NEXUS", "BIT", "ATHENA"],  # Victory celebration
            TradeEventType.EXECUTION_FAILURE: ["DRILL", "DOC"],  # Discipline + protection
            TradeEventType.TAKE_PROFIT_HIT: ["NEXUS", "BIT"],  # Celebration specialists
            TradeEventType.STOP_LOSS_HIT: ["DOC", "DRILL"],  # Protection + learning
            TradeEventType.TIMEOUT_WARNING: ["DRILL"],  # Discipline enforcement
            TradeEventType.SYSTEM_STATUS: ["BIT", "OVERWATCH"],  # System + intelligence
            TradeEventType.RISK_WARNING: ["DOC"],  # Protection specialist
            TradeEventType.MARKET_ANALYSIS: ["OVERWATCH"],  # Intelligence specialist
            TradeEventType.PRECISION_TRADE: ["STEALTH"],  # Efficiency specialist
            TradeEventType.RECRUITMENT: ["NEXUS"]  # Recruitment specialist
        }
        
        # Character personality modules
        self.characters = {}
        self._load_character_modules()
    
    def _load_character_modules(self):
        """Load all character personality modules"""
        try:
            # ATHENA - Strategic Commander
            from .athena_personality import (
                get_mission_briefing, get_fire_confirmation, 
                get_execution_success, get_execution_failure
            )
            self.characters['ATHENA'] = {
                'mission_briefing': get_mission_briefing,
                'fire_confirmation': get_fire_confirmation,
                'execution_success': get_execution_success,
                'execution_failure': get_execution_failure
            }
        except ImportError:
            pass
            
        try:
            # BIT - System Core
            from .bit_personality import get_bit_response, bit_react_trade
            self.characters['BIT'] = {
                'system_status': get_bit_response,
                'trade_reaction': bit_react_trade
            }
        except ImportError:
            pass
        
        try:
            # NEXUS - Recruitment and Celebrations
            from .nexus_personality import (
                get_take_profit_celebration, get_execution_celebration, get_recruitment_message
            )
            self.characters['NEXUS'] = {
                'take_profit_celebration': get_take_profit_celebration,
                'execution_celebration': get_execution_celebration,
                'recruitment_message': get_recruitment_message
            }
        except ImportError:
            pass
        
        try:
            # DOC - Protection and Risk Management
            from .doc_personality import (
                get_stop_loss_protection, get_execution_failure_protection, 
                get_risk_management_warning, get_reassurance
            )
            self.characters['DOC'] = {
                'stop_loss_protection': get_stop_loss_protection,
                'execution_failure_protection': get_execution_failure_protection,
                'risk_management_warning': get_risk_management_warning,
                'reassurance': get_reassurance
            }
        except ImportError:
            pass
    
    def route_event(self, event_type: TradeEventType, event_data: Dict, user_context: Dict = None) -> Dict:
        """
        Route trade event to appropriate character(s)
        Returns character response with personality attribution
        """
        
        # Get possible characters for this event type
        possible_characters = self.event_routing.get(event_type, ["ATHENA"])
        
        # Select character based on context or rotation
        selected_character = self._select_character(possible_characters, event_data, user_context)
        
        # Generate response from selected character
        response = self._generate_character_response(selected_character, event_type, event_data, user_context)
        
        return {
            'character': selected_character,
            'response': response,
            'event_type': event_type.value,
            'timestamp': datetime.now().isoformat()
        }
    
    def _select_character(self, possible_characters: List[str], event_data: Dict, user_context: Dict) -> str:
        """Select appropriate character based on context"""
        
        # Context-based selection rules
        user_tier = user_context.get('tier', 'NIBBLER') if user_context else 'NIBBLER'
        
        # Tier-based character preferences
        if user_tier in ['COMMANDER', ''] and 'ATHENA' in possible_characters:
            return 'ATHENA'  # Strategic command for elite users
        elif user_tier == 'NIBBLER' and 'NEXUS' in possible_characters:
            return 'NEXUS'  # Recruitment focus for new users
        elif event_data.get('precision_required') and 'STEALTH' in possible_characters:
            return 'STEALTH'  # Precision trades
        elif event_data.get('risk_level', 'normal') == 'high' and 'DOC' in possible_characters:
            return 'DOC'  # Risk protection
        
        # Default: rotate or pick most appropriate
        return possible_characters[0] if possible_characters else 'ATHENA'
    
    def _generate_character_response(self, character: str, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate response from specific character"""
        
        # Character-specific response generation
        if character == 'ATHENA':
            return self._generate_athena_response(event_type, event_data, user_context)
        elif character == 'NEXUS':
            return self._generate_nexus_response(event_type, event_data, user_context)
        elif character == 'DRILL':
            return self._generate_drill_response(event_type, event_data, user_context)
        elif character == 'DOC':
            return self._generate_doc_response(event_type, event_data, user_context)
        elif character == 'BIT':
            return self._generate_bit_response(event_type, event_data, user_context)
        elif character == 'OVERWATCH':
            return self._generate_overwatch_response(event_type, event_data, user_context)
        elif character == 'STEALTH':
            return self._generate_stealth_response(event_type, event_data, user_context)
        else:
            return f"Character {character} response for {event_type.value}"
    
    def _generate_athena_response(self, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate ATHENA strategic command responses"""
        if event_type == TradeEventType.MISSION_BRIEFING:
            if 'ATHENA' in self.characters and 'mission_briefing' in self.characters['ATHENA']:
                return self.characters['ATHENA']['mission_briefing'](
                    event_data, 
                    user_context.get('tier', 'NIBBLER'), 
                    event_data.get('mission_id', 'UNKNOWN')
                )
        elif event_type == TradeEventType.FIRE_CONFIRMATION:
            if 'ATHENA' in self.characters and 'fire_confirmation' in self.characters['ATHENA']:
                return self.characters['ATHENA']['fire_confirmation'](
                    event_data, 
                    datetime.now().isoformat()
                )
        
        # Fallback responses
        return self._get_athena_fallback(event_type, event_data)
    
    def _generate_nexus_response(self, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate NEXUS recruitment/celebration responses"""
        
        # Try to use actual NEXUS personality module first
        if 'NEXUS' in self.characters:
            try:
                if event_type == TradeEventType.TAKE_PROFIT_HIT:
                    profit_pips = event_data.get('profit_pips', 0)
                    return self.characters['NEXUS']['take_profit_celebration'](event_data, profit_pips)
                elif event_type == TradeEventType.EXECUTION_SUCCESS:
                    return self.characters['NEXUS']['execution_celebration'](event_data, event_data)
                elif event_type == TradeEventType.RECRUITMENT:
                    user_tier = user_context.get('tier', 'NIBBLER') if user_context else 'NIBBLER'
                    context = event_data.get('context', 'general')
                    return self.characters['NEXUS']['recruitment_message'](user_tier, context)
            except Exception:
                pass  # Fall back to static responses
        
        # Fallback static responses
        nexus_responses = {
            TradeEventType.EXECUTION_SUCCESS: [
                "Affirmative! Mission accomplished. Outstanding work, recruit!",
                "Tactical excellence demonstrated. Ready for the next deployment?",
                "Mission parameters achieved. You're proving operational readiness."
            ],
            TradeEventType.TAKE_PROFIT_HIT: [
                "Target eliminated. Mission accomplished, operative!",
                "Precision strike confirmed. Tactical victory achieved.",
                "Objective secured. You're showing real potential for advanced operations."
            ]
        }
        
        responses = nexus_responses.get(event_type, ["Mission status acknowledged."])
        return random.choice(responses)
    
    def _generate_drill_response(self, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate DRILL discipline/learning responses"""
        drill_responses = {
            TradeEventType.EXECUTION_FAILURE: [
                "FAILURE DETECTED. ANALYZE ERROR. DO NOT REPEAT MISTAKE.",
                "EXECUTION FAILED. UNDERSTAND THE CAUSE. DISCIPLINE PREVENTS FUTURE FAILURE.",
                "MISSION ABORTED. REVIEW PARAMETERS. THIS IS LEARNING DATA."
            ],
            TradeEventType.STOP_LOSS_HIT: [
                "STOP LOSS EXECUTED. DISCIPLINE MAINTAINED. THIS IS PROTECTION.",
                "TACTICAL WITHDRAWAL COMPLETE. PROTOCOL FOLLOWED. ANALYZE AND REPEAT.",
                "RISK MANAGEMENT SUCCESSFUL. DISCIPLINE SAVES CAPITAL."
            ],
            TradeEventType.TIMEOUT_WARNING: [
                "TIMEOUT DETECTED. EXECUTION WINDOW CLOSED. INVESTIGATE IMMEDIATELY.",
                "MISSION TIMELINE EXCEEDED. SYSTEM REQUIRES ATTENTION.",
                "DELAY UNACCEPTABLE. OPERATIONAL REVIEW REQUIRED."
            ]
        }
        
        responses = drill_responses.get(event_type, ["DISCIPLINE IS VICTORY."])
        return random.choice(responses)
    
    def _generate_doc_response(self, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate DOC protection/risk responses"""
        
        # Try to use actual DOC personality module first
        if 'DOC' in self.characters:
            try:
                if event_type == TradeEventType.STOP_LOSS_HIT:
                    loss_pips = event_data.get('loss_pips', 0)
                    return self.characters['DOC']['stop_loss_protection'](event_data, loss_pips)
                elif event_type == TradeEventType.EXECUTION_FAILURE:
                    error_data = event_data.get('error_data', {'message': 'Execution failed'})
                    return self.characters['DOC']['execution_failure_protection'](event_data, error_data)
                elif event_type == TradeEventType.RISK_WARNING:
                    risk_data = event_data.get('risk_data', {'risk_level': 'moderate'})
                    return self.characters['DOC']['risk_management_warning'](risk_data)
            except Exception:
                pass  # Fall back to static responses
        
        # Fallback static responses
        doc_responses = {
            TradeEventType.EXECUTION_FAILURE: [
                "Trade rejected. Your capital remains protected. Analyzing cause.",
                "Execution blocked. Safety protocols engaged. Your funds are secure.",
                "Mission failed, but protection systems held. Capital preserved."
            ],
            TradeEventType.STOP_LOSS_HIT: [
                "Stop loss triggered as planned. Risk management successful.",
                "Capital protection engaged. Defensive systems operational.",
                "Strategic withdrawal executed. Your account remains stable."
            ],
            TradeEventType.RISK_WARNING: [
                "Risk threshold approaching. Capital protection is paramount.",
                "Elevated risk detected. Proceed with enhanced caution.",
                "Market volatility high. Protection protocols recommended."
            ]
        }
        
        responses = doc_responses.get(event_type, ["Capital protection is paramount."])
        return random.choice(responses)
    
    def _generate_bit_response(self, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate BIT system core responses"""
        bit_responses = {
            TradeEventType.EXECUTION_SUCCESS: [
                "Target vaporized. XP inbound. *BIT's eyes glow with satisfaction*",
                "Clean kill confirmed. Now scratch behind the ears.",
                "Mission complete. *BIT purrs with tactical precision*"
            ],
            TradeEventType.SYSTEM_STATUS: [
                "*BIT's eyes glow green* All systems purring perfectly.",
                "I'm Bit. System's running smooth as Delta whiskey.",
                "Born in a truck, raised in the charts. Everything's nominal."
            ],
            TradeEventType.FIRE_CONFIRMATION: [
                "*BIT's whiskers twitch* Fire vector locked. This one's mine.",
                "Sniper ready. Fire clean. *BIT's tactical mode engaged*",
                "Target acquired. *BIT's eyes narrow with precision*"
            ]
        }
        
        responses = bit_responses.get(event_type, ["*BIT observes quietly*"])
        return random.choice(responses)
    
    def _generate_overwatch_response(self, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate OVERWATCH intelligence responses"""
        overwatch_responses = {
            TradeEventType.MARKET_ANALYSIS: [
                "Intel incoming: Market surveillance indicates optimal positioning.",
                "Strategic intelligence processed. Pattern recognition complete.",
                "Operational intelligence summary: Market conditions analyzed."
            ],
            TradeEventType.SYSTEM_STATUS: [
                "Intel systems online. Market surveillance active.",
                "Tactical assessment: All monitoring systems operational.",
                "Intelligence gathered. System performance nominal."
            ]
        }
        
        responses = overwatch_responses.get(event_type, ["Intel systems online."])
        return random.choice(responses)
    
    def _generate_stealth_response(self, event_type: TradeEventType, event_data: Dict, user_context: Dict) -> str:
        """Generate STEALTH minimal responses"""
        stealth_responses = {
            TradeEventType.PRECISION_TRADE: [
                "Target acquired.",
                "Precision required.",
                "Silent approach optimal."
            ],
            TradeEventType.EXECUTION_SUCCESS: [
                "Confirmed.",
                "Precision achieved.",
                "..."
            ]
        }
        
        responses = stealth_responses.get(event_type, ["..."])
        return random.choice(responses)
    
    def _get_athena_fallback(self, event_type: TradeEventType, event_data: Dict) -> str:
        """Fallback ATHENA responses when modules aren't available"""
        fallback_responses = {
            TradeEventType.EXECUTION_SUCCESS: "Direct hit confirmed. Mission parameters achieved.",
            TradeEventType.EXECUTION_FAILURE: "Mission aborted. Tactical assessment required.",
            TradeEventType.FIRE_CONFIRMATION: "Mission active. Strike vector acquired. Fire when ready."
        }
        
        return fallback_responses.get(event_type, "Strategic command acknowledged.")

# Global dispatcher instance
character_dispatcher = CharacterEventDispatcher()

# Convenience functions for easy integration
def route_trade_event(event_type: str, event_data: Dict, user_context: Dict = None) -> Dict:
    """Route trade event to appropriate character"""
    try:
        event_enum = TradeEventType(event_type)
        return character_dispatcher.route_event(event_enum, event_data, user_context)
    except ValueError:
        # Unknown event type, default to ATHENA
        return {
            'character': 'ATHENA',
            'response': f"Strategic assessment: {event_type} event processed.",
            'event_type': event_type,
            'timestamp': datetime.now().isoformat()
        }

def get_mission_briefing_response(signal_data: Dict, user_tier: str, mission_id: str) -> Dict:
    """Get mission briefing from ATHENA"""
    return character_dispatcher.route_event(
        TradeEventType.MISSION_BRIEFING,
        signal_data,
        {'tier': user_tier, 'mission_id': mission_id}
    )

def get_trade_execution_response(signal_data: Dict, execution_result: Dict, user_context: Dict = None) -> Dict:
    """Get trade execution response from appropriate character"""
    event_type = TradeEventType.EXECUTION_SUCCESS if execution_result.get('success') else TradeEventType.EXECUTION_FAILURE
    
    event_data = {**signal_data, **execution_result}
    return character_dispatcher.route_event(event_type, event_data, user_context)

def get_take_profit_response(signal_data: Dict, profit_pips: float, user_context: Dict = None) -> Dict:
    """Get take profit celebration from appropriate character"""
    event_data = {**signal_data, 'profit_pips': profit_pips}
    return character_dispatcher.route_event(TradeEventType.TAKE_PROFIT_HIT, event_data, user_context)

def get_stop_loss_response(signal_data: Dict, loss_pips: float, user_context: Dict = None) -> Dict:
    """Get stop loss response from appropriate character"""
    event_data = {**signal_data, 'loss_pips': loss_pips}
    return character_dispatcher.route_event(TradeEventType.STOP_LOSS_HIT, event_data, user_context)