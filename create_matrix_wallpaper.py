#!/usr/bin/env python3
"""
Create Matrix-style wallpaper for BITTEN Telegram theme
"""

from PIL import Image, ImageDraw, ImageFont
import random
import os

def create_matrix_wallpaper(width=1080, height=1920):
    """Create Matrix code rain wallpaper"""
    
    # Create image with dark background
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Matrix green colors
    colors = [
        (0, 100, 0),    # Dark green
        (0, 150, 0),    # Medium green  
        (0, 200, 0),    # Bright green
        (0, 255, 65),   # BITTEN green
        (100, 255, 100) # Light green
    ]
    
    # Matrix characters (Japanese katakana + numbers)
    matrix_chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789"
    
    # Column settings
    col_width = 20
    num_cols = width // col_width
    
    # Font (fallback to default if special font not available)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    # Create falling code columns
    for col in range(num_cols):
        x = col * col_width
        
        # Random column height and starting position
        col_height = random.randint(height // 4, height)
        start_y = random.randint(0, height // 2)
        
        # Character spacing
        char_spacing = 20
        
        for i in range(0, col_height, char_spacing):
            y = start_y + i
            
            if y > height:
                break
                
            # Random character
            char = random.choice(matrix_chars)
            
            # Color fade effect (brighter at top of each stream)
            fade_factor = min(1.0, (col_height - i) / 200)
            color_idx = int(fade_factor * (len(colors) - 1))
            color = colors[color_idx]
            
            # Add some transparency for depth
            alpha = int(255 * fade_factor * random.uniform(0.3, 1.0))
            
            try:
                draw.text((x, y), char, fill=color, font=font)
            except:
                draw.text((x, y), char, fill=color)
    
    return img

def create_ticker_wallpaper(width=1080, height=1920):
    """Create stock ticker feed wallpaper"""
    
    img = Image.new('RGB', (width, height), (5, 5, 5))
    draw = ImageDraw.Draw(img)
    
    # Ticker symbols and prices
    tickers = [
        "EURUSD 1.0875 +0.12%", "GBPUSD 1.2634 -0.08%", "USDJPY 149.23 +0.34%",
        "AUDUSD 0.6721 +0.19%", "USDCAD 1.3456 -0.05%", "NZDUSD 0.6123 +0.24%",
        "XAUUSD 1954.32 +1.2%", "BTCUSD 43250 +2.1%", "ETHUSD 2634 +1.8%",
        "SPX500 4567.89 +0.45%", "NAS100 15234.67 +0.67%", "GER40 15987.23 +0.32%"
    ]
    
    # Colors for different ticker types
    colors = {
        'positive': (0, 255, 65),  # BITTEN green
        'negative': (255, 64, 64), # Red
        'neutral': (200, 200, 200) # Grey
    }
    
    # Font
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Create scrolling ticker lines
    line_height = 30
    num_lines = height // line_height
    
    for line in range(num_lines):
        y = line * line_height
        
        # Stagger the tickers across lines
        ticker_offset = (line * 3) % len(tickers)
        
        x_pos = -100 + (line * 50) % 200  # Scrolling effect
        
        for i in range(8):  # Multiple tickers per line
            ticker_idx = (ticker_offset + i) % len(tickers)
            ticker_text = tickers[ticker_idx]
            
            # Determine color based on +/- in ticker
            if '+' in ticker_text:
                color = colors['positive']
            elif '-' in ticker_text:
                color = colors['negative']
            else:
                color = colors['neutral']
            
            # Add transparency for depth
            alpha_factor = random.uniform(0.3, 0.8)
            faded_color = tuple(int(c * alpha_factor) for c in color)
            
            try:
                draw.text((x_pos, y), ticker_text, fill=faded_color, font=font_small)
            except:
                draw.text((x_pos, y), ticker_text, fill=faded_color)
            
            x_pos += 200
            
            if x_pos > width + 100:
                break
    
    # Add some BITTEN branding
    bitten_text = "BITTEN COMMAND • TACTICAL TRADING • LIVE MARKET DATA"
    try:
        draw.text((50, height - 50), bitten_text, fill=(0, 255, 65), font=font_large)
    except:
        draw.text((50, height - 50), bitten_text, fill=(0, 255, 65))
    
    return img

def create_hybrid_wallpaper(width=1080, height=1920):
    """Create hybrid Matrix + ticker wallpaper"""
    
    # Start with matrix background
    img = create_matrix_wallpaper(width, height)
    
    # Add ticker overlay
    ticker_img = create_ticker_wallpaper(width, height)
    
    # Blend them together
    from PIL import ImageChops
    
    # Make ticker more transparent
    ticker_img = ticker_img.convert("RGBA")
    alpha = Image.new("L", ticker_img.size, 80)  # 80/255 = ~30% opacity
    ticker_img.putalpha(alpha)
    
    # Composite
    img = img.convert("RGBA")
    final_img = Image.alpha_composite(img, ticker_img)
    
    return final_img.convert("RGB")

if __name__ == "__main__":
    print("🎨 Creating BITTEN wallpapers...")
    
    # Create wallpaper options
    wallpapers = {
        "matrix": create_matrix_wallpaper,
        "ticker": create_ticker_wallpaper, 
        "hybrid": create_hybrid_wallpaper
    }
    
    for name, create_func in wallpapers.items():
        print(f"Creating {name} wallpaper...")
        img = create_func()
        filename = f"bitten_{name}_wallpaper.jpg"
        img.save(filename, "JPEG", quality=85)
        print(f"✅ Saved: {filename}")
    
    print("🚀 Wallpapers ready for deployment!")