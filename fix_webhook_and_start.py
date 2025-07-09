#!/usr/bin/env python3
"""
Fix webhook issue and start BITTEN signals
"""

import asyncio
import os
from telegram import Bot
import time

BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = '-1002581996861'


async def fix_and_start():
    """Delete webhook and start bot"""
    print("🔧 Fixing webhook issue...")
    
    bot = Bot(BOT_TOKEN)
    
    try:
        # Delete any existing webhook
        print("📡 Deleting webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted successfully")
        
        # Verify webhook is gone
        webhook_info = await bot.get_webhook_info()
        print(f"📊 Webhook status: {webhook_info.url if webhook_info.url else 'No webhook set'}")
        
        # Send confirmation
        await bot.send_message(
            chat_id=CHAT_ID,
            text="✅ **Webhook Fixed!**\n\nBot is ready for polling mode.\nStarting signals now..."
        )
        
        print("\n✅ Bot is ready! Starting signal system...")
        print("=" * 50)
        
        # Small delay before starting main bot
        await asyncio.sleep(2)
        
        # Now start the main signal bot
        print("🚀 Starting BITTEN Signal Bot...")
        import subprocess
        subprocess.run(["python3", "START_SIGNALS_NOW.py"])
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    print("BITTEN Webhook Fix & Start\n")
    asyncio.run(fix_and_start())