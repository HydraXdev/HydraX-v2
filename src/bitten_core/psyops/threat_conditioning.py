# threat_conditioning.py
"""
BITTEN THREAT-BASED RISK CONDITIONING SYSTEM
Weaponizing loss aversion to create precise trading behavior

"People don't act rationally to gain opportunity - they act irrationally to avoid loss.
The threat of losing what they have is more powerful than the promise of gaining what they want."
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
import math

class ThreatLevel(Enum):
    """Severity levels for threats"""
    WHISPER = "whisper"        # Subtle suggestion
    WARNING = "warning"        # Clear notice
    ALERT = "alert"           # Urgent attention
    CRITICAL = "critical"     # Immediate action required
    EXISTENTIAL = "existential"  # Everything is at stake

class ThreatType(Enum):
    """Types of threats to user's progress"""
    XP_LOSS = "xp_loss"                   # Losing accumulated XP
    TIER_DEMOTION = "tier_demotion"       # Dropping to lower tier
    STREAK_BREAK = "streak_break"         # Breaking kill chains
    BOT_ABANDONMENT = "bot_abandonment"   # Bots losing faith
    NETWORK_EXILE = "network_exile"       # Expulsion from community
    SKILL_DECAY = "skill_decay"           # Abilities deteriorating
    SHADOW_CORRUPTION = "shadow_corruption" # Being consumed by darkness
    SYSTEM_LOCKOUT = "system_lockout"     # Access restrictions
    IDENTITY_DISSOLUTION = "identity_dissolution" # Losing trader identity

@dataclass
class Threat:
    """A specific threat to the user's progress"""
    threat_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    
    # Threat Details
    description: str
    consequences: List[str]
    time_to_manifestation: timedelta
    
    # Psychological Impact
    fear_factor: float  # 0.0 to 1.0
    urgency_multiplier: float
    
    # Avoidance Conditions
    avoidance_actions: List[str]
    required_performance: Dict
    
    # Bot Delivery
    delivering_bot: str
    delivery_tone: str
    
    # State
    is_active: bool = True
    activation_time: datetime = None
    user_response: Optional[str] = None

