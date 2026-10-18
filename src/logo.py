"""The site logo as vector files. Run by hand after changing the logo: python src/logo.py [--png]

Writes public/assets/img/logo-asa.svg (white wordmark, for dark backgrounds), logo-asa-dark.svg
(grey wordmark, for light backgrounds) and favicon.svg. With --png (needs cairosvg) it also writes
favicon-32.png, apple-touch-icon.png and logo_color@3x.png.
The hexagon is the 12 stripe paths of mark.py (same geometry as the hero hexagon), scaled into place.
The "ASA" wordmark is outlined (no font needed), traced from the original logo artwork.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import mark

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'public/assets/img')
# the logo's own colours (the hero hexagon uses #A6D8EE for the top-right group)
COLORS = ('#80CAE3', '#99D3EA', '#B2DCF2', '#C3D648')
WHITE, GREY = '#FFF', '#949599'
# logo canvas: same framing as the old 900x268 raster, so the logo keeps its size and place in the page
W, H = 900, 268
MARK_T = 'matrix(2.1452 0 0 2.1452 117.53 133.7)'
WORDMARK = ('M244 251.2L320.5 10.3L383.6 10.3L460 251.2L405.6 251.2L390.7 202.7L313.3 202.7L298.5 251.2Z'
            'M352 73.3L378.3 156.9L325.8 156.9Z'
            'M672.3 251.2L748.8 10.3L811.9 10.3L888.3 251.2L833.9 251.2L819 202.7L741.6 202.7L726.8 251.2Z'
            'M780.3 73.3L806.6 156.9L754.1 156.9Z'
            'M648.7 21.6L648.7 78.4C628.1 60.8 590.9 46.9 563.6 49.3C550.6 50.4 529.8 62.6 535 78.5'
            'C539.7 93 565.3 98.3 578.3 101C604.8 106.5 630.5 115.2 645.5 139.4'
            'C674.2 185.5 642.7 239.3 594.7 253.7C557.2 264.9 515.1 253.5 480.6 238.1L480.6 178.5'
            'C503.4 200.4 538.2 214.2 570.1 213.4C585.1 213.1 608.8 202.3 602.5 183.7'
            'C597 167.7 573.8 161.1 559.3 157.2C532.3 149.9 506.2 142.4 489.5 118.1'
            'C464.2 81.2 484.6 35 523.6 18.2C558.7 3 613.5 8.9 648.7 21.6Z')
NS = 'xmlns="http://www.w3.org/2000/svg"'


def mark_paths():
    """The 12 stripes of mark.py as 4 paths, one per colour group."""
    groups = (mark.TL, mark.TR, mark.BR, mark.BL)
    return ''.join(f'<path fill="{c}" d="{"".join(mark.path(g) for g in grp)}"/>' for grp, c in zip(groups, COLORS))


def logo_svg(word_fill):
    return (f'<svg {NS} viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<g transform="{MARK_T}">{mark_paths()}</g>'
            f'<path fill="{word_fill}" fill-rule="evenodd" d="{WORDMARK}"/></svg>')


def icon_svg(bg=None, size=118):
    """The mark alone, centred in a square. bg: a background colour (apple-touch-icon)."""
    s = size / 2
    rect = f'<rect x="{-s:g}" y="{-s:g}" width="{size:g}" height="{size:g}" fill="{bg}"/>' if bg else ''
    return f'<svg {NS} viewBox="{-s:g} {-s:g} {size:g} {size:g}">{rect}{mark_paths()}</svg>'


def write(name, data):
    path = os.path.join(IMG, name)
    open(path, 'wb' if isinstance(data, bytes) else 'w').write(data)
    print(f'{name}: {os.path.getsize(path):,} bytes')


if __name__ == '__main__':
    write('logo-asa.svg', logo_svg(WHITE))
    write('logo-asa-dark.svg', logo_svg(GREY))
    write('favicon.svg', icon_svg())
    if '--png' in sys.argv:
        import io, cairosvg
        from PIL import Image

        def png(svg, w, h):
            im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h)))
            out = io.BytesIO(); im.save(out, 'PNG', optimize=True); return out.getvalue()
        write('favicon-32.png', png(icon_svg(), 32, 32))
        # 180px tile on the dark brand background; the mark is 146px tall, as before
        write('apple-touch-icon.png', png(icon_svg('#23262B', 116 * 180 / 146), 180, 180))
        write('logo_color@3x.png', png(logo_svg(GREY), W * 3, H * 3))
