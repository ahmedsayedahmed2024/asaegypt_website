import datetime, json, os, sys, time, importlib
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
sys.path.insert(0, os.path.dirname(__file__))
import mark, content_en, content_ar, articles_meta, news
import next as nextdata  # ASA NEXT (aliased: do not shadow the builtin next())

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
SITE = 'https://asaegypt.com'
REL = '--rel' in sys.argv  # relative links for offline preview
V = str(int(time.time()))
ICONS = json.load(open(os.path.join(ROOT, 'src/icons.json')))
C = {'en': content_en, 'ar': content_ar}

# route key -> path (en); ar = '/ar' + path
ROUTES = {'home': '/', 'about': '/about/', 'services': '/services/', 'who': '/who-we-serve/',
          'approach': '/our-approach/', 'people': '/our-people/', 'insights': '/insights/',
          'briefing': '/briefing/', 'next': '/next/', 'contact': '/contact/', 'privacy': '/privacy/'}
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
            out.append(dict(url=link('art-' + a['slug'], L, from_path), tag=a['tag'][i], title=a['title'][i],
                            summary=a['summary'][i], author=author, role=role,
                            byline=(f"By {author}, {role}" if L == 'en' else f"بقلم {author}، {role}"),
                            date_iso=a['date'], date=fmt_date(a['date'], L),
                            read=(f"{a['minutes']} min read" if L == 'en' else f"{a['minutes']} دقائق قراءة")))
    return out

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
                        note=n.get('note'), related=n.get('related'),
                        date_iso=n['date'], date=fmt_date(n['date'], L)))
    return out

def next_items(L, from_path):
    # newest first; items with the same date keep their order in next.py
    i = 0 if L == 'en' else 1
    out = []
    for x in sorted(nextdata.NEXT, key=lambda x: x['date'], reverse=True):
        out.append(dict(slug=x['slug'], url=link('nx-' + x['slug'], L, from_path), section=x['section'],
                        section_label=nextdata.SECTIONS[x['section']][i], title=x['title_' + L],
                        summary=x['summary_' + L], body=x['body_' + L], byline=x['byline_' + L],
                        date_iso=x['date'], date=fmt_date(x['date'], L)))
    return out

def brief_slots(L, from_path='/'):
    """The five rotating items of the homepage banner: 2 newest news, 2 newest articles, the ECL service.
    If fewer than 2 news items exist, the gap is filled with the next newest articles."""
    H = C[L].HOME
    ns = news_items(L, from_path)[:2]
    arts = featured(L, latest(4 - len(ns)), from_path)
    items = [dict(kind='news', chip=n['cat_label'], title=n['short'], summary=n['summary'], by=n['source_name'],
                  date_iso=n['date_iso'], date=n['date'], url=n['url']) for n in ns]
    items += [dict(kind='article', chip=H['brief_new'], title=a['title'], summary=a['summary'], by=a['author'],
                   date_iso=a['date_iso'], date=a['date'], url=a['url']) for a in arts]
    items.sort(key=lambda x: (x['date_iso'], x['kind'] == 'news'), reverse=True)
    s = next(x for x in C[L].SERVICES if x['key'] == 'svc-ecl')
    items.append(dict(kind='service', chip=H['brief_service'], title=s['name'], summary=s['desc'], by=H['brief_from'],
                      date_iso=None, date=None, url=link('svc-ecl', L, from_path)))
    return items

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
        MARK=MARK, MARK_BG=MARK_BG, title=title, desc=desc, path=path,
        alt_en=path_for(key, 'en'), alt_ar=path_for(key, 'ar'), alt_other=link(key, other, path),
        section=section, solid=solid, schema=Markup(schema), **ctx)
    out = os.path.join(DIST, path.lstrip('/'), 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(html)
    return path

ORG_SCHEMA = '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"AccountingService","name":"ASA Chartered Accountants and Consultants","alternateName":"أحمد سيد أحمد محاسبون قانونيون ومستشارون","url":"https://asaegypt.com","logo":"https://asaegypt.com/assets/img/logo_color.png","telephone":"+201115652365","email":"ahmed.sayed@asaegypt.com","foundingDate":"2022","address":{"@type":"PostalAddress","streetAddress":"58A Teraat El Zomor St., Al Haram","addressLocality":"Giza","addressCountry":"EG"},"areaServed":["EG","SA"]}</script>'''

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
        built += asanext.build(L, render, next_items, path_for)
    return built

def build_404():
    html = env.get_template('404.html').render(L='en', SITE=SITE, V=V, T=content_en.T, C=content_en, SERVICES=content_en.SERVICES, I=icon,
        P=lambda k: path_for(k, 'en'), R='/', MARK=MARK, MARK_BG=MARK_BG, title='Page not found | ASA', desc='', path='/404.html',
        alt_en='/', alt_ar='/ar/', alt_other='/ar/', section=None, solid=False, schema='')
    open(os.path.join(DIST, '404.html'), 'w', encoding='utf-8').write(html)

if __name__ == '__main__':
    b = build()
    build_404()
    print(len(b), 'pages')
