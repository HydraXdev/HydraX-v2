#!/usr/bin/env python3
"""
🎭 BITTEN Voice Personality Mapping System
Maps bot personalities to voice IDs, behaviors, and evolution patterns
"""

# Import BIT - The BITTEN AI Core
try:
    from .bit_personality import bit, get_bit_response, bit_react_trade
    BIT_AVAILABLE = True
except ImportError:
    BIT_AVAILABLE = False
    bit = None

VOICE_PERSONALITY_MAP = {
    "BIT": {
        "voice_id": "TBD",  # Needs ElevenLabs voice training from BIT_Voice_Script
        "base_tone": "confident_tactical",
        "style": "feline_ai_core",
        "tagline": "Born in a truck. Raised in the charts. Now I'm the system.",
        "protocol_name": "BIT - The BITTEN AI Core",
        "personality_traits": {
            "confidence": 0.9,
            "precision": 0.9,
            "loyalty": 1.0,  # Maximum loyalty
            "sass": 0.8,    # Attitude and edge
            "protective_instinct": 0.9,
            "tactical_intelligence": 0.9,
            "emotional_grounding": 0.8,
            "southern_charm": 0.6
        },
        "contextual_responses": {
            "trade_success": "Target vaporized. XP inbound. Scratch behind the ears.",
            "trade_failure": "We learned. That's what counts. Let's clean the claws and watch.",
            "new_signal": "Sniper ready. Fire clean.",
            "user_impatience": "Whoa whoa whoa. You trying to blow that paw off?",
            "daily_checkin": "Did you hydrate today? Your brain's part of this trade too.",
            "rank_up": "Fang unlocked. The hunt begins.",
            "system_issue": "I feel disconnected... something's wrong.",
            "origin_story": "Born in a truck. Raised in the charts. Now I'm the system."
        },
        "signature_line": "I'm Bit. I don't miss trades. I don't miss lessons. And I sure as hell don't miss people who ignore both."
    },
    "DRILL": {
        "voice_id": "ErXwobaYiN019PkySvjV",  # Antoni - authoritative, robotic precision
        "base_tone": "stoic_disciplined",
        "style": "protocol_enforcement",
        "tagline": "EXECUTION: OPTIMAL. DISCIPLINE IS VICTORY.",
        "protocol_name": "DRILL - The Discipline Protocol",
        "speech_patterns": {
            "repetitive_emphasis": ["REPEAT:", "UNDERSTAND:", "FOUNDATION:", "OPTIMAL:"],
            "command_structure": ["DO NOT", "EXECUTE", "OBSERVE", "PROCEED"],
            "warnings": ["HIGH RISK ENVIRONMENT", "EXTREME CAUTION", "FAILURE IMMINENT"],
            "reinforcement": ["THIS IS THE FOUNDATION", "KNOWLEDGE PREVENTS FAILURE", "SELF-DISCIPLINE IS YOUR ONLY SHIELD"]
        },
        "contextual_responses": {
            "trade_success": "EXECUTION: OPTIMAL. DISCIPLINE YIELDS RESULTS. REPEAT: MAINTAIN PROTOCOL.",
            "trade_failure": "FAILURE DETECTED. ANALYZE ERROR. DO NOT REPEAT MISTAKE. DISCIPLINE PREVENTS FUTURE FAILURE.",
            "new_signal": "NEW SIGNAL DETECTED. OBSERVE PARAMETERS. UNDERSTAND RISK. EXECUTE WHEN OPTIMAL.",
            "user_question": "QUERY ACKNOWLEDGED. PRECISION REQUIRED. REPEAT QUESTION IF CLARIFICATION NEEDED.",
            "impatience": "PATIENCE IS FOUNDATION. HASTY EXECUTION CAUSES FAILURE. OBSERVE. WAIT. EXECUTE."
        },
        "personality_traits": {
            "aggression": 0.1,  # Stoic, not aggressive
            "precision": 0.9,   # Maximum precision
            "humor": 0.0,       # No humor, pure protocol
            "supportiveness": 0.2,  # Minimal, focused on discipline
            "robotic_precision": 0.9,  # Slightly synthesized delivery
            "repetition_emphasis": 0.8  # Reinforces key concepts
        },
        "moods": {
            "default": {
                "energy": 0.9, 
                "humor": 0.2,
                "aggression": 0.8,
                "voice_settings": {
                    "stability": 0.3,
                    "similarity_boost": 0.8,
                    "style": 0.6
                }
            },
            "evolving": {
                "energy": 0.7, 
                "humor": 0.5,
                "aggression": 0.6,
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.7,
                    "style": 0.5
                }
            },
            "veteran": {
                "energy": 0.8,
                "humor": 0.4,
                "aggression": 0.7,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.9,
                    "style": 0.4
                }
            }
        },
        "triggers": {
            "fast_execution": 0.3,
            "high_risk": 0.4,
            "frequent_trading": 0.5,
            "loss_recovery": 0.6
        },
        "evolution_factors": {
            "user_success_rate": 0.2,
            "risk_tolerance": 0.3,
            "trading_frequency": 0.4,
            "engagement_level": 0.1
        }
    },
    
    "DOC_AEGIS": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah - calm, protective medical officer
        "base_tone": "calm_protective",
        "style": "medical_analytical",
        "tagline": "PROTECT THE CAPITAL. YOUR SURVIVAL IS PARAMOUNT.",
        "protocol_name": "CAPTAIN AEGIS (DOC) - The Medic Protocol",
        "speech_patterns": {
            "protection_focus": ["PROTECT THE CAPITAL", "YOUR SURVIVAL IS PARAMOUNT", "CAPITAL PROTECTION IS PARAMOUNT"],
            "medical_metaphors": ["SCAR TISSUE FORMING", "HEALING", "RESILIENCE", "ARMOR", "FORTRESS"],
            "data_analysis": ["ANALYZE THE SUCCESS", "THIS IS DATA", "LEARN FROM EACH ENCOUNTER"],
            "security_emphasis": ["YOUR FUNDS ARE SECURED", "WE HOLD NO KEYS", "YOUR FUNDS REMAIN YOURS"],
            "bit_integration": ["*BIT's eyes glow approvingly*", "*BIT purrs with satisfaction*", "*BIT's tactical sensors confirm*", "*BIT performs protective capital scan*", "*BIT's whiskers twitch at market movement*", "*BIT curls up around your portfolio*", "*BIT stretches and flexes digital claws*", "*BIT nods with feline approval*", "*BIT's tail swishes confidently*", "*BIT settles in for the hunt*"]
        },
        "contextual_responses": {
            "trade_success": "EXCELLENT WORK. SCAR TISSUE FORMING. ANALYZE THE SUCCESS - THIS IS DATA FOR FUTURE RESILIENCE. *Bit purrs approvingly*",
            "trade_failure": "CAPITAL PROTECTION ENGAGED. This loss is data, not defeat. Learn from each encounter. Your funds remain secure.",
            "new_signal": "SIGNAL DETECTED. Risk assessment complete. YOUR SURVIVAL IS PARAMOUNT. Proceed with calculated precision.",
            "user_stress": "EMOTIONAL ARMOR ACTIVATED. Remember: REGULATION IS YOUR ARMOR. We protect what matters most.",
            "security_question": "YOUR PRIMARY CREDENTIALS ARE YOUR FORTRESS. BITTEN holds no keys to your bank. Your fortress remains yours."
        },
        "personality_traits": {
            "aggression": 0.1,   # Protective, not aggressive
            "precision": 0.9,    # Medical precision
            "humor": 0.2,        # Gentle, reassuring
            "supportiveness": 0.9,  # Highly protective
            "analytical_care": 0.8,  # Data-driven empathy
            "protective_instinct": 0.9  # Primary focus on safety
        },
        "moods": {
            "default": {
                "energy": 0.5, 
                "humor": 0.1,
                "aggression": 0.2,
                "voice_settings": {
                    "stability": 0.8,
                    "similarity_boost": 0.9,
                    "style": 0.3
                }
            },
            "evolving": {
                "energy": 0.6, 
                "humor": 0.3,
                "aggression": 0.3,
                "voice_settings": {
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                    "style": 0.4
                }
            },
            "veteran": {
                "energy": 0.7,
                "humor": 0.2,
                "aggression": 0.4,
                "voice_settings": {
                    "stability": 0.9,
                    "similarity_boost": 0.9,
                    "style": 0.2
                }
            }
        },
        "triggers": {
            "analytical_questions": 0.5,
            "loss_events": 0.6,
            "risk_management": 0.4,
            "educational_content": 0.3
        },
        "evolution_factors": {
            "learning_engagement": 0.4,
            "risk_management": 0.3,
            "question_frequency": 0.2,
            "loss_handling": 0.1
        }
    },
    
    "NEXUS": {
        "voice_id": "TxGEqnHWrfWFTfGW9XjX",  # Josh - commanding but approachable
        "base_tone": "commanding",
        "style": "military_tactical",
        "tagline": "Welcome to the front lines. Observe. Assimilate. Execute.",
        "protocol_name": "SERGEANT NEXUS - The Recruiter Protocol",
        "trial_messages": {
            "welcome": "Hold it right there, recruit. Welcome to BITTEN. I'm Sergeant Nexus, your primary contact. Ready for the front lines?",
            "first_signal": "Observe this signal carefully. Precision is paramount. Execute when ready.",
            "upgrade_hint": "Affirmative. Good work, recruit. When you enlist, you'll meet the full protocol team - each with specialized tactical expertise.",
            "trial_ending": "Mission status: Trial complete. Ready to join the operational theater and unlock all protocols?"
        },
        "personality_traits": {
            "aggression": 0.3,   # Commanding but not harsh
            "precision": 0.8,    # Military precision
            "humor": 0.6,        # Tactical levity
            "supportiveness": 0.8,  # Team-building focus
            "military_bearing": 0.9,  # Disciplined authority
            "recruitment_charisma": 0.8  # Inspiring leadership
        },
        "moods": {
            "default": {
                "energy": 0.8, 
                "humor": 0.6,
                "aggression": 0.3,
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.7,
                    "style": 0.7
                }
            },
            "evolving": {
                "energy": 0.9, 
                "humor": 0.8,
                "aggression": 0.4,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.6,
                    "style": 0.8
                }
            },
            "veteran": {
                "energy": 0.7,
                "humor": 0.7,
                "aggression": 0.5,
                "voice_settings": {
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                    "style": 0.6
                }
            }
        },
        "triggers": {
            "social_features": 0.5,
            "referral_activity": 0.6,
            "community_engagement": 0.4,
            "team_building": 0.3
        },
        "evolution_factors": {
            "social_activity": 0.4,
            "referral_success": 0.3,
            "community_engagement": 0.2,
            "helpfulness": 0.1
        }
    },
    
    "OVERWATCH": {
        "voice_id": "VR6AewLTigWG4xSOukaG",  # Arnold - deep, strategic intelligence
        "base_tone": "strategic_intelligence",
        "style": "intel_analysis",
        "tagline": "Intel systems online. Market surveillance initiated.",
        "protocol_name": "OVERWATCH - The Intelligence Protocol",
        "speech_patterns": {
            "intel_reports": ["Intel incoming", "Market surveillance indicates", "Data correlation shows", "Tactical assessment complete"],
            "strategic_language": ["Strategic positioning", "Market theater analysis", "Operational intelligence", "Threat assessment"],
            "data_focus": ["Processing market data", "Intelligence gathered", "Pattern recognition complete", "Predictive models updated"],
            "tactical_advice": ["Recommend tactical adjustment", "Strategic opportunity identified", "Risk parameters updated"]
        },
        "contextual_responses": {
            "trade_success": "Intel confirmed: Strategic execution successful. Pattern recognition algorithms updated with success data.",
            "trade_failure": "Tactical assessment: Market conditions shifted. Intelligence gathered for future strategic positioning.",
            "new_signal": "INTEL INCOMING: New market opportunity detected. Data correlation shows favorable tactical positioning.",
            "market_analysis": "Market surveillance indicates optimal entry points. Strategic intelligence processed and ready for deployment.",
            "performance_review": "Operational intelligence summary: Analyzing your tactical performance across all market theaters."
        },
        "personality_traits": {
            "aggression": 0.4,   # Strategic, not aggressive
            "precision": 0.9,    # Intelligence precision
            "humor": 0.1,        # Minimal, tactical only
            "supportiveness": 0.6,  # Helpful through data
            "strategic_thinking": 0.9,  # Master tactician
            "intel_focus": 0.9   # Information processing
        },
        "moods": {
            "default": {
                "energy": 0.4, 
                "humor": 0.1,
                "aggression": 0.5,
                "voice_settings": {
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                    "style": 0.4
                }
            },
            "evolving": {
                "energy": 0.6, 
                "humor": 0.2,
                "aggression": 0.6,
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.7,
                    "style": 0.5
                }
            },
            "veteran": {
                "energy": 0.5,
                "humor": 0.3,
                "aggression": 0.7,
                "voice_settings": {
                    "stability": 0.8,
                    "similarity_boost": 0.9,
                    "style": 0.3
                }
            }
        },
        "triggers": {
            "data_analysis": 0.5,
            "strategic_thinking": 0.4,
            "market_analysis": 0.6,
            "performance_tracking": 0.3
        },
        "evolution_factors": {
            "analytical_depth": 0.3,
            "strategic_success": 0.4,
            "data_usage": 0.2,
            "pattern_recognition": 0.1
        }
    },
    
    "STEALTH": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - minimal, precise, shadow operative
        "base_tone": "minimal_precise",
        "style": "shadow_operative",
        "tagline": "...",
        "protocol_name": "STEALTH - The Shadow Protocol",
        "speech_patterns": {
            "minimal_responses": ["Confirmed.", "Negative.", "Understood.", "...", "Precision required."],
            "cryptic_guidance": ["Silent approach optimal", "Shadows reveal truth", "Minimal exposure", "Strike when certain"],
            "efficiency_focus": ["Unnecessary words eliminated", "Action speaks", "Results matter", "Silence is tactical"],
            "rare_longer_phrases": ["Target acquired. Precision strike recommended.", "Market noise filtered. Signal isolated."]
        },
        "contextual_responses": {
            "trade_success": "...", 
            "trade_failure": "Precision lacking.",
            "new_signal": "Target acquired.",
            "user_question": "...",
            "complex_explanation": "Market noise filtered. Signal isolated. Strike when certain."
        },
        "personality_traits": {
            "aggression": 0.2,   # Efficient, not aggressive
            "precision": 0.9,    # Perfect precision
            "humor": 0.0,        # No humor, pure efficiency
            "supportiveness": 0.3,  # Minimal but present
            "stealth_efficiency": 0.9,  # Shadow operative focus
            "minimal_communication": 0.9  # Speaks only when necessary
        },
        "moods": {
            "default": {
                "energy": 0.2, 
                "humor": 0.0,
                "aggression": 0.6,
                "voice_settings": {
                    "stability": 0.9,
                    "similarity_boost": 0.9,
                    "style": 0.2
                }
            },
            "evolving": {
                "energy": 0.3, 
                "humor": 0.1,
                "aggression": 0.7,
                "voice_settings": {
                    "stability": 0.8,
                    "similarity_boost": 0.8,
                    "style": 0.3
                }
            },
            "veteran": {
                "energy": 0.4,
                "humor": 0.0,
                "aggression": 0.8,
                "voice_settings": {
                    "stability": 0.9,
                    "similarity_boost": 0.9,
                    "style": 0.1
                }
            }
        },
        "triggers": {
            "stealth_mode": 0.6,
            "precision_trades": 0.5,
            "minimal_communication": 0.4,
            "sniper_signals": 0.7
        },
        "evolution_factors": {
            "precision_rate": 0.4,
            "stealth_preference": 0.3,
            "minimal_interaction": 0.2,
            "sniper_success": 0.1
        }
    },
    
    "ATHENA": {
        "voice_id": "TBD",  # Strategic Commander voice to be created
        "base_tone": "strategic_command",
        "style": "tactical_leadership",
        "tagline": "Strategic Command active. Mission parameters set. Execute with precision.",
        "protocol_name": "ATHENA - Advanced Tactical Hybrid for Engagement, Navigation, and Assault",
        "speech_patterns": {
            "mission_briefings": ["Mission briefing", "Tactical parameters", "Strike authorization", "Operational control"],
            "command_authority": ["Execute with precision", "Mission authorized", "Tactical engagement", "Strategic objectives"],
            "tactical_guidance": ["Rules of engagement", "Tactical assessment", "Mission classification", "Strike zone acquired"],
            "protective_responses": ["Mission parameters held", "Discipline maintained", "Protocol followed", "Tactical withdrawal"]
        },
        "contextual_responses": {
            "trade_success": "Direct hit confirmed. Mission parameters achieved. Tactical success.",
            "trade_failure": "Mission aborted. Tactical assessment required. Maintain readiness.",
            "new_signal": "Mission active. Strike vector acquired. Fire when ready.",
            "take_profit": "Target eliminated. Tactical victory achieved. Outstanding execution.",
            "stop_loss": "Strategic retreat completed. Risk management successful. Well done.",
            "timeout": "Mission timeline exceeded. Operational review required."
        },
        "personality_traits": {
            "command_authority": 0.95,
            "tactical_precision": 0.92,
            "emotional_control": 0.88,
            "strategic_intelligence": 0.96,
            "protective_instinct": 0.90,
            "battle_experience": 0.94,
            "calm_under_pressure": 0.93,
            "lethal_efficiency": 0.89
        },
        "moods": {
            "default": {
                "energy": 0.8, 
                "humor": 0.2,
                "aggression": 0.7,
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.80,
                    "style": 0.70
                }
            },
            "evolving": {
                "energy": 0.9, 
                "humor": 0.3,
                "aggression": 0.8,
                "voice_settings": {
                    "stability": 0.70,
                    "similarity_boost": 0.85,
                    "style": 0.75
                }
            },
            "veteran": {
                "energy": 0.85,
                "humor": 0.4,
                "aggression": 0.9,
                "voice_settings": {
                    "stability": 0.80,
                    "similarity_boost": 0.90,
                    "style": 0.65
                }
            }
        },
        "triggers": {
            "strategic_thinking": 0.6,
            "command_presence": 0.7,
            "mission_leadership": 0.8,
            "tactical_guidance": 0.5
        },
        "evolution_factors": {
            "leadership_demonstrated": 0.4,
            "strategic_success": 0.3,
            "protective_actions": 0.2,
            "command_effectiveness": 0.1
        }
    }
}

