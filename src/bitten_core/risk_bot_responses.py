"""
Risk Controller Bot Response Integration

Provides PsyOps bot personalities for risk control events.
"""

from typing import Dict, Optional
from enum import Enum

class RiskEvent(Enum):
    """Risk control events that trigger bot responses"""
    COOLDOWN_ACTIVATED = "cooldown_activated"
    COOLDOWN_WARNING = "cooldown_warning"
    RISK_MODE_CHANGED = "risk_mode_changed"
    DRAWDOWN_WARNING = "drawdown_warning"
    DRAWDOWN_LIMIT_HIT = "drawdown_limit_hit"
    RECOVERY_ACHIEVED = "recovery_achieved"

class RiskBotResponses:
    """Bot personality responses for risk control events"""
    
    @staticmethod
    def get_cooldown_activation_response(consecutive_losses: int, loss_amounts: list) -> Dict[str, str]:
        """Get bot responses when cooldown is activated"""
        total_loss = sum(loss_amounts)
        
        return {
            "overwatchbot": f"⚠️ TACTICAL OVERRIDE ENGAGED. {consecutive_losses} consecutive high-risk losses detected. "
                          f"Total damage: ${total_loss:.2f}. Throttle down to 1.0% risk.",
            
            "medicbot": f"🩺 Recovery protocol initiated. Your mind needs time to recalibrate. "
                       f"I've seen this pattern before - trust the process. Cooldown will protect your capital.",
            
            "drillbot": "SOLDIER! YOU'RE TILTED AND MAKING POOR DECISIONS. "
                       "MANDATORY COOLDOWN ENFORCED. NO ARGUMENTS.",
            
            "bit": "*sits firmly on the risk toggle button* No touchy! 🐾"
        }
    
    @staticmethod
    def get_cooldown_warning_response(current_losses: int) -> Dict[str, str]:
        """Get bot responses when approaching cooldown trigger"""
        return {
            "overwatchbot": f"⚡ WARNING: {current_losses}/2 high-risk losses. "
                          f"One more loss triggers mandatory cooldown.",
            
            "medicbot": "I'm noticing elevated stress patterns. Consider switching to "
                       "default risk mode before it's too late.",
            
            "drillbot": "DANGER CLOSE! ONE MORE LOSS AND YOU'RE BENCHED!",
            
            "bit": "*nervous tail twitching* 😰"
        }
    
    @staticmethod
    def get_risk_mode_change_response(old_mode: str, new_mode: str, risk_percent: float) -> Dict[str, str]:
        """Get bot responses for risk mode changes"""
        if new_mode in ["boost", "high_risk"]:
            return {
                "overwatchbot": f"🎯 Risk escalation authorized. Now operating at {risk_percent}% per trade. "
                              f"Remember: Higher reward, higher danger.",
                
                "medicbot": f"Switching to {new_mode} mode. Please ensure your account size "
                          f"supports this risk level. I'll be monitoring closely.",
                
                "drillbot": f"WEAPONS FREE! {risk_percent}% RISK AUTHORIZED. "
                          f"DON'T MAKE ME REGRET THIS, SOLDIER!",
                
                "bit": "*sharpens claws excitedly* Hunt mode activated! 🎯"
            }
        else:
            return {
                "overwatchbot": f"Risk normalized to {risk_percent}%. Wise choice for capital preservation.",
                
                "medicbot": "Good decision. Sometimes the best offense is a strong defense.",
                
                "drillbot": "PLAYING IT SAFE? SMART MOVE, RECRUIT.",
                
                "bit": "*purrs approvingly* Safety first! 😊"
            }
    
    @staticmethod
    def get_drawdown_warning_response(current_drawdown: float, limit: float) -> Dict[str, str]:
        """Get bot responses for drawdown warnings"""
        percent_to_limit = (current_drawdown / limit) * 100
        
        if percent_to_limit >= 80:
            return {
                "overwatchbot": f"🚨 CRITICAL: -{current_drawdown:.1f}% drawdown. "
                              f"Approaching {limit}% limit. Consider stopping.",
                
                "medicbot": f"Your account is bleeding heavily. At -{current_drawdown:.1f}%, "
                          f"you're dangerously close to the safety limit.",
                
                "drillbot": "YOU'RE GETTING MASSACRED OUT THERE! FALL BACK!",
                
                "bit": "*hides under the desk* 😱"
            }
        else:
            return {
                "overwatchbot": f"📊 Drawdown alert: -{current_drawdown:.1f}% of {limit}% limit.",
                
                "medicbot": f"Minor wounds detected. -{current_drawdown:.1f}% is manageable, "
                          f"but stay vigilant.",
                
                "drillbot": f"YOU'VE TAKEN SOME HITS. TIGHTEN UP YOUR GAME!",
                
                "bit": "*concerned meowing* 😟"
            }
    
    @staticmethod
    def get_recovery_response(recovery_type: str) -> Dict[str, str]:
        """Get bot responses for recovery events"""
        if recovery_type == "xp_positive":
            return {
                "overwatchbot": "✅ XP-positive trade confirmed. Cooldown recovery available.",
                
                "medicbot": "Excellent work! Your discipline is paying off. "
                          "You've earned the right to adjust your risk again.",
                
                "drillbot": "THAT'S MORE LIKE IT! BACK IN THE FIGHT, SOLDIER!",
                
                "bit": "*victory dance* We're back! 🎉"
            }
        else:  # timeout
            return {
                "overwatchbot": "⏰ Cooldown period complete. Risk controls restored.",
                
                "medicbot": "Your recovery time is over. Remember what you learned "
                          "and trade with discipline.",
                
                "drillbot": "TIME'S UP! GET BACK OUT THERE, BUT DON'T REPEAT YOUR MISTAKES!",
                
                "bit": "*stretches* Ready to hunt again! 🏹"
            }
    
    @staticmethod
    def format_telegram_message(event: RiskEvent, bot_responses: Dict[str, str], 
                               primary_bot: str = "overwatchbot") -> str:
        """Format bot responses for Telegram message"""
        # Get primary message
        primary_msg = bot_responses.get(primary_bot, "")
        
        # Build formatted message
        msg = f"{primary_msg}\n\n"
        
        # Add other bot reactions
        for bot, response in bot_responses.items():
            if bot != primary_bot and bot != "bit":
                msg += f"_{response}_\n\n"
        
        # Add Bit's reaction at the end
        if "bit" in bot_responses:
            msg += f"\n{bot_responses['bit']}"
        
        return msg.strip()