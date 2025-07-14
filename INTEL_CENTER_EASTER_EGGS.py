#!/usr/bin/env python3
"""
Intel Command Center Easter Eggs & Hidden Features
Adds secret menus, achievements, and cultural references
"""

from datetime import datetime, time
from typing import Dict, List, Optional
import random

class IntelCenterEasterEggs:
    """Hidden features and easter eggs for Intel Command Center"""
    
    def __init__(self):
        self.secret_combos = {
            'the cake is a lie': 'portal_mode',
            'show me the money': 'profit_vault',
            'bitten by the bug': 'dev_secrets', 
            'norman lives': 'cat_companion_mode',
            'mississippi magic': 'origin_story_unlock',
            'diamond hands': 'hodl_therapy',
            'wen lambo': 'lambo_calculator',
            'number go up': 'hopium_injection',
            'trust the process': 'zen_mode'
        }
        
        self.konami_code = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
        self.user_sequences = {}  # Track user input sequences
    
    def get_time_based_eggs(self) -> List[Dict]:
        """Get easter eggs based on current time"""
        now = datetime.now()
        current_time = now.time()
        eggs = []
        
        # Midnight protocol (00:00 - 01:00 UTC)
        if time(0, 0) <= current_time <= time(1, 0):
            eggs.append({
                'id': 'midnight_protocol',
                'label': '🌙 MIDNIGHT PROTOCOL', 
                'description': 'The witching hour - special powers activated',
                'rarity': 'legendary'
            })
        
        # Friday vibes (Friday after 20:00)
        if now.weekday() == 4 and current_time >= time(20, 0):
            eggs.append({
                'id': 'friday_vibes',
                'label': '🍻 WEEKEND PREP',
                'description': 'Markets closing, time to celebrate or cry',
                'rarity': 'rare'
            })
        
        # Monday motivation (Monday before 10:00)
        if now.weekday() == 0 and current_time <= time(10, 0):
            eggs.append({
                'id': 'monday_motivation', 
                'label': '💪 MONDAY WARRIOR',
                'description': 'New week, new losses... I mean gains!',
                'rarity': 'common'
            })
        
        return eggs
    
    def get_achievement_locked_eggs(self, user_achievements: List[str]) -> List[Dict]:
        """Get easter eggs unlocked by achievements"""
        eggs = []
        
        if 'master_trader' in user_achievements:
            eggs.append({
                'id': 'elite_vault',
                'label': '🏆 ELITE VAULT',
                'description': 'Secrets only masters know',
                'content': 'The real treasure was the friends we liquidated along the way'
            })
        
        if 'cat_whisperer' in user_achievements:
            eggs.append({
                'id': 'norman_diary',
                'label': '📔 NORMAN\'S DIARY', 
                'description': 'Private thoughts from a truck cat',
                'content': 'Entry 1: Human discovered I can predict markets by knocking things off tables...'
            })
        
        if 'loss_survivor' in user_achievements:
            eggs.append({
                'id': 'trauma_vault',
                'label': '💀 TRAUMA VAULT',
                'description': 'Where blown accounts go to rest',
                'content': 'Remember: It\'s not a loss until you sell... or get margin called'
            })
        
        return eggs
    
    def get_meme_references(self) -> List[Dict]:
        """Get meme and cultural reference easter eggs"""
        return [
            {
                'id': 'hodl_therapy',
                'label': '💎 HODL THERAPY',
                'description': 'Diamond hands support group',
                'responses': [
                    'HODL is not just a strategy, it\'s a way of life',
                    'Paper hands were made for toilet, not trading',
                    'When in doubt, zoom out (and cry privately)'
                ]
            },
            {
                'id': 'wen_lambo',
                'label': '🏎️ WEN LAMBO CALC',
                'description': 'Calculate your path to riches',
                'calculator': True
            },
            {
                'id': 'number_go_up', 
                'label': '📈 NUMBER GO UP',
                'description': 'Pure hopium injection',
                'effect': 'Temporarily increases optimism by 420%'
            },
            {
                'id': 'this_is_fine',
                'label': '🔥 THIS IS FINE',
                'description': 'For when your account is burning',
                'triggers': ['portfolio_down_50_percent']
            }
        ]
    
    def get_developer_secrets(self, user_tier: str) -> List[Dict]:
        """Get developer/admin easter eggs (tier-locked)"""
        if user_tier not in ['apex', 'admin']:
            return []
        
        return [
            {
                'id': 'dev_console',
                'label': '👨‍💻 DEV CONSOLE',
                'description': 'Behind the scenes magic',
                'warning': 'May contain traces of bugs and sarcasm'
            },
            {
                'id': 'feature_graveyard',
                'label': '⚰️ FEATURE GRAVEYARD', 
                'description': 'Ideas that didn\'t make it',
                'content': 'Here lies: Auto-YOLO mode, Revenge trading assistant, Crystal ball indicator'
            },
            {
                'id': 'profit_printer',
                'label': '🖨️ MONEY PRINTER',
                'description': 'Top secret algorithms',
                'disclaimer': 'Warning: May cause unrealistic expectations'
            }
        ]
    
    def check_konami_code(self, user_id: str, input_sequence: List[str]) -> Optional[str]:
        """Check if user entered Konami code"""
        if user_id not in self.user_sequences:
            self.user_sequences[user_id] = []
        
        self.user_sequences[user_id].extend(input_sequence)
        
        # Keep only last 10 inputs
        if len(self.user_sequences[user_id]) > 10:
            self.user_sequences[user_id] = self.user_sequences[user_id][-10:]
        
        # Check if matches Konami code
        if self.user_sequences[user_id] == self.konami_code:
            self.user_sequences[user_id] = []  # Reset
            return 'konami_unlocked'
        
        return None
    
    def get_random_easter_egg(self) -> Dict:
        """Get a random easter egg for spontaneous discovery"""
        eggs = [
            {
                'message': '🐱 Norman says: "Meow" (Translation: "Your risk management is terrible")',
                'type': 'norman_wisdom'
            },
            {
                'message': '🚀 Fun fact: 69% of statistics in trading are made up on the spot',
                'type': 'fake_stat'
            },
            {
                'message': '💡 Pro tip: The best traders are either lying or dead',
                'type': 'dark_humor'
            },
            {
                'message': '🎯 Achievement unlocked: "Found Easter Egg" - You\'re more curious than profitable!',
                'type': 'meta_achievement'
            }
        ]
        
        return random.choice(eggs)
    
    def get_seasonal_content(self) -> List[Dict]:
        """Get seasonal/holiday easter eggs"""
        now = datetime.now()
        month = now.month
        day = now.day
        
        seasonal = []
        
        # Christmas (December)
        if month == 12:
            seasonal.append({
                'id': 'santa_rally',
                'label': '🎄 SANTA RALLY',
                'description': 'Ho ho ho-ly gains!',
                'special_signals': True
            })
        
        # April Fools (April 1st)
        if month == 4 and day == 1:
            seasonal.append({
                'id': 'trust_no_one',
                'label': '😜 TRUST NO ONE',
                'description': 'Especially your indicators today',
                'chaos_mode': True
            })
        
        # Black Friday (Last Friday of November)
        if month == 11 and now.weekday() == 4 and day >= 22:
            seasonal.append({
                'id': 'black_friday',
                'label': '🛍️ BLACK FRIDAY TRADES',
                'description': 'Shopping for pips at discount prices',
                'discount_signals': True
            })
        
        return seasonal

