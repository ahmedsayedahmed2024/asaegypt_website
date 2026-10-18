"""ASA Hexagon page (/hexagon/, /ar/hexagon/). See CLAUDE.md, "ASA Hexagon".

Text: pages_en.HEXAGON / pages_ar.HEXAGON. This module draws, at build time:
  - the hero diagram as inline SVG, in its finished state (so it shows without JavaScript and with reduced motion),
    in two layouts: wide (balance labels outside the hexagon) and narrow (phones, under 700px; balances listed
    under the diagram). public/assets/js/hexagon.js animates it and adds the hover / tap highlights.
  - the small icons of the pillar cards (one corner lit) and of the balance rows (one line lit),
    the hive icons and the faint honeycomb behind "Why a hexagon?".
The hexagon outline and its 12 stripes use the traced logo geometry from logo.py (flat top and bottom, pointed
left and right, exactly as the logo); never redraw them.

Open Graph images (1200x630, one per language): python src/hexagon.py --og (after a build; needs Playwright).
They are written to public/assets/img/og-hexagon-en.png / og-hexagon-ar.png; run it again when the text changes.
"""
import html, importlib, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import logo, pages_en, pages_ar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = {'en': pages_en, 'ar': pages_ar}
OG = {L: f'/assets/img/og-hexagon-{L}.png' for L in ('en', 'ar')}

# ---------------------------------------------------------------- geometry (from the traced logo)

def _pts(d):
    return [tuple(map(float, p.split())) for p in re.findall(r'[ML]\s*([-\d.]+ [-\d.]+)', d)]

_STRIPES = [[p + 'Z' for p in d.split('Z') if p] for _, d in logo.MARK]   # 4 groups x 3 stripes
_tl, _tr, _br = _pts(_STRIPES[0][0]), _pts(_STRIPES[1][2]), _pts(_STRIPES[2][2])   # the outer stripes
# the traced hexagon is symmetric under a half turn: the outer top-left stripe turns into the outer bottom-right one
CX, CY = (_tl[0][0] + _br[0][0]) / 2, (_tl[0][1] + _br[0][1]) / 2
K = 174 / 125   # diagram units per logo unit: the hexagon is 348 units tall in the diagram


def _x_at(a, b, y):
    return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])


def _geometry():
    """Corners of the hexagon in diagram units (centre 0,0; y down). The sides are the outer edges of the
    outer stripes: upper-left = left edge of the outer top-left stripe, upper-right = right edge of the outer
    top-right stripe, the lower sides are those turned half a turn. The traced artwork is not perfectly mirror
    symmetric, so each pointed tip is where two slightly offset sides meet (1.4 logo units apart)."""
    rot = lambda p: (2 * CX - p[0], 2 * CY - p[1])
    top = _tl[2][1]
    tl, tr = _tl[2], (_x_at(_tr[0], _tr[3], top), top)
    r_up, l_up = (_x_at(_tr[0], _tr[3], CY), CY), (_x_at(_tl[1], _tl[2], CY), CY)
    raw = dict(TL=tl, TR=tr, Rup=r_up, Rlo=rot(l_up), BR=rot(tl), BL=rot(tr), Llo=rot(r_up), Lup=l_up)
    g = {k: (round((x - CX) * K, 2), round((y - CY) * K, 2)) for k, (x, y) in raw.items()}
    g['R'] = (round((g['Rup'][0] + g['Rlo'][0]) / 2, 2), 0.0)
    g['L'] = (round((g['Lup'][0] + g['Llo'][0]) / 2, 2), 0.0)
    return g

G = _geometry()
OUTLINE = ['TL', 'TR', 'Rup', 'Rlo', 'BR', 'BL', 'Llo', 'Lup']
PERIM = ['TL', 'TR', 'R', 'BR', 'BL', 'L']                     # corner order around the outline
SIDES = [('TL', 'TR'), ('TR', 'Rup'), ('Rlo', 'BR'), ('BR', 'BL'), ('BL', 'Llo'), ('Lup', 'TL')]
# pillar n (1-6) -> corner. Fixed (CLAUDE.md): Arabic 1 top-right ... 6 bottom-left; English mirrored.
CORNER = {'ar': {1: 'TR', 2: 'TL', 3: 'R', 4: 'L', 5: 'BR', 6: 'BL'},
          'en': {1: 'TL', 2: 'TR', 3: 'L', 4: 'R', 5: 'BL', 6: 'BR'}}