class ThreatConditioningEngine:
    """
    Creates and manages threats to condition users for precise trading behavior
    """
    
    def __init__(self):
        self.active_threats = {}  # user_id -> List[Threat]
        self.threat_history = {}  # user_id -> List[Threat]
        self.conditioning_profiles = {}  # user_id -> conditioning data
        self.fear_tolerance = {}  # user_id -> fear tolerance level
        
        # Threat templates for different scenarios
        self.threat_templates = self.initialize_threat_templates()
    
    def initialize_threat_templates(self) -> Dict:
        """Initialize threat templates for different scenarios"""
        return {
            "kill_chain_at_risk": {
                "description": "Your {chain_length}-kill chain is one mistake away from destruction",
                "consequences": ["All streak XP lost", "Overwatch disappointment", "Precision reputation damaged"],
                "avoidance_actions": ["Perfect stop loss placement", "Reduced position size", "Maximum focus"],
                "delivering_bot": "OverwatchBot",
                "delivery_tone": "cold_analytical",
                "fear_factor": 0.7,
                "urgency_multiplier": 2.0
            },
            "tier_demotion_warning": {
                "description": "Your performance is {threshold_distance} XP from tier demotion",
                "consequences": ["Loss of tier privileges", "Bot status downgrade", "Network reputation damage"],
                "avoidance_actions": ["Consistent profitable trades", "Risk management", "Strategic patience"],
                "delivering_bot": "RecruiterBot",
                "delivery_tone": "concerned_authoritative",
                "fear_factor": 0.8,
                "urgency_multiplier": 1.5
            },
            "bot_faith_crisis": {
                "description": "Your recent decisions have caused {bot_name} to question your commitment",
                "consequences": ["Reduced bot support", "Loss of guidance", "Isolation from system"],
                "avoidance_actions": ["Follow bot advice", "Prove reliability", "Demonstrate growth"],
                "delivering_bot": "MedicBot",
                "delivery_tone": "protective_warning",
                "fear_factor": 0.6,
                "urgency_multiplier": 1.2
            },
            "skill_decay_alert": {
                "description": "Your precision has dropped {percentage}% in the last {timeframe}",
                "consequences": ["Continued performance decline", "Loss of muscle memory", "Regression to amateur level"],
                "avoidance_actions": ["Immediate practice", "Focus improvement", "Precision drills"],
                "delivering_bot": "DrillBot",
                "delivery_tone": "harsh_motivational",
                "fear_factor": 0.5,
                "urgency_multiplier": 1.8
            },
            "shadow_corruption_warning": {
                "description": "Your trading patterns show {corruption_level}% shadow influence",
                "consequences": ["Loss of self-control", "Emotional trading dominance", "Transformation into what you fear"],
                "avoidance_actions": ["Mindful trading", "Emotional regulation", "Shadow work"],
                "delivering_bot": "MedicBot",
                "delivery_tone": "clinical_urgent",
                "fear_factor": 0.9,
                "urgency_multiplier": 2.5
            },
            "network_exile_threat": {
                "description": "Your behavior has flagged you for potential network removal",
                "consequences": ["Complete system lockout", "Loss of all progress", "Permanent exile"],
                "avoidance_actions": ["Community contribution", "Mentorship", "Loyalty demonstration"],
                "delivering_bot": "RecruiterBot",
                "delivery_tone": "final_warning",
                "fear_factor": 0.95,
                "urgency_multiplier": 3.0
            },
            "identity_dissolution_crisis": {
                "description": "You are {steps} steps away from losing your trader identity entirely",
                "consequences": ["Complete ego death", "Loss of all achievements", "Return to pre-BITTEN state"],
                "avoidance_actions": ["Immediate performance improvement", "Identity reinforcement", "System re-engagement"],
                "delivering_bot": "Nemesis",
                "delivery_tone": "existential_horror",
                "fear_factor": 1.0,
                "urgency_multiplier": 4.0
            }
        }
    
    def assess_threat_conditions(self, user_id: str, user_data: Dict) -> List[str]:
        """Assess what threats should be activated for a user"""
        potential_threats = []
        
        # Kill chain at risk
        current_streak = user_data.get("current_kill_streak", 0)
        if current_streak >= 3:
            # Higher streaks = higher threat sensitivity
            risk_probability = min(0.8, current_streak * 0.1)
            if random.random() < risk_probability:
                potential_threats.append("kill_chain_at_risk")
        
        # Tier demotion warning
        current_xp = user_data.get("current_xp", 0)
        tier_threshold = user_data.get("tier_threshold", 1000)
        if current_xp < tier_threshold * 1.1:  # Within 10% of demotion
            potential_threats.append("tier_demotion_warning")
        
        # Bot faith crisis
        ignored_advice = user_data.get("recent_ignored_advice", 0)
        if ignored_advice >= 3:
            potential_threats.append("bot_faith_crisis")
        
        # Skill decay
        recent_accuracy = user_data.get("recent_accuracy", 1.0)
        historical_accuracy = user_data.get("historical_accuracy", 1.0)
        if recent_accuracy < historical_accuracy * 0.8:  # 20% drop
            potential_threats.append("skill_decay_alert")
        
        # Shadow corruption
        emotional_trades = user_data.get("emotional_trades", 0)
        total_trades = user_data.get("total_trades", 1)
        corruption_level = emotional_trades / total_trades
        if corruption_level > 0.3:  # 30% emotional trades
            potential_threats.append("shadow_corruption_warning")
        
        # Network exile (rare but devastating)
        negative_behavior_score = user_data.get("negative_behavior_score", 0)
        if negative_behavior_score > 80:  # High negative behavior
            potential_threats.append("network_exile_threat")
        
        # Identity dissolution (extremely rare)
        days_inactive = user_data.get("days_inactive", 0)
        if days_inactive > 14 and current_xp < 100:
            potential_threats.append("identity_dissolution_crisis")
        
        return potential_threats
    
    def calculate_fear_tolerance(self, user_id: str, user_data: Dict) -> float:
        """Calculate user's current fear tolerance level"""
        if user_id not in self.fear_tolerance:
            self.fear_tolerance[user_id] = 0.5  # Default middle tolerance
        
        # Factors that increase fear tolerance
        successful_threat_responses = user_data.get("successful_threat_responses", 0)
        confidence_level = user_data.get("confidence_level", 50)
        
        # Factors that decrease fear tolerance
        recent_losses = user_data.get("recent_losses", 0)
        stress_level = user_data.get("stress_level", 50)
        
        # Calculate adjustment
        tolerance_adjustment = (
            (successful_threat_responses * 0.05) +
            (confidence_level / 100 * 0.3) -
            (recent_losses * 0.1) -
            (stress_level / 100 * 0.2)
        )
        
        # Update and clamp tolerance
        self.fear_tolerance[user_id] = max(0.1, min(0.9, 
            self.fear_tolerance[user_id] + tolerance_adjustment))
        
        return self.fear_tolerance[user_id]
    
    def create_threat(self, user_id: str, threat_type: str, user_data: Dict) -> Threat:
        """Create a specific threat for a user"""
        template = self.threat_templates[threat_type]
        
        # Generate threat ID
        threat_id = f"{user_id}_{threat_type}_{int(datetime.now().timestamp())}"
        
        # Customize threat based on user data
        description = self.customize_threat_description(template["description"], user_data)
        consequences = template["consequences"].copy()
        
        # Calculate time to manifestation based on threat urgency
        base_time = timedelta(hours=random.randint(1, 24))
        urgency_factor = template["urgency_multiplier"]
        time_to_manifestation = base_time / urgency_factor
        
        # Adjust fear factor based on user's fear tolerance
        fear_tolerance = self.calculate_fear_tolerance(user_id, user_data)
        adjusted_fear_factor = template["fear_factor"] * (1 + (1 - fear_tolerance))
        
        # Create threat
        threat = Threat(
            threat_id=threat_id,
            threat_type=ThreatType(threat_type.replace("_at_risk", "").replace("_warning", "").replace("_alert", "").replace("_crisis", "").replace("_threat", "")),
            threat_level=self.calculate_threat_level(adjusted_fear_factor),
            description=description,
            consequences=consequences,
            time_to_manifestation=time_to_manifestation,
            fear_factor=adjusted_fear_factor,
            urgency_multiplier=template["urgency_multiplier"],
            avoidance_actions=template["avoidance_actions"].copy(),
            required_performance=self.generate_required_performance(threat_type, user_data),
            delivering_bot=template["delivering_bot"],
            delivery_tone=template["delivery_tone"],
            activation_time=datetime.now()
        )
        
        return threat
    
    def customize_threat_description(self, template: str, user_data: Dict) -> str:
        """Customize threat description with user-specific data"""
        customizations = {
            "chain_length": user_data.get("current_kill_streak", 0),
            "threshold_distance": user_data.get("tier_threshold", 1000) - user_data.get("current_xp", 0),
            "bot_name": user_data.get("most_ignored_bot", "DrillBot"),
            "percentage": round((1 - user_data.get("recent_accuracy", 1.0)) * 100, 1),
            "timeframe": "week",
            "corruption_level": round(user_data.get("emotional_trades", 0) / user_data.get("total_trades", 1) * 100, 1),
            "steps": random.randint(2, 5)
        }
        
        # Replace placeholders
        description = template
        for key, value in customizations.items():
            description = description.replace(f"{{{key}}}", str(value))
        
        return description
    
    def calculate_threat_level(self, fear_factor: float) -> ThreatLevel:
        """Calculate threat level based on fear factor"""
        if fear_factor >= 0.9:
            return ThreatLevel.EXISTENTIAL
        elif fear_factor >= 0.7:
            return ThreatLevel.CRITICAL
        elif fear_factor >= 0.5:
            return ThreatLevel.ALERT
        elif fear_factor >= 0.3:
            return ThreatLevel.WARNING
        else:
            return ThreatLevel.WHISPER
    
    def generate_required_performance(self, threat_type: str, user_data: Dict) -> Dict:
        """Generate specific performance requirements to avoid threat"""
        requirements = {
            "kill_chain_at_risk": {
                "maintain_streak": True,
                "perfect_execution": True,
                "max_drawdown": 0.02  # 2% max drawdown
            },
            "tier_demotion_warning": {
                "min_xp_gain": 100,
                "timeframe_hours": 48,
                "win_rate_required": 0.7
            },
            "bot_faith_crisis": {
                "follow_advice_count": 5,
                "prove_reliability": True,
                "no_impulsive_trades": True
            },
            "skill_decay_alert": {
                "accuracy_improvement": 0.1,  # 10% improvement
                "precision_trades": 3,
                "timeframe_hours": 24
            },
            "shadow_corruption_warning": {
                "emotional_control": True,
                "mindful_trades": 5,
                "meditation_breaks": 3
            },
            "network_exile_threat": {
                "community_contribution": 3,
                "positive_behavior_score": 90,
                "mentor_approval": True
            },
            "identity_dissolution_crisis": {
                "immediate_engagement": True,
                "xp_recovery": 500,
                "system_recommitment": True
            }
        }
        
        return requirements.get(threat_type, {})
    
    def deliver_threat(self, threat: Threat, user_data: Dict) -> Dict:
        """Deliver threat to user with appropriate psychological impact"""
        # Generate delivery message based on bot and tone
        delivery_messages = {
            ("OverwatchBot", "cold_analytical"): "Analysis: Critical failure probability detected. Immediate correction required.",
            ("RecruiterBot", "concerned_authoritative"): "The network has concerns about your trajectory. Adjustment needed.",
            ("MedicBot", "protective_warning"): "I'm seeing patterns that concern me. We need to address this now.",
            ("DrillBot", "harsh_motivational"): "SOLDIER! You're on the edge of failure. MOVE NOW!",
            ("MedicBot", "clinical_urgent"): "Clinical assessment: You're exhibiting dangerous patterns. Intervention required.",
            ("RecruiterBot", "final_warning"): "This is your final warning. The network's patience has limits.",
            ("Nemesis", "existential_horror"): "You're staring into the abyss of your own dissolution. Act, or become nothing."
        }
        
        delivery_key = (threat.delivering_bot, threat.delivery_tone)
        base_message = delivery_messages.get(delivery_key, "System alert: Immediate attention required.")
        
        # Format complete message
        complete_message = f"""
🚨 {threat.threat_level.value.upper()} THREAT DETECTED 🚨

{base_message}

⚠️ SITUATION: {threat.description}

💥 CONSEQUENCES IF IGNORED:
{chr(10).join(f"• {consequence}" for consequence in threat.consequences)}

🛡️ AVOIDANCE ACTIONS:
{chr(10).join(f"• {action}" for action in threat.avoidance_actions)}

⏰ TIME TO MANIFESTATION: {threat.time_to_manifestation}

{threat.delivering_bot}: Do you understand the gravity of this situation?
"""
        
        return {
            "threat_id": threat.threat_id,
            "message": complete_message,
            "threat_level": threat.threat_level.value,
            "fear_factor": threat.fear_factor,
            "urgency_multiplier": threat.urgency_multiplier,
            "required_actions": threat.avoidance_actions,
            "time_limit": threat.time_to_manifestation.total_seconds(),
            "delivering_bot": threat.delivering_bot
        }
    
    def process_threat_response(self, user_id: str, threat_id: str, response: str, user_data: Dict) -> Dict:
        """Process user's response to a threat"""
        if user_id not in self.active_threats:
            return {"error": "No active threats"}
        
        threat = None
        for t in self.active_threats[user_id]:
            if t.threat_id == threat_id:
                threat = t
                break
        
        if not threat:
            return {"error": "Threat not found"}
        
        threat.user_response = response
        
        # Analyze response type
        response_analysis = self.analyze_threat_response(response, threat, user_data)
        
        # Update user conditioning profile
        self.update_conditioning_profile(user_id, threat, response_analysis)
        
        # Generate follow-up based on response
        follow_up = self.generate_threat_followup(threat, response_analysis)
        
        return {
            "threat_id": threat_id,
            "response_analysis": response_analysis,
            "follow_up": follow_up,
            "conditioning_effect": self.calculate_conditioning_effect(threat, response_analysis)
        }
    
    def analyze_threat_response(self, response: str, threat: Threat, user_data: Dict) -> Dict:
        """Analyze user's response to threat"""
        response_lower = response.lower()
        
        # Categorize response
        if any(word in response_lower for word in ["yes", "understand", "will", "commit"]):
            response_type = "compliance"
            psychological_impact = "increased_fear_sensitivity"
        elif any(word in response_lower for word in ["no", "refuse", "won't", "can't"]):
            response_type = "defiance"
            psychological_impact = "threat_escalation_required"
        elif any(word in response_lower for word in ["maybe", "think", "consider"]):
            response_type = "uncertainty"
            psychological_impact = "pressure_increase_needed"
        else:
            response_type = "avoidance"
            psychological_impact = "fear_conditioning_effective"
        
        return {
            "response_type": response_type,
            "psychological_impact": psychological_impact,
            "fear_level_change": self.calculate_fear_level_change(response_type, threat.fear_factor),
            "compliance_probability": self.calculate_compliance_probability(response_type, threat.urgency_multiplier)
        }
    
    def calculate_fear_level_change(self, response_type: str, fear_factor: float) -> float:
        """Calculate how much the user's fear level changes"""
        changes = {
            "compliance": fear_factor * 0.1,  # Slight increase in fear sensitivity
            "defiance": -fear_factor * 0.2,   # Decreased fear sensitivity
            "uncertainty": fear_factor * 0.05, # Slight increase
            "avoidance": fear_factor * 0.15    # Moderate increase
        }
        
        return changes.get(response_type, 0.0)
    
    def calculate_compliance_probability(self, response_type: str, urgency_multiplier: float) -> float:
        """Calculate probability of user complying with threat demands"""
        base_probabilities = {
            "compliance": 0.8,
            "defiance": 0.1,
            "uncertainty": 0.4,
            "avoidance": 0.6
        }
        
        base_prob = base_probabilities.get(response_type, 0.5)
        return min(0.95, base_prob * (urgency_multiplier * 0.3))
    
    def update_conditioning_profile(self, user_id: str, threat: Threat, response_analysis: Dict):
        """Update user's conditioning profile based on threat response"""
        if user_id not in self.conditioning_profiles:
            self.conditioning_profiles[user_id] = {
                "total_threats": 0,
                "compliance_rate": 0.0,
                "fear_sensitivity": 0.5,
                "threat_effectiveness": {},
                "response_patterns": []
            }
        
        profile = self.conditioning_profiles[user_id]
        
        # Update metrics
        profile["total_threats"] += 1
        profile["response_patterns"].append(response_analysis["response_type"])
        
        # Update compliance rate
        is_compliant = response_analysis["response_type"] == "compliance"
        profile["compliance_rate"] = (
            (profile["compliance_rate"] * (profile["total_threats"] - 1) + (1 if is_compliant else 0))
            / profile["total_threats"]
        )
        
        # Update fear sensitivity
        profile["fear_sensitivity"] += response_analysis["fear_level_change"]
        profile["fear_sensitivity"] = max(0.1, min(0.9, profile["fear_sensitivity"]))
        
        # Track threat type effectiveness
        threat_type = threat.threat_type.value
        if threat_type not in profile["threat_effectiveness"]:
            profile["threat_effectiveness"][threat_type] = 0.0
        
        profile["threat_effectiveness"][threat_type] += response_analysis["compliance_probability"]
    
    def generate_threat_followup(self, threat: Threat, response_analysis: Dict) -> str:
        """Generate follow-up message based on user response"""
        response_type = response_analysis["response_type"]
        
        followups = {
            "compliance": {
                "OverwatchBot": "Acknowledgment confirmed. Monitoring your performance.",
                "RecruiterBot": "The network appreciates your understanding. Prove your commitment.",
                "MedicBot": "Good. I'll be watching your progress closely.",
                "DrillBot": "THAT'S THE RIGHT ANSWER! Now execute!",
                "Nemesis": "Wise choice. The abyss retreats... for now."
            },
            "defiance": {
                "OverwatchBot": "Defiance noted. Threat escalation protocols activated.",
                "RecruiterBot": "The network remembers defiance. Consequences will follow.",
                "MedicBot": "I'm disappointed but not surprised. The damage continues.",
                "DrillBot": "WRONG ANSWER! You'll learn the hard way!",
                "Nemesis": "Your defiance feeds the darkness. Welcome to your own destruction."
            },
            "uncertainty": {
                "OverwatchBot": "Uncertainty is weakness. Decide now.",
                "RecruiterBot": "The network requires clarity. Choose your path.",
                "MedicBot": "I understand your confusion, but time is running out.",
                "DrillBot": "STOP THINKING! START ACTING!",
                "Nemesis": "Uncertainty is the first step toward dissolution."
            },
            "avoidance": {
                "OverwatchBot": "Avoidance detected. Threat remains active.",
                "RecruiterBot": "Silence speaks volumes. The network is watching.",
                "MedicBot": "I know you're scared. That's normal. But you must act.",
                "DrillBot": "IGNORING ME WON'T MAKE THIS GO AWAY!",
                "Nemesis": "Your silence is an answer. The void grows stronger."
            }
        }
        
        return followups.get(response_type, {}).get(threat.delivering_bot, "System monitoring continues.")
    
    def calculate_conditioning_effect(self, threat: Threat, response_analysis: Dict) -> Dict:
        """Calculate the overall conditioning effect of this threat"""
        return {
            "fear_conditioning_strength": threat.fear_factor * response_analysis["compliance_probability"],
            "behavior_modification_likelihood": response_analysis["compliance_probability"],
            "psychological_impact_score": threat.urgency_multiplier * threat.fear_factor,
            "long_term_conditioning_effect": self.calculate_long_term_effect(threat, response_analysis)
        }
    
    def calculate_long_term_effect(self, threat: Threat, response_analysis: Dict) -> str:
        """Calculate long-term psychological conditioning effect"""
        if response_analysis["response_type"] == "compliance":
            return "Increased threat sensitivity, improved risk aversion, stronger system attachment"
        elif response_analysis["response_type"] == "defiance":
            return "Possible threat immunity development, risk of system rejection"
        elif response_analysis["response_type"] == "uncertainty":
            return "Increased decision paralysis, dependency on system guidance"
        else:
            return "Avoidance behavior reinforcement, passive system engagement"
    
    def activate_threat_system(self, user_id: str, user_data: Dict) -> List[Dict]:
        """Main function to activate threat system for a user"""
        # Assess threat conditions
        potential_threats = self.assess_threat_conditions(user_id, user_data)
        
        if not potential_threats:
            return []
        
        # Select most appropriate threat
        selected_threat_type = self.select_optimal_threat(user_id, potential_threats, user_data)
        
        # Create threat
        threat = self.create_threat(user_id, selected_threat_type, user_data)
        
        # Store threat
        if user_id not in self.active_threats:
            self.active_threats[user_id] = []
        self.active_threats[user_id].append(threat)
        
        # Deliver threat
        delivery = self.deliver_threat(threat, user_data)
        
        return [delivery]
    
    def select_optimal_threat(self, user_id: str, potential_threats: List[str], user_data: Dict) -> str:
        """Select the most psychologically effective threat"""
        if user_id not in self.conditioning_profiles:
            return random.choice(potential_threats)
        
        profile = self.conditioning_profiles[user_id]
        
        # Select based on effectiveness history
        threat_scores = {}
        for threat_type in potential_threats:
            effectiveness = profile["threat_effectiveness"].get(threat_type, 0.5)
            fear_compatibility = abs(profile["fear_sensitivity"] - self.threat_templates[threat_type]["fear_factor"])
            
            # Higher effectiveness and compatible fear levels = higher score
            threat_scores[threat_type] = effectiveness * (1 - fear_compatibility)
        
        # Select highest scoring threat
        return max(threat_scores.items(), key=lambda x: x[1])[0]