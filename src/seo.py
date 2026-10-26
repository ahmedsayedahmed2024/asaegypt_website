"""Search engines, AI assistants and sharing cards. See CLAUDE.md, "SEO, AI search and sharing".

Called by build.py for every page (render() -> head()):
  - <title> and meta description of Insights, Briefing and ASA NEXT items, built from the item's own title and
    summary (item_title(), item_desc()). Fixed pages take theirs from `title` / `desc` in pages_*.py / content_*.py.
  - Open Graph / X cards: og:image is the item's own photo cropped to 1200x630 (assets/img/og/<section>/<slug>.jpg),
    else a card drawn here: dark background, faint honeycomb, the title, and the firm's name (no logo mark).
    Other pages share one default card per language (assets/img/og/site-<L>.png). All written into dist/ only.
  - JSON-LD: Organization + AccountingService and WebSite (with SearchAction) on every page, BreadcrumbList on
    inner pages, Article (Insights, guides, ASA NEXT), NewsArticle (Briefing), FAQPage only where the page already
    shows questions and answers (service pages, the reference guide's quick guides).
Called by extras.py: sitemap.xml with real lastmod dates, robots.txt, llms.txt.
Called by check_links.py: check() fails the build when a public page is missing a title, description, canonical or
hreflang, when two pages share a title, or when the sitemap and the pages disagree.
"""
import datetime, html, json, math, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import articles_meta, news, guide, config, pages_en, pages_ar
import next as nextdata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://asaegypt.com'
FIRM = {'en': 'ASA Chartered Accountants and Consultants', 'ar': 'ASA محاسبون قانونيون ومستشارون'}
LEGAL = 'أحمد سيد أحمد محاسبون قانونيون ومستشارون'  # the firm's full Arabic legal name (CLAUDE.md, rule 4)
PC = {'en': pages_en, 'ar': pages_ar}
ORG_ID = SITE + '/#organization'
SITE_ID = SITE + '/#website'
LOGO = SITE + '/assets/img/logo_color@3x.png'  # the current logo file (never a new one)
LINKEDIN = 'https://www.linkedin.com/company/asa-chartered-accountants-and-consultants/'  # footer icon + schema sameAs
SAME_AS = [LINKEDIN]  # the firm's own profiles linked from the site (add Facebook here when it is linked)
TITLE_MAX, DESC_MIN, DESC_MAX = 65, 110, 160   # check() warns outside these; it fails only on missing or duplicate
OG_W, OG_H = 1200, 630
OG_DIR = 'assets/img/og'
# each item kind (route key prefix): (list page, title suffix en, title suffix ar, card kicker en, card kicker ar)
KINDS = {
    'art': ('insights', ' | ASA Insights', ' | مقالات ASA', 'ASA INSIGHTS', 'مقالات ASA'),
    'news': ('briefing', ' | ASA Briefing', ' | إحاطة ASA', 'ASA BRIEFING', 'إحاطة ASA'),
    'nx': ('next', ' | ASA NEXT', ' | ASA NEXT', 'ASA NEXT', 'ASA NEXT'),
}


def ix(L):
    return 0 if L == 'en' else 1


def item(key):
    """(kind, data dict) of an Insights / Briefing / ASA NEXT route key, else (None, None)."""
    kind, _, slug = key.partition('-')
    data = {'art': articles_meta.ARTICLES, 'news': news.NEWS, 'nx': nextdata.NEXT}.get(kind)
    if data is None:
        return None, None
    return kind, next(x for x in data if x['slug'] == slug)


def field(x, name, L):
    """An item's text in one language: articles keep (en, ar) tuples, Briefing and ASA NEXT name_en / name_ar."""
    v = x.get(name)
    if isinstance(v, (tuple, list)):
        return v[ix(L)]
    return x.get(f'{name}_{L}')


# ---------------------------------------------------------------- titles and descriptions

def item_title(key, L):
    """<title> of an item page: its own title plus the section ("| ASA Insights"). When that is longer than
    TITLE_MAX, the shorter forms are tried in turn: the item's `short` title with the section, then the title alone,
    then `short` alone. An optional `seo_title` (articles: (en, ar); Briefing / ASA NEXT: seo_title_en / _ar)
    replaces the title in these forms."""
    kind, x = item(key)
    suffix = KINDS[kind][1 if L == 'en' else 2]
    full = field(x, 'seo_title', L) or field(x, 'title', L)
    short = field(x, 'short', L)
    tries = [full + suffix] + ([short + suffix] if short else []) + [full] + ([short] if short else [])
    return next((t for t in tries if len(t) <= TITLE_MAX), min(tries, key=len))


