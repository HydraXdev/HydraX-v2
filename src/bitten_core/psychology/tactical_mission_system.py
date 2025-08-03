"""
BITTEN Tactical Mission System
Transform forex education into military operations that strip emotions and build discipline
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

class MissionType(Enum):
    RECON = "reconnaissance"          # Information gathering (education)
    ASSAULT = "assault"              # Direct trading execution  
    DEFENSE = "defense"              # Risk management and protection
    SURVIVAL = "survival"            # Loss recovery and emotional control
    TRAINING = "training"            # Skill building without risk
    LIBERATION = "liberation"        # Breaking bad habits

class MissionTier(Enum):
    RECRUIT = 1      # Level 1-10: Basic training
    PRIVATE = 2      # Level 11-25: Discipline building
    SERGEANT = 3     # Level 26-50: Pattern recognition
    LIEUTENANT = 4   # Level 51-75: Advanced tactics
    CAPTAIN = 5      # Level 76-100: Market mastery
    COMMANDER = 6    # Level 100+: Teaching others

class TacticalMissionSystem:
    """
    The system that converts forex education into psychological warfare training
    """
    
    def __init__(self, db_connection, emotion_engine, personality_system):
        self.db = db_connection
        self.emotion_engine = emotion_engine
        self.personality_system = personality_system
        
        # Mission templates for progressive education
        self.mission_templates = {
            # RECRUIT TIER - Basics
            "first_contact": {
                "tier": MissionTier.RECRUIT,
                "type": MissionType.RECON,
                "title": "First Contact",
                "objective": "Understand the battlefield layout",
                "hidden_education": "Learn what pips, spreads, and leverage mean",
                "briefing": """Soldier, you've entered a war zone. The enemy has weapons you don't understand yet.
                
Your mission: Study the terrain. Learn what these 'pips' and 'spreads' are. 
This isn't gambling - it's warfare. Every number has meaning.

Intel Package: Watch the charts. Notice how price moves in small steps (pips).
See how different pairs move differently. EURUSD isn't GBPJPY.

Success Condition: Watch 5 signals without trading. Just observe.
                
