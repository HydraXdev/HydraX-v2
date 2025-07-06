# fire_mode_validator.py
# BITTEN Fire Mode Validation Engine - THE BEATING HEART OF CONTROL

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .fire_modes import FireMode, TierLevel, TIER_CONFIGS, ChaingunState
from .risk_controller import get_risk_controller, TierLevel as RiskTierLevel
from .emergency_stop_controller import EmergencyStopController

@dataclass
class ValidationResult:
    """Result of fire validation with bot responses"""
    valid: bool
    reason: str
    bot_responses: Dict[str, str]
    mutations: Optional[Dict] = None
    delay: Optional[int] = None

class FireModeValidator:
    """
    THE GATEKEEPER - Nothing fires without passing through here.
    This is where rules become law, where discipline is enforced.
    """
    
    def __init__(self):
        # Initialize validation rules per tier
        self.validation_rules = {
            TierLevel.NIBBLER: self._validate_nibbler,
            TierLevel.FANG: self._validate_fang,
            TierLevel.COMMANDER: self._validate_commander,
            TierLevel.APEX: self._validate_apex
        }
        
        # Mode-specific validators
        self.mode_validators = {
            FireMode.SINGLE_SHOT: self._validate_single_shot,
            FireMode.CHAINGUN: self._validate_chaingun_mode,
            FireMode.AUTO_FIRE: self._validate_auto_fire,
            FireMode.STEALTH: self._validate_stealth_mode,
            FireMode.MIDNIGHT_HAMMER: self._validate_midnight_hammer
        }
        
        # Cooldown tracking
        self.cooldowns = {}
        self.penalties = {}
        
        # Emergency stop controller
        self.emergency_controller = EmergencyStopController()
        
    def validate_fire(self, trade_payload: Dict, user_profile: Dict) -> ValidationResult:
        """
        Master validation flow - THE GAUNTLET
        Every trade must pass these trials
        """
        
        # Extract key parameters
        user_tier = TierLevel(user_profile.get('tier', 'nibbler'))
        active_mode = FireMode(trade_payload.get('fire_mode', 'single_shot'))
        signal_tcs = trade_payload.get('tcs', 0)
        
        # 1. System-wide kill switch check
        kill_switch_check = self._check_kill_switch()
        if not kill_switch_check.valid:
            return kill_switch_check
        
        # 2. Check tier permissions
        tier_validation = self.validation_rules[user_tier](trade_payload, user_profile)
        if not tier_validation.valid:
            return tier_validation
        
        # 3. Validate mode-specific rules
        mode_validation = self.mode_validators[active_mode](trade_payload, user_profile)
        if not mode_validation.valid:
            return mode_validation
        
        # 4. Check cooldowns and penalties
        cooldown_check = self._check_cooldowns(user_profile)
        if not cooldown_check.valid:
            return cooldown_check
        
        # 5. Validate TCS threshold
        tcs_check = self._validate_tcs(signal_tcs, user_tier, active_mode)
        if not tcs_check.valid:
            return tcs_check
        
        # 6. Check risk limits
        risk_check = self._validate_risk_limits(trade_payload, user_profile)
        if not risk_check.valid:
            return risk_check
        
        # 7. Apply mode mutations if needed
        mutations = self._apply_mode_mutations(trade_payload, user_profile)
        
        # 8. Calculate execution delay if needed
        delay = self._calculate_delay(active_mode, user_profile)
        
        # All checks passed!
        return ValidationResult(
            valid=True,
            reason="FIRE AUTHORIZED",
            bot_responses={
                "drillbot": "TARGET VALIDATED. FIRE WHEN READY.",
                "medicbot": "All systems green. Good hunting.",
                "bit": "*focused hunting stance*"
            },
            mutations=mutations,
            delay=delay
        )
    
    # TIER VALIDATORS
    
    def _validate_nibbler(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Nibbler tier: Basic safety only"""
        
        # Check daily shot limit
        if profile.get('shots_today', 0) >= 6:
            return ValidationResult(
                valid=False,
                reason="DAILY LIMIT REACHED",
                bot_responses={
                    "drillbot": "AMMO DEPLETED. RESUPPLY AT 0000 UTC.",
                    "medicbot": "Rest is part of the process. See you tomorrow.",
                    "bit": "*yawns and curls up*"
                }
            )
        
        # Only arcade shots allowed
        if payload.get('signal_type') not in ['arcade', 'dawn_raid', 'wall_defender', 'rocket_ride', 'rubber_band']:
            return ValidationResult(
                valid=False,
                reason="SNIPER SHOTS LOCKED",
                bot_responses={
                    "drillbot": "YOU'RE NOT READY FOR THAT WEAPON.",
                    "recruiterbot": "Evolve to FANG to unlock sniper shots.",
                    "bit": "*blocks the sniper button with paw*"
                }
            )
        
        return ValidationResult(valid=True, reason="Nibbler validation passed", bot_responses={})
    
    def _validate_fang(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Fang tier: Sniper access + CHAINGUN"""
        
        # Check daily limit (10 shots)
        if profile.get('shots_today', 0) >= 10:
            return ValidationResult(
                valid=False,
                reason="FANG LIMIT REACHED",
                bot_responses={
                    "drillbot": "EVEN PREDATORS NEED REST.",
                    "bit": "*protective nuzzle*"
                }
            )
        
        # Check concurrent positions
        if profile.get('open_positions', 0) >= 2:
            return ValidationResult(
                valid=False,
                reason="POSITION SLOTS FULL",
                bot_responses={
                    "drillbot": "TWO TARGETS MAXIMUM. CLOSE ONE FIRST.",
                    "medicbot": "Managing multiple positions. Stay focused."
                }
            )
        
        return ValidationResult(valid=True, reason="Fang validation passed", bot_responses={})
    
    def _validate_commander(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Commander tier: AUTO-FIRE enabled"""
        
        # Check concurrent positions (3 max)
        if profile.get('open_positions', 0) >= 3:
            return ValidationResult(
                valid=False,
                reason="COMMANDER SLOTS FULL",
                bot_responses={
                    "drillbot": "THREE-FRONT LIMIT. TACTICAL NECESSITY.",
                    "medicbot": "Cognitive load at maximum. Close a position."
                }
            )
        
        # No daily limit for Commander+
        return ValidationResult(valid=True, reason="Commander validation passed", bot_responses={})
    
    def _validate_apex(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Apex tier: No limits, full access"""
        return ValidationResult(
            valid=True, 
            reason="APEX PREDATOR - NO RESTRICTIONS",
            bot_responses={
                "drillbot": "YOU ARE THE WEAPON.",
                "bit": "*proud purr*"
            }
        )
    
    # MODE VALIDATORS
    
    def _validate_single_shot(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Standard single shot validation"""
        # Base validation covered by tier validators
        return ValidationResult(valid=True, reason="Single shot validated", bot_responses={})
    
    def _validate_stealth_mode(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Stealth Mode: Apex only, full randomization"""
        
        if profile.get('tier') != 'apex':
            return ValidationResult(
                valid=False,
                reason="STEALTH MODE: APEX ONLY",
                bot_responses={
                    "stealthbot": "YOU'RE NOT READY TO DISAPPEAR.",
                    "drillbot": "EARN YOUR GHOST STATUS FIRST."
                }
            )
        
        # Stealth mode always valid for Apex
        return ValidationResult(
            valid=True,
            reason="GHOST PROTOCOL ACTIVE",
            bot_responses={
                "stealthbot": "RANDOMIZING PARAMETERS. BECOMING NOISE.",
                "bit": "*flickers in and out of visibility*"
            }
        )
    
    def _validate_chaingun_mode(self, payload: Dict, profile: Dict) -> ValidationResult:
        """CHAINGUN: Progressive risk sequence"""
        
        sequence = profile.get('active_chaingun_sequence')
        if not sequence:
            return ValidationResult(
                valid=False,
                reason="NO ACTIVE CHAINGUN SEQUENCE",
                bot_responses={
                    "drillbot": "INITIATE SEQUENCE FIRST."
                }
            )
        
        # Check shot number requirements
        shot_num = sequence.get('current_shot', 1)
        required_tcs = [85, 87, 89, 91][shot_num - 1] if shot_num <= 4 else 91
        
        if payload.get('tcs', 0) < required_tcs:
            return ValidationResult(
                valid=False,
                reason=f"SHOT {shot_num} REQUIRES {required_tcs}% TCS",
                bot_responses={
                    "drillbot": f"INSUFFICIENT CONFIDENCE FOR SHOT {shot_num}.",
                    "medicbot": "Wait for a better setup."
                }
            )
        
        return ValidationResult(valid=True, reason="Chaingun shot authorized", bot_responses={})
    
    def _validate_auto_fire(self, payload: Dict, profile: Dict) -> ValidationResult:
        """AUTO-FIRE: Commander+ only, autonomous trading"""
        
        user_tier = TierLevel(profile.get('tier', 'nibbler'))
        if user_tier not in [TierLevel.COMMANDER, TierLevel.APEX]:
            return ValidationResult(
                valid=False,
                reason="AUTO-FIRE: COMMANDER+ ONLY",
                bot_responses={
                    "drillbot": "MANUAL CONTROL ONLY. EARN AUTOMATION.",
                    "recruiterbot": "Reach Commander tier for AUTO-FIRE access."
                }
            )
        
        # AUTO-FIRE requires 91%+ TCS
        if payload.get('tcs', 0) < 91:
            return ValidationResult(
                valid=False,
                reason="AUTO-FIRE REQUIRES 91%+ TCS",
                bot_responses={
                    "drillbot": "CONFIDENCE TOO LOW FOR AUTONOMOUS FIRE.",
                    "medicbot": "Wait for higher certainty signals."
                }
            )
        
        return ValidationResult(valid=True, reason="Auto-fire authorized", bot_responses={})
    
    def _validate_midnight_hammer(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Special validation for network-wide events"""
        
        hammer_event = profile.get('active_hammer_event')
        if not hammer_event:
            return ValidationResult(
                valid=False,
                reason="NO ACTIVE HAMMER EVENT",
                bot_responses={
                    "drillbot": "FALSE ALARM. NO HAMMER CALLED."
                }
            )
        
        # Check if user opted in
        if profile.get('user_id') not in hammer_event.get('participants', []):
            return ValidationResult(
                valid=False,
                reason="NOT REGISTERED FOR HAMMER",
                bot_responses={
                    "recruiterbot": "Join the strike first. Time is running out.",
                    "bit": "*urgent chirping*"
                }
            )
        
        # Check TCS requirement (95%+)
        if payload.get('tcs', 0) < 95:
            return ValidationResult(
                valid=False,
                reason="HAMMER REQUIRES 95%+ TCS",
                bot_responses={
                    "drillbot": "NOT ENOUGH FORCE FOR THE HAMMER.",
                    "bit": "*disappointed meow*"
                }
            )
        
        return ValidationResult(
            valid=True,
            reason="HAMMER STRIKE AUTHORIZED",
            bot_responses={
                "drillbot": "FOR THE NETWORK. STRIKE AS ONE.",
                "medicbot": "Remember: 5% risk for the collective.",
                "bit": "*battle cry*",
                "recruiterbot": "12,847 nodes striking together. LEGENDARY."
            }
        )
    
    # MUTATION SYSTEM
    
    def _apply_mode_mutations(self, payload: Dict, profile: Dict) -> Optional[Dict]:
        """Apply mode-specific trade mutations"""
        
        mutations = {}
        mode = FireMode(payload.get('fire_mode', 'single_shot'))
        
        if mode == FireMode.STEALTH:
            # Randomize everything slightly
            mutations['entry_delay'] = secrets.randbelow(181) + 120  # 120-300 range  # 2-5 min
            mutations['size_variance'] = 0.8 + (secrets.randbelow(401) / 1000)  # 0.8-1.2 range
            mutations['tp_variance'] = 0.95 + (secrets.randbelow(101) / 1000)  # 0.95-1.05 range
            mutations['sl_variance'] = 0.95 + (secrets.randbelow(101) / 1000)  # 0.95-1.05 range
            
            # Sometimes inject intentional loss
            if profile.get('recent_win_rate', 0) > 0.85 and secrets.randbelow(100) < 7:
                mutations['force_loss'] = True
                mutations['loss_reason'] = "STEALTH_CAMOUFLAGE"
        
        elif mode == FireMode.CHAINGUN:
            shot_num = profile.get('active_chaingun_sequence', {}).get('current_shot', 1)
            mutations['risk_multiplier'] = [1, 2, 4, 4][shot_num - 1] if shot_num <= 4 else 4
        
        elif mode == FireMode.MIDNIGHT_HAMMER:
            # Unity bonus - all participants get boost
            participants = profile.get('active_hammer_event', {}).get('participants', [])
            if len(participants) > 100:
                mutations['unity_bonus'] = 1.2  # 20% size boost
                mutations['community_power'] = True
        
        return mutations if mutations else None
    
    # COOLDOWN AND PENALTY SYSTEM
    
    def _check_cooldowns(self, profile: Dict) -> ValidationResult:
        """Check various cooldowns and penalties"""
        
        # Revenge trade cooldown
        last_loss = profile.get('last_loss_time')
        if last_loss and isinstance(last_loss, datetime):
            time_since_loss = (datetime.now() - last_loss).seconds
            if time_since_loss < 300:  # 5 minutes
                return ValidationResult(
                    valid=False,
                    reason="REVENGE TRADE BLOCKED",
                    bot_responses={
                        "drillbot": "EMOTION DETECTED. STAND DOWN.",
                        "medicbot": "Breathe. Process the loss first.",
                        "bit": "*sits firmly on trade button*"
                    }
                )
        
        # XP penalty lockout
        if profile.get('xp_penalty_active'):
            return ValidationResult(
                valid=False,
                reason="XP PENALTY LOCKOUT",
                bot_responses={
                    "drillbot": "PRIVILEGES REVOKED. EARN THEM BACK.",
                    "recruiterbot": "Complete your redemption tasks first."
                }
            )
        
        # Single shot cooldown (30 minutes between shots)
        last_shot = profile.get('last_shot_time')
        if last_shot and isinstance(last_shot, datetime):
            time_since_shot = (datetime.now() - last_shot).seconds
            if time_since_shot < 1800:  # 30 minutes
                remaining = 1800 - time_since_shot
                return ValidationResult(
                    valid=False,
                    reason=f"COOLDOWN ACTIVE: {remaining//60} MIN",
                    bot_responses={
                        "drillbot": "PATIENCE. RELOAD IN PROGRESS.",
                        "bit": "*guarding the trigger*"
                    }
                )
        
        return ValidationResult(valid=True, reason="No active cooldowns", bot_responses={})
    
    # RISK VALIDATION
    
    def _validate_risk_limits(self, payload: Dict, profile: Dict) -> ValidationResult:
        """Validate risk management rules using new risk controller"""
        
        # Get risk controller
        risk_controller = get_risk_controller()
        
        # Get user's tier
        user_tier = TierLevel(profile.get('tier', 'nibbler'))
        risk_tier = RiskTierLevel[user_tier.value.upper()]
        
        # Get account balance (must be provided in profile)
        account_balance = profile.get('account_balance', 10000)
        if account_balance <= 0:
            return ValidationResult(
                valid=False,
                reason="INVALID ACCOUNT BALANCE",
                bot_responses={
                    "drillbot": "ACCOUNT DATA CORRUPTED. ABORT.",
                    "medicbot": "Cannot verify account status."
                }
            )
        
        # Get risk percentage from controller
        risk_percent, risk_reason = risk_controller.get_user_risk_percent(
            profile['user_id'], risk_tier
        )
        
        # Calculate potential loss
        potential_loss = account_balance * (risk_percent / 100)
        
        # Check if trade is allowed
        trade_allowed, block_reason = risk_controller.check_trade_allowed(
            profile['user_id'], risk_tier, potential_loss, account_balance
        )
        
        if not trade_allowed:
            # Map block reasons to bot responses
            if "drawdown" in block_reason.lower():
                return ValidationResult(
                    valid=False,
                    reason=block_reason.upper(),
                    bot_responses={
                        "drillbot": "DRAWDOWN LIMIT HIT. CEASE FIRE.",
                        "medicbot": f"Capital preservation protocol active. {block_reason}",
                        "bit": "*sits on trading terminal*"
                    }
                )
            elif "cooldown" in block_reason.lower():
                return ValidationResult(
                    valid=False,
                    reason="COOLDOWN ACTIVE",
                    bot_responses={
                        "drillbot": "TACTICAL OVERRIDE IN EFFECT. STAND DOWN.",
                        "medicbot": "Recovery period mandatory. Time heals all wounds.",
                        "bit": "*guarding the trigger protectively*"
                    }
                )
            elif "trade limit" in block_reason.lower():
                return ValidationResult(
                    valid=False,
                    reason=block_reason.upper(),
                    bot_responses={
                        "drillbot": "AMMO DEPLETED. RESUPPLY AT 0000 UTC.",
                        "medicbot": "Rest is part of the strategy. See you tomorrow.",
                        "bit": "*yawns and curls up*"
                    }
                )
            else:
                return ValidationResult(
                    valid=False,
                    reason=block_reason.upper(),
                    bot_responses={
                        "drillbot": "FIRE CONTROL SAYS NO.",
                        "medicbot": block_reason,
                        "bit": "*shakes head*"
                    }
                )
        
        # Update payload with controller's risk percentage
        payload['risk_percent'] = risk_percent
        payload['risk_reason'] = risk_reason
        
        # Account balance check
        if account_balance < 100:
            return ValidationResult(
                valid=False,
                reason="INSUFFICIENT CAPITAL",
                bot_responses={
                    "drillbot": "NO AMMUNITION LEFT. RELOAD ACCOUNT.",
                    "medicbot": "Protect what remains. Time to regroup."
                }
            )
        
        # Exposure check - now using controller's risk
        total_exposure = profile.get('total_exposure_percent', 0)
        new_risk = risk_percent
        
        if total_exposure + new_risk > 10:  # 10% max combined
            return ValidationResult(
                valid=False,
                reason="EXPOSURE LIMIT EXCEEDED",
                bot_responses={
                    "drillbot": "TOO MANY FRONTS. TACTICAL RETREAT.",
                    "medicbot": "Risk concentration too high. Diversify."
                }
            )
        
        return ValidationResult(valid=True, reason="Risk parameters acceptable", bot_responses={})
    
    # UTILITY METHODS
    
    def _check_kill_switch(self) -> ValidationResult:
        """Check if system-wide halt is active"""
        # Check emergency stop controller first
        if self.emergency_controller.is_active():
            status = self.emergency_controller.get_emergency_status()
            current_event = status.get('current_event', {})
            trigger = current_event.get('trigger', 'unknown')
            level = current_event.get('level', 'unknown')
            reason = current_event.get('reason', 'Emergency stop active')
            
            # Different responses based on trigger
            if trigger == 'panic':
                bot_responses = {
                    "drillbot": "🚨 PANIC PROTOCOL ACTIVE. ALL UNITS STAND DOWN.",
                    "medicbot": "Emergency medical protocol. All trading suspended.",
                    "bit": "*trembling in corner* No fire! No fire!"
                }
            elif trigger == 'admin_override':
                bot_responses = {
                    "drillbot": "🚨 COMMAND OVERRIDE. ALL UNITS CEASE FIRE.",
                    "medicbot": "System-wide halt by command authority.",
                    "bit": "*saluting* Yes sir! Standing down!"
                }
            elif trigger == 'drawdown':
                bot_responses = {
                    "drillbot": "🚨 CASUALTY PROTOCOL. RETREAT AND REGROUP.",
                    "medicbot": "Excessive losses detected. Recovery mode active.",
                    "bit": "*bandaging wounds* Owie... need time to heal"
                }
            elif trigger == 'news':
                bot_responses = {
                    "drillbot": "🚨 INTEL BLACKOUT. HOLD POSITION UNTIL CLEAR.",
                    "medicbot": "High-impact news event. Maintaining safe distance.",
                    "bit": "*peeking through blinds* Too scary outside!"
                }
            else:
                bot_responses = {
                    "drillbot": "🚨 EMERGENCY PROTOCOL ACTIVE. ALL UNITS STAND DOWN.",
                    "medicbot": "Emergency halt in effect. Stand by for assessment.",
                    "bit": "*hiding under desk* Emergency! Emergency!"
                }
            
            return ValidationResult(
                valid=False,
                reason=f"EMERGENCY STOP ACTIVE: {trigger.upper()} - {reason}",
                bot_responses=bot_responses
            )
        
        # Fallback to environment variable check
        import os
        if os.getenv('BITTEN_KILL_SWITCH', 'false').lower() == 'true':
            return ValidationResult(
                valid=False,
                reason="SYSTEM HALT - GLOBAL EMERGENCY",
                bot_responses={
                    "drillbot": "ALL UNITS CEASE FIRE. EMERGENCY PROTOCOL.",
                    "medicbot": "System-wide halt. Stand by for assessment.",
                    "bit": "*hiding under furniture*"
                }
            )
        
        return ValidationResult(valid=True, reason="System operational", bot_responses={})
    
    def _validate_tcs(self, tcs: float, tier: TierLevel, mode: FireMode) -> ValidationResult:
        """Validate TCS meets requirements"""
        
        # Get tier configuration
        tier_config = TIER_CONFIGS.get(tier)
        if not tier_config:
            return ValidationResult(
                valid=False,
                reason="INVALID TIER",
                bot_responses={"drillbot": "SYSTEM ERROR. REPORT THIS."}
            )
        
        min_tcs = tier_config.min_tcs
        
        # Mode-specific TCS overrides
        mode_requirements = {
            FireMode.CHAINGUN: 85,  # Base chaingun requirement
            FireMode.AUTO_FIRE: 91,
            FireMode.MIDNIGHT_HAMMER: 95
        }
        
        required_tcs = mode_requirements.get(mode, min_tcs)
        
        if tcs < required_tcs:
            return ValidationResult(
                valid=False,
                reason=f"TCS {tcs}% < {required_tcs}% REQUIRED",
                bot_responses={
                    "drillbot": f"INSUFFICIENT CONFIDENCE. NEED {required_tcs}%+",
                    "bit": "*disapproving look*"
                }
            )
        
        return ValidationResult(valid=True, reason="TCS acceptable", bot_responses={})
    
    def _calculate_delay(self, mode: FireMode, profile: Dict) -> Optional[int]:
        """Calculate execution delay if needed"""
        
        if mode == FireMode.STEALTH:
            return random.randint(120, 300)  # 2-5 minutes
        elif profile.get('network_latency_simulation'):
            return random.randint(1, 5)  # Realistic latency
        
        return None

# INTEGRATION HELPERS

def validate_fire_request(trade_payload: Dict, user_id: str, user_profile: Dict) -> Dict:
    """
    Main entry point from fire_router.py
    Returns formatted validation result
    """
    validator = FireModeValidator()
    
    # Run validation
    result = validator.validate_fire(trade_payload, user_profile)
    
    # Return formatted response
    return {
        "valid": result.valid,
        "reason": result.reason,
        "bot_responses": result.bot_responses,
        "mutations": result.mutations,
        "delay": result.delay
    }

def apply_trade_mutations(original_request: Dict, mutations: Dict) -> Dict:
    """Apply validated mutations to trade request"""
    if not mutations:
        return original_request
    
    modified = original_request.copy()
    
    # Apply size variance
    if 'size_variance' in mutations:
        modified['volume'] *= mutations['size_variance']
    
    # Apply risk multiplier (for chaingun)
    if 'risk_multiplier' in mutations:
        modified['volume'] *= mutations['risk_multiplier']
    
    # Apply TP/SL variance (for stealth)
    if 'tp_variance' in mutations:
        modified['take_profit'] *= mutations['tp_variance']
    if 'sl_variance' in mutations:
        modified['stop_loss'] *= mutations['sl_variance']
    
    # Apply unity bonus (for midnight hammer)
    if 'unity_bonus' in mutations:
        modified['volume'] *= mutations['unity_bonus']
    
    return modified