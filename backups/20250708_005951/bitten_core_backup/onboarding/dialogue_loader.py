"""
BITTEN Onboarding Dialogue Loader

Loads and manages dialogue content from onboarding_dialogue.json with
dynamic variable substitution and character voice management.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DialogueLoader:
    """Loads and manages onboarding dialogue content"""
    
    def __init__(self, dialogue_path: str = "docs/onboarding/onboarding_dialogue.json"):
        self.dialogue_path = Path(dialogue_path)
        self.dialogue_data = {}
        self.variable_pattern = re.compile(r'\{([A-Z_]+)\}')
        
        # Load dialogue on initialization
        self._load_dialogue_file()
        
        logger.info(f"Dialogue loader initialized with {len(self.dialogue_data)} dialogue sections")
    
    def _load_dialogue_file(self):
        """Load dialogue content from JSON file"""
        try:
            if not self.dialogue_path.exists():
                logger.error(f"Dialogue file not found: {self.dialogue_path}")
                return
            
            with open(self.dialogue_path, 'r', encoding='utf-8') as f:
                self.dialogue_data = json.load(f)
            
            logger.info(f"Loaded dialogue from {self.dialogue_path}")
            
        except Exception as e:
            logger.error(f"Error loading dialogue file: {e}")
            self.dialogue_data = {}
    
    def load_dialogue(self) -> Dict[str, Any]:
        """
        Get all dialogue data
        
        Returns:
            Complete dialogue dictionary
        """
        return self.dialogue_data
    
    def get_phase_dialogue(self, phase: str) -> Dict[str, Any]:
        """
        Get dialogue for a specific phase
        
        Args:
            phase: Phase name (e.g., 'first_contact')
            
        Returns:
            Phase dialogue dictionary
        """
        return self.dialogue_data.get('phases', {}).get(phase, {})
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get validation rules for user inputs
        
        Returns:
            Validation rules dictionary
        """
        return self.dialogue_data.get('callsign_validation', {})
    
    def format_message(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Format message template with variables
        
        Args:
            template: Message template with {VARIABLE} placeholders
            variables: Dictionary of variables to substitute
            
        Returns:
            Formatted message string
        """
        try:
            # Find all variables in template
            found_vars = self.variable_pattern.findall(template)
            
            # Replace each variable
            formatted_message = template
            for var_name in found_vars:
                var_value = variables.get(var_name.lower(), f"{{{var_name}}}")
                formatted_message = formatted_message.replace(f"{{{var_name}}}", str(var_value))
            
            return formatted_message
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return template
    
    def get_nexus_opening(self, phase: str, has_experience: bool = None) -> str:
        """
        Get Sergeant Nexus opening message for a phase
        
        Args:
            phase: Phase name
            has_experience: User's experience level (for first_contact)
            
        Returns:
            Nexus opening message
        """
        try:
            phase_data = self.get_phase_dialogue(phase)
            
            if phase == 'first_contact':
                if has_experience is not None:
                    response_key = 'yes' if has_experience else 'no'
                    return phase_data.get('responses', {}).get(response_key, '')
                else:
                    return phase_data.get('nexus_opening', '')
            
            return phase_data.get('nexus_opening', '') or phase_data.get('nexus_intro', '')
            
        except Exception as e:
            logger.error(f"Error getting nexus opening for phase {phase}: {e}")
            return ""
    
    def get_character_message(self, phase: str, character: str, message_key: str = None) -> str:
        """
        Get message from specific character
        
        Args:
            phase: Phase name
            character: Character name (nexus, drill, doc)
            message_key: Specific message key (optional)
            
        Returns:
            Character message
        """
        try:
            phase_data = self.get_phase_dialogue(phase)
            
            # Try different character key patterns
            character_keys = [
                f"{character}_{message_key}" if message_key else f"{character}_message",
                f"{character}_response",
                f"{character}_intro",
                character
            ]
            
            for key in character_keys:
                if key in phase_data:
                    message = phase_data[key]
                    if isinstance(message, list):
                        return '\n'.join(message)
                    return str(message)
            
            logger.warning(f"Character message not found: {character} in phase {phase}")
            return ""
            
        except Exception as e:
            logger.error(f"Error getting character message: {e}")
            return ""
    
    def get_phase_steps(self, phase: str) -> Dict[str, Any]:
        """
        Get steps for multi-step phases
        
        Args:
            phase: Phase name
            
        Returns:
            Steps dictionary
        """
        phase_data = self.get_phase_dialogue(phase)
        return phase_data.get('steps', {})
    
    def get_theater_options(self) -> Dict[str, Any]:
        """
        Get theater selection options
        
        Returns:
            Theater options dictionary
        """
        theater_phase = self.get_phase_dialogue('theater_selection')
        return theater_phase.get('options', {})
    
    def get_callsign_suggestions(self) -> List[str]:
        """
        Get callsign suggestions
        
        Returns:
            List of callsign suggestions
        """
        try:
            callsign_phase = self.get_phase_dialogue('callsign_creation')
            suggestions = callsign_phase.get('suggestions', {}).get('examples', [])
            
            # Extract callsign names from formatted examples
            callsign_names = []
            for example in suggestions:
                # Extract text between quotes
                import re
                match = re.search(r'"([^"]*)"', example)
                if match:
                    callsign_names.append(match.group(1))
            
            return callsign_names
            
        except Exception as e:
            logger.error(f"Error getting callsign suggestions: {e}")
            return ["TacticalRecrut", "MarketWarrior", "SignalHunter"]
    
    def get_error_message(self, error_type: str) -> str:
        """
        Get error message for validation failures
        
        Args:
            error_type: Type of error (too_short, too_long, etc.)
            
        Returns:
            Error message string
        """
        try:
            validation_rules = self.get_validation_rules()
            error_messages = validation_rules.get('error_messages', {})
            
            return error_messages.get(error_type, "Invalid input. Please try again.")
            
        except Exception as e:
            logger.error(f"Error getting error message: {e}")
            return "Invalid input. Please try again."
    
    def get_formatted_phase_content(self, phase: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get complete phase content with variable substitution
        
        Args:
            phase: Phase name
            variables: Variables for substitution
            
        Returns:
            Formatted phase content
        """
        try:
            phase_data = self.get_phase_dialogue(phase)
            
            if not phase_data:
                return {}
            
            # Recursively format all string values
            formatted_data = self._format_recursive(phase_data, variables)
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error formatting phase content: {e}")
            return {}
    
    def _format_recursive(self, data: Any, variables: Dict[str, Any]) -> Any:
        """
        Recursively format all string values in data structure
        
        Args:
            data: Data to format
            variables: Variables for substitution
            
        Returns:
            Formatted data
        """
        if isinstance(data, str):
            return self.format_message(data, variables)
        elif isinstance(data, dict):
            return {k: self._format_recursive(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._format_recursive(item, variables) for item in data]
        else:
            return data
    
    def get_phase_title(self, phase: str) -> str:
        """
        Get formatted title for a phase
        
        Args:
            phase: Phase name
            
        Returns:
            Phase title
        """
        phase_data = self.get_phase_dialogue(phase)
        title = phase_data.get('title', '')
        
        if not title:
            # Generate title from phase name
            title = phase.replace('_', ' ').title()
        
        return title
    
    def get_progress_message(self, completed_states: List[str], current_state: str) -> str:
        """
        Generate progress message
        
        Args:
            completed_states: List of completed states
            current_state: Current state name
            
        Returns:
            Progress message
        """
        try:
            total_states = 14
            completed_count = len(completed_states)
            percentage = (completed_count / total_states) * 100
            
            current_title = self.get_phase_title(current_state)
            
            return (
                f"🎯 **Training Progress**: {completed_count}/{total_states} phases completed ({percentage:.1f}%)\n"
                f"📍 **Current Phase**: {current_title}\n"
                f"⏱️ **Status**: In Progress"
            )
            
        except Exception as e:
            logger.error(f"Error generating progress message: {e}")
            return "🎯 **Training Progress**: In Progress"
    
    def validate_dialogue_integrity(self) -> Dict[str, Any]:
        """
        Validate dialogue file integrity
        
        Returns:
            Validation results
        """
        try:
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'stats': {}
            }
            
            # Check if dialogue data loaded
            if not self.dialogue_data:
                results['valid'] = False
                results['errors'].append("No dialogue data loaded")
                return results
            
            # Check required sections
            required_sections = ['phases', 'callsign_validation']
            for section in required_sections:
                if section not in self.dialogue_data:
                    results['valid'] = False
                    results['errors'].append(f"Missing required section: {section}")
            
            # Check phases
            phases = self.dialogue_data.get('phases', {})
            expected_phases = [
                'first_contact', 'market_warfare_intro', 'knowledge_source',
                'training_setup', 'first_mission', 'theater_selection',
                'oath_of_enlistment', 'secure_link', 'callsign_creation',
                'operational_interface', 'core_maneuvers', 'field_manual',
                'personal_record'
            ]
            
            for phase in expected_phases:
                if phase not in phases:
                    results['warnings'].append(f"Missing phase: {phase}")
            
            # Stats
            results['stats'] = {
                'total_phases': len(phases),
                'expected_phases': len(expected_phases),
                'validation_rules': len(self.dialogue_data.get('callsign_validation', {}))
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error validating dialogue integrity: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': [],
                'stats': {}
            }