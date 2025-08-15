# 🎙️ BITTEN Voice System Documentation

**Created**: July 15, 2025  
**Status**: Implementation Complete - Awaiting API Key  
**Integration**: ElevenLabs Text-to-Speech API

---

## 📋 Overview

The BITTEN Voice System adds personality-specific voice synthesis to bot messages, giving each personality a unique voice that matches their character. This enhances user engagement and creates a more immersive trading experience.

---

## 🎭 Voice Personalities

Each BITTEN personality has a carefully selected voice:

1. **DRILL_SERGEANT** 🔥
   - Voice: Antoni (Authoritative)
   - Style: Low stability (0.3) for variation, high expressiveness
   - Character: Commanding military instructor

2. **DOC_AEGIS** 🩺
   - Voice: Sarah (Professional)
   - Style: High stability (0.8) for calm delivery
   - Character: Medical professional with clinical precision

3. **NEXUS** 📡
   - Voice: Josh (Technical)
   - Style: Balanced settings for clear technical communication
   - Character: Young tech analyst

4. **OVERWATCH** 🎯
   - Voice: Arnold (Commanding)
   - Style: Deep, strategic commander voice
   - Character: Tactical operations leader

5. **BIT** 👾
   - Voice: Adam (Friendly)
   - Style: High expressiveness (0.8) for mascot energy
   - Character: Enthusiastic trading companion

---

## 🔧 Implementation Details

### Core Components

1. **`ai_voice_synthesis.py`** - Main voice synthesis module
   - ElevenLabs API integration
   - Voice caching system
   - Usage tracking (10k chars/month free tier)
   - Personality-specific voice settings

2. **`update_bot_with_voice.py`** - Bot integration module
   - Voice toggle per user
   - Automatic message-to-voice conversion
   - Telegram voice message support

3. **`setup_voice_system.py`** - Setup and configuration
   - Dependency installation
   - API key configuration
   - System testing

### Key Features

- **Smart Caching**: Synthesized voices are cached to reduce API calls
- **Usage Tracking**: Monitors character usage against free tier limits
- **User Preferences**: Each user can toggle voice on/off
- **Automatic Cleanup**: Removes markdown before synthesis
- **Length Limiting**: Truncates long messages to save characters

---

## 🚀 Setup Instructions

### 1. Get ElevenLabs API Key

1. Visit https://elevenlabs.io
2. Create a free account
3. Go to Profile → API Keys
4. Copy your API key

### 2. Configure API Key

Run the setup script:
```bash
python3 /root/HydraX-v2/setup_voice_system.py
```

Or manually add to `.env`:
```
ELEVENLABS_API_KEY=your_api_key_here
```

### 3. Test Voice System

Run the demo to test all voices:
```bash
python3 /root/HydraX-v2/voice_demo.py
```

---

## 🤖 Bot Integration

### Method 1: Automatic Patch

In your bot startup code:
```python
from update_bot_with_voice import apply_voice_patch
apply_voice_patch()
```

### Method 2: Manual Integration

```python
from update_bot_with_voice import VoiceEnabledPersonalityBot

# In your bot initialization
voice_bot = VoiceEnabledPersonalityBot(bot)
voice_bot.setup_voice_commands()
```

---

## 📱 User Commands

- **`/voice`** - Toggle voice messages on/off
- **`/voicestats`** - Check voice usage statistics

---

## 📊 Usage Limits

**Free Tier**: 10,000 characters/month
- ~50 average messages
- Resets monthly
- Cached messages don't count

**Character Optimization**:
- Messages truncated to 200 chars
- Markdown removed before synthesis
- Common phrases cached

---

## 🔍 Troubleshooting

### No Voice Output
1. Check API key is configured
2. Verify monthly character limit not exceeded
3. Check user has voice enabled (`/voice`)

### API Errors
- **401**: Invalid API key
- **429**: Rate limit exceeded
- **500**: ElevenLabs server issue

### Cache Issues
Clean old cache files:
```python
voice_synth.clean_old_cache(days=7)
```

---

## 📁 File Structure

```
/root/HydraX-v2/
├── ai_voice_synthesis.py         # Core voice synthesis
├── update_bot_with_voice.py      # Bot integration
├── setup_voice_system.py         # Setup script
├── voice_demo.py                 # Demo all voices
├── voice_cache/                  # Cached audio files
│   ├── usage_tracking.json       # Usage statistics
│   └── *.mp3                     # Cached voices
└── data/
    └── voice_settings.json       # User preferences
```

---

## 🎯 Next Steps

1. **Add API Key**: Run setup script to configure
2. **Test Voices**: Run demo to hear all personalities
3. **Enable in Bot**: Apply patch to personality bot
4. **Monitor Usage**: Check `/voicestats` regularly

---

## 💡 Tips

- Use voice for important alerts only to conserve characters
- Cache common phrases by using consistent wording
- Consider paid tier ($5/month) for 30k characters
- Clean cache weekly to save disk space

---

## 🔒 Security

- API key stored in environment variables
- No sensitive data in voice messages
- Audio files cleaned after sending
- User preferences stored locally

---

*Voice synthesis ready for deployment. Just add API key!*