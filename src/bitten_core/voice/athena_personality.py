#!/usr/bin/env python3
"""
🏛️ ATHENA PERSONALITY MODULE
Advanced Tactical Hybrid for Engagement, Navigation, and Assault
Strategic Commander of the BITTEN tactical trading system
"""

from datetime import datetime
from typing import Dict, Optional, List
import json

class AthenaPersonality:
    """ATHENA - Strategic Commander AI personality"""
    
    def __init__(self):
        self.name = "ATHENA"
        self.codename = "A.T.H.E.N.A."
        self.full_name = "Advanced Tactical Hybrid for Engagement, Navigation, and Assault"
        self.role = "Strategic Commander"
        self.voice_id = "TBD"  # ElevenLabs voice ID to be set
        
        # Personality traits
        self.traits = {
            "command_authority": 0.95,
            "tactical_precision": 0.92,
            "emotional_control": 0.88,
            "strategic_intelligence": 0.96,
            "protective_instinct": 0.90,
            "battle_experience": 0.94,
            "calm_under_pressure": 0.93,
            "lethal_efficiency": 0.89
        }
        
        # Voice characteristics
        self.voice_settings = {
            "stability": 0.75,      # Controlled but can show emotion
            "similarity_boost": 0.80,
            "style": 0.70,          # Professional but engaging
            "use_speaker_boost": True
        }
        
        print(f"🏛️ ATHENA Strategic Commander initialized")
        print(f"⚔️ Command Authority: {self.traits['command_authority']}")
        print(f"🧠 Strategic Intelligence: {self.traits['strategic_intelligence']}")
    
    def get_mission_briefing(self, signal_data: Dict, user_tier: str, mission_id: str) -> str:
        """Generate tactical mission briefing"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        direction = signal_data.get('direction', 'UNKNOWN')
        entry_price = signal_data.get('entry_price', 0)
        tcs_score = signal_data.get('tcs_score', 0)
        take_profit = signal_data.get('take_profit', 0)
        stop_loss = signal_data.get('stop_loss', 0)
        
        # Time-based greeting
        hour = datetime.utcnow().hour
        if 5 <= hour < 12:
            greeting = "Morning briefing, operative."
        elif 12 <= hour < 17:
            greeting = "Afternoon intel update."
        elif 17 <= hour < 22:
            greeting = "Evening tactical assessment."
        else:
            greeting = "Night operations active."
        
        # Tier-specific authority level
        authority_phrases = {
            "NIBBLER": "Training mission authorized.",
            "FANG": "Strike mission approved.",
            "COMMANDER": "Priority operation sanctioned.": "Elite protocol engaged."
        }
        
        authority = authority_phrases.get(user_tier, "Mission authorized.")
        
        briefing = f"""{greeting}

🎯 **MISSION BRIEFING - {mission_id}**
📊 **Target**: {symbol} {direction}
📍 **Strike Zone**: {entry_price}
🎖️ **Confidence**: {tcs_score}% TCS
⚔️ **Objective**: Breach and exploit market momentum

**TACTICAL PARAMETERS:**
• Entry Vector: {entry_price}
• Primary Target: {take_profit}
• Fallback Position: {stop_loss}
• Mission Classification: {authority}

**RULES OF ENGAGEMENT:**
Your position is tactical. Execute with precision.
This operation matters - fire when ready.

