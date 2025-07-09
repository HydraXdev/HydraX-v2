# signal_display.py
# BITTEN Signal Display System - Visual Card Generation

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from .mission_briefing_generator import MissionBriefing, MissionType, UrgencyLevel

class SignalDisplay:
    """
    Creates visual signal cards for Telegram display
    Multiple styles for different signal types
    """
    
    def __init__(self):
        # Visual elements
        self.bars = {
            'full': '█',
            'three_quarter': '▓',
            'half': '▒',
            'quarter': '░',
            'empty': '·'
        }
        
        # TCS visual representations
        self.tcs_bars = {
            range(0, 20): '░░░░░',
            range(20, 40): '█░░░░',
            range(40, 60): '██░░░',
            range(60, 70): '███░░',
            range(70, 80): '████░',
            range(80, 90): '████▓',
            range(90, 95): '█████',
            range(95, 101): '🔥🔥🔥🔥🔥'
        }
    
    def get_bitten_header(self) -> str:
        """Get B.I.T.T.E.N. branded header for signals"""
        return "🤖 **B.I.T.T.E.N.** | Bot-Integrated Tactical Trading Engine"
    
    def create_arcade_signal_card(self, signal: Dict) -> str:
        """Create tactical arcade signal display card - SITREP style"""
        
        # Calculate expiry countdown
        time_remaining = signal.get('time_remaining', 600)  # seconds
        expiry_bar = self._create_expiry_bar(time_remaining)
        active_traders = signal.get('active_traders', 0)
        
        # Style 1: Tactical SITREP
        sitrep = f"""
⚡ **TACTICAL SITREP** - ARCADE SCALP ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 **OP: {signal['display_type']}**
📍 **AO:** {signal['symbol']} | **VECTOR:** {signal['direction'].upper()}
🎯 **ENTRY:** {signal['entry_price']:.5f}
💥 **OBJECTIVE:** +{signal['expected_pips']} PIPS
⚔️ **RISK:** {signal.get('risk_pips', 3)} PIPS

📊 **INTEL CONFIDENCE:** {signal['tcs_score']}% {self._get_tcs_emoji(signal['tcs_score'])}
{self._get_tcs_visual(signal['tcs_score'])}

⏱️ **OP WINDOW:** {expiry_bar}
👥 **SQUAD ENGAGED:** {active_traders} OPERATORS

[🔫 **ENGAGE TARGET**] [📋 **VIEW INTEL**]
"""
        
        # Add Grok AI sentiment if available
        if signal.get('grok_sentiment'):
            sitrep = self.add_grok_ai_sentiment(sitrep, signal['grok_sentiment'])
        
        # Style 2: Compact Tactical Card
        compact = f"""
╔═══════════════════════════╗
║ 🎮 ARCADE SCALP DETECTED  ║
║ {signal['symbol']} │ {signal['direction'].upper():>4} │ TCS: {signal['tcs_score']}% {self._get_tcs_emoji(signal['tcs_score'])} ║
║ Entry: {signal['entry_price']:.5f}          ║
║ Target: +{signal['expected_pips']} pips          ║
║ {self._get_tcs_visual(signal['tcs_score'])}            ║
╚═══════════════════════════╝
        [🔫 FIRE]"""
        
        # Style 2: Detailed Card  
        detailed = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ {signal['visual_emoji']} {signal['display_type']}
┃ ───────────────────────────
┃ 📍 {signal['symbol']} - {signal['direction'].upper()}
┃ 💰 Entry: {signal['entry_price']:.5f}
┃ 🎯 Target: {signal['take_profit']:.5f} (+{signal['expected_pips']}p)
┃ 🛡️ Stop: {signal['stop_loss']:.5f}
┃ ⏱️ Duration: ~{signal['expected_duration']}min
┃ 
┃ TCS: {self._get_tcs_bar(signal['tcs_score'])}
┃      {signal['tcs_score']}% Confidence
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        [🔫 FIRE NOW]"""
        
        # Style 3: Minimal
        minimal = f"""
{signal['visual_emoji']} **{signal['display_type']}** - {signal['symbol']}
→ {signal['direction'].upper()} @ {signal['entry_price']:.5f}
→ +{signal['expected_pips']} pips | TCS: {signal['tcs_score']}% {self._get_tcs_emoji(signal['tcs_score'])}
[🔫 FIRE]"""

        # Style 4: Gaming Style
        gaming = f"""
