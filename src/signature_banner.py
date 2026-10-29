"""The email signature banner and the "Latest" pages (/latest/, /ar/latest/). See CLAUDE.md, "Email signature banner".

Every build writes, from the site data only (never by hand, never committed):
  dist/assets/img/signature/banner-en.gif, banner-ar.gif  animated, 896x224 (shown at 448x112), loops forever
  dist/assets/img/signature/banner-en.png, banner-ar.png  the first frame as a still image
The banner shows the 3 items most recently added to ASA Briefing and ASA Insights (same `added` order as the
homepage hexagon; ASA NEXT is left out). Sent emails load these URLs, so they must never change.

Frames are drawn by headless Chromium (Playwright) from an HTML/SVG template with the site's own fonts embedded,
so Arabic is shaped and laid out right to left by the browser. Pillow assembles the GIF; gifsicle (if installed)
shrinks it. Frame 1 is item 1, complete: Outlook on Windows shows only the first frame.
If rendering fails, the build goes on: the banners currently on asaegypt.com are kept (downloaded), or else a
simple static banner is written, and a warning is printed.

Run on its own (after a build): python src/signature_banner.py
"""
import base64, datetime, functools, io, json, math, os, shutil, subprocess, sys, tempfile, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import articles_meta, news, pages_en, pages_ar, asa_mark, mark

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'public/assets/fonts')
OUT_DIR = 'assets/img/signature'          # inside dist/; URLs used by sent emails: never change
FILES = ['banner-en.gif', 'banner-ar.gif', 'banner-en.png', 'banner-ar.png']
LIVE = 'https://asaegypt.com/' + OUT_DIR + '/'
PC = {'en': pages_en, 'ar': pages_ar}

COUNT = 3                 # items in the banner and on /latest/
NEW_DAYS = 7              # "NEW" tag on item 1 when it was added in the last 7 days
W, H, SCALE = 448, 112, 2  # CSS size; rendered at 2x
HOLD_MS = 3500            # each item stays 3.5 s
TRANSITION_MS = 840       # change between items: 12 frames of 70 ms
# the light along the letters of "ASA HEXAGON" (A to N) right after the wave over the mark reaches the beam, like the
# Hexagon page (site.css, "ASA Hexagon: the mark and kicker shine"): each letter brightens to pale lime with a soft
# lime glow, then back to lime. It starts during the change and ends in extra frames before the hold (still 3.5 s).
TAG = 'ASA HEXAGON'
LETTER_AFTER_BEAM_MS = 110  # first letter's peak after the beam's
LETTER_GAP_MS = 75          # between letters
LETTER_RISE_MS, LETTER_FALL_MS = 180, 280
MAX_KB = 290              # each GIF stays under this (check_links.py fails the build over 300 KB)
# file size ladder: (transition frames, text steps per transition, gifsicle --lossy); the first one under MAX_KB
# is kept. The light wave moves on every frame; the text fade has fewer steps (each one redraws the whole text
# area, the biggest cost). Fewer steps come before lossy compression, which also softens the text.
LADDER = [(12, 6, 0), (12, 4, 0), (12, 4, 20), (12, 3, 40), (8, 2, 60)]
EN_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def today():
    return datetime.datetime.now(datetime.timezone.utc).date()


def short_date(iso, L, B):
    if L == 'ar':
        return B.fmt_date(iso, L)  # «18 أكتوبر 2026»
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {EN_MONTHS[d.month - 1]} {d.year}"  # "18 Oct 2026"


def latest_items(L, B, from_path='/'):
    """The COUNT items most recently added to Briefing and Insights, newest first, for one language.
    B is the build module (sort order, links, images and reading times come from there)."""
    i = 0 if L == 'en' else 1
    D = PC[L].LATEST
    arts = {a['slug']: a for a in articles_meta.ARTICLES}
    items = {n['slug']: n for n in news.NEWS}
    out = []
    for pos, (kind, slug) in enumerate(B.recently_added(COUNT, ('article', 'news'))):
        if kind == 'news':
            x = items[slug]  # meta shows the source's date (`date`), never `added`
            title = x['title_' + L]
            region = news.REGIONS[x['region']][i]
            d = dict(kicker=D['kicker_news'], tag=news.CATEGORIES[x['category']][i], title=title,
                     short=x.get('short_' + L) or title, summary=x['summary_' + L],
                     meta=[region, short_date(x['date'], L, B)], meta_page=[region, B.fmt_date(x['date'], L)],
                     url=B.link('news-' + slug, L, from_path), image=B.image_for(x, 'news', L), date_iso=x['date'])
        else:
            x = arts[slug]
            cat = articles_meta.CATEGORIES[x['category']][i]
            read = B.read_time(B.guide.minutes(slug) if slug in B.guide.GUIDES else x['minutes'], L)
            d = dict(kicker=D['kicker_article'], tag=cat, title=x['title'][i], short=x.get('short', x['title'])[i],
                     summary=x['summary'][i], meta=[cat, read], meta_page=[cat, read],
                     url=B.link('art-' + slug, L, from_path), image=B.image_for(x, 'article', L), date_iso=x['date'])
        added = datetime.date.fromisoformat(x.get('added') or x['date'])
        d.update(kind=kind, slug=slug, new=pos == 0 and 0 <= (today() - added).days < NEW_DAYS)
        out.append(d)
    return out