def clip(s, n=DESC_MAX):
    """s cut at the last word that fits in n characters, with an ellipsis."""
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) <= n:
        return s
    cut = s[:n - 1].rsplit(' ', 1)[0].rstrip(' ,;:،؛—–-')
    return cut + '…'


def item_desc(key, L, body_key=None):
    """Meta description of an item page: its summary (cut to DESC_MAX at a word). A short summary of an Insights
    article is followed by its first key takeaway, so the description says what the reader will learn."""
    kind, x = item(key)
    s = field(x, 'summary', L)
    if len(s) < 130 and body_key:
        s = s + ' ' + body_key[0]
    return clip(s)


# ---------------------------------------------------------------- structured data (JSON-LD)

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def organization(B, L):
    T = B.C[L].T
    other = 'ar' if L == 'en' else 'en'
    hours = pages_en.CONTACT['hours']  # "Sunday – Thursday, 9:00 – 17:00" (contact page)
    m = re.search(r'(\d+):(\d\d)\s*–\s*(\d+):(\d\d)', hours)
    return {
        "@type": ["AccountingService", "Organization"], "@id": ORG_ID,
        "name": FIRM[L], "alternateName": [FIRM[other], "ASA"], "legalName": LEGAL,
        "url": SITE + B.path_for('home', L), "logo": {"@type": "ImageObject", "url": LOGO}, "image": LOGO,
        "description": T['foot_about'],
        "address": {"@type": "PostalAddress", "streetAddress": "58A Teraat El Zomor St., Al Haram",
                    "addressLocality": "Giza", "addressCountry": "EG"},
        "telephone": "+201115652365", "email": "ahmed.sayed@asaegypt.com",
        "contactPoint": {"@type": "ContactPoint", "contactType": "customer service", "telephone": "+201115652365",
                         "email": "ahmed.sayed@asaegypt.com", "availableLanguage": ["Arabic", "English"],
                         "url": SITE + B.path_for('contact', L)},
        "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
                                      "dayOfWeek": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
                                      "opens": f"{int(m[1]):02d}:{m[2]}", "closes": f"{int(m[3]):02d}:{m[4]}"},
        "areaServed": [{"@type": "Country", "name": "Egypt"}, {"@type": "Country", "name": "Saudi Arabia"}],
        "knowsLanguage": ["ar", "en"], "foundingDate": "2022", "taxID": "577-152-629",
        "knowsAbout": [s['name'] for s in B.C[L].SERVICES], "sameAs": SAME_AS,
    }


def website(B, L):
    return {"@type": "WebSite", "@id": SITE_ID, "url": SITE + '/', "name": FIRM[L], "alternateName": "ASA",
            "inLanguage": ["en", "ar"], "publisher": {"@id": ORG_ID},
            "potentialAction": {"@type": "SearchAction",
                                "target": {"@type": "EntryPoint", "urlTemplate": SITE + B.path_for('search', L) + "?q={search_term_string}"},
                                "query-input": "required name=search_term_string"}}


def page_name(B, key, L):
    """The short name of a page in breadcrumbs: its menu label, service name or item title."""
    T = B.C[L].T
    kind, x = item(key)
    if x:
        return field(x, 'title', L)
    for s in B.C[L].SERVICES:
        if s['key'] == key:
            return s['name']
    if key == 'home':
        return T['home']
    return T['nav'].get(key) or {'search': T['search']['kicker'], 'latest': PC[L].LATEST['h1']}.get(key, key)


def crumbs(B, key, L):
    """[(name, url)] from Home down to the page, following the URL (/insights/<slug>/ -> Insights)."""
    by_path = {B.ROUTES[k]: k for k in B.ROUTES}
    p = B.ROUTES[key]
    keys = []
    while p != '/':
        if p in by_path:
            keys.insert(0, by_path[p])
        p = p.rstrip('/').rsplit('/', 1)[0] + '/'
    return [(B.C[L].T['home'], SITE + B.path_for('home', L))] + [(page_name(B, k, L), SITE + B.path_for(k, L)) for k in keys]


def publisher():
    return {"@type": "Organization", "@id": ORG_ID, "name": FIRM['en'], "logo": {"@type": "ImageObject", "url": LOGO}}