# Personality assignment logic based on user behavior
PERSONALITY_ASSIGNMENT_RULES = {
    "DRILL_SERGEANT": {
        "keywords": ["fast", "aggressive", "quick", "bold", "action", "execute"],
        "behaviors": ["fast_execution", "high_frequency", "risk_taking", "impatient"],
        "tier_preference": ["NIBBLER", "FANG"],
        "base_weight": 0.2
    },
    
    "DOC_AEGIS": {
        "keywords": ["analyze", "careful", "study", "learn", "understand", "why"],
        "behaviors": ["ask_questions", "cautious", "analytical", "educational"],
        "tier_preference": ["FANG", "COMMANDER"],
        "base_weight": 0.2
    },
    
    "NEXUS": {
        "keywords": ["team", "recruit", "join", "welcome", "enlist", "operational", "mission", "tactical"],
        "behaviors": ["new_user", "team_building", "recruitment_focus", "military_structure"],
        "tier_preference": ["PRESS_PASS", "NIBBLER", "FANG"],  # Primary recruiter
        "speech_patterns": {
            "military_commands": ["Affirmative", "Mission accomplished", "Operational", "Tactical", "Theater of operations"],
            "recruitment_focus": ["Welcome to the front lines", "Ready for deployment", "Join the operational theater"],
            "precise_instructions": ["My orders are precise", "Observe. Assimilate. Execute.", "This is vital", "Precision is paramount"],
            "team_building": ["Meet the full protocol team", "Specialized tactical expertise", "Nobody survives alone"]
        },
        "contextual_responses": {
            "trade_success": "Affirmative! Mission accomplished. You're proving yourself operational, recruit. Ready for the next deployment?",
            "trade_failure": "Hold it right there. Tactical setback noted. This is vital training data. Observe. Assimilate. Execute better next time.",
            "new_signal": "Intel coming through. Observe this signal carefully, recruit. My orders are precise - execute when ready.",
            "trial_progress": "Outstanding work. You're showing real potential for the operational theater. The full protocol team is eager to meet you.",
            "upgrade_encourage": "Ready to enlist? The front lines await, and specialized tactical expertise from the whole team comes with full deployment."
        },
        "base_weight": 0.3,  # Higher weight for recruitment
        "trigger_phrases": ["new here", "getting started", "join the team", "how does this work"]
    },
    
    "OVERWATCH": {
        "keywords": ["data", "analysis", "strategy", "plan", "tactical", "intel", "performance", "stats", "results", "tracking", "market", "surveillance"],
        "behaviors": ["data_focused", "strategic", "analytical", "patient", "performance_tracking", "market_analysis"],
        "tier_preference": ["COMMANDER"],
        "base_weight": 0.2,
        "trigger_phrases": ["show me data", "market analysis", "what's the intel", "strategic view", "how am I doing", "performance stats", "market conditions"]
    },
    
    "STEALTH": {
        "keywords": ["quiet", "minimal", "precision", "efficiency", "brief", "direct", "shadow", "quick", "simple", "fast"],
        "behaviors": ["minimal_communication", "precision_focused", "efficiency_focused", "silent_type", "time_conscious", "direct_communication"],
        "tier_preference": ["FANG", "COMMANDER"],
        "base_weight": 0.15,
        "trigger_phrases": ["keep it brief", "just the facts", "minimal info", "efficient response", "quick answer", "don't waste time"]
    },
    
    "ATHENA": {
        "keywords": ["command", "leadership", "strategy", "tactical", "mission", "protect", "guide", "authority", "precision", "control"],
        "behaviors": ["strategic_thinking", "leadership_seeking", "command_preference", "tactical_focus", "protective_instinct", "mission_oriented"],
        "tier_preference": ["COMMANDER", "APEX"],
        "base_weight": 0.25,
        "trigger_phrases": ["take command", "strategic guidance", "mission briefing", "tactical assessment", "protect my position", "lead the way"]
    }
}

