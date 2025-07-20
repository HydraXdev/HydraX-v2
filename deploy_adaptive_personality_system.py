#!/usr/bin/env python3
"""
🚀 Deploy Adaptive Personality System to BITTEN Bot
Integrates the advanced personality system with voice evolution
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/root/HydraX-v2/src')

from bitten_core.voice import (
    personality_engine,
    voice_driver,
    VOICE_PERSONALITY_MAP
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('PersonalityDeployment')

class AdaptivePersonalityBot:
    """
    Enhanced bot integration with adaptive personality system
    """
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.personality_engine = personality_engine
        self.voice_driver = voice_driver
        self.voice_enabled_users = set()
        self.load_voice_settings()
        
    def load_voice_settings(self):
        """Load user voice preferences"""
        settings_file = Path("/root/HydraX-v2/data/voice_settings.json")
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.voice_enabled_users = set(data.get('enabled_users', []))
    
    def save_voice_settings(self):
        """Save user voice preferences"""
        settings_file = Path("/root/HydraX-v2/data/voice_settings.json")
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump({
                'enabled_users': list(self.voice_enabled_users)
            }, f, indent=2)
    
    def is_voice_enabled(self, user_id: str) -> bool:
        """Check if user has voice enabled"""
        return str(user_id) in self.voice_enabled_users
    
    def toggle_voice(self, user_id: str) -> bool:
        """Toggle voice for user, returns new state"""
        user_id = str(user_id)
        if user_id in self.voice_enabled_users:
            self.voice_enabled_users.remove(user_id)
            enabled = False
        else:
            self.voice_enabled_users.add(user_id)
            enabled = True
        
        self.save_voice_settings()
        return enabled
    
    async def send_adaptive_message(self, chat_id: int, message_text: str, user_tier: str = "NIBBLER", 
                                  user_action: str = None, force_personality: str = None):
        """
        Send message with adaptive personality and optional voice
        """
        user_id = str(chat_id)
        
        # Analyze user behavior
        if user_action:
            self.personality_engine.analyze_user_behavior(user_id, message_text, user_action)
        
        # Ensure user has personality assigned
        profile = self.personality_engine.get_user_profile(user_id)
        if not profile:
            self.personality_engine.assign_personality(user_id, user_tier, force_personality)
            profile = self.personality_engine.get_user_profile(user_id)
        
        # Format message with personality
        formatted_message, voice_config = self.personality_engine.format_personality_message(
            user_id, message_text
        )
        
        # Send text message
        self.bot.send_message(chat_id, formatted_message, parse_mode='Markdown')
        
        # Send voice if enabled
        if self.is_voice_enabled(user_id):
            try:
                audio_file = await self.voice_driver.generate_personality_voice(
                    message_text, voice_config
                )
                
                if audio_file and os.path.exists(audio_file):
                    with open(audio_file, 'rb') as audio:
                        self.bot.send_voice(
                            chat_id, 
                            audio,
                            caption=f"🎙️ {voice_config['personality']}",
                            duration=None
                        )
                    
                    # Clean up temp file
                    os.remove(audio_file)
                    logger.info(f"Sent voice message for {voice_config['personality']}")
                
            except Exception as e:
                logger.error(f"Error sending voice message: {e}")
    
    def setup_personality_commands(self):
        """Add personality-related commands to bot"""
        
        @self.bot.message_handler(commands=['voice'])
        def handle_voice_toggle(message):
            """Toggle voice messages on/off"""
            user_id = str(message.from_user.id)
            enabled = self.toggle_voice(user_id)
            
            if enabled:
                response = "🔊 **Voice messages ENABLED!** Your personality will now speak to you!"
                # Send a sample voice message
                asyncio.create_task(self.send_adaptive_message(
                    message.chat.id,
                    "Voice system activated! Your personality is ready to speak!",
                    user_action="voice_enabled"
                ))
            else:
                response = "🔇 **Voice messages DISABLED.** You'll receive text-only responses."
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['personality'])
        def handle_personality_info(message):
            """Show user's personality information"""
            user_id = str(message.from_user.id)
            stats = self.personality_engine.get_personality_stats(user_id)
            
            if "error" in stats:
                self.bot.send_message(message.chat.id, "❌ No personality profile found. Send a message to get assigned!")
                return
            
            response = f"""🎭 **Your Personality Profile**
            
**Assigned Personality**: {stats['personality']}
**Current Mood**: {stats['current_mood']}
**Evolution Stage**: {stats['evolution_stage']:.1%}
**Total Interactions**: {stats['interaction_count']}
**Personality Evolutions**: {stats['evolution_count']}

**Current Traits**:
{self.format_traits(stats['traits'])}

**Adaptation Factors**:
{self.format_traits(stats['adaptation_factors'])}

*Your personality evolves based on your trading style and interactions!*"""
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['voiceforce'])
        def handle_force_personality(message):
            """Force a specific personality (for testing)"""
            user_id = str(message.from_user.id)
            args = message.text.split()[1:]
            
            if not args:
                personalities = ", ".join(VOICE_PERSONALITY_MAP.keys())
                response = f"**Available Personalities:**\n{personalities}\n\nUsage: `/voiceforce PERSONALITY_NAME`"
                self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
                return
            
            personality = args[0].upper()
            if personality not in VOICE_PERSONALITY_MAP:
                response = f"❌ Unknown personality: {personality}"
                self.bot.send_message(message.chat.id, response)
                return
            
            # Force assign personality
            self.personality_engine.assign_personality(user_id, "NIBBLER", personality)
            
            response = f"🎭 **Personality changed to {personality}!**"
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
            
            # Send a sample message from new personality
            asyncio.create_task(self.send_adaptive_message(
                message.chat.id,
                f"Hello! I'm your new personality, {personality}. Let's get started!",
                user_action="personality_change"
            ))
        
        @self.bot.message_handler(commands=['voicestats'])
        def handle_voice_stats(message):
            """Show voice synthesis usage stats"""
            usage_stats = self.voice_driver.get_usage_stats()
            performance_stats = self.voice_driver.get_performance_stats()
            
            response = f"""📊 **Voice System Statistics**
            
**Monthly Usage:**
- Characters Used: {usage_stats['characters_used']:,} / {self.voice_driver.monthly_limit:,}
- Usage: {usage_stats['percentage_used']:.1f}%
- Characters Remaining: {usage_stats['characters_remaining']:,}

**Performance:**
- Total Requests: {performance_stats['total_requests']}
- Success Rate: {(performance_stats['successful_requests'] / max(1, performance_stats['total_requests']) * 100):.1f}%
- Average Response Time: {performance_stats['average_response_time']:.2f}s
- Cache Hit Rate: {usage_stats['cache_hit_rate']:.1f}%

**Current Month**: {usage_stats['current_month']}

💡 Voice synthesis resets monthly on the free tier."""
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        logger.info("✅ Personality commands registered")
    
    def format_traits(self, traits: dict) -> str:
        """Format traits dictionary for display"""
        if not traits:
            return "*No traits recorded yet*"
        
        formatted = []
        for trait, value in traits.items():
            if isinstance(value, float):
                bar_length = int(abs(value) * 10)
                bar = "█" * bar_length + "░" * (10 - bar_length)
                sign = "+" if value >= 0 else "-"
                formatted.append(f"• {trait.title()}: {sign}{bar} ({value:.2f})")
            else:
                formatted.append(f"• {trait.title()}: {value}")
        
        return "\n".join(formatted)
    
    def enhance_existing_message_handler(self, original_handler):
        """Enhance existing message handler with personality system"""
        def enhanced_handler(message):
            # Call original handler
            original_result = original_handler(message)
            
            # Add personality analysis
            user_id = str(message.from_user.id)
            self.personality_engine.analyze_user_behavior(
                user_id, 
                message.text or "", 
                "general_message"
            )
            
            return original_result
        
        return enhanced_handler


