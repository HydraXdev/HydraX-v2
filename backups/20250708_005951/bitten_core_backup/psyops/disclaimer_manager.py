# disclaimer_manager.py
# DISCLAIMER AND USER CONTROL SYSTEM
# Ensures users understand the system and have control over their experience

from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class UserConsent:
    """Track user consent and preferences"""
    user_id: str
    disclaimer_accepted: bool
    acceptance_timestamp: Optional[datetime]
    bots_enabled: bool
    bot_preferences: Dict[str, bool]  # Individual bot on/off
    immersion_level: str  # 'full', 'moderate', 'minimal'
    stress_simulation_enabled: bool
    performance_pressure_enabled: bool

class DisclaimerManager:
    """Manages disclaimers and user control settings"""
    
    def __init__(self):
        self.user_consents = {}  # user_id -> UserConsent
        
        # The main disclaimer
        self.primary_disclaimer = """
🛡️ **Terms of Tactical Engagement (User Disclaimer)**

*BITTEN ACTUAL Tactical Trading System*

---

## 🔒 Mission Overview

By accessing and using the BITTEN system, you acknowledge that you are engaging with a **tactical simulation environment** designed for educational, psychological, and experimental purposes in the context of foreign exchange (Forex) trading.

BITTEN is **not a financial advisor**, broker, or licensed asset manager. It does **not guarantee profit**, **eliminate risk**, or provide investment advice.

---

## 🎮 System Behavior

BITTEN includes:

* **Automated and semi-automated trade signal delivery**
* **Gamified XP, badge, and reward systems**
* **Emotionally intelligent bot characters** (DrillBot, MedicBot, OverwatchBot, etc.)
* **Immersive lore and narrative layers** (e.g., Gemini opposition, Stealth Mode)

These elements are **fictional**, **motivational**, and designed to create a psychologically engaging experience — not to manipulate or mislead.

---

## ✅ User Control & Consent

* All trade actions require **your explicit approval** unless you have enabled full-auto Bit Mode.
* You may **opt out of bot-based messaging or XP overlays** at any time.
* No system actions will affect your trading account without user-issued commands or pre-authorized trade modes.
* All decisions are **yours** — BITTEN assists, but does not override.

---

## 💡 Risk Acknowledgment

Forex trading involves significant risk. You may lose all capital. By using BITTEN, you acknowledge:

* You are solely responsible for your trades and financial decisions
* XP, badges, bots, and kill cards are **symbolic tools** and hold no real-world monetary value
* Any loss, gain, or market behavior is **independent of BITTEN's control**

---

## 🧠 Psychological Framework

BITTEN may:

* Adapt tone and messaging based on your behavior and trade performance
* Simulate stress, success, reward, and risk through bot personalities
* Introduce narrative tension or "AI opposition" for immersion

All such features are **optional**, **non-coercive**, and intended to enhance focus, discipline, and engagement — not to deceive or shame.

---

## 📜 Legal Stuff

* BITTEN is a product of **HydraX Dynamics LLC**
* Use of the system constitutes agreement to these Terms
* No part of the system may be copied, rebranded, or resold without express permission

---

## ☑️ Final Word

You're not just trading. You're training.
BITTEN gives you tools, triggers, and feedback — but **you make the decisions.**
Every win, loss, and evolution is **earned**, not given.

Proceed with awareness.
Engage with control.
Stay tactical.

Do you understand and accept these terms?
"""
        
        # Secondary warnings for specific features
        self.feature_warnings = {
            'chaingun_mode': "⚠️ CHAINGUN mode uses progressive risk. Ensure you understand the mechanics.",
            'stress_simulation': "🧠 Stress simulation will create pressure scenarios. Toggle off if uncomfortable.",
            'performance_bots': "🤖 Performance bots may use challenging language. They're designed to motivate, not harm."
        }
        
        # Bot control descriptions
        self.bot_descriptions = {
            'DrillBot': {
                'name': 'DrillBot',
                'role': 'Discipline Coach',
                'description': 'Military-style motivation and discipline enforcement',
                'intensity': 'High',
                'can_disable': True
            },
            'MedicBot': {
                'name': 'MedicBot',
                'role': 'Emotional Support',
                'description': 'Provides comfort and psychological support during losses',
                'intensity': 'Medium',
                'can_disable': True
            },
            'RecruiterBot': {
                'name': 'RecruiterBot',
                'role': 'Community Builder',
                'description': 'Encourages network participation and growth',
                'intensity': 'Low',
                'can_disable': True
            },
            'OverwatchBot': {
                'name': 'OverwatchBot',
                'role': 'Performance Analyst',
                'description': 'Provides detailed performance analysis',
                'intensity': 'Low',
                'can_disable': True
            },
            'StealthBot': {
                'name': 'StealthBot',
                'role': 'Hidden Insights',
                'description': 'Occasional mysterious insights and warnings',
                'intensity': 'Low',
                'can_disable': True
            }
        }
    
    def get_onboarding_disclaimer(self) -> Dict:
        """Get the full onboarding disclaimer"""
        return {
            'type': 'disclaimer',
            'title': '🛡️ Terms of Tactical Engagement',
            'content': self.primary_disclaimer,
            'requires_acceptance': True,
            'options': {
                'accept': {
                    'text': '✅ I understand and accept',
                    'action': 'accept_disclaimer'
                },
                'decline': {
                    'text': '❌ I do not accept',
                    'action': 'exit_onboarding'
                }
            },
            'additional_controls': {
                'bot_toggle': {
                    'label': '🤖 Enable AI Bot Personalities',
                    'default': True,
                    'description': 'You can change this anytime in settings'
                },
                'immersion_level': {
                    'label': '🎮 Immersion Level',
                    'options': ['Full', 'Moderate', 'Minimal'],
                    'default': 'Moderate',
                    'description': 'How intense should the experience be?'
                }
            }
        }
    
    def accept_disclaimer(self, user_id: str, preferences: Dict) -> UserConsent:
        """Record user's acceptance and preferences"""
        
        consent = UserConsent(
            user_id=user_id,
            disclaimer_accepted=True,
            acceptance_timestamp=datetime.now(),
            bots_enabled=preferences.get('bots_enabled', True),
            bot_preferences={
                'DrillBot': preferences.get('DrillBot', True),
                'MedicBot': preferences.get('MedicBot', True),
                'RecruiterBot': preferences.get('RecruiterBot', True),
                'OverwatchBot': preferences.get('OverwatchBot', True),
                'StealthBot': preferences.get('StealthBot', True)
            },
            immersion_level=preferences.get('immersion_level', 'moderate'),
            stress_simulation_enabled=preferences.get('stress_simulation', True),
            performance_pressure_enabled=preferences.get('performance_pressure', True)
        )
        
        self.user_consents[user_id] = consent
        return consent
    
    def get_settings_menu(self, user_id: str) -> Dict:
        """Get the settings menu with bot controls"""
        
        consent = self.user_consents.get(user_id)
        if not consent:
            return {'error': 'User not found'}
        
        return {
            'type': 'settings_menu',
            'title': '⚙️ BITTEN Settings',
            'sections': [
                {
                    'name': 'Bot Controls',
                    'description': 'Enable or disable AI personalities',
                    'controls': [
                        {
                            'type': 'master_toggle',
                            'label': '🤖 All Bots',
                            'current': consent.bots_enabled,
                            'action': 'toggle_all_bots'
                        },
                        {
                            'type': 'separator'
                        }
                    ] + [
                        {
                            'type': 'bot_toggle',
                            'bot': bot_name,
                            'label': f"{info['name']} ({info['role']})",
                            'description': info['description'],
                            'intensity': info['intensity'],
                            'current': consent.bot_preferences.get(bot_name, True),
                            'enabled': consent.bots_enabled,  # Disabled if master is off
                            'action': f'toggle_bot_{bot_name.lower()}'
                        }
                        for bot_name, info in self.bot_descriptions.items()
                    ]
                },
                {
                    'name': 'Immersion Settings',
                    'description': 'Control your experience intensity',
                    'controls': [
                        {
                            'type': 'select',
                            'label': '🎮 Immersion Level',
                            'options': [
                                {'value': 'full', 'label': 'Full (Maximum intensity)'},
                                {'value': 'moderate', 'label': 'Moderate (Balanced)'},
                                {'value': 'minimal', 'label': 'Minimal (Just trading)'}
                            ],
                            'current': consent.immersion_level,
                            'action': 'set_immersion_level'
                        },
                        {
                            'type': 'toggle',
                            'label': '😰 Stress Simulation',
                            'description': 'Simulate trading pressure',
                            'current': consent.stress_simulation_enabled,
                            'action': 'toggle_stress_simulation'
                        },
                        {
                            'type': 'toggle',
                            'label': '📊 Performance Pressure',
                            'description': 'Add competitive elements',
                            'current': consent.performance_pressure_enabled,
                            'action': 'toggle_performance_pressure'
                        }
                    ]
                },
                {
                    'name': 'About',
                    'description': 'System information',
                    'controls': [
                        {
                            'type': 'info',
                            'content': 'All bot personalities are fictional AI constructs designed to enhance your trading experience.'
                        },
                        {
                            'type': 'button',
                            'label': '📄 View Full Disclaimer',
                            'action': 'show_disclaimer'
                        }
                    ]
                }
            ]
        }
    
    def toggle_all_bots(self, user_id: str, enabled: bool) -> Dict:
        """Toggle all bots on/off"""
        
        consent = self.user_consents.get(user_id)
        if not consent:
            return {'error': 'User not found'}
        
        consent.bots_enabled = enabled
        
        # If turning off, disable all individual bots too
        if not enabled:
            for bot in consent.bot_preferences:
                consent.bot_preferences[bot] = False
        else:
            # If turning on, restore previous preferences or default to all on
            for bot in consent.bot_preferences:
                consent.bot_preferences[bot] = True
        
        return {
            'success': True,
            'bots_enabled': enabled,
            'message': f"All bots {'enabled' if enabled else 'disabled'}"
        }
    
    def toggle_individual_bot(self, user_id: str, bot_name: str, enabled: bool) -> Dict:
        """Toggle individual bot on/off"""
        
        consent = self.user_consents.get(user_id)
        if not consent:
            return {'error': 'User not found'}
        
        if bot_name not in consent.bot_preferences:
            return {'error': 'Invalid bot name'}
        
        # Can only toggle if master switch is on
        if not consent.bots_enabled:
            return {
                'error': 'Cannot toggle individual bot',
                'message': 'Enable all bots first'
            }
        
        consent.bot_preferences[bot_name] = enabled
        
        return {
            'success': True,
            'bot': bot_name,
            'enabled': enabled,
            'message': f"{bot_name} {'enabled' if enabled else 'disabled'}"
        }
    
    def set_immersion_level(self, user_id: str, level: str) -> Dict:
        """Set immersion level"""
        
        consent = self.user_consents.get(user_id)
        if not consent:
            return {'error': 'User not found'}
        
        if level not in ['full', 'moderate', 'minimal']:
            return {'error': 'Invalid immersion level'}
        
        consent.immersion_level = level
        
        # Adjust bot behavior based on level
        adjustments = {
            'full': {
                'message': 'Maximum intensity engaged. Prepare for the full experience.',
                'bot_intensity': 1.0,
                'stress_multiplier': 1.2
            },
            'moderate': {
                'message': 'Balanced experience selected.',
                'bot_intensity': 0.7,
                'stress_multiplier': 1.0
            },
            'minimal': {
                'message': 'Minimal mode. Just you and the markets.',
                'bot_intensity': 0.3,
                'stress_multiplier': 0.5
            }
        }
        
        adjustment = adjustments[level]
        
        return {
            'success': True,
            'immersion_level': level,
            'message': adjustment['message'],
            'adjustments': adjustment
        }
    
    def check_bot_permission(self, user_id: str, bot_name: str) -> bool:
        """Check if a specific bot is allowed to interact with user"""
        
        consent = self.user_consents.get(user_id)
        if not consent:
            return False
        
        # Master switch check
        if not consent.bots_enabled:
            return False
        
        # Individual bot check
        return consent.bot_preferences.get(bot_name, True)
    
    def get_user_preferences(self, user_id: str) -> Optional[UserConsent]:
        """Get user's current preferences"""
        return self.user_consents.get(user_id)
    
    def format_bot_control_buttons(self) -> Dict:
        """Format inline keyboard for bot controls in Telegram"""
        
        return {
            'inline_keyboard': [
                [
                    {
                        'text': '🤖 Bot Settings',
                        'callback_data': 'settings_bots'
                    },
                    {
                        'text': '🎮 Immersion',
                        'callback_data': 'settings_immersion'
                    }
                ],
                [
                    {
                        'text': '📄 View Disclaimer',
                        'callback_data': 'show_disclaimer'
                    }
                ]
            ]
        }