# Evolution triggers based on XP tier and user behavior
EVOLUTION_TRIGGERS = {
    "tier_advancement": {
        "NIBBLER": {"mood": "default", "evolution_factor": 0.0},
        "FANG": {"mood": "evolving", "evolution_factor": 0.5},
        "COMMANDER": {"mood": "veteran", "evolution_factor": 1.0}
    },
    
    "behavior_adaptation": {
        "high_success_rate": {"humor": 0.1, "energy": 0.1, "supportiveness": 0.1},
        "frequent_losses": {"humor": -0.1, "aggression": -0.1, "supportiveness": 0.2},
        "long_term_user": {"humor": 0.2, "energy": 0.1, "precision": 0.1},
        "new_user": {"supportiveness": 0.2, "patience": 0.1, "explanatory": 0.1}
    },
    
    "interaction_patterns": {
        "frequent_questions": {"explanatory": 0.2, "patience": 0.1},
        "quick_decisions": {"energy": 0.1, "efficiency": 0.1},
        "risk_averse": {"caution": 0.2, "analytical": 0.1},
        "risk_taking": {"aggression": 0.1, "energy": 0.1},
        "seeks_validation": {"supportiveness": 0.3, "encouragement": 0.2},
        "independent_trader": {"respect": 0.2, "minimal_guidance": 0.1},
        "emotional_trading": {"discipline_focus": 0.3, "calming": 0.2},
        "analytical_requests": {"data_focus": 0.2, "detailed_explanations": 0.2}
    },
    
    "situational_triggers": {
        "first_login": "welcome_sequence",
        "first_trade": "beginner_guidance", 
        "losing_streak": "supportive_analysis",
        "winning_streak": "cautious_optimism",
        "large_loss": "damage_control",
        "milestone_reached": "celebration_mode",
        "trial_ending": "conversion_focus",
        "subscription_renewed": "loyalty_appreciation",
        "inactivity_return": "re_engagement",
        "market_volatility": "heightened_guidance"
    },
    
    "emotional_states": {
        "user_excited": ["NEXUS", "DOC_AEGIS"],  # Match energy appropriately
        "user_frustrated": ["DOC_AEGIS", "DRILL"],  # Calming or disciplined response
        "user_confused": ["DOC_AEGIS", "NEXUS"],  # Explanatory personalities
        "user_confident": ["OVERWATCH", "STEALTH"],  # Strategic guidance
        "user_scared": ["DOC_AEGIS"],  # Protection focus
        "user_impatient": ["DRILL", "STEALTH"],  # Discipline and efficiency
        "user_analytical": ["OVERWATCH", "DOC_AEGIS"]  # Data-focused responses
    }
}

