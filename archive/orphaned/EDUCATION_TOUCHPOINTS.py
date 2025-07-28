#!/usr/bin/env python3
"""
Education Touchpoints for BITTEN
Strategic educational interventions to reduce support needs
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

class EducationTouchpoints:
    """Manages educational content delivery at key moments"""
    
    def __init__(self):
        self.touchpoint_triggers = {
            # Onboarding
            'first_login': self.first_login_education,
            'first_signal': self.first_signal_education,
            'first_trade': self.first_trade_education,
            'first_win': self.first_win_education,
            'first_loss': self.first_loss_education,
            
            # Ongoing education
            'cooldown_start': self.cooldown_education,
            'daily_login': self.daily_tip,
            'losing_streak': self.losing_streak_support,
            'winning_streak': self.winning_streak_caution,
            'tier_upgrade': self.tier_upgrade_education,
            
            # Error prevention
            'low_tcs_warning': self.low_tcs_education,
            'high_risk_warning': self.risk_management_education,
            'news_event_warning': self.news_event_education,
            'weekend_warning': self.weekend_trading_education,
            
            # Feature discovery
            'unused_feature': self.feature_discovery,
            'achievement_near': self.achievement_hint,
            'squad_invite': self.squad_benefits_education
        }
    
    def first_login_education(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """First login - critical onboarding"""
        return {
            'type': 'interactive_tutorial',
            'priority': 'critical',
            'content': {
                'title': "🎖️ Welcome to BITTEN, Recruit!",
                'steps': [
                    {
                        'text': "I'm Drill Sergeant Nexus. I'll make a trader out of you!",
                        'action': 'next'
                    },
                    {
                        'text': "First rule: We trade with DISCIPLINE. Every signal has a TCS score.",
                        'visual': 'tcs_explanation.png',
                        'action': 'next'
                    },
                    {
                        'text': "TCS > 85 = SNIPER shots. These are your best opportunities.",
                        'example': 'signal_example_sniper.png',
                        'action': 'next'
                    },
                    {
                        'text': "You're a NIBBLER - 6 trades daily. Make them count!",
                        'action': 'understood'
                    }
                ],
                'completion_reward': {
                    'xp': 50,
                    'achievement': 'first_briefing'
                }
            },
            'follow_up': 'daily_mission_intro'
        }
    
    def first_signal_education(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """First signal received - explain the interface"""
        return {
            'type': 'overlay_guide',
            'priority': 'high',
            'content': {
                'message': "🎯 Your first signal! Let me explain...",
                'highlights': [
                    {
                        'element': 'tcs_score',
                        'text': f"TCS {signal_data['tcs_score']}% - This is the confidence level"
                    },
                    {
                        'element': 'webapp_button',
                        'text': "Click here to see full intel and FIRE"
                    },
                    {
                        'element': 'expiry_timer',
                        'text': "Signals expire! Act within the time limit"
                    }
                ],
                'tip': "💡 Pro tip: Start with 85+ TCS signals until you're comfortable"
            }
        }
    
    def first_loss_education(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """First loss - critical psychological moment"""
        return {
            'type': 'supportive_message',
            'priority': 'critical',
            'persona': 'doc',  # Captain Aegis
            'content': {
                'message': """Hey soldier, Doc here. 🏥

That loss stings, I know. But here's the truth - even snipers miss sometimes.

