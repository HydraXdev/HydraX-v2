#!/usr/bin/env python3
"""
Test tactical signal displays locally
"""

from datetime import datetime
import random

class SignalDisplay:
    """Local copy for testing"""
    
    def _get_tcs_visual(self, tcs: int) -> str:
        """Get visual representation of TCS"""
        if tcs >= 95:
            return "⚡⚡⚡⚡⚡ PERFECT!"
        elif tcs >= 90:
            return "████████░ ELITE"
        elif tcs >= 80:
            return "███████░░ HIGH"
        elif tcs >= 70:
            return "█████░░░░ GOOD"
        else:
            return "███░░░░░░ STANDARD"
    
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
    
    def create_arcade_signal_card(self, signal: dict) -> str:
        """Create tactical arcade signal display card - SITREP style"""
        
        # Calculate expiry countdown
        time_remaining = signal.get('time_remaining', 600)  # seconds
        expiry_bar = self._create_expiry_bar(time_remaining)
        active_traders = signal.get('active_traders', 0)
        
        # Style 1: Tactical SITREP
        sitrep = f"""
⚡ **TACTICAL SITREP** - ARCADE SCALP ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 **OP: {signal['display_type']}**
📍 **AO:** {signal['symbol']} | **VECTOR:** {signal['direction'].upper()}
🎯 **ENTRY:** {signal['entry_price']:.5f}
💥 **OBJECTIVE:** +{signal['expected_pips']} PIPS
⚔️ **RISK:** {signal.get('risk_pips', 3)} PIPS

📊 **INTEL CONFIDENCE:** {signal['tcs_score']}%
{self._get_tcs_visual(signal['tcs_score'])}

⏱️ **OP WINDOW:** {expiry_bar}
👥 **SQUAD ENGAGED:** {active_traders} OPERATORS

[🔫 **ENGAGE TARGET**] [📋 **VIEW INTEL**]
"""
        return sitrep
    
    def create_sniper_signal_card(self, signal: dict) -> str:
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
        return sniper_brief

# Test the displays
def test_displays():
    display = SignalDisplay()
    
    # Sample arcade signal
    arcade_signal = {
        'visual_emoji': '🎮',
        'display_type': 'DAWN RAID',
        'symbol': 'EURUSD',
        'direction': 'buy',
        'entry_price': 1.08234,
        'expected_pips': 12,
        'risk_pips': 3,
        'tcs_score': 78,
        'expected_duration': 15,
        'time_remaining': 540,  # 9 minutes
        'active_traders': 23,
        'squad_avg_tcs': 75,
        'type': 'arcade',
        'callsign': 'BRAVO-7'
    }
    
    # Sample sniper signal
    sniper_signal = {
        'visual_emoji': '🎯',
        'display_type': 'PRECISION STRIKE',
        'symbol': 'GBPUSD',
        'direction': 'sell',
        'entry_price': 1.26789,
        'expected_pips': 25,
        'risk_pips': 5,
        'tcs_score': 92,
        'expected_duration': 30,
        'time_remaining': 480,  # 8 minutes
        'active_traders': 12,
        'squad_avg_tcs': 88,
        'type': 'sniper',
        'callsign': 'GHOST-1'
    }
    
    print("\n🎖️ TACTICAL SIGNAL DISPLAY MOCKUPS 🎖️")
    print("═" * 50)
    
    print("\n1️⃣ ARCADE SIGNAL - SITREP STYLE:")
    print(display.create_arcade_signal_card(arcade_signal))
    
    print("\n2️⃣ SNIPER SIGNAL - ELITE BRIEFING:")
    print(display.create_sniper_signal_card(sniper_signal))
    
    print("\n3️⃣ EXPIRY COUNTDOWN EXAMPLES:")
    print("🟩🟩🟩🟩🟩 HOT (>8 min)")
    print("🟩🟩🟩🟩⬜ ACTIVE (6-8 min)")
    print("🟨🟨🟨⬜⬜ FADING (4-6 min)")
    print("🟧🟧⬜⬜⬜ CLOSING (2-4 min)")
    print("🟥⬜⬜⬜⬜ CRITICAL (<2 min)")
    print("⬛⬛⬛⬛⬛ EXPIRED (0 min)")
    
    print("\n4️⃣ EXPIRED SIGNAL EXAMPLE:")
    expired_signal = arcade_signal.copy()
    expired_signal['time_remaining'] = 0
    expired_signal['active_traders'] = 89
    expired_card = f"""
⚫ **[EXPIRED]** OPERATION COMPLETE ⚫
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
~~**OP: {expired_signal['display_type']}**~~
~~**TARGET:** {expired_signal['symbol']} | {expired_signal['direction'].upper()}~~
~~**ENTRY:** {expired_signal['entry_price']:.5f}~~

**FINAL REPORT:**
• 89 operators engaged
• Operation window closed
• Check battle report for results

⬛⬛⬛⬛⬛ EXPIRED
"""
    print(expired_card)
    
    print("\n✅ KEY FEATURES:")
    print("• Clear trade info (symbol, direction, entry)")
    print("• Risk/Reward shown (risk pips + target pips)")
    print("• Visual expiry countdown bar")
    print("• Squad engagement tracking")
    print("• Military terminology throughout")
    print("• Distinct arcade (🎮) vs sniper (🎯) styles")
    
    print("\n" + "="*50)
    print("\n5️⃣ ACTIVE POSITIONS DISPLAY:")
    
    # Test with active positions
    active_positions = [
        {'symbol': 'EURUSD', 'direction': 'buy', 'pnl': 15, 'time_in_minutes': 45},
        {'symbol': 'GBPUSD', 'direction': 'sell', 'pnl': -8, 'time_in_minutes': 23},
        {'symbol': 'USDJPY', 'direction': 'buy', 'pnl': 22, 'time_in_minutes': 67},
        {'symbol': 'AUDUSD', 'direction': 'sell', 'pnl': 0, 'time_in_minutes': 5},
    ]
    
    print(display.create_position_summary_card(active_positions))
    
    # Test with no positions
    print("\nWith no positions:")
    print(display.create_position_summary_card([]))
    
    print("\n" + "="*50)
    print("\n6️⃣ DAILY BATTLE REPORT:")
    
    # Test daily stats
    daily_stats = {
        'trades': 5,
        'wins': 4,
        'win_rate': 80,
        'pips': 73,
        'xp': 285,
        'rank_progress': 82,
        'current_badge': '🥉 RECRUIT',
        'next_badge': '🥈 WARRIOR',
        'xp_to_next': 150
    }
    
    print(display.create_daily_summary_card(daily_stats))
    
    # Test with poor performance
    print("\nWith poor performance:")
    poor_stats = {
        'trades': 3,
        'wins': 1,
        'win_rate': 33,
        'pips': -25,
        'xp': 45,
        'rank_progress': 12,
        'current_badge': '🥉 RECRUIT',
        'next_badge': '🥈 WARRIOR',
        'xp_to_next': 400
    }
    
    print(display.create_daily_summary_card(poor_stats))

# Add helper methods to the test class
def create_position_summary_card(self, positions):
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

def create_daily_summary_card(self, stats):
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

def _create_progress_bar(self, percentage):
    """Create visual progress bar"""
    filled = int(percentage / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty

def _get_daily_objectives(self, stats):
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

# Add methods to test class
SignalDisplay.create_position_summary_card = create_position_summary_card
SignalDisplay.create_daily_summary_card = create_daily_summary_card
SignalDisplay._create_progress_bar = _create_progress_bar
SignalDisplay._get_daily_objectives = _get_daily_objectives

if __name__ == "__main__":
    test_displays()