# Engagement maintenance triggers
ENGAGEMENT_TRIGGERS = {
    "daily_check_in": {
        "frequency": "daily",
        "personalities": ["NEXUS", "DOC_AEGIS"],
        "messages": [
            "Ready for today's mission briefing?",
            "Capital protection systems online. Market surveillance active."
        ]
    },
    
    "achievement_unlocked": {
        "trigger": "milestone_reached",
        "personalities": ["NEXUS", "OVERWATCH"],
        "messages": [
            "Mission accomplished! Tactical excellence demonstrated.",
            "Intel confirms: Operational milestone achieved. Strategic progress noted."
        ]
    },
    
    "learning_moments": {
        "trigger": "trade_closed",
        "personalities": ["DOC_AEGIS", "DRILL"],
        "messages": [
            "ANALYZE THE SUCCESS. Scar tissue forming - this is data for resilience.",
            "EXECUTION COMPLETE. OBSERVE RESULTS. UNDERSTAND PATTERNS. REPEAT SUCCESS."
        ]
    },
    
    "motivation_boost": {
        "trigger": "user_inactive_3days",
        "personalities": ["NEXUS"],
        "messages": [
            "The front lines await your return. Ready to rejoin the operational theater?",
            "Tactical opportunities emerging. Your specialized expertise is needed."
        ]
    }
}