def article(B, key, L, x, kind, image):
    url = SITE + B.path_for(key, L)
    if kind == 'art':
        author, role = x['author_' + L], x['role_' + L]
        if role:  # signed by a person: name and job title as in the byline
            who = {"@type": "Person", "name": author, "jobTitle": role, "worksFor": {"@id": ORG_ID}}
        else:     # "ASA Insights Team": the firm's team, not a person
            who = {"@type": "Organization", "name": author, "url": SITE + B.path_for('insights', L), "parentOrganization": {"@id": ORG_ID}}
        section = articles_meta.CATEGORIES[x['category']][ix(L)]
        modified = x.get('reviewed') or x['date']
    else:
        who = {"@type": "Organization", "name": x['byline_' + L], "url": SITE + B.path_for('next', L), "parentOrganization": {"@id": ORG_ID}}
        section = nextdata.SECTIONS[x['section']][ix(L)]
        modified = x['date']
    return {"@context": "https://schema.org", "@type": "Article", "@id": url + '#article',
            "headline": field(x, 'title', L), "description": field(x, 'summary', L), "inLanguage": L,
            "url": url, "mainEntityOfPage": url, "image": image, "articleSection": section,
            "datePublished": x['date'], "dateModified": modified, "author": who, "publisher": publisher(),
            "isPartOf": {"@id": SITE_ID}}


def news_article(B, key, L, x, image):
    url = SITE + B.path_for(key, L)
    added = x.get('added') or x['date']
    return {"@context": "https://schema.org", "@type": "NewsArticle", "@id": url + '#article',
            "headline": x['title_' + L], "description": x['summary_' + L], "inLanguage": L,
            "url": url, "mainEntityOfPage": url, "image": image,
            "articleSection": news.CATEGORIES[x['category']][ix(L)],
            "datePublished": added, "dateModified": added,  # the day it went live here; the source's date is below
            "author": {"@type": "Organization", "@id": ORG_ID, "name": FIRM[L]}, "publisher": publisher(),
            "isBasedOn": {"@type": "CreativeWork", "name": x['source_name'], "url": x['source_url'], "datePublished": x['date']},
            "isPartOf": {"@id": SITE_ID}}


def faq(B, key, L, qa):
    return {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": L, "url": SITE + B.path_for(key, L),
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}


PAGE_TYPE = {'about': 'AboutPage', 'contact': 'ContactPage', 'insights': 'CollectionPage', 'briefing': 'CollectionPage',
             'next': 'CollectionPage', 'services': 'CollectionPage', 'search': 'SearchResultsPage'}


def schema(B, key, L, title, desc, image, ctx):
    """Every JSON-LD block of a page."""
    url = SITE + B.path_for(key, L)
    trail = crumbs(B, key, L)
    page = {"@type": PAGE_TYPE.get(key, 'WebPage'), "@id": url + '#webpage', "url": url, "name": title,
            "description": desc, "inLanguage": L, "isPartOf": {"@id": SITE_ID},
            "primaryImageOfPage": {"@type": "ImageObject", "url": image}}
    if key in ('home', 'about', 'contact'):
        page["about"] = {"@id": ORG_ID}
    graph = [organization(B, L), website(B, L), page]
    if len(trail) > 1:  # inner pages
        page["breadcrumb"] = {"@id": url + '#breadcrumb'}
        graph.append({"@type": "BreadcrumbList", "@id": url + '#breadcrumb', "itemListElement": [
            {"@type": "ListItem", "position": n, "name": name, "item": u} for n, (name, u) in enumerate(trail, 1)]})
    out = [{"@context": "https://schema.org", "@graph": graph}]
    kind, x = item(key)
    images = [image] + ([SITE + '/' + ctx['_photo']] if ctx.get('_photo') else [])
    if kind in ('art', 'nx'):
        out.append(article(B, key, L, x, kind, images))
        if kind == 'art' and x['slug'] in guide.GUIDES and guide.faq(x['slug'], L):  # the guide's quick guides
            out.append(faq(B, key, L, guide.faq(x['slug'], L)))
    elif kind == 'news':
        out.append(news_article(B, key, L, x, images))
    elif key.startswith('svc-') and ctx.get('D', {}).get('faq'):  # the "Frequently asked questions" of a service page
        out.append(faq(B, key, L, ctx['D']['faq']))
    return '\n'.join(ld(o) for o in out)


# ---------------------------------------------------------------- sharing cards (Open Graph / X)

