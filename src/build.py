import datetime, json, os, re, sys, time, importlib
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape
sys.path.insert(0, os.path.dirname(__file__))
import mark, config, content_en, content_ar, articles_meta, news
import next as nextdata  # ASA NEXT (aliased: do not shadow the builtin next())

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
SITE = 'https://asaegypt.com'
REL = '--rel' in sys.argv  # relative links for offline preview
V = str(int(time.time()))
ICONS = json.load(open(os.path.join(ROOT, 'src/icons.json')))
# small line icons drawn for the site (not from react-icons)
_LINE = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
ICONS.update({
    'Search': _LINE + '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg>',
    'ChevPrev': _LINE + '<path d="m14.5 6-6 6 6 6"/></svg>',
    'ChevNext': _LINE + '<path d="m9.5 6 6 6-6 6"/></svg>',
})
C = {'en': content_en, 'ar': content_ar}

# route key -> path (en); ar = '/ar' + path
ROUTES = {'home': '/', 'about': '/about/', 'hexagon': '/hexagon/', 'services': '/services/', 'who': '/who-we-serve/',
          'approach': '/our-approach/', 'people': '/our-people/', 'insights': '/insights/',
          'briefing': '/briefing/', 'next': '/next/', 'contact': '/contact/', 'privacy': '/privacy/',
          'search': '/search/', 'latest': '/latest/'}
NO_SITEMAP = {'search', 'latest'}  # utility pages left out of sitemap.xml
for s in content_en.SERVICES:
    ROUTES[s['key']] = f"/services/{s['slug']}/"
for a in articles_meta.ARTICLES:
    ROUTES['art-' + a['slug']] = f"/insights/{a['slug']}/"
for n in news.NEWS:
    ROUTES['news-' + n['slug']] = f"/briefing/{n['slug']}/"
for x in nextdata.NEXT:
    ROUTES['nx-' + x['slug']] = f"/next/{x['slug']}/"

def path_for(key, L):
    p = ROUTES[key]
    return p if L == 'en' else '/ar' + p

def icon(name, cls=None):
    s = ICONS[name]
    if cls:
        s = s.replace('<svg ', f'<svg class="{cls}" ', 1)
    return Markup(s)

MARK = mark.svg('mark')
MARK_BG = mark.svg('mark-bg')
BRIEF_MARK = Markup(mark.svg('brief-mark'))

env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'src/templates')), autoescape=True)

# Arabic text with English words (Excel 2021, IFRS 9, XLOOKUP...): wrap each Latin run in <bdi class="lt">
# so it keeps its own direction and is never split across lines. English pages are returned unchanged.
LATIN_RUN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[ .:!/+\-–][A-Za-z0-9]+)*")
def bidi(s, L):
    if L != 'ar':
        return s
    out, last = [], 0
    for m in LATIN_RUN.finditer(s):
        out += [escape(s[last:m.start()]), Markup('<bdi class="lt">'), escape(m.group()), Markup('</bdi>')]
        last = m.end()
    out.append(escape(s[last:]))
    return Markup('').join(out)
env.filters['bidi'] = bidi
import guide  # reference guides: **bold**, links and Arabic bidi in the guide text
env.filters['rich'] = guide.rich
env.filters['gcell'] = guide.cell

def link(key, L, from_path):
    target = path_for(key, L)
    if not REL:
        return target
    depth = len([x for x in from_path.split('/') if x])
    return '../' * depth + target.lstrip('/') + 'index.html'