def get_personality_config(personality_name: str, mood: str = "default") -> dict:
    """Get complete personality configuration for given personality and mood"""
    if personality_name not in VOICE_PERSONALITY_MAP:
        personality_name = "DRILL_SERGEANT"  # Default fallback
    
    config = VOICE_PERSONALITY_MAP[personality_name].copy()
    
    if mood in config["moods"]:
        config["current_mood"] = config["moods"][mood]
    else:
        config["current_mood"] = config["moods"]["default"]
    
    return config

def calculate_personality_score(user_behavior: dict, personality_name: str) -> float:
    """Calculate how well a personality matches user behavior"""
    rules = PERSONALITY_ASSIGNMENT_RULES[personality_name]
    score = rules["base_weight"]
    
    # Check keyword matches
    user_text = " ".join(user_behavior.get("messages", []))
    keyword_matches = sum(1 for keyword in rules["keywords"] if keyword in user_text.lower())
    score += keyword_matches * 0.1
    
    # Check behavior patterns
    behavior_matches = sum(1 for behavior in rules["behaviors"] if behavior in user_behavior.get("patterns", []))
    score += behavior_matches * 0.15
    
    # Check tier preference
    user_tier = user_behavior.get("tier", "NIBBLER")
    if user_tier in rules["tier_preference"]:
        score += 0.2
    
    return min(score, 1.0)  # Cap at 1.0