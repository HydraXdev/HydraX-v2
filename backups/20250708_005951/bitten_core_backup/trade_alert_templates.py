# trade_alert_templates.py
# BITTEN Military-Style Trade Alert Templates

from enum import Enum
from typing import Dict, Optional
from datetime import datetime, timedelta

class TradeAlertStyle(Enum):
    SITREP = "sitrep"
    COMBAT_BRIEFING = "combat_briefing"
    SNIPER_ELITE = "sniper_elite"
    MISSION_ALERT = "mission_alert"

class ArcadeCallsigns(Enum):
    DAWN_RAID = ("🌅", "London Breakout - Early morning assault")
    WALL_DEFENDER = ("🏰", "Support/Resistance Bounce - Defending key levels")
    ROCKET_RIDE = ("🚀", "Momentum Continuation - Riding the trend")
    RUBBER_BAND = ("🎯", "Mean Reversion - Snapping back to balance")

class TradeAlertTemplates:
    """Military-themed trade alert templates for Telegram"""
    
    @staticmethod
    def create_tcs_bar(tcs_score: int) -> str:
        """Create visual TCS confidence bar"""
        filled = int(tcs_score / 10)
        empty = 10 - filled
        
        if tcs_score >= 90:
            bar = "█" * filled + "░" * empty
        elif tcs_score >= 80:
            bar = "█" * (filled - 1) + "▓" + "░" * empty
        else:
            bar = "█" * filled + "░" * empty
            
        return f"{bar} {tcs_score}%"
    
    @staticmethod
    def create_countdown_bar(seconds_remaining: int, total_seconds: int = 600) -> str:
        """Create visual countdown timer bar"""
        if seconds_remaining <= 0:
            return "[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]"
            
        percent = seconds_remaining / total_seconds
        filled = int(percent * 30)
        empty = 30 - filled
        
        # Change color as time expires
        if percent > 0.5:
            bar_char = "▓"
        elif percent > 0.25:
            bar_char = "▒"
        else:
            bar_char = "░"
            
        return f"[{bar_char * filled}{'░' * empty}]"
    
    @staticmethod
    def format_time_remaining(seconds: int) -> str:
        """Format seconds to MM:SS"""
        if seconds <= 0:
            return "EXPIRED"
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def tactical_sitrep(trade_data: Dict) -> str:
        """SITREP style alert for arcade trades"""
        callsign = trade_data.get('callsign', 'VORTEX AMBUSH')
        symbol = trade_data['symbol']
        direction = trade_data['direction'].upper()
        direction_emoji = "🟢" if direction == "BUY" else "🔴"
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        sl_pips = trade_data['stop_loss_pips']
        tcs = trade_data['tcs_score']
        active_traders = trade_data.get('active_traders', 0)
        seconds_left = trade_data.get('seconds_remaining', 300)
        
        tcs_bar = TradeAlertTemplates.create_tcs_bar(tcs)
        countdown_bar = TradeAlertTemplates.create_countdown_bar(seconds_left)
        time_display = TradeAlertTemplates.format_time_remaining(seconds_left)
        
        return f"""┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🎮 TACTICAL SITREP - FIRE MISSION ACTIVE   ┃
┃━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
┃ CALLSIGN: {callsign:<32}┃
┃ SECTOR: {symbol} | VECTOR: {direction_emoji} {direction:<11}┃
┃ ENTRY: {entry:<35}┃
┃ OBJECTIVE: +{tp_pips} PIPS | RISK: -{sl_pips} PIPS{' ' * (20 - len(str(tp_pips)) - len(str(sl_pips)))}┃
┃                                            ┃
┃ TCS CONFIDENCE: {tcs_bar:<26}┃
┃ SQUAD STATUS: 👥 {active_traders} OPERATORS ENGAGED{' ' * (21 - len(str(active_traders)))}┃
┃                                            ┃
┃ ⏱️ MISSION EXPIRES: {time_display} ⬇️{' ' * (21 - len(time_display))}┃
┃ {countdown_bar:<42}┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        [🔫 ENGAGE] [📊 INTEL]"""

    @staticmethod
    def sniper_elite(trade_data: Dict) -> str:
        """Elite sniper style for high confidence trades"""
        symbol = trade_data['symbol']
        direction = trade_data['direction'].upper()
        direction_text = "LONG" if direction == "BUY" else "SHORT"
        direction_emoji = "🟢" if direction == "BUY" else "🔴"
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        sl_pips = trade_data['stop_loss_pips']
        tcs = trade_data['tcs_score']
        active_traders = trade_data.get('active_traders', 0)
        seconds_left = trade_data.get('seconds_remaining', 480)
        
        tcs_bar = "█" * int(tcs / 10) + "░" * (10 - int(tcs / 10))
        countdown_bar = TradeAlertTemplates.create_countdown_bar(seconds_left, 480)
        time_display = TradeAlertTemplates.format_time_remaining(seconds_left)
        
        return f"""┌─────────────────────────────────────────┐
│ 🎯 SNIPER SHOT DETECTED - EYES ONLY 🎯  │
│ ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ │
│ STRATEGY: ████ CLASSIFIED ████          │
│ TARGET: {symbol:<31}│
│ AUTHORIZATION: {direction_emoji} {direction_text} {entry:<17}│
│                                         │
│ REWARD PROFILE: +{tp_pips} PIPS{' ' * (22 - len(str(tp_pips)))}│
│ EXPOSURE LIMIT: -{sl_pips} PIPS{' ' * (22 - len(str(sl_pips)))}│
│                                         │
│ CONFIDENCE MATRIX: {tcs_bar} {tcs}%{' ' * (4 - len(str(tcs)))}│
│ ELITE OPERATORS: 👥 {active_traders} CONFIRMED{' ' * (16 - len(str(active_traders)))}│
│                                         │
│ AUTHORIZATION EXPIRES: {time_display:<16}│
│ {countdown_bar:<39}│
└─────────────────────────────────────────┘
      [🎯 EXECUTE] [🚫 ABORT]"""

    @staticmethod
    def tactical_hud_display(trade_data: Dict) -> str:
        """Futuristic HUD-style display with live data"""
        callsign = trade_data.get('callsign', 'DAWN RAID')
        symbol = trade_data['symbol']
        direction = trade_data['direction'].upper()
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        sl_pips = trade_data['stop_loss_pips']
        tcs = trade_data['tcs_score']
        active_traders = trade_data.get('active_traders', 0)
        seconds_left = trade_data.get('seconds_remaining', 300)
        
        # Dynamic elements
        pulse = "◉" if seconds_left % 2 == 0 else "○"
        threat_level = "🟩" if tcs >= 85 else "🟨" if tcs >= 70 else "🟥"
        
        return f"""╔═══════════════[ TACTICAL HUD ]═══════════════╗
║ {pulse} LIVE FIRE MISSION {pulse}                      ║
╠══════════════════════════════════════════════╣
║ ▣ OPERATION: {callsign:<31}║
║ ▣ COORDINATES: {symbol} [{direction}]                   ║
║ ▣ BREACH POINT: {entry}                      ║
╟──────────────────────────────────────────────╢
║ ◈ REWARD ZONE: +{tp_pips} PIPS {threat_level}                   ║
║ ◈ DANGER ZONE: -{sl_pips} PIPS ⚠️                    ║
║ ◈ CONFIDENCE: ▰▰▰▰▰▰▰▰▱▱ {tcs}%              ║
╟──────────────────────────────────────────────╢
║ 🛡️ SQUAD: ●●●●●●●●●● {active_traders} ACTIVE           ║
║ ⏳ T-MINUS: {TradeAlertTemplates.format_time_remaining(seconds_left)} ▼                       ║
╚══════════════════════════════════════════════╝
         〘 ⚡ EXECUTE 〙  〘 📡 SCAN 〙"""

    @staticmethod
    def matrix_style_alert(trade_data: Dict) -> str:
        """Matrix-inspired digital rain effect"""
        symbol = trade_data['symbol']
        direction = "▲ LONG" if trade_data['direction'].upper() == "BUY" else "▼ SHORT"
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        tcs = trade_data['tcs_score']
        
        # Create matrix effect
        matrix_bar = "┃10110┃01001┃11010┃00111┃10100┃"
        
        return f"""┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ {matrix_bar} ┃
┃     ⟪ SIGNAL DETECTED ⟫          ┃
┃     {symbol} {direction}                   ┃
┃     ENTRY: {entry}              ┃  
┃     TARGET: +{tp_pips} PIPS            ┃
┃     CONFIDENCE: {tcs}%              ┃
┃ {matrix_bar} ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"""

    @staticmethod
    def radar_sweep_alert(trade_data: Dict) -> str:
        """Radar sweep visualization with rotating scanner"""
        callsign = trade_data.get('callsign', 'TARGET')
        symbol = trade_data['symbol']
        direction = trade_data['direction'].upper()
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        tcs = trade_data['tcs_score']
        active_traders = trade_data.get('active_traders', 0)
        
        # Create radar sweep effect
        sweep_frames = ["◐", "◓", "◑", "◒"]
        sweep = sweep_frames[active_traders % 4]
        
        return f"""╭─────────[ RADAR CONTACT ]─────────╮
│         {sweep} SCANNING {sweep}           │
│                                   │
│    🎯 {callsign:<27}│
│    📍 {symbol} :: {direction:<19}│
│    💹 ENTRY: {entry:<19}│
│    🏁 TARGET: +{tp_pips} PIPS{' ' * (14 - len(str(tp_pips)))}│
│                                   │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ {tcs}% LOCK    │
│ [{active_traders:02d}] OPERATORS ON TARGET         │
╰───────────────────────────────────╯
     ⟨ ENGAGE ⟩   ⟨ MONITOR ⟩"""

    @staticmethod
    def glitch_effect_alert(trade_data: Dict) -> str:
        """Cyberpunk glitch effect alert"""
        symbol = trade_data['symbol']
        direction = "▲" if trade_data['direction'].upper() == "BUY" else "▼"
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        tcs = trade_data['tcs_score']
        
        # Glitch characters
        glitch = "░▒▓█▓▒░"
        
        return f"""█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ {glitch} SIGNAL BREACH {glitch} █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
 ➤ {symbol} {direction} @ {entry}
 ➤ PROFIT: +{tp_pips} PIPS
 ➤ CONFIDENCE: {tcs}%
 ➤ STATUS: ⚡ ACTIVE ⚡
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█"""

    @staticmethod 
    def heat_map_alert(trade_data: Dict) -> str:
        """Heat map style with intensity indicators"""
        callsign = trade_data.get('callsign', 'OPERATION')
        symbol = trade_data['symbol']
        direction = trade_data['direction'].upper()
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        sl_pips = trade_data['stop_loss_pips']
        tcs = trade_data['tcs_score']
        
        # Heat intensity based on TCS
        if tcs >= 90:
            heat = "🔴🔴🔴 CRITICAL HEAT 🔴🔴🔴"
            intensity = "████████████"
        elif tcs >= 80:
            heat = "🟠🟠 HIGH HEAT 🟠🟠"
            intensity = "█████████░░░"
        elif tcs >= 70:
            heat = "🟡 MODERATE HEAT 🟡"
            intensity = "██████░░░░░░"
        else:
            heat = "🟢 LOW HEAT 🟢"
            intensity = "███░░░░░░░░░"
            
        return f"""┌─── THERMAL DETECTION ───┐
│ {heat} │
├─────────────────────────┤
│ 🎯 {callsign:<20}│
│ 📊 {symbol} {direction:<14}│
│ 📍 {entry:<20}│
│ ✅ +{tp_pips}p / ❌ -{sl_pips}p         │
│ {intensity} {tcs}%   │
└─────────────────────────┘
   [FIRE] [SCAN] [ABORT]"""

    @staticmethod
    def mission_alert_compact(trade_data: Dict) -> str:
        """Compact mission alert style"""
        callsign = trade_data.get('callsign', 'SHADOW PIERCE')
        symbol = trade_data['symbol']
        direction = trade_data['direction'].upper()
        direction_emoji = "🟢" if direction == "BUY" else "🔴"
        direction_text = "LONG" if direction == "BUY" else "SHORT"
        entry = trade_data['entry_price']
        tp_pips = trade_data['take_profit_pips']
        sl_pips = trade_data['stop_loss_pips']
        tcs = trade_data['tcs_score']
        active_traders = trade_data.get('active_traders', 0)
        seconds_left = trade_data.get('seconds_remaining', 300)
        
        countdown_bar = TradeAlertTemplates.create_countdown_bar(seconds_left)
        time_display = TradeAlertTemplates.format_time_remaining(seconds_left)
        
        return f"""🚨 MISSION ALERT: {callsign} 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 {symbol} | {direction_emoji} {direction_text} @ {entry}
🎯 +{tp_pips} PIPS | 💣 -{sl_pips} PIPS | TCS: {tcs}%
👥 {active_traders} IN POSITION | ⏱️ {time_display} LEFT
{countdown_bar}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    @staticmethod
    def expired_alert(original_alert: str, trade_data: Dict) -> str:
        """Convert active alert to expired social proof"""
        # Add strikethrough to key elements
        lines = original_alert.split('\n')
        expired_lines = []
        
        for line in lines:
            if any(keyword in line for keyword in ['CALLSIGN:', 'SECTOR:', 'ENTRY:', 'OBJECTIVE:', 'TARGET:', 'AUTHORIZATION:']):
                # Add strikethrough to these lines
                line = '~~' + line.strip() + '~~'
            expired_lines.append(line)
        
        # Add expiry notice
        total_engaged = trade_data.get('total_engaged', trade_data.get('active_traders', 0))
        tcs = trade_data['tcs_score']
        
        expiry_notice = f"""