def build_page(L, render, B):
    """/latest/ and /ar/latest/: where the signature banner links to. noindex, not in the sitemap or the menu."""
    D = PC[L].LATEST
    return [render('latest.html', 'latest', L, D['title'], D['desc'], D=D, noindex=True,
                   ITEMS=latest_items(L, B, B.path_for('latest', L)))]


# ---------------------------------------------------------------- the banner template

def font_face(family, weight, fname, urange=''):
    data = base64.b64encode(open(os.path.join(FONTS, fname), 'rb').read()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')"
            + (f";unicode-range:{urange}" if urange else '') + '}')


AR_RANGE = 'U+0600-06FF,U+0750-077F,U+08A0-08FF,U+200C-200F,U+FB50-FDFF,U+FE70-FEFC'


def fonts_css(L):
    if L == 'en':
        return ''.join(font_face('Sans', w, f'pjs-{w}.woff2') for w in (400, 700, 800))
    return ''.join(font_face('Sans', w, f'plexar-lat-{w}.woff2') + font_face('Sans', w, f'plexar-ar-{w}.woff2', AR_RANGE)
                   for w in (400, 700))


def pieces():
    """The five colour pieces of the ASA mark (asa_mark.py), in the order of the site intro (mark.py: top-left,
    top-right, bottom-right, bottom-left, then the beam): [(colour, polygon in mark units)]."""
    return [(c, poly) for _, c, poly in mark.pieces(seam=0.6)]  # opaque: the left quarters run a hair under the right ones


def _d(poly):
    return 'M' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in poly) + 'Z'


def tm_path_polys():
    """asa_mark.TM_MARK (the TM of the header logo: M, H, V, L, Z only) as polygons, for the Pillow fallback."""
    import re
    polys, x, y = [], 0.0, 0.0
    for cmd, args in re.findall(r'([MHVLZ])([^MHVLZ]*)', asa_mark.TM_MARK):
        v = [float(a) for a in re.findall(r'-?\d+(?:\.\d+)?', args)]
        if cmd == 'M':
            x, y = v[0], v[1]; polys.append([(x, y)]); v = v[2:]; cmd = 'L'
        if cmd == 'L':
            for k in range(0, len(v), 2):
                x, y = v[k], v[k + 1]; polys[-1].append((x, y))
        elif cmd == 'H':
            for x in v: polys[-1].append((x, y))
        elif cmd == 'V':
            for y in v: polys[-1].append((x, y))
    return polys


TAG_FONT = os.path.join(FONTS, 'pjs-800.woff2')  # the tag's font (Plus Jakarta Sans ExtraBold)
TAG_PX = 7.5              # the tag's letter size (CSS px; drawn at SCALE)
TAG_LS = 1.3 / 7.5        # the tag's letter-spacing (1.3px at 7.5px), in em
# the TM after the N: the superscript proportions of the Hexagon page (mark.TM_H tall, its bottom mark.TM_RAISE above
# the baseline) and its gap after the N's ink, TM_GAP (there: the .24em letter-spacing + the N's .072em side bearing);
# never under TM_MIN_PX device pixels tall (legibility at email size), with the same raise and gap
TM_GAP = 0.312
TM_MIN_PX = 4
TM_H = max(mark.TM_H, TM_MIN_PX / SCALE / TAG_PX)
TAG_DEPTH = 0.15          # optical spacing: openings deeper than this share of the cap height count only up to it


