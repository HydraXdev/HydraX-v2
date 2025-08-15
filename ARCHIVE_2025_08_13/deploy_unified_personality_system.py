#!/usr/bin/env python3
"""
🎭 Deploy Unified Personality System
Integrates all 3 personality layers into the production bot
"""

import os
import sys
import json
import asyncio
import logging
import random
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/root/HydraX-v2/src')
sys.path.insert(0, '/root/HydraX-v2')

from bitten_core.voice.unified_personality_orchestrator import unified_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('UnifiedPersonalityDeployment')

class UnifiedPersonalityBot:
    """
    Enhanced bot integration with unified personality system
    Combines all 3 personality layers into one cohesive experience
    """
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.unified_orchestrator = unified_orchestrator
        self.voice_enabled_users = set()
        self.load_voice_settings()
        
    def load_voice_settings(self):
        """Load user voice preferences"""
        settings_file = Path("/root/HydraX-v2/data/voice_settings.json")
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.voice_enabled_users = set(data.get('enabled_users', []))
                # Also track users who explicitly disabled voice
                self.voice_disabled_users = set(data.get('disabled_users', []))
        else:
            # Create data directory if it doesn't exist
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            self.voice_disabled_users = set()
    
    def is_voice_enabled(self, user_id: str) -> bool:
        """Check if user has voice enabled (DEFAULT: True unless explicitly disabled)"""
        user_id = str(user_id)
        # If user explicitly disabled voice, return False
        if hasattr(self, 'voice_disabled_users') and user_id in self.voice_disabled_users:
            return False
        # Otherwise, voice is enabled by default
        return True
    
    def save_voice_settings(self):
        """Save user voice preferences"""
        settings_file = Path("/root/HydraX-v2/data/voice_settings.json")
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump({
                'enabled_users': list(self.voice_enabled_users),
                'disabled_users': list(getattr(self, 'voice_disabled_users', set()))
            }, f, indent=2)
    
    def toggle_voice(self, user_id: str) -> bool:
        """Toggle voice for user, returns new state (DEFAULT: voice enabled)"""
        user_id = str(user_id)
        
        # Initialize disabled_users set if it doesn't exist
        if not hasattr(self, 'voice_disabled_users'):
            self.voice_disabled_users = set()
        
        # Check current state
        currently_enabled = self.is_voice_enabled(user_id)
        
        if currently_enabled:
            # Currently enabled, so disable it
            self.voice_disabled_users.add(user_id)
            # Remove from enabled list if it was there
            if user_id in self.voice_enabled_users:
                self.voice_enabled_users.remove(user_id)
            enabled = False
        else:
            # Currently disabled, so enable it (remove from disabled list)
            if user_id in self.voice_disabled_users:
                self.voice_disabled_users.remove(user_id)
            self.voice_enabled_users.add(user_id)
            enabled = True
        
        self.save_voice_settings()
        return enabled
    
    async def send_unified_message(self, chat_id: int, message_text: str, 
                                 user_tier: str = "NIBBLER", user_action: str = None,
                                 market_context: dict = None):
        """
        Send message using unified personality system
        Combines all 3 personality layers for rich character experience
        """
        user_id = str(chat_id)
        
        try:
            # Add voice enabled status to context
            context = market_context or {}
            context['voice_enabled'] = self.is_voice_enabled(user_id)
            
            # Process through unified orchestrator
            unified_response = await self.unified_orchestrator.process_user_interaction(
                user_id, message_text, user_tier, user_action, context
            )
            
            # Send text message with rich personality
            message_to_send = unified_response.message
            
            # Add evolution notification if triggered
            if unified_response.evolution_triggered:
                message_to_send += f"\n\n✨ **PERSONALITY EVOLUTION DETECTED!** ✨"
            
            # Add Norman's story element if present
            if unified_response.norman_story_element:
                message_to_send += f"\n\n💫 *{unified_response.norman_story_element}*"
            
            # Add multi-layer personality info
            personality_info = f"\n\n🎭 **{unified_response.primary_personality}**"
            if unified_response.deep_persona:
                personality_info += f" | {unified_response.deep_persona}"
            if unified_response.intel_role:
                personality_info += f" | {unified_response.intel_role}"
            
            message_to_send += personality_info
            
            # Send text message
            self.bot.send_message(chat_id, message_to_send, parse_mode='Markdown')
            
            # Send voice if enabled and available
            if unified_response.voice_file and os.path.exists(unified_response.voice_file):
                try:
                    with open(unified_response.voice_file, 'rb') as audio:
                        caption = f"🎙️ {unified_response.primary_personality}"
                        if unified_response.deep_persona:
                            caption += f" with {unified_response.deep_persona} depth"
                        
                        self.bot.send_voice(
                            chat_id,
                            audio,
                            caption=caption,
                            duration=None
                        )
                    
                    # Clean up temp file
                    os.remove(unified_response.voice_file)
                    logger.info(f"Sent unified voice message for {unified_response.primary_personality}")
                    
                except Exception as e:
                    logger.error(f"Voice message error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Unified message failed: {e}")
            # Fallback to simple message
            self.bot.send_message(chat_id, message_text, parse_mode='Markdown')
            return False
    
    def setup_unified_commands(self):
        """Setup commands for unified personality system"""
        
        @self.bot.message_handler(commands=['voice'])
        def handle_voice_toggle(message):
            """Toggle voice messages on/off (DEFAULT: enabled)"""
            user_id = str(message.from_user.id)
            
            # Check current state before toggling
            was_enabled = self.is_voice_enabled(user_id)
            enabled = self.toggle_voice(user_id)
            
            if enabled:
                if was_enabled:
                    response = "🔊 **Voice messages remain ENABLED!** All 3 personality layers are speaking to you!"
                else:
                    response = "🔊 **Voice messages RE-ENABLED!** All 3 personality layers will now speak to you!"
                    # Send a sample unified message
                    asyncio.create_task(self.send_unified_message(
                        message.chat.id,
                        "Voice system reactivated! Your unified personality system is ready to speak!",
                        user_action="voice_enabled"
                    ))
            else:
                response = "🔇 **Voice messages DISABLED.** You'll receive text-only responses. Use `/voice` again to re-enable."
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['personality'])
        def handle_personality_info(message):
            """Show comprehensive personality information"""
            user_id = str(message.from_user.id)
            
            async def get_stats():
                return await self.unified_orchestrator.get_personality_stats(user_id)
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                stats = loop.run_until_complete(get_stats())
            finally:
                loop.close()
            
            if stats and 'primary_personality' in stats:
                response = f"""🎭 **Your Unified Personality Profile**

**Primary Personality**: {stats['primary_personality']}
**Deep Persona**: {stats.get('deep_persona', 'Not assigned')}
**Intel Role**: {stats.get('intel_role', 'Not assigned')}
**Voice Traits**: {', '.join(stats.get('voice_traits', []))}

**System Integration**:
• **Layers Active**: {stats.get('system_layers', 0)}/3
• **Character Depth**: {stats.get('character_depth', 'Basic')}
• **Evolution Level**: {stats.get('evolution_level', 0):.1%}
• **Story Integration**: {stats.get('story_integration', 0)} elements

**Adaptive Stats**:
{self.format_adaptive_stats(stats.get('adaptive_stats', {}))}

*Your personality grows and evolves across all layers with every interaction!*"""
            else:
                response = "❌ No personality profile found. Send a message to get assigned to the unified system!"
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['evolve'])
        def handle_force_evolution(message):
            """Force personality evolution across all systems"""
            user_id = str(message.from_user.id)
            
            async def force_evolution():
                return await self.unified_orchestrator.force_personality_evolution(
                    user_id, 'manual_trigger', {'reason': 'user_request'}
                )
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(force_evolution())
            finally:
                loop.close()
            
            if success:
                response = "🌟 **PERSONALITY EVOLUTION TRIGGERED!** Your unified personality system has evolved across all layers!"
            else:
                response = "⚠️ Evolution not triggered. Your personality may already be at optimal state."
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['layers'])
        def handle_personality_layers(message):
            """Show information about all personality layers"""
            response = """🎭 **BITTEN Unified Personality System**

**Layer 1: Adaptive Personalities** ✅
• 5 AI personalities that evolve with you
• Voice synthesis with unique settings
• Behavioral learning and adaptation

**Layer 2: Core Personas** ✅
• Deep character responses based on Norman's story
• Emotional state detection and response
• Mississippi culture and family wisdom

**Layer 3: Intel Bot Personalities** ✅
• 10 specialized trading roles
• Tactical responses for specific situations
• Mission-oriented character interactions

**Integration Features**:
• **Character Continuity**: Same personality across all layers
• **Story Weaving**: Norman's story integrated throughout
• **Evolution System**: Grows with your trading journey
• **Voice Consistency**: Same voice across all responses

*All layers work together to create one unified, evolving character experience!*"""
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['norman'])
        def handle_norman_story(message):
            """Share Norman's story elements"""
            story_elements = [
                "Norman grew up in the Mississippi Delta, learning discipline from his father and wisdom from his mother.",
                "His grandmother taught him 'Work the plan, trust the process' - advice that shaped his trading philosophy.",
                "Bit, his loyal cat, appeared during Norman's darkest trading moments and became his intuitive companion.",
                "Norman's vision was to create a system that would lift up his Mississippi community through trading education.",
                "The BITTEN personalities are based on Norman's journey from struggle to success.",
                "Each personality carries a piece of Norman's story, his family's wisdom, and his determination to help others."
            ]
            
            selected_story = random.choice(story_elements)
            
            response = f"""📖 **Norman's Story**

{selected_story}

*Every interaction with BITTEN carries forward Norman's legacy and his dream of creating a supportive trading community.*

Use `/layers` to see how Norman's story is woven through all personality layers."""
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')
        
        logger.info("✅ Unified personality commands registered")
    
    def send_welcome_message(self, chat_id: int, user_tier: str = "NIBBLER"):
        """Send welcome message explaining default voice setup"""
        welcome_text = f"""🎉 **Welcome to BITTEN's Unified Personality System!**

**✅ VOICE MESSAGES ARE ENABLED BY DEFAULT**
• All 3 personality layers will speak to you
• Voice responses include Norman's story elements
• Personalities evolve and adapt as you interact

**🎭 Your Personality Layers:**
• **Adaptive AI**: Learns your trading style
• **Norman's Story**: Deep character with Mississippi wisdom
• **Intel Specialist**: Expert trading guidance

**🎮 Quick Commands:**
• `/voice` - Toggle voice on/off
• `/personality` - View your profile
• `/layers` - See all personality layers

*Your unified personality system is ready to guide your trading journey!*"""
        
        # Send welcome message using unified system
        asyncio.create_task(self.send_unified_message(
            chat_id, welcome_text, user_tier, "welcome_message"
        ))
        
        logger.info(f"✅ Welcome message sent to {chat_id}")
    
    def get_voice_status_for_webapp(self, user_id: str) -> dict:
        """Get voice status formatted for webapp"""
        is_enabled = self.is_voice_enabled(user_id)
        
        return {
            "voice_enabled": is_enabled,
            "status": "enabled" if is_enabled else "disabled",
            "default_state": "enabled",
            "message": "Voice messages are enabled by default. Click to disable." if is_enabled else "Voice messages are disabled. Click to enable."
        }
    
    def format_adaptive_stats(self, stats: dict) -> str:
        """Format adaptive stats for display"""
        if not stats or 'error' in stats:
            return "*No stats available yet*"
        
        return f"""• **Current Mood**: {stats.get('current_mood', 'Unknown')}
• **Interactions**: {stats.get('interaction_count', 0)}
• **Evolution Stage**: {stats.get('evolution_stage', 0):.1%}
• **Evolutions**: {stats.get('evolution_count', 0)}"""
    
    def enhance_message_handler(self, original_handler):
        """Enhance existing message handler with unified personality system"""
        def enhanced_handler(message):
            # Call original handler
            original_result = original_handler(message)
            
            # Add unified personality analysis
            user_id = str(message.from_user.id)
            
            # Schedule async personality analysis
            async def analyze_behavior():
                await self.unified_orchestrator.process_user_interaction(
                    user_id, 
                    message.text or "", 
                    "NIBBLER",  # Default tier
                    "general_message"
                )
            
            # Run in background
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(analyze_behavior())
                loop.close()
            except Exception as e:
                logger.error(f"Background personality analysis failed: {e}")
            
            return original_result
        
        return enhanced_handler

