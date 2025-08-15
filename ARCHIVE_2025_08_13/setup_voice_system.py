#!/usr/bin/env python3
"""
🎤 Quick Setup Script for BITTEN Voice System
Run this to configure and test voice synthesis
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_dependencies():
    """Check and install required dependencies"""
    print("🔍 Checking dependencies...")
    
    required_packages = {
        'aiohttp': 'aiohttp',
        'python-dotenv': 'dotenv'
    }
    
    missing = []
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("✅ Dependencies installed")
    
    return True

def setup_api_key():
    """Help user set up ElevenLabs API key"""
    env_file = Path("/root/HydraX-v2/.env")
    
    # Check if API key already exists
    current_key = os.getenv('ELEVENLABS_API_KEY')
    if current_key:
        print(f"✅ API key already configured (ends with ...{current_key[-4:]})")
        return True
    
    # Check .env file
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if 'ELEVENLABS_API_KEY' in content:
                print("✅ API key found in .env file")
                return True
    
    print("\n🔑 ElevenLabs API Key Setup")
    print("=" * 50)
    print("To get your free API key:")
    print("1. Go to https://elevenlabs.io")
    print("2. Sign up for a free account")
    print("3. Go to Profile → API Keys")
    print("4. Copy your API key")
    print("=" * 50)
    
    api_key = input("\nPaste your ElevenLabs API key (or press Enter to skip): ").strip()
    
    if api_key:
        # Add to .env file
        with open(env_file, 'a') as f:
            f.write(f"\n# ElevenLabs Voice Synthesis\nELEVENLABS_API_KEY={api_key}\n")
        
        os.environ['ELEVENLABS_API_KEY'] = api_key
        print("✅ API key saved to .env file")
        return True
    else:
        print("⚠️ Skipping API key setup. Voice synthesis will not work without it.")
        return False

def test_voice_system():
    """Test the voice synthesis system"""
    print("\n🧪 Testing Voice System...")
    
    # Import after dependencies are installed
    from ai_voice_synthesis import BITTENVoiceSynthesis
    
    voice_synth = BITTENVoiceSynthesis()
    
    if not voice_synth.api_key:
        print("❌ No API key configured. Cannot test voice synthesis.")
        return False
    
    # Test a simple message
    test_message = "Testing BITTEN voice system. Ready for trading!"
    
    async def test():
        result = await voice_synth.synthesize_telegram_voice(test_message, "BIT")
        if result:
            print(f"✅ Voice file created: {result}")
            print(f"📊 Usage: {voice_synth.get_usage_stats()}")
            return True
        else:
            print("❌ Voice synthesis failed")
            return False
    
    return asyncio.run(test())

def integrate_with_bot():
    """Show integration instructions"""
    print("\n🤖 Bot Integration Instructions")
    print("=" * 50)
    print("To add voice to your personality bot:")
    print("\n1. Import the voice module in your bot:")
    print("   from update_bot_with_voice import VoiceEnabledPersonalityBot")
    print("\n2. Initialize voice bot with your bot instance:")
    print("   voice_bot = VoiceEnabledPersonalityBot(bot)")
    print("   voice_bot.setup_voice_commands()")
    print("\n3. Or use the automatic patch:")
    print("   from update_bot_with_voice import apply_voice_patch")
    print("   apply_voice_patch()")
    print("\n4. Users can toggle voice with /voice command")
    print("=" * 50)

def create_voice_demo():
    """Create a demo script for voice synthesis"""
    demo_content = '''#!/usr/bin/env python3
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
    
    print("🎤 BITTEN Voice Demo\\n")
    
    for personality, text in demos.items():
        print(f"\\n{personality}:")
        print(f'"{text}"')
        
        audio_file = await voice_synth.synthesize_telegram_voice(text, personality)
        if audio_file:
            print(f"✅ Audio saved: {audio_file}")
        else:
            print("❌ Failed to generate audio")
    
    print(f"\\n📊 Usage Stats: {voice_synth.get_usage_stats()}")

if __name__ == "__main__":
    asyncio.run(demo_voices())
'''
    
    demo_file = Path("/root/HydraX-v2/voice_demo.py")
    demo_file.write_text(demo_content)
    demo_file.chmod(0o755)
    print(f"\n📝 Created voice demo script: {demo_file}")
    print("Run it with: python3 voice_demo.py")

def main():
    """Main setup flow"""
    print("🎙️ BITTEN Voice System Setup")
    print("=" * 50)
    
    # 1. Check dependencies
    if not check_dependencies():
        return
    
    # 2. Setup API key
    has_key = setup_api_key()
    
    # 3. Test voice system
    if has_key:
        test_voice_system()
    
    # 4. Show integration instructions
    integrate_with_bot()
    
    # 5. Create demo script
    create_voice_demo()
    
    print("\n✅ Voice system setup complete!")
    print("\nNext steps:")
    print("1. Run the demo: python3 voice_demo.py")
    print("2. Integrate with your bot using the instructions above")
    print("3. Users can enable voice with /voice command")

if __name__ == "__main__":
    main()