@functools.lru_cache(maxsize=None)
def tag_layout():
    """Even, optical spacing for the letters of "ASA HEXAGON", in em (the same at any size): at the tag's tiny size the
    font's own spacing looks uneven (S-A, A-G and O-N open). For each pair of letters, the space between them is
    measured row by row over the cap height (an opening deeper than TAG_DEPTH of the cap height, such as the top of
    an A, counts only up to that depth) and averaged; every pair is set to the same average, the mean of the font's
    own pairs at the old letter-spacing (1.3px), so the word keeps about its width; the word space stays as before.
    Used by the animated banner (and so its PNG) and by static_banner().
    Returns x (each letter's origin), adv (advances), left (ink start of the first letter), right (ink end of the last).
    None if the font tools are missing (the tag then keeps the plain letter-spacing)."""
    try:
        from fontTools.ttLib import TTFont
        from PIL import Image, ImageDraw, ImageFont
        tt = TTFont(TAG_FONT)
        upm, cmap, hmtx = tt['head'].unitsPerEm, tt.getBestCmap(), tt['hmtx']
        cap = tt['OS/2'].sCapHeight / upm
        adv = lambda ch: hmtx[cmap[ord(ch)]][0] / upm
        S = 200
        font = ImageFont.truetype(TAG_FONT, S)

        def rows(ch):  # {row: (ink left, ink right)} over the cap height, in em from the glyph's origin
            im = Image.new('L', (2 * S, 2 * S), 0)
            ImageDraw.Draw(im).text((S // 2, 3 * S // 2), ch, font=font, fill=255, anchor='ls')
            im = im.point(lambda v: 255 if v > 127 else 0)
            out = {}
            for y in range(3 * S // 2 - round(cap * S), 3 * S // 2):
                bb = im.crop((0, y, 2 * S, y + 1)).getbbox()
                if bb:
                    out[y] = ((bb[0] - S // 2) / S, (bb[2] - S // 2) / S)
            return out
        word = TAG.replace(' ', '')
        P = {ch: rows(ch) for ch in set(word)}
        depth = TAG_DEPTH * cap

        def space(a, b, d):  # average optical space between a and b with b's origin d after a's
            g = [d + P[b][y][0] - P[a][y][1] for y in P[a] if y in P[b]]
            m = min(g)
            return sum(min(v, m + depth) for v in g) / len(g)
        gap_at = TAG.index(' ')  # the word space comes after this many letters
        pairs = [(word[i], word[i + 1]) for i in range(len(word) - 1)]
        own = [space(a, b, adv(a) + TAG_LS) for k, (a, b) in enumerate(pairs) if k != gap_at - 1]
        target = sum(own) / len(own)
        x = [0.0]
        for k, (a, b) in enumerate(pairs):
            if k == gap_at - 1:  # the word space: as the font sets it with the old letter-spacing
                x.append(x[-1] + adv(a) + TAG_LS + adv(' ') + TAG_LS)
                continue
            lo, hi = 0.0, 2.0
            for _ in range(50):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if space(a, b, mid) < target else (lo, mid)
            x.append(x[-1] + lo)
        return dict(x=x, adv=[adv(ch) for ch in word],
                    left=min(l for l, _ in P[word[0]].values()), right=x[-1] + max(r for _, r in P[word[-1]].values()))
    except Exception as e:
        print(f'WARNING: signature banner: even tag spacing skipped ({type(e).__name__}: {e})')
        return None


@functools.lru_cache(maxsize=None)
def tag_outlines():
    """The outlines of the tag's letters from the font (TAG_FONT), in em, y down, origin on the baseline:
    {letter: [contour, ...]} with each contour a polygon (curves flattened). None without fontTools."""
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.basePen import BasePen
    except ImportError:
        return None

    class Flat(BasePen):
        def __init__(self, gs, upm):
            super().__init__(gs)
            self.k, self.out = 1 / upm, []

        def _pt(self, p):
            return (p[0] * self.k, -p[1] * self.k)

        def _moveTo(self, p):
            self.out.append([self._pt(p)])
            self.cur = p

        def _lineTo(self, p):
            self.out[-1].append(self._pt(p))
            self.cur = p

        def _curveToOne(self, a, b, c):
            p0 = self.cur
            for i in range(1, 9):
                t = i / 8
                u = 1 - t
                self.out[-1].append(self._pt((u ** 3 * p0[0] + 3 * u * u * t * a[0] + 3 * u * t * t * b[0] + t ** 3 * c[0],
                                              u ** 3 * p0[1] + 3 * u * u * t * a[1] + 3 * u * t * t * b[1] + t ** 3 * c[1])))
            self.cur = c

        def _qCurveToOne(self, a, b):
            p0 = self.cur
            for i in range(1, 9):
                t = i / 8
                u = 1 - t
                self.out[-1].append(self._pt((u * u * p0[0] + 2 * u * t * a[0] + t * t * b[0],
                                              u * u * p0[1] + 2 * u * t * a[1] + t * t * b[1])))
            self.cur = b
    tt = TTFont(TAG_FONT)
    gs, cmap, upm = tt.getGlyphSet(), tt.getBestCmap(), tt['head'].unitsPerEm
    out = {}
    for ch in set(TAG.replace(' ', '')):
        pen = Flat(gs, upm)
        gs[cmap[ord(ch)]].draw(pen)
        out[ch] = [c for c in pen.out if len(c) > 2]
    return out


@functools.lru_cache(maxsize=None)
def tag_paths():
    """The tag's letters as SVG path data from the font (exact curves), in font units (1 em = 1000), y down, origin on
    the baseline: {letter: d}. None without fontTools."""
    try:
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
        tt = TTFont(TAG_FONT)
        gs, cmap, upm = tt.getGlyphSet(), tt.getBestCmap(), tt['head'].unitsPerEm
        out = {}
        for ch in set(TAG.replace(' ', '')):
            pen = SVGPathPen(gs)
            gs[cmap[ord(ch)]].draw(TransformPen(pen, (1000 / upm, 0, 0, -1000 / upm, 0, 0)))
            out[ch] = pen.getCommands()
        return out
    except Exception as e:
        print(f'WARNING: signature banner: tag outlines skipped ({type(e).__name__}: {e})')
        return None


def tm_at(lay):
    """The TM's box after the N, in em from the first letter's origin and the baseline (y down): x, top, width, height."""
    h = TM_H
    return lay['right'] + TM_GAP, -(mark.TM_RAISE + h), h * mark.TM_BOX[2] / mark.TM_BOX[3], h


def tag_svg(lay, paths):
    """The letters of the tag as vector outlines from the font, each at its tag_layout() position, and the TM, in one
    SVG (font units: 1 em = 1000, y down, the first letter's origin on the baseline at 0,0). Nothing is snapped to
    the pixel grid letter by letter (HTML text is), so the spacing stays even at email size. The shine (setFrame):
    each letter (class "l") changes colour, and its two blurred copies under the letters (classes "g1", "g2", the
    old text-shadow 0 0 4px and 0 0 9px) light up. The SVG box is a whole number of CSS pixels (so it is not
    resized to the pixel grid), placed from a zero-size box on the baseline (tag_html)."""
    word = TAG.replace(' ', '')
    u = 1000 / TAG_PX                                   # font units per CSS pixel
    tx, ty, tw, th = tm_at(lay)
    left, below = 1, 2                                  # CSS px of the box before the first origin and under the baseline
    w = math.ceil((tx + tw) * TAG_PX) + left + 1
    h = math.ceil(-ty * TAG_PX) + below + 1
    vb = f'{-left * u:.2f} {-(h - below) * u:.2f} {w * u:.2f} {h * u:.2f}'
    defs = ''.join(f'<path id="tg{i}" d="{paths[ch]}" transform="translate({lay["x"][i] * 1000:.2f} 0)"/>'
                   for i, ch in enumerate(word))
    blur = ''.join(f'<filter id="tgb{n}" filterUnits="userSpaceOnUse" x="{-40 * u:.0f}" y="{-40 * u:.0f}" '
                   f'width="{(w + 80) * u:.0f}" height="{(h + 80) * u:.0f}"><feGaussianBlur stdDeviation="{r / 2 * u:.2f}"/></filter>'
                   for n, r in ((1, 4), (2, 9)))
    glow = ''.join(f'<use href="#tg{i}" class="g{n}" fill="#C3D648" opacity="0" filter="url(#tgb{n})"/>'
                   for n in (2, 1) for i in range(len(word)))
    letters = ''.join(f'<use href="#tg{i}" class="l" fill="#C3D648"/>' for i in range(len(word)))
    bx, by, bw, bh = mark.TM_BOX
    k = th * 1000 / bh
    tm = (f'<path fill="#C3D648" transform="matrix({k:.5f} 0 0 {k:.5f} {tx * 1000 - bx * k:.2f} {ty * 1000 - by * k:.2f})" '
          f'd="{asa_mark.TM_MARK}"/>')
    return (f'<svg class="tgv" viewBox="{vb}" width="{w}" height="{h}" style="left:{-left}px;bottom:{-below}px" '
            f'xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs>{defs}{blur}</defs>{glow}{letters}{tm}</svg>')


def tag_html(lay):
    """The "ASA HEXAGON" tag under the mark. With tag_layout() and the font's outlines: the letters and the lockup's
    one TM after the N (the header logo's TM, as a small superscript) drawn as vector outlines (tag_svg), from a
    zero-size box on the tag's baseline; the box is as wide as the letters were, and its padding centres their ink
    under the mark; the TM hangs outside it and never shines. Without them: the letters as text, one span per letter
    (the shine), and the TM (mark.tm_svg) in a zero-size box on the baseline."""
    paths = tag_paths() if lay else None
    if not paths:
        letters = ''.join(' ' if ch == ' ' else f'<span class="l">{ch}</span>' for ch in TAG)
        return f'<span class="tag">{letters}<i class="tmb">{mark.tm_svg()}</i></span>'
    x, adv = lay['x'], lay['adv']
    lsb, rsb = lay['left'], x[-1] + adv[-1] - lay['right']   # side space before the first and after the last letter
    pl, pr = max(0, rsb - lsb), max(0, lsb - rsb)
    style = f'width:{pl + x[-1] + adv[-1] + pr:.4f}em;padding-left:{pl:.4f}em;padding-right:{pr:.4f}em'
    return f'<span class="tag even" style="{style}"><i class="tgb">{tag_svg(lay, paths)}</i></span>'


def mark_svg():
    paths = ''.join(f'<path fill="{c}" d="{_d(p)}"/>' for c, p in pieces())
    glow = ''.join(f'<path class="w" fill="#fff" fill-opacity="0" d="{_d(p)}"/>' for _, p in pieces())
    return f'<svg class="mark" viewBox="{asa_mark.VIEWBOX}" xmlns="http://www.w3.org/2000/svg">{paths}{glow}</svg>'



TEMPLATE = """<!doctype html><html lang="{L}" dir="{dir}"><head><meta charset="utf-8"><style>
{fonts}{lat}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#23262B}}
body{{font-family:'Sans',sans-serif;color:#fff;-webkit-font-smoothing:antialiased;position:relative}}
.mk{{position:absolute;top:{mark_top}px;inset-inline-start:18px;width:82px;height:86px;display:flex;flex-direction:column;align-items:center;justify-content:space-between}}
.mark{{display:block;width:76px;height:66px;margin-top:4px}}
.mk .tag{{direction:ltr;font-family:'Lat',sans-serif;font-weight:800;font-size:{tag_px}px;line-height:9px;letter-spacing:1.3px;padding-left:1.3px;color:#C3D648;white-space:nowrap}}
.mk .tag.even{{letter-spacing:0;font-kerning:none}}
.tmb,.tgb{{position:relative;display:inline-block;width:0;height:0;vertical-align:baseline}}
.tmb .tm{{position:absolute;left:calc({tm_gap}em - 1.3px - .066em);bottom:{tm_raise}em;height:{tm_h}em;width:{tm_w}em;display:block;overflow:visible}}
.tgb .tgv{{position:absolute;display:block;overflow:visible}}
.items{{position:absolute;top:0;bottom:12px;inset-inline-start:116px;inset-inline-end:18px}}
.item{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;opacity:0}}
.kick{{display:flex;align-items:center;gap:6px;height:14px;font-weight:700;color:#C3D648;white-space:nowrap}}
.kick .t{{font-size:{kick_size}px;letter-spacing:{kick_ls};{kick_tt}}}
.dot{{width:7px;height:7px;border-radius:50%;background:#C3D648;box-shadow:0 0 0 2px rgba(195,214,72,.28);margin-inline-end:2px;flex:none}}
.new{{background:#C3D648;color:#23262B;font-size:{new_size}px;font-weight:800;letter-spacing:{new_ls};padding:1px 5px;border-radius:1.5px;line-height:12px;{kick_tt};margin-inline-start:2px}}
.title{{margin-top:5px;font-size:{title_size}px;font-weight:700;line-height:{title_lh}px;max-height:{title_max}px;overflow:hidden;color:#fff}}
.meta{{margin-top:5px;display:flex;align-items:baseline;gap:10px;font-size:10.5px;line-height:14px;color:#AEB4BC;white-space:nowrap}}
.meta .m{{overflow:hidden;text-overflow:ellipsis}}
.meta .read{{margin-inline-start:auto;color:#C3D648;font-weight:700}}
.dashes{{position:absolute;bottom:9px;inset-inline-end:18px;display:flex;gap:4px}}
.dashes i{{display:block;width:14px;height:2.5px;background:#4A4F57}}
.dashes i.on{{background:#C3D648}}
bdi{{unicode-bidi:isolate}}
</style></head><body>
<div class="mk">{mark}{tag}</div>
<div class="items">{items}</div>
<div class="dashes">{dashes}</div>
<script>
const DATA = {data};
const LATIN = /[A-Za-z][A-Za-z0-9]*(?:[ .:!\\/+\\-–][A-Za-z0-9]+)*/g;
function esc(s){{return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}
function fmt(s){{return DATA.rtl ? esc(s).replace(LATIN, m => '<bdi>' + m + '</bdi>') : esc(s)}}
// title: at most 2 lines; if longer, cut at a whole word and add an ellipsis
function fit(el, text){{
  const max = DATA.titleMax + 1;
  el.style.maxHeight = 'none';
  el.innerHTML = fmt(text);
  if (el.scrollHeight <= max) return;
  const words = text.split(' ');
  let lo = 1, hi = words.length - 1, best = 1;
  while (lo <= hi) {{
    const mid = (lo + hi) >> 1;
    el.innerHTML = fmt(words.slice(0, mid).join(' ').replace(/[\\s,;:،؛–—-]+$/, '') + '…');
    if (el.scrollHeight <= max) {{ best = mid; lo = mid + 1; }} else hi = mid - 1;
  }}
  el.innerHTML = fmt(words.slice(0, best).join(' ').replace(/[\\s,;:،؛–—-]+$/, '') + '…');
}}
document.querySelectorAll('.item').forEach((el, i) => {{
  el.querySelector('.kick .t').innerHTML = fmt(DATA.items[i].kicker);
  el.querySelector('.m').innerHTML = fmt(DATA.items[i].meta);
  fit(el.querySelector('.title'), DATA.items[i].title);
}});
const items = [...document.querySelectorAll('.item')], dashes = [...document.querySelectorAll('.dashes i')];
const glow = [...document.querySelectorAll('.mark .w')], letters = [...document.querySelectorAll('.tag .l')];
const g1 = [...document.querySelectorAll('.tag .g1')], g2 = [...document.querySelectorAll('.tag .g2')];
const mix = (a, b, v) => Math.round(a + (b - a) * v);
// one frame: {{items: {{index: [opacity, dy]}}, dash: index, wave: [5 opacities], letters: [10 levels 0..1]}}
window.setFrame = st => {{
  items.forEach((el, i) => {{
    const s = st.items[i];
    el.style.opacity = s ? s[0] : 0;
    el.style.transform = s ? 'translateY(' + s[1] + 'px)' : 'none';
  }});
  dashes.forEach((d, i) => d.classList.toggle('on', i === st.dash));
  glow.forEach((p, k) => p.setAttribute('fill-opacity', st.wave[k] || 0));
  // lime #C3D648 -> pale lime #F4F8DC with a soft lime glow, and back
  // (vector letters: the fill, and their two blurred copies for the glow; text letters: color and text-shadow)
  letters.forEach((el, k) => {{
    const v = (st.letters || [])[k] || 0;
    const c = v ? 'rgb(' + mix(195, 244, v) + ',' + mix(214, 248, v) + ',' + mix(72, 220, v) + ')' : '';
    if (g1.length) {{
      el.style.fill = c;
      g1[k].setAttribute('opacity', (.85 * v).toFixed(3));
      g2[k].setAttribute('opacity', (.35 * v).toFixed(3));
      return;
    }}
    el.style.color = c;
    el.style.textShadow = v ? '0 0 4px rgba(195,214,72,' + (.85 * v).toFixed(3) + '),0 0 9px rgba(195,214,72,' + (.35 * v).toFixed(3) + ')' : '';
  }});
}};
window.titleLines = () => items.map(el => Math.round(el.querySelector('.title').scrollHeight / DATA.titleLh));
</script></body></html>"""


def banner_html(L, items):
    ar = L == 'ar'
    title_size, title_lh = (14, 19) if ar else (13.5, 17.5)
    item_html = ''.join(
        '<div class="item"><div class="kick"><i class="dot"></i><span class="t"></span>'
        + (f'<b class="new">{PC[L].LATEST["new"]}</b>' if it['new'] else '')
        + f'</div><div class="title"></div><div class="meta"><span class="m"></span>'
        f'<span class="read">{PC[L].LATEST["read"]} {"←" if ar else "→"}</span></div></div>'
        for it in items)
    data = dict(rtl=ar, titleMax=title_lh * 2, titleLh=title_lh,
                items=[dict(kicker=it['kicker'], title=it['short'], meta=' · '.join(it['meta'])) for it in items])
    return TEMPLATE.format(
        L=L, dir='rtl' if ar else 'ltr', fonts=fonts_css(L), lat=font_face('Lat', 800, 'pjs-800.woff2'),
        W=W, H=H, mark=mark_svg(), tag=tag_html(tag_layout()), mark_top=(H - 86) // 2, tag_px=TAG_PX,
        tm_gap=TM_GAP, tm_raise=mark.TM_RAISE, tm_h=f'{TM_H:.4f}', tm_w=f'{TM_H * mark.TM_BOX[2] / mark.TM_BOX[3]:.4f}',
        items=item_html, dashes='<i></i>' * len(items), data=json.dumps(data, ensure_ascii=False),
        kick_size=11 if ar else 9.5, kick_ls='0' if ar else '2px', kick_tt='' if ar else 'text-transform:uppercase',
        new_size=10 if ar else 8, new_ls='0' if ar else '1px',
        title_size=title_size, title_lh=title_lh, title_max=title_lh * 2)


# ---------------------------------------------------------------- frames and the GIF

def ease(p):
    return p * p * (3 - 2 * p)


def wave_at(t):
    """The soft light wave over the five pieces of the mark (tl, tr, br, bl, beam), one after another, at t (0..1)."""
    return [round(0.45 * max(0.0, 1 - abs(t - (0.12 + k * 0.17)) / 0.22), 3) for k in range(5)]


def letters_at(ms, beam_ms):
    """The light on each letter of the tag (0..1) at ms after the change starts; beam_ms: the beam's peak."""
    out = []
    for j in range(sum(ch != ' ' for ch in TAG)):
        d = ms - (beam_ms + LETTER_AFTER_BEAM_MS + j * LETTER_GAP_MS)
        out.append(round(max(0.0, 1 - (-d / LETTER_RISE_MS if d < 0 else d / LETTER_FALL_MS)), 3))
    return out


def timeline(n_items, n_trans, text_steps=None):
    """[(state, duration_ms)]: item 1 held, change to item 2 (then the last letters' light), held, ..., change back to
    item 1 (the GIF loops). The light wave moves on every frame; the text changes on `text_steps` of them (fewer =
    smaller file). The light along the letters follows the beam: it starts in the change and ends in a few frames
    of their own (the new item already in place), then the hold (HOLD_MS) as before."""
    text_steps = text_steps or n_trans
    frames = []
    step = round(TRANSITION_MS / n_trans / 10) * 10  # GIF delays are in 1/100 s
    # frame f of the change is shown at f * step ms and has t = (f + 1) / (n_trans + 1); the beam peaks at t = 0.80
    beam_ms = (0.80 * (n_trans + 1) - 1) * step
    tail = []
    ms = n_trans * step
    while any(letters_at(ms, beam_ms)):
        tail.append(letters_at(ms, beam_ms))
        ms += step
    for i in range(n_items):
        frames.append((dict(items={str(i): [1, 0]}, dash=i, wave=[0] * 5), HOLD_MS))
        nxt = (i + 1) % n_items
        if nxt == i:
            break
        for f in range(n_trans):
            t = (f + 1) / (n_trans + 1)
            tt = (f * text_steps // n_trans + 1) / (text_steps + 1)
            if tt < 0.5:  # old text fades out and moves up
                p = ease(tt / 0.5)
                st = {str(i): [round(1 - p, 3), round(-5 * p, 2)]}
            else:         # new text fades in from slightly below
                p = ease((tt - 0.5) / 0.5)
                st = {str(nxt): [round(p, 3), round(5 * (1 - p), 2)]}
            # a soft light wave over the five pieces of the mark, one after another (brightness up, then back)
            frames.append((dict(items=st, dash=i if tt < 0.5 else nxt, wave=wave_at(t),
                                letters=letters_at(f * step, beam_ms)), step))
        for lv in tail:  # the letters' light ends over the new item
            frames.append((dict(items={str(nxt): [1, 0]}, dash=nxt, wave=[0] * 5, letters=lv), step))
    return frames


class Renderer:
    """The banner page in headless Chromium; shot(state) screenshots one frame at 2x (cached)."""
    def __init__(self, html):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        try:
            self.browser = self.pw.chromium.launch()
            self.page = self.browser.new_page(viewport=dict(width=W, height=H), device_scale_factor=SCALE)
            self.page.set_content(html, wait_until='load')
            self.page.evaluate('document.fonts.ready')
            # fit the titles again now that the fonts are loaded
            self.page.evaluate("() => document.querySelectorAll('.item').forEach((el, i) => fit(el.querySelector('.title'), DATA.items[i].title))")
            self.lines = self.page.evaluate('titleLines()')
        except Exception:
            self.close()
            raise
        self.cache = {}

    def shot(self, st):
        from PIL import Image
        key = json.dumps(st, sort_keys=True)
        if key not in self.cache:
            self.page.evaluate('st => setFrame(st)', st)
            png = self.page.screenshot(clip=dict(x=0, y=0, width=W, height=H), type='png', animations='disabled')
            self.cache[key] = Image.open(io.BytesIO(png)).convert('RGB')
        return self.cache[key]

    def close(self):
        try:
            self.browser.close()
        except Exception:
            pass
        self.pw.stop()


def to_gif(images, durations, path, lossy=None):
    """One shared 256-colour palette for all frames (no dithering: crisp text); Pillow stores only the changed
    area of each frame; gifsicle -O3 (and --lossy) shrinks it further when it is installed."""
    from PIL import Image, features
    uniq = list({im.tobytes(): im for im in images}.values())
    sheet = Image.new('RGB', (W * SCALE, H * SCALE * len(uniq)))
    for k, im in enumerate(uniq):
        sheet.paste(im, (0, H * SCALE * k))
    method = Image.Quantize.LIBIMAGEQUANT if features.check_feature('libimagequant') else Image.Quantize.MEDIANCUT
    pal = sheet.quantize(256, method=method, dither=Image.Dither.NONE)
    frames = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in images]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=False, disposal=1)
    gifsicle = shutil.which('gifsicle')
    if gifsicle:
        args = [gifsicle, '-O3', '--no-comments', '--no-names', '--loopcount=forever'] + ([f'--lossy={lossy}'] if lossy else [])
        subprocess.run(args + ['-b', path], check=True, capture_output=True)
    return os.path.getsize(path)


def render_banner(L, items, out_dir):
    """Write banner-<L>.gif and banner-<L>.png. Returns a short report."""
    from PIL import Image
    gif, png = os.path.join(out_dir, f'banner-{L}.gif'), os.path.join(out_dir, f'banner-{L}.png')
    r = Renderer(banner_html(L, items))
    try:
        tried = []
        # without gifsicle (no lossy option) the same steps are tried losslessly
        ladder = LADDER if shutil.which('gifsicle') else list(dict.fromkeys((n, k, 0) for n, k, _ in LADDER))
        for n_trans, steps, lossy in ladder:
            tl = timeline(len(items), n_trans, steps)
            shots = [r.shot(s) for s, _ in tl]
            size = to_gif(shots, [d for _, d in tl], gif, lossy)
            tried.append(f'{n_trans} frames, {steps} text steps, lossy {lossy}: {size / 1024:.0f} KB')
            if size <= MAX_KB * 1024:
                break
        else:
            # still too big: a one-frame GIF (item 1), always small
            shots[0].quantize(256, dither=Image.Dither.NONE).save(gif)
            tried.append(f'static: {os.path.getsize(gif) / 1024:.0f} KB')
            print(f'WARNING: signature banner {L}: animated GIF over {MAX_KB} KB; wrote a still GIF instead')
        shots[0].save(png, optimize=True)  # frame 1 = item 1
        lines = r.lines
    finally:
        r.close()
    return f"banner-{L}.gif {os.path.getsize(gif) / 1024:.0f} KB [{'; '.join(tried)}], banner-{L}.png {os.path.getsize(png) / 1024:.0f} KB, title lines {lines}"


# ---------------------------------------------------------------- fallbacks

def keep_live(out_dir):
    """Download the banners currently published on asaegypt.com, so a failed render keeps them."""
    got = {}
    for f in FILES:
        with urllib.request.urlopen(LIVE + f, timeout=20) as r:
            data = r.read()
        if not data.startswith((b'GIF8', b'\x89PNG')):
            raise ValueError(f'{f}: not an image')
        got[f] = data
    for f, data in got.items():
        open(os.path.join(out_dir, f), 'wb').write(data)


def fill_shapes(im, shapes, colour, ss=8):
    """Paint shapes (each a list of contours in device pixels; a contour wound against the shape's largest one is a
    hole) onto im, anti-aliased: drawn ss times larger, then reduced."""
    from PIL import Image, ImageChops, ImageDraw
    pts = [p for sh in shapes for c in sh for p in c]
    x0, y0 = math.floor(min(p[0] for p in pts)) - 1, math.floor(min(p[1] for p in pts)) - 1
    x1, y1 = math.ceil(max(p[0] for p in pts)) + 1, math.ceil(max(p[1] for p in pts)) + 1
    big = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
    area = lambda c: sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(c, c[1:] + c[:1]))
    for sh in shapes:
        one = Image.new('L', big.size, 0)
        d = ImageDraw.Draw(one)
        sign = area(max(sh, key=lambda c: abs(area(c)))) > 0
        to = lambda c: [((x - x0) * ss, (y - y0) * ss) for x, y in c]
        for c in sh:
            if (area(c) > 0) == sign:
                d.polygon(to(c), fill=255)
        for c in sh:
            if (area(c) > 0) != sign:
                d.polygon(to(c), fill=0)
        big = ImageChops.lighter(big, one)
    mask = big.resize((x1 - x0, y1 - y0), Image.Resampling.BOX)
    im.paste(colour, (x0, y0, x1, y1), mask)


def static_banner(out_dir):
    """Last resort, without a browser: the logo hexagon and the site address on the dark background."""
    from PIL import Image, ImageDraw, ImageFont
    s = SCALE
    for L in ('en', 'ar'):
        im = Image.new('RGB', (W * s, H * s), '#23262B')
        dr = ImageDraw.Draw(im)
        k = 66 * s / (2 * asa_mark.H)  # the mark (66px tall) and the "ASA HEXAGON" tag under it, in the 82x86 column
        cx = (18 + 41) * s if L == 'en' else (W - 18 - 41) * s
        cy = ((H - 86) / 2 + 4 + 33) * s
        for colour, poly in pieces():
            dr.polygon([(cx + x * k, cy + y * k) for x, y in poly], fill=colour)
        try:
            big = ImageFont.truetype(os.path.join(FONTS, 'pjs-700.woff2'), 15 * s)
            small = ImageFont.truetype(os.path.join(FONTS, 'pjs-400.woff2'), 11 * s)
            tag = ImageFont.truetype(os.path.join(FONTS, 'pjs-800.woff2'), round(7.5 * s))
        except Exception:
            big = small = tag = ImageFont.load_default()
        x_col = (18 + 41) * s if L == 'en' else (W - 18 - 41) * s
        bottom = ((H - 86) / 2 + 86) * s
        lay = tag_layout() if hasattr(tag, 'getmetrics') else None
        outlines = tag_outlines() if lay else None
        if outlines:
            # the letters as outlines from the font, placed as in the animated banner (tag_layout), their ink centred
            # under the mark, then the TM after the N as in the animated banner (tm_at); anti-aliased, not snapped
            em = TAG_PX * s
            base = bottom - tag.getmetrics()[1]
            x0 = x_col - (lay['left'] + lay['right']) / 2 * em
            shapes = [[[(x0 + (xi + gx) * em, base + gy * em) for gx, gy in c] for c in outlines[ch]]
                      for ch, xi in zip(TAG.replace(' ', ''), lay['x'])]
            tx, ty, tw, th = tm_at(lay)
            bx, by, bw, bh = mark.TM_BOX
            k = th * em / bh
            shapes.append([[(x0 + tx * em + (x - bx) * k, base + ty * em + (y - by) * k) for x, y in poly]
                           for poly in tm_path_polys()])
            fill_shapes(im, shapes, '#C3D648')
        else:
            dr.text((x_col, bottom), 'ASA HEXAGON', font=tag, fill='#C3D648', anchor='md')
        anchor, x = ('la', 116 * s) if L == 'en' else ('ra', (W - 116) * s)
        dr.text((x, 38 * s), 'ASA Briefing · ASA Insights', font=big, fill='#FFFFFF', anchor=anchor)
        dr.text((x, 62 * s), 'asaegypt.com' + ('/latest' if L == 'en' else '/ar/latest'), font=small, fill='#C3D648', anchor=anchor)
        im.save(os.path.join(out_dir, f'banner-{L}.png'), optimize=True)
        im.quantize(256).save(os.path.join(out_dir, f'banner-{L}.gif'))


def build_banners(dist, B=None):
    """Write the 4 banner files into dist/. Never raises: a failure falls back and prints a warning."""
    out_dir = os.path.join(dist, OUT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    try:
        if B is None:
            import build as B
        for L in ('en', 'ar'):
            print('signature banner:', render_banner(L, latest_items(L, B), out_dir))
        return True
    except Exception as e:
        print(f'WARNING: signature banner could not be rendered ({type(e).__name__}: {str(e).strip()[:400]})')
        if 'playwright' in str(e).lower() or isinstance(e, ImportError):
            print('  It needs Playwright and Chromium: pip install -r requirements.txt && python -m playwright install chromium')
    try:
        keep_live(out_dir)
        print('WARNING: signature banner: kept the banners currently on asaegypt.com')
    except Exception as e:
        print(f'WARNING: signature banner: could not download the live banners ({e}); writing a simple static banner')
        try:
            static_banner(out_dir)
        except Exception as e2:
            print(f'WARNING: signature banner: static fallback failed too ({e2})')
    return False


if __name__ == '__main__':
    import build
    build_banners(build.DIST, build)
