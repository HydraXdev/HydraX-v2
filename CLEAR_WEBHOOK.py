#!/usr/bin/env python3
"""
Clear webhook and check bot info to troubleshoot command issues
"""

import asyncio
from telegram import Bot

BOT_TOKEN = '7854827710:AAGsO-vgMpsTOVNu6zoo_-GGJkYQd97Mc5w'

async def clear_webhook_and_check():
    """Clear webhook and check bot status"""
    bot = Bot(token=BOT_TOKEN)
    
    print("🔧 DIAGNOSING BOT ISSUES")
    print("=" * 30)
    
    try:
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot Info: @{me.username} ({me.first_name})")
        
        # Get webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"🔗 Webhook URL: {webhook_info.url}")
        print(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        # Clear webhook if set
        if webhook_info.url:
            print("🧹 Clearing webhook...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook cleared!")
        else:
            print("✅ No webhook set (good for polling)")
            
        # Drop pending updates
        print("🧹 Dropping pending updates...")
        await bot.delete_webhook(drop_pending_updates=True)
        
        print("\n🎯 Bot should now respond to commands")
        print("Try /ping in Telegram now")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(clear_webhook_and_check())