MONTHS = {'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                  'September', 'October', 'November', 'December'],
          'ar': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس',
                 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']}

def fmt_date(iso, L):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {MONTHS[L][d.month - 1]} {d.year}"

def by_date():
    # newest first; articles with the same date keep their order in articles_meta.py
    return sorted(articles_meta.ARTICLES, key=lambda a: a['date'], reverse=True)

def latest(n):
    return [a['slug'] for a in by_date()[:n]]

def featured(L, slugs, from_path='/'):
    i = 0 if L == 'en' else 1
    out = []
    for a in by_date():
        if a['slug'] in slugs:
            author, role = a['author_' + L], a['role_' + L]
            out.append(dict(slug=a['slug'], url=link('art-' + a['slug'], L, from_path),
                            cat=a['category'], tag=articles_meta.CATEGORIES[a['category']][i], title=a['title'][i],
                            card_title=a.get('short', a['title'])[i],
                            reviewed_iso=a.get('reviewed'), reviewed=a.get('reviewed') and fmt_date(a['reviewed'], L),
                            summary=a['summary'][i], author=author, role=role,
                            byline=(f"By {author}" if L == 'en' else f"بقلم {author}") + ((", " if L == 'en' else "، ") + role if role else ""),
                            date_iso=a['date'], date=fmt_date(a['date'], L), image=image_for(a, 'article', L),
                            read=read_time(guide.minutes(a['slug']) if a['slug'] in guide.GUIDES else a['minutes'], L)))
    return out

def read_time(n, L):
    """Reading time: "7 min read" / «7 دقائق قراءة». Arabic: 3–10 take «دقائق», 11 and above «دقيقة» («18 دقيقة قراءة»)."""
    if L == 'en':
        return f"{n} min read"
    return f"{n} {'دقائق' if 3 <= n <= 10 else 'دقيقة'} قراءة"

# Images (see CLAUDE.md, "Images"). Files live in public/assets/img/content/<section>/:
# photos as <slug>-lg.webp (1600px) + <slug>-card.webp (800px), ASA NEXT illustrations as <slug>.svg.
IMG_DIR = 'assets/img/content'
IMG_SECTION = {'article': 'articles', 'news': 'briefing', 'next': 'next'}

def image_for(item, kind, L):
    """An item's image for the templates (paths relative to the site root), or None when the item has no
    image or images are switched off (SHOW_IMAGES in config.py). A missing file stops the build."""
    im = item.get('image')
    if not (config.SHOW_IMAGES and im):
        return None
    base = f"{IMG_DIR}/{IMG_SECTION[kind]}/{item['slug']}"
    illustration = im.get('kind') in ('illustration', 'cover')  # drawn images: no photo credit
    if im.get('kind') == 'cover':  # reference guide cover (src/guide_cover.py): SVG band, WebP cards
        lg, card = base + '.svg', base + '-card.webp'
    else:
        lg, card = (base + '.svg', base + '.svg') if illustration else (base + '-lg.webp', base + '-card.webp')
    for f in (lg, card):
        if not os.path.exists(os.path.join(ROOT, 'public', f)):
            sys.exit(f"ERROR: {kind} '{item['slug']}' has an image but public/{f} is missing")
    # focus: the image's focal point as CSS object-position ("x% y%"), so the subject stays in view when the
    # image is cropped (image band, cards, homepage hexagon). Optional; the centre is used when it is missing.
    focus = im.get('focus', '50% 50%')
    if not re.fullmatch(r'(100|[1-9]?\d)% (100|[1-9]?\d)%', focus):
        sys.exit(f"ERROR: {kind} '{item['slug']}' has an invalid image focus {focus!r} (expected e.g. \"70% 50%\")")
    return dict(lg=lg, card=card, alt=im['alt_' + L], illustration=illustration, focus=focus,
                photographer=im.get('photographer'), site=im.get('site'), source=im.get('source'))

def news_by_date():
    # newest first; items with the same date keep their order in news.py
    return sorted(news.NEWS, key=lambda n: n['date'], reverse=True)

def news_items(L, from_path):
    i = 0 if L == 'en' else 1
    out = []
    for n in news_by_date():
        out.append(dict(slug=n['slug'], url=link('news-' + n['slug'], L, from_path),
                        cat=n['category'], cat_label=news.CATEGORIES[n['category']][i],
                        region=n['region'], region_label=news.REGIONS[n['region']][i],
                        title=n['title_' + L], short=n['short_' + L], summary=n['summary_' + L],
                        body=n['body_' + L], source_name=n['source_name'], source_url=n['source_url'],
                        note=n.get('note'), related=n.get('related'), image=image_for(n, 'news', L),
                        date_iso=n['date'], date=fmt_date(n['date'], L)))
    return out

def next_items(L, from_path):
    # newest first; items with the same date keep their order in next.py
    i = 0 if L == 'en' else 1
    out = []
    for x in sorted(nextdata.NEXT, key=lambda x: x['date'], reverse=True):
        out.append(dict(slug=x['slug'], url=link('nx-' + x['slug'], L, from_path), section=x['section'],
                        section_label=nextdata.SECTIONS[x['section']][i], title=x['title_' + L],
                        summary=x['summary_' + L], body=x['body_' + L], byline=x['byline_' + L], image=image_for(x, 'next', L),
                        date_iso=x['date'], date=fmt_date(x['date'], L)))
    return out

BRIEF_COUNT = 8  # items in the homepage hexagon

def added_key(item, kind):
    """Sort key for "newest added to asaegypt.com". `added` is required (CLAUDE.md); if it is missing the
    build warns and falls back to `date`. `added_at` (HH:MM UTC) only orders items added on the same day;
    without it an item counts as added at the end of that day."""
    if not item.get('added'):
        print(f"WARNING: {kind} '{item['slug']}' has no 'added' date; using 'date' ({item['date']}) instead")
    return (item.get('added') or item['date']) + ' ' + item.get('added_at', '24:00')

def recently_added(n=BRIEF_COUNT, kinds=('article', 'news', 'next')):
    """The n items most recently added to the site, across Insights, Briefing and ASA NEXT (or only `kinds`):
    [(kind, slug)]. Newest first; ties keep the order of the data files (newer items sit higher in each list)."""
    data = {'article': articles_meta.ARTICLES, 'news': news.NEWS, 'next': nextdata.NEXT}
    pool = [(added_key(x, kind), kind, x['slug']) for kind in ('article', 'news', 'next') if kind in kinds for x in data[kind]]
    pool.sort(key=lambda p: p[0], reverse=True)  # stable: same key keeps file order
    return [(kind, slug) for _, kind, slug in pool[:n]]

def brief_slots(L, from_path='/'):
    """The rotating items of the homepage hexagon: the BRIEF_COUNT items most recently added to the site."""
    H = C[L].HOME
    ns = {n['slug']: n for n in news_items(L, from_path)}
    xs = {x['slug']: x for x in next_items(L, from_path)}
    items = []
    for kind, slug in recently_added():
        if kind == 'news':
            n = ns[slug]
            items.append(dict(kind=kind, chip=n['cat_label'], title=n['short'], summary=n['summary'], by=n['source_name'],
                              date_iso=n['date_iso'], date=n['date'], url=n['url'], image=n['image']))
        elif kind == 'article':
            a = featured(L, [slug], from_path)[0]
            items.append(dict(kind=kind, chip=f"{H['brief_insight']} · {a['tag']}", title=a['card_title'], summary=a['summary'],
                              by=a['author'], date_iso=a['date_iso'], date=a['date'], url=a['url'], image=a['image']))
        else:
            x = xs[slug]
            items.append(dict(kind=kind, chip=f"ASA NEXT · {x['section_label']}", title=x['title'], summary=x['summary'],
                              by=x['byline'], date_iso=x['date_iso'], date=x['date'], url=x['url'], image=x['image']))
    return items

def search_cfg(L, R, from_path):
    """Settings and strings for public/assets/js/search.js (passed in the search panel's data-cfg)."""
    other = 'ar' if L == 'en' else 'en'
    S = C[L].T['search']
    nav = C[L].T['nav']
    P = lambda k: link(k, L, from_path)
    return dict(lang=L, other=other, v=V, idx=f"{R}assets/search/{L}.json", idx2=f"{R}assets/search/{other}.json",
                page=P('search'), page2=link('search', other, from_path), months=MONTHS[L], s={k: v for k, v in S.items() if k not in ('title', 'desc', 'kicker', 'h1', 'lead', 'nojs', 'notfound')},
                links=[[nav['insights'], P('insights')], [nav['briefing'], P('briefing')], [nav['contact'], P('contact')]])

def render(tpl, key, L, title, desc, section=None, solid=False, schema='', **ctx):
    mod = C[L]
    path = path_for(key, L)
    other = 'ar' if L == 'en' else 'en'
    depth = len([x for x in path.split('/') if x])
    R = ('../' * depth) if REL else '/'
    if REL and 'FEATURED' in ctx:
        pass
    html = env.get_template(tpl).render(
        L=L, SITE=SITE, V=V, T=mod.T, C=mod, SERVICES=mod.SERVICES, I=icon, P=lambda k: link(k, L, path), R=R,
        MARK=MARK, MARK_BG=MARK_BG, IMAGES=config.SHOW_IMAGES, title=title, desc=desc, path=path, SEARCH=search_cfg(L, R, path),
        alt_en=path_for(key, 'en'), alt_ar=path_for(key, 'ar'), alt_other=link(key, other, path),
        section=section, solid=solid, schema=Markup(schema), **ctx)
    out = os.path.join(DIST, path.lstrip('/'), 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    return path

ORG_SCHEMA = '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"AccountingService","name":"ASA Chartered Accountants and Consultants","alternateName":"أحمد سيد أحمد محاسبون قانونيون ومستشارون","url":"https://asaegypt.com","logo":"https://asaegypt.com/assets/img/logo_color@3x.png","telephone":"+201115652365","email":"ahmed.sayed@asaegypt.com","foundingDate":"2022","address":{"@type":"PostalAddress","streetAddress":"58A Teraat El Zomor St., Al Haram","addressLocality":"Giza","addressCountry":"EG"},"areaServed":["EG","SA"]}</script>'''

def build(pages=None):
    built = []
    for L in ('en', 'ar'):
        H = C[L].HOME
        built.append(render('home.html', 'home', L, H['title'], H['desc'], schema=ORG_SCHEMA,
                            FEATURED=featured(L, latest(3), path_for('home', L)),
                            BRIEF=brief_slots(L, path_for('home', L)), BRIEF_MARK=BRIEF_MARK))
        # further pages are registered in pages.py when available
        try:
            import pages
            importlib.reload(pages)
            built += pages.build_all(L, render, featured, path_for, C, ROUTES)
        except ImportError:
            pass
        import briefing
        importlib.reload(briefing)
        built += briefing.build(L, render, featured, news_items, path_for)
        import asanext
        importlib.reload(asanext)
        built += asanext.build(L, render, next_items, path_for, featured)
        import hexagon
        importlib.reload(hexagon)
        built += hexagon.build(L, render, path_for)
        import search
        importlib.reload(search)
        built += search.build(L, render, C)
        import signature_banner
        importlib.reload(signature_banner)
        built += signature_banner.build_page(L, render, sys.modules[__name__])
    import search
    for L, (n_pages, n_passages, size) in search.index_site(sys.modules[__name__]).items():  # after every page is written
        print(f"search index {L}: {n_pages} pages, {n_passages} passages, {size // 1024} KB")
    return built

# Retired pages: old URL (en) -> route key of the page that now covers it. Each old URL (and its /ar/ twin)
# gets a small noindex page that forwards visitors, so links already shared keep working. Not in the sitemap.
REDIRECTS = {'/services/ifrs-9-ecl/': 'svc-acc'}  # ECL is now one line under Accounting & IFRS

def build_redirects():
    for old, key in REDIRECTS.items():
        for L in ('en', 'ar'):
            to = path_for(key, L)
            html = (f'<!doctype html><html lang="{L}"><head><meta charset="utf-8"><title>ASA</title>'
                    f'<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}{to}">'
                    f'<meta http-equiv="refresh" content="0; url={to}"></head>'
                    f'<body><p><a href="{to}">{SITE}{to}</a></p></body></html>')
            out = os.path.join(DIST, (old if L == 'en' else '/ar' + old).lstrip('/'), 'index.html')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'w', encoding='utf-8').write(html)

def build_404():
    html = env.get_template('404.html').render(L='en', SITE=SITE, V=V, T=content_en.T, C=content_en, SERVICES=content_en.SERVICES, I=icon,
        P=lambda k: path_for(k, 'en'), R='/', MARK=MARK, MARK_BG=MARK_BG, title='Page not found | ASA', desc='', path='/404.html',
        SEARCH=search_cfg('en', '/', '/404.html'), S_AR=content_ar.T['search'], noindex=True,
        alt_en='/', alt_ar='/ar/', alt_other='/ar/', section=None, solid=False, schema='')
    open(os.path.join(DIST, '404.html'), 'w', encoding='utf-8').write(html)

if __name__ == '__main__':
    b = build()
    build_404()
    build_redirects()
    print(len(b), 'pages')
    import signature_banner
    signature_banner.build_banners(DIST, sys.modules[__name__])  # email signature banner; never fails the build
