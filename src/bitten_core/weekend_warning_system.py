"""
🎯 BITTEN Weekend Safety Briefing System

Pre-liberty safety brief for all operators before weekend market conditions
"""

import logging
from datetime import datetime, time
from typing import Dict, List

logger = logging.getLogger(__name__)


class WeekendSafetyBriefing:
    """
    Mandatory safety briefing before weekend liberty.
    Just like the military - you get briefed before you're released.
    """

    def get_weekend_warning_message(self, user_tier: str, open_positions: int) -> str:
        """
        Generate tier-appropriate weekend warning
        """

        if open_positions == 0:
            return self._get_no_positions_message(user_tier)
        else:
            return self._get_open_positions_message(user_tier, open_positions)

    def _get_no_positions_message(self, tier: str) -> str:
        """Message when user has no open positions"""

        base_message = (
            "📋 **WEEKEND SAFETY BRIEFING**\n"
            "────────────────────\n"
            "**ATTENTION ALL OPERATORS**\n\n"
            "This is your pre-liberty safety brief.\n\n"
            "**Weekend Market Conditions:**\n"
            "• Liquidity: DOWN 70%\n"
            "• Spreads: WIDENED\n"
            "• Gap Risk: ELEVATED\n"
            "• Chaos Level: HIGH\n\n"
        )

        tier_specific = {
            "NIBBLER": (
                "🟢 **NIBBLER LIBERTY STATUS: APPROVED**\n"
                "• No positions open - Well done\n"
                "• Enjoy your weekend liberty\n"
                "• Rest and recharge, operator\n"
                "• Report back Monday 0800 UTC\n\n"
                "_Liberty secured. Dismissed._"
            ),
            "FANG": (
                "🟡 **FANG LIBERTY BRIEF:**\n"
                "• Weekend operations = High risk\n"
                "• If engaging: 50% position sizes\n"
                "• TCS minimum raised to 80%\n"
                "• Don't be a liberty incident\n\n"
                "_Your weekend pass is approved - use it wisely._"
            ),
            "COMMANDER": (
                "🟠 **COMMANDER LIBERTY GUIDANCE:**\n"
                "• Weekend ops authorized at discretion\n"
                "• You've been briefed on gap risk\n"
                "• Thin liquidity = Wide spreads\n"
                "• Make smart choices out there\n\n"
                "_Liberty granted. Stay sharp, Commander._"
            ),
            "APEX": (
                "⚫ **LIBERTY PROTOCOL:**\n"
                "• No restrictions - You know the game\n"
                "• Weekend chaos is your playground\n"
                "• Brief complete - Make your choice\n"
                "• See you on the other side\n\n"
                "_Liberty authorized. Hunt well._"
            ),
        }

        return base_message + tier_specific.get(tier, tier_specific["NIBBLER"])

    def _get_open_positions_message(self, tier: str, positions: int) -> str:
        """Message when user has open positions"""

        base_message = (
            f"🔴 **WEEKEND SAFETY BRIEF - POSITIONS DETECTED**\n"
            f"────────────────\n"
            f"**ATTENTION OPERATOR**\n\n"
            f"Pre-liberty check shows {positions} ACTIVE position{'s' if positions > 1 else ''}.\n\n"
            f"⚠️ Weekend gaps are NOT your friend.\n"
            f"📊 Friday close ≠ Sunday open.\n\n"
        )

        tier_specific = {
            "NIBBLER": (
                "🔴 **NIBBLER SAFETY DIRECTIVE:**\n"
                "\n‼️ STRONG RECOMMENDATION: Close all positions\n\n"
                "• Weekend gaps have no mercy\n"
                "• Your stops may not save you\n"
                "• Monday gaps can skip past stops\n"
                "• Don't be a weekend casualty\n\n"
                "🚨 **Liberty Status: CONDITIONAL**\n\n"
                "_Secure your positions before liberty, Soldier._"
            ),
            "FANG": (
                "🟡 **FANG LIBERTY ASSESSMENT:**\n"
                "\n⚠️ RISK LEVEL: ELEVATED\n\n"
                "**Your Options:**\n"
                "1️⃣ Close positions (Recommended)\n"
                "2️⃣ Tighten stops to breakeven\n"
                "3️⃣ Accept gap risk (Not advised)\n\n"
                "📢 Weekend spreads = 2-3x normal\n\n"
                "_Liberty granted with warning logged._"
            ),
            "COMMANDER": (
                "🟠 **COMMANDER BRIEF ACKNOWLEDGED:**\n"
                "\n🌍 Weekend Intelligence:\n"
                "• Asia opens Sunday 2100 UTC\n"
                "• Gap probability: 65%\n"
                "• Average weekend move: ±30-50 pips\n"
                "• Worst case: ±200+ pips\n\n"
                "You have command authority.\n\n"
                "_Liberty approved. Brief complete._"
            ),
            "APEX": (
                "⚫ **ACKNOWLEDGMENT ONLY:**\n"
                "\nPositions detected. Brief noted.\n\n"
                "The weekend market takes no prisoners.\n"
                "But you already know that.\n\n"
                "🌀 **Liberty Status: UNRESTRICTED**\n\n"
                "_Happy hunting. Or happy resting._\n"
                "_Your choice, as always._"
            ),
        }

        return base_message + tier_specific.get(tier, tier_specific["NIBBLER"])

    def should_send_warning(self, current_time: datetime) -> bool:
        """
        Check if it's time to send weekend warning
        Friday after 12:00 PM UTC (noon)
        """
        # Friday = 4
        if current_time.weekday() != 4:
            return False

        # After noon UTC
        if current_time.hour >= 12:
            return True

        return False

    def get_weekend_stats_summary(self, user_stats: Dict) -> str:
        """
        Include user's weekend performance history
        """
        weekend_wins = user_stats.get("weekend_wins", 0)
        weekend_losses = user_stats.get("weekend_losses", 0)
        weekend_total = weekend_wins + weekend_losses

        if weekend_total == 0:
            return "\n📊 _No weekend trading history yet._"

        weekend_wr = (weekend_wins / weekend_total) * 100

        if weekend_wr >= 70:
            return f"\n📊 Your weekend record: {weekend_wins}W-{weekend_losses}L ({weekend_wr:.0f}% WR) 💪"
        elif weekend_wr >= 50:
            return f"\n📊 Your weekend record: {weekend_wins}W-{weekend_losses}L ({weekend_wr:.0f}% WR) ⚖️"
        else:
            return f"\n📊 Your weekend record: {weekend_wins}W-{weekend_losses}L ({weekend_wr:.0f}% WR) ⚠️"


# Integration function for telegram_router.py
async def send_weekend_warnings(telegram_router, active_users: List[Dict]):
    """
    Send weekend warnings to all active users
    Called by scheduler every Friday at noon UTC
    """
    warning_system = WeekendSafetyBriefing()

    for user in active_users:
        try:
            # Get user's open positions
            positions = await telegram_router.get_user_positions(user["user_id"])

            # Generate message
            message = warning_system.get_weekend_warning_message(user["tier"], len(positions))

            # Add stats if available
            if user.get("stats"):
                message += warning_system.get_weekend_stats_summary(user["stats"])

            # Send via Telegram
            await telegram_router.send_message(user["chat_id"], message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Failed to send weekend warning to user {user['user_id']}: {e}")