# Integration helper for quick menu access
def create_bot_toggle_menu(user_id: str, disclaimer_manager: DisclaimerManager) -> str:
    """Create formatted menu text for Telegram"""
    
    consent = disclaimer_manager.get_user_preferences(user_id)
    if not consent:
        return "❌ Settings not found. Please complete onboarding."
    
    menu_text = "⚙️ **BITTEN Bot Settings**\n\n"
    
    # Master toggle
    master_status = "✅ ON" if consent.bots_enabled else "❌ OFF"
    menu_text += f"**All Bots:** {master_status}\n"
    menu_text += "_Use /bots on or /bots off to toggle all_\n\n"
    
    # Individual bots
    if consent.bots_enabled:
        menu_text += "**Individual Bots:**\n"
        for bot_name, enabled in consent.bot_preferences.items():
            status = "✅" if enabled else "❌"
            bot_info = disclaimer_manager.bot_descriptions.get(bot_name, {})
            menu_text += f"{status} **{bot_name}** - {bot_info.get('role', 'Unknown')}\n"
        
        menu_text += "\n_Use /toggle [botname] to control individual bots_\n"
    else:
        menu_text += "_Individual bot controls disabled when all bots are off_\n"
    
    # Immersion level
    menu_text += f"\n**Immersion Level:** {consent.immersion_level.title()}\n"
    menu_text += "_Use /immersion [full/moderate/minimal] to adjust_\n"
    
    # Footer
    menu_text += "\n📄 _All characters are fictional. Use /disclaimer to review._"
    
    return menu_text