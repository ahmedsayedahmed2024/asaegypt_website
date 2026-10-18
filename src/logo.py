"""The site logo as vector files. Run by hand after changing the logo: python src/logo.py [--png]

Writes public/assets/img/logo-asa.svg (white wordmark, for dark backgrounds), logo-asa-dark.svg
(grey wordmark, for light backgrounds) and favicon.svg. With --png (needs cairosvg) it also writes
favicon-32.png, apple-touch-icon.png, logo_color@3x.png and signature/logo-sig.png (email signature logo,
grey wordmark, 450x134 = 3x of 150x45, transparent; its URL must never change).
The hexagon (12 straight-edged stripes) and the "ASA" wordmark are traced from the original logo artwork,
which is final (trademark): do not change the shapes. The wordmark is outlined, so no font is needed.
The large homepage hexagon (mark.py) is a separate, slightly different drawing; it is not used here.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'public/assets/img')
WHITE, GREY = '#FFF', '#949599'
# logo canvas: same framing as the old 900x268 raster, so the logo keeps its size and place in the page
# (shifted 1 unit so the hexagon's left tip, cut off in the old raster, is not clipped)
W, H = 900, 268
VIEWBOX = f'-1 0 {W} {H}'
# the hexagon: (colour, stripes) for the top-left, top-right, bottom-right and bottom-left groups;
# the bottom half is the top half turned 180 degrees
MARK = (
    ('#80CAE3', 'M33.35 129.84L0.67 129.84L64.11 8.48L96.79 8.48Z'
                'M71.66 129.84L38.99 129.84L102.43 8.48L135.1 8.48Z'
                'M110.05 129.84L77.31 129.84L140.75 8.48L173.49 8.48Z'),
    ('#99D3EA', 'M156.86 129.84L119.8 129.84L138.06 94.54Z'
                'M198.53 129.84L162.75 129.84L140.96 88.93L158.6 54.85Z'
                'M235.78 129.84L204.45 129.84L161.51 49.21L178.33 16.72Z'),
    ('#B2DCF2', 'M124.98 137.11L157.72 137.11L94.27 258.47L61.53 258.47Z'
                'M163.37 137.11L196.04 137.11L132.59 258.47L99.92 258.47Z'
                'M201.68 137.11L234.36 137.11L170.92 258.47L138.24 258.47Z'),
    ('#C3D648', 'M-0.75 137.11L30.57 137.11L73.51 217.74L56.7 250.23Z'
                'M36.49 137.11L72.28 137.11L94.06 178.02L76.43 212.1Z'
                'M78.16 137.11L115.23 137.11L96.96 172.41Z'),
)
MARK_C, MARK_H = (117.52, 133.48), 250  # centre and height of the hexagon's bounding box
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
    return ''.join(f'<path fill="{c}" d="{d}"/>' for c, d in MARK)


def logo_svg(word_fill):
    return (f'<svg {NS} viewBox="{VIEWBOX}" width="{W}" height="{H}">{mark_paths()}'
            f'<path fill="{word_fill}" fill-rule="evenodd" d="{WORDMARK}"/></svg>')


def icon_svg(bg=None, margin=118 / 116):
    """The hexagon alone, centred in a square whose side is margin x its height. bg: background colour."""
    side = MARK_H * margin
    x, y = MARK_C[0] - side / 2, MARK_C[1] - side / 2
    rect = f'<rect x="{x:.2f}" y="{y:.2f}" width="{side:.2f}" height="{side:.2f}" fill="{bg}"/>' if bg else ''
    return f'<svg {NS} viewBox="{x:.2f} {y:.2f} {side:.2f} {side:.2f}">{rect}{mark_paths()}</svg>'


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
        write('apple-touch-icon.png', png(icon_svg('#23262B', 180 / 146), 180, 180))
        write('logo_color@3x.png', png(logo_svg(GREY), W * 3, H * 3))
        os.makedirs(os.path.join(IMG, 'signature'), exist_ok=True)
        write('signature/logo-sig.png', png(logo_svg(GREY), 450, 134))
