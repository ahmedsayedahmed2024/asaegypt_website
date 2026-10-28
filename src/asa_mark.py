"""ASA mark (approved October 2026) - the single source of truth for the ASA logo.

Pure Python, no dependencies. Every logo file is generated from the numbers below.
Never redraw the mark by hand; never change these numbers or colours.

Geometry (mark units, origin at the centre, y pointing down):
  - Regular hexagon, flat top and bottom, pointed left and right, circumradius R = 100.
    Corners: L(-100,0) TL(-50,-H) TR(50,-H) R(100,0) BR(50,H) BL(-50,H), H = 50*sqrt(3) = 86.6025.
  - Three pieces separated by two horizontal gaps of 6 units:
      top piece    y in [-H, -15]
      beam         y in [-9, 9], full width: its two pointed tips ARE corners L and R
      bottom piece y in [15, H]
  - Balance point: a V notch cut into the top piece's lower edge and the bottom piece's upper edge,
    centred on x = 0, half-width 14, depth 16 (apexes at y = -31 and y = 31). With the gaps it forms a
    small diamond-shaped opening around the centre of the beam. Keep it small: never enlarge it.
  - Colour version (prism): the top and bottom pieces are split at x = 0 into four quarters, each in its
    own colour, in the same places as the earlier ASA logo; the beam carries the firm colour (Deep Blue)
    or, for a department, that department's beam colour.
  - Small version (32 px and below: favicons, tiny icons): the same pieces WITHOUT the notch.
"""
import math, re

R = 100.0
H = 50 * math.sqrt(3)          # 86.60254
GAP = 6.0
BEAM = 9.0                     # half thickness of the beam
NOTCH_W, NOTCH_D = 14.0, 16.0
YT = -(BEAM + GAP)             # -15: lower edge of the top piece
YB = BEAM + GAP                #  15: upper edge of the bottom piece
VIEWBOX = f'{-R:g} {-H:.4f} {2 * R:g} {2 * H:.4f}'   # tight box around the hexagon

# ---- ASA colours -------------------------------------------------------------------------
SKY, MIST, ICE = '#80CAE3', '#99D3EA', '#B2DCF2'
LIME, DEEP_BLUE = '#C3D648', '#1C7AA6'
CHARCOAL, GREY, WHITE, BLACK = '#23262B', '#949599', '#FFFFFF', '#000000'
COLOURS = [  # name, hex (CMYK is an approximate conversion; the printer matches it to a real proof)
    ('ASA Sky', SKY), ('ASA Mist', MIST), ('ASA Ice', ICE), ('ASA Lime', LIME),
    ('ASA Deep Blue', DEEP_BLUE), ('ASA Charcoal', CHARCOAL), ('ASA Grey', GREY)]
# quarters: top-left, top-right, bottom-left, bottom-right (same places as the earlier ASA logo)
QUARTERS = (SKY, MIST, LIME, ICE)
BEAM_FIRM = DEEP_BLUE


def rgb(hexc):
    return tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))


def cmyk(hexc):
    r, g, b = [v / 255 for v in rgb(hexc)]
    k = 1 - max(r, g, b)
    if k >= 1:
        return (0, 0, 0, 100)
    return tuple(round(100 * v) for v in ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k))


def _lx(y):
    """x of the hexagon's left side at height y (the right side is -_lx(y))."""
    return -R + abs(y) / H * (R / 2)


def pieces(notch=True):
    """[(name, [(x, y), ...])] for top, beam, bottom (closed polygons)."""
    w, d = (NOTCH_W, NOTCH_D) if notch else (0, 0)
    top = [(_lx(-H), -H), (-_lx(-H), -H), (-_lx(YT), YT)]
    top += [(w, YT), (0, YT - d), (-w, YT)] if notch else []
    top += [(_lx(YT), YT)]
    beam = [(-R, 0), (_lx(-BEAM), -BEAM), (-_lx(-BEAM), -BEAM), (R, 0), (-_lx(BEAM), BEAM), (_lx(BEAM), BEAM)]
    bot = [(_lx(YB), YB)]
    bot += [(-w, YB), (0, YB + d), (w, YB)] if notch else []
    bot += [(-_lx(YB), YB), (-_lx(H), H), (_lx(H), H)]
    return [('top', top), ('beam', beam), ('bottom', bot)]


