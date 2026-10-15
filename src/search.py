"""Site search: the search pages (/search/, /ar/search/) and one JSON index per language
(dist/assets/search/en.json, dist/assets/search/ar.json), built from the site data at build time.

Each index entry: g (group: insights | briefing | next | services | pages), t (title), m (summary),
c (category label), d (date, YYYY-MM-DD or ""), u (URL), b (body as plain text).
Matching and ranking run in the browser: public/assets/js/search.js. No external service, no tracking.
"""
import html, json, os, re, importlib
import articles_meta, news, articles_en, articles_ar, pages_en, pages_ar
import next as nextdata

AC = {'en': articles_en, 'ar': articles_ar}
PC = {'en': pages_en, 'ar': pages_ar}
GROUPS = ('insights', 'briefing', 'next', 'services', 'pages')

TAG = re.compile(r'<[^>]+>')
BLOCK = re.compile(r'^[a-z][a-z0-9_]{0,9}$')   # body block type: ('p', ...), ('h3', ...), ('stages', ...)
SKIP_STR = re.compile(r'^(?:Fa[A-Z]\w+|https?://\S+|mailto:\S+|/\S*)$')  # icons, links
SKIP_KEYS = {'title', 'desc', 'related', 'icon', 'slug', 'key', 'url', 'type', 'source_url'}

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(TAG.sub(' ', s))).strip()

def texts(x, skip=SKIP_KEYS):
    """All human-readable strings in a data structure, in order."""
    if x is None or isinstance(x, (int, float, bool)):
        return []
    if isinstance(x, str):
        return [] if SKIP_STR.match(x.strip()) else [clean(x)]
    if isinstance(x, dict):
        return [t for k, v in x.items() if k not in skip for t in texts(v, skip)]
    items = list(x)
    if isinstance(x, tuple) and len(items) == 2 and isinstance(items[0], str) and BLOCK.match(items[0]):
        items = items[1:]  # drop the block type
    return [t for v in items for t in texts(v, skip)]

def body(x, skip=SKIP_KEYS):
    return ' '.join(t for t in texts(x, skip) if t)

def build_index(L, featured, news_items, next_items, path_for, C):
    """Entries for one language, grouped in GROUPS order (newest first inside the dated groups)."""
    importlib.reload(articles_en); importlib.reload(articles_ar); importlib.reload(pages_en); importlib.reload(pages_ar)
    i = 0 if L == 'en' else 1
    T, D, A = C[L].T, PC[L], AC[L]
    out = []
    for a in featured(L, [x['slug'] for x in articles_meta.ARTICLES], '/'):
        d = A.ART[a['slug']]
        out.append(dict(g='insights', t=a['title'], m=a['summary'], c=a['tag'], d=a['date_iso'],
                        u=path_for('art-' + a['slug'], L), b=body([d.get('key'), d['body']])))
    for n in news_items(L, '/'):
        note = n['note'] or {}
        out.append(dict(g='briefing', t=n['title'], m=n['summary'], c=n['cat_label'], d=n['date_iso'],
                        u=path_for('news-' + n['slug'], L),
                        b=body([n['body']] + [note.get(f'{k}_{L}') for k in ('who', 'accounting', 'auditor')] + [n['source_name']])))
    for x in next_items(L, '/'):
        out.append(dict(g='next', t=x['title'], m=x['summary'], c=x['section_label'], d=x['date_iso'],
                        u=path_for('nx-' + x['slug'], L), b=body(x['body'])))
    for s in C[L].SERVICES:
        out.append(dict(g='services', t=s['name'], m=s['desc'], c='', d='', u=path_for(s['key'], L),
                        b=body([s['short'], D.SVC[s['key']]])))
    nav = T['nav']
    pages = [('home', T['home'], C[L].HOME), ('about', nav['about'], D.ABOUT), ('services', nav['services'], D.SERVICES_HUB),
             ('who', nav['who'], D.WHO), ('approach', nav['approach'], D.APPROACH), ('people', nav['people'], D.PEOPLE),
             ('insights', nav['insights'], D.INSIGHTS), ('briefing', nav['briefing'], D.BRIEFING),
             ('next', nav['next'], D.NEXT_PAGE), ('contact', nav['contact'], D.CONTACT), ('privacy', nav['privacy'], D.PRIVACY)]
    for key, title, obj in pages:
        fields = {k: v for k, v in obj.items() if not k.startswith(('f_', 'thanks_', 'map_'))}  # skip form labels
        out.append(dict(g='pages', t=title, m=clean(obj['desc']), c='', d='', u=path_for(key, L), b=body(fields)))
    return out

def write_index(L, entries, dist):
    os.makedirs(os.path.join(dist, 'assets', 'search'), exist_ok=True)
    path = os.path.join(dist, 'assets', 'search', f'{L}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, separators=(',', ':'))
    return path

def build(L, render, featured, news_items, next_items, path_for, C, dist):
    write_index(L, build_index(L, featured, news_items, next_items, path_for, C), dist)
    S = C[L].T['search']
    return [render('search.html', 'search', L, S['title'], S['desc'], S=S, noindex=True)]
