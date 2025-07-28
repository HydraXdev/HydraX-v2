#!/usr/bin/env python3
"""
Performance Commands for BITTEN Telegram Bot
Implements /PERFORMANCE and related monitoring commands
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from bitten_core.live_performance_tracker import live_tracker, get_performance_command_response
except ImportError:
    # Fallback for when performance tracker isn't available
    def get_performance_command_response(hours_back: int = 24) -> str:
        return "⚠️ Performance tracking system not initialized. Starting up..."

def handle_performance_command(message_text: str) -> str:
    """
    Handle /PERFORMANCE command with optional time parameters
    
    Examples:
    /PERFORMANCE -> Last 24 hours
    /PERFORMANCE 12 -> Last 12 hours  
    /PERFORMANCE 168 -> Last week
    """
    try:
        # Parse command for time parameter
        parts = message_text.strip().split()
        hours_back = 24  # Default
        
        if len(parts) > 1:
            try:
                hours_back = int(parts[1])
                # Limit to reasonable ranges
                hours_back = max(1, min(hours_back, 720))  # 1 hour to 30 days
            except ValueError:
                return "❌ Invalid time parameter. Use: /PERFORMANCE [hours] (1-720)"
        
        return get_performance_command_response(hours_back)
        
    except Exception as e:
        return f"❌ Error processing performance command: {str(e)}"

def handle_ghosted_command(args=None):
    """Handle /GHOSTED command for tactical ghosted operations report"""
    try:
        # Import required modules
        from bitten_core.enhanced_ghost_tracker import enhanced_ghost_tracker
        from bitten_core.live_performance_tracker import live_tracker
        
        # Get data from tracking systems
        summary = enhanced_ghost_tracker.get_missed_win_summary()
        true_rate = live_tracker.get_true_win_rate()

        fired_wins = true_rate.get('fired_wins', 0)
        fired_total = true_rate.get('fired_total', 1)  # Avoid division by zero
        ghost_wins = true_rate.get('ghost_wins', 0)
        ghost_total = true_rate.get('ghost_total', 1)  # Avoid division by zero
        total_missions = fired_total + ghost_total
        total_true = fired_wins + ghost_wins

        # Calculate percentages safely
        fired_pct = round(fired_wins/fired_total*100, 1) if fired_total > 0 else 0
        ghosted_pct = round(ghost_wins/ghost_total*100, 1) if ghost_total > 0 else 0
        true_pct = round(total_true/total_missions*100, 1) if total_missions > 0 else 0

        # Get TCS band stats
        tcs_band_stats = true_rate.get('tcs_band_stats', '• No TCS data available')
        
        # Get top opportunity
        top_opportunity = summary.get('top_opportunity', 'No significant missed opportunities detected')
        
        # Calculate impact
        impact_pct = summary.get('impact_pct', 0)

        return f"""☠️ GHOSTED OPS REPORT — Last 24h
━━━━━━━━━━━━━━━━━━━━━━
📦 TOTAL MISSIONS GENERATED: {total_missions}
🎯 EXECUTED: {fired_total}
👻 GHOSTED: {ghost_total}

💥 HIT RATES:
• Fired: {fired_wins}/{fired_total} → {fired_pct}%
• Ghosted Wins: {ghost_wins}/{ghost_total} → {ghosted_pct}%
• 💀 TRUE Win Rate: {true_pct}%

📊 TCS BAND INTEL:
{tcs_band_stats}

🔍 TOP GHOSTED SHOT:
• {top_opportunity}