def _clip(poly, keep_left):
    """Sutherland-Hodgman clip of a polygon against x <= 0 (keep_left) or x >= 0."""
    inside = (lambda p: p[0] <= 1e-9) if keep_left else (lambda p: p[0] >= -1e-9)
    out = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        if inside(a):
            out.append(a)
        if inside(a) != inside(b):
            t = (0 - a[0]) / (b[0] - a[0])
            out.append((0.0, a[1] + t * (b[1] - a[1])))
    clean = []
    for p in out:
        if not clean or abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
            clean.append(p)
    return clean


def _d(poly, tf=lambda x, y: (x, y)):
    return 'M' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in (tf(x, y) for x, y in poly)) + 'Z'


def mark_paths(style='prism', notch=True, tf=lambda x, y: (x, y), beam=BEAM_FIRM):
    """SVG <path> elements of the mark.
    style: 'prism' (colour; 'prism-light' and 'prism-dark' are accepted as the same thing), 'black', 'white'.
    beam: the beam colour of the prism version (firm = Deep Blue; a department may use its own)."""
    (_, t), (_, b), (_, o) = pieces(notch)
    if style in ('black', 'white'):
        c = BLACK if style == 'black' else WHITE
        return ''.join(f'<path fill="{c}" d="{_d(p, tf)}"/>' for p in (t, b, o))
    tl, tr, bl, br = QUARTERS
    # each piece is drawn whole in its left colour, then its right half on top: no hairline at the seam
    return (f'<path fill="{tl}" d="{_d(t, tf)}"/><path fill="{tr}" d="{_d(_clip(t, False), tf)}"/>'
            f'<path fill="{beam}" d="{_d(b, tf)}"/>'
            f'<path fill="{bl}" d="{_d(o, tf)}"/><path fill="{br}" d="{_d(_clip(o, False), tf)}"/>')


NS = 'xmlns="http://www.w3.org/2000/svg"'


def mark_svg(style='prism', notch=True, pad=0.0, bg=None, title='ASA', beam=BEAM_FIRM):
    x, y, w, h = -R - pad, -H - pad, 2 * R + 2 * pad, 2 * H + 2 * pad
    rect = f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" fill="{bg}"/>' if bg else ''
    return (f'<svg {NS} viewBox="{x:.4f} {y:.4f} {w:.4f} {h:.4f}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{rect}{mark_paths(style, notch, beam=beam)}</svg>')


def square_icon_svg(style='prism', notch=True, side_ratio=1.0, bg=None, rx=0, beam=BEAM_FIRM):
    """The mark centred in a square. side_ratio = square side / mark width (200 units)."""
    s = 2 * R * side_ratio
    rect = f'<rect x="{-s / 2:.4f}" y="{-s / 2:.4f}" width="{s:.4f}" height="{s:.4f}" rx="{rx:g}" fill="{bg}"/>' if bg else ''
    return f'<svg {NS} viewBox="{-s / 2:.4f} {-s / 2:.4f} {s:.4f} {s:.4f}">{rect}{mark_paths(style, notch, beam=beam)}</svg>'


# ---- horizontal lockup: mark + the outlined "ASA" wordmark ------------------------------------
# Same height as the earlier 900x268 logo: the mark is 250 units tall (y 8.48 .. 258.48), its left tip
# at x = 0; the wordmark keeps its exact outline and size, WORD_GAP units after the beam's right tip.
LOCK_H = 268
_S = 250 / (2 * H)                       # 1.443376: mark units -> lockup units
_MX, _MY = R * _S, 133.48                # mark centre in the lockup
WORD_GAP = 30.0                          # space between the beam tip and the first A (approved)
WORD_DX = 2 * R * _S + WORD_GAP - 244    # shift of the original wordmark (it started at x = 244)
LOCK_W = math.ceil(888.3 + WORD_DX + 1)  # right edge of the last A + 1
LOCK_VIEWBOX = f'-1 0 {LOCK_W + 1} 268'
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


