#!/usr/bin/env python3
"""
Convert PGG Tour logo to PWA icons in all required sizes
"""

from PIL import Image, ImageDraw
import os

def create_logo_icon(size, filename):
    """Create PWA icon from existing logo"""
    
    try:
        # Open the existing logo
        logo = Image.open('static/logo.jpg')
        print(f"📷 Original logo size: {logo.size}")
        
        # Convert to RGBA if needed
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        # Create new image with transparent background
        icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        
        # Calculate size to fit logo with some padding
        padding = size // 10  # 10% padding
        logo_size = size - (padding * 2)
        
        # Resize logo to fit
        logo_resized = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Center the logo on the icon
        x = (size - logo_size) // 2
        y = (size - logo_size) // 2
        
        # Paste logo onto icon
        icon.paste(logo_resized, (x, y), logo_resized)
        
        # Save the icon
        icon.save(filename, 'PNG')
        print(f"✅ Created {filename} ({size}x{size})")
        
    except Exception as e:
        print(f"❌ Error creating {filename}: {e}")
        # Fallback: create simple colored icon
        create_fallback_icon(size, filename)

def create_fallback_icon(size, filename):
    """Create a simple fallback icon if logo processing fails"""
    
    # Create image with PGG Tour green background
    img = Image.new('RGB', (size, size), color='#16a34a')
    draw = ImageDraw.Draw(img)
    
    # Add white circle
    margin = size // 8
    circle_size = size - (margin * 2)
    draw.ellipse([margin, margin, margin + circle_size, margin + circle_size], 
                 fill='white', outline='#16a34a', width=3)
    
    # Add "PGG" text
    try:
        from PIL import ImageFont
        font_size = size // 4
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "PGG"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='#16a34a', font=font)
    
    # Save the image
    img.save(filename, 'PNG')
    print(f"✅ Created fallback {filename} ({size}x{size})")

def main():
    """Generate all PWA icon sizes from logo"""
    
    # Check if logo exists
    if not os.path.exists('static/logo.jpg'):
        print("❌ Logo file 'static/logo.jpg' not found!")
        print("Please make sure your logo file exists.")
        return
    
    # Create icons directory if it doesn't exist
    os.makedirs('static/icons', exist_ok=True)
    
    # Icon sizes required for PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    print("🎨 Converting PGG Tour logo to PWA icons...")
    print(f"📁 Using logo: static/logo.jpg")
    
    for size in sizes:
        filename = f"static/icons/icon-{size}x{size}.png"
        create_logo_icon(size, filename)
    
    print(f"\n🎉 Generated {len(sizes)} logo-based icons for PWA!")
    print("📱 Your app will now use the PGG Tour logo!")

if __name__ == "__main__":
    main()