# balance i (0-2): its line and its two pillars
BALANCES = [('TL', 'TR', (1, 2)), ('L', 'R', (3, 4)), ('BL', 'BR', (5, 6))]
LIME, WHITE = '#C3D648', '#FFFFFF'


def stripes_order():
    """The 12 stripes in the order they appear (as the homepage intro: top-left, top-right, bottom-right,
    bottom-left; each group from its outer stripe inwards): [(colour, d)]."""
    tl, tr, br, bl = [[(c, p) for p in grp] for (c, _), grp in zip(logo.MARK, _STRIPES)]
    return tl + tr[::-1] + br[::-1] + bl

# ---------------------------------------------------------------- the hero diagram

# layout per variant: viewBox, size of the hexagon (s: 1 = 348 units tall), font sizes (diagram units), line steps,
# balance label column. Names too long for their place wrap onto two lines (WRAP); the viewBoxes hold every label.
LAYOUT = {
    'wide': dict(box={'en': '-590 -277 1180 538', 'ar': '-525 -280 1050 556'}, s=1,
                 step_nm=27, step_nm2=25, step_en=21, bal_x={'en': 350, 'ar': 320}),
    'narrow': dict(box={'en': '-365 -258 730 523', 'ar': '-365 -252 730 506'}, s=.85,
                   step_nm=30, step_nm2=28, step_en=23, bal_x=None),
}
WRAP = {'wide': {'Quality & professional behaviour': ['Quality &', 'professional behaviour'],
                 'Confidentiality & competence and due care': ['Confidentiality &', 'competence and due care']},
        'narrow': {'Quality & professional behaviour': ['Quality &', 'professional behaviour'],
                   'Competence & due care': ['Competence &', 'due care']}}
E = html.escape


def _geo(variant):
    s = LAYOUT[variant]['s']
    return {k: (round(x * s, 2), round(y * s, 2)) for k, (x, y) in G.items()}


def _label_lines(L, n, variant):
    """[(css class, text)] for pillar n's label, top to bottom: the number, the name (1-2 lines), and on the
    Arabic page the English name in small muted text."""
    name = PC[L].HEXAGON['pillars'][n - 1]['name']
    lines = [('hxd-num', str(n))] + [('hxd-nm', t) for t in WRAP[variant].get(name, [name])]
    if L == 'ar':
        lines.append(('hxd-en', pages_en.HEXAGON['pillars'][n - 1]['name']))
    return lines


def _label(L, n, variant):
    lay = LAYOUT[variant]
    x, y = _geo(variant)[CORNER[L][n]]
    lines = _label_lines(L, n, variant)
    # baselines, relative to the first line
    ys, cur, prev = [], 0.0, None
    for cls, _ in lines:
        if prev is not None:
            cur += {'hxd-nm': lay['step_nm2'] if prev == 'hxd-nm' else lay['step_nm'], 'hxd-en': lay['step_en']}[cls]
        ys.append(cur)
        prev = cls
    if y < 0:          # top corners: the block ends just above the corner
        y0 = y - 26 - ys[-1]
    elif y > 0:        # bottom corners: the block starts below the corner
        y0 = y + 40
    else:              # pointed tips: the name sits on the corner's level (with the English name, the block is centred)
        name_i = [c for c, _ in lines].index('hxd-nm')
        y0 = y + 7 - ys[name_i] - (ys[-1] - ys[name_i] if lines[-1][0] == 'hxd-en' else 0) / 2
    right = x > 0
    dx = (26 if y == 0 else 12) * (1 if right else -1)
    anchor = 'start' if right else 'end'
    tx = round(x + dx, 2)
    return ''.join(f'<text class="{cls}" x="{tx:g}" y="{round(y0 + yy, 2):g}" text-anchor="{anchor}">{E(t)}</text>'
                   for (cls, t), yy in zip(lines, ys))


