import json, os, sys, time, importlib
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
sys.path.insert(0, os.path.dirname(__file__))
import mark, content_en, content_ar, articles_meta

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
          'contact': '/contact/', 'privacy': '/privacy/'}
for s in content_en.SERVICES:
    ROUTES[s['key']] = f"/services/{s['slug']}/"
for a in articles_meta.ARTICLES:
    ROUTES['art-' + a['slug']] = f"/insights/{a['slug']}/"

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

env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'src/templates')), autoescape=True)

def link(key, L, from_path):
    target = path_for(key, L)
    if not REL:
        return target
    depth = len([x for x in from_path.split('/') if x])
    return '../' * depth + target.lstrip('/') + 'index.html'

def featured(L, slugs, from_path='/'):
    i = 0 if L == 'en' else 1
    out = []
    for a in articles_meta.ARTICLES:
        if a['slug'] in slugs:
            out.append(dict(url=link('art-' + a['slug'], L, from_path), tag=a['tag'][i], title=a['title'][i],
                            summary=a['summary'][i],
                            read=(f"{a['minutes']} min read" if L == 'en' else f"{a['minutes']} دقائق قراءة")))
    return out

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
                            FEATURED=featured(L, ['transfer-pricing-egypt-guide', 'ecl-model-ifrs-9', 'financial-due-diligence'], path_for('home', L))))
        # further pages are registered in pages.py when available
        try:
            import pages
            importlib.reload(pages)
            built += pages.build_all(L, render, featured, path_for, C, ROUTES)
        except ImportError:
            pass
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