def _shift_path(d, dx):
    """Shift an absolute-coordinate path (M, L, C, Z only) by dx."""
    toks = re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?', d)
    out, i = [], 0
    for t in toks:
        if t in 'MLCZ':
            out.append(t); i = 0
        else:
            v = float(t) + (dx if i % 2 == 0 else 0)
            out.append(f'{v:.2f}'.rstrip('0').rstrip('.')); i += 1
    s = ''
    for t in out:
        s += t if t in 'MLCZ' else ((' ' if s and s[-1] not in 'MLCZ' else '') + t)
    return s


WORDMARK_SHIFTED = _shift_path(WORDMARK, WORD_DX)


def lockup_tf(x, y):
    return (_MX + x * _S, _MY + y * _S)


def lockup_svg(style='prism', word_fill=CHARCOAL, notch=True, beam=BEAM_FIRM):
    """Mark + ASA. Light backgrounds: word_fill=CHARCOAL. Dark backgrounds: word_fill=WHITE."""
    return (f'<svg {NS} viewBox="{LOCK_VIEWBOX}" width="{LOCK_W + 1}" height="{LOCK_H}" role="img" aria-label="ASA">'
            f'<title>ASA</title>{mark_paths(style, notch, lockup_tf, beam)}'
            f'<path fill="{word_fill}" fill-rule="evenodd" d="{WORDMARK_SHIFTED}"/></svg>')


def pattern_tile_svg(cell=60.0, beam=SKY, faint=SKY, faint_opacity=0.14, bg=None):
    """Seamless brand pattern: tessellated small marks whose beams line up like ledger rows."""
    s = cell / 100
    tw, th = 3 * R * s, 2 * H * s
    out = []
    for (cx, cy) in [(0, 0), (1.5 * R * s, H * s), (3 * R * s, 0), (0, 2 * H * s), (3 * R * s, 2 * H * s),
                     (1.5 * R * s, -H * s)]:
        tf = lambda x, y, cx=cx, cy=cy: (cx + x * s * 0.94, cy + y * s * 0.94)
        (_, t), (_, b), (_, o) = pieces(False)
        out.append(f'<path fill="{faint}" fill-opacity="{faint_opacity}" d="{_d(t, tf)}{_d(o, tf)}"/>')
        out.append(f'<path fill="{beam}" fill-opacity=".55" d="{_d(b, tf)}"/>')
    rect = f'<rect width="{tw:.2f}" height="{th:.2f}" fill="{bg}"/>' if bg else ''
    return f'<svg {NS} viewBox="0 0 {tw:.2f} {th:.2f}" width="{tw:.2f}" height="{th:.2f}">{rect}{"".join(out)}</svg>'


