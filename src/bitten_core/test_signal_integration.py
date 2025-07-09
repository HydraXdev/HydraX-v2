"""
Test Signal Integration
Connects test signals with XP, achievements, and daily shots
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .test_signal_system import test_signal_system
from .xp_integration import XPIntegrationManager
from .education_achievements import EducationAchievementSystem

logger = logging.getLogger(__name__)


class TestSignalIntegration:
    """Integrates test signals with other game systems"""
    
    def __init__(self, 
                 xp_manager: Optional[XPIntegrationManager] = None,
                 achievement_system: Optional[EducationAchievementSystem] = None,
                 shot_manager: Optional[Any] = None,
                 telegram_messenger: Optional[Any] = None):
        
        self.test_system = test_signal_system
        self.xp_manager = xp_manager
        self.achievement_system = achievement_system
        self.shot_manager = shot_manager
        self.telegram = telegram_messenger
        
    async def process_test_signal_rewards(self, user_id: str, rewards: Dict[str, Any]):
        """Process all rewards from test signal actions"""
        try:
            messages = []
            
            # Award XP
            if rewards['xp_earned'] > 0 and self.xp_manager:
                try:
                    # Add XP to user's balance
                    self.xp_manager.add_xp(
                        user_id=user_id,
                        amount=rewards['xp_earned'],
                        source="test_signal",
                        description=f"Test signal reward: {rewards.get('message', '')}"
                    )
                    messages.append(f"🌟 +{rewards['xp_earned']} XP")
                    logger.info(f"Awarded {rewards['xp_earned']} XP to user {user_id}")
                except Exception as e:
                    logger.error(f"Error awarding XP: {e}")
            
            # Grant extra shots
            if rewards['extra_shots'] > 0 and self.shot_manager:
                try:
                    # Add extra shots for today
                    self.shot_manager.add_extra_shots(
                        user_id=user_id,
                        shots=rewards['extra_shots'],
                        reason="test_signal_consolation"
                    )
                    messages.append(f"🎯 +{rewards['extra_shots']} extra shot(s) for today!")
                    logger.info(f"Granted {rewards['extra_shots']} extra shots to user {user_id}")
                except Exception as e:
                    logger.error(f"Error granting extra shots: {e}")
            
            # Process achievement
            if rewards['achievement'] and self.achievement_system:
                try:
                    achievement = rewards['achievement']
                    
                    # Unlock the achievement
                    unlock_result = await self.achievement_system.unlock_achievement(
                        user_id=user_id,
                        achievement_id=achievement['id']
                    )
                    
                    if unlock_result.get('newly_unlocked'):
                        messages.append(f"{achievement['badge']} Achievement Unlocked: {achievement['name']}")
                        
                        # Award achievement XP bonus
                        if achievement.get('xp_reward', 0) > 0 and self.xp_manager:
                            self.xp_manager.add_xp(
                                user_id=user_id,
                                amount=achievement['xp_reward'],
                                source="achievement",
                                description=f"Achievement: {achievement['name']}"
                            )
                            messages.append(f"🏆 +{achievement['xp_reward']} XP (Achievement Bonus)")
                    
                    logger.info(f"User {user_id} earned achievement: {achievement['name']}")
                except Exception as e:
                    logger.error(f"Error processing achievement: {e}")
            
            # Send consolidated notification
            if messages and self.telegram:
                try:
                    # Add the main reward message
                    if rewards.get('message'):
                        messages.insert(0, rewards['message'])
                    
                    full_message = "\n\n".join(messages)
                    
                    await self.telegram.send_message(
                        chat_id=user_id,
                        text=f"🎯 **Test Signal Result**\n\n{full_message}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error sending notification: {e}")
            
        except Exception as e:
            logger.error(f"Error processing test signal rewards: {e}")
    
    async def check_and_process_signal_action(self, user_id: str, signal_id: str, 
                                            action: str, trade_result: Optional[str] = None):
        """
        Check if a signal was a test signal and process accordingly
        Returns True if it was a test signal, False otherwise
        """
        try:
            # Check if this is a test signal
            if not signal_id.startswith('TEST_'):
                return False
            
            # Record the action and get rewards
            rewards = self.test_system.record_user_action(
                signal_id=signal_id,
                user_id=user_id,
                action=action,
                trade_result=trade_result
            )
            
            # Process the rewards
            await self.process_test_signal_rewards(user_id, rewards)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking/processing signal action: {e}")
            return False
    
    def get_test_signal_summary(self) -> Dict[str, Any]:
        """Get summary statistics for admin dashboard"""
        try:
            total_users = len(self.test_system.user_stats)
            total_signals = len(self.test_system.signal_history)
            
            if total_signals == 0:
                return {
                    'enabled': self.test_system.config.get('enabled', True),
                    'total_signals_sent': 0,
                    'active_users': 0,
                    'average_pass_rate': 0,
                    'total_xp_awarded': 0,
                    'total_extra_shots': 0,
                    'next_signal_time': self.test_system.next_signal_time.isoformat()
                }
            
            # Calculate aggregates
            total_xp = sum(stats.xp_bonuses_earned for stats in self.test_system.user_stats.values())
            total_shots = sum(stats.extra_shots_earned for stats in self.test_system.user_stats.values())
            
            # Calculate average pass rate
            pass_rates = []
            for stats in self.test_system.user_stats.values():
                if stats.total_received > 0:
                    pass_rates.append(stats.total_passed / stats.total_received * 100)
            
            avg_pass_rate = sum(pass_rates) / len(pass_rates) if pass_rates else 0
            
            return {
                'enabled': self.test_system.config.get('enabled', True),
                'total_signals_sent': total_signals,
                'active_users': total_users,
                'average_pass_rate': round(avg_pass_rate, 1),
                'total_xp_awarded': total_xp,
                'total_extra_shots': total_shots,
                'next_signal_time': self.test_system.next_signal_time.isoformat(),
                'top_detectors': self.test_system.get_leaderboard(3)
            }
            
        except Exception as e:
            logger.error(f"Error getting test signal summary: {e}")
            return {}
    
    def should_show_test_signal_hint(self, user_id: str) -> bool:
        """
        Check if user should see a hint about test signals
        Shows hint to users who have failed multiple test signals
        """
        try:
            stats = self.test_system.user_stats.get(user_id)
            if not stats:
                return False
            
            # Show hint if user has poor pass rate
            if stats.total_received >= 3:
                pass_rate = stats.total_passed / stats.total_received
                if pass_rate < 0.3:  # Less than 30% pass rate
                    return True
            
            # Show hint if attention score is low
            if stats.attention_score < 50:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking hint eligibility: {e}")
            return False


# Create global instance
test_signal_integration = TestSignalIntegration()