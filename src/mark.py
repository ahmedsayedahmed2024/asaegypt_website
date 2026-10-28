"""The ASA mark as inline SVG for the site's decorations: the homepage hexagon (class "brief-mark"), the faint
mark behind page heroes and cards ("mark-bg") and the large mark on About / Our Team ("mark").

The geometry comes only from asa_mark.py (never redrawn here): its five colour pieces (top-left Sky, top-right Mist,
bottom-right Ice, bottom-left Lime and the Deep Blue beam), scaled by K so the hexagon is 111 x 96.13 units, in the
tight viewBox below. The homepage outline (home.html) uses the same six corners, so it sits exactly on the
pieces' outer edges at every width.
"""
import asa_mark as am

K = 0.555                                   # mark units -> these units (R = 100 -> 55.5)
W, H = am.R * K, am.H * K                   # half width 55.5, half height 48.0644
VIEWBOX = f'{-W:g} {-H:.4f} {2 * W:g} {2 * H:.4f}'
CORNERS = [(-W / 2, -H), (W / 2, -H), (W, 0), (W / 2, H), (-W / 2, H), (-W, 0)]   # TL TR R BR BL L
OUTLINE = ' '.join(f'{x:.3f},{y:.3f}' for x, y in CORNERS)


def _clip(poly, keep_left, at=0.0):
    """The part of a polygon left (keep_left) or right of the vertical line x = at."""
    inside = (lambda p: p[0] <= at + 1e-9) if keep_left else (lambda p: p[0] >= at - 1e-9)
    out = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        if inside(a):
            out.append(a)
        if inside(a) != inside(b):
            t = (at - a[0]) / (b[0] - a[0])
            out.append((at, a[1] + t * (b[1] - a[1])))
    return out


def _d(poly):
    return 'M' + 'L'.join(f'{x * K:.2f} {y * K:.2f}' for x, y in poly) + 'Z'


def pieces(seam=0.0):
    """The five colour pieces in the order they appear: [(name, colour, polygon in mark units)].
    seam > 0 lets each left quarter run that far under its right neighbour (opaque drawings: no hairline)."""
    (_, top), (_, beam), (_, bot) = am.pieces(True)
    tl, tr, bl, br = am.QUARTERS
    return [('tl', tl, _clip(top, True, seam)), ('tr', tr, _clip(top, False)),
            ('br', br, _clip(bot, False)), ('bl', bl, _clip(bot, True, seam)), ('beam', am.BEAM_FIRM, beam)]


def svg(cls='mark', animate=False):
    """The mark: five <path class="s nm-<piece>"> (--i = order of appearance). The brief mark is see-through,
    so its quarters meet exactly at x = 0; the other ones are opaque and overlap by a hair."""
    seam = 0.0 if cls == 'brief-mark' else 0.6
    # see-through: the right quarters get a hairline stroke in their own colour, which closes the seam while the pieces
    # are opaque (intro) without a visible double layer at rest
    hair = lambda n, c: f' stroke="{c}" stroke-width=".25"' if seam == 0 and n in ('tr', 'br') else ''
    parts = ''.join(f'<path class="s nm-{n}" style="--i:{i}" fill="{c}"{hair(n, c)} d="{_d(p)}"/>' for i, (n, c, p) in enumerate(pieces(seam)))
    return f'<svg class="{cls}" viewBox="{VIEWBOX}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{parts}</svg>'


def shine_svg(cls='hxg-mark'):
    """The mark above the "ASA HEXAGON" kicker on the ASA Hexagon page: the five opaque colour pieces, then the same
    five shapes in white on top (class "hxl hxl-<piece>", --k = order tl, tr, br, bl, beam), invisible at rest. The
    CSS light wave (site.css, "ASA Hexagon: the mark and kicker shine") flashes them one after another, like the
    light wave of the email signature banner."""
    shapes = pieces(0.6)
    parts = ''.join(f'<path fill="{c}" d="{_d(p)}"/>' for _, c, p in shapes)
    glow = ''.join(f'<path class="hxl hxl-{n}" style="--k:{k}" fill="#fff" d="{_d(p)}"/>' for k, (n, _, p) in enumerate(shapes))
    return f'<svg class="{cls}" viewBox="{VIEWBOX}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">{parts}{glow}</svg>'


if __name__ == '__main__':
    print(svg())
