"""
BITTEN Emotion Replacement Engine
The core system that strips trading emotions and replaces them with tactical protocols
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging

class TradingEmotion(Enum):
    FEAR = "fear"
    GREED = "greed" 
    REVENGE = "revenge"
    HOPE = "hope"
    PANIC = "panic"
    FOMO = "fomo"
    OVERCONFIDENCE = "overconfidence"
    DESPERATION = "desperation"

class TacticalProtocol(Enum):
    RETREAT = "retreat"
    OBJECTIVE = "objective"
    COOLDOWN = "cooldown"
    EVACUATION = "evacuation"
    DRILL = "drill"
    PATIENCE = "patience"
    HUMILITY = "humility"
    DISCIPLINE = "discipline"

class EmotionReplacementEngine:
    """
    The weapon that turns emotional traders into tactical operators
    """
    
    def __init__(self, db_connection, personality_system, lockout_system):
        self.db = db_connection
        self.personality = personality_system
        self.lockout = lockout_system
        
        # Emotion -> Protocol mapping
        self.replacement_matrix = {
            TradingEmotion.FEAR: {
                "protocol": TacticalProtocol.RETREAT,
                "message": "Fear detected. Executing tactical retreat protocol.",
                "action": "reduce_position_size",
                "personality": "DRILL",
                "lockout_minutes": 10
            },
            TradingEmotion.GREED: {
                "protocol": TacticalProtocol.OBJECTIVE,
                "message": "Greed compromises mission success. Stick to objectives.",
                "action": "enforce_take_profit",
                "personality": "DOC",
                "lockout_minutes": 5
            },
            TradingEmotion.REVENGE: {
                "protocol": TacticalProtocol.COOLDOWN,
                "message": "Revenge gets soldiers killed. Mandatory cooldown initiated.",
                "action": "trading_lockout",
                "personality": "DRILL",
                "lockout_minutes": 60
            },
            TradingEmotion.HOPE: {
                "protocol": TacticalProtocol.EVACUATION,
                "message": "Hope is not a strategy. Evacuate failing positions.",
                "action": "force_stop_loss",
                "personality": "OVERWATCH",
                "lockout_minutes": 15
            },
            TradingEmotion.PANIC: {
                "protocol": TacticalProtocol.DRILL,
                "message": "Panic breaks formation. Execute emergency protocols.",
                "action": "close_all_positions",
                "personality": "DRILL",
                "lockout_minutes": 30
            },
            TradingEmotion.FOMO: {
                "protocol": TacticalProtocol.PATIENCE,
                "message": "Sniper waits for perfect shot. FOMO gets you killed.",
                "action": "delay_entry",
                "personality": "OVERWATCH",
                "lockout_minutes": 20
            },
            TradingEmotion.OVERCONFIDENCE: {
                "protocol": TacticalProtocol.HUMILITY,
                "message": "Even generals can die. Reduce exposure.",
                "action": "reduce_leverage",
                "personality": "ATHENA",
                "lockout_minutes": 0
            },
            TradingEmotion.DESPERATION: {
                "protocol": TacticalProtocol.DISCIPLINE,
                "message": "Desperation clouds judgment. Return to basics.",
                "action": "force_demo_mode",
                "personality": "DOC",
                "lockout_minutes": 120
            }
        }
        
        # Emotion detection triggers
        self.emotion_triggers = {
            TradingEmotion.FEAR: [
                "consecutive_losses >= 2",
                "drawdown_percent > 5",
                "position_size > normal_size * 0.5"
            ],
            TradingEmotion.GREED: [
                "profit_target_moved_up > 2",
                "position_size > normal_size * 2", 
                "risk_per_trade > 3"
            ],
            TradingEmotion.REVENGE: [
                "trade_within_minutes_of_loss <= 10",
                "position_size_after_loss > previous_size * 1.5",
                "same_pair_reentry_immediate == True"
            ],
            TradingEmotion.HOPE: [
                "stop_loss_moved_further > 2",
                "position_held_past_target == True",
                "drawdown_ignored > 10"
            ],
            TradingEmotion.PANIC: [
                "rapid_trades_in_minutes > 3",
                "stop_losses_removed > 1",
                "account_drawdown > 15"
            ],
            TradingEmotion.FOMO: [
                "trade_after_big_move == True",
                "no_analysis_trade == True",
                "chase_breakout == True"
            ],
            TradingEmotion.OVERCONFIDENCE: [
                "win_streak >= 5",
                "position_size_increasing_trend == True",
                "risk_management_relaxed == True"
            ],
            TradingEmotion.DESPERATION: [
                "account_balance < 50_percent_of_start",
                "borrowed_money_flags == True",
                "all_in_trades > 0"
            ]
        }
        
    async def detect_emotion(self, user_id: str, trading_event: Dict) -> Optional[TradingEmotion]:
        """
        Analyze trading behavior to detect emotional state
        """
        try:
            # Get user's recent trading history
            user_history = await self._get_user_trading_history(user_id, days=7)
            
            # Check each emotion trigger
            for emotion, triggers in self.emotion_triggers.items():
                if await self._evaluate_triggers(user_id, triggers, trading_event, user_history):
                    return emotion
                    
            return None
            
        except Exception as e:
            logging.error(f"Emotion detection failed for {user_id}: {e}")
            return None
    
    async def replace_emotion(self, user_id: str, emotion: TradingEmotion, context: Dict) -> Dict:
        """
        Execute emotion replacement protocol
        """
        if emotion not in self.replacement_matrix:
            return {"success": False, "error": "Unknown emotion"}
            
        protocol_config = self.replacement_matrix[emotion]
        
        try:
            # Log the emotion event
            await self._log_emotion_event(user_id, emotion, context)
            
            # Execute tactical protocol
            protocol_result = await self._execute_protocol(
                user_id, 
                protocol_config["protocol"],
                protocol_config["action"],
                context
            )
            
            # Send personality intervention
            personality_message = await self._send_personality_intervention(
                user_id,
                protocol_config["personality"],
                emotion,
                protocol_config["message"],
                context
            )
            
            # Apply lockout if necessary
            lockout_result = None
            if protocol_config["lockout_minutes"] > 0:
                lockout_result = await self._apply_tactical_lockout(
                    user_id,
                    protocol_config["lockout_minutes"],
                    f"{emotion.value} intervention"
                )
            
            # Update user psychology profile
            await self._update_psychology_profile(user_id, emotion, protocol_config["protocol"])
            
            return {
                "success": True,
                "emotion": emotion.value,
                "protocol": protocol_config["protocol"].value,
                "personality_response": personality_message,
                "protocol_result": protocol_result,
                "lockout_applied": lockout_result is not None,
                "lockout_minutes": protocol_config["lockout_minutes"]
            }
            
        except Exception as e:
            logging.error(f"Emotion replacement failed for {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _evaluate_triggers(self, user_id: str, triggers: List[str], 
                                event: Dict, history: Dict) -> bool:
        """
        Evaluate if emotion triggers are met
        """
        triggered_count = 0
        
        for trigger in triggers:
            if await self._evaluate_single_trigger(trigger, user_id, event, history):
                triggered_count += 1
                
        # Require at least 1 trigger for emotion detection
        return triggered_count >= 1
    
    async def _evaluate_single_trigger(self, trigger: str, user_id: str, 
                                     event: Dict, history: Dict) -> bool:
        """
        Evaluate a single emotion trigger condition
        """
        try:
            # Parse trigger condition
            if ">=" in trigger:
                field, value = trigger.split(">=")
                field, value = field.strip(), float(value.strip())
                return self._get_field_value(field, event, history) >= value
                
            elif ">" in trigger:
                field, value = trigger.split(">")
                field, value = field.strip(), float(value.strip())
                return self._get_field_value(field, event, history) > value
                
            elif "<=" in trigger:
                field, value = trigger.split("<=")
                field, value = field.strip(), float(value.strip())
                return self._get_field_value(field, event, history) <= value
                
            elif "<" in trigger:
                field, value = trigger.split("<")
                field, value = field.strip(), float(value.strip())
                return self._get_field_value(field, event, history) < value
                
            elif "==" in trigger:
                field, value = trigger.split("==")
                field, value = field.strip(), value.strip()
                if value == "True":
                    return bool(self._get_field_value(field, event, history))
                elif value == "False":
                    return not bool(self._get_field_value(field, event, history))
                else:
                    return str(self._get_field_value(field, event, history)) == value
                    
            return False
            
        except Exception as e:
            logging.error(f"Trigger evaluation failed: {trigger} - {e}")
            return False
    
    def _get_field_value(self, field: str, event: Dict, history: Dict) -> Any:
        """
        Extract field value from event or history data
        """
        # Check event data first
        if field in event:
            return event[field]
            
        # Check calculated fields from history
        calculated_fields = {
            "consecutive_losses": self._count_consecutive_losses(history),
            "drawdown_percent": self._calculate_drawdown_percent(history),
            "normal_size": self._get_normal_position_size(history),
            "win_streak": self._count_win_streak(history),
            "account_balance": history.get("current_balance", 0),
            "50_percent_of_start": history.get("starting_balance", 0) * 0.5
        }
        
        if field in calculated_fields:
            return calculated_fields[field]
            
        return 0
    
    async def _execute_protocol(self, user_id: str, protocol: TacticalProtocol, 
                              action: str, context: Dict) -> Dict:
        """
        Execute the tactical protocol action
        """
        try:
            protocol_actions = {
                "reduce_position_size": self._reduce_position_size,
                "enforce_take_profit": self._enforce_take_profit,
                "trading_lockout": self._apply_trading_lockout,
                "force_stop_loss": self._force_stop_loss,
                "close_all_positions": self._close_all_positions,
                "delay_entry": self._delay_entry,
                "reduce_leverage": self._reduce_leverage,
                "force_demo_mode": self._force_demo_mode
            }
            
            if action in protocol_actions:
                return await protocol_actions[action](user_id, context)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logging.error(f"Protocol execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_personality_intervention(self, user_id: str, personality: str,
                                           emotion: TradingEmotion, message: str,
                                           context: Dict) -> Dict:
        """
        Send personality-specific intervention message
        """
        personality_messages = {
            "DRILL": {
                TradingEmotion.FEAR: [
                    "EMOTION GETS YOU KILLED! Fear is the enemy's weapon. Use protocol instead.",
                    "Scared soldiers don't make it home. Execute retreat protocol NOW.",
                    "Fear is information, not instruction. What's the protocol tell you?"
                ],
                TradingEmotion.REVENGE: [
                    "REVENGE TRADING IS SUICIDE! Wounded soldiers can't fight effectively.",
                    "The market doesn't care about your feelings. DISCIPLINE wins wars.",
                    "You want revenge? Get profitable. Everything else is just bleeding."
                ]
            },
            "DOC": {
                TradingEmotion.GREED: [
                    "Greed is the silent killer in trading. Stick to your risk parameters.",
                    "I've seen traders lose everything chasing just one more pip.",
                    "Your family needs you profitable, not broke. Take the profit."
                ],
                TradingEmotion.DESPERATION: [
                    "Desperation makes bad decisions. Let's step back and regroup.",
                    "The market will be here tomorrow. Your capital might not be if you keep this up.",
                    "Sometimes the best trade is no trade. Protect what you have."
                ]
            },
            "OVERWATCH": {
                TradingEmotion.HOPE: [
                    "Hope without a plan is just gambling. Cut the losses.",
                    "The market doesn't care about your hopes. It cares about probability.",
                    "Another retail dreamer holding bags. When will you learn?"
                ],
                TradingEmotion.FOMO: [
                    "FOMO is how they separate you from your money. Stay patient.",
                    "The best opportunities come to those who wait. Don't chase.",
                    "Every missed trade saves you from the next trap. Trust the process."
                ]
            },
            "ATHENA": {
                TradingEmotion.OVERCONFIDENCE: [
                    "Pride comes before the fall, child. The river humbles all swimmers.",
                    "Confidence is good. Overconfidence is expensive. Know the difference.",
                    "Even the mightiest oak can be felled by wind. Stay flexible."
                ]
            }
        }
        
        # Get personality-specific messages
        messages = personality_messages.get(personality, {}).get(emotion, [message])
        selected_message = messages[0] if messages else message
        
        # Send through personality system
        return await self.personality.send_intervention(
            user_id, 
            personality, 
            selected_message,
            context
        )
    
    async def _log_emotion_event(self, user_id: str, emotion: TradingEmotion, context: Dict):
        """
        Log emotion replacement event to database
        """
        query = """
        INSERT INTO emotion_replacements 
        (user_id, original_emotion, emotion_trigger, emotion_intensity, 
         replacement_protocol, market_conditions, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        await self.db.execute(query, (
            user_id,
            emotion.value,
            context.get("trigger", "unknown"),
            context.get("intensity", 0.5),
            self.replacement_matrix[emotion]["protocol"].value,
            json.dumps(context.get("market_conditions", {})),
            datetime.now()
        ))
    
    async def _update_psychology_profile(self, user_id: str, emotion: TradingEmotion, 
                                       protocol: TacticalProtocol):
        """
        Update user's psychological profile with replacement progress
        """
        query = """
        UPDATE user_psychology 
        SET emotions_replaced = COALESCE(emotions_replaced, '{}'::jsonb) || 
            json_build_object(%s, COALESCE((emotions_replaced->>%s)::float, 0) + 0.1)::jsonb,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
        """
        
        await self.db.execute(query, (emotion.value, emotion.value, user_id))
    
    # Protocol action implementations
    async def _reduce_position_size(self, user_id: str, context: Dict) -> Dict:
        """Reduce position size by 50%"""
        # Implementation would integrate with trading system
        return {"action": "position_size_reduced", "reduction": 0.5}
    
    async def _enforce_take_profit(self, user_id: str, context: Dict) -> Dict:
        """Force take profit at current levels"""
        return {"action": "take_profit_enforced", "level": context.get("current_profit", 0)}
    
    async def _apply_trading_lockout(self, user_id: str, context: Dict) -> Dict:
        """Apply trading lockout"""
        return await self.lockout.apply_lockout(user_id, 60, "revenge_trading_prevention")
    
    async def _force_stop_loss(self, user_id: str, context: Dict) -> Dict:
        """Force stop loss execution"""
        return {"action": "stop_loss_forced", "positions_closed": context.get("open_positions", 0)}
    
    async def _close_all_positions(self, user_id: str, context: Dict) -> Dict:
        """Emergency position closure"""
        return {"action": "all_positions_closed", "emergency": True}
    
    async def _delay_entry(self, user_id: str, context: Dict) -> Dict:
        """Delay trade entry"""
        return await self.lockout.apply_lockout(user_id, 20, "fomo_prevention")
    
    async def _reduce_leverage(self, user_id: str, context: Dict) -> Dict:
        """Reduce leverage"""
        return {"action": "leverage_reduced", "new_leverage": "conservative"}
    
    async def _force_demo_mode(self, user_id: str, context: Dict) -> Dict:
        """Force demo trading mode"""
        return {"action": "demo_mode_activated", "duration_hours": 48}
    
    # Helper methods for trigger evaluation
    def _count_consecutive_losses(self, history: Dict) -> int:
        """Count consecutive losing trades"""
        trades = history.get("recent_trades", [])
        consecutive = 0
        for trade in reversed(trades):
            if trade.get("profit", 0) < 0:
                consecutive += 1
            else:
                break
        return consecutive
    
    def _calculate_drawdown_percent(self, history: Dict) -> float:
        """Calculate current drawdown percentage"""
        peak = history.get("peak_balance", history.get("current_balance", 0))
        current = history.get("current_balance", 0)
        if peak == 0:
            return 0
        return ((peak - current) / peak) * 100
    
    def _get_normal_position_size(self, history: Dict) -> float:
        """Get user's normal position size"""
        trades = history.get("recent_trades", [])
        if not trades:
            return 0.01
        sizes = [trade.get("position_size", 0.01) for trade in trades[-10:]]
        return sum(sizes) / len(sizes)
    
    def _count_win_streak(self, history: Dict) -> int:
        """Count consecutive winning trades"""
        trades = history.get("recent_trades", [])
        streak = 0
        for trade in reversed(trades):
            if trade.get("profit", 0) > 0:
                streak += 1
            else:
                break
        return streak
    
    async def _get_user_trading_history(self, user_id: str, days: int = 7) -> Dict:
        """Get user's recent trading history"""
        # This would query the trading database
        # Return mock data for now
        return {
            "recent_trades": [],
            "current_balance": 10000,
            "starting_balance": 10000,
            "peak_balance": 10000
        }