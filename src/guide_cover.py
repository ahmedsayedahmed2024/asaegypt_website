"""Cover of the reference guide "The Institutions Behind the Global Accounting and Auditing Profession":
a loose honeycomb of hexagon badges carrying institution acronyms in the five category colours of the guide
(src/guide.py, CATS / INST) on the dark ASA background. No other text, no logos.

Writes public/assets/img/content/articles/<slug>.svg (the image band on the article page, font embedded).
With --png (needs Playwright's Chromium) also <slug>-card.webp (cards and homepage hexagon, 800x400) and
<slug>-og.png (share image, 1200x630). Run by hand when the cover changes; not part of the build:
    python src/guide_cover.py --png
"""
import base64, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import guide

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUG = 'global-accounting-auditing-institutions'
OUT = os.path.join(ROOT, 'public/assets/img/content/articles')
BG = '#23262B'
STYLE = {  # category -> (fill, stroke, text)
    'std': ('#C3D648', 'none', '#23262B'),
    'reg': ('#1C7AA6', 'none', '#FFFFFF'),
    'pao': ('#80CAE3', 'none', '#23262B'),
    'lic': ('#23262B', '#C3D648', '#C3D648'),
    'net': ('#949599', 'none', '#23262B'),
}
# badges from the centre outwards: the most recognisable first, categories mixed
ACRONYMS = ['IFAC', 'IAASB', 'SOCPA', 'IASB', 'PCAOB', 'IFIAR', 'ACCA', 'ESAA', 'IESBA', 'FRA', 'ISSB', 'INTOSAI',
            'FRC', 'COSO', 'IIA', 'NASBA', 'ICAEW', 'IOSCO', 'SEC', 'PIOB', 'AICPA', 'AAOIFI', 'FASB', 'CBE',
            'IPSASB', 'GRI', 'BCBS', 'CMA', 'IFEA', 'SAMA', 'CIMA', 'FSB', 'GASB', 'CPAB', 'ICAS', 'ISACA', 'IFSB',
            'CEAOB', 'IMA', 'BIS', 'IAIS', 'GSSB', 'EFRAG', 'GCA', 'CIPFA', 'CAPA', 'PAFA', 'SASB']

def font_face():
    data = base64.b64encode(open(os.path.join(ROOT, 'public/assets/fonts/pjs-800.woff2'), 'rb').read()).decode()
    return ("@font-face{font-family:PJS;font-weight:800;src:url(data:font/woff2;base64," + data + ") format('woff2')}"
            "text{font-family:PJS,'Plus Jakarta Sans',Arial,sans-serif;font-weight:800;text-anchor:middle;dominant-baseline:central}")

def hexagon(cx, cy, r):
    """Flat-top hexagon (the ASA hexagon: 25% 0, 75% 0, 100% 50% ...), r = half the width."""
    h = r * math.sqrt(3) / 2
    pts = [(cx - r / 2, cy - h), (cx + r / 2, cy - h), (cx + r, cy), (cx + r / 2, cy + h), (cx - r / 2, cy + h), (cx - r, cy)]
    return ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)

def svg(W, H, R=74, badges=None, embed=True):
    """A honeycomb lattice covering W x H; cells nearest the centre carry badges (every few cells left empty
    so the comb stays loose), the others are faint outlines that fade towards the edges."""
    step_x, step_y = 1.5 * R, math.sqrt(3) * R
    cx0, cy0 = W / 2, H / 2
    cells = []
    for col in range(-int(W / step_x) - 2, int(W / step_x) + 3):
        for row in range(-int(H / step_y) - 2, int(H / step_y) + 3):
            x = cx0 + col * step_x
            y = cy0 + row * step_y + (step_y / 2 if col % 2 else 0)
            if -R < x < W + R and -R < y < H + R:
                d = math.hypot((x - cx0) / W * 1.6, (y - cy0) / H)  # wider than tall: spread sideways
                cells.append((d, col, row, x, y))
    cells.sort()
    names = list(badges or ACRONYMS)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    if embed:
        out.append(f'<style>{font_face()}</style>')
    out.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    k = 0
    for n, (d, col, row, x, y) in enumerate(cells):
        loose = (col * 7 + row * 3) % 5 == 0 and n > 2   # a few gaps in the comb
        inside = R * .9 < x < W - R * .9 and R * .8 < y < H - R * .8  # badges only where they are not cut off
        if names and not loose and inside and k < len(names):
            acr = names[k]; k += 1
            cat = guide.INST[acr][0]
            fill, stroke, ink = STYLE[cat]
            op = max(.28, min(1, 1.25 - d * 1.15))
            r = R * .86
            sw = f' stroke="{stroke}" stroke-width="{R * .055:.1f}"' if stroke != 'none' else ''
            size = R * (.36 if len(acr) <= 3 else .31 if len(acr) == 4 else .26 if len(acr) == 5 else .22)
            out.append(f'<g opacity="{op:.2f}"><polygon points="{hexagon(x, y, r - (R * .03 if sw else 0))}" fill="{fill}"{sw}/>'
                       f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size:.1f}" fill="{ink}" letter-spacing="{size * .02:.2f}">{acr}</text></g>')
        else:
            op = max(.0, min(.55, .7 - d * .55))
            if op > .04:
                out.append(f'<polygon points="{hexagon(x, y, R * .86)}" fill="none" stroke="#5F646C" stroke-width="1.5" opacity="{op:.2f}"/>')
    out.append('</svg>')
    return '\n'.join(out)

def render_png(svg_text, W, H, path, fmt):
    from playwright.sync_api import sync_playwright
    from PIL import Image
    import io
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        pg.set_content(f'<html><body style="margin:0;background:{BG}">{svg_text}</body></html>')
        pg.wait_for_timeout(300)
        png = pg.screenshot(clip={'x': 0, 'y': 0, 'width': W, 'height': H})
        b.close()
    im = Image.open(io.BytesIO(png)).convert('RGB')
    if fmt == 'webp':
        im.save(path, 'WEBP', quality=84, method=6)
    else:
        im = im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        im.save(path, 'PNG', optimize=True)
    return os.path.getsize(path) // 1024

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    band = svg(1800, 600, R=70)
    open(os.path.join(OUT, SLUG + '.svg'), 'w', encoding='utf-8').write(band)
    print(SLUG + '.svg', len(band.encode()) // 1024, 'KB')
    if '--png' in sys.argv:
        print(SLUG + '-card.webp', render_png(svg(800, 400, R=44), 800, 400, os.path.join(OUT, SLUG + '-card.webp'), 'webp'), 'KB')
        print(SLUG + '-og.png', render_png(svg(1200, 630, R=62), 1200, 630, os.path.join(OUT, SLUG + '-og.png'), 'png'), 'KB')