async def test_unified_system():
    """Test the unified personality system"""
    logger.info("🧪 Testing Unified Personality System...")
    
    # Test unified orchestrator
    test_user = "12345"
    
    # Test personality assignment and processing
    response = await unified_orchestrator.process_user_interaction(
        test_user, 
        "I want to execute trades fast and aggressively!", 
        "FANG",
        "trade_request"
    )
    
    logger.info(f"✅ Unified Response Generated:")
    logger.info(f"  Primary: {response.primary_personality}")
    logger.info(f"  Deep Persona: {response.deep_persona}")
    logger.info(f"  Intel Role: {response.intel_role}")
    logger.info(f"  Message: {response.message[:100]}...")
    
    # Test stats
    stats = await unified_orchestrator.get_personality_stats(test_user)
    logger.info(f"✅ Unified Stats: {stats}")
    
    return True

def main():
    """Main deployment function"""
    logger.info("🚀 Deploying Unified Personality System...")
    
    # Test the system first
    success = asyncio.run(test_unified_system())
    
    if success:
        logger.info("✅ Unified Personality System ready for deployment!")
        logger.info("📖 Integration Instructions:")
        logger.info("1. Import: from deploy_unified_personality_system import UnifiedPersonalityBot")
        logger.info("2. Initialize: unified_bot = UnifiedPersonalityBot(your_bot_instance)")
        logger.info("3. Setup commands: unified_bot.setup_unified_commands()")
        logger.info("4. Use: await unified_bot.send_unified_message(chat_id, message, user_tier)")
    else:
        logger.error("❌ Unified system test failed")

if __name__ == "__main__":
    main()