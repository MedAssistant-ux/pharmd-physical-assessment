"""Generate a 3000x3000 podcast cover image."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "cover.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

SIZE = 3000
img = Image.new("RGB", (SIZE, SIZE), color=(15, 23, 42))
draw = ImageDraw.Draw(img)

# Gradient overlay
for y in range(SIZE):
    t = y / SIZE
    r = int(12 + (15 - 12) * t)
    g = int(74 + (23 - 74) * t)
    b = int(110 + (42 - 110) * t)
    draw.line([(0, y), (SIZE, y)], fill=(r, g, b))

# Accent ring
center = SIZE // 2
for r in range(880, 900):
    draw.ellipse([center - r, center - r, center + r, center + r], outline=(56, 189, 248), width=1)

# Stethoscope-ish abstract icon
draw.arc([center - 500, center - 800, center + 500, center - 200],
         start=200, end=340, fill=(34, 211, 238), width=40)
draw.line([center - 380, center - 350, center - 380, center + 100], fill=(34, 211, 238), width=40)
draw.line([center + 380, center - 350, center + 380, center + 100], fill=(34, 211, 238), width=40)
draw.ellipse([center - 100, center + 50, center + 100, center + 250], outline=(56, 189, 248), width=40)

# Font: try common Windows fonts
font_candidates = ["arialbd.ttf", "arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]
title_font = None
sub_font = None
for f in font_candidates:
    try:
        title_font = ImageFont.truetype(f, 180)
        sub_font = ImageFont.truetype(f, 90)
        break
    except (OSError, IOError):
        continue
if title_font is None:
    title_font = ImageFont.load_default()
    sub_font = ImageFont.load_default()

# Title text
title_lines = ["PharmD", "Physical", "Assessment"]
y = center + 350
for line in title_lines:
    bbox = draw.textbbox((0, 0), line, font=title_font)
    w = bbox[2] - bbox[0]
    draw.text(((SIZE - w) // 2, y), line, font=title_font, fill=(226, 232, 240))
    y += 200

# Subtitle
sub = "Audio Course"
bbox = draw.textbbox((0, 0), sub, font=sub_font)
w = bbox[2] - bbox[0]
draw.text(((SIZE - w) // 2, y + 30), sub, font=sub_font, fill=(56, 189, 248))

img.save(OUT, "PNG", optimize=True)
print(f"Cover saved to {OUT} ({OUT.stat().st_size // 1024} KB)")