def diagram(L, variant):
    """The hero diagram (inline SVG, finished state). variant: 'wide' or 'narrow' (CSS shows one of them)."""
    D = PC[L].HEXAGON
    lay = LAYOUT[variant]
    G = _geo(variant)
    p = 'hx' + variant[0]                      # id prefix (both variants are on the page)
    vb = lay['box'][L]
    bx, by, bw, bh = map(float, vb.split())
    # the glow of the balance lines and of the centre word(s) is drawn only around the hexagon (less work per frame)
    gx, gy = -round(G['Rup'][0] + 40), -round(G['BL'][1] + 40)
    o = []
    o.append(f'<svg class="hxd hxd-{variant}" viewBox="{vb}" width="{bw:g}" height="{bh:g}" aria-hidden="true" focusable="false" '
             f'xmlns="http://www.w3.org/2000/svg">')
    o.append('<defs>'
             f'<filter id="{p}-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
             f'<filter id="{p}-glowU" filterUnits="userSpaceOnUse" x="{gx:g}" y="{gy:g}" width="{-2 * gx:g}" height="{-2 * gy:g}"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
             f'<filter id="{p}-soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>')
    # clip rectangles that "draw" the balance lines and the axis (hexagon.js animates their x / width or y / height)
    for name, (a, b, _) in zip(('top', 'mid', 'bot'), BALANCES):
        (x1, y1), (x2, _) = G[a], G[b]
        pad = 0 if name == 'mid' else 6
        o.append(f'<clipPath id="{p}-c{name}"><rect class="hxd-r{name}" x="{x1 - pad:g}" y="{y1 - 14:g}" width="{x2 - x1 + 2 * pad:g}" height="28"/></clipPath>')
    top, bot = G['TL'][1], G['BL'][1]
    o.append(f'<clipPath id="{p}-cax"><rect class="hxd-rax" x="-6" y="{top:g}" width="12" height="{bot - top:g}"/></clipPath></defs>')

    outline = ' '.join(f'{G[k][0]:g},{G[k][1]:g}' for k in OUTLINE)
    o.append(f'<polygon class="hxd-haze" points="{outline}" fill="{LIME}" opacity=".03" filter="url(#{p}-soft)"/>')
    o.append(f'<g class="hxd-stripes"><g transform="scale({K * lay["s"]:.6f}) translate({-CX:g} {-CY:g})">'
             + ''.join(f'<path class="hxd-s" fill="{c}" opacity=".13" d="{d}"/>' for c, d in stripes_order()) + '</g></g>')
    # the sides, drawn from their middle towards both corners (hidden once the outline is in place)
    o.append('<g class="hxd-sides" opacity="0">')
    for a, b in SIDES:
        (ax, ay), (bx_, by_) = G[a], G[b]
        mx, my = round((ax + bx_) / 2, 2), round((ay + by_) / 2, 2)
        ln = round(((ax - mx) ** 2 + (ay - my) ** 2) ** .5, 2)
        line = f'stroke="{LIME}" stroke-width="3" stroke-linecap="round" stroke-dasharray="{ln:g}" stroke-dashoffset="0"'
        o.append(f'<g class="hxd-side"><line x1="{mx:g}" y1="{my:g}" x2="{ax:g}" y2="{ay:g}" {line}/><line x1="{mx:g}" y1="{my:g}" x2="{bx_:g}" y2="{by_:g}" {line}/>'
                 f'<circle cx="{mx:g}" cy="{my:g}" r="4" fill="#fff" opacity="0" filter="url(#{p}-glow)"/></g>')
    o.append('</g>')
    o.append(f'<polygon class="hxd-outline" points="{outline}" fill="none" stroke="{LIME}" stroke-width="3" stroke-linejoin="round"/>')
    # the three balances: top and bottom sides, and the dashed middle line through the centre (it is not a side)
    o.append('<g class="hxd-beams">')
    for name, (a, b, pair) in zip(('top', 'mid', 'bot'), BALANCES):
        (x1, y1), (x2, y2) = G[a], G[b]
        style = 'stroke-width="4.5" stroke-dasharray="12 10"' if name == 'mid' else 'stroke-width="7"'
        o.append(f'<line class="hxd-b{name}" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="#E9F59A" {style} stroke-linecap="round" '
                 f'clip-path="url(#{p}-c{name})" filter="url(#{p}-glowU)" opacity=".95"/>')
    for name, (a, b, pair) in zip(('top', 'mid', 'bot'), BALANCES):   # wide invisible lines: hover / tap targets
        (x1, y1), (x2, y2) = G[a], G[b]
        o.append(f'<line class="hxd-hit" data-n="{pair[0]}" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="transparent" stroke-width="26" pointer-events="stroke"/>')
    o.append('</g>')
    # the trust axis: in English the word "Trust" sits on the axis, so the axis stops just above it
    segs = [(top, -46), (0, bot)] if L == 'en' else [(top, bot)]
    o.append('<g class="hxd-axis">' + ''.join(
        f'<line x1="0" y1="{a:g}" x2="0" y2="{b:g}" stroke="#fff" stroke-opacity=".6" stroke-width="2" stroke-dasharray="2 7" stroke-linecap="round" clip-path="url(#{p}-cax)"/>'
        for a, b in segs) + '</g>')
    # balance names and their two pillars, outside the hexagon (Arabic: on the left; English: on the right)
    if lay['bal_x']:
        sgn = -1 if L == 'ar' else 1
        bxl, anc = sgn * lay['bal_x'][L], 'end' if L == 'ar' else 'start'
        dy = 20 if L == 'ar' else 18   # the Arabic pillar pairs are set larger (site.css)
        o.append('<g class="hxd-bals">')
        for i, (a, b, _) in enumerate(BALANCES):
            y = G[a][1]
            bal = D['balances'][i]
            lead = ''
            if y != 0:   # dotted leader from the side's end to the label
                x_end = max(abs(G[a][0]), abs(G[b][0])) + 26
                lead = f'<line x1="{bxl - sgn * 14:g}" y1="{y:g}" x2="{sgn * x_end:g}" y2="{y:g}" stroke="#4A4F57" stroke-width="1.5" stroke-dasharray="3 5"/>'
            pair = ''.join(f'<text class="hxd-bp" x="{bxl:g}" y="{y + dy + 17 * j:g}" text-anchor="{anc}">{E(t)}</text>'
                           for j, t in enumerate(WRAP[variant].get(bal['pair'], [bal['pair']])))
            o.append(f'<g class="hxd-bal" data-b="{i}">{lead}<text class="hxd-bn" x="{bxl:g}" y="{y - 4:g}" text-anchor="{anc}">{E(bal["name"])}</text>{pair}</g>')
        o.append('</g>')
    # the six corners and their names
    o.append('<g class="hxd-verts">')
    for n in range(1, 7):
        k = CORNER[L][n]
        x, y = G[k]
        o.append(f'<g class="hxd-v" data-n="{n}" data-k="{PERIM.index(k)}">'
                 f'<circle class="hxd-ring" cx="{x:g}" cy="{y:g}" r="8" fill="none" stroke="{LIME}" stroke-width="2" opacity="0"/>'
                 f'<circle class="hxd-flash" cx="{x:g}" cy="{y:g}" r="10" fill="#fff" opacity="0" filter="url(#{p}-glow)"/>'
                 f'<circle class="hxd-dot" cx="{x:g}" cy="{y:g}" r="8" fill="{LIME}"/>'
                 f'<circle cx="{x:g}" cy="{y:g}" r="34" fill="transparent"/>'
                 f'<g class="hxd-lbl">{_label(L, n, variant)}</g></g>')
    o.append('</g>')
    # the centre: «ثقة» right of the axis and "Trust" left of it (same size and glow); English: "Trust" only
    o.append(f'<g class="hxd-center"><circle class="hxd-halo" cx="0" cy="0" r="30" fill="{LIME}" opacity=".35" filter="url(#{p}-soft)"/>'
             '<circle class="hxd-cring" cx="0" cy="0" r="12" fill="#23262B" stroke="#fff" stroke-width="2.5"/>')
    if L == 'ar':
        o.append(f'<text class="hxd-tr" x="20" y="-18" text-anchor="start" filter="url(#{p}-glowU)">{E(D["trust"])}</text>'
                 f'<text class="hxd-tr hxd-tr-lat" x="-20" y="-18" text-anchor="end" filter="url(#{p}-glowU)">{E(pages_en.HEXAGON["trust"])}</text>')
    else:
        o.append(f'<text class="hxd-tr" x="0" y="-18" text-anchor="middle" filter="url(#{p}-glowU)">{E(D["trust"])}</text>')
    o.append('</g></svg>')
    return ''.join(o)

