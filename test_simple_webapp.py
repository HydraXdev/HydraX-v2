#!/usr/bin/env python3
"""Test simple WebApp button"""

import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

async def test_webapp():
    bot = Bot("8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k")
    
    # Simple message first
    message = "🔥 SNIPER SHOT\nEURUSD BUY | 87%"
    
    try:
        # Test 1: Simple URL button (not WebApp)
        keyboard1 = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎯 VIEW INTEL", url="https://joinbitten.com/hud")
        ]])
        
        await bot.send_message(
            chat_id="-1002581996861",
            text=f"**TEST 1: URL BUTTON**\n{message}",
            parse_mode='Markdown',
            reply_markup=keyboard1
        )
        print("✅ URL button sent")
        
        await asyncio.sleep(2)
        
        # Test 2: Try WebApp button
        keyboard2 = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🎯 WEBAPP TEST", 
                web_app=WebAppInfo(url="https://joinbitten.com/hud")
            )
        ]])
        
        await bot.send_message(
            chat_id="-1002581996861",
            text=f"**TEST 2: WEBAPP BUTTON**\n{message}",
            parse_mode='Markdown', 
            reply_markup=keyboard2
        )
        print("✅ WebApp button sent")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_webapp())