async def test_personality_system():
    """Test the personality system without full bot integration"""
    logger.info("🧪 Testing Personality System...")
    
    # Test personality assignment
    test_user = "12345"
    personality = personality_engine.assign_personality(test_user, "FANG")
    logger.info(f"Assigned personality: {personality}")
    
    # Test behavior analysis
    personality_engine.analyze_user_behavior(test_user, "I want to execute trades fast and aggressively!", "trade_request")
    
    # Test message formatting
    formatted_msg, voice_config = personality_engine.format_personality_message(
        test_user, "Here's your trading signal analysis!"
    )
    logger.info(f"Formatted message: {formatted_msg}")
    logger.info(f"Voice config: {voice_config}")
    
    # Test voice generation
    if voice_driver.api_key:
        logger.info("Testing voice generation...")
        audio_file = await voice_driver.generate_personality_voice(
            "Testing adaptive personality voice system!", 
            voice_config
        )
        if audio_file:
            logger.info(f"✅ Voice generated: {audio_file}")
        else:
            logger.info("❌ Voice generation failed")
    
    # Test evolution
    personality_engine.evolve_personality(test_user, "tier_advancement", {"new_tier": "COMMANDER"})
    
    # Show stats
    stats = personality_engine.get_personality_stats(test_user)
    logger.info(f"Final stats: {json.dumps(stats, indent=2)}")


def apply_to_existing_bot():
    """Apply personality system to existing bot"""
    logger.info("🔧 Applying personality system to existing bot...")
    
    try:
        # Try to import existing bot
        from bitten_production_bot import bot
        
        # Create adaptive personality integration
        adaptive_bot = AdaptivePersonalityBot(bot)
        adaptive_bot.setup_personality_commands()
        
        # Enhance existing message handlers
        # This would require more specific integration based on existing bot structure
        
        logger.info("✅ Personality system applied to existing bot")
        return True
        
    except ImportError:
        logger.error("❌ Could not import existing bot")
        return False


def main():
    """Main deployment function"""
    logger.info("🚀 Deploying Adaptive Personality System...")
    
    # Test the system first
    asyncio.run(test_personality_system())
    
    # Try to apply to existing bot
    if apply_to_existing_bot():
        logger.info("✅ Deployment successful!")
    else:
        logger.info("⚠️ Could not integrate with existing bot. System is ready for manual integration.")
    
    logger.info("📖 Integration Instructions:")
    logger.info("1. Import: from deploy_adaptive_personality_system import AdaptivePersonalityBot")
    logger.info("2. Initialize: adaptive_bot = AdaptivePersonalityBot(your_bot_instance)")
    logger.info("3. Setup commands: adaptive_bot.setup_personality_commands()")
    logger.info("4. Use: await adaptive_bot.send_adaptive_message(chat_id, message, user_tier)")


if __name__ == "__main__":
    main()