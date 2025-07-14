#!/usr/bin/env python3
"""
Send lore correction message
"""

import asyncio
from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'
CHAT_ID = -1002581996861

async def send_lore_correction():
    """Send corrected lore information"""
    bot = Bot(token=BOT_TOKEN)
    
    correction_message = """🚨 **LORE CORRECTION - CRITICAL UPDATE**

I made a HUGE error in the character lore! Here's the corrected version:

## ✅ **CORRECT LORE:**

👦 **NORMAN** = The 17-year-old human boy from Mississippi
- The founder and original trader
- Found Bit as an abandoned kitten in a truck
- Still learning and growing as a trader
- Speaks normally (no purring!)

🐱 **BIT** = The legendary black cat (Born In Truck)
- The actual cat companion
- Doesn't purr - he CHIRPS
- Has judgmental personality 
- Walks across keyboards and knocks things over
- True genius behind the operation

## 🔧 **CORRECTED EASTER EGGS:**

✅ **'norman lives'** → Now correctly shows Norman the human boy
✅ **'bit lives'** → NEW easter egg for Bit the cat  
✅ **Bot Concierge Menu** → Now has both 🐱 BIT and 👦 NORMAN options

## 🎯 **Updated Menu Features:**
- **🐱 BIT Companion** - Chat with the legendary black cat (chirps, not purrs)
- **👦 NORMAN Companion** - Chat with the 17-year-old founder from Mississippi

**The lore is now 100% accurate! Try the corrected easter eggs:**
• Type: **'norman lives'** for the human boy
• Type: **'bit lives'** for the cat who chirps

*Sorry for the mix-up - the menu system now has the correct BITTEN lore!*"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=correction_message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    print("✅ Lore correction sent!")
    print("\n🎯 CORRECTED LORE:")
    print("👦 NORMAN = 17-year-old human boy from Mississippi") 
    print("🐱 BIT = Black cat who chirps (Born In Truck)")
    print("\nEaster eggs and menu system updated with correct lore!")

if __name__ == "__main__":
    asyncio.run(send_lore_correction())