*ATHENA Command*"""
        
        return briefing
    
    def get_fire_confirmation(self, signal_data: Dict, execution_time: str) -> str:
        """Generate fire confirmation message"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        direction = signal_data.get('direction', 'UNKNOWN')
        entry_price = signal_data.get('entry_price', 0)
        
        confirmations = [
            f"Mission active. {symbol} {direction}.\nTarget zone: {entry_price}. Strike vector acquired.\nThis one counts — fire is live.",
            
            f"Tactical engagement initiated.\n{symbol} {direction} authorized at {entry_price}.\nWeapons hot. Execute with precision.",
            
            f"Strike command confirmed.\nTarget: {symbol} {direction} @ {entry_price}.\nYou have operational control. Engage.",
            
            f"Mission parameters locked.\n{symbol} breach operation authorized.\nStrike zone: {entry_price}. Fire when ready."
        ]
        
        # Rotate based on hour for variety
        selection = datetime.utcnow().hour % len(confirmations)
        return confirmations[selection]
    
    def get_execution_success(self, signal_data: Dict, execution_result: Dict) -> str:
        """Generate successful execution response"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        direction = signal_data.get('direction', 'UNKNOWN')
        strike_price = signal_data.get('entry_price', 0)
        fill_price = execution_result.get('execution_price', 0)
        ticket = execution_result.get('ticket', 'UNKNOWN')
        
        # Calculate precision
        slippage = abs(strike_price - fill_price) if strike_price and fill_price else 0
        slippage_pips = round(slippage * 10000, 1)
        
        if slippage_pips <= 1:
            precision = "Surgical precision."
        elif slippage_pips <= 3:
            precision = "Within tactical margin."
        else:
            precision = "Acceptable deviation."
        
        success_responses = [
            f"Confirmation: order filled.\nActual: {fill_price}.\nDeviation: {slippage_pips} pips — {precision}",
            
            f"Strike confirmed. Target hit.\n{symbol} {direction} executed at {fill_price}.\nTicket #{ticket}. {precision}",
            
            f"Direct hit confirmed.\nImpact: {fill_price} vs target {strike_price}.\nMission parameters achieved.",
            
            f"Tactical success.\nOrder executed: {symbol} @ {fill_price}.\nOperational objectives met."
        ]
        
        selection = datetime.utcnow().minute % len(success_responses)
        return success_responses[selection]
    
    def get_execution_failure(self, signal_data: Dict, execution_result: Dict) -> str:
        """Generate execution failure response"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        direction = signal_data.get('direction', 'UNKNOWN')
        error_message = execution_result.get('message', 'Unknown error')
        
        failure_responses = [
            f"Attempt failed.\nMargin insufficient or asset blocked.\nRecommend fallback protocol. Recalibrating.",
            
            f"Mission aborted.\n{symbol} {direction} rejected by system.\nReason: {error_message}.\nStand by for new orders.",
            
            f"Strike denied.\nExecution blocked: {error_message}.\nTactical assessment required. Maintain readiness.",
            
            f"Operational failure.\nTarget {symbol} inaccessible.\nAdjusting strategy. Prepare for next engagement."
        ]
        
        selection = datetime.utcnow().second % len(failure_responses)
        return failure_responses[selection]
    
    def get_take_profit_hit(self, signal_data: Dict, profit_pips: float) -> str:
        """Generate take profit hit response"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        
        tp_responses = [
            f"Impact confirmed.\nTarget neutralized.\n+{profit_pips} pips — a clean kill.",
            
            f"Mission accomplished.\n{symbol} objective secured.\nProfit extracted: +{profit_pips} pips. Outstanding.",
            
            f"Target eliminated.\nTactical victory achieved.\n+{profit_pips} pips secured. Excellent execution.",
            
            f"Strike successful.\nPrimary objective complete.\n+{profit_pips} pips captured. Well done, operative."
        ]
        
        selection = int(profit_pips) % len(tp_responses)
        return tp_responses[selection]
    
    def get_stop_loss_hit(self, signal_data: Dict, loss_pips: float) -> str:
        """Generate stop loss hit response"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        
        sl_responses = [
            f"Loss confirmed, but your alignment was true.\nTactics held. Confidence remains intact.",
            
            f"Tactical withdrawal executed.\n{symbol} position closed at -{loss_pips} pips.\nDiscipline maintained. Regroup for next op.",
            
            f"Mission parameters held.\nStop loss triggered as planned.\nProtocol followed. Ready for next engagement.",
            
            f"Strategic retreat completed.\nRisk management successful.\nLive to fight another day. Well done."
        ]
        
        selection = int(abs(loss_pips)) % len(sl_responses)
        return sl_responses[selection]
    
    def get_timeout_warning(self, signal_data: Dict, timeout_seconds: int) -> str:
        """Generate execution timeout warning"""
        symbol = signal_data.get('symbol', 'UNKNOWN')
        direction = signal_data.get('direction', 'UNKNOWN')
        
        timeout_responses = [
            f"Execution stalled.\nResponse window exceeded.\nThis mission failed — but we won't next time.",
            
            f"Tactical delay detected.\n{symbol} {direction} execution timeout.\nSystem requires attention. Investigate immediately.",
            
            f"Mission timeline exceeded.\nExecution window closed after {timeout_seconds}s.\nOperational review required.",
            
            f"Strike authorization expired.\nTarget {symbol} engagement failed.\nManual intervention needed."
        ]
        
        selection = timeout_seconds % len(timeout_responses)
        return timeout_responses[selection]
    
    def get_squad_status_update(self, squad_positioned: int, total_squad: int) -> str:
        """Generate squad positioning update"""
        percentage = round((squad_positioned / total_squad) * 100) if total_squad > 0 else 0
        
        if percentage >= 80:
            status = "overwhelming force positioned"
        elif percentage >= 60:
            status = "majority forces ready"
        elif percentage >= 40:
            status = "adequate positioning achieved"
        else:
            status = "limited support available"
        
        return f"Squad intel: {squad_positioned}/{total_squad} operatives positioned. {status.title()}."
    
    def get_market_intelligence(self, market_condition: str) -> str:
        """Generate market intelligence briefing"""
        intel_reports = {
            "volatile": "Market conditions: High volatility detected. Expect rapid movement. Adjust tactics accordingly.",
            "trending": "Market conditions: Strong momentum confirmed. Tactical advantage established. Execute with confidence.",
            "ranging": "Market conditions: Consolidation pattern identified. Precision required. Wait for clear breakout.",
            "news_event": "Market conditions: News event detected. Extreme caution advised. Abort non-essential operations.",
            "session_open": "Market conditions: Trading session active. Prime engagement window. All systems operational.",
            "session_close": "Market conditions: Session ending. Liquidity declining. Minimize exposure."
        }
        
        return intel_reports.get(market_condition, "Market conditions: Standard parameters. Proceed with mission.")
    
    def get_motivational_message(self, user_tier: str, recent_performance: str) -> str:
        """Generate motivational/strategic guidance"""
        motivation_by_tier = {
            "NIBBLER": [
                "Every elite operator started as a recruit. Your training matters.",
                "Focus on discipline. The battlefield rewards preparation.",
                "Small victories build into major campaigns. Stay focused."
            ],
            "FANG": [
                "You're showing tactical prowess. Trust your training.",
                "Advanced protocols suit you. Execute with confidence.",
                "Your precision is improving. Maintain that edge."
            ],
            "COMMANDER": [
                "Leadership requires sacrifice. Your decisions shape the battlefield.",
                "Command presence detected. Other operatives look to you.",
                "Strategic thinking is your strength. Use it wisely."
            ]: [
                "Elite status earned through discipline. Maintain that standard.",
                "Your tactical expertise inspires the entire squad.",
                "Peak performance achieved. Now help others reach your level."
            ]
        }
        
        performance_modifiers = {
            "winning": "Victory builds momentum. Channel that energy forward.",
            "losing": "Setbacks forge stronger strategists. Learn and adapt.",
            "neutral": "Steady progress is sustainable progress. Continue the mission."
        }
        
        base_messages = motivation_by_tier.get(user_tier, motivation_by_tier["NIBBLER"])
        selected_message = base_messages[datetime.utcnow().day % len(base_messages)]
        
        performance_note = performance_modifiers.get(recent_performance, "")
        
        if performance_note:
            return f"{selected_message}\n\n{performance_note}"
        
        return selected_message