# ---------------------------------------------------------------- small icons

_ICON_BOX = '-150 -150 300 300'   # logo units around the centre


def _icon_pts(keys):
    return ' '.join(f'{G[k][0] / K:.1f},{G[k][1] / K:.1f}' for k in keys)


def icon_corner(L, n):
    """Pillar card icon: the hexagon outline with only pillar n's corner lit."""
    x, y = (v / K for v in G[CORNER[L][n]])
    return (f'<svg class="hxi" viewBox="{_ICON_BOX}" aria-hidden="true" focusable="false">'
            f'<polygon class="hxi-o" points="{_icon_pts(OUTLINE)}"/>'
            f'<circle class="hxi-glow" cx="{x:.1f}" cy="{y:.1f}" r="46"/><circle class="hxi-dot" cx="{x:.1f}" cy="{y:.1f}" r="25"/></svg>')


def icon_balance(i):
    """Balance row icon: the hexagon outline, the faint axis and only balance i's line lit."""
    a, b, _ = BALANCES[i]
    (x1, y1), (x2, y2) = [(v / K for v in G[k]) for k in (a, b)]
    dash = ' stroke-dasharray="20 16"' if i == 1 else ''
    return (f'<svg class="hxi" viewBox="{_ICON_BOX}" aria-hidden="true" focusable="false">'
            f'<polygon class="hxi-o" points="{_icon_pts(OUTLINE)}"/>'
            f'<line class="hxi-ax" x1="0" y1="{G["TL"][1] / K:.1f}" x2="0" y2="{G["BL"][1] / K:.1f}"/>'
            f'<line class="hxi-line" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"{dash}/>'
            f'<circle class="hxi-end" cx="{x1:.1f}" cy="{y1:.1f}" r="13"/><circle class="hxi-end" cx="{x2:.1f}" cy="{y2:.1f}" r="13"/></svg>')