What matters is what you do next.""",
                'options': [
                    {
                        'text': "📝 Journal this trade",
                        'action': 'open_journal',
                        'reward_xp': 25
                    },
                    {
                        'text': "📚 Review risk management",
                        'action': 'open_lesson',
                        'lesson_id': 'risk_basics'
                    },
                    {
                        'text': "☕ Take a break",
                        'action': 'start_cooldown',
                        'duration': 30
                    }
                ],
                'follow_up': {
                    'delay': 300,  # 5 minutes
                    'message': "Ready to get back out there? The market's always moving."
                }
            }
        }
    
    def cooldown_education(self, remaining_time: int) -> Dict[str, Any]:
        """Education during cooldown periods"""
        mini_games = [
            {
                'type': 'quiz',
                'title': "Quick Fire Round!",
                'questions': [
                    {
                        'q': "What TCS score indicates a SNIPER shot?",
                        'options': ["75+", "80+", "85+", "90+"],
                        'correct': 2,
                        'explanation': "85+ TCS are SNIPER shots - your highest probability trades!"
                    }
                ],
                'reward_xp': 10
            },
            {
                'type': 'pattern_recognition',
                'title': "Spot the Setup!",
                'image': 'chart_pattern.png',
                'time_limit': 30,
                'reward_xp': 15
            },
            {
                'type': 'risk_calculator',
                'title': "Calculate the Position Size",
                'scenario': {
                    'account': 1000,
                    'risk_percent': 2,
                    'stop_loss_pips': 20
                },
                'reward_xp': 20
            }
        ]
        
        return {
            'type': 'cooldown_activity',
            'content': random.choice(mini_games),
            'message': f"⏰ {remaining_time} minutes left. Let's use this time wisely!"
        }
    
    def losing_streak_support(self, streak_data: Dict[str, Any]) -> Dict[str, Any]:
        """Support during losing streaks"""
        streak_count = streak_data['count']
        
        if streak_count == 3:
            persona = 'drill'
            message = "Three losses? Time to STOP and REASSESS, soldier! No shame in regrouping."
        elif streak_count == 5:
            persona = 'doc'
            message = "Hey, it's Doc. I'm prescribing a mandatory break. The market will be here tomorrow."
        else:
            persona = 'bit'
            message = "*purrs softly* Even the best hunters miss sometimes... 🐾"
        
        return {
            'type': 'intervention',
            'priority': 'critical',
            'persona': persona,
            'content': {
                'message': message,
                'actions': [
                    {
                        'text': "📊 Review my trades",
                        'action': 'analyze_streak'
                    },
                    {
                        'text': "🎮 Play recovery mission",
                        'action': 'recovery_mission'
                    },
                    {
                        'text': "💤 Call it a day",
                        'action': 'end_session'
                    }
                ],
                'lock_trading': streak_count >= 5  # Force break after 5 losses
            }
        }
    
    def daily_tip(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Daily educational tips based on user behavior"""
        
        # Analyze user patterns
        weak_areas = self.analyze_weak_areas(user_profile)
        
        tips_pool = {
            'risk_management': [
                "💡 Never risk more than 2% per trade - it's not about the win, it's about surviving to trade another day.",
                "💡 Your stop loss is your best friend. Respect it like your life depends on it.",
                "💡 Position sizing is 90% of risk management. Get it right!"
            ],
            'psychology': [
                "💡 Feeling FOMO? That's your cue to step back and breathe.",
                "💡 The market rewards patience, not action. Wait for YOUR setup.",
                "💡 Every pro trader has lost money. The difference? They learned from it."
            ],
            'technical': [
                "💡 Higher timeframes = Higher probability. When in doubt, zoom out.",
                "💡 Support becomes resistance. What held before may push back now.",
                "💡 Volume confirms price. No volume? No conviction."
            ],
            'discipline': [
                "💡 Your trading plan is your battle strategy. Stick to it!",
                "💡 Journal every trade. Future you will thank present you.",
                "💡 Consistency beats intensity. Small wins compound."
            ]
        }
        
        # Select relevant tip
        category = weak_areas[0] if weak_areas else random.choice(list(tips_pool.keys()))
        tip = random.choice(tips_pool[category])
        
        return {
            'type': 'daily_tip',
            'content': {
                'tip': tip,
                'category': category,
                'related_lesson': f"lesson_{category}_advanced"
            }
        }
    
    def analyze_weak_areas(self, user_profile: Dict[str, Any]) -> List[str]:
        """Identify areas where user needs education"""
        weak_areas = []
        
        stats = user_profile.get('stats', {})
        
        # Check various metrics
        if stats.get('avg_rr_ratio', 0) < 1.5:
            weak_areas.append('risk_management')
        
        if stats.get('win_rate', 0) < 0.6:
            weak_areas.append('technical')
        
        if stats.get('revenge_trades', 0) > 2:
            weak_areas.append('psychology')
        
        if stats.get('plan_adherence', 100) < 80:
            weak_areas.append('discipline')
        
        return weak_areas
    
    def get_touchpoint(self, trigger: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get appropriate educational content for a trigger"""
        
        if trigger in self.touchpoint_triggers:
            handler = self.touchpoint_triggers[trigger]
            return handler(context)
        
        return None
    
    def format_for_telegram(self, education_content: Dict[str, Any]) -> Dict[str, Any]:
        """Format educational content for Telegram delivery"""
        
        formatted = {
            'text': '',
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        content = education_content['content']
        
        # Build message based on type
        if education_content['type'] == 'interactive_tutorial':
            # Return first step for Telegram
            step = content['steps'][0]
            formatted['text'] = f"*{content['title']}*\n\n{step['text']}"
            
        elif education_content['type'] == 'supportive_message':
            formatted['text'] = content['message']
            
        elif education_content['type'] == 'daily_tip':
            formatted['text'] = content['tip']
        
        # Add inline keyboard if there are options
        if 'options' in content:
            buttons = []
            for opt in content['options']:
                buttons.append([{
                    'text': opt['text'],
                    'callback_data': opt['action']
                }])
            formatted['reply_markup'] = {'inline_keyboard': buttons}
        
        return formatted

# Integration example
async def deliver_education(user_id: int, trigger: str, context: Dict[str, Any]):
    """Deliver education at the right moment"""
    
    touchpoints = EducationTouchpoints()
    education = touchpoints.get_touchpoint(trigger, context)
    
    if education and education['priority'] in ['critical', 'high']:
        # Format and send via Telegram
        formatted = touchpoints.format_for_telegram(education)
        # await bot.send_message(user_id, **formatted)
        
        # Log education delivery
        print(f"📚 Delivered {trigger} education to user {user_id}")