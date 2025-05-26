#!/usr/bin/env python3
"""
Simple icon generator for PGG Tour PWA
Creates basic colored icons in different sizes
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    """Create a simple PGG Tour icon"""
    
    # Create image with green background
    img = Image.new('RGB', (size, size), color='#16a34a')  # Green color
    draw = ImageDraw.Draw(img)
    
    # Add white circle background
    margin = size // 8
    circle_size = size - (margin * 2)
    draw.ellipse([margin, margin, margin + circle_size, margin + circle_size], 
                 fill='white', outline='#16a34a', width=3)
    
    # Add text
    try:
        # Try to use a nice font
        font_size = size // 4
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw "PGG" text
    text = "PGG"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size // 20
    
    draw.text((x, y), text, fill='#16a34a', font=font)
    
    # Add golf ball dots
    dot_size = size // 20
    for i in range(3):
        for j in range(3):
            if (i + j) % 2 == 0:  # Checkerboard pattern
                dot_x = x + text_width + size // 15 + (i * dot_size // 2)
                dot_y = y + text_height + size // 20 + (j * dot_size // 2)
                if dot_x < size - margin and dot_y < size - margin:
                    draw.ellipse([dot_x, dot_y, dot_x + dot_size//2, dot_y + dot_size//2], 
                               fill='#16a34a')
    
    # Save the image
    img.save(filename, 'PNG')
    print(f"✅ Created {filename} ({size}x{size})")

def main():
    """Generate all required icon sizes"""
    
    # Create icons directory if it doesn't exist
    os.makedirs('static/icons', exist_ok=True)
    
    # Icon sizes required for PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    print("🎨 Generating PGG Tour PWA icons...")
    
    for size in sizes:
        filename = f"static/icons/icon-{size}x{size}.png"
        create_icon(size, filename)
    
    print(f"\n🎉 Generated {len(sizes)} icons for PWA!")
    print("📱 Your app is ready to be installed on mobile devices!")

if __name__ == "__main__":
    main()