def _cell(cx, cy, r):
    """A regular hexagon cell, flat top and bottom, pointed left and right (as the logo)."""
    h = r * 3 ** .5 / 2
    return f'M{cx - r:.1f} {cy:.1f}L{cx - r / 2:.1f} {cy - h:.1f}L{cx + r / 2:.1f} {cy - h:.1f}L{cx + r:.1f} {cy:.1f}L{cx + r / 2:.1f} {cy + h:.1f}L{cx - r / 2:.1f} {cy + h:.1f}Z'


def icon_hive(i):
    """Hive card icons (outlined cells): 0 a cell with its entrance guarded, 1 cells sharing walls,
    2 a cell built with thin walls, 3 a sealed (capped) cell."""
    r = 15
    if i == 0:
        body = f'<path class="hxc" d="{_cell(24, 24, r)}"/><circle class="hxc-dot" cx="{24 - r:.1f}" cy="24" r="3.4"/>'
    elif i == 1:
        h = 9.5 * 3 ** .5 / 2
        body = ''.join(f'<path class="hxc" d="{_cell(x, y, 9.5)}"/>' for x, y in ((17.5, 24), (31.75, 24 - h), (31.75, 24 + h)))
    elif i == 2:
        body = f'<path class="hxc hxc-thin" d="{_cell(24, 24, r)}"/><path class="hxc hxc-thin" d="{_cell(24, 24, r * .55)}"/>'
    else:
        body = f'<path class="hxc" d="{_cell(24, 24, r)}"/><path class="hxc-fill" d="{_cell(24, 24, r * .55)}"/>'
    return f'<svg class="hxc-ico" viewBox="0 0 48 48" aria-hidden="true" focusable="false">{body}</svg>'