FONTS = os.path.join(ROOT, 'public/assets/fonts')
BG, LIME, BLUE, INK, SOFT, LINE = (35, 38, 43), (195, 214, 72), (128, 202, 227), (255, 255, 255), (197, 201, 207), (95, 100, 108)
_done = set()
_warned = []


def _raqm():
    """True when Arabic can be drawn: Pillow with raqm (FriBiDi) and fontTools to merge the font subsets."""
    from PIL import features
    try:
        import fontTools  # noqa: F401
    except ImportError:
        return False
    return features.check('raqm')


_merged = {}


def _arabic(weight):
    """The site's Arabic font with its Latin letters, digits and punctuation: plexar-ar-<w> covers Arabic only and
    plexar-lat-<w> the rest, so the two subsets (same family and size grid) are merged once per build into a
    temporary file. Arabic titles that mention IFRS 18 or (ISSB) then render in one font, laid out by raqm."""
    if weight not in _merged:
        import tempfile
        from fontTools.ttLib import TTFont
        from fontTools.merge import Merger
        tmp = tempfile.mkdtemp(prefix='asa-og-')
        parts = []
        for sub in ('ar', 'lat'):
            t = TTFont(os.path.join(FONTS, f'plexar-{sub}-{weight}.woff2'))
            t.flavor = None
            parts.append(os.path.join(tmp, f'{sub}.ttf'))
            t.save(parts[-1])
        _merged[weight] = os.path.join(tmp, f'plexar-{weight}.ttf')
        Merger().merge(parts).save(_merged[weight])
    return _merged[weight]


def _font(name, size):
    from PIL import ImageFont
    eng = ImageFont.Layout.RAQM if _raqm() else ImageFont.Layout.BASIC
    path = _arabic(name.split('-')[-1].split('.')[0]) if name.startswith('plexar-ar') else os.path.join(FONTS, name)
    return ImageFont.truetype(path, size, layout_engine=eng)


def _hexagon(cx, cy, r):
    h = r * math.sqrt(3) / 2
    return [(cx - r / 2, cy - h), (cx + r / 2, cy - h), (cx + r, cy), (cx + r / 2, cy + h), (cx - r / 2, cy + h), (cx - r, cy)]


TIGHT = ',.:;!?%)'


def _ink(font, text):
    """(left, right) of the ink of text drawn at x = 0 (getbbox counts from the pen position, not the ink)."""
    from PIL import Image, ImageDraw
    pad = font.size
    im = Image.new('L', (int(font.getlength(text)) + 2 * pad, int(font.size * 1.6)), 0)
    ImageDraw.Draw(im).text((pad, 0), text, font=font, fill=255)
    box = im.getbbox() or (pad, 0, pad, 0)
    return box[0] - pad, box[2] - pad


def _pieces(text, font):
    """[(x, piece)] for one line of English and its width. The brand font (Plus Jakarta Sans) leaves a wide gap
    before , . : ; and the like at title sizes ("depth ."). Each such mark that touches the character before it is
    drawn on its own, a hair after the ink of that character; what follows it (if not a space) is pulled in too."""
    out, x, cur, start = [], 0.0, '', 0.0
    keep = font.size * 0.03  # the space left between the ink of the word and the mark
    for i, ch in enumerate(text):
        if ch in TIGHT and i and text[i - 1] != ' ':
            prev_right = x + _ink(font, cur)[1] if cur else x
            if cur:
                out.append((x, cur))
            l, r = _ink(font, ch)
            px = prev_right + keep - l
            out.append((px, ch))
            nxt = text[i + 1] if i + 1 < len(text) else ' '
            x = px + (font.getlength(ch) if nxt == ' ' else r + keep)
            cur = ''
        else:
            cur += ch
    if cur:
        out.append((x, cur))
        x += font.getlength(cur)
    return out, x


def _width(text, font, kw):
    return font.getlength(text, **kw) if kw else _pieces(text, font)[1]


