"""Draws the home-screen icons (icon-192.png, icon-512.png, apple-touch-icon.png) as the
faceted-gem emblem from the app header, on the app's background colour.

The emblem keeps to the middle of the square so Android's maskable crop (circle, squircle,
rounded square: the safe zone is the central 80% circle) never cuts into it.
Run from the repo root:  python tools/build_icons.py
"""
from PIL import Image, ImageDraw

BG, RING_FILL, RING = '#0f172a', '#2e1065', '#7c3aed'
EMBLEM = 0.64   # emblem diameter as a share of the icon width
SS = 4          # supersampling for smooth edges

# The header's 26x26 SVG: ring of radius 12 around (13, 13), then the gem's facets (points, colour)
FACETS = [
    ([(9, 6), (17, 6), (15, 10), (11, 10)], '#ede9fe'),   # table
    ([(9, 6), (11, 10), (5, 10)], '#c4b5fd'),             # crown, left
    ([(17, 6), (21, 10), (15, 10)], '#a78bfa'),           # crown, right
    ([(5, 10), (11, 10), (13, 20)], '#8b5cf6'),           # pavilion, left
    ([(11, 10), (15, 10), (13, 20)], '#a78bfa'),          # pavilion, middle
    ([(15, 10), (21, 10), (13, 20)], '#6d28d9'),          # pavilion, right
]


def icon(size):
    n = size * SS
    im = Image.new('RGB', (n, n), BG)
    d = ImageDraw.Draw(im)
    u = n * EMBLEM / 24          # one unit of the header SVG (ring radius 12)
    c = n / 2
    pt = lambda x, y: (c + (x - 13) * u, c + (y - 13) * u)
    box = lambda r: (c - r * u, c - r * u, c + r * u, c + r * u)
    d.ellipse(box(12), fill=RING)                  # outer edge of the 1.5-wide ring stroke
    d.ellipse(box(10.5), fill=RING_FILL)
    for pts, col in FACETS:
        d.polygon([pt(x, y) for x, y in pts], fill=col)
    return im.resize((size, size), Image.LANCZOS)


for name, size in (('icon-192.png', 192), ('icon-512.png', 512), ('apple-touch-icon.png', 180)):
    icon(size).save(name, optimize=True)
    print('wrote', name)
