# signal_display.py
# BITTEN Signal Display System - Visual Card Generation

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

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
        """Create arcade signal display card"""
        
        # Style 1: Compact Card
        compact = f"""
╔═══════════════════════════╗
║ {signal['visual_emoji']} {signal['display_type']:<20}║
║ {signal['symbol']} │ {signal['direction'].upper():>4} │ TCS: {signal['tcs_score']}% ║
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
→ +{signal['expected_pips']} pips | TCS: {signal['tcs_score']}%
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
        
        # Return detailed style for now
        return detailed
    
    def create_sniper_signal_card(self, signal: Dict) -> str:
        """Create mysterious sniper signal card"""
        
        # Style 1: Classified
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
        
        return classified
    
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
        """Create active positions summary"""
        
        if not positions:
            return """
╔═══════════════════════════════╗
║ 📊 NO ACTIVE POSITIONS        ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║                               ║
║   Ready to hunt! 🎯           ║
║   Shots available: 6/6        ║
║                               ║
╚═══════════════════════════════╝"""
        
        position_lines = []
        total_pnl = 0
        
        for pos in positions[:3]:  # Show max 3
            pnl = pos.get('pnl', 0)
            total_pnl += pnl
            emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            position_lines.append(
                f"║ {emoji} {pos['symbol']} {pos['direction'].upper()} │ {pnl:+.0f}p ║"
            )
        
        return f"""
╔═══════════════════════════════╗
║ 📊 ACTIVE POSITIONS ({len(positions)})       ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
{''.join(position_lines)}
║ ─────────────────────────── ║
║ Total P/L: {total_pnl:+.0f} pips         ║
╚═══════════════════════════════╝"""
    
    def create_daily_summary_card(self, stats: Dict) -> str:
        """Create daily performance summary"""
        
        return f"""
╔═══════════════════════════════════╗
║ 📈 DAILY BATTLE REPORT           ║
║ ═════════════════════════════════ ║
║ Shots Fired: {stats.get('trades', 0)}/6              ║
║ Direct Hits: {stats.get('wins', 0)} ({stats.get('win_rate', 0)}%)          ║
║ Total Pips: {stats.get('pips', 0):+.0f}                 ║
║ XP Earned: +{stats.get('xp', 0)}                 ║
║                                   ║
║ Rank Progress: ████████░░ 82%     ║
║ Next Badge: 🥈 WARRIOR            ║
╚═══════════════════════════════════╝"""
    
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