def _wrap(text, font, width, kw):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if cur and _width(t, font, kw) > width:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def card(title, kicker, L, out):
    """A 1200x630 sharing card: dark background, faint honeycomb, kicker, title, the firm's name. No logo mark."""
    from PIL import Image, ImageDraw
    S = 2  # drawn at 2x, then reduced: smooth edges
    W, H = OG_W * S, OG_H * S
    rtl = L == 'ar'
    im = Image.new('RGB', (W, H), BG)
    # honeycomb: outlines that fade in towards the side away from the text
    comb = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(comb)
    R = 50 * S
    sx, sy = 1.5 * R, math.sqrt(3) * R
    for c in range(-1, int(W / sx) + 2):
        for r in range(-1, int(H / sy) + 2):
            x, y = c * sx, r * sy + (sy / 2 if c % 2 else 0)
            t = x / W if not rtl else 1 - x / W
            a = max(0.0, min(1.0, (t - 0.30) / 0.6)) * 0.55
            if a > 0.02:
                d.polygon(_hexagon(x, y, R * 0.9), outline=int(255 * a), width=2 * S)
    im.paste(Image.new('RGB', (W, H), LINE), (0, 0), comb)
    d = ImageDraw.Draw(im)
    M = 80 * S
    kw = dict(direction='rtl', language='ar') if rtl and _raqm() else {}
    x0 = W - M if rtl else M
    anchor = 'ra' if rtl else 'la'
    # lime bar and kicker
    d.rectangle([W - M - 56 * S, 84 * S, W - M, 90 * S] if rtl else [M, 84 * S, M + 56 * S, 90 * S], fill=LIME)
    if not kicker:
        pass
    elif rtl:
        d.text((x0, 112 * S), kicker, font=_font('plexar-ar-600.woff2', 26 * S), fill=LIME, anchor=anchor, **kw)
    else:
        f, x = _font('pjs-700.woff2', 21 * S), M
        for ch in kicker:  # letter-spaced capitals
            d.text((x, 116 * S), ch, font=f, fill=LIME, anchor='la')
            x += f.getlength(ch) + 4 * S
    # title: the largest size that fits in four lines above the foot
    width, room = (OG_W - 160) * S, 330 * S
    for size in (68, 62, 56, 50, 46, 42, 38, 34):
        f = _font('plexar-ar-700.woff2' if rtl else 'pjs-800.woff2', size * S)
        lines = _wrap(title, f, width, kw)
        lh = size * S * (1.36 if rtl else 1.18)
        if len(lines) <= 4 and len(lines) * lh <= room:
            break
    y = 160 * S
    for line in lines[:4]:
        if rtl:
            d.text((x0, y), line, font=f, fill=INK, anchor=anchor, **kw)
        else:
            for dx, piece in _pieces(line, f)[0]:
                d.text((x0 + dx, y), piece, font=f, fill=INK, anchor=anchor)
        y += lh
    # foot: the firm's name and the address of the site
    d.line([M, H - 116 * S, W - M, H - 116 * S], fill=(58, 63, 70), width=2 * S)
    fn = _font('plexar-ar-600.woff2' if rtl else 'pjs-700.woff2', 26 * S)
    d.text((x0, H - 82 * S), FIRM[L], font=fn, fill=SOFT, anchor=anchor, **kw)
    d.text((M if rtl else W - M, H - 80 * S), 'asaegypt.com', font=_font('pjs-600.woff2', 22 * S), fill=BLUE,
           anchor='la' if rtl else 'ra')
    im = im.resize((OG_W, OG_H), Image.LANCZOS)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.quantize(colors=128, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(out, 'PNG', optimize=True)


def photo(src, focus, out):
    """The item's photo cropped to 1200x630 around its focus point (the same focus as the cards)."""
    from PIL import Image
    im = Image.open(src).convert('RGB')
    w, h = im.size
    fx, fy = (int(v.rstrip('%')) / 100 for v in focus.split())
    if w / h > OG_W / OG_H:  # wider: crop the sides
        cw, ch = round(h * OG_W / OG_H), h
    else:
        cw, ch = w, round(w * OG_H / OG_W)
    left, top = round((w - cw) * fx), round((h - ch) * fy)  # CSS object-position: the same point lines up
    im = im.crop((left, top, left + cw, top + ch)).resize((OG_W, OG_H), Image.LANCZOS)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, 'JPEG', quality=82, optimize=True, progressive=True)


