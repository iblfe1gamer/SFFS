"""
generate_icon.py — Creates a multi-resolution SFFS shield+lock icon.

Design: Hexagonal shield in deep blue with a silver border, gold padlock
with an "S" shaped keyhole inside.

Sizes: 16, 24, 32, 48, 64, 128
"""

from __future__ import annotations

import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow is required: pip install Pillow")
    raise


def _hexagon(cx: int, cy: int, radius: int) -> list[tuple[int, int]]:
    """Generate hexagon vertices centered at (cx, cy)."""
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((int(round(x)), int(round(y))))
    return points


def _lock_body(cx: int, cy: int, size: int) -> tuple:
    """Return (body_rect, shackle_arc_center, shackle_radius) for a padlock."""
    body_w = size * 0.6
    body_h = size * 0.4
    body_x = cx - body_w / 2
    body_y = cy - body_h / 2 + size * 0.15
    body = (body_x, body_y, body_x + body_w, body_y + body_h)

    shackle_cx = cx
    shackle_cy = body_y
    shackle_r = body_w * 0.3
    return body, (shackle_cx, shackle_cy), shackle_r


def draw_icon(size: int) -> Image.Image:
    """Draw a single-resolution SFFS icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size / 2, size / 2

    # Shield hexagon
    shield_r = int(size * 0.44)
    shield_points = _hexagon(cx, cy, shield_r)

    # Shield fill gradient (approximated with solid deep blue)
    shield_color = (26, 35, 126)  # #1a237e
    draw.polygon(shield_points, fill=shield_color)

    # Shield border (silver)
    border_color = (189, 195, 199)  # #bdc3c7
    border_width = max(1, size // 32)
    draw.polygon(shield_points, outline=border_color, width=border_width)

    # Inner subtle highlight
    inner_r = shield_r - border_width * 3
    if inner_r > 0:
        inner_points = _hexagon(cx, cy, inner_r)
        highlight = (40, 53, 147)
        draw.polygon(inner_points, fill=highlight)

    # Padlock
    body, shackle_c, shackle_r = _lock_body(cx, cy, int(size * 0.5))
    lock_color = (255, 215, 0)  # Gold #ffd700
    lock_dark = (200, 165, 0)

    # Shackle (arc)
    shackle_w = max(2, size // 24)
    draw.arc(
        [
            shackle_c[0] - shackle_r,
            shackle_c[1] - shackle_r * 1.5,
            shackle_c[0] + shackle_r,
            shackle_c[1] + shackle_r * 0.5,
        ],
        start=180,
        end=0,
        fill=lock_dark,
        width=shackle_w,
    )

    # Lock body (rectangle with rounded corners)
    corner_r = max(2, size // 24)
    draw.rounded_rectangle(body, radius=corner_r, fill=lock_color)

    # Keyhole — "S" shape
    keyhole_size = max(2, int(size * 0.08))
    keyhole_y = cy + size * 0.12
    draw.ellipse(
        [cx - keyhole_size, keyhole_y - keyhole_size, cx + keyhole_size, keyhole_y + keyhole_size],
        fill=(26, 35, 126),
    )
    # S-shape slot below the circle
    slot_w = max(1, size // 48)
    slot_h = keyhole_size * 1.5
    draw.line(
        [(cx - keyhole_size, keyhole_y), (cx + keyhole_size, keyhole_y + slot_h)],
        fill=(26, 35, 126),
        width=slot_w,
    )
    draw.line(
        [(cx + keyhole_size, keyhole_y), (cx - keyhole_size, keyhole_y + slot_h)],
        fill=(26, 35, 126),
        width=slot_w,
    )

    # Subtle shadow at bottom of shield
    shadow_y = cy + shield_r - size // 16
    if shadow_y < size:
        draw.line(
            [(cx - shield_r * 0.6, shadow_y), (cx + shield_r * 0.6, shadow_y)],
            fill=(0, 0, 0, 40),
            width=max(1, size // 48),
        )

    return img


def _save_ico_fallback(output_path: Path, images: list) -> None:
    """Manually construct a multi-resolution .ico file."""
    import struct
    ico_header = struct.pack("<HHH", 0, 1, len(images))
    entries = b""
    data = b""
    offset = 6 + 16 * len(images)
    for img in images:
        w = img.width if img.width < 256 else 0
        h = img.height if img.height < 256 else 0
        # Convert to BMP format (XOR mask only, no AND mask)
        bmp_data = img.tobytes("raw", "BGRA")
        bmp_header = struct.pack(
            "<IiiHHIIiiII",
            40, img.width, img.height * 2, 1, 32, 0, len(bmp_data), 0, 0, 0, 0,
        )
        img_data = bmp_header + bmp_data
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(img_data), offset)
        data += img_data
        offset += len(img_data)
    output_path.write_bytes(ico_header + entries + data)
    print(f"Icon saved (fallback): {output_path} ({output_path.stat().st_size} bytes)")


def generate_ico(output_path: Path) -> None:
    """Generate a multi-resolution .ico file."""
    sizes = [16, 24, 32, 48, 64, 128]
    images = [draw_icon(s) for s in sizes]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Save with all sizes embedded
    images[0].save(
        str(output_path),
        format="ICO",
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:],
    )
    # Verify
    actual_size = output_path.stat().st_size
    print(f"Icon saved: {output_path} ({len(sizes)} resolutions, {actual_size} bytes)")
    if actual_size < 1000:
        # Fallback: save each size separately and combine manually
        print("Small file detected, regenerating with fallback method...")
        _save_ico_fallback(output_path, images)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate SFFS .ico file")
    parser.add_argument("-o", "--output", default="sffs.ico", help="Output .ico path")
    args = parser.parse_args()
    generate_ico(Path(args.output))
