"""
BITTEN Psychological Integration Layer
Connects all psychological warfare components into a unified system
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from .norman_start import NormanOnboarding
from .emotion_replacement_engine import EmotionReplacementEngine, TradingEmotion
from .tactical_mission_system import TacticalMissionSystem, MissionType, MissionTier
from .bitten_soul_filter import BittenSoulFilter, SoulAlignment

class BittenPsychologicalSystem:
    """
    The master orchestrator of BITTEN's psychological warfare system
    """
    
    def __init__(self, db_connection, telegram_bot, lockout_system):
        self.db = db_connection
        self.telegram_bot = telegram_bot
        
        # Initialize core psychological components
        self.soul_filter = BittenSoulFilter()
        self.norman_onboarding = NormanOnboarding()
        
        # Initialize with proper mock systems for now
        self.emotion_engine = EmotionReplacementEngine(
            db_connection, 
            self, # personality system
            lockout_system
        )
        
        self.mission_system = TacticalMissionSystem(
            db_connection,
            self.emotion_engine,
            self  # personality system
        )
        
        # Psychological state tracking
        self.active_interventions = {}  # user_id -> intervention_data
        self.mission_progress = {}      # user_id -> mission_state
        
    async def process_user_onboarding(self, user_id: str, username: str) -> Dict:
        """
        Handle complete user onboarding with Norman's story
        """
        try:
            # Generate Norman's onboarding sequence
            sequence = await self.norman_onboarding.start_sequence(user_id, username)
            
            # Initialize psychological profile
            await self._initialize_user_psychology(user_id)
            
            # Assign first mission
            first_mission = await self.mission_system.assign_mission(
                user_id, 
                "first_contact"
            )
            
            return {
                "success": True,
                "onboarding_sequence": sequence,
                "first_mission": first_mission,
                "psychological_profile_created": True
            }
            
        except Exception as e:
            logging.error(f"Onboarding failed for {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_trading_event(self, user_id: str, event_type: str, event_data: Dict) -> Dict:
        """
        Process any trading-related event through the psychological system
        """
        try:
            results = {
                "emotion_analysis": None,
                "mission_progress": None,
                "interventions": [],
                "soul_filter_check": None
            }
            
            # 1. Emotion Detection and Replacement
            if event_type in ["trade_placed", "trade_closed", "loss_occurred"]:
                emotion = await self.emotion_engine.detect_emotion(user_id, event_data)
                if emotion:
                    replacement_result = await self.emotion_engine.replace_emotion(
                        user_id, emotion, event_data
                    )
                    results["emotion_analysis"] = replacement_result
                    
                    # Check if we need situational missions
                    if emotion in [TradingEmotion.REVENGE, TradingEmotion.PANIC, TradingEmotion.DESPERATION]:
                        situational_mission = await self.mission_system.trigger_situational_mission(
                            user_id, f"{emotion.value}_detected", event_data
                        )
                        if situational_mission:
                            results["interventions"].append(situational_mission)
            
            # 2. Mission Progress Check
            mission_progress = await self.mission_system.check_mission_progress(
                user_id, event_data
            )
            results["mission_progress"] = mission_progress
            
            # 3. Soul Filter for any messages/features being used
            if "message" in event_data:
                soul_check = self.soul_filter.evaluate_message(
                    event_data["message"],
                    {"user_id": user_id, "event_type": event_type}
                )
                results["soul_filter_check"] = soul_check
                
                # Auto-improve non-aligned messages
                if soul_check["alignment"] in [SoulAlignment.CORRUPTED, SoulAlignment.POISON]:
                    improved_message = self.soul_filter.ensure_tactical_message(
                        event_data["message"]
                    )
                    results["improved_message"] = improved_message
            
            return {
                "success": True,
                "user_id": user_id,
                "event_type": event_type,
                "results": results,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logging.error(f"Failed to process trading event for {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_psychological_state(self, user_id: str) -> Dict:
        """
        Get complete psychological state for user
        """
        try:
            # Get psychology profile
            query = """
            SELECT * FROM user_psychology WHERE user_id = %s
            """
            psychology = await self.db.fetch_one(query, (user_id,))
            
            # Get current mission
            current_mission = await self.mission_system.get_current_mission(user_id)
            
            # Get recent emotion replacements
            emotion_query = """
            SELECT * FROM emotion_replacements 
            WHERE user_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 5
            """
            recent_emotions = await self.db.fetch_all(emotion_query, (user_id,))
            
            # Get stealth education progress
            education_query = """
            SELECT concept_category, COUNT(*) as concepts_learned,
                   AVG(understanding_level) as avg_understanding
            FROM stealth_education 
            WHERE user_id = %s
            GROUP BY concept_category
            """
            education_progress = await self.db.fetch_all(education_query, (user_id,))
            
            return {
                "psychology_profile": dict(psychology) if psychology else None,
                "current_mission": current_mission,
                "recent_emotions": [dict(row) for row in recent_emotions],
                "education_progress": [dict(row) for row in education_progress],
                "psychological_health_score": await self._calculate_health_score(user_id)
            }
            
        except Exception as e:
            logging.error(f"Failed to get psychological state for {user_id}: {e}")
            return {"error": str(e)}
    
    async def send_intervention(self, user_id: str, personality: str, message: str, context: Dict) -> Dict:
        """
        Send intervention message through appropriate personality
        """
        try:
            # Filter message through soul filter
            filtered_message = self.soul_filter.ensure_tactical_message(message, personality)
            
            # Send via Telegram bot (mock implementation)
            await self.send_message(user_id, personality, filtered_message, context)
            
            # Log intervention
            await self._log_intervention(user_id, personality, filtered_message, context)
            
            return {
                "success": True,
                "personality": personality,
                "message_sent": filtered_message,
                "original_message": message
            }
            
        except Exception as e:
            logging.error(f"Failed to send intervention to {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_message(self, user_id: str, personality: str, message: str, context: Dict):
        """
        Mock personality system message sending
        """
        # This would integrate with the actual personality bot system
        logging.info(f"[{personality}] Message to {user_id}: {message}")
        
        # Store for retrieval
        if user_id not in self.active_interventions:
            self.active_interventions[user_id] = []
        
        self.active_interventions[user_id].append({
            "personality": personality,
            "message": message,
            "context": context,
            "timestamp": datetime.now()
        })
    
    def validate_feature_alignment(self, feature_description: str, feature_config: Dict = None) -> Dict:
        """
        Validate any new feature against BITTEN's soul
        """
        return self.soul_filter.evaluate_feature(feature_description, feature_config or {})
    
    def validate_message_alignment(self, message: str, context: Dict = None) -> Dict:
        """
        Validate message alignment with psychological warfare mission
        """
        return self.soul_filter.evaluate_message(message, context or {})
    
    # Helper methods
    async def _initialize_user_psychology(self, user_id: str):
        """
        Create initial psychological profile for new user
        """
        query = """
        INSERT INTO user_psychology 
        (user_id, trauma_severity, emotions_replaced, tactical_identity,
         story_chapter, bit_trust_score, dissociation_level, reality_anchor_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
        """
        
        await self.db.execute(query, (
            user_id,
            5,  # Default trauma severity
            '{}',  # Empty emotions replaced
            None,  # No tactical identity yet
            0,  # Story chapter 0
            0,  # No Bit trust yet
            0.0,  # No dissociation yet
            1.0   # Full reality anchor
        ))
    
    async def _calculate_health_score(self, user_id: str) -> float:
        """
        Calculate overall psychological health score (0-100)
        """
        try:
            # Get psychology data
            query = """
            SELECT 
                emotion_incidents,
                tilt_recovery_time,
                bit_trust_score,
                dissociation_level,
                reality_anchor_score
            FROM user_psychology 
            WHERE user_id = %s
            """
            
            result = await self.db.fetch_one(query, (user_id,))
            if not result:
                return 50.0  # Neutral baseline
            
            # Calculate component scores
            emotion_score = max(0, 100 - len(result.get("emotion_incidents", [])) * 5)
            trust_score = max(0, min(100, result.get("bit_trust_score", 0) + 50))
            reality_score = result.get("reality_anchor_score", 1.0) * 100
            
            # Weighted average
            health_score = (emotion_score * 0.4 + trust_score * 0.3 + reality_score * 0.3)
            
            return round(health_score, 1)
            
        except Exception as e:
            logging.error(f"Failed to calculate health score for {user_id}: {e}")
            return 50.0
    
    async def _log_intervention(self, user_id: str, personality: str, message: str, context: Dict):
        """
        Log personality intervention to database
        """
        query = """
        INSERT INTO personality_interactions
        (user_id, personality, trigger_event, message_sent, timestamp)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        await self.db.execute(query, (
            user_id,
            personality,
            context.get("trigger_event", "manual"),
            message,
            datetime.now()
        ))