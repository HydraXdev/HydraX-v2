"""
BITTEN Kill Card Generator - Military-Style Trade Achievement Cards
Generates epic visual cards for successful trades with military aesthetics
"""

import os
import io
import qrcode
import hashlib
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from typing import Dict, Any, Optional, Tuple, List
import json
import base64
from dataclasses import dataclass
from enum import Enum


class RankTier(Enum):
    """Military rank tiers based on profit levels"""
    RECRUIT = ("Recruit", 0, 50, "#808080", "⬤")
    PRIVATE = ("Private", 50, 100, "#CD7F32", "⬤⬤")
    CORPORAL = ("Corporal", 100, 250, "#C0C0C0", "⬤⬤⬤")
    SERGEANT = ("Sergeant", 250, 500, "#FFD700", "★")
    LIEUTENANT = ("Lieutenant", 500, 1000, "#FFD700", "★★")
    CAPTAIN = ("Captain", 1000, 2500, "#FFD700", "★★★")
    MAJOR = ("Major", 2500, 5000, "#E5E4E2", "★★★★")
    COLONEL = ("Colonel", 5000, 10000, "#E5E4E2", "★★★★★")
    GENERAL = ("General", 10000, float('inf'), "#B9F2FF", "⚔️")


class CardTheme(Enum):
    """Card themes"""
    DARK = "dark"
    LIGHT = "light"
    TACTICAL = "tactical"
    NEON = "neon"


@dataclass
class TradeData:
    """Trade information for the kill card"""
    pair: str
    entry_price: float
    exit_price: float
    profit_usd: float
    profit_percent: float
    duration: str
    timestamp: datetime.datetime
    strategy: str = "Manual"
    leverage: float = 1.0
    volume: float = 0
    achievements: List[str] = None
    trader_name: str = "Anonymous"
    trader_id: str = ""
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []


class KillCardGenerator:
    """Generates military-style kill cards for successful trades"""
    
    def __init__(self, assets_dir: Optional[str] = None):
        self.assets_dir = assets_dir or os.path.join(os.path.dirname(__file__), "assets")
        self.fonts = self._load_fonts()
        self.colors = {
            "dark": {
                "bg_primary": "#0a0a0a",
                "bg_secondary": "#1a1a1a",
                "accent": "#ff0066",
                "text_primary": "#ffffff",
                "text_secondary": "#cccccc",
                "success": "#00ff88",
                "danger": "#ff3366",
                "warning": "#ffaa00",
                "info": "#00aaff"
            },
            "light": {
                "bg_primary": "#f5f5f5",
                "bg_secondary": "#ffffff",
                "accent": "#ff0066",
                "text_primary": "#0a0a0a",
                "text_secondary": "#666666",
                "success": "#00cc66",
                "danger": "#ff3366",
                "warning": "#ff9900",
                "info": "#0088ff"
            },
            "tactical": {
                "bg_primary": "#1c2833",
                "bg_secondary": "#2c3e50",
                "accent": "#e74c3c",
                "text_primary": "#ecf0f1",
                "text_secondary": "#bdc3c7",
                "success": "#27ae60",
                "danger": "#e74c3c",
                "warning": "#f39c12",
                "info": "#3498db"
            },
            "neon": {
                "bg_primary": "#0a0a0a",
                "bg_secondary": "#1a0a2a",
                "accent": "#ff00ff",
                "text_primary": "#ffffff",
                "text_secondary": "#cc00ff",
                "success": "#00ffff",
                "danger": "#ff0066",
                "warning": "#ffff00",
                "info": "#00ff00"
            }
        }
        
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts with fallbacks"""
        fonts = {}
        try:
            # Try to load custom military-style fonts
            fonts["title"] = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 48)
            fonts["heading"] = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 36)
            fonts["body"] = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
            fonts["small"] = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 18)
            fonts["tiny"] = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 14)
        except:
            # Fallback to default fonts
            fonts["title"] = ImageFont.load_default()
            fonts["heading"] = ImageFont.load_default()
            fonts["body"] = ImageFont.load_default()
            fonts["small"] = ImageFont.load_default()
            fonts["tiny"] = ImageFont.load_default()
        return fonts
    
    def _get_rank_info(self, profit_usd: float) -> Tuple[str, str, str, int]:
        """Get rank information based on profit"""
        for rank in RankTier:
            name, min_profit, max_profit, color, badge = rank.value
            if min_profit <= profit_usd < max_profit:
                # Calculate XP within rank
                if max_profit == float('inf'):
                    xp = int(profit_usd)
                else:
                    xp = int((profit_usd - min_profit) / (max_profit - min_profit) * 1000)
                return name, badge, color, xp
        return "Recruit", "⬤", "#808080", 0
    
    def _create_background(self, size: Tuple[int, int], theme: str) -> Image.Image:
        """Create military-style background with patterns"""
        width, height = size
        bg = Image.new('RGB', size, self.colors[theme]["bg_primary"])
        draw = ImageDraw.Draw(bg)
        
        # Add tactical grid pattern
        grid_color = self.colors[theme]["bg_secondary"]
        for x in range(0, width, 50):
            draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
        for y in range(0, height, 50):
            draw.line([(0, y), (width, y)], fill=grid_color, width=1)
        
        # Add noise texture
        noise = Image.new('RGB', size)
        pixels = noise.load()
        import random
        for i in range(width):
            for j in range(height):
                val = random.randint(0, 20)
                pixels[i, j] = (val, val, val)
        
        bg = Image.blend(bg, noise, 0.1)
        
        # Add vignette effect
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        for i in range(min(width, height) // 2):
            alpha = int(255 * (1 - i / (min(width, height) // 2)))
            mask_draw.ellipse(
                [i, i, width - i, height - i],
                fill=alpha
            )
        
        vignette = Image.new('RGB', size, (0, 0, 0))
        bg = Image.composite(bg, vignette, mask)
        
        return bg
    
    def _draw_rank_badge(self, draw: ImageDraw.Draw, position: Tuple[int, int], 
                        rank: str, badge: str, color: str, size: int = 40):
        """Draw military rank badge"""
        x, y = position
        
        # Draw badge background
        draw.ellipse([x, y, x + size, y + size], fill=color, outline="#ffffff", width=2)
        
        # Draw rank symbol
        font = self.fonts["heading"]
        bbox = draw.textbbox((0, 0), badge, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        draw.text(
            (x + size // 2 - text_width // 2, y + size // 2 - text_height // 2),
            badge,
            font=font,
            fill="#ffffff"
        )
    
    def _draw_achievement_badges(self, draw: ImageDraw.Draw, achievements: List[str], 
                               position: Tuple[int, int], theme: str):
        """Draw achievement badges"""
        x, y = position
        badge_size = 60
        spacing = 10
        
        achievement_icons = {
            "First Blood": ("🩸", "#ff0000"),
            "Headshot": ("🎯", "#ff6600"),
            "Double Kill": ("⚡", "#ffaa00"),
            "Triple Kill": ("🔥", "#ff3300"),
            "Rampage": ("💀", "#ff0066"),
            "Godlike": ("👑", "#ffd700"),
            "Perfect Trade": ("💎", "#00ffff"),
            "Speed Demon": ("🏃", "#00ff00"),
            "Big Fish": ("🐋", "#0066ff"),
            "Sniper": ("🔫", "#666666")
        }
        
        for i, achievement in enumerate(achievements[:5]):  # Max 5 achievements
            if achievement in achievement_icons:
                icon, color = achievement_icons[achievement]
                badge_x = x + i * (badge_size + spacing)
                
                # Draw badge background
                draw.ellipse(
                    [badge_x, y, badge_x + badge_size, y + badge_size],
                    fill=color,
                    outline=self.colors[theme]["text_primary"],
                    width=2
                )
                
                # Draw icon
                font = self.fonts["body"]
                bbox = draw.textbbox((0, 0), icon, font=font)
                icon_width = bbox[2] - bbox[0]
                icon_height = bbox[3] - bbox[1]
                
                draw.text(
                    (badge_x + badge_size // 2 - icon_width // 2,
                     y + badge_size // 2 - icon_height // 2),
                    icon,
                    font=font,
                    fill="#ffffff"
                )
    
    def _generate_qr_code(self, data: Dict[str, Any]) -> Image.Image:
        """Generate QR code for verification"""
        # Create verification data
        verification_data = {
            "pair": data["pair"],
            "profit": data["profit_usd"],
            "timestamp": data["timestamp"].isoformat(),
            "trader_id": data.get("trader_id", ""),
            "hash": hashlib.sha256(
                f"{data['pair']}{data['profit_usd']}{data['timestamp']}".encode()
            ).hexdigest()[:8]
        }
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=1,
        )
        qr.add_data(json.dumps(verification_data))
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="white", back_color="black")
        return qr_img.resize((80, 80), Image.Resampling.LANCZOS)
    
    def _add_security_watermark(self, img: Image.Image, theme: str) -> Image.Image:
        """Add security watermark to prevent forgery"""
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Add diagonal watermark text
        watermark_text = "BITTEN VERIFIED"
        font = self.fonts["small"]
        
        # Calculate text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw watermark multiple times
        for i in range(0, width + height, 200):
            x = i - height
            y = height - i + width
            draw.text(
                (x, y),
                watermark_text,
                font=font,
                fill=(*ImageColor.getrgb(self.colors[theme]["text_secondary"]), 30)
            )
        
        return img
    
    def generate_kill_card(self, trade_data: TradeData, 
                          theme: CardTheme = CardTheme.DARK,
                          size: Tuple[int, int] = (1200, 675)) -> Image.Image:
        """Generate the main kill card"""
        theme_name = theme.value
        width, height = size
        
        # Create background
        card = self._create_background(size, theme_name)
        draw = ImageDraw.Draw(card)
        
        # Get rank information
        rank_name, rank_badge, rank_color, xp = self._get_rank_info(trade_data.profit_usd)
        
        # Draw header section
        header_height = 120
        draw.rectangle(
            [0, 0, width, header_height],
            fill=self.colors[theme_name]["bg_secondary"]
        )
        
        # Add BITTEN logo/title
        draw.text(
            (50, 30),
            "BITTEN",
            font=self.fonts["title"],
            fill=self.colors[theme_name]["accent"]
        )
        
        draw.text(
            (50, 80),
            "KILL CONFIRMED",
            font=self.fonts["small"],
            fill=self.colors[theme_name]["text_secondary"]
        )
        
        # Draw rank badge
        self._draw_rank_badge(draw, (width - 150, 30), rank_name, rank_badge, rank_color, 60)
        
        # Draw main content area
        content_y = header_height + 40
        
        # Trade pair
        draw.text(
            (50, content_y),
            trade_data.pair,
            font=self.fonts["heading"],
            fill=self.colors[theme_name]["text_primary"]
        )
        
        # Profit information
        profit_color = self.colors[theme_name]["success"] if trade_data.profit_usd > 0 else self.colors[theme_name]["danger"]
        draw.text(
            (50, content_y + 50),
            f"+${trade_data.profit_usd:,.2f}",
            font=self.fonts["title"],
            fill=profit_color
        )
        
        draw.text(
            (50, content_y + 110),
            f"+{trade_data.profit_percent:.2f}%",
            font=self.fonts["heading"],
            fill=profit_color
        )
        
        # Trade details box
        details_y = content_y + 180
        details_box_height = 150
        draw.rectangle(
            [40, details_y, width - 40, details_y + details_box_height],
            fill=self.colors[theme_name]["bg_secondary"],
            outline=self.colors[theme_name]["accent"],
            width=2
        )
        
        # Trade statistics
        stats_x = 60
        stats_y = details_y + 20
        line_height = 35
        
        stats = [
            ("ENTRY", f"${trade_data.entry_price:,.4f}"),
            ("EXIT", f"${trade_data.exit_price:,.4f}"),
            ("DURATION", trade_data.duration),
            ("LEVERAGE", f"{trade_data.leverage}x")
        ]
        
        for i, (label, value) in enumerate(stats):
            y_pos = stats_y + (i % 2) * line_height
            x_pos = stats_x + (i // 2) * 300
            
            draw.text(
                (x_pos, y_pos),
                f"{label}:",
                font=self.fonts["small"],
                fill=self.colors[theme_name]["text_secondary"]
            )
            
            draw.text(
                (x_pos + 100, y_pos),
                value,
                font=self.fonts["body"],
                fill=self.colors[theme_name]["text_primary"]
            )
        
        # XP and rank progress
        xp_y = details_y + details_box_height + 30
        draw.text(
            (50, xp_y),
            f"XP EARNED: +{xp}",
            font=self.fonts["body"],
            fill=self.colors[theme_name]["warning"]
        )
        
        # Progress bar
        progress_y = xp_y + 40
        progress_width = width - 100
        progress_height = 20
        
        # Background bar
        draw.rectangle(
            [50, progress_y, 50 + progress_width, progress_y + progress_height],
            fill=self.colors[theme_name]["bg_secondary"],
            outline=self.colors[theme_name]["text_secondary"],
            width=2
        )
        
        # Progress fill
        progress_fill = int(progress_width * (xp / 1000))
        draw.rectangle(
            [50, progress_y, 50 + progress_fill, progress_y + progress_height],
            fill=self.colors[theme_name]["accent"]
        )
        
        # Achievement badges
        if trade_data.achievements:
            self._draw_achievement_badges(
                draw, 
                trade_data.achievements,
                (50, height - 150),
                theme_name
            )
        
        # QR code for verification
        qr_data = {
            "pair": trade_data.pair,
            "profit_usd": trade_data.profit_usd,
            "timestamp": trade_data.timestamp,
            "trader_id": trade_data.trader_id
        }
        qr_img = self._generate_qr_code(qr_data)
        card.paste(qr_img, (width - 120, height - 120))
        
        # Timestamp and trader info
        draw.text(
            (width - 350, height - 40),
            f"{trade_data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            font=self.fonts["tiny"],
            fill=self.colors[theme_name]["text_secondary"]
        )
        
        draw.text(
            (width - 350, height - 60),
            f"Trader: {trade_data.trader_name}",
            font=self.fonts["tiny"],
            fill=self.colors[theme_name]["text_secondary"]
        )
        
        # Add security watermark
        card = self._add_security_watermark(card, theme_name)
        
        # Add glitch effect for big wins
        if trade_data.profit_usd > 1000:
            card = self._add_glitch_effect(card)
        
        return card
    
    def _add_glitch_effect(self, img: Image.Image) -> Image.Image:
        """Add glitch effect for epic wins"""
        # Create RGB shift effect
        r, g, b = img.split()
        
        # Shift channels slightly
        r = r.transform(img.size, Image.Transform.AFFINE, (1, 0, 2, 0, 1, 0))
        b = b.transform(img.size, Image.Transform.AFFINE, (1, 0, -2, 0, 1, 0))
        
        # Merge back
        glitched = Image.merge('RGB', (r, g, b))
        
        # Blend with original
        return Image.blend(img, glitched, 0.1)
    
    def generate_social_card(self, trade_data: TradeData,
                           platform: str = "twitter",
                           theme: CardTheme = CardTheme.DARK) -> Image.Image:
        """Generate optimized cards for social media platforms"""
        sizes = {
            "twitter": (1200, 675),
            "instagram": (1080, 1080),
            "facebook": (1200, 630),
            "discord": (800, 450)
        }
        
        size = sizes.get(platform, (1200, 675))
        
        # Generate base card
        card = self.generate_kill_card(trade_data, theme, size)
        
        # Add platform-specific optimizations
        if platform == "instagram":
            # Square format adjustments
            card = self._adjust_for_square(card)
        
        return card
    
    def _adjust_for_square(self, img: Image.Image) -> Image.Image:
        """Adjust layout for square format"""
        # This would contain logic to reposition elements for square format
        # For now, just return the original
        return img
    
    def save_card(self, card: Image.Image, output_path: str, 
                 quality: int = 95, optimize: bool = True) -> str:
        """Save the kill card to file"""
        card.save(output_path, "PNG", quality=quality, optimize=optimize)
        return output_path
    
    def generate_card_batch(self, trades: List[TradeData], 
                          theme: CardTheme = CardTheme.DARK) -> List[Image.Image]:
        """Generate multiple kill cards"""
        cards = []
        for trade in trades:
            card = self.generate_kill_card(trade, theme)
            cards.append(card)
        return cards
    
    def create_animated_card(self, trade_data: TradeData,
                           theme: CardTheme = CardTheme.DARK,
                           duration: int = 3000) -> List[Image.Image]:
        """Create animated version of kill card for social media"""
        frames = []
        
        # Frame 1: Base card with fade in
        base_card = self.generate_kill_card(trade_data, theme)
        
        # Create animation frames
        for i in range(10):
            alpha = int(255 * (i / 10))
            frame = Image.new('RGBA', base_card.size, (0, 0, 0, 255))
            base_with_alpha = base_card.convert('RGBA')
            base_with_alpha.putalpha(alpha)
            frame = Image.alpha_composite(frame, base_with_alpha)
            frames.append(frame.convert('RGB'))
        
        # Add final frame
        frames.extend([base_card] * 20)
        
        return frames
    
    def export_for_web(self, card: Image.Image) -> Dict[str, Any]:
        """Export card data for web display"""
        # Convert to base64
        buffer = io.BytesIO()
        card.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "image": f"data:image/png;base64,{img_str}",
            "width": card.width,
            "height": card.height,
            "format": "png"
        }


# Achievement detection functions
def detect_achievements(trade_data: TradeData) -> List[str]:
    """Detect achievements earned from the trade"""
    achievements = []
    
    # Profit-based achievements
    if trade_data.profit_percent >= 100:
        achievements.append("Double Kill")
    if trade_data.profit_percent >= 200:
        achievements.append("Triple Kill")
    if trade_data.profit_percent >= 500:
        achievements.append("Rampage")
    if trade_data.profit_percent >= 1000:
        achievements.append("Godlike")
    
    # Time-based achievements
    duration_minutes = parse_duration_to_minutes(trade_data.duration)
    if duration_minutes < 5:
        achievements.append("Speed Demon")
    if duration_minutes < 1:
        achievements.append("Headshot")
    
    # Precision achievements
    if trade_data.profit_percent > 0 and abs(trade_data.entry_price - trade_data.exit_price) / trade_data.entry_price < 0.001:
        achievements.append("Sniper")
    
    # Volume achievements
    if trade_data.volume > 100000:
        achievements.append("Big Fish")
    
    # Perfect trade (high profit, low drawdown)
    if trade_data.profit_percent > 50 and trade_data.leverage == 1:
        achievements.append("Perfect Trade")
    
    # First blood (first profitable trade of the day)
    # This would need session tracking
    
    return achievements


def parse_duration_to_minutes(duration: str) -> float:
    """Parse duration string to minutes"""
    # Simple parser for formats like "5m", "1h 30m", "2d 3h"
    total_minutes = 0
    parts = duration.lower().split()
    
    for part in parts:
        if 'd' in part:
            days = float(part.replace('d', ''))
            total_minutes += days * 24 * 60
        elif 'h' in part:
            hours = float(part.replace('h', ''))
            total_minutes += hours * 60
        elif 'm' in part:
            minutes = float(part.replace('m', ''))
            total_minutes += minutes
        elif 's' in part:
            seconds = float(part.replace('s', ''))
            total_minutes += seconds / 60
    
    return total_minutes


# Example usage
if __name__ == "__main__":
    # Example trade data
    trade = TradeData(
        pair="BTC/USDT",
        entry_price=43250.50,
        exit_price=45780.25,
        profit_usd=2529.75,
        profit_percent=5.84,
        duration="2h 45m",
        timestamp=datetime.datetime.now(),
        strategy="Momentum",
        leverage=10.0,
        volume=125000,
        trader_name="CryptoSniper",
        trader_id="usr_123456"
    )
    
    # Detect achievements
    trade.achievements = detect_achievements(trade)
    
    # Generate kill card
    generator = KillCardGenerator()
    
    # Generate different themed cards
    for theme in CardTheme:
        card = generator.generate_kill_card(trade, theme)
        generator.save_card(card, f"kill_card_{theme.value}.png")
    
    # Generate social media versions
    twitter_card = generator.generate_social_card(trade, "twitter", CardTheme.DARK)
    generator.save_card(twitter_card, "kill_card_twitter.png")
    
    # Generate animated version
    frames = generator.create_animated_card(trade, CardTheme.NEON)
    # Save as GIF
    if frames:
        frames[0].save(
            "kill_card_animated.gif",
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0
        )