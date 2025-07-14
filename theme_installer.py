#!/usr/bin/env python3
"""
BITTEN Military Theme Installer
Handles theme distribution and installation for users
"""

import os
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

class BITTENThemeInstaller:
    def __init__(self):
        self.theme_file_path = "/root/HydraX-v2/bitten_military.attheme"
        self.theme_name = "BITTEN Military Theme"
        
    async def send_theme_installer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send theme installation options to user"""
        
        # Read the theme file
        try:
            with open(self.theme_file_path, 'rb') as theme_file:
                theme_data = theme_file.read()
        except FileNotFoundError:
            await update.message.reply_text("❌ Military theme not available. Contact support.")
            return
        
        # Create installation message
        message_text = """🎖️ **BITTEN MILITARY THEME**

Transform your Telegram into a tactical command interface!

**Features:**
✅ Dark military color scheme
✅ Tactical green accents  
✅ Combat-ready interface
✅ Optimized for all devices

**Installation:**
1. Tap the button below
2. Choose "Apply Theme"
3. Your Telegram transforms instantly!

Ready to deploy, Commander?"""

        # Create inline keyboard with theme file
        keyboard = [
            [InlineKeyboardButton("🎨 INSTALL MILITARY THEME", 
                                callback_data="install_theme")],
            [InlineKeyboardButton("📱 Installation Help", 
                                callback_data="theme_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send with theme file
        try:
            await update.message.reply_document(
                document=open(self.theme_file_path, 'rb'),
                filename="bitten_military.attheme",
                caption=message_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            # Fallback to text message with instructions
            await update.message.reply_text(
                message_text + "\n\n⚠️ Theme file available on request. Use /theme_help for manual installation.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def handle_theme_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle theme installation callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "install_theme":
            instructions = """🎖️ **THEME INSTALLATION GUIDE**

**For Android:**
1. Download the .attheme file sent above
2. Tap on the file in Downloads
3. Select "Apply Theme"
4. Confirm installation

**For iPhone/iOS:**
1. Save the .attheme file
2. Open in Telegram app
3. Tap "Apply Theme"
4. Confirm changes

**For Desktop:**
1. Download the theme file
2. Go to Telegram Settings > Chat Settings
3. Click "Choose from file"
4. Select the .attheme file

Your Telegram will instantly transform into a military command interface! 🚁"""

            await query.edit_message_text(
                text=instructions,
                parse_mode='Markdown'
            )
            
        elif query.data == "theme_help":
            help_text = """🛠️ **THEME TROUBLESHOOTING**

**Theme not applying?**
• Make sure you have the latest Telegram version
• Try restarting Telegram after installation
• Some custom themes require Android 6.0+

**Want to revert?**
• Go to Settings > Chat Settings > Chat Background
• Select "Default" or choose another theme

**Need support?**
Contact @BITTENSupport for assistance.

**Pro tip:** Screenshots look even cooler with the military theme when sharing your trading wins! 📸"""

            keyboard = [
                [InlineKeyboardButton("🔙 Back to Installation", 
                                    callback_data="install_theme")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=help_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

# Integration function for main bot
async def handle_theme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /theme command"""
    installer = BITTENThemeInstaller()
    await installer.send_theme_installer(update, context)

async def handle_theme_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle theme-related callback queries"""
    installer = BITTENThemeInstaller()
    await installer.handle_theme_callback(update, context)

if __name__ == "__main__":
    print("BITTEN Military Theme Installer Ready")
    print("Theme file:", "/root/HydraX-v2/bitten_military.attheme")