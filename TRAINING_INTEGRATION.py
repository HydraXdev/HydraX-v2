#!/usr/bin/env python3
"""Training System Integration for BITTEN"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

class TrainingIntegration:
    """Manages all training touchpoints and education flow"""
    
    def __init__(self):
        self.education_api_base = "/api/tcs/education"
        self.webapp_base = "http://134.199.204.67:8888"
        
        # Training touchpoints configuration
        self.touchpoints = {
            # Signal viewing
            'signal_view': {
                'nibbler': {
                    'threshold': 3,  # After 3 signals
                    'content': "💡 Tip: Focus on 85%+ TCS signals for best results!",
                    'link': f"{self.webapp_base}/education/nibbler#tcs-basics"
                },
                'fang': {
                    'threshold': 5,
                    'content': "💡 Pro tip: Check market session alignment for better entries",
                    'link': f"{self.webapp_base}/education/fang#session-trading"
                }
            },
            
            # After losses
            'loss_recovery': {
                'all': {
                    'content': "📚 Quick lesson: Why stops are your best friend",
                    'link': f"{self.webapp_base}/education/nibbler#risk-management",
                    'xp_reward': 25
                }
            },
            
            # Cooldown periods
            'cooldown': {
                'nibbler': {
                    'mini_games': [
                        {
                            'title': 'TCS Score Challenge',
                            'description': 'Identify the highest probability setup',
                            'duration': 60,
                            'xp_reward': 15
                        },
                        {
                            'title': 'Risk Calculator',
                            'description': 'Calculate position size in 30 seconds',
                            'duration': 30,
                            'xp_reward': 10
                        }
                    ]
                }
            },
            
            # Daily login
            'daily_login': {
                'all': {
                    'missions': [
                        {
                            'title': 'Sharp Shooter',
                            'description': 'Take only 85%+ TCS signals today',
                            'xp_reward': 50,
                            'achievement': 'sniper_discipline'
                        },
                        {
                            'title': 'Risk Guardian',
                            'description': 'Keep all trades at 2% risk',
                            'xp_reward': 30,
                            'achievement': 'risk_master'
                        }
                    ]
                }
            }
        }
    
    def get_training_endpoints(self) -> Dict[str, str]:
        """Get all training-related endpoints"""
        return {
            'main_education': f"{self.webapp_base}/education/{{tier}}",
            'tcs_tutorial': f"{self.webapp_base}/api/tcs/education/tutorial",
            'quiz': f"{self.webapp_base}/api/tcs/education/quiz",
            'progress': f"{self.webapp_base}/api/tcs/education/progress",
            'achievements': f"{self.webapp_base}/api/achievements",
            'missions': f"{self.webapp_base}/api/missions"
        }
    
    def get_touchpoint_content(self, trigger: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get appropriate training content for a touchpoint"""
        tier = user_data.get('tier', 'nibbler')
        
        if trigger in self.touchpoints:
            touchpoint = self.touchpoints[trigger]
            
            # Get tier-specific or 'all' content
            content = touchpoint.get(tier, touchpoint.get('all', {}))
            
            return {
                'type': trigger,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def format_for_telegram(self, training_content: Dict[str, Any]) -> Dict[str, Any]:
        """Format training content for Telegram delivery"""
        content = training_content['content']
        
        # Build inline keyboard
        keyboard = []
        
        if 'link' in content:
            keyboard.append([{
                'text': '📚 Learn More',
                'url': content['link']
            }])
        
        if 'mini_games' in content:
            for game in content['mini_games'][:2]:  # Show max 2 games
                keyboard.append([{
                    'text': f"🎮 {game['title']}",
                    'callback_data': f"game_{game['title'].lower().replace(' ', '_')}"
                }])
        
        if 'missions' in content:
            keyboard.append([{
                'text': '🎯 View Daily Missions',
                'callback_data': 'view_missions'
            }])
        
        message = content.get('content', '')
        
        if 'xp_reward' in content:
            message += f"\n\n+{content['xp_reward']} XP available!"
        
        return {
            'text': message,
            'reply_markup': {'inline_keyboard': keyboard} if keyboard else None
        }
    
    def create_education_routes(self) -> List[Dict[str, Any]]:
        """Create Flask routes for education endpoints"""
        routes = []
        
        # Main education hub
        routes.append({
            'path': '/education/<tier>',
            'methods': ['GET'],
            'description': 'Main education page for tier'
        })
        
        # API endpoints
        routes.append({
            'path': '/api/tcs/education',
            'methods': ['GET'],
            'description': 'Get TCS education content'
        })
        
        routes.append({
            'path': '/api/tcs/education/quiz',
            'methods': ['POST'],
            'description': 'Submit quiz answers'
        })
        
        routes.append({
            'path': '/api/missions',
            'methods': ['GET'],
            'description': 'Get daily missions'
        })
        
        routes.append({
            'path': '/api/achievements',
            'methods': ['GET'],
            'description': 'Get user achievements'
        })
        
        return routes
    
    def get_cooldown_activity(self, tier: str, remaining_time: int) -> Dict[str, Any]:
        """Get activity for cooldown period"""
        activities = self.touchpoints['cooldown'].get(tier, {}).get('mini_games', [])
        
        if activities:
            # Pick activity based on remaining time
            suitable = [a for a in activities if a['duration'] <= remaining_time]
            if suitable:
                import random
                activity = random.choice(suitable)
                
                return {
                    'type': 'mini_game',
                    'activity': activity,
                    'start_url': f"{self.webapp_base}/game/{activity['title'].lower().replace(' ', '_')}"
                }
        
        # Default: educational content
        return {
            'type': 'education',
            'content': '📚 While you wait, review the last trade setup',
            'url': f"{self.webapp_base}/education/{tier}#recent-trades"
        }
    
    def track_education_event(self, user_id: int, event_type: str, details: Dict[str, Any]):
        """Track education engagement for optimization"""
        # This would write to database
        event = {
            'user_id': user_id,
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log for now
        print(f"Education Event: {json.dumps(event)}")

# Integration helper functions
def inject_education_prompts(signal_data: Dict[str, Any], user_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Add educational prompts to signals based on user performance"""
    
    # Check if user is struggling
    if user_stats.get('recent_win_rate', 1.0) < 0.5:
        signal_data['education_prompt'] = {
            'message': "📚 Struggling? Review TCS factors",
            'link': "http://134.199.204.67:8888/education/nibbler#tcs-factors"
        }
    
    # Check if low TCS signal
    elif signal_data.get('tcs_score', 100) < 75:
        signal_data['education_prompt'] = {
            'message': "⚠️ Low confidence signal - learn why",
            'link': "http://134.199.204.67:8888/education/nibbler#signal-quality"
        }
    
    return signal_data

def create_mission_brief_education_link(tier: str) -> str:
    """Create contextual education link for mission briefs"""
    base_url = "http://134.199.204.67:8888/education"
    
    topics = {
        'nibbler': '#risk-basics',
        'fang': '#advanced-setups',
        'commander': '#market-structure',
        'apex': '#quantum-analysis'
    }
    
    topic = topics.get(tier, '#getting-started')
    return f"{base_url}/{tier}{topic}"

# Quick test
if __name__ == '__main__':
    training = TrainingIntegration()
    
    # Test touchpoint
    user_data = {'tier': 'nibbler', 'signals_viewed': 3}
    content = training.get_touchpoint_content('signal_view', user_data)
    
    if content:
        formatted = training.format_for_telegram(content)
        print("Training Message:", formatted['text'])
        print("Buttons:", formatted.get('reply_markup', {}).get('inline_keyboard', []))