Remember: Dead soldiers don't learn. Patience keeps you alive.""",
                "success_reward": 20,
                "failure_consequence": "Extension to training mode",
                "personality_guide": "DRILL",
                "duration_minutes": 60,
                "requirements": {
                    "signals_observed": 5,
                    "no_trades_placed": True,
                    "notes_taken": True
                }
            },
            
            "reading_battlefield": {
                "tier": MissionTier.RECRUIT,
                "type": MissionType.RECON,
                "title": "Reading the Battlefield",
                "objective": "Identify support and resistance zones",
                "hidden_education": "Technical analysis basics - support/resistance",
                "briefing": """The enemy leaves tracks, soldier. Learn to read them.

Support and resistance are where battles were fought before.
Price bounces off support like bullets off armor.
Resistance stops advances like barbed wire.

Mission Protocol:
1. Find 3 support levels on EURUSD daily chart
2. Mark where price reversed at least twice
3. Document why these levels held

Intel: The more times a level holds, the stronger it becomes.
When it finally breaks, the breakthrough is violent.

This knowledge separates soldiers from casualties.""",
                "success_reward": 30,
                "personality_guide": "OVERWATCH",
                "requirements": {
                    "levels_identified": 3,
                    "chart_analysis": True,
                    "documentation": True
                }
            },
            
            # PRIVATE TIER - Discipline
            "risk_protocols": {
                "tier": MissionTier.PRIVATE,
                "type": MissionType.DEFENSE,
                "title": "Risk Protocols",
                "objective": "Never risk more than you can afford to lose",
                "hidden_education": "Position sizing and risk management",
                "briefing": """Discipline separates soldiers from dead men, private.

Rule #1: Never risk more than 2% of your account on any single mission.
Why? Because even the best snipers miss sometimes.

Your Mission:
- Calculate position size for a 50-pip stop loss
- Use only 2% risk per trade
- Document the math

If you can't do the math, you can't trade.
If you won't follow the rules, you're already dead.

The market doesn't care about your feelings. It only respects discipline.""",
                "success_reward": 40,
                "personality_guide": "DOC",
                "requirements": {
                    "position_size_calculated": True,
                    "risk_percentage": 2.0,
                    "math_documented": True
                }
            },
            
            "first_blood": {
                "tier": MissionTier.PRIVATE,
                "type": MissionType.ASSAULT,
                "title": "First Blood",
                "objective": "Execute your first disciplined trade",
                "hidden_education": "Order execution and trade management",
                "briefing": """Time to draw blood, private. But controlled, calculated blood.

Your first kill must be clean:
- 85+ TCS score only
- Proper position sizing (2% risk)
- Set stop loss BEFORE you enter
- Set take profit at 2:1 ratio

This isn't gambling. This is surgical precision.

Mission Parameters:
- One trade only
- Document everything
- Follow protocol exactly
- Exit at targets (no emotions)

Success means you followed orders. Profit is secondary.
Discipline is what keeps you alive in this war.""",
                "success_reward": 100,
                "personality_guide": "DRILL",
                "requirements": {
                    "tcs_score_minimum": 85,
                    "stop_loss_set": True,
                    "take_profit_set": True,
                    "risk_managed": True,
                    "protocol_followed": True
                }
            },
            
            # SERGEANT TIER - Pattern Recognition
            "enemy_psychology": {
                "tier": MissionTier.SERGEANT,
                "type": MissionType.RECON,
                "title": "Enemy Psychology",
                "objective": "Understand retail trader behavior patterns",
                "hidden_education": "Market psychology and sentiment analysis",
                "briefing": """Know your enemy, Sergeant. Most traders are predictable.

They buy at tops (FOMO). They sell at bottoms (panic).
They overtrade after losses (revenge). They get greedy after wins.

Your mission: Study the retail herd.
- Watch how they react to news
- See how they chase breakouts
- Notice their patterns

The smart money (institutions) hunt retail stops.
They know where amateurs place orders.
Learn to think like the hunter, not the hunted.

Intel: When 95% of retail traders lose, being different isn't optional.""",
                "success_reward": 60,
                "personality_guide": "ATHENA",
                "requirements": {
                    "retail_patterns_identified": 5,
                    "institutional_analysis": True,
                    "sentiment_tracking": True
                }
            },
            
            # LIEUTENANT TIER - Advanced Tactics
            "institutional_thinking": {
                "tier": MissionTier.LIEUTENANT,
                "type": MissionType.RECON,
                "title": "Think Like the Enemy Commander",
                "objective": "Understand institutional order flow",
                "hidden_education": "Advanced market structure and order flow",
                "briefing": """You've proven yourself, Lieutenant. Time for advanced intel.

Banks and hedge funds move billions. They can't hide these movements.
Learn to see their footprints:

- Order blocks (where they accumulate positions)
- Liquidity sweeps (where they hunt stops)
- Fair value gaps (inefficiencies they create)

Mission Objectives:
1. Identify 3 institutional patterns this week
2. Document their effects on price
3. Plan entries based on their activity

The retail traders watch indicators.
The professionals watch each other.
Now you're becoming a professional.""",
                "success_reward": 150,
                "personality_guide": "OVERWATCH",
                "requirements": {
                    "institutional_patterns": 3,
                    "order_flow_analysis": True,
                    "professional_thinking": True
                }
            },
            
            # CAPTAIN TIER - Market Mastery
            "market_commander": {
                "tier": MissionTier.CAPTAIN,
                "type": MissionType.TRAINING,
                "title": "Market Commander",
                "objective": "Develop your own trading methodology",
                "hidden_education": "Creating personal trading systems",
                "briefing": """Captain, you've earned the right to lead.

Now create your own battle plan:
- Define your market approach
- Create your entry/exit rules
- Build your risk management system
- Document your methodology

This system must be:
- Backtestable
- Repeatable 
- Emotionless
- Profitable

You're no longer following orders.
You're giving them.

The market will test your leadership.
Will you lead yourself to victory or defeat?""",
                "success_reward": 300,
                "personality_guide": "ATHENA",
                "requirements": {
                    "methodology_created": True,
                    "backtesting_completed": True,
                    "rules_documented": True,
                    "leadership_demonstrated": True
                }
            },
            
            # COMMANDER TIER - Teaching Others
            "build_the_army": {
                "tier": MissionTier.COMMANDER,
                "type": MissionType.LIBERATION,
                "title": "Build the Army",
                "objective": "Train other soldiers in your methods",
                "hidden_education": "Teaching and mentoring systems",
                "briefing": """Commander, the final mission.

You've mastered the battlefield. Now multiply your force.

Train 3 recruits in your methods:
- Share your hard-earned knowledge
- Guide them through their first missions
- Help them avoid your early mistakes
- Build them into weapons like yourself

This is Norman's vision realized:
An army of disciplined traders who think tactically,
not emotionally.

Success isn't measured by your profits anymore.
It's measured by the soldiers you create.

The market bit you once. Now you bite back.
Together.""",
                "success_reward": 1000,
                "personality_guide": "NEXUS",
                "requirements": {
                    "recruits_trained": 3,
                    "knowledge_shared": True,
                    "mentoring_completed": True,
                    "army_built": True
                }
            }
        }
        
        # Situational missions for emotional events
        self.situational_missions = {
            "revenge_trading_lockdown": {
                "trigger": "consecutive_losses >= 2",
                "type": MissionType.SURVIVAL,
                "title": "Tactical Retreat",
                "briefing": """SOLDIER! Your emotions are compromised.

Consecutive losses detected. This is when most traders destroy themselves.
Not you. Not anymore.

MANDATORY STAND-DOWN:
- No trades for next 2 hours
- Review what went wrong
- Write battle report
- Wait for clear head

Revenge trading gets soldiers killed.
Smart commanders retreat to fight another day.

This isn't punishment. This is survival protocol.
Live to fight when conditions improve.""",
                "requirements": {
                    "no_trading_hours": 2,
                    "battle_report": True,
                    "emotional_reset": True
                }
            },
            
            "overconfidence_check": {
                "trigger": "win_streak >= 5",
                "type": MissionType.DEFENSE,
                "title": "Ego Check Protocol",
                "briefing": """Congratulations on your victories, soldier.

But danger approaches. Five wins in a row breeds overconfidence.
Overconfidence gets cocky soldiers killed.

MANDATORY ASSESSMENT:
- Review your recent trades
- Identify any rule violations
- Check if position sizes crept up
- Verify discipline remains intact

The market humbles everyone eventually.
Stay sharp. Stay disciplined. Stay alive.

Your next trade determines if you're lucky or skilled.""",
                "requirements": {
                    "trade_review": True,
                    "discipline_check": True,
                    "position_size_audit": True
                }
            }
        }
    
    async def get_current_mission(self, user_id: str) -> Optional[Dict]:
        """
        Get user's current active mission
        """
        try:
            query = """
            SELECT * FROM mission_progress 
            WHERE user_id = %s AND status IN ('assigned', 'in_progress')
            ORDER BY assigned_at DESC
            LIMIT 1
            """
            
            result = await self.db.fetch_one(query, (user_id,))
            return dict(result) if result else None
            
        except Exception as e:
            logging.error(f"Failed to get current mission for {user_id}: {e}")
            return None
    
    async def assign_mission(self, user_id: str, mission_id: str, context: Dict = None) -> Dict:
        """
        Assign a new mission to user
        """
        try:
            if mission_id not in self.mission_templates:
                return {"success": False, "error": "Unknown mission"}
            
            template = self.mission_templates[mission_id]
            
            # Create mission record
            query = """
            INSERT INTO mission_progress 
            (user_id, mission_id, mission_name, mission_tier, psychological_goal, 
             educational_goal, status, assigned_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            result = await self.db.fetch_one(query, (
                user_id,
                mission_id,
                template["title"],
                template["tier"].value,
                template["objective"],
                template["hidden_education"],
                "assigned",
                datetime.now()
            ))
            
            # Send mission briefing via personality system
            await self._send_mission_briefing(
                user_id,
                template,
                template["personality_guide"]
            )
            
            return {
                "success": True,
                "mission_id": mission_id,
                "database_id": result["id"],
                "title": template["title"],
                "tier": template["tier"].value
            }
            
        except Exception as e:
            logging.error(f"Failed to assign mission {mission_id} to {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_mission_progress(self, user_id: str, event_data: Dict) -> Dict:
        """
        Check if user's actions progress their current mission
        """
        try:
            current_mission = await self.get_current_mission(user_id)
            if not current_mission:
                return {"success": False, "error": "No active mission"}
            
            mission_id = current_mission["mission_id"]
            template = self.mission_templates.get(mission_id)
            
            if not template:
                return {"success": False, "error": "Mission template not found"}
            
            # Check requirements against event data
            requirements = template.get("requirements", {})
            progress = await self._evaluate_requirements(user_id, requirements, event_data)
            
            # Update mission progress
            if progress["completed"]:
                await self._complete_mission(user_id, mission_id, template)
                return {
                    "success": True,
                    "mission_completed": True,
                    "reward": template.get("success_reward", 0),
                    "next_mission": await self._suggest_next_mission(user_id, template)
                }
            else:
                await self._update_mission_progress(user_id, mission_id, progress)
                return {
                    "success": True,
                    "mission_completed": False,
                    "progress": progress["percentage"],
                    "next_step": progress["next_requirement"]
                }
                
        except Exception as e:
            logging.error(f"Failed to check mission progress for {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def trigger_situational_mission(self, user_id: str, trigger_event: str, context: Dict) -> Optional[Dict]:
        """
        Create situational mission based on emotional triggers
        """
        try:
            # Find matching situational mission
            for mission_id, mission_data in self.situational_missions.items():
                if self._evaluate_trigger(trigger_event, mission_data["trigger"], context):
                    
                    # Cancel current mission if necessary
                    current_mission = await self.get_current_mission(user_id)
                    if current_mission and mission_data["type"] == MissionType.SURVIVAL:
                        await self._suspend_mission(user_id, current_mission["mission_id"])
                    
                    # Create situational mission
                    situational_id = f"situational_{mission_id}_{int(datetime.now().timestamp())}"
                    
                    query = """
                    INSERT INTO mission_progress 
                    (user_id, mission_id, mission_name, mission_tier, psychological_goal,
                     status, assigned_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """
                    
                    result = await self.db.fetch_one(query, (
                        user_id,
                        situational_id,
                        mission_data["title"],
                        999,  # Emergency priority
                        "Emotional intervention",
                        "assigned",
                        datetime.now()
                    ))
                    
                    # Send emergency briefing
                    await self.personality_system.send_intervention(
                        user_id,
                        "DRILL",
                        mission_data["briefing"],
                        context
                    )
                    
                    return {
                        "mission_id": situational_id,
                        "title": mission_data["title"],
                        "type": mission_data["type"].value,
                        "emergency": True
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to trigger situational mission for {user_id}: {e}")
            return None
    
    async def get_mission_briefing(self, user_id: str, mission_id: str) -> Dict:
        """
        Generate formatted mission briefing for user
        """
        try:
            if mission_id not in self.mission_templates:
                return {"success": False, "error": "Mission not found"}
            
            template = self.mission_templates[mission_id]
            
            # Get user's psychological profile for personalization
            user_profile = await self._get_user_psychology_profile(user_id)
            
            # Format briefing with military styling
            briefing = f"""🎖️ **MISSION BRIEFING**
**Operation**: {template['title']}
**Classification**: {template['tier'].name}
**Objective**: {template['objective']}

📋 **INTELLIGENCE REPORT**
{template['briefing']}

⏱️ **TIME FRAME**: {template.get('duration_minutes', 'Unlimited')} minutes
🎯 **SUCCESS REWARD**: +{template.get('success_reward', 0)} XP
👤 **COMMANDING OFFICER**: {template['personality_guide']}

**TYPE /missions TO ACCEPT THIS ASSIGNMENT**
"""
            
            return {
                "success": True,
                "briefing": briefing,
                "mission_data": template,
                "personalization": self._personalize_briefing(template, user_profile)
            }
            
        except Exception as e:
            logging.error(f"Failed to generate briefing for {mission_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # Helper methods
    async def _send_mission_briefing(self, user_id: str, template: Dict, personality: str):
        """Send mission briefing through personality system"""
        await self.personality_system.send_message(
            user_id,
            personality,
            template["briefing"],
            {"mission": True, "educational": True}
        )
    
    async def _evaluate_requirements(self, user_id: str, requirements: Dict, event_data: Dict) -> Dict:
        """Evaluate if user has met mission requirements"""
        completed_count = 0
        total_requirements = len(requirements)
        next_requirement = None
        
        for req_key, req_value in requirements.items():
            if self._check_requirement(req_key, req_value, event_data):
                completed_count += 1
            elif next_requirement is None:
                next_requirement = req_key
        
        percentage = (completed_count / total_requirements) * 100
        
        return {
            "completed": completed_count == total_requirements,
            "percentage": percentage,
            "completed_count": completed_count,
            "total_requirements": total_requirements,
            "next_requirement": next_requirement
        }
    
    def _check_requirement(self, req_key: str, req_value: Any, event_data: Dict) -> bool:
        """Check if individual requirement is met"""
        if req_key in event_data:
            if isinstance(req_value, bool):
                return bool(event_data[req_key]) == req_value
            elif isinstance(req_value, (int, float)):
                return event_data[req_key] >= req_value
            else:
                return event_data[req_key] == req_value
        return False
    
    def _evaluate_trigger(self, trigger_event: str, trigger_condition: str, context: Dict) -> bool:
        """Evaluate if trigger condition is met"""
        # Parse trigger condition (e.g., "consecutive_losses >= 2")
        if ">=" in trigger_condition:
            field, value = trigger_condition.split(">=")
            field, value = field.strip(), int(value.strip())
            return context.get(field, 0) >= value
        elif "==" in trigger_condition:
            field, value = trigger_condition.split("==")
            field, value = field.strip(), value.strip()
            return str(context.get(field, "")) == value
        
        return False
    
    async def _complete_mission(self, user_id: str, mission_id: str, template: Dict):
        """Mark mission as completed and award rewards"""
        query = """
        UPDATE mission_progress 
        SET status = 'completed', completed_at = %s
        WHERE user_id = %s AND mission_id = %s
        """
        
        await self.db.execute(query, (datetime.now(), user_id, mission_id))
        
        # Award XP
        reward = template.get("success_reward", 0)
        if reward > 0:
            await self._award_xp(user_id, reward, f"Mission: {template['title']}")
        
        # Send completion message
        await self.personality_system.send_message(
            user_id,
            template["personality_guide"],
            f"Mission accomplished, soldier! {template['title']} completed. +{reward} XP earned.",
            {"celebration": True, "mission_complete": True}
        )
    
    async def _suggest_next_mission(self, user_id: str, completed_template: Dict) -> Optional[str]:
        """Suggest next logical mission based on progression"""
        user_level = await self._get_user_level(user_id)
        current_tier = completed_template["tier"]
        
        # Find next mission in same tier or next tier
        for mission_id, template in self.mission_templates.items():
            if (template["tier"] == current_tier or 
                template["tier"].value == current_tier.value + 1):
                
                # Check if user already completed this mission
                if not await self._mission_completed_by_user(user_id, mission_id):
                    return mission_id
        
        return None
    
    async def _get_user_psychology_profile(self, user_id: str) -> Dict:
        """Get user's psychological profile for personalization"""
        query = """
        SELECT trauma_type, tactical_identity, emotions_replaced, story_chapter
        FROM user_psychology 
        WHERE user_id = %s
        """
        
        result = await self.db.fetch_one(query, (user_id,))
        return dict(result) if result else {}
    
    def _personalize_briefing(self, template: Dict, profile: Dict) -> str:
        """Add personal touches based on user's psychological profile"""
        trauma_type = profile.get("trauma_type")
        
        if trauma_type == "blown_account":
            return "Remember: Discipline prevents account destruction."
        elif trauma_type == "revenge_trade":
            return "Stay calm. Emotion is the enemy's weapon."
        elif trauma_type == "borrowed_money":
            return "Risk only what you can afford. Protect your family."
        else:
            return "Follow protocol. Trust the process."
    
    async def _award_xp(self, user_id: str, amount: int, reason: str):
        """Award XP to user"""
        # Integration with existing XP system
        pass
    
    async def _get_user_level(self, user_id: str) -> int:
        """Get user's current level"""
        # Integration with existing level system
        return 1
    
    async def _mission_completed_by_user(self, user_id: str, mission_id: str) -> bool:
        """Check if user already completed this mission"""
        query = """
        SELECT 1 FROM mission_progress 
        WHERE user_id = %s AND mission_id = %s AND status = 'completed'
        """
        
        result = await self.db.fetch_one(query, (user_id, mission_id))
        return result is not None