#!/usr/bin/env python3
"""
🎙️ BITTEN AI Voice Synthesis System
Integrates ElevenLabs API for personality-specific voice generation
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import hashlib
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VoiceSynthesis')

class BITTENVoiceSynthesis:
    """Voice synthesis system for BITTEN personality bots"""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.api_url = "https://api.elevenlabs.io/v1"
        self.voice_cache_dir = Path("/root/HydraX-v2/voice_cache")
        self.voice_cache_dir.mkdir(exist_ok=True)
        
        # Voice IDs for each personality (using ElevenLabs pre-made voices)
        self.voice_mapping = {
            'DRILL_SERGEANT': {
                'voice_id': 'ErXwobaYiN019PkySvjV',  # Antoni - authoritative
                'settings': {
                    'stability': 0.3,  # More variation for drill sergeant
                    'similarity_boost': 0.8,
                    'style': 0.6,  # More expressive
                    'use_speaker_boost': True
                }
            },
            'DOC_AEGIS': {
                'voice_id': 'EXAVITQu4vr4xnSDxMaL',  # Sarah - calm, professional
                'settings': {
                    'stability': 0.8,  # Very stable for doctor
                    'similarity_boost': 0.9,
                    'style': 0.3,  # Less expressive, more clinical
                    'use_speaker_boost': True
                }
            },
            'NEXUS': {
                'voice_id': 'TxGEqnHWrfWFTfGW9XjX',  # Josh - young, technical
                'settings': {
                    'stability': 0.7,
                    'similarity_boost': 0.7,
                    'style': 0.5,  # Balanced
                    'use_speaker_boost': True
                }
            },
            'OVERWATCH': {
                'voice_id': 'VR6AewLTigWG4xSOukaG',  # Arnold - deep, commanding
                'settings': {
                    'stability': 0.6,
                    'similarity_boost': 0.8,
                    'style': 0.4,
                    'use_speaker_boost': True
                }
            },
            'BIT': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - versatile, friendly
                'settings': {
                    'stability': 0.5,  # Dynamic for mascot
                    'similarity_boost': 0.6,
                    'style': 0.8,  # Very expressive
                    'use_speaker_boost': True
                }
            }
        }
        
        # Character limits and usage tracking
        self.monthly_limit = 10000  # Free tier limit
        self.usage_file = self.voice_cache_dir / "usage_tracking.json"
        self.load_usage_tracking()
        
    def load_usage_tracking(self):
        """Load monthly usage tracking"""
        if self.usage_file.exists():
            with open(self.usage_file, 'r') as f:
                self.usage_data = json.load(f)
        else:
            self.usage_data = {
                'current_month': datetime.now().strftime('%Y-%m'),
                'characters_used': 0,
                'requests_made': 0
            }
            self.save_usage_tracking()
    
    def save_usage_tracking(self):
        """Save usage tracking data"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def check_usage_limits(self, text_length: int) -> bool:
        """Check if we're within usage limits"""
        current_month = datetime.now().strftime('%Y-%m')
        
        # Reset counter if new month
        if self.usage_data['current_month'] != current_month:
            self.usage_data = {
                'current_month': current_month,
                'characters_used': 0,
                'requests_made': 0
            }
        
        # Check if adding this text would exceed limit
        if self.usage_data['characters_used'] + text_length > self.monthly_limit:
            logger.warning(f"Monthly character limit reached: {self.usage_data['characters_used']}/{self.monthly_limit}")
            return False
        
        return True
    
    def get_cache_filename(self, text: str, voice: str) -> Path:
        """Generate cache filename for text/voice combination"""
        cache_key = f"{text}_{voice}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.voice_cache_dir / f"{voice}_{cache_hash}.mp3"
    
    async def synthesize_speech(self, text: str, voice_personality: str) -> Optional[bytes]:
        """Synthesize speech for given text and personality"""
        
        # Check API key
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return None
        
        # Check cache first
        cache_file = self.get_cache_filename(text, voice_personality)
        if cache_file.exists():
            logger.info(f"Using cached voice for {voice_personality}")
            with open(cache_file, 'rb') as f:
                return f.read()
        
        # Check usage limits
        if not self.check_usage_limits(len(text)):
            logger.warning("Usage limit reached, returning None")
            return None
        
        # Get voice configuration
        voice_config = self.voice_mapping.get(voice_personality)
        if not voice_config:
            logger.error(f"Unknown voice personality: {voice_personality}")
            return None
        
        # Prepare API request
        url = f"{self.api_url}/text-to-speech/{voice_config['voice_id']}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": voice_config['settings']
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        
                        # Cache the audio
                        with open(cache_file, 'wb') as f:
                            f.write(audio_data)
                        
                        # Update usage tracking
                        self.usage_data['characters_used'] += len(text)
                        self.usage_data['requests_made'] += 1
                        self.save_usage_tracking()
                        
                        logger.info(f"Successfully synthesized {len(text)} chars for {voice_personality}")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Voice synthesis error: {e}")
            return None
    
    async def synthesize_telegram_voice(self, text: str, voice_personality: str) -> Optional[str]:
        """Synthesize and save voice file for Telegram"""
        audio_data = await self.synthesize_speech(text, voice_personality)
        
        if audio_data:
            # Save to temporary file for Telegram upload
            temp_file = self.voice_cache_dir / f"temp_{voice_personality}_{datetime.now().timestamp()}.mp3"
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            return str(temp_file)
        
        return None
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        current_month = datetime.now().strftime('%Y-%m')
        if self.usage_data['current_month'] != current_month:
            # Reset if new month
            self.load_usage_tracking()
        
        return {
            'characters_used': self.usage_data['characters_used'],
            'characters_remaining': self.monthly_limit - self.usage_data['characters_used'],
            'requests_made': self.usage_data['requests_made'],
            'percentage_used': (self.usage_data['characters_used'] / self.monthly_limit) * 100,
            'current_month': self.usage_data['current_month']
        }
    
    def clean_old_cache(self, days: int = 7):
        """Clean cache files older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for cache_file in self.voice_cache_dir.glob("*.mp3"):
            if cache_file.stat().st_mtime < cutoff_time.timestamp():
                cache_file.unlink()
                cleaned += 1
        
        logger.info(f"Cleaned {cleaned} old cache files")
        return cleaned

# Example usage and testing
async def test_voice_synthesis():
    """Test the voice synthesis system"""
    voice_synth = BITTENVoiceSynthesis()
    
    # Test messages for each personality
    test_messages = {
        'DRILL_SERGEANT': "LISTEN UP MAGGOT! Time to execute this trade with military precision!",
        'DOC_AEGIS': "According to my analysis, this trade presents optimal risk-reward parameters.",
        'NEXUS': "Signal detected. Analyzing market matrix. Probability calculations complete.",
        'OVERWATCH': "Target acquired. Preparing for strategic market entry.",
        'BIT': "Hey buddy! Got a sweet trading opportunity for you!"
    }
    
    for personality, message in test_messages.items():
        logger.info(f"\nTesting {personality} voice...")
        audio_file = await voice_synth.synthesize_telegram_voice(message, personality)
        if audio_file:
            logger.info(f"✅ Voice file created: {audio_file}")
        else:
            logger.info(f"❌ Failed to create voice for {personality}")
    
    # Show usage stats
    stats = voice_synth.get_usage_stats()
    logger.info(f"\nUsage Stats: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_voice_synthesis())