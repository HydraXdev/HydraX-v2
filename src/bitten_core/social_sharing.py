# social_sharing.py
# BITTEN Social Sharing System - Achievement cards and sharing functionality

import json
import time
import base64
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
import io

@dataclass
class AchievementCard:
    """Achievement card data structure"""
    card_id: str
    type: str  # medal, milestone, streak, profit
    title: str
    description: str
    value: Any
    earned_at: int
    user_data: Dict[str, Any]
    visual_style: Dict[str, Any]

class SocialSharingManager:
    """Manages social sharing features for BITTEN achievements"""
    
    def __init__(self):
        # Card templates
        self.card_templates = {
            'medal': {
                'size': (800, 400),
                'background': 'gradient_dark',
                'accent_color': '#f39c12',
                'layout': 'medal_showcase'
            },
            'milestone': {
                'size': (800, 400),
                'background': 'gradient_blue',
                'accent_color': '#3498db',
                'layout': 'milestone_banner'
            },
            'streak': {
                'size': (800, 400),
                'background': 'gradient_fire',
                'accent_color': '#e74c3c',
                'layout': 'streak_flame'
            },
            'profit': {
                'size': (800, 400),
                'background': 'gradient_green',
                'accent_color': '#2ecc71',
                'layout': 'profit_chart'
            },
            'recruitment': {
                'size': (800, 400),
                'background': 'gradient_purple',
                'accent_color': '#9b59b6',
                'layout': 'network_growth'
            }
        }
        
        # Share message templates
        self.message_templates = {
            'medal': {
                'telegram': "🎖️ Just earned the {medal_name} medal on BITTEN! {medal_desc}\n\n🤖 Join the elite trading network: {referral_link}",
                'twitter': "🎖️ Achievement Unlocked: {medal_name}! {medal_desc} #BITTEN #Trading #Achievement",
                'discord': "**🎖️ Achievement Unlocked!**\nJust earned: **{medal_name}**\n{medal_desc}\n\nJoin BITTEN: {referral_link}"
            },
            'milestone': {
                'telegram': "🎯 Milestone reached on BITTEN! {milestone_desc}\n\n📊 Stats: {stats}\n\n🤖 Start your journey: {referral_link}",
                'twitter': "🎯 Milestone Alert! {milestone_desc} #BITTEN #TradingMilestone",
                'discord': "**🎯 Milestone Achieved!**\n{milestone_desc}\n\n📊 {stats}"
            },
            'streak': {
                'telegram': "🔥 On fire with BITTEN! {streak_count} winning trades in a row!\n\n💪 Join the winning team: {referral_link}",
                'twitter': "🔥 {streak_count} trade winning streak! The BITTEN system is unstoppable! #WinningStreak #BITTEN",
                'discord': "**🔥 WINNING STREAK!**\n{streak_count} successful trades in a row!"
            },
            'profit': {
                'telegram': "💰 Profit milestone with BITTEN! Total earnings: ${profit_amount}\n\n📈 Start earning: {referral_link}",
                'twitter': "💰 Reached ${profit_amount} in profits with @BITTEN_bot! #ProfitMilestone #Trading",
                'discord': "**💰 PROFIT MILESTONE!**\nTotal Earnings: **${profit_amount}**"
            }
        }
        
        # Visual elements
        self.visual_elements = {
            'logos': {
                'bitten': self._get_bitten_logo(),
                'watermark': self._get_watermark()
            },
            'gradients': {
                'gradient_dark': ['#0a0a0a', '#1a1a1a', '#2a2a2a'],
                'gradient_blue': ['#2c3e50', '#3498db', '#5dade2'],
                'gradient_fire': ['#c0392b', '#e74c3c', '#ec7063'],
                'gradient_green': ['#27ae60', '#2ecc71', '#58d68d'],
                'gradient_purple': ['#8e44ad', '#9b59b6', '#bb8fce']
            },
            'fonts': {
                'title': {'size': 48, 'weight': 'bold'},
                'subtitle': {'size': 32, 'weight': 'medium'},
                'body': {'size': 24, 'weight': 'regular'},
                'stats': {'size': 36, 'weight': 'bold'}
            }
        }
    
    def create_achievement_card(self, achievement_type: str, achievement_data: Dict) -> AchievementCard:
        """Create an achievement card for sharing"""
        card_id = f"{achievement_type}_{int(time.time())}_{achievement_data.get('user_id', 0)}"
        
        # Get template
        template = self.card_templates.get(achievement_type, self.card_templates['medal'])
        
        # Build card data
        card = AchievementCard(
            card_id=card_id,
            type=achievement_type,
            title=achievement_data.get('title', 'Achievement Unlocked'),
            description=achievement_data.get('description', ''),
            value=achievement_data.get('value'),
            earned_at=int(time.time()),
            user_data={
                'user_id': achievement_data.get('user_id'),
                'username': achievement_data.get('username', 'Anonymous'),
                'rank': achievement_data.get('rank', 'USER'),
                'avatar': achievement_data.get('avatar', '🤖')
            },
            visual_style=template
        )
        
        return card
    
    def generate_card_image(self, card: AchievementCard) -> bytes:
        """Generate visual achievement card image"""
        if not PIL_AVAILABLE:
            # Return empty bytes if PIL not available
            return b'CARD_IMAGE_PLACEHOLDER'
        
        # Get template settings
        width, height = card.visual_style['size']
        
        # Create image
        img = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(img)
        
        # Apply gradient background
        self._apply_gradient(img, draw, card.visual_style['background'])
        
        # Add BITTEN branding
        self._add_branding(draw, width, height)
        
        # Add achievement content based on type
        if card.type == 'medal':
            self._draw_medal_card(draw, card, width, height)
        elif card.type == 'milestone':
            self._draw_milestone_card(draw, card, width, height)
        elif card.type == 'streak':
            self._draw_streak_card(draw, card, width, height)
        elif card.type == 'profit':
            self._draw_profit_card(draw, card, width, height)
        else:
            self._draw_generic_card(draw, card, width, height)
        
        # Add user info
        self._add_user_info(draw, card, width, height)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    def generate_share_content(self, card: AchievementCard, platform: str, referral_link: str) -> Dict[str, Any]:
        """Generate platform-specific share content"""
        # Get message template
        templates = self.message_templates.get(card.type, self.message_templates['medal'])
        message_template = templates.get(platform, templates['telegram'])
        
        # Build context for template
        context = {
            'referral_link': referral_link,
            'username': card.user_data['username'],
            'rank': card.user_data['rank']
        }
        
        # Add type-specific context
        if card.type == 'medal':
            context.update({
                'medal_name': card.title,
                'medal_desc': card.description
            })
        elif card.type == 'milestone':
            context.update({
                'milestone_desc': card.description,
                'stats': f"{card.value} completed"
            })
        elif card.type == 'streak':
            context.update({
                'streak_count': card.value
            })
        elif card.type == 'profit':
            context.update({
                'profit_amount': f"{card.value:,.2f}"
            })
        
        # Format message
        message = message_template.format(**context)
        
        # Build share data
        share_data = {
            'message': message,
            'image': None,  # Will be set if image is generated
            'url': referral_link,
            'hashtags': self._get_hashtags(card.type, platform)
        }
        
        # Platform-specific formatting
        if platform == 'telegram':
            share_data['parse_mode'] = 'Markdown'
            share_data['disable_web_page_preview'] = False
        elif platform == 'twitter':
            # Ensure message fits Twitter limit
            if len(message) > 280:
                message = message[:277] + "..."
                share_data['message'] = message
        elif platform == 'discord':
            share_data['embed'] = self._create_discord_embed(card, referral_link)
        
        return share_data
    
    def create_recruitment_card(self, user_data: Dict) -> Dict[str, Any]:
        """Create special recruitment invitation card"""
        recruiter_stats = {
            'total_recruits': user_data.get('total_recruits', 0),
            'active_recruits': user_data.get('active_recruits', 0),
            'total_xp_earned': user_data.get('recruit_xp', 0),
            'rank': user_data.get('rank', 'USER')
        }
        
        # Create custom recruitment card
        card_data = {
            'type': 'recruitment',
            'title': f"Join {user_data.get('username', 'BITTEN')}' Squad!",
            'subtitle': "Elite Trading Network",
            'stats': recruiter_stats,
            'benefits': [
                "🎯 Professional trading signals",
                "💰 Proven profit system",
                "🏆 Exclusive community",
                "📈 Advanced analytics"
            ],
            'cta': "Join Now & Get Bonus XP!",
            'visual_style': {
                'theme': 'elite',
                'accent': '#f39c12',
                'pattern': 'network'
            }
        }
        
        return card_data
    
    def create_leaderboard_card(self, leaderboard_data: Dict, user_position: Dict) -> Dict[str, Any]:
        """Create leaderboard position share card"""
        card_data = {
            'type': 'leaderboard',
            'title': f"#{user_position['rank']} on BITTEN Leaderboard!",
            'timeframe': leaderboard_data.get('timeframe', 'All Time'),
            'metric': leaderboard_data.get('metric', 'Profit'),
            'value': user_position.get('value', 0),
            'top_traders': leaderboard_data.get('top_5', []),
            'percentile': user_position.get('percentile', 0),
            'visual_style': {
                'theme': 'competitive',
                'show_podium': user_position['rank'] <= 3
            }
        }
        
        return card_data
    
    def _apply_gradient(self, img, draw, gradient_name: str):
        """Apply gradient background to image"""
        colors = self.visual_elements['gradients'].get(gradient_name, ['#000000', '#333333'])
        width, height = img.size
        
        # Simple linear gradient
        for i in range(height):
            # Calculate color for this line
            ratio = i / height
            if ratio < 0.5:
                # Blend first two colors
                color = self._blend_colors(colors[0], colors[1], ratio * 2)
            else:
                # Blend second two colors
                color = self._blend_colors(colors[1], colors[2] if len(colors) > 2 else colors[1], (ratio - 0.5) * 2)
            
            draw.line([(0, i), (width, i)], fill=color)
    
    def _blend_colors(self, color1: str, color2: str, ratio: float) -> tuple:
        """Blend two hex colors"""
        # Convert hex to RGB
        c1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        
        # Blend
        blended = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
        return blended
    
    def _add_branding(self, draw: ImageDraw.Draw, width: int, height: int):
        """Add BITTEN branding to card"""
        # Add logo/text in corner
        brand_text = "B.I.T.T.E.N."
        # In production, use actual font loading
        draw.text((20, 20), brand_text, fill='white', font=None)
        
        # Add tagline
        tagline = "Bot-Integrated Tactical Trading Engine"
        draw.text((20, 50), tagline, fill='#888888', font=None)
    
    def _draw_medal_card(self, draw: ImageDraw.Draw, card: AchievementCard, width: int, height: int):
        """Draw medal achievement card"""
        # Medal icon/emoji at center
        medal_y = height // 3
        draw.text((width // 2 - 50, medal_y), card.value.get('icon', '🎖️'), fill='white', font=None)
        
        # Medal name
        title_y = medal_y + 80
        draw.text((width // 2 - 100, title_y), card.title, fill='white', font=None)
        
        # Description
        desc_y = title_y + 40
        draw.text((width // 2 - 150, desc_y), card.description, fill='#cccccc', font=None)
        
        # XP reward
        xp_text = f"+{card.value.get('xp_reward', 0)} XP"
        draw.text((width // 2 - 50, desc_y + 40), xp_text, fill='#f39c12', font=None)
    
    def _draw_milestone_card(self, draw: ImageDraw.Draw, card: AchievementCard, width: int, height: int):
        """Draw milestone achievement card"""
        # Big number at center
        value_text = str(card.value)
        draw.text((width // 2 - 50, height // 3), value_text, fill='white', font=None)
        
        # Milestone description
        draw.text((width // 2 - 100, height // 2), card.description, fill='white', font=None)
    
    def _draw_streak_card(self, draw: ImageDraw.Draw, card: AchievementCard, width: int, height: int):
        """Draw winning streak card"""
        # Flame emoji and streak count
        streak_text = f"🔥 {card.value} WIN STREAK! 🔥"
        draw.text((width // 2 - 100, height // 3), streak_text, fill='white', font=None)
        
        # Motivational text
        draw.text((width // 2 - 80, height // 2), "ON FIRE!", fill='#e74c3c', font=None)
    
    def _draw_profit_card(self, draw: ImageDraw.Draw, card: AchievementCard, width: int, height: int):
        """Draw profit milestone card"""
        # Profit amount
        profit_text = f"${card.value:,.2f}"
        draw.text((width // 2 - 80, height // 3), profit_text, fill='#2ecc71', font=None)
        
        # Label
        draw.text((width // 2 - 100, height // 2), "TOTAL PROFIT", fill='white', font=None)
    
    def _draw_generic_card(self, draw: ImageDraw.Draw, card: AchievementCard, width: int, height: int):
        """Draw generic achievement card"""
        # Title
        draw.text((width // 2 - 100, height // 3), card.title, fill='white', font=None)
        
        # Description
        draw.text((width // 2 - 150, height // 2), card.description, fill='#cccccc', font=None)
    
    def _add_user_info(self, draw: ImageDraw.Draw, card: AchievementCard, width: int, height: int):
        """Add user information to card"""
        # User info at bottom
        user_text = f"{card.user_data['avatar']} {card.user_data['username']} | {card.user_data['rank']}"
        draw.text((20, height - 40), user_text, fill='#888888', font=None)
        
        # Date
        date_text = datetime.fromtimestamp(card.earned_at).strftime("%d %b %Y")
        draw.text((width - 120, height - 40), date_text, fill='#888888', font=None)
    
    def _get_hashtags(self, card_type: str, platform: str) -> List[str]:
        """Get relevant hashtags for sharing"""
        base_hashtags = ['BITTEN', 'Trading', 'ForexTrading', 'Achievement']
        
        type_hashtags = {
            'medal': ['TradingMedal', 'Milestone'],
            'streak': ['WinningStreak', 'TradingSuccess'],
            'profit': ['ProfitMilestone', 'TradingProfit'],
            'milestone': ['TradingMilestone', 'Success']
        }
        
        hashtags = base_hashtags + type_hashtags.get(card_type, [])
        
        if platform == 'twitter':
            return hashtags[:5]  # Limit for Twitter
        
        return hashtags
    
    def _create_discord_embed(self, card: AchievementCard, referral_link: str) -> Dict[str, Any]:
        """Create Discord embed object"""
        embed = {
            'title': card.title,
            'description': card.description,
            'color': int(card.visual_style['accent_color'].replace('#', ''), 16),
            'timestamp': datetime.fromtimestamp(card.earned_at).isoformat(),
            'footer': {
                'text': 'BITTEN Trading Network',
                'icon_url': 'https://example.com/bitten-icon.png'
            },
            'author': {
                'name': card.user_data['username'],
                'icon_url': f"https://example.com/avatar/{card.user_data['user_id']}.png"
            },
            'fields': []
        }
        
        # Add type-specific fields
        if card.type == 'medal':
            embed['fields'].append({
                'name': 'XP Earned',
                'value': f"+{card.value.get('xp_reward', 0)}",
                'inline': True
            })
            embed['fields'].append({
                'name': 'Tier',
                'value': card.value.get('tier', 'Bronze'),
                'inline': True
            })
        elif card.type == 'streak':
            embed['fields'].append({
                'name': 'Streak Count',
                'value': str(card.value),
                'inline': True
            })
        elif card.type == 'profit':
            embed['fields'].append({
                'name': 'Total Profit',
                'value': f"${card.value:,.2f}",
                'inline': True
            })
        
        # Add CTA
        embed['fields'].append({
            'name': 'Join BITTEN',
            'value': f"[Start Trading Now]({referral_link})",
            'inline': False
        })
        
        return embed
    
    def _get_bitten_logo(self) -> str:
        """Get BITTEN logo as base64 or URL"""
        # In production, return actual logo
        return "data:image/png;base64,..."
    
    def _get_watermark(self) -> str:
        """Get watermark for cards"""
        return "BITTEN"
    
    def track_share_event(self, user_id: int, card_id: str, platform: str) -> bool:
        """Track when user shares an achievement"""
        # In production, log to database
        share_event = {
            'user_id': user_id,
            'card_id': card_id,
            'platform': platform,
            'timestamp': int(time.time())
        }
        
        # Award XP for sharing
        share_xp = {
            'telegram': 10,
            'twitter': 15,
            'discord': 10,
            'whatsapp': 5
        }
        
        xp_reward = share_xp.get(platform, 5)
        
        # In production, actually award XP
        print(f"User {user_id} shared {card_id} on {platform}, earned {xp_reward} XP")
        
        return True
    
    def get_share_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's sharing statistics"""
        # In production, fetch from database
        return {
            'total_shares': 0,
            'platforms': {
                'telegram': 0,
                'twitter': 0,
                'discord': 0,
                'whatsapp': 0
            },
            'xp_earned_from_shares': 0,
            'most_shared_achievement': None,
            'share_streak': 0
        }