# ---- the filed lockup: mark + ASA + "AHMED SAYED AHMED" (EGIPA application 643926) ------------------
# This is the public logo: "ASA" is never shown without the name line (ASA alone is registered by another
# office in classes 35 and 36). Name line and symbols are Plus Jakarta Sans ExtraBold, outlined.
NAME_LINE = "M94.3 340 109.8 294H122.5L138.1 340H127.7L124.6 330.6H107.7L104.6 340ZM110.4 322.3H121.9L114.9 300.5H117.5ZM148.4 340V294H158V313.9H175.9V294H185.5V340H175.9V322.2H158V340ZM199.2 340V294H208.4L225.6 316.8H221.3L238.1 294H247.3V340H237.7V304.6L241.6 305.4L223.9 328.3H222.6L205.5 305.4L208.7 304.6V340ZM261 340V294H292V302.3H270.6V312.8H290.7V321.1H270.6V331.7H292V340ZM303 340V294H318Q325.4 294 330.9 297Q336.4 299.9 339.4 305.1Q342.5 310.3 342.5 317Q342.5 323.6 339.4 328.9Q336.4 334.1 330.9 337Q325.4 340 318 340ZM312.5 331.7H318.2Q322.7 331.7 326 329.8Q329.3 328 331.1 324.7Q332.9 321.4 332.9 317Q332.9 312.5 331.1 309.2Q329.3 305.9 326 304.1Q322.7 302.3 318.2 302.3H312.5ZM387.5 340.7Q383.2 340.7 379.4 339.2Q375.6 337.6 372.9 334.7Q370.1 331.8 368.8 327.8L376.6 324.3Q378.3 328.1 381.4 330.2Q384.5 332.4 388.2 332.4Q390.1 332.4 391.6 331.8Q393 331.2 393.8 330.1Q394.6 329 394.6 327.5Q394.6 325.9 393.6 324.8Q392.6 323.6 390.5 323L381.5 320Q376 318.2 373.2 314.9Q370.4 311.6 370.4 307Q370.4 302.9 372.4 299.8Q374.5 296.7 378.1 295Q381.7 293.3 386.4 293.3Q390.5 293.3 394 294.7Q397.5 296.1 400.1 298.7Q402.7 301.3 404 304.9L396.2 308.4Q394.9 305.2 392.3 303.4Q389.7 301.6 386.4 301.6Q384.5 301.6 383 302.2Q381.5 302.8 380.7 304Q379.9 305.1 379.9 306.6Q379.9 308.2 380.9 309.4Q382 310.6 384.1 311.3L392.9 314.1Q398.5 315.9 401.2 319.1Q404 322.3 404 327Q404 331 401.9 334.1Q399.8 337.2 396.1 339Q392.4 340.7 387.5 340.7ZM412.9 340 428.5 294H441.2L456.8 340H446.3L443.2 330.6H426.4L423.3 340ZM429 322.3H440.6L433.5 300.5H436.1ZM479 340V319.9L463.7 294H474.6L485.7 313.5H481.8L492.9 294H503.8L488.6 319.9V340ZM514.1 340V294H545.1V302.3H523.7V312.8H543.8V321.1H523.7V331.7H545.1V340ZM556 340V294H571Q578.5 294 584 297Q589.5 299.9 592.5 305.1Q595.6 310.3 595.6 317Q595.6 323.6 592.5 328.9Q589.5 334.1 584 337Q578.5 340 571 340ZM565.6 331.7H571.3Q575.8 331.7 579.1 329.8Q582.3 328 584.2 324.7Q586 321.4 586 317Q586 312.5 584.2 309.2Q582.3 305.9 579.1 304.1Q575.8 302.3 571.3 302.3H565.6ZM620.5 340 636.1 294H648.8L664.3 340H653.9L650.8 330.6H634L630.9 340ZM636.6 322.3H648.2L641.1 300.5H643.7ZM674.7 340V294H684.2V313.9H702.1V294H711.7V340H702.1V322.2H684.2V340ZM725.4 340V294H734.7L751.9 316.8H747.6L764.3 294H773.6V340H764V304.6L767.8 305.4L750.1 328.3H748.9L731.8 305.4L735 304.6V340ZM787.3 340V294H818.2V302.3H796.8V312.8H817V321.1H796.8V331.7H818.2V340ZM829.2 340V294H844.2Q851.7 294 857.2 297Q862.7 299.9 865.7 305.1Q868.7 310.3 868.7 317Q868.7 323.6 865.7 328.9Q862.7 334.1 857.2 337Q851.7 340 844.2 340ZM838.8 331.7H844.5Q849 331.7 852.2 329.8Q855.5 328 857.3 324.7Q859.2 321.4 859.2 317Q859.2 312.5 857.3 309.2Q855.5 305.9 852.2 304.1Q849 302.3 844.5 302.3H838.8Z"
TM_MARK = "M983 42V17.4H975.4V12H996.8V17.4H989.3V42ZM1000.7 42V12H1006.7L1017.9 26.9H1015.1L1026 12H1032.1V42H1025.8V18.9L1028.3 19.4L1016.8 34.3H1016L1004.8 19.4L1006.9 18.9V42Z"
R_MARK = "M1004.8 56Q998.7 56 993.7 53Q988.7 50 985.7 45Q982.8 40 982.8 33.9Q982.8 27.8 985.7 22.8Q988.7 17.8 993.7 14.9Q998.7 12 1004.8 12Q1009.4 12 1013.3 13.7Q1017.3 15.3 1020.3 18.3Q1023.3 21.3 1025 25.3Q1026.7 29.3 1026.7 34Q1026.7 40 1023.8 45Q1020.9 50 1015.9 53Q1010.9 56 1004.8 56ZM1004.8 49.6Q1009.1 49.6 1012.6 47.5Q1016.1 45.4 1018.2 41.8Q1020.3 38.2 1020.3 34Q1020.3 29.6 1018.2 26Q1016.1 22.5 1012.5 20.4Q1009 18.3 1004.8 18.3Q1000.4 18.3 996.9 20.4Q993.3 22.5 991.2 26.1Q989.1 29.7 989.1 34Q989.1 38.3 991.2 41.9Q993.3 45.5 996.9 47.5Q1000.5 49.6 1004.8 49.6ZM995.1 45.6V22.3H1005.7Q1009.5 22.3 1012 24.1Q1014.5 26 1014.5 30.2Q1014.5 33 1013.2 34.6Q1011.9 36.3 1010.1 37.2L1014.8 45.6H1007.6L1003.3 37.8H1002V45.6ZM1002 32.2H1005.9Q1006.8 32.2 1007.4 31.6Q1007.9 31 1007.9 30.1Q1007.9 29.2 1007.4 28.6Q1006.8 28 1005.9 28H1002Z"
NAMED_VIEWBOX = '-1 0 1045 352'
NAMED_W = 1045


