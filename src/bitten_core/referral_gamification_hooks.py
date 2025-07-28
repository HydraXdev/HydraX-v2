#!/usr/bin/env python3
"""
BITTEN Referral Gamification Hooks
Integrates referral success with XP system and military progression
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class RecruitmentBadge(Enum):
    """Recruitment badges for successful referrals"""
    RECRUITER = 1           # 🥉 First successful referral
    SQUAD_BUILDER = 5       # 🥈 5 successful referrals  
    ELITE_RECRUITER = 10    # 🥇 10 successful referrals
    RECRUITMENT_MASTER = 25 # ⭐ 25 successful referrals
    LEGENDARY_RECRUITER = 50 # 👑 50+ successful referrals

class ReferralGamificationHooks:
    """Gamification integration for referral system"""
    
    def __init__(self):
        self.badge_rewards = {
            RecruitmentBadge.RECRUITER: {
                'xp': 100,
                'badge': '🥉 RECRUITER',
                'title': 'Recruiter',
                'message': 'First recruitment success! You\'re building your squad.'
            },
            RecruitmentBadge.SQUAD_BUILDER: {
                'xp': 500,
                'badge': '🥈 SQUAD_BUILDER',
                'title': 'Squad Builder',
                'message': 'You\'re building a solid recruitment foundation!',
                'war_room_unlock': 'RECRUITMENT_DASHBOARD'
            },
            RecruitmentBadge.ELITE_RECRUITER: {
                'xp': 1000,
                'badge': '🥇 ELITE_RECRUITER',
                'title': 'Elite Recruiter',
                'message': 'Double-digit recruits! You\'re becoming a recruitment specialist.',
                'special_privilege': 'ADVANCED_REFERRAL_ANALYTICS'
            },
            RecruitmentBadge.RECRUITMENT_MASTER: {
                'xp': 2500,
                'badge': '⭐ RECRUITMENT_MASTER',
                'title': 'Recruitment Master',
                'message': 'Quarter-century of successful recruits! You\'re a master of the craft.',
                'special_privilege': 'RECRUITMENT_LEADERBOARD_FEATURES'
            },
            RecruitmentBadge.LEGENDARY_RECRUITER: {
                'xp': 5000,
                'badge': '👑 LEGENDARY_RECRUITER',
                'title': 'Legendary Recruiter',
                'message': 'LEGENDARY STATUS: 50+ recruits! You\'re in the hall of fame.',
                'special_privilege': 'RECRUITMENT_HALL_OF_FAME',
                'legendary_status': True
            }
        }
    
    def trigger_referral_success_rewards(self, referrer_id: str, referral_count: int) -> Dict:
        """Trigger rewards when a referral is successfully confirmed"""
        rewards = {
            'xp_gained': 0,
            'badges_earned': [],
            'milestones_reached': [],
            'bonus_missions_unlocked': [],
            'special_privileges': [],
            'notifications': []
        }
        
        # Base XP for successful referral
        base_xp = 50
        rewards['xp_gained'] += base_xp
        rewards['notifications'].append(f"🎉 +{base_xp} XP for successful recruitment!")
        
        # Check for badge achievements
        badge = self._get_badge_for_count(referral_count)
        if badge:
            badge_reward = self.badge_rewards[badge]
            
            # Add badge XP
            badge_xp = badge_reward['xp']
            rewards['xp_gained'] += badge_xp
            
            # Add badge
            rewards['badges_earned'].append(badge_reward['badge'])
            
            # Add badge notification  
            rewards['milestones_reached'].append(badge.name)
            rewards['notifications'].append(
                f"🏆 BADGE EARNED: {badge_reward['badge']} (+{badge_xp} XP)"
            )
            rewards['notifications'].append(
                f"💬 {badge_reward['message']}"
            )
            
            # Add special privileges
            if 'special_privilege' in badge_reward:
                rewards['special_privileges'].append(badge_reward['special_privilege'])
                rewards['notifications'].append(
                    f"⭐ SPECIAL FEATURE UNLOCKED: {badge_reward['special_privilege']}"
                )
            
            # War room unlock
            if 'war_room_unlock' in badge_reward:
                rewards['notifications'].append(
                    f"🏛️ WAR ROOM FEATURE UNLOCKED: {badge_reward['war_room_unlock']}"
                )
            
            # Legendary status
            if badge_reward.get('legendary_status'):
                rewards['notifications'].append(
                    f"👑 LEGENDARY STATUS ACHIEVED: Recruitment Hall of Fame!"
                )
        
        # Apply multipliers for high-performing recruiters
        if referral_count >= 10:
            multiplier = min(1.5, 1.0 + (referral_count - 10) * 0.05)  # Up to 1.5x
            bonus_xp = int(base_xp * (multiplier - 1.0))
            rewards['xp_gained'] += bonus_xp
            rewards['notifications'].append(
                f"🔥 VETERAN RECRUITER BONUS: +{bonus_xp} XP ({multiplier:.1f}x multiplier)"
            )
        
        logger.info(f"Referral rewards for {referrer_id}: {rewards}")
        return rewards
    
    def trigger_credit_milestone_rewards(self, user_id: str, total_credits_earned: float) -> Dict:
        """Trigger rewards based on total credits earned"""
        rewards = {
            'xp_gained': 0,
            'badges_earned': [],
            'notifications': []
        }
        
        # Credit-based milestones (every $50 in credits = special recognition)
        credit_milestones = [50, 100, 250, 500, 1000]
        
        for milestone in credit_milestones:
            if total_credits_earned >= milestone and total_credits_earned < milestone + 10:
                # Just hit this milestone
                xp_reward = milestone // 10  # $50 = 5 XP, $100 = 10 XP, etc.
                rewards['xp_gained'] += xp_reward
                
                badge_name = f"CREDIT_MASTER_{milestone}"
                rewards['badges_earned'].append(badge_name)
                
                rewards['notifications'].append(
                    f"💰 CREDIT MILESTONE: ${milestone} total earned! (+{xp_reward} XP)"
                )
                
                if milestone >= 500:
                    rewards['notifications'].append(
                        f"🌟 ELITE EARNER STATUS: You've earned ${milestone} in referral credits!"
                    )
        
        return rewards
    
    def _get_badge_for_count(self, count: int) -> Optional[RecruitmentBadge]:
        """Get the badge that matches the exact count"""
        for badge in RecruitmentBadge:
            if badge.value == count:
                return badge
        return None
    
    def get_recruitment_progress(self, referral_count: int) -> Dict:
        """Get progress toward next recruitment badge"""
        next_badge = None
        current_badge = None
        
        # Find current and next badges
        for badge in sorted(RecruitmentBadge, key=lambda x: x.value):
            if referral_count >= badge.value:
                current_badge = badge
            elif referral_count < badge.value and next_badge is None:
                next_badge = badge
                break
        
        progress = {
            'current_badge': current_badge.name if current_badge else None,
            'current_title': self.badge_rewards[current_badge]['title'] if current_badge else 'New Recruit',
            'next_badge': next_badge.name if next_badge else None,
            'next_title': self.badge_rewards[next_badge]['title'] if next_badge else 'Legendary Recruiter',
            'progress_count': referral_count,
            'next_target': next_badge.value if next_badge else 50,
            'remaining': (next_badge.value - referral_count) if next_badge else 0
        }
        
        return progress
    
    def generate_recruitment_motivation_message(self, referral_count: int, pending_count: int = 0) -> str:
        """Generate motivational message based on recruitment progress"""
        progress = self.get_recruitment_progress(referral_count)
        
        if referral_count == 0:
            return """🎖️ **READY TO BUILD YOUR SQUAD?**

