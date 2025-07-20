#!/usr/bin/env python3
"""Voice Demo - Test all BITTEN personality voices"""

import asyncio
import sys
sys.path.insert(0, '/root/HydraX-v2')

from ai_voice_synthesis import BITTENVoiceSynthesis

async def demo_voices():
    voice_synth = BITTENVoiceSynthesis()
    
    demos = {
        'DRILL_SERGEANT': "ATTENTION! New signal detected! This is not a drill, soldier! Execute with precision!",
        'DOC_AEGIS': "Vital signs are stable. Market analysis indicates favorable conditions for entry.",
        'NEXUS': "Processing market data. Quantum analysis complete. Probability matrix favorable.",
        'OVERWATCH': "Tactical assessment complete. All systems green. Proceed with caution.",
        'BIT': "Hey there! I found an awesome trading opportunity just for you!"
    }
    
    print("🎤 BITTEN Voice Demo\n")
    
    for personality, text in demos.items():
        print(f"\n{personality}:")
        print(f'"{text}"')
        
        audio_file = await voice_synth.synthesize_telegram_voice(text, personality)
        if audio_file:
            print(f"✅ Audio saved: {audio_file}")
        else:
            print("❌ Failed to generate audio")
    
    print(f"\n📊 Usage Stats: {voice_synth.get_usage_stats()}")

if __name__ == "__main__":
    asyncio.run(demo_voices())