def og_image(B, key, L, ctx):
    """Path (from the site root) of the page's sharing image; drawn into dist/ on first use."""
    kind, x = item(key)
    if ctx.get('og_image'):
        return ctx['og_image']
    if not _raqm() and not _warned:
        _warned.append(1)
        print('WARNING: Arabic text cannot be drawn (Pillow without raqm / FriBiDi, or fontTools missing); Arabic sharing cards use the English card')
    lang = L if _raqm() else 'en'
    if kind is None:
        rel = f'{OG_DIR}/site-{lang}.png'
        if rel not in _done:
            # the home page's headline; no kicker (the firm's name is already in the foot)
            card(re.sub(r'<[^>]+>', '', B.C[lang].HOME['h1']), '', lang, os.path.join(B.DIST, rel))
            _done.add(rel)
        return '/' + rel
    sec = KINDS[kind][0]
    im = x.get('image') if config.SHOW_IMAGES else None
    if kind == 'art' and im and im.get('kind') == 'cover':  # a reference guide's own share image (guide_cover.py)
        return f"/assets/img/content/articles/{x['slug']}-og.png"
    if im and im.get('kind') not in ('illustration', 'cover'):
        rel = f"{OG_DIR}/{sec}/{x['slug']}.jpg"
        if rel not in _done:
            photo(os.path.join(B.DIST, B.image_for(x, {'art': 'article', 'news': 'news', 'nx': 'next'}[kind], L)['lg']), im.get('focus', '50% 50%'),
                  os.path.join(B.DIST, rel))
            _done.add(rel)
        return '/' + rel
    rel = f"{OG_DIR}/{sec}/{x['slug']}-{L}.png"
    if rel not in _done:
        card(field(x, 'title', lang), KINDS[kind][3 if lang == 'en' else 4], lang, os.path.join(B.DIST, rel))
        _done.add(rel)
    return '/' + rel


def head(B, key, L, title, desc, ctx):
    """Everything base.html needs in <head> for search engines and sharing cards."""
    kind, x = item(key)
    image = SITE + og_image(B, key, L, ctx)
    if x and x.get('image') and config.SHOW_IMAGES and x['image'].get('kind') not in ('illustration', 'cover'):
        ctx['_photo'] = B.image_for(x, {'art': 'article', 'news': 'news', 'nx': 'next'}[kind], L)['lg']
    og_title = field(x, 'title', L) if x else title
    h = dict(og_title=og_title, og_image=image, og_alt=og_title, og_type='article' if x else 'website',
             og_image_type='image/jpeg' if image.endswith('.jpg') else 'image/png',
             locale='ar_EG' if L == 'ar' else 'en_US', locale_alt='en_US' if L == 'ar' else 'ar_EG', site_name=FIRM[L])
    if x:
        h['published'] = x.get('added') if kind == 'news' else x['date']
        h['modified'] = x.get('reviewed') or h['published']
        h['section'] = (articles_meta.CATEGORIES[x['category']] if kind == 'art' else
                        news.CATEGORIES[x['category']] if kind == 'news' else nextdata.SECTIONS[x['section']])[ix(L)]
    h['ld'] = schema(B, key, L, title, desc, image, ctx) + (('\n' + ctx['schema']) if ctx.get('schema') else '')
    return h


# ---------------------------------------------------------------- sitemap, robots.txt, llms.txt

def git_date(*paths):
    """The day the last commit touched any of these files (YYYY-MM-DD), or None outside a git checkout."""
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--'] + list(paths), cwd=ROOT,
                             capture_output=True, text=True, timeout=20).stdout.strip()
        return out or None
    except Exception:
        return None


def _item_day(x):
    return max(d for d in (x.get('date'), x.get('added'), x.get('reviewed')) if d)


# the source files of each fixed page (besides base.html and the shared header / footer text)
PAGE_FILES = {'home': ['src/content_en.py', 'src/content_ar.py', 'src/templates/home.html'],
              'services': ['src/pages_en.py', 'src/pages_ar.py', 'src/content_en.py', 'src/content_ar.py', 'src/templates/services.html']}


def lastmod(B, key):
    """When a page's content last changed: an item's latest date (published, added, reviewed); a list page's
    newest item; a fixed page's last commit to its text or template."""
    kind, x = item(key)
    if x:
        return _item_day(x)
    files = PAGE_FILES.get(key)
    if files is None:
        tpl = {'who': 'who', 'approach': 'approach', 'people': 'people', 'contact': 'contact', 'privacy': 'privacy',
               'about': 'about', 'insights': 'insights', 'briefing': 'briefing', 'next': 'next'}.get(key, 'service')
        files = ['src/pages_en.py', 'src/pages_ar.py', f'src/templates/{tpl}.html']
    days = [git_date(*files)]
    if key in ('home', 'insights'):
        days += [_item_day(a) for a in articles_meta.ARTICLES]
    if key in ('home', 'briefing'):
        days += [_item_day(n) for n in news.NEWS]
    if key in ('home', 'next'):
        days += [_item_day(n) for n in nextdata.NEXT]
    days = [d for d in days if d]
    return max(days) if days else datetime.date.today().isoformat()