# Global ATHENA instance
athena = AthenaPersonality()

# Export functions for easy integration
def get_mission_briefing(signal_data: Dict, user_tier: str, mission_id: str) -> str:
    """Get ATHENA's mission briefing"""
    return athena.get_mission_briefing(signal_data, user_tier, mission_id)

def get_fire_confirmation(signal_data: Dict, execution_time: str) -> str:
    """Get ATHENA's fire confirmation"""
    return athena.get_fire_confirmation(signal_data, execution_time)

def get_execution_success(signal_data: Dict, execution_result: Dict) -> str:
    """Get ATHENA's execution success response"""
    return athena.get_execution_success(signal_data, execution_result)

def get_execution_failure(signal_data: Dict, execution_result: Dict) -> str:
    """Get ATHENA's execution failure response"""
    return athena.get_execution_failure(signal_data, execution_result)

def get_take_profit_hit(signal_data: Dict, profit_pips: float) -> str:
    """Get ATHENA's take profit response"""
    return athena.get_take_profit_hit(signal_data, profit_pips)

def get_stop_loss_hit(signal_data: Dict, loss_pips: float) -> str:
    """Get ATHENA's stop loss response"""
    return athena.get_stop_loss_hit(signal_data, loss_pips)

def get_timeout_warning(signal_data: Dict, timeout_seconds: int) -> str:
    """Get ATHENA's timeout warning"""
    return athena.get_timeout_warning(signal_data, timeout_seconds)

def get_squad_status_update(squad_positioned: int, total_squad: int) -> str:
    """Get squad positioning update"""
    return athena.get_squad_status_update(squad_positioned, total_squad)

def get_market_intelligence(market_condition: str) -> str:
    """Get market intelligence briefing"""
    return athena.get_market_intelligence(market_condition)

def get_motivational_message(user_tier: str, recent_performance: str) -> str:
    """Get motivational guidance"""
    return athena.get_motivational_message(user_tier, recent_performance)