Start recruiting fellow traders and earn:
• $10 credit per successful recruit
• XP rewards and military badges
• Unlock special war room features

Share your referral link and begin your rise through the ranks!"""
        
        elif referral_count < 5:
            remaining = 5 - referral_count
            return f"""🔥 **BUILDING MOMENTUM!**

**Current Rank:** {progress['current_title']}
**Recruits:** {referral_count}/5 for next promotion

You're {remaining} recruits away from **Squad Builder** status!
Keep sharing your link to unlock advanced recruitment features."""
        
        elif referral_count < 10:
            remaining = 10 - referral_count
            return f"""⚡ **STRONG LEADERSHIP!**

**Current Rank:** {progress['current_title']}
**Recruits:** {referral_count}/10 for next promotion

Only {remaining} more recruits to become a **Platoon Leader**!
Your recruitment skills are becoming legendary."""
        
        elif referral_count < 25:
            remaining = 25 - referral_count
            return f"""👑 **ELITE RECRUITER!**

**Current Rank:** {progress['current_title']}
**Recruits:** {referral_count}/25 for next promotion

{remaining} recruits away from **Company Commander** rank!
You're in the top tier of BITTEN recruiters."""
        
        else:
            return f"""🌟 **LEGENDARY STATUS!**

**Current Rank:** {progress['current_title']}
**Total Recruits:** {referral_count}

You've achieved elite recruitment status! Your squad-building mastery is unmatched in the BITTEN academy."""
    
    def create_war_room_recruitment_widget(self, user_id: str, stats: Dict) -> Dict:
        """Create war room widget data for recruitment dashboard"""
        balance = stats['balance']
        progress = self.get_recruitment_progress(balance.referral_count)
        
        widget = {
            'title': '🎖️ RECRUITMENT COMMAND CENTER',
            'current_rank': progress['current_title'],
            'recruitment_stats': {
                'total_recruits': balance.referral_count,
                'credits_earned': balance.applied_credits + balance.total_credits,
                'pending_credits': balance.pending_credits,
                'free_months_earned': int((balance.applied_credits + balance.total_credits) // 39)
            },
            'progress_bar': {
                'current': balance.referral_count,
                'target': progress['next_target'],
                'percentage': min(100, (balance.referral_count / progress['next_target']) * 100) if progress['next_target'] > 0 else 100
            },
            'next_badge': {
                'title': progress['next_title'],
                'remaining': progress['remaining'],
                'rewards': self.badge_rewards.get(self._get_badge_for_count(progress['next_target']), {})
            },
            'recent_activity': stats.get('recent_referrals', [])[:3],  # Last 3 referrals
            'quick_actions': [
                {'label': 'Get Referral Link', 'action': 'generate_link'},
                {'label': 'View Full Stats', 'action': 'detailed_stats'},
                {'label': 'Share on Telegram', 'action': 'share_telegram'}
            ]
        }
        
        return widget

# Global instance
_referral_gamification = None

def get_referral_gamification_hooks() -> ReferralGamificationHooks:
    """Get global referral gamification hooks instance"""
    global _referral_gamification
    if _referral_gamification is None:
        _referral_gamification = ReferralGamificationHooks()
    return _referral_gamification