def is_noindex(B, path):
    f = os.path.join(B.DIST, path.lstrip('/'), 'index.html')
    return not os.path.exists(f) or re.search(r'<meta name="robots" content="[^"]*noindex', open(f, encoding='utf-8').read()) is not None


def sitemap(B):
    """Every public page in both languages, with its real lastmod and its language alternates. Left out: noindex
    pages (search, latest), forwarding pages of retired URLs (REDIRECTS, including the hidden ASA Hexagon page)."""
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    n = 0
    for key in B.ROUTES:
        if key in B.NO_SITEMAP:
            continue
        en, ar = B.path_for(key, 'en'), B.path_for(key, 'ar')
        if is_noindex(B, en) or is_noindex(B, ar):
            continue
        day = lastmod(B, key)
        alts = (f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}{en}"/>'
                f'<xhtml:link rel="alternate" hreflang="ar" href="{SITE}{ar}"/>'
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{en}"/>')
        for p in (en, ar):
            sm.append(f'<url><loc>{SITE}{p}</loc><lastmod>{day}</lastmod>{alts}</url>')
            n += 1
    sm.append('</urlset>')
    return '\n'.join(sm) + '\n', n


AI_BOTS = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-User', 'Claude-SearchBot', 'PerplexityBot',
           'Perplexity-User', 'Google-Extended', 'Applebot-Extended', 'Bingbot']


def robots():
    out = ['# asaegypt.com: every page is open to search engines and AI assistants.', 'User-agent: *', 'Allow: /', '']
    out += ['# AI assistants and search crawlers, named explicitly'] + [f'User-agent: {b}' for b in AI_BOTS] + ['Allow: /', '']
    return '\n'.join(out) + f'\nSitemap: {SITE}/sitemap.xml\n'


def llms(B):
    """/llms.txt: a plain-language map of the site for AI assistants (llmstxt.org), from the site data."""
    en = B.C['en']
    P = pages_en
    u = lambda k: SITE + B.path_for(k, 'en')
    lines = [f"# {FIRM['en']}", '',
             f"> {en.T['foot_about']} Founded in 2022. Arabic name: {FIRM['ar']} ({LEGAL}).", '',
             f"- Office: {en.T['address']}",
             '- Clients: Egypt, Saudi Arabia and international',
             f"- Languages: English and Arabic. The website is in both: English at {SITE}/ and Arabic at {SITE}/ar/",
             f"- Contact: {u('contact')} · +20 111 565 2365 · ahmed.sayed@asaegypt.com · {P.CONTACT['hours']}",
             f"- Memberships: {'; '.join(t for _, t in en.HOME['trust'])}",
             f"- LinkedIn: {LINKEDIN}",
             '', '## Services', '']
    lines += [f"- [{s['name']}]({u(s['key'])}): {s['desc']}" for s in en.SERVICES] + [f"- {en.T['more'].lstrip('… ').capitalize()}"]
    lines += ['', '## Main pages', '']
    for k in ('home', 'about', 'services', 'who', 'approach', 'people', 'insights', 'briefing', 'next', 'contact'):
        D = {'home': en.HOME, 'services': P.SERVICES_HUB, 'who': P.WHO, 'approach': P.APPROACH, 'people': P.PEOPLE,
             'insights': P.INSIGHTS, 'briefing': P.BRIEFING, 'next': P.NEXT_PAGE, 'contact': P.CONTACT, 'about': P.ABOUT}[k]
        lines.append(f"- [{page_name(B, k, 'en') if k != 'home' else 'Home'}]({u(k)}): {D['desc']}")
    arts = sorted(articles_meta.ARTICLES, key=lambda a: B.added_key(a, 'article'), reverse=True)
    guides = [a for a in arts if a['slug'] in guide.GUIDES]
    if guides:
        lines += ['', '## Reference guides', '']
        lines += [f"- [{a['title'][0]}]({u('art-' + a['slug'])}): {a['summary'][0]}" for a in guides]
    lines += ['', '## Latest Insights', '']
    lines += [f"- [{a['title'][0]}]({u('art-' + a['slug'])}) ({a['date']}): {a['summary'][0]}" for a in arts if a not in guides][:10]
    items = sorted(news.NEWS, key=lambda n: B.added_key(n, 'news'), reverse=True)[:10]
    lines += ['', '## Latest Briefing (professional updates, each linked to its official source)', '']
    lines += [f"- [{n['title_en']}]({u('news-' + n['slug'])}) ({n['date']}, source: {n['source_name']})" for n in items]
    lines += ['', '## ASA NEXT (for juniors in their first five years in audit, tax and advisory)', '']
    lines += [f"- [{x['title_en']}]({u('nx-' + x['slug'])}): {x['summary_en']}" for x in nextdata.NEXT]
    lines += ['', '## Optional', '',
              f"- [Arabic site]({SITE}/ar/): the same pages in Arabic",
              f"- [Sitemap]({SITE}/sitemap.xml): every public page in both languages",
              f"- [Privacy policy]({u('privacy')})"]
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------- build check

