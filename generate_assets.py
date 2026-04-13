"""Generate raster image assets for RecallOS landing page."""

from PIL import Image, ImageDraw, ImageFont
import math
import os

OUT = os.path.join(os.path.dirname(__file__), "site", "assets")
os.makedirs(OUT, exist_ok=True)

# Brand colors
BG       = (8, 12, 26)
MAROON   = (26, 10, 18)
GOLD     = (212, 168, 67)
GOLD_DIM = (140, 110, 44)
TURQ     = (46, 196, 182)
TURQ_DIM = (30, 120, 112)
WHITE    = (240, 237, 232)
GRAY     = (168, 164, 160)
CARD_BG  = (15, 18, 37)


def blend(c1, c2, t):
    """Blend two colors by factor t (0=c1, 1=c2)."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_hexagon(draw, cx, cy, r, fill=None, outline=None, width=1):
    """Draw a regular hexagon."""
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(pts, fill=fill, outline=outline, width=width)


def draw_radial_glow(img, cx, cy, radius, color, intensity=0.15):
    """Draw a soft radial glow effect."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    steps = 40
    for i in range(steps):
        t = i / steps
        r = radius * (1 - t)
        alpha = int(255 * intensity * (1 - t) ** 2)
        c = color + (alpha,)
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))


# ==========================================================================
# OG CARD — 1200 x 630
# ==========================================================================
def generate_og_card():
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Subtle maroon gradient band at top
    for y in range(H):
        t = max(0, 1 - (y / (H * 0.7)))
        row_color = blend(BG, MAROON, t * 0.4)
        draw.line([(0, y), (W, y)], fill=row_color)

    # Radial glow behind center
    draw_radial_glow(img, W // 2, H // 2 - 30, 280, TURQ, 0.08)
    draw_radial_glow(img, W // 2 - 200, H // 2, 200, GOLD, 0.05)
    draw = ImageDraw.Draw(img)

    # Gold border
    draw.rectangle([0, 0, W - 1, H - 1], outline=GOLD_DIM, width=2)
    # Gold accent line at bottom
    draw.rectangle([0, H - 4, W, H], fill=GOLD)

    # Decorative hexagons (faint)
    for hx, hy, hr, col in [
        (900, 120, 60, TURQ_DIM), (950, 400, 45, GOLD_DIM),
        (180, 480, 50, TURQ_DIM), (120, 150, 35, GOLD_DIM),
        (1050, 280, 30, TURQ_DIM),
    ]:
        draw_hexagon(draw, hx, hy, hr, outline=col, width=1)

    # Central hexagon icon
    draw_hexagon(draw, W // 2, 180, 55, outline=TURQ, width=3)
    draw_hexagon(draw, W // 2, 180, 35, fill=TURQ_DIM, outline=TURQ, width=2)

    # Text — use default font at various sizes
    try:
        font_big = ImageFont.truetype("arial.ttf", 54)
        font_med = ImageFont.truetype("arial.ttf", 26)
        font_sm = ImageFont.truetype("arial.ttf", 18)
        font_tag = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font_big = ImageFont.load_default()
        font_med = font_big
        font_sm = font_big
        font_tag = font_big

    # Title
    title = "RecallOS"
    bbox = draw.textbbox((0, 0), title, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 260), title, fill=WHITE, font=font_big)

    # Subtitle
    sub = "Local-First AI Memory. No Cloud. No Subscription."
    bbox = draw.textbbox((0, 0), sub, font=font_med)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 335), sub, fill=GRAY, font=font_med)

    # Tagline
    tag = "Your AI remembers what matters."
    bbox = draw.textbbox((0, 0), tag, font=font_sm)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 385), tag, fill=GOLD, font=font_sm)

    # Stats row
    stats = "96.6% R@5  ·  30× compression  ·  $0.70/yr  ·  Open Source"
    bbox = draw.textbbox((0, 0), stats, font=font_tag)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 540), stats, fill=TURQ_DIM, font=font_tag)

    # Version badge
    ver = "v4.0.0"
    bbox = draw.textbbox((0, 0), ver, font=font_tag)
    vw = bbox[2] - bbox[0]
    vh = bbox[3] - bbox[1]
    vx, vy = W - vw - 30, 20
    draw.rounded_rectangle([vx - 8, vy - 4, vx + vw + 8, vy + vh + 4],
                           radius=6, fill=CARD_BG, outline=GOLD_DIM, width=1)
    draw.text((vx, vy), ver, fill=GOLD, font=font_tag)

    img.save(os.path.join(OUT, "og-card.png"), "PNG")
    print(f"  ✔ og-card.png (1200×630)")


# ==========================================================================
# APPLE TOUCH ICON — 180 x 180
# ==========================================================================
def generate_apple_touch_icon():
    S = 180
    img = Image.new("RGB", (S, S), BG)
    draw = ImageDraw.Draw(img)

    # Radial glow
    draw_radial_glow(img, S // 2, S // 2, 80, TURQ, 0.12)
    draw = ImageDraw.Draw(img)

    # Central hexagon
    draw_hexagon(draw, S // 2, S // 2, 55, outline=TURQ, width=3)
    draw_hexagon(draw, S // 2, S // 2, 36, fill=TURQ_DIM, outline=TURQ, width=2)

    # Inner "R" text
    try:
        font = ImageFont.truetype("arial.ttf", 38)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "R", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((S - tw) // 2 - 1, (S - th) // 2 - 6), "R", fill=WHITE, font=font)

    # Gold corner accents
    draw.line([(8, 8), (30, 8)], fill=GOLD, width=2)
    draw.line([(8, 8), (8, 30)], fill=GOLD, width=2)
    draw.line([(S - 8, S - 8), (S - 30, S - 8)], fill=GOLD, width=2)
    draw.line([(S - 8, S - 8), (S - 8, S - 30)], fill=GOLD, width=2)

    img.save(os.path.join(OUT, "apple-touch-icon.png"), "PNG")
    print(f"  ✔ apple-touch-icon.png (180×180)")


# ==========================================================================
# FAVICON — .ico (16x16 + 32x32 + 48x48)
# ==========================================================================
def generate_favicon():
    sizes = [16, 32, 48]
    frames = []

    for s in sizes:
        img = Image.new("RGBA", (s, s), BG + (255,))
        draw = ImageDraw.Draw(img)
        cx, cy = s // 2, s // 2
        r_outer = int(s * 0.42)
        r_inner = int(s * 0.28)

        draw_hexagon(draw, cx, cy, r_outer, outline=TURQ + (255,), width=max(1, s // 16))
        draw_hexagon(draw, cx, cy, r_inner, fill=TURQ_DIM + (255,), outline=TURQ + (255,),
                     width=max(1, s // 20))

        if s >= 32:
            try:
                font = ImageFont.truetype("arial.ttf", int(s * 0.38))
            except OSError:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), "R", font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((s - tw) // 2, (s - th) // 2 - 1), "R",
                      fill=WHITE + (255,), font=font)

        frames.append(img)

    # Save as .ico with all sizes
    frames[0].save(
        os.path.join(OUT, "favicon.ico"),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"  ✔ favicon.ico (16+32+48)")


# ==========================================================================

if __name__ == "__main__":
    print("Generating RecallOS raster assets...")
    generate_og_card()
    generate_apple_touch_icon()
    generate_favicon()
    print("Done.")