def named_lockup_svg(style='prism', word_fill=CHARCOAL, symbol='tm', notch=True, beam=BEAM_FIRM):
    """Public logo: mark + ASA + AHMED SAYED AHMED. symbol: 'tm' (until the registration certificate),
    'r' (only after registration), or None."""
    sym = {'tm': TM_MARK, 'r': R_MARK}.get(symbol, '')
    sym_path = f'<path fill="{word_fill}" d="{sym}"/>' if sym else ''
    return (f'<svg {NS} viewBox="{NAMED_VIEWBOX}" width="{NAMED_W}" height="352" role="img" aria-label="ASA Ahmed Sayed Ahmed">'
            f'<title>ASA Ahmed Sayed Ahmed</title>{mark_paths(style, notch, lockup_tf, beam)}'
            f'<path fill="{word_fill}" fill-rule="evenodd" d="{WORDMARK_SHIFTED}"/>'
            f'<path fill="{word_fill}" d="{NAME_LINE}"/>{sym_path}</svg>')


# ---- ASA NEXT icon (sub-brand exception: the only tilted use of the mark) ------------------------
NEXT_ANGLE = 10.4   # degrees, rising to the right (same angle as the earlier ASA NEXT icon)


def next_spark_svg():
    """ASA NEXT icon: the colour mark tilted NEXT_ANGLE degrees, rising to the right, with two lime sparks.
    Same viewBox as the earlier asa-next-spark.svg, so the site's CSS sizes stay unchanged.
    Used only together with the "ASA NEXT" wordmark; never for the firm or the departments."""
    a = math.radians(-NEXT_ANGLE)
    s = 0.5473928595699897          # fits the mark's rotated width into the earlier icon's 107.68 units
    def tf(x, y):
        xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        return (xr * s - 6, yr * s)
    sparks = ('<path fill="#C3D648" d="M46.00 -62.00 L48.77 -50.77 L60.00 -48.00 L48.77 -45.23 L46.00 -34.00 '
              'L43.23 -45.23 L32.00 -48.00 L43.23 -50.77Z"/>'
              '<path fill="#C3D648" fill-opacity=".7" d="M58.00 -32.00 L59.19 -27.19 L64.00 -26.00 L59.19 -24.81 '
              'L58.00 -20.00 L56.81 -24.81 L52.00 -26.00 L56.81 -27.19Z"/>')
    return f'<svg viewBox="-64 -66 128 132" {NS}>{mark_paths("prism", True, tf)}{sparks}</svg>'


if __name__ == '__main__':
    import sys
    sys.stdout.write(mark_svg() + '\n')
