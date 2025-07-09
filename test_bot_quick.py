#!/usr/bin/env python3
"""
Quick bot test to check if commands are working
"""

import asyncio
import os
from telegram import Bot
from telegram.error import TelegramError

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1002581996861')


async def test_bot():
    """Test if bot is working"""
    print("🔍 Testing BITTEN Bot...")
    
    try:
        bot = Bot(BOT_TOKEN)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"✅ Bot connected: @{bot_info.username}")
        print(f"   Name: {bot_info.first_name}")
        print(f"   Can read messages: {bot_info.can_read_all_group_messages}")
        
        # Send test message
        print("\n📤 Sending test message...")
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text="🤖 BITTEN Bot Test - Commands should now work!\n\nTry these:\n/ping\n/mode\n/status"
        )
        print(f"✅ Message sent successfully to chat {CHAT_ID}")
        
        # Check for updates
        print("\n📥 Checking for recent commands...")
        updates = await bot.get_updates(limit=10)
        
        if updates:
            print(f"Found {len(updates)} recent updates:")
            for update in updates[-5:]:  # Last 5
                if update.message and update.message.text:
                    print(f"   - {update.message.from_user.username}: {update.message.text}")
        
    except TelegramError as e:
        print(f"❌ Telegram Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    print("BITTEN Bot Quick Test\n")
    asyncio.run(test_bot())