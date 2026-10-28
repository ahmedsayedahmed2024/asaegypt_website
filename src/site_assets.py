"""Writes every logo file the website uses from src/asa_mark.py (run from the repo root).

    python src/site_assets.py        # SVGs only (no dependencies)
    python src/site_assets.py --png  # + PNGs (needs cairosvg and Pillow, like logo.py --png)

Output names and pixel sizes are the same as the old logo files, so templates and email signatures keep working.
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import asa_mark as m

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'public/assets/img')
SMALL_ICON = m.square_icon_svg('prism', notch=False, side_ratio=1.04)   # 32 px and below: no notch


def write(name, data):
    path = os.path.join(IMG, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb' if isinstance(data, bytes) else 'w').write(data)
    print(f'{name}: {os.path.getsize(path):,} bytes')


# ---- site additions (October 2026, Ahmed's decisions for the website; asa_mark.py is not edited) -----------
# The short lockup (mark + ASA, no name line) is used in the header (every page but the top of the homepage)
# and, without the symbol, in the mobile menu. It is built from the same parts as the filed lockup.
SHORT_VIEWBOX = '-1 0 1045 268'


def short_lockup_svg(word_fill=m.CHARCOAL, symbol='tm'):
    """Mark + ASA (+ TM at the top right). symbol: 'tm' or None."""
    sym = f'<path fill="{word_fill}" d="{m.TM_MARK}"/>' if symbol == 'tm' else ''
    return (f'<svg {m.NS} viewBox="{SHORT_VIEWBOX}" width="1045" height="268" role="img" aria-label="ASA">'
            f'<title>ASA</title>{m.mark_paths("prism", True, m.lockup_tf)}'
            f'<path fill="{word_fill}" fill-rule="evenodd" d="{m.WORDMARK_SHIFTED}"/>{sym}</svg>')


def og_svg():
    """Default sharing image (og.png, 1200x630): Charcoal, a large faint mark on the right and the public logo
    (white text, no symbol) on the left."""
    k = 3.1                                       # the faint mark, 537 px tall, cut by the right edge
    big = m.mark_paths('prism', True, lambda x, y: (1010 + x * k, 315 + y * k))
    s = 0.52                                      # the public logo, 1045 x 352 units -> 543 x 183 px
    logo = m.named_lockup_svg('prism', m.WHITE, symbol=None).split('<title>ASA Ahmed Sayed Ahmed</title>')[1][:-6]
    return (f'<svg {m.NS} viewBox="0 0 1200 630" width="1200" height="630"><rect width="1200" height="630" fill="{m.CHARCOAL}"/>'
            f'<g opacity=".16">{big}</g><g transform="translate(96 196) scale({s})">{logo}</g>'
            f'<rect x="96" y="418" width="56" height="5" fill="{m.LIME}"/></svg>')


if __name__ == '__main__':
    write('logo-asa.svg', m.named_lockup_svg('prism', m.WHITE))          # public logo, dark backgrounds
    write('logo-asa-dark.svg', m.named_lockup_svg('prism', m.CHARCOAL))  # public logo, light header
    write('favicon.svg', SMALL_ICON)
    write('mark.svg', m.mark_svg('prism'))
    write('asa-next-spark.svg', m.next_spark_svg())             # ASA NEXT icon (tilted sub-brand use)
    write('logo-asa-short.svg', short_lockup_svg(m.WHITE))                      # header, dark backgrounds
    write('logo-asa-short-dark.svg', short_lockup_svg(m.CHARCOAL))              # header, light (scrolled) header
    write('logo-asa-short-plain.svg', short_lockup_svg(m.WHITE, None))          # mobile menu, small uses
    write('logo-asa-short-plain-dark.svg', short_lockup_svg(m.CHARCOAL, None))
    write('asa-ledger-pattern-dark.svg', m.pattern_tile_svg())                  # faint pattern on Charcoal
    if '--png' in sys.argv:
        import cairosvg
        from PIL import Image

        def fit(svg, W, H, bg=None):
            im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=W * 4)))
            im.thumbnail((W, H), Image.LANCZOS)
            c = Image.new('RGBA', (W, H), bg or (0, 0, 0, 0))
            c.alpha_composite(im.convert('RGBA'), ((W - im.width) // 2, (H - im.height) // 2))
            out = io.BytesIO(); (c.convert('RGB') if bg else c).save(out, 'PNG', optimize=True); return out.getvalue()

        write('favicon-32.png', fit(SMALL_ICON, 32, 32))
        ratio = (180 / 146) * (2 * m.H) / (2 * m.R)    # 180 px tile on charcoal, mark 146 px tall
        write('apple-touch-icon.png', fit(m.square_icon_svg('prism', side_ratio=ratio, bg=m.CHARCOAL), 180, 180, m.CHARCOAL))
        write('logo_color.png', fit(m.named_lockup_svg('prism', m.CHARCOAL), 900, 268))     # email signature: same URL
        write('logo_white.png', fit(m.named_lockup_svg('prism', m.WHITE), 900, 268))
        write('logo_color@3x.png', fit(m.named_lockup_svg("prism", m.CHARCOAL), 3135, 1056))
        write('signature/logo-sig.png', fit(m.named_lockup_svg('prism', m.CHARCOAL), 450, 134))  # URL must never change
        write('og.png', fit(og_svg(), 1200, 630, m.CHARCOAL))
