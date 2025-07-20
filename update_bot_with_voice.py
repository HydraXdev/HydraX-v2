#!/usr/bin/env python3
"""
🔊 Update BITTEN Personality Bot with Voice Capabilities
Integrates ElevenLabs voice synthesis into existing bot messaging
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Optional
import telebot
from telebot import types
import time

# Add project root to path
sys.path.insert(0, '/root/HydraX-v2')

from ai_voice_synthesis import BITTENVoiceSynthesis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VoiceIntegration')

class VoiceEnabledPersonalityBot:
    """Extension to add voice capabilities to personality bot"""
    
    def __init__(self, bot_instance: telebot.TeleBot):
        self.bot = bot_instance
        self.voice_synth = BITTENVoiceSynthesis()
        self.voice_enabled_users = set()  # Track users who want voice
        self.voice_settings_file = "/root/HydraX-v2/data/voice_settings.json"
        self.load_voice_settings()
        
    def load_voice_settings(self):
        """Load user voice preferences"""
        import json
        if os.path.exists(self.voice_settings_file):
            with open(self.voice_settings_file, 'r') as f:
                data = json.load(f)
                self.voice_enabled_users = set(data.get('enabled_users', []))
        else:
            self.save_voice_settings()
    
    def save_voice_settings(self):
        """Save user voice preferences"""
        import json
        os.makedirs(os.path.dirname(self.voice_settings_file), exist_ok=True)
        with open(self.voice_settings_file, 'w') as f:
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
    
    async def send_voice_message(self, chat_id: int, text: str, voice_personality: str):
        """Send voice message if synthesis successful"""
        try:
            # Synthesize voice
            audio_file = await self.voice_synth.synthesize_telegram_voice(text, voice_personality)
            
            if audio_file and os.path.exists(audio_file):
                # Send as voice message
                with open(audio_file, 'rb') as audio:
                    self.bot.send_voice(
                        chat_id, 
                        audio,
                        caption=f"🎙️ {voice_personality}",
                        duration=None  # Let Telegram calculate
                    )
                
                # Clean up temp file after sending
                os.remove(audio_file)
                logger.info(f"Sent voice message for {voice_personality}")
                return True
            else:
                logger.warning(f"Failed to synthesize voice for {voice_personality}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending voice message: {e}")
            return False
    
    def setup_voice_commands(self):
        """Add voice-related commands to bot"""
        
        @self.bot.message_handler(commands=['voice'])
        def handle_voice_toggle(message):
            """Toggle voice messages on/off"""
            user_id = str(message.from_user.id)
            enabled = self.toggle_voice(user_id)
            
            if enabled:
                response = "🔊 Voice messages ENABLED! You'll now receive audio responses from our personalities."
                # Send a sample voice message
                asyncio.run(self.send_voice_message(
                    message.chat.id,
                    "Voice system activated. Ready to serve, soldier!",
                    "DRILL_SERGEANT"
                ))
            else:
                response = "🔇 Voice messages DISABLED. You'll receive text-only responses."
            
            self.bot.send_message(message.chat.id, response)
        
        @self.bot.message_handler(commands=['voicestats'])
        def handle_voice_stats(message):
            """Show voice synthesis usage stats"""
            stats = self.voice_synth.get_usage_stats()
            
            response = f"""📊 **Voice Usage Statistics**
            
Characters Used: {stats['characters_used']:,} / {self.voice_synth.monthly_limit:,}
Percentage Used: {stats['percentage_used']:.1f}%
Requests Made: {stats['requests_made']}
Characters Remaining: {stats['characters_remaining']:,}
Current Month: {stats['current_month']}

💡 Voice synthesis resets monthly on the free tier."""
            
            self.bot.send_message(message.chat.id, response, parse_mode='Markdown')


def integrate_voice_with_personality_bot(original_send_function):
    """Decorator to add voice capability to send_personality_message"""
    
    voice_bot = None  # Will be initialized with bot instance
    
    def enhanced_send_personality_message(self, chat_id: int, response: Dict):
        """Enhanced version with voice synthesis"""
        
        # Initialize voice bot if needed
        nonlocal voice_bot
        if voice_bot is None:
            voice_bot = VoiceEnabledPersonalityBot(self.bot)
        
        # Call original send function first
        original_send_function(self, chat_id, response)
        
        # Check if user has voice enabled
        user_id = str(chat_id)  # Assuming chat_id = user_id for private chats
        if voice_bot.is_voice_enabled(user_id):
            message = response.get('message', '')
            voice = response.get('voice', 'BIT')
            
            # Clean up message for voice (remove markdown)
            clean_message = message.replace('*', '').replace('_', '').replace('`', '')
            clean_message = clean_message.replace('\\n', '. ')
            
            # Limit message length for voice synthesis
            if len(clean_message) > 200:
                clean_message = clean_message[:197] + "..."
            
            # Send voice asynchronously
            asyncio.create_task(voice_bot.send_voice_message(chat_id, clean_message, voice))
    
    return enhanced_send_personality_message


# Patch the personality bot
def apply_voice_patch():
    """Apply voice capabilities to existing personality bot"""
    try:
        # Import the personality bot module
        import bitten_personality_bot
        
        # Store original function
        original_send = bitten_personality_bot.BittenPersonalityBot.send_personality_message
        
        # Apply enhanced version
        bitten_personality_bot.BittenPersonalityBot.send_personality_message = integrate_voice_with_personality_bot(original_send)
        
        logger.info("✅ Voice capabilities successfully integrated!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply voice patch: {e}")
        return False


# Configuration helper
def setup_elevenlabs_api():
    """Help user set up ElevenLabs API key"""
    print("\n🎙️ BITTEN Voice Setup")
    print("=" * 50)
    
    # Check if API key exists
    if os.getenv('ELEVENLABS_API_KEY'):
        print("✅ ElevenLabs API key detected in environment")
    else:
        print("❌ No ElevenLabs API key found")
        print("\nTo enable voice synthesis:")
        print("1. Sign up for free at https://elevenlabs.io")
        print("2. Get your API key from the profile section")
        print("3. Add to your .env file:")
        print("   ELEVENLABS_API_KEY=your_key_here")
        print("\nFree tier includes 10,000 characters/month")
    
    print("\n📊 Available Voices:")
    print("- DRILL_SERGEANT: Authoritative military commander")
    print("- DOC_AEGIS: Calm medical professional")
    print("- NEXUS: Technical analyst")
    print("- OVERWATCH: Strategic commander")
    print("- BIT: Friendly mascot")
    
    print("\n🔧 Commands:")
    print("/voice - Toggle voice messages on/off")
    print("/voicestats - Check usage statistics")
    print("=" * 50)


if __name__ == "__main__":
    # Show setup instructions
    setup_elevenlabs_api()
    
    # Test voice synthesis if API key exists
    if os.getenv('ELEVENLABS_API_KEY'):
        print("\n🧪 Testing voice synthesis...")
        asyncio.run(test_voice_synthesis())
    else:
        print("\n⚠️ Set up API key to test voice synthesis")