┃ FINAL TCS: {tcs}% | ENGAGED: {total_engaged} TOTAL        ┃
┃ STATUS: ⛔ WINDOW CLOSED                   ┃
┃                                            ┃
┃ 📌 KEPT FOR SOCIAL PROOF - 10H            ┃"""
        
        # Replace the countdown section with expiry notice
        result = '\n'.join(expired_lines)
        # Find and replace the timer section
        timer_start = result.find('⏱️ MISSION EXPIRES:')
        if timer_start == -1:
            timer_start = result.find('AUTHORIZATION EXPIRES:')
        
        if timer_start != -1:
            # Find the end of the timer section (next ┃ or │)
            timer_line_end = result.find('\n', timer_start)
            next_line_end = result.find('\n', timer_line_end + 1)
            
            # Replace timer section with expiry notice
            before = result[:timer_start - 3]  # -3 to include the ┃
            after = result[next_line_end:]
            result = before + expiry_notice + after
            
        return result

# Example usage functions
def create_arcade_alert(symbol: str, direction: str, entry: float, 
                       tp_pips: int, sl_pips: int, tcs: int, 
                       callsign: str = "VORTEX AMBUSH") -> str:
    """Create arcade trade alert"""
    trade_data = {
        'callsign': callsign,
        'symbol': symbol,
        'direction': direction,
        'entry_price': entry,
        'take_profit_pips': tp_pips,
        'stop_loss_pips': sl_pips,
        'tcs_score': tcs,
        'active_traders': 0,
        'seconds_remaining': 600
    }
    return TradeAlertTemplates.tactical_sitrep(trade_data)

def create_sniper_alert(symbol: str, direction: str, entry: float,
                       tp_pips: int, sl_pips: int, tcs: int) -> str:
    """Create sniper elite alert"""
    trade_data = {
        'symbol': symbol,
        'direction': direction,
        'entry_price': entry,
        'take_profit_pips': tp_pips,
        'stop_loss_pips': sl_pips,
        'tcs_score': tcs,
        'active_traders': 0,
        'seconds_remaining': 480
    }
    return TradeAlertTemplates.sniper_elite(trade_data)