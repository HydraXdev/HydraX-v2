"""
Test Signal Command Handlers
Telegram commands for the 60 TCS test signal system
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .test_signal_system import test_signal_system
from .advanced_signal_integration import advanced_integration

logger = logging.getLogger(__name__)


class TestSignalCommands:
    """Command handlers for test signal system"""
    
    def __init__(self, telegram_bot=None):
        self.bot = telegram_bot
        self.test_system = test_signal_system
        self.integration = advanced_integration
    
    async def handle_test_stats_command(self, update, context) -> str:
        """Handle /teststats command - show user's test signal statistics"""
        try:
            user_id = str(update.effective_user.id)
            stats = self.test_system.get_user_stats(user_id)
            
            if not stats['has_received_test_signals']:
                return "🔍 You haven't received any test signals yet. Stay alert!"
            
            user_stats = stats['stats']
            
            # Format the message
            message = "📊 **Your Test Signal Stats**\n\n"
            
            # Basic stats
            message += f"📨 Signals Received: {user_stats['total_received']}\n"
            message += f"✅ Correctly Passed: {user_stats['total_passed']}\n"
            message += f"❌ Taken (Baited): {user_stats['total_taken']}\n"
            message += f"📈 Pass Rate: {user_stats['pass_rate']:.1f}%\n\n"
            
            # Rewards earned
            message += "🎁 **Rewards Earned:**\n"
            message += f"🌟 XP Bonuses: +{user_stats['xp_bonuses_earned']} XP\n"
            message += f"🎯 Extra Shots: {user_stats['extra_shots_earned']}\n"
            message += f"🎲 Lucky Wins: {user_stats['total_won']}\n\n"
            
            # Attention score
            attention_emoji = self._get_attention_emoji(user_stats['attention_score'])
            message += f"👁️ **Attention Score:** {attention_emoji} {user_stats['attention_score']:.0f}/100\n\n"
            
            # Add tips based on performance
            if user_stats['pass_rate'] >= 80:
                message += "💡 *Excellent work! You have a sharp eye for suspicious signals.*"
            elif user_stats['pass_rate'] >= 50:
                message += "💡 *Good detection skills! Remember: 60 pip SL is a red flag.*"
            else:
                message += "💡 *Tip: Always check the SL distance. 60 pips is unusually high!*"
            
            return message
            
        except Exception as e:
            logger.error(f"Error handling test stats command: {e}")
            return "❌ Error retrieving test signal stats. Please try again later."
    
    async def handle_test_leaderboard_command(self, update, context) -> str:
        """Handle /testleaders command - show test signal leaderboard"""
        try:
            leaderboard = self.test_system.get_leaderboard(10)
            
            if not leaderboard:
                return "🏆 No test signal leaderboard data yet. Be the first!"
            
            message = "🏆 **Test Signal Detection Leaderboard**\n\n"
            message += "Top signal detectors who can spot the fakes:\n\n"
            
            medals = ["🥇", "🥈", "🥉"]
            
            for i, entry in enumerate(leaderboard):
                medal = medals[i] if i < 3 else f"{i+1}."
                
                # Anonymize user ID for privacy
                anon_id = f"Agent{entry['user_id'][-4:]}"
                
                message += f"{medal} **{anon_id}**\n"
                message += f"   📍 Signals Passed: {entry['signals_passed']}\n"
                message += f"   👁️ Attention Score: {entry['attention_score']:.0f}\n"
                message += f"   ✅ Pass Rate: {entry['pass_rate']:.1f}%\n"
                
                if entry['lucky_wins'] > 0:
                    message += f"   🎲 Lucky Wins: {entry['lucky_wins']}\n"
                
                message += "\n"
            
            message += "\n💡 *Test signals have 60 pip SL and bad R:R. Can you spot them?*"
            
            return message
            
        except Exception as e:
            logger.error(f"Error handling test leaderboard command: {e}")
            return "❌ Error retrieving leaderboard. Please try again later."
    
    async def handle_test_info_command(self, update, context) -> str:
        """Handle /testinfo command - explain the test signal system"""
        message = """🎯 **Test Signal System**

**What are Test Signals?**
Occasionally, the system sends out "test signals" with obviously bad parameters:
• Exactly 60 pip stop loss (TCS)
• Terrible risk/reward ratio (1:0.33)
• Sent at unusual times

**Why?**
To reward traders who are paying attention and can identify bad trades!

**Rewards:**
✅ **If you PASS (don't take it):** +10-20 XP bonus
❌ **If you take it and hit SL:** Get an extra shot for the day
🎲 **If you take it and WIN (30% chance):** Special achievement + 50 XP

**How to Spot Them:**
• Check SL distance - exactly 60 pips is suspicious
• Look at R:R ratio - 1:0.33 is terrible
• Consider the timing - odd hours are a hint
• Trust your instincts!

**Stats Commands:**
📊 `/teststats` - Your personal test signal statistics
🏆 `/testleaders` - Top test signal detectors

Remember: Real signals rarely have 60 pip SL. Stay sharp! 👁️"""
        
        return message
    
    def _get_attention_emoji(self, score: float) -> str:
        """Get emoji based on attention score"""
        if score >= 90:
            return "🦅"  # Eagle eye
        elif score >= 70:
            return "👁️"  # Watchful
        elif score >= 50:
            return "😴"  # Getting sleepy
        else:
            return "😵"  # Not paying attention
    
    async def process_signal_feedback(self, user_id: str, signal_id: str, action: str) -> Optional[str]:
        """
        Process when user reports passing on a signal
        Returns a message if it was a test signal
        """
        try:
            # Check if this was a test signal
            if not signal_id.startswith('TEST_'):
                return None
            
            # Process the pass action
            await self.integration.process_user_passed_signal(user_id, signal_id)
            
            # Get the rewards
            stats = self.test_system.user_stats.get(user_id)
            if stats and stats.last_test_signal:
                # Check if this was recent
                time_diff = datetime.now() - stats.last_test_signal
                if time_diff.total_seconds() < 300:  # Within 5 minutes
                    return "🎯 Well spotted! That was a test signal. +15 XP for staying sharp!"
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing signal feedback: {e}")
            return None


# Command registration helper
def register_test_signal_commands(dispatcher):
    """Register test signal commands with the telegram dispatcher"""
    commands = TestSignalCommands()
    
    dispatcher.add_handler(CommandHandler('teststats', commands.handle_test_stats_command))
    dispatcher.add_handler(CommandHandler('testleaders', commands.handle_test_leaderboard_command))
    dispatcher.add_handler(CommandHandler('testinfo', commands.handle_test_info_command))
    
    logger.info("Test signal commands registered")