🧠 Missed Opportunity Impact: {impact_pct}% of wins were ghosted.
━━━━━━━━━━━━━━━━━━━━━━
💡 Raise TCS filter to reduce signals.
💡 Lower to hunt more targets.
"""

    except Exception as e:
        return f"❌ Error generating GHOSTED report: {str(e)}\n🔧 Check tracking system status."

def handle_ghost_stats_command() -> str:
    """Handle /GHOSTSTATS command for detailed ghost mode analysis"""
    try:
        from bitten_core.live_performance_tracker import live_tracker
        
        ghost_summary = live_tracker.get_ghost_mode_summary(24)
        
        if not ghost_summary:
            return "👻 **GHOST MODE STATUS**: No recent activity\n🔧 Starting stealth protocols..."
        
        response = "👻 **GHOST MODE DETAILED ANALYSIS**\n"
        response += "⏰ **Period**: Last 24 hours\n\n"
        
        total_actions = sum(data['usage_count'] for data in ghost_summary.values())
        response += f"🎯 **Total Stealth Actions**: {total_actions:}\n\n"
        
        response += "📊 **STEALTH BREAKDOWN:**\n"
        for action, data in ghost_summary.items():
            effectiveness_emoji = "🟢" if data['avg_effectiveness'] >= 75 else "🟡" if data['avg_effectiveness'] >= 50 else "🔴"
            response += f"• **{action.replace('_', ' ').title()}**: {data['usage_count']} uses\n"
            response += f"  └ Effectiveness: {data['avg_effectiveness']:.1f}% {effectiveness_emoji}\n"
        
        # Overall assessment
        avg_effectiveness = sum(data['avg_effectiveness'] for data in ghost_summary.values()) / len(ghost_summary)
        
        if avg_effectiveness >= 75:
            status = "🛡️ **EXCELLENT STEALTH**"
        elif avg_effectiveness >= 50:
            status = "⚠️ **MODERATE STEALTH**"
        else:
            status = "🚨 **STEALTH NEEDS IMPROVEMENT**"
        
        response += f"\n{status}\n"
        response += f"📈 **Overall Ghost Effectiveness**: {avg_effectiveness:.1f}%"
        
        return response
        
    except Exception as e:
        return f"❌ Error fetching ghost stats: {str(e)}"

def handle_recent_signals_command(limit: int = 10) -> str:
    """Handle /RECENTSIGNALS command"""
    try:
        from bitten_core.live_performance_tracker import live_tracker
        
        recent = live_tracker.get_recent_signals(limit)
        
        if not recent:
            return "📡 **No recent signals found**\n🔧 Check signal generation system"
        
        response = f"📡 **LAST {len(recent)} SIGNALS**\n\n"
        
        for i, signal in enumerate(recent, 1):
            result_emoji = {
                'WIN': '✅',
                'LOSS': '❌',
                None: '⏳'
            }.get(signal['result'], '⏳')
            
            timestamp = datetime.fromisoformat(signal['timestamp']).strftime('%H:%M')
            
            response += f"**{i}.** {signal['symbol']} {signal['direction']} | "
            response += f"TCS {signal['tcs_score']}% | {timestamp} {result_emoji}\n"
            
            if signal['result']:
                response += f"   └ Result: {signal['profit_pips']:+.1f} pips | "
                response += f"{signal['users_executed']} executions\n"
            else:
                response += f"   └ Status: {signal['status']} | {signal['users_executed']} executions\n"
        
        return response
        
    except Exception as e:
        return f"❌ Error fetching recent signals: {str(e)}"

def handle_live_stats_command() -> str:
    """Handle /LIVESTATS for real-time statistics"""
    try:
        from bitten_core.live_performance_tracker import live_tracker
        
        # Get quick stats for multiple time periods
        stats_1h = live_tracker.get_live_performance_metrics(1)
        stats_24h = live_tracker.get_live_performance_metrics(24)
        stats_7d = live_tracker.get_live_performance_metrics(168)
        
        response = "⚡ **BITTEN LIVE STATISTICS**\n\n"
        
        response += "📊 **SIGNAL GENERATION:**\n"
        response += f"• Last Hour: **{stats_1h.signals_last_24h}** signals\n"
        response += f"• Last 24h: **{stats_24h.signals_last_24h}** signals\n"
        response += f"• Last 7 days: **{stats_7d.signals_last_24h}** signals\n\n"
        
        response += "🎯 **WIN RATES:**\n"
        response += f"• Last Hour: **{stats_1h.win_rate_24h:.1f}%**\n"
        response += f"• Last 24h: **{stats_24h.win_rate_24h:.1f}%**\n"
        response += f"• Last 7 days: **{stats_7d.win_rate_24h:.1f}%**\n"
        response += f"• All Time: **{stats_7d.win_rate_overall:.1f}%**\n\n"
        
        response += "🎲 **TCS QUALITY:**\n"
        response += f"• Current Avg: **{stats_24h.avg_tcs_score:.1f}%**\n"
        response += f"• 7-day Avg: **{stats_7d.avg_tcs_score:.1f}%**\n\n"
        
        response += "👻 **GHOST MODE:**\n"
        response += f"• 24h Effectiveness: **{stats_24h.ghost_mode_effectiveness:.1f}%**\n"
        response += f"• 7d Effectiveness: **{stats_7d.ghost_mode_effectiveness:.1f}%**\n\n"
        
        # Status indicator
        if stats_24h.win_rate_24h >= 85:
            status = "🟢 **EXCEEDING TARGETS**"
        elif stats_24h.win_rate_24h >= 75:
            status = "🟡 **MEETING TARGETS**"
        else:
            status = "🔴 **BELOW TARGETS**"
        
        response += f"🎖️ **Status**: {status}"
        
        return response
        
    except Exception as e:
        return f"❌ Error fetching live stats: {str(e)}"

def handle_missed_wins_command(message_text: str = "/MISSEDWINS") -> str:
    """Handle /MISSEDWINS command for missed opportunity analysis"""
    try:
        # Parse command for time parameter
        parts = message_text.strip().split()
        hours_back = 24  # Default
        
        if len(parts) > 1:
            try:
                hours_back = int(parts[1])
                # Limit to reasonable ranges
                hours_back = max(1, min(hours_back, 168))  # 1 hour to 7 days
            except ValueError:
                return "❌ Invalid time parameter. Use: /MISSEDWINS [hours] (1-168)"
        
        from bitten_core.live_performance_tracker import live_tracker
        from bitten_core.enhanced_ghost_tracker import enhanced_ghost_tracker
        
        # Get true win rate analysis
        true_stats = live_tracker.get_true_win_rate(hours_back, include_unfired=True)
        missed_summary = enhanced_ghost_tracker.get_missed_win_summary(hours_back)
        
        if 'error' in true_stats or 'error' in missed_summary:
            return "❌ Error analyzing missed wins. Check system logs."
        
        # Build response
        response = f"📊 **MISSED WIN REPORT** (Last {hours_back}h)\n\n"
        
        # Overview stats
        fired_total = true_stats['fired_signals']['total']
        fired_wins = true_stats['fired_signals']['wins']
        fired_win_rate = true_stats['fired_signals']['win_rate']
        
        unfired_total = true_stats['unfired_signals']['total']
        unfired_wins = true_stats['unfired_signals']['wins']
        unfired_win_rate = true_stats['unfired_signals']['win_rate']
        
        true_win_rate = true_stats['true_performance']['true_win_rate']
        
        response += "🎯 **EXECUTION ANALYSIS:**\n"
        response += f"• **{unfired_total}** expired missions not fired\n"
        response += f"• **{unfired_wins}** would have hit TP\n"
        response += f"• **{unfired_total - unfired_wins}** would have hit SL or ranged\n\n"
        
        response += "📈 **WIN RATE COMPARISON:**\n"
        response += f"• Fired Signals: **{fired_win_rate:.1f}%** ({fired_wins}/{fired_total})\n"
        response += f"• Missed Winners: **{unfired_win_rate:.1f}%** ({unfired_wins}/{unfired_total})\n"
        response += f"• **True Win Rate**: **{true_win_rate:.1f}%** (including unfired)\n\n"
        
        # Top missed opportunities
        if missed_summary.get('top_missed_tcs'):
            top_missed = missed_summary['top_missed_tcs']
            response += "🎲 **TOP MISSED OPPORTUNITY:**\n"
            response += f"• **{top_missed['symbol']}** {top_missed['direction']} (TCS {top_missed['tcs_score']}%)\n\n"
        
        if missed_summary.get('top_missed_symbol'):
            top_symbol = missed_summary['top_missed_symbol']
            response += "📍 **MOST MISSED SYMBOL:**\n"
            response += f"• **{top_symbol['symbol']}**: {top_symbol['count']} missed wins\n\n"
        
        # TCS Band Analysis (top 3 bands)
        tcs_bands = true_stats.get('tcs_band_breakdown', {})
        if tcs_bands:
            response += "🎚️ **TCS BAND PERFORMANCE:**\n"
            sorted_bands = sorted(tcs_bands.items(), key=lambda x: x[1]['combined_win_rate'], reverse=True)
            
            for tcs_range, data in sorted_bands[:3]:
                if data['combined_total'] > 0:
                    response += f"• **TCS {tcs_range}%**: {data['combined_win_rate']:.1f}% "
                    response += f"({data['fired_wins']}F + {data['unfired_wins']}U wins)\n"
        
        # Performance assessment
        if true_win_rate >= 90:
            assessment = "🟢 **EXCEPTIONAL PERFORMANCE**"
        elif true_win_rate >= 85:
            assessment = "🟢 **EXCELLENT PERFORMANCE**"
        elif true_win_rate >= 80:
            assessment = "🟡 **GOOD PERFORMANCE**"
        elif true_win_rate >= 75:
            assessment = "🟡 **MEETING TARGETS**"
        else:
            assessment = "🔴 **BELOW TARGETS**"
        
        missed_opportunity_impact = unfired_wins / (fired_wins + unfired_wins) * 100 if (fired_wins + unfired_wins) > 0 else 0
        
        response += f"\n{assessment}\n"
        response += f"💡 **Missed Opportunity Impact**: {missed_opportunity_impact:.1f}% of total wins"
        
        return response
        
    except ImportError:
        return "❌ Missed wins analysis not available. Ghost tracker not initialized."
    except Exception as e:
        return f"❌ Error analyzing missed wins: {str(e)}"

# Command mapping for easy integration
PERFORMANCE_COMMANDS = {
    'PERFORMANCE': handle_performance_command,
    'PERF': handle_performance_command,  # Short alias
    'GHOSTSTATS': lambda _: handle_ghost_stats_command(),
    'GHOST': lambda _: handle_ghost_stats_command(),  # Short alias
    'RECENTSIGNALS': lambda _: handle_recent_signals_command(),
    'RECENT': lambda _: handle_recent_signals_command(),  # Short alias
    'LIVESTATS': lambda _: handle_live_stats_command(),
    'STATS': lambda _: handle_live_stats_command(),  # Short alias
    'MISSEDWINS': handle_missed_wins_command,
    'MISSED': handle_missed_wins_command,  # Short alias
}

def process_performance_command(command: str, message_text: str) -> str:
    """
    Process any performance-related command
    
    Args:
        command: The command name (e.g., 'PERFORMANCE')
        message_text: Full message text for parameter parsing
    
    Returns:
        Formatted response string
    """
    handler = PERFORMANCE_COMMANDS.get(command.upper())
    
    if not handler:
        return f"❌ Unknown performance command: {command}"
    
    try:
        return handler(message_text)
    except Exception as e:
        return f"❌ Error processing command {command}: {str(e)}"

# Quick test function
def test_performance_commands():
    """Test the performance command system"""
    print("🧪 Testing Performance Commands...")
    
    # Test basic performance command
    result = handle_performance_command("/PERFORMANCE")
    print(f"✅ /PERFORMANCE: {len(result)} chars")
    
    # Test with time parameter
    result = handle_performance_command("/PERFORMANCE 12")
    print(f"✅ /PERFORMANCE 12: {len(result)} chars")
    
    # Test ghost stats
    result = handle_ghost_stats_command()
    print(f"✅ /GHOSTSTATS: {len(result)} chars")
    
    # Test recent signals
    result = handle_recent_signals_command(5)
    print(f"✅ /RECENTSIGNALS: {len(result)} chars")
    
    # Test live stats
    result = handle_live_stats_command()
    print(f"✅ /LIVESTATS: {len(result)} chars")
    
    # Test missed wins
    result = handle_missed_wins_command("/MISSEDWINS")
    print(f"✅ /MISSEDWINS: {len(result)} chars")
    
    print("🎯 All performance commands tested!")

if __name__ == "__main__":
    test_performance_commands()