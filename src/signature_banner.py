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
import base64, datetime, io, json, os, re, shutil, subprocess, sys, tempfile, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import articles_meta, news, pages_en, pages_ar, logo

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
            read = B.read_time(x['minutes'], L)
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


def stripes():
    """The 12 stripes of the logo hexagon (logo.py, traced from the original), in the order of the site intro
    (mark.py: top-left, top-right, bottom-right, bottom-left; each group from its outer stripe inwards)."""
    groups = []
    for colour, d in logo.MARK:
        groups.append([(colour, p + 'Z') for p in d.split('Z') if p])
    tl, tr, br, bl = groups
    return tl + tr[::-1] + br[::-1] + bl


def mark_svg():
    x0, y0 = -1.5, 7.5
    w, h = 238.5, 252
    paths = ''.join(f'<path fill="{c}" d="{d}"/>' for c, d in stripes())
    glow = ''.join(f'<path class="w" fill="#fff" fill-opacity="0" d="{d}"/>' for _, d in stripes())
    return (f'<svg class="mark" viewBox="{x0} {y0} {w} {h}" xmlns="http://www.w3.org/2000/svg">'
            f'{paths}{glow}</svg>')


TEMPLATE = """<!doctype html><html lang="{L}" dir="{dir}"><head><meta charset="utf-8"><style>
{fonts}{lat}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#23262B}}
body{{font-family:'Sans',sans-serif;color:#fff;-webkit-font-smoothing:antialiased;position:relative}}
.mk{{position:absolute;top:{mark_top}px;inset-inline-start:18px;width:82px;height:86px;display:flex;flex-direction:column;align-items:center;justify-content:space-between}}
.mark{{display:block;width:70px;height:74px}}
.mk .tag{{direction:ltr;font-family:'Lat',sans-serif;font-weight:800;font-size:7.5px;line-height:9px;letter-spacing:1.3px;padding-left:1.3px;color:#C3D648;white-space:nowrap}}
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
<div class="mk">{mark}<span class="tag">ASA HEXAGON</span></div>
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
const glow = [...document.querySelectorAll('.mark .w')];
// one frame: {{items: {{index: [opacity, dy]}}, dash: index, wave: [12 opacities]}}
window.setFrame = st => {{
  items.forEach((el, i) => {{
    const s = st.items[i];
    el.style.opacity = s ? s[0] : 0;
    el.style.transform = s ? 'translateY(' + s[1] + 'px)' : 'none';
  }});
  dashes.forEach((d, i) => d.classList.toggle('on', i === st.dash));
  glow.forEach((p, k) => p.setAttribute('fill-opacity', st.wave[k] || 0));
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
        W=W, H=H, mark=mark_svg(), mark_top=(H - 86) // 2,
        items=item_html, dashes='<i></i>' * len(items), data=json.dumps(data, ensure_ascii=False),
        kick_size=11 if ar else 9.5, kick_ls='0' if ar else '2px', kick_tt='' if ar else 'text-transform:uppercase',
        new_size=10 if ar else 8, new_ls='0' if ar else '1px',
        title_size=title_size, title_lh=title_lh, title_max=title_lh * 2)


# ---------------------------------------------------------------- frames and the GIF

def ease(p):
    return p * p * (3 - 2 * p)


def timeline(n_items, n_trans, text_steps=None):
    """[(state, duration_ms)]: item 1 held, change to item 2, held, ..., change back to item 1 (the GIF loops).
    The light wave moves on every frame; the text changes on `text_steps` of them (fewer = smaller file)."""
    text_steps = text_steps or n_trans
    frames = []
    step = round(TRANSITION_MS / n_trans / 10) * 10  # GIF delays are in 1/100 s
    for i in range(n_items):
        frames.append((dict(items={str(i): [1, 0]}, dash=i, wave=[0] * 12), HOLD_MS))
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
            # a soft light wave over the 12 stripes, one after another (brightness up, then back)
            wave = [round(0.5 * max(0.0, 1 - abs(t - (0.1 + k * 0.07)) / 0.16), 3) for k in range(12)]
            frames.append((dict(items=st, dash=i if tt < 0.5 else nxt, wave=wave), step))
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


def static_banner(out_dir):
    """Last resort, without a browser: the logo hexagon and the site address on the dark background."""
    from PIL import Image, ImageDraw, ImageFont
    s = SCALE
    for L in ('en', 'ar'):
        im = Image.new('RGB', (W * s, H * s), '#23262B')
        dr = ImageDraw.Draw(im)
        k = 74 * s / 252  # the mark (74px tall) and the "ASA HEXAGON" tag under it, in the 82x86 column
        x_mark = (18 + 6) * s if L == 'en' else (W - 18 - 82 + 6) * s
        for colour, d in stripes():
            pts = [tuple(map(float, q.split())) for q in re.findall(r'[ML]\s*([-\d.]+ [-\d.]+)', d)]
            dr.polygon([(x_mark + (x + 1.5) * k, (H - 86) / 2 * s + (y - 7.5) * k) for x, y in pts], fill=colour)
        try:
            big = ImageFont.truetype(os.path.join(FONTS, 'pjs-700.woff2'), 15 * s)
            small = ImageFont.truetype(os.path.join(FONTS, 'pjs-400.woff2'), 11 * s)
            tag = ImageFont.truetype(os.path.join(FONTS, 'pjs-800.woff2'), round(7.5 * s))
        except Exception:
            big = small = tag = ImageFont.load_default()
        x_col = (18 + 41) * s if L == 'en' else (W - 18 - 41) * s
        dr.text((x_col, ((H - 86) / 2 + 86) * s), 'ASA HEXAGON', font=tag, fill='#C3D648', anchor='md')
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