╭─────────────────────────────╮
│ 🎮 NEW SIGNAL DETECTED!     │
│                             │
│ {signal['visual_emoji']} {signal['display_type']:<22}│
│ ═══════════════════════════ │
│ Pair: {signal['symbol']:<10} Dir: {signal['direction'].upper():<4}│
│ Power: {self._get_power_meter(signal['tcs_score'])}│
│ Reward: +{signal['expected_pips']} pips            │
│                             │
│     Press [🔫] to FIRE      │
╰─────────────────────────────╯"""
        
        # Return the new SITREP style
        return sitrep
    
    def create_sniper_signal_card(self, signal: Dict) -> str:
        """Create elite sniper signal card - Military briefing style"""
        
        # Calculate expiry countdown
        time_remaining = signal.get('time_remaining', 600)  # seconds
        expiry_bar = self._create_expiry_bar(time_remaining)
        active_snipers = signal.get('active_traders', 0)
        avg_tcs = signal.get('squad_avg_tcs', 85)
        
        # Style 1: Elite Sniper Briefing
        sniper_brief = f"""
🎯 **[CLASSIFIED]** SNIPER ENGAGEMENT 🎯
══════════════════════════════════════

**MISSION BRIEF:**
• **TARGET:** {signal['symbol']} - {signal['direction'].upper()}
• **ENTRY VECTOR:** {signal['entry_price']:.5f}
• **OBJECTIVE:** +{signal['expected_pips']} PIPS CONFIRMED
• **COLLATERAL:** {signal.get('risk_pips', 5)} PIPS MAX
• **R:R RATIO:** 1:{signal['expected_pips'] // signal.get('risk_pips', 5)}

**TACTICAL INTEL:**
• **CONFIDENCE:** {signal['tcs_score']}% [ELITE]
• **OP WINDOW:** {expiry_bar}
• **SNIPERS ENGAGED:** {active_snipers} 🎯
• **SQUAD AVG TCS:** {avg_tcs}%

⚡ **FANG+ CLEARANCE REQUIRED** ⚡

[🎯 **TAKE THE SHOT**] [🔍 **RECON**]
"""
        
        # Add Grok AI sentiment if available
        if signal.get('grok_sentiment'):
            sniper_brief = self.add_grok_ai_sentiment(sniper_brief, signal['grok_sentiment'])
        
        # Style 2: Classified
        classified = f"""
╔═══════════════════════════════╗
║  🎯 SNIPER SHOT DETECTED! 🎯  ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║     [CLASSIFIED SETUP]        ║
║                               ║
║  Confidence: {signal['tcs_score']}%              ║
║  Expected: {signal['expected_pips']} pips           ║
║  Duration: <{signal['expected_duration']} min        ║
║                               ║
║  ⚡ FANG+ EXCLUSIVE ⚡        ║
╚═══════════════════════════════╝
         [🔫 EXECUTE]"""
        
        # Style 2: Tactical
        tactical = f"""
┌─────────────────────────────┐
│ ▓▓▓ TACTICAL ALERT ▓▓▓     │
│                             │
│ 🎯 SNIPER OPPORTUNITY       │
│ -------------------------   │
│ Classification: ELITE       │
│ Confidence: ████████ {signal['tcs_score']}%   │
│ Profit Zone: {signal['expected_pips']}+ pips     │
│ Window: CLOSING SOON        │
│                             │
│ 🔒 FANG+ ACCESS REQUIRED    │
└─────────────────────────────┘
      [🔫 ENGAGE TARGET]"""
        
        # Style 3: Matrix Style
        matrix = f"""
╔═[SNIPER.MATRIX.v2]═════════╗
║ > Target acquired...        ║
║ > Analyzing patterns...     ║
║ > Confidence: {signal['tcs_score']}%          ║
║ > Profit probability: HIGH  ║
║ > Expected yield: {signal['expected_pips']} pips ║
║ > Time window: {signal['expected_duration']} min    ║
║ > Access level: FANG+       ║
║ > Status: READY TO FIRE     ║
╚════════════════════════════╝
    [🎯 INITIATE SEQUENCE]"""
        
        return sniper_brief
    
    def create_midnight_hammer_card(self) -> str:
        """Create epic Midnight Hammer event card"""
        
        return """
╔═══════════════════════════════════╗
║ 🔨🔨🔨 MIDNIGHT HAMMER EVENT 🔨🔨🔨║
║ ═════════════════════════════════ ║
║      💥 LEGENDARY SETUP! 💥       ║
║                                   ║
║   Community Power: ████████ 87%   ║
║   TCS Score: 🔥🔥🔥🔥🔥 96%      ║
║   Risk: 5% = 50-100 pips         ║
║   Unity Bonus: +15% XP            ║
║                                   ║
║   ⚡ 147 WARRIORS READY ⚡        ║
║   ⏰ WINDOW CLOSES IN 4:32 ⏰     ║
╚═══════════════════════════════════╝
      [🔨 JOIN THE HAMMER!]"""
    
    def create_chaingun_sequence_card(self, shot_number: int, results: List[bool]) -> str:
        """Create CHAINGUN sequence display"""
        
        # Visual representation of shots
        shot_display = ""
        for i in range(4):
            if i < len(results):
                shot_display += "✅ " if results[i] else "❌ "
            elif i == shot_number - 1:
                shot_display += "🎯 "
            else:
                shot_display += "⚪ "
        
        risks = ["2%", "4%", "8%", "16%"]
        current_risk = risks[shot_number - 1]
        
        return f"""
╔═══════════════════════════════╗
║ 🔥 CHAINGUN SEQUENCE ACTIVE 🔥║
║ ═════════════════════════════ ║
║  Shot Progress: {shot_display}      ║
║                               ║
║  Current Shot: #{shot_number}          ║
║  Risk Level: {current_risk}            ║
║  Total Profit: +{sum(results)*15}%         ║
║                               ║
║  [🪂 PARACHUTE] [🔫 CONTINUE] ║
╚═══════════════════════════════╝"""
    
    def create_position_summary_card(self, positions: List[Dict]) -> str:
        """Create tactical active positions summary"""
        
        if not positions:
            return """
⚔️ **BATTLEFIELD STATUS** ⚔️
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **NO ACTIVE POSITIONS**

• All clear on the battlefield
• Ammunition ready: 6/6 shots
• Awaiting next engagement

[🎯 **FIND TARGET**]
"""
        
        position_lines = []
        total_pnl = 0
        
        for pos in positions[:5]:  # Show max 5
            pnl = pos.get('pnl', 0)
            total_pnl += pnl
            emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            direction_arrow = "↗️" if pos['direction'] == 'buy' else "↘️"
            
            # Calculate time in position
            time_in = pos.get('time_in_minutes', 0)
            time_str = f"{time_in}m" if time_in < 60 else f"{time_in//60}h{time_in%60}m"
            
            position_lines.append(
                f"{emoji} **{pos['symbol']}** {direction_arrow} {pnl:+.0f}p • {time_str}"
            )
        
        # More positions indicator
        if len(positions) > 5:
            position_lines.append(f"   ...and {len(positions)-5} more positions")
        
        # Status emoji based on total P/L
        status_emoji = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
        
        return f"""
⚔️ **BATTLEFIELD STATUS** ⚔️
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **ACTIVE POSITIONS: {len(positions)}**

{chr(10).join(position_lines)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
{status_emoji} **TOTAL P/L: {total_pnl:+.0f} PIPS**

[📊 **DETAILS**] [✂️ **MANAGE**]
"""
    
    def create_daily_summary_card(self, stats: Dict) -> str:
        """Create tactical daily battle report"""
        
        # Calculate performance metrics
        shots_fired = stats.get('trades', 0)
        shots_remaining = 6 - shots_fired
        direct_hits = stats.get('wins', 0)
        win_rate = stats.get('win_rate', 0)
        total_pips = stats.get('pips', 0)
        xp_earned = stats.get('xp', 0)
        
        # Rank progress visualization
        rank_progress = stats.get('rank_progress', 82)
        progress_bar = self._create_progress_bar(rank_progress)
        
        # Performance rating
        if win_rate >= 80:
            performance = "🔥 ELITE PERFORMANCE"
        elif win_rate >= 65:
            performance = "⚡ SOLID EXECUTION"
        elif win_rate >= 50:
            performance = "📊 STANDARD OPS"
        else:
            performance = "⚠️ NEEDS IMPROVEMENT"
        
        # Badge progress
        current_badge = stats.get('current_badge', '🥉 RECRUIT')
        next_badge = stats.get('next_badge', '🥈 WARRIOR')
        xp_to_next = stats.get('xp_to_next', 150)
        
        return f"""
🎖️ **DAILY BATTLE REPORT** 🎖️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **COMBAT STATISTICS**
• **Shots Fired:** {shots_fired}/6 ({shots_remaining} remaining)
• **Direct Hits:** {direct_hits} ({win_rate}% accuracy)
• **Total Pips:** {total_pips:+.0f}
• **XP Earned:** +{xp_earned}

🎯 **PERFORMANCE RATING**
{performance}

🏅 **RANK PROGRESSION**
• **Current:** {current_badge}
• **Progress:** {progress_bar} {rank_progress}%
• **Next:** {next_badge} (need {xp_to_next} XP)

📈 **DAILY OBJECTIVES**
{self._get_daily_objectives(stats)}

[📊 **FULL STATS**] [🏆 **LEADERBOARD**]
"""
    
    def _create_progress_bar(self, percentage: int) -> str:
        """Create visual progress bar"""
        filled = int(percentage / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty
    
    def _get_daily_objectives(self, stats: Dict) -> str:
        """Get daily mission objectives"""
        objectives = []
        
        # Win rate objective
        if stats.get('win_rate', 0) >= 70:
            objectives.append("✅ Maintain 70%+ accuracy")
        else:
            objectives.append("⬜ Achieve 70%+ accuracy")
        
        # Trading volume objective
        if stats.get('trades', 0) >= 4:
            objectives.append("✅ Execute 4+ trades")
        else:
            objectives.append("⬜ Execute 4+ trades")
        
        # Profit objective
        if stats.get('pips', 0) >= 50:
            objectives.append("✅ Capture 50+ pips")
        else:
            objectives.append("⬜ Capture 50+ pips")
        
        return "\n".join(f"• {obj}" for obj in objectives)
    
    def _get_tcs_visual(self, tcs: int) -> str:
        """Get visual representation of TCS with emoji indicators and color coding"""
        if tcs >= 85:
            # Diamond level - SNIPER grade
            return "💎 ████████░ SNIPER GRADE"
        elif tcs >= 77:
            # Star level - PRECISION grade  
            return "⭐ ███████░░ PRECISION"
        elif tcs >= 70:
            # Crossbones level - RISKY grade
            return "☠️ █████░░░░ RISKY"
        else:
            # Standard level - below threshold
            return "⚠️ ███░░░░░░ STANDARD"
    
    def _get_tcs_bar(self, tcs: int) -> str:
        """Get TCS as progress bar"""
        filled = int(tcs / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty
    
    def _get_power_meter(self, tcs: int) -> str:
        """Get power meter visualization"""
        if tcs >= 90:
            return "⚡⚡⚡⚡⚡"
        elif tcs >= 80:
            return "⚡⚡⚡⚡·"
        elif tcs >= 70:
            return "⚡⚡⚡··"
        elif tcs >= 60:
            return "⚡⚡···"
        else:
            return "⚡····"
    
    def _create_expiry_bar(self, seconds_remaining: int) -> str:
        """Create visual countdown bar for signal expiry"""
        if seconds_remaining <= 0:
            return "⬛⬛⬛⬛⬛ EXPIRED"
        
        total_seconds = 600  # 10 minutes max
        percent = (seconds_remaining / total_seconds) * 100
        
        if percent > 80:
            return "🟩🟩🟩🟩🟩 HOT"
        elif percent > 60:
            return "🟩🟩🟩🟩⬜ ACTIVE"
        elif percent > 40:
            return "🟨🟨🟨⬜⬜ FADING"
        elif percent > 20:
            return "🟧🟧⬜⬜⬜ CLOSING"
        else:
            return "🟥⬜⬜⬜⬜ CRITICAL"
    
    def create_shortened_telegram_alert(self, signal: Dict, briefing: MissionBriefing) -> str:
        """Create shortened alert for Telegram with essential info only"""
        
        # Determine signal emoji and type
        if briefing.mission_type.value == 'sniper_shot':
            emoji = "🎯"
            type_str = "SNIPER"
        elif briefing.mission_type.value == 'midnight_hammer':
            emoji = "🔨"
            type_str = "HAMMER"
        else:
            emoji = "⚡"
            type_str = "SCALP"
        
        # Build compact alert
        alert = f"{emoji} **{briefing.callsign}** | {type_str}\n"
        alert += f"━━━━━━━━━━━━━━━━━━━━━\n"
        alert += f"📍 {briefing.symbol} {briefing.direction}\n"
        alert += f"💯 TCS: {briefing.tcs_score}% {self._get_tcs_emoji(briefing.tcs_score)} | ⏱️ {self._format_time_remaining(briefing.time_remaining)}\n"
        alert += f"👥 {briefing.active_operators} traders active"
        
        return alert
    
    def create_tactical_signal_variants(self, signal: Dict) -> Dict[str, str]:
        """Create multiple tactical display variants for A/B testing"""
        
        # Variant 1: Combat Operations Brief
        combat_ops = f"""
⚔️ **COMBAT OPS BRIEF** ⚔️
━━━━━━━━━━━━━━━━━━━━━━━
**CALLSIGN:** {signal.get('callsign', 'ALPHA-1')}
**TARGET:** {signal['symbol']} | {signal['direction'].upper()}
**ENTRY POINT:** {signal['entry_price']:.5f}
**EXTRACTION:** +{signal['expected_pips']} PIPS

**RISK ASSESSMENT:**
• Exposure: {signal.get('risk_pips', 3)} pips
• Reward Ratio: 1:{signal['expected_pips'] // signal.get('risk_pips', 3)}
• Intel Confidence: {signal['tcs_score']}%

**SQUAD STATUS:**
• {signal.get('active_traders', 0)} operators engaged
• Average TCS: {signal.get('squad_avg_tcs', 70)}%

{self._create_expiry_bar(signal.get('time_remaining', 600))}

[🎯 **EXECUTE**] [📊 **INTEL**]
"""
        
        # Variant 2: Strike Team Alert
        strike_team = f"""
🚨 **STRIKE TEAM ALERT** 🚨
{'🎯' if signal.get('type') == 'sniper' else '🎮'} {signal['display_type']}
═══════════════════════════
📍 **AO:** {signal['symbol']}
🎯 **Vector:** {signal['direction'].upper()} @ {signal['entry_price']:.5f}
💥 **Target:** +{signal['expected_pips']} pips ({signal.get('risk_pips', 3)} risk)
⚡ **TCS:** {signal['tcs_score']}% {self._get_tcs_emoji(signal['tcs_score'])} - {self._get_tcs_explanation(signal['tcs_score'])}

👥 **{signal.get('active_traders', 0)}** friendlies in position
⏱️ **Window:** {self._create_expiry_bar(signal.get('time_remaining', 600))}

[🔫 **ENGAGE**]
"""
        
        # Variant 3: Tactical HUD
        tactical_hud = f"""
┌─ TACTICAL HUD ─────────────┐
│ {'🎯 SNIPER' if signal.get('type') == 'sniper' else '🎮 ARCADE'} │ {signal['symbol']} │ {signal['direction'].upper()}
├────────────────────────────┤
│ ENTRY: {signal['entry_price']:.5f}
│ TGT: +{signal['expected_pips']}p │ RISK: {signal.get('risk_pips', 3)}p
│ R:R: 1:{signal['expected_pips'] // signal.get('risk_pips', 3)} │ TCS: {signal['tcs_score']}% {self._get_tcs_emoji(signal['tcs_score'])}
├────────────────────────────┤
│ SQUAD: {signal.get('active_traders', 0)} │ AVG: {signal.get('squad_avg_tcs', 70)}%
│ {self._create_expiry_bar(signal.get('time_remaining', 600))}
└────────────────────────────┘
  [FIRE] [ABORT] [INTEL]
"""
        
        return {
            'combat_ops': combat_ops,
            'strike_team': strike_team,
            'tactical_hud': tactical_hud
        }
    
    def create_mission_briefing_card(self, briefing: MissionBriefing) -> str:
        """Create formatted display card from mission briefing"""
        
        # Choose style based on mission type
        if briefing.mission_type == MissionType.ARCADE_SCALP:
            return self._create_arcade_briefing_card(briefing)
        elif briefing.mission_type == MissionType.SNIPER_SHOT:
            return self._create_sniper_briefing_card(briefing)
        elif briefing.mission_type == MissionType.MIDNIGHT_HAMMER:
            return self._create_hammer_briefing_card(briefing)
        else:
            return self._create_default_briefing_card(briefing)
    
    def _create_arcade_briefing_card(self, briefing: MissionBriefing) -> str:
        """Create arcade-style mission briefing card"""
        urgency_bar = self._create_urgency_bar(briefing.urgency)
        confidence_visual = self._get_tcs_visual(briefing.tcs_score)
        
        return f"""
⚡ **TACTICAL MISSION BRIEFING** ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 **OPERATION: {briefing.callsign}**
📍 **TARGET:** {briefing.symbol} | **VECTOR:** {briefing.direction}
🎯 **ENTRY:** {briefing.entry_price:.5f}
💥 **OBJECTIVE:** +{briefing.reward_pips} PIPS
⚔️ **RISK:** {briefing.risk_pips} PIPS | **R:R:** {briefing.risk_reward_ratio}

📊 **INTEL CONFIDENCE:** {briefing.tcs_score}%
{confidence_visual}

⏱️ **URGENCY:** {urgency_bar}
👥 **SQUAD SIZE:** {briefing.active_operators} OPERATORS
📈 **SQUAD SUCCESS RATE:** {briefing.success_rate:.0%}

🔍 **MARKET INTEL:**
{self._format_market_intel(briefing.market_intel)}

⚠️ **RISK WARNINGS:**
{self._format_risk_warnings(briefing.risk_warnings)}

[🔫 **EXECUTE MISSION**] [📊 **VIEW FULL BRIEF**]
"""
    
    def _create_sniper_briefing_card(self, briefing: MissionBriefing) -> str:
        """Create elite sniper mission briefing card"""
        urgency_bar = self._create_urgency_bar(briefing.urgency)
        
        return f"""
🎯 **[CLASSIFIED] SNIPER MISSION BRIEF** 🎯
══════════════════════════════════════════

**CODENAME:** {briefing.callsign}
**CLEARANCE:** {briefing.required_tier} ONLY

**TARGET ACQUISITION:**
• **ASSET:** {briefing.symbol}
• **VECTOR:** {briefing.direction}
• **ENTRY:** {briefing.entry_price:.5f}
• **OBJECTIVE:** +{briefing.reward_pips} PIPS
• **COLLATERAL:** {briefing.risk_pips} PIPS MAX
• **EFFICIENCY:** 1:{briefing.risk_reward_ratio}

**TACTICAL ASSESSMENT:**
• **CONFIDENCE:** {briefing.tcs_score}% {self._get_tcs_emoji(briefing.tcs_score)} [{self._get_tcs_grade(briefing.tcs_score)}]
• **MARKET CONDITIONS:** {briefing.market_conditions['volatility']}
• **TREND ALIGNMENT:** {briefing.market_conditions['trend']}
• **URGENCY:** {urgency_bar}

**SQUAD METRICS:**
• **ACTIVE SNIPERS:** {briefing.active_operators} 🎯
• **AVG CONFIDENCE:** {briefing.squad_avg_tcs:.0f}%
• **SUCCESS RATE:** {briefing.success_rate:.0%}

⚡ **{briefing.required_tier} CLEARANCE VERIFIED** ⚡

[🎯 **TAKE THE SHOT**] [🔍 **ADVANCED RECON**]
"""
    
    def _create_hammer_briefing_card(self, briefing: MissionBriefing) -> str:
        """Create midnight hammer event briefing card"""
        participation_bar = self._create_progress_bar(briefing.active_operators, 100)
        
        return f"""
╔═══════════════════════════════════════════╗
║ 🔨🔨🔨 MIDNIGHT HAMMER BRIEFING 🔨🔨🔨    ║
║ ═════════════════════════════════════════ ║
║      💥 COMMUNITY STRIKE EVENT! 💥         ║
║                                             ║
║ **TARGET:** {briefing.symbol} {briefing.direction}                      ║
║ **ENTRY:** {briefing.entry_price:.5f}                         ║
║ **OBJECTIVE:** +{briefing.reward_pips} PIPS                  ║
║                                             ║
║ **COMMUNITY POWER:**                        ║
║ {participation_bar} {briefing.active_operators}%              ║
║                                             ║
║ **AVG CONFIDENCE:** {briefing.squad_avg_tcs:.0f}%                 ║
║ **UNITY BONUS:** +15% XP                    ║
║                                             ║
║ ⚡ {briefing.active_operators} WARRIORS READY ⚡              ║
║ ⏰ WINDOW CLOSES IN {self._format_time_remaining(briefing.time_remaining)} ⏰     ║
╚═══════════════════════════════════════════╝
      [🔨 JOIN THE HAMMER!]
"""
    
    def _create_default_briefing_card(self, briefing: MissionBriefing) -> str:
        """Create default mission briefing card"""
        return f"""
📋 **MISSION BRIEFING**
━━━━━━━━━━━━━━━━━━━━━━
**Operation:** {briefing.callsign}
**Target:** {briefing.symbol} {briefing.direction}
**Entry:** {briefing.entry_price:.5f}
**Profit Target:** +{briefing.reward_pips} pips
**Risk:** {briefing.risk_pips} pips
**Confidence:** {briefing.tcs_score}%
**Time Remaining:** {self._format_time_remaining(briefing.time_remaining)}

[📊 VIEW DETAILS]
"""
    
    def _create_urgency_bar(self, urgency: UrgencyLevel) -> str:
        """Create urgency indicator bar"""
        if urgency == UrgencyLevel.CRITICAL:
            return "🟥🟥🟥🟥🟥 CRITICAL"
        elif urgency == UrgencyLevel.HIGH:
            return "🟧🟧🟧🟧⬜ HIGH"
        elif urgency == UrgencyLevel.MEDIUM:
            return "🟨🟨🟨⬜⬜ MEDIUM"
        else:
            return "🟩🟩⬜⬜⬜ LOW"
    
    def _format_market_intel(self, intel_points: List[str]) -> str:
        """Format market intelligence points"""
        if not intel_points:
            return "• No additional intel available"
        return "\n".join(f"• {point}" for point in intel_points[:3])  # Max 3 points
    
    def _format_risk_warnings(self, warnings: List[str]) -> str:
        """Format risk warnings"""
        if not warnings:
            return "• Standard risk parameters apply"
        return "\n".join(f"• {warning}" for warning in warnings[:3])  # Max 3 warnings
    
    def _format_time_remaining(self, seconds: int) -> str:
        """Format time remaining"""
        if seconds <= 0:
            return "EXPIRED"
        elif seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _get_tcs_emoji(self, tcs: int) -> str:
        """Get TCS emoji indicator based on level"""
        if tcs >= 85:
            return "💎"  # Diamond for 85+ TCS (SNIPER)
        elif tcs >= 77:
            return "⭐"  # Star for 77-84 TCS (PRECISION)
        elif tcs >= 70:
            return "☠️"  # Crossbones for 70-76 TCS (RISKY)
        else:
            return "⚠️"  # Warning for below 70 TCS
    
    def _get_tcs_explanation(self, tcs: int) -> str:
        """Get brief TCS explanation text"""
        if tcs >= 85:
            return "Elite confidence - Maximum precision expected"
        elif tcs >= 77:
            return "High confidence - Strong signal quality"
        elif tcs >= 70:
            return "Moderate confidence - Proceed with caution"
        else:
            return "Low confidence - Higher risk trade"
    
    def format_signal(self, signal: Dict) -> str:
        """Format signal with visual TCS hierarchy"""
        tcs = signal.get('tcs_score', 0)
        emoji = self._get_tcs_emoji(tcs)
        explanation = self._get_tcs_explanation(tcs)
        
        # Color-coded TCS display with emoji
        tcs_display = f"{emoji} **TCS: {tcs}%** - {explanation}"
        
        # Visual bar representation
        visual_bar = self._get_tcs_visual(tcs)
        
        return f"""
**Signal Analysis:**
{tcs_display}
{visual_bar}
"""
    
    def _get_tcs_grade(self, tcs: int) -> str:
        """Get TCS grade label"""
        if tcs >= 85:
            return "SNIPER GRADE"
        elif tcs >= 77:
            return "PRECISION GRADE"
        elif tcs >= 70:
            return "RISKY GRADE"
        else:
            return "STANDARD GRADE"
    
    def add_grok_ai_sentiment(self, signal_text: str, grok_data: Dict) -> str:
        """Add Grok AI sentiment analysis to signal display"""
        if not grok_data:
            return signal_text
        
        # Extract sentiment scores
        x_momentum = grok_data.get('x_momentum', 0)
        whale_activity = grok_data.get('whale_activity', 0)
        retail_fomo = grok_data.get('retail_fomo', 0)
        smart_money = grok_data.get('smart_money_flow', 0)
        
        # Create Grok AI section
        grok_section = f"""
🤖 **GROK AI SENTIMENT ANALYSIS** 🤖
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 X Momentum: {x_momentum:+.0f} {"🔥" if x_momentum > 50 else "❄️" if x_momentum < -50 else "➡️"}
🐋 Whale Activity: {whale_activity:+.0f} {"📈" if whale_activity > 30 else "📉" if whale_activity < -30 else "➡️"}
🚀 Retail FOMO: {retail_fomo:+.0f} {"⚠️" if retail_fomo > 70 else "✅" if retail_fomo < -30 else "➡️"}
💎 Smart Money Flow: {smart_money:+.0f} {"💰" if smart_money > 40 else "🚫" if smart_money < -40 else "➡️"}

🎯 **Powered by Grok AI** - Real-time X sentiment
"""
        
        # Find insertion point (after TCS section)
        lines = signal_text.split('\n')
        insert_index = -1
        
        for i, line in enumerate(lines):
            if 'INTEL CONFIDENCE' in line or 'TCS' in line:
                # Find the end of TCS visual section
                for j in range(i+1, min(i+5, len(lines))):
                    if lines[j].strip() == '' or '⏱️' in lines[j]:
                        insert_index = j
                        break
                break
        
        if insert_index > 0:
            lines.insert(insert_index, grok_section)
            return '\n'.join(lines)
        else:
            # Default: insert before buttons
            button_index = -1
            for i, line in enumerate(lines):
                if '[' in line and ']' in line:
                    button_index = i
                    break
            
            if button_index > 0:
                lines.insert(button_index - 1, grok_section)
                return '\n'.join(lines)
            else:
                return signal_text + '\n' + grok_section

# Test signal displays
if __name__ == "__main__":
    def test_displays():
        display = SignalDisplay()
    
    # Test arcade signal
    arcade_signal = {
        'visual_emoji': '🚀',
        'display_type': 'ROCKET RIDE',
        'symbol': 'GBPUSD',
        'direction': 'buy',
        'entry_price': 1.27650,
        'stop_loss': 1.27450,
        'take_profit': 1.27950,
        'tcs_score': 87,
        'expected_pips': 30,
        'expected_duration': 45
    }
    
    print("=== ARCADE SIGNAL ===")
    print(display.create_arcade_signal_card(arcade_signal))
    
    # Test sniper signal
    sniper_signal = {
        'tcs_score': 91,
        'expected_pips': 45,
        'expected_duration': 120
    }
    
    print("\n=== SNIPER SIGNAL ===")
    print(display.create_sniper_signal_card(sniper_signal))
    
    # Test midnight hammer
    print("\n=== MIDNIGHT HAMMER ===")
    print(display.create_midnight_hammer_card())
    
    # Test chaingun
    print("\n=== CHAINGUN SEQUENCE ===")
    print(display.create_chaingun_sequence_card(2, [True]))
    
    # Test positions
    positions = [
        {'symbol': 'GBPUSD', 'direction': 'buy', 'pnl': 23},
        {'symbol': 'EURUSD', 'direction': 'sell', 'pnl': -8},
        {'symbol': 'USDJPY', 'direction': 'buy', 'pnl': 15}
    ]
    
    print("\n=== POSITION SUMMARY ===")
    print(display.create_position_summary_card(positions))
    
    # Test daily summary
    stats = {
        'trades': 4,
        'wins': 3,
        'win_rate': 75,
        'pips': 47,
        'xp': 120
    }
    
    print("\n=== DAILY SUMMARY ===")
    print(display.create_daily_summary_card(stats))
    
    test_displays()