#!/usr/bin/env python3
"""
🎙️ ElevenLabs Voice Driver for BITTEN Personality System
Enhanced voice generation with personality-specific settings
"""

import os
import json
import asyncio
import aiohttp
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ElevenLabsDriver')

class ElevenLabsVoiceDriver:
    """
    Enhanced ElevenLabs voice driver with personality-specific voice generation
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.api_url = "https://api.elevenlabs.io/v1"
        self.voice_cache_dir = Path("/root/HydraX-v2/voice_cache")
        self.voice_cache_dir.mkdir(exist_ok=True)
        
        # Usage tracking
        self.monthly_limit = 10000  # Free tier limit
        self.usage_file = self.voice_cache_dir / "usage_tracking.json"
        self.load_usage_tracking()
        
        # Performance tracking
        self.performance_file = self.voice_cache_dir / "performance_stats.json"
        self.load_performance_stats()
        
    def load_usage_tracking(self):
        """Load monthly usage tracking"""
        if self.usage_file.exists():
            with open(self.usage_file, 'r') as f:
                data = json.load(f)
                # Ensure all required fields exist
                self.usage_data = {
                    'current_month': data.get('current_month', datetime.now().strftime('%Y-%m')),
                    'characters_used': data.get('characters_used', 0),
                    'requests_made': data.get('requests_made', 0),
                    'cache_hits': data.get('cache_hits', 0),
                    'cache_misses': data.get('cache_misses', 0)
                }
        else:
            self.usage_data = {
                'current_month': datetime.now().strftime('%Y-%m'),
                'characters_used': 0,
                'requests_made': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
            self.save_usage_tracking()
    
    def save_usage_tracking(self):
        """Save usage tracking data"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def load_performance_stats(self):
        """Load performance statistics"""
        if self.performance_file.exists():
            with open(self.performance_file, 'r') as f:
                self.performance_stats = json.load(f)
        else:
            self.performance_stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_response_time': 0.0,
                'personality_usage': {}
            }
            self.save_performance_stats()
    
    def save_performance_stats(self):
        """Save performance statistics"""
        with open(self.performance_file, 'w') as f:
            json.dump(self.performance_stats, f, indent=2)
    
    def check_usage_limits(self, text_length: int) -> bool:
        """Check if we're within usage limits"""
        current_month = datetime.now().strftime('%Y-%m')
        
        # Reset counter if new month
        if self.usage_data['current_month'] != current_month:
            self.usage_data = {
                'current_month': current_month,
                'characters_used': 0,
                'requests_made': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
            self.save_usage_tracking()
        
        # Check if adding this text would exceed limit
        if self.usage_data['characters_used'] + text_length > self.monthly_limit:
            logger.warning(f"Monthly character limit reached: {self.usage_data['characters_used']}/{self.monthly_limit}")
            return False
        
        return True
    
    def get_cache_filename(self, text: str, voice_id: str, voice_settings: Dict) -> Path:
        """Generate cache filename for text/voice combination"""
        # Create cache key from text, voice_id, and settings
        settings_str = json.dumps(voice_settings, sort_keys=True)
        cache_key = f"{text}_{voice_id}_{settings_str}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.voice_cache_dir / f"{voice_id}_{cache_hash}.mp3"
    
    async def generate_voice(self, text: str, voice_id: str, voice_settings: Dict = None) -> Optional[bytes]:
        """Generate voice audio using ElevenLabs API"""
        start_time = datetime.now()
        
        # Check API key
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return None
        
        # Default voice settings if not provided
        if voice_settings is None:
            voice_settings = {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.5,
                "use_speaker_boost": True
            }
        
        # Check cache first
        cache_file = self.get_cache_filename(text, voice_id, voice_settings)
        if cache_file.exists():
            logger.info(f"Using cached voice for {voice_id}")
            self.usage_data['cache_hits'] += 1
            self.save_usage_tracking()
            with open(cache_file, 'rb') as f:
                return f.read()
        
        # Check usage limits
        if not self.check_usage_limits(len(text)):
            logger.warning("Usage limit reached, returning None")
            return None
        
        # Track cache miss
        self.usage_data['cache_misses'] += 1
        
        # Prepare API request
        url = f"{self.api_url}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": voice_settings
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
                        
                        # Update performance stats
                        response_time = (datetime.now() - start_time).total_seconds()
                        self.update_performance_stats(voice_id, response_time, True)
                        
                        logger.info(f"Successfully synthesized {len(text)} chars for {voice_id}")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        self.update_performance_stats(voice_id, 0, False)
                        return None
                        
        except Exception as e:
            logger.error(f"Voice synthesis error: {e}")
            self.update_performance_stats(voice_id, 0, False)
            return None
    
    def update_performance_stats(self, voice_id: str, response_time: float, success: bool):
        """Update performance statistics"""
        self.performance_stats['total_requests'] += 1
        
        if success:
            self.performance_stats['successful_requests'] += 1
            # Update average response time
            current_avg = self.performance_stats['average_response_time']
            total_successful = self.performance_stats['successful_requests']
            self.performance_stats['average_response_time'] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        else:
            self.performance_stats['failed_requests'] += 1
        
        # Track personality usage
        if voice_id not in self.performance_stats['personality_usage']:
            self.performance_stats['personality_usage'][voice_id] = 0
        self.performance_stats['personality_usage'][voice_id] += 1
        
        self.save_performance_stats()
    
    async def generate_personality_voice(self, text: str, personality_config: Dict) -> Optional[str]:
        """Generate voice with personality-specific configuration"""
        voice_id = personality_config.get("voice_id")
        voice_settings = personality_config.get("voice_settings", {})
        
        if not voice_id:
            logger.error("No voice_id provided in personality config")
            return None
        
        # Clean text for voice synthesis
        clean_text = self.clean_text_for_voice(text)
        
        # Generate voice
        audio_data = await self.generate_voice(clean_text, voice_id, voice_settings)
        
        if audio_data:
            # Save to temporary file for Telegram upload
            temp_file = self.voice_cache_dir / f"temp_{voice_id}_{datetime.now().timestamp()}.mp3"
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            return str(temp_file)
        
        return None
    
    def clean_text_for_voice(self, text: str) -> str:
        """Clean text for voice synthesis"""
        # Remove markdown formatting
        clean_text = text.replace('*', '').replace('_', '').replace('`', '')
        clean_text = clean_text.replace('\\n', '. ')
        
        # Remove personality tags
        lines = clean_text.split('\n')
        if lines and any(keyword in lines[0] for keyword in ['DRILL_SERGEANT', 'DOC_AEGIS', 'RECRUITER', 'OVERWATCH', 'STEALTH']):
            clean_text = '\n'.join(lines[1:])
        
        # Limit message length for voice synthesis
        if len(clean_text) > 250:
            clean_text = clean_text[:247] + "..."
        
        return clean_text.strip()
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        current_month = datetime.now().strftime('%Y-%m')
        if self.usage_data['current_month'] != current_month:
            self.load_usage_tracking()
        
        return {
            'characters_used': self.usage_data['characters_used'],
            'characters_remaining': self.monthly_limit - self.usage_data['characters_used'],
            'requests_made': self.usage_data['requests_made'],
            'cache_hits': self.usage_data['cache_hits'],
            'cache_misses': self.usage_data['cache_misses'],
            'cache_hit_rate': (self.usage_data['cache_hits'] / max(1, self.usage_data['cache_hits'] + self.usage_data['cache_misses'])) * 100,
            'percentage_used': (self.usage_data['characters_used'] / self.monthly_limit) * 100,
            'current_month': self.usage_data['current_month']
        }
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return self.performance_stats.copy()
    
    def clean_old_cache(self, days: int = 7) -> int:
        """Clean cache files older than specified days"""
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for cache_file in self.voice_cache_dir.glob("*.mp3"):
            try:
                if cache_file.stat().st_mtime < cutoff_time.timestamp():
                    cache_file.unlink()
                    cleaned += 1
            except OSError:
                pass
        
        logger.info(f"Cleaned {cleaned} old cache files")
        return cleaned
    
    async def test_voice_generation(self, personality_configs: Dict) -> Dict:
        """Test voice generation for all personalities"""
        results = {}
        
        test_message = "Testing BITTEN personality voice system."
        
        for personality_name, config in personality_configs.items():
            logger.info(f"Testing {personality_name} voice...")
            
            start_time = datetime.now()
            audio_file = await self.generate_personality_voice(test_message, config)
            end_time = datetime.now()
            
            results[personality_name] = {
                "success": audio_file is not None,
                "audio_file": audio_file,
                "response_time": (end_time - start_time).total_seconds(),
                "voice_id": config.get("voice_id"),
                "settings": config.get("voice_settings", {})
            }
        
        return results


# Global voice driver instance
voice_driver = ElevenLabsVoiceDriver()