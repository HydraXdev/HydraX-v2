#!/usr/bin/env python3
"""
BITTEN Seamless Signal Flow
Complete solution for smooth signal delivery without external webapps
"""

import asyncio
import json
import time
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ'
CHAT_ID = -1002581996861

# Store signal data in memory (in production, use database)
active_signals = {}

async def send_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a new signal with seamless flow"""
    
    # Create signal data
    signal_id = f'sig_{int(time.time())}'
    signal_data = {
        'id': signal_id,
        'symbol': 'EUR/USD',
        'direction': 'BUY',
        'entry': 1.0850,
        'sl': 1.0830,
        'tp': 1.0880,
        'confidence': 87,
        'risk_pips': 20,
        'reward_pips': 30,
        'expires_at': int(time.time()) + 600
    }
    
    # Store signal
    active_signals[signal_id] = signal_data
    
    # Brief alert message
    message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🎯 VIEW FULL INTEL", callback_data=f"view_{signal_id}")],
        [
            InlineKeyboardButton("🔫 QUICK FIRE", callback_data=f"quick_{signal_id}"),
            InlineKeyboardButton("❌ SKIP", callback_data=f"skip_{signal_id}")
        ]
    ]
    
    await update.effective_chat.send_message(
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks for seamless experience"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    action, signal_id = query.data.split('_', 1)
    
    # Get signal data
    signal = active_signals.get(signal_id)
    if not signal:
        await query.edit_message_text("⚠️ Signal expired!")
        return
    
    if action == "view":
        # Show full intel
        full_intel = f"""⚡ **TACTICAL MISSION BRIEF** ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 **Asset:** {signal['symbol']}
💹 **Direction:** {signal['direction']}
🎯 **Entry:** {signal['entry']}

📊 **Risk Management:**
• Stop Loss: {signal['sl']} (-{signal['risk_pips']} pips)
• Take Profit: {signal['tp']} (+{signal['reward_pips']} pips)
• Risk/Reward: 1:{signal['reward_pips']/signal['risk_pips']:.1f}

📈 **Technical Confidence:** {signal['confidence']}%
⏰ **Valid for:** {(signal['expires_at'] - int(time.time())) // 60} minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        # New keyboard with execution options
        keyboard = [
            [InlineKeyboardButton("🔫 EXECUTE TRADE", callback_data=f"execute_{signal_id}")],
            [
                InlineKeyboardButton("0.01 lot", callback_data=f"lot_0.01_{signal_id}"),
                InlineKeyboardButton("0.05 lot", callback_data=f"lot_0.05_{signal_id}"),
                InlineKeyboardButton("0.10 lot", callback_data=f"lot_0.10_{signal_id}")
            ],
            [InlineKeyboardButton("⬅️ BACK", callback_data=f"back_{signal_id}")]
        ]
        
        await query.edit_message_text(
            text=full_intel,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "quick":
        # Quick fire with default settings
        await query.edit_message_text(
            text=f"""🔫 **QUICK FIRE EXECUTED!**
━━━━━━━━━━━━━━━━━━━━━━━
{signal['symbol']} {signal['direction']} @ {signal['entry']}
Lot size: 0.01 (default)
━━━━━━━━━━━━━━━━━━━━━━━

✅ Trade sent to MT5
📊 Check /positions for status""",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif action == "skip":
        await query.edit_message_text(
            text="❌ Signal skipped\n\nWaiting for next opportunity..."
        )
    
    elif action == "execute":
        # Execute with selected lot size
        lot_size = context.user_data.get('lot_size', '0.01')
        await query.edit_message_text(
            text=f"""✅ **TRADE EXECUTED!**
━━━━━━━━━━━━━━━━━━━━━━━
{signal['symbol']} {signal['direction']} @ {signal['entry']}
Lot size: {lot_size}
SL: {signal['sl']} | TP: {signal['tp']}
━━━━━━━━━━━━━━━━━━━━━━━

📊 Position opened successfully
💡 Use /positions to monitor""",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif action.startswith("lot_"):
        # Store lot size selection
        lot_size = action.split('_')[1]
        context.user_data['lot_size'] = lot_size
        
        # Update message with confirmation
        keyboard = [
            [InlineKeyboardButton(f"✅ CONFIRM {lot_size} LOT", callback_data=f"execute_{signal_id}")],
            [InlineKeyboardButton("⬅️ CHANGE SIZE", callback_data=f"view_{signal_id}")]
        ]
        
        await query.edit_message_text(
            text=f"""🎯 **READY TO EXECUTE**
━━━━━━━━━━━━━━━━━━━━━━━
{signal['symbol']} {signal['direction']} @ {signal['entry']}
Selected lot size: **{lot_size}**
━━━━━━━━━━━━━━━━━━━━━━━

Confirm execution?""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif action == "back":
        # Go back to initial view
        keyboard = [
            [InlineKeyboardButton("🎯 VIEW FULL INTEL", callback_data=f"view_{signal_id}")],
            [
                InlineKeyboardButton("🔫 QUICK FIRE", callback_data=f"quick_{signal_id}"),
                InlineKeyboardButton("❌ SKIP", callback_data=f"skip_{signal_id}")
            ]
        ]
        
        message = """⚡ **SIGNAL DETECTED**
EUR/USD | BUY | 87% confidence
⏰ Expires in 10 minutes"""
        
        await query.edit_message_text(
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current positions"""
    positions_text = """📊 **ACTIVE POSITIONS**
━━━━━━━━━━━━━━━━━━━━━━━
1. EUR/USD BUY @ 1.0850
   P/L: +12 pips 🟢
   Time: 5 minutes
━━━━━━━━━━━━━━━━━━━━━━━

Total P/L: +$24.50"""
    
    await update.effective_chat.send_message(
        text=positions_text,
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    """Run the seamless bot"""
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("signal", send_signal_command))
    app.add_handler(CommandHandler("positions", positions_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🚀 BITTEN Seamless Bot Started!")
    print("Commands:")
    print("  /signal - Send test signal")
    print("  /positions - View positions")
    print("\nThis creates a completely seamless experience within Telegram!")
    
    # Run bot
    app.run_polling()

if __name__ == "__main__":
    main()