def check(dist):
    """Errors for the public pages in dist/ (every page without noindex): a missing <title>, description,
    canonical or hreflang (en, ar, x-default), invalid JSON-LD, two pages with the same title, a sitemap URL that is
    not a public page, or a public page missing from the sitemap. Warnings for lengths outside the targets."""
    errors, warnings, titles = [], [], {}
    public = set()
    for root, _, files in os.walk(dist):
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            rel = '/' + os.path.relpath(p, dist).replace(os.sep, '/')
            src = open(p, encoding='utf-8').read()
            head_ = src.split('</head>', 1)[0]
            if '<head' not in head_ or re.search(r'<meta name="robots" content="[^"]*noindex', head_):
                continue  # noindex pages, forwarding pages, the Search Console verification file
            url = rel[:-len('index.html')] if rel.endswith('/index.html') else rel
            public.add(url)
            t = re.search(r'<title>([^<]*)</title>', head_)
            d = re.search(r'<meta name="description" content="([^"]*)"', head_)
            t = html.unescape(t.group(1)).strip() if t else ''
            d = html.unescape(d.group(1)).strip() if d else ''
            if not t:
                errors.append(f'{url}: no <title>')
            if not d:
                errors.append(f'{url}: no meta description')
            c = re.search(r'<link rel="canonical" href="([^"]+)"', head_)
            if not c:
                errors.append(f'{url}: no canonical link')
            elif c.group(1) != SITE + url:
                errors.append(f'{url}: canonical points to {c.group(1)}')
            for lang in ('en', 'ar', 'x-default'):
                if not re.search(rf'<link rel="alternate" hreflang="{lang}" href="{re.escape(SITE)}/[^"]*"', head_):
                    errors.append(f'{url}: no hreflang="{lang}" link')
            for prop in ('og:title', 'og:description', 'og:url', 'og:image', 'og:type', 'og:locale'):
                if f'property="{prop}"' not in head_:
                    errors.append(f'{url}: no {prop}')
            m = re.search(r'<meta property="og:image" content="' + re.escape(SITE) + r'(/[^"]+)"', head_)
            if m and not os.path.exists(os.path.join(dist, m.group(1).lstrip('/'))):
                errors.append(f'{url}: og:image {m.group(1)} is missing')
            for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', head_, re.S):
                try:
                    json.loads(block)
                except ValueError as e:
                    errors.append(f'{url}: invalid JSON-LD ({e})')
            if t:
                titles.setdefault(t, []).append(url)
                if len(t) > TITLE_MAX:
                    warnings.append(f'{url}: title is {len(t)} characters (target {TITLE_MAX} or fewer)')
            if d and not DESC_MIN <= len(d) <= DESC_MAX:
                warnings.append(f'{url}: description is {len(d)} characters (target {DESC_MIN}–{DESC_MAX})')
    for t, urls in titles.items():
        if len(urls) > 1:
            errors.append(f'same <title> on {len(urls)} pages ({", ".join(sorted(urls))}): {t}')
    sm = os.path.join(dist, 'sitemap.xml')
    if os.path.exists(sm):
        listed = {u[len(SITE):] for u in re.findall(r'<loc>([^<]+)</loc>', open(sm, encoding='utf-8').read())}
        for u in sorted(listed - public):
            errors.append(f'sitemap.xml lists {u}, which is not a public page')
        for u in sorted(public - listed - {'/404.html'}):
            errors.append(f'{u} is a public page but not in sitemap.xml')
    else:
        errors.append('dist/sitemap.xml is missing')
    return errors, warnings, len(public)
