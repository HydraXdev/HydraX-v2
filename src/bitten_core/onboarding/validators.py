"""
BITTEN Onboarding Input Validators

Validates user inputs during onboarding flow including callsign validation,
email validation, and other form inputs with military-themed error messages.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
# from email_validator import validate_email, EmailNotValidError
# Using simple regex for now
import re

logger = logging.getLogger(__name__)

class OnboardingValidators:
    """Validates user inputs during onboarding"""
    
    def __init__(self):
        # Callsign validation rules
        self.callsign_min_length = 3
        self.callsign_max_length = 20
        self.callsign_pattern = re.compile(r'^[a-zA-Z0-9_]+$')
        
        # Reserved callsigns
        self.reserved_callsigns = {
            'admin', 'bitten', 'system', 'nexus', 'drill', 'doc', 'bit',
            'commander', 'sergeant', 'captain', 'major', 'general',
            'support', 'help', 'bot', 'test', 'debug', 'null', 'undefined'
        }
        
        # Phone validation
        self.phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
        
        # Name validation
        self.name_pattern = re.compile(r'^[a-zA-Z\s\-\']{2,50}$')
        
        logger.info("Onboarding validators initialized")
    
    async def validate_callsign(self, callsign: str) -> Tuple[bool, str]:
        """
        Validate callsign according to BITTEN rules
        
        Args:
            callsign: Proposed callsign
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not callsign:
                return False, "🚨 **Invalid Input**: Callsign cannot be empty, recruit."
            
            # Strip whitespace
            callsign = callsign.strip()
            
            # Check length
            if len(callsign) < self.callsign_min_length:
                return False, f"🚨 **Too Short**: Callsign must be at least {self.callsign_min_length} characters, recruit."
            
            if len(callsign) > self.callsign_max_length:
                return False, f"🚨 **Too Long**: Keep it under {self.callsign_max_length} characters. Brevity is tactical."
            
            # Check pattern
            if not self.callsign_pattern.match(callsign):
                return False, "🚨 **Invalid Characters**: Alphanumeric and underscores only. No special ops characters."
            
            # Check reserved words
            if callsign.lower() in self.reserved_callsigns:
                return False, "🚨 **Classified**: That callsign is reserved. Choose another, operative."
            
            # Check uniqueness (placeholder - would check database)
            if await self._is_callsign_taken(callsign):
                return False, "🚨 **Already Taken**: Another operative claimed that callsign. Be original."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating callsign: {e}")
            return False, "🚨 **System Error**: Unable to validate callsign. Try again."
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """
        Validate email address
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not email:
                return False, "📧 **Required**: Email address is required for secure communications."
            
            # Strip whitespace
            email = email.strip()
            
            # Use simple regex validation for now
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2}$')
            if email_pattern.match(email):
                return True, ""
            else:
                return False, "📧 **Invalid Email**: Please enter a valid email address (e.g., soldier@bitten.com)"
            
        except Exception as e:
            logger.error(f"Error validating email: {e}")
            return False, "📧 **System Error**: Unable to validate email. Try again."
    
    def validate_phone(self, phone: str) -> Tuple[bool, str]:
        """
        Validate phone number
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not phone:
                return False, "📱 **Required**: Phone number is required for emergency communications."
            
            # Strip whitespace and common separators
            phone = re.sub(r'[\s\-\(\)\.]+', '', phone.strip())
            
            # Check pattern
            if not self.phone_pattern.match(phone):
                return False, "📱 **Invalid Format**: Use international format (+1234567890) or local format."
            
            # Check length
            if len(phone) < 7 or len(phone) > 16:
                return False, "📱 **Invalid Length**: Phone number must be 7-16 digits."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating phone: {e}")
            return False, "📱 **System Error**: Unable to validate phone. Try again."
    
    def validate_name(self, name: str) -> Tuple[bool, str]:
        """
        Validate first name
        
        Args:
            name: Name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not name:
                return False, "👤 **Required**: First name is required for identification."
            
            # Strip whitespace
            name = name.strip()
            
            # Check pattern
            if not self.name_pattern.match(name):
                return False, "👤 **Invalid Format**: Use only letters, spaces, hyphens, and apostrophes."
            
            # Check length
            if len(name) < 2:
                return False, "👤 **Too Short**: Name must be at least 2 characters."
            
            if len(name) > 50:
                return False, "👤 **Too Long**: Name must be under 50 characters."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating name: {e}")
            return False, "👤 **System Error**: Unable to validate name. Try again."
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password for training account
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not password:
                return False, "🔒 **Required**: Password is required for secure access."
            
            # Check length
            if len(password) < 8:
                return False, "🔒 **Too Short**: Password must be at least 8 characters for security."
            
            if len(password) > 128:
                return False, "🔒 **Too Long**: Password must be under 128 characters."
            
            # Check complexity
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            
            if not (has_upper or has_lower or has_digit):
                return False, "🔒 **Too Simple**: Include letters and numbers for tactical security."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating password: {e}")
            return False, "🔒 **System Error**: Unable to validate password. Try again."
    
    def validate_theater_selection(self, theater: str) -> Tuple[bool, str]:
        """
        Validate theater selection
        
        Args:
            theater: Selected theater
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            valid_theaters = {
                'demo': 'US Regulated Demo Account',
                'regulated': 'US Regulated Live Account',
                'offshore': 'Offshore Unregulated Account'
            }
            
            if theater not in valid_theaters:
                return False, "🎯 **Invalid Selection**: Choose a valid theater of operations."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating theater: {e}")
            return False, "🎯 **System Error**: Unable to validate theater. Try again."
    
    def validate_broker_credentials(self, account_id: str, trading_password: str) -> Tuple[bool, str]:
        """
        Validate broker credentials
        
        Args:
            account_id: Broker account ID
            trading_password: Trading password
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not account_id:
                return False, "🔐 **Required**: Trading account ID is required for secure link."
            
            if not trading_password:
                return False, "🔐 **Required**: Trading password is required for secure link."
            
            # Strip whitespace
            account_id = account_id.strip()
            trading_password = trading_password.strip()
            
            # Check account ID format (basic validation)
            if not re.match(r'^[a-zA-Z0-9]+$', account_id):
                return False, "🔐 **Invalid Format**: Account ID should contain only letters and numbers."
            
            if len(account_id) < 3 or len(account_id) > 20:
                return False, "🔐 **Invalid Length**: Account ID must be 3-20 characters."
            
            # Check password (basic validation)
            if len(trading_password) < 4:
                return False, "🔐 **Too Short**: Trading password must be at least 4 characters."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating broker credentials: {e}")
            return False, "🔐 **System Error**: Unable to validate credentials. Try again."
    
    def validate_terms_acceptance(self, accepted: bool) -> Tuple[bool, str]:
        """
        Validate terms acceptance
        
        Args:
            accepted: Whether terms were accepted
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not accepted:
                return False, "⚔️ **Required**: You must accept the BITTEN Protocols to continue."
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating terms acceptance: {e}")
            return False, "⚔️ **System Error**: Unable to validate terms. Try again."
    
    def validate_user_input(self, input_type: str, value: Any) -> Tuple[bool, str]:
        """
        Validate user input based on type
        
        Args:
            input_type: Type of input to validate
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if input_type == 'callsign':
                return self.validate_callsign(value)
            elif input_type == 'email':
                return self.validate_email(value)
            elif input_type == 'phone':
                return self.validate_phone(value)
            elif input_type == 'name':
                return self.validate_name(value)
            elif input_type == 'password':
                return self.validate_password(value)
            elif input_type == 'theater':
                return self.validate_theater_selection(value)
            elif input_type == 'terms':
                return self.validate_terms_acceptance(value)
            else:
                return False, f"🚨 **Unknown Input Type**: {input_type}"
                
        except Exception as e:
            logger.error(f"Error validating user input: {e}")
            return False, "🚨 **System Error**: Unable to validate input. Try again."
    
    def get_callsign_suggestions(self, user_name: str = None) -> List[str]:
        """
        Generate callsign suggestions
        
        Args:
            user_name: User's name for personalized suggestions
            
        Returns:
            List of callsign suggestions
        """
        try:
            base_suggestions = [
                "GhostPip", "MarketMaverick", "TrendWrangler", "PixelProfiteer",
                "BitWhisperer", "ApexAlgo", "TacticalTrader", "SignalHunter",
                "PipCommander", "ChartWarrior", "MarketSniper", "TradingNinja",
                "VolatilityViper", "BullishBear", "CandleStick", "FibonacciPhantom"
            ]
            
            suggestions = base_suggestions.copy()
            
            # Add personalized suggestions if name provided
            if user_name:
                name_clean = re.sub(r'[^a-zA-Z]', '', user_name)
                if len(name_clean) >= 3:
                    suggestions.extend([
                        f"{name_clean}Trader",
                        f"{name_clean}Pip",
                        f"{name_clean}Signal",
                        f"Tactical{name_clean}"
                    ])
            
            return suggestions[:8]  # Return max 8 suggestions
            
        except Exception as e:
            logger.error(f"Error generating callsign suggestions: {e}")
            return ["TacticalRecruit", "MarketWarrior", "SignalHunter"]
    
    async def _is_callsign_taken(self, callsign: str) -> bool:
        """
        Check if callsign is already taken
        
        Args:
            callsign: Callsign to check
            
        Returns:
            True if taken, False if available
        """
        try:
            # Placeholder implementation
            # In real implementation, this would check database
            
            # For now, simulate some taken callsigns
            taken_callsigns = {
                'admin', 'test', 'demo', 'sample', 'example'
            }
            
            return callsign.lower() in taken_callsigns
            
        except Exception as e:
            logger.error(f"Error checking callsign availability: {e}")
            return False  # Assume available if check fails
    
    def sanitize_input(self, value: str, max_length: int = 1000) -> str:
        """
        Sanitize user input for security
        
        Args:
            value: Input value to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized input
        """
        try:
            if not value:
                return ""
            
            # Strip whitespace
            sanitized = value.strip()
            
            # Limit length
            if len(sanitized) > max_length:
                sanitized = sanitized[:max_length]
            
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>\"\'&]', '', sanitized)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing input: {e}")
            return str(value)[:max_length] if value else ""