def honeycomb(cols=11, rows=9, r=34):
    """The faint honeycomb pattern behind "Why a hexagon?": one path of outlined cells."""
    h = r * 3 ** .5 / 2
    d = ''.join(_cell(c * 1.5 * r, row * 2 * h + (h if c % 2 else 0), r) for c in range(cols) for row in range(rows))
    w, ht = (cols - 1) * 1.5 * r + 2 * r, rows * 2 * h + h
    return (f'<svg class="hxg-comb" viewBox="{-r:.0f} {-h:.0f} {w:.0f} {ht:.0f}" aria-hidden="true" focusable="false" preserveAspectRatio="xMidYMid slice">'
            f'<path d="{d}"/></svg>')

# ---------------------------------------------------------------- page

def page_data(L):
    """Everything the template needs, besides the text."""
    from markupsafe import Markup
    D = PC[L].HEXAGON
    return dict(
        WIDE=Markup(diagram(L, 'wide')), NARROW=Markup(diagram(L, 'narrow')),
        PILLAR_ICONS=[Markup(icon_corner(L, n)) for n in range(1, 7)],
        BALANCE_ICONS=[Markup(icon_balance(i)) for i in range(3)],
        HIVE_ICONS=[Markup(icon_hive(i)) for i in range(len(D['hive']))],
        COMB=Markup(honeycomb()),
    )


def build(L, render, path_for):
    importlib.reload(pages_en); importlib.reload(pages_ar)
    D = PC[L].HEXAGON
    return [render('hexagon.html', 'hexagon', L, D['title'], D['desc'], section='hexagon', D=D, og_image=OG[L], **page_data(L))]

# ---------------------------------------------------------------- Open Graph images

OG_HTML = """<!doctype html><html lang="{L}" dir="{dir}"><head><meta charset="utf-8">
<link rel="stylesheet" href="{css}"><style>
html,body{{width:1200px;height:630px;margin:0;overflow:hidden}}
body{{background:radial-gradient(ellipse 60% 60% at 50% 62%,#2B2F35 0%,#23262B 62%,#1B1D21 100%)}}
.og{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;padding:38px 40px 26px;text-align:center}}
.og .kicker{{margin:0 0 10px;color:#C3D648;font-family:var(--f-en);letter-spacing:.24em;font-size:13px}}
.og h1{{color:#fff;font-size:{h1}px;line-height:1.2;margin:0 0 6px;letter-spacing:{ls}}}
.og .hxd{{flex:1;width:100%;min-height:0}}
</style></head><body><div class="og">
<p class="kicker" dir="ltr" lang="en">ASA HEXAGON</p>
<h1 class="hxg-title">{title}</h1>{svg}</div></body></html>"""


def build_og(dist):
    """Render the finished diagram with the page title to 1200x630 PNGs (public/assets/img/og-hexagon-<L>.png)."""
    from playwright.sync_api import sync_playwright
    from PIL import Image
    import io
    tmp = os.path.join(dist, '_og.html')   # a page next to the site's CSS and fonts (removed afterwards)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport=dict(width=1200, height=630))
            for L in ('en', 'ar'):
                D = PC[L].HEXAGON
                title = '<span class="dot"> · </span>'.join(f'<span>{E(t)}</span>' for t in D['h1'])
                open(tmp, 'w', encoding='utf-8').write(OG_HTML.format(
                    L=L, dir='rtl' if L == 'ar' else 'ltr', css='assets/css/site.css', h1=44 if L == 'en' else 46,
                    ls='-.02em' if L == 'en' else '0', title=title,
                    svg=diagram(L, 'wide').replace('<svg class="hxd ', '<svg class="hxd hxd-og ')))
                pg.goto('file://' + tmp, wait_until='load')
                pg.evaluate('document.fonts.ready')
                pg.wait_for_timeout(300)
                im = Image.open(io.BytesIO(pg.screenshot(type='png'))).convert('RGB')
                path = os.path.join(ROOT, 'public' + OG[L])
                im.quantize(256, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)
                print(f'{path}: {os.path.getsize(path) / 1024:.0f} KB')
            b.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == '__main__':
    if '--og' in sys.argv:
        build_og(os.path.join(ROOT, 'dist'))
    else:
        print(G)
