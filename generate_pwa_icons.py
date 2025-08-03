#!/usr/bin/env python3
"""
Generate simple PWA icons for Commander Throne
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a simple Commander Throne icon"""
    # Create image with dark background
    img = Image.new('RGB', (size, size), color='#0a0a0a')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    border_width = max(2, size // 32)
    draw.rectangle([border_width, border_width, size-border_width, size-border_width], 
                   outline='#00ff41', width=border_width)
    
    # Draw crown symbol
    crown_size = size // 3
    crown_x = size // 2 - crown_size // 2
    crown_y = size // 2 - crown_size // 2
    
    # Crown base
    draw.rectangle([crown_x, crown_y + crown_size//2, crown_x + crown_size, crown_y + crown_size], 
                   fill='#ff6b00')
    
    # Crown points
    point_width = crown_size // 5
    for i in range(3):
        x = crown_x + i * point_width + point_width//2
        points = [(x, crown_y), (x - point_width//2, crown_y + crown_size//2), 
                  (x + point_width//2, crown_y + crown_size//2)]
        draw.polygon(points, fill='#ff6b00')
    
    # Add text if icon is large enough
    if size >= 64:
        try:
            # Try to use a system font
            font_size = max(8, size // 8)
            font = ImageFont.load_default()
            text = "CT"
            
            # Get text size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center text at bottom
            text_x = (size - text_width) // 2
            text_y = size - text_height - size // 8
            
            draw.text((text_x, text_y), text, font=font, fill='#00ff41')
        except:
            pass
    
    # Save image
    img.save(output_path, 'PNG')
    print(f"Created icon: {output_path}")

def main():
    """Generate all PWA icons"""
    icons_dir = '/root/HydraX-v2/static/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Standard PWA icon sizes
    sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        output_path = f'{icons_dir}/icon-{size}x{size}.png'
        create_icon(size, output_path)
    
    print(f"Generated {len(sizes)} PWA icons in {icons_dir}")

if __name__ == '__main__':
    main()