# Integration with main Intel Command Center
def enhance_intel_center_with_eggs():
    """Add easter eggs to existing Intel Command Center"""
    
    additional_menu_items = {
        # Add to BOT CONCIERGE
        'bot_norman_companion': {
            'id': 'norman_companion',
            'label': '🐱 NORMAN',
            'description': 'Chat with the legendary black cat',
            'category': 'speak_to_bot',
            'hidden': False
        },
        
        # Add to EMERGENCY (hidden until triggered)
        'emergency_hodl_therapy': {
            'id': 'hodl_therapy',
            'label': '💎 HODL THERAPY', 
            'description': 'Diamond hands support group',
            'category': 'emergency',
            'hidden': True,
            'trigger': 'major_loss'
        },
        
        # Add to TOOLS
        'tool_wen_lambo': {
            'id': 'wen_lambo_calc',
            'label': '🏎️ WEN LAMBO',
            'description': 'Calculate your path to riches',
            'category': 'tools', 
            'hidden': True,
            'unlock': 'meme_discovery'
        },
        
        # Add to FIELD MANUAL
        'manual_trading_trauma': {
            'id': 'trading_trauma',
            'label': '🧠 TRAUMA RECOVERY',
            'description': 'Heal from major losses',
            'category': 'field_manual',
            'hidden': False
        }
    }
    
    return additional_menu_items

# Secret callback responses
SECRET_RESPONSES = {
    'norman_companion': [
        "🐱 *Norman purrs and knocks your phone off the table*",
        "🐱 Norman: 'Meow meow meow' (Translation: 'Stop revenge trading, human')",
        "🐱 *Norman stares at you judgmentally* You know what you did wrong.",
        "🐱 Norman found this shiny thing: 📈 (He recommends you don't touch it)"
    ],
    
    'dev_secrets': [
        "👨‍💻 Dev Note: 'If you're reading this, you found the secret menu. Congrats!'",
        "🐛 Bug Report: User has too much time on their hands",
        "💡 Feature Idea: Auto-delete user account when they find easter eggs",
        "🤫 Insider Info: The algorithm is just Norman walking across the keyboard"
    ],
    
    'profit_vault': [
        "💰 Secret #1: The house always wins... we just make you feel like you're the house",
        "💎 Secret #2: Diamond hands are just paper hands that forgot how to sell",
        "🚀 Secret #3: Moon is actually just the friends we liquidated along the way",
        "🎯 Secret #4: The real profit was inside you all along (kidding, it's in our wallet)"
    ]
}

if __name__ == "__main__":
    eggs = IntelCenterEasterEggs()
    print("🥚 Intel Command Center Easter Eggs System Ready!")
    print(f"📊 {len(eggs.secret_combos)} secret combinations available")
    print(f"🎮 Konami code detection enabled")
    print(f"🎭 {len(eggs.get_meme_references())} meme references loaded")
    print("🎯 Ready to surprise users with hidden features!")