"""Site search: the search pages (/search/, /ar/search/) and one passage index per language
(dist/assets/search/en.json, dist/assets/search/ar.json), built at build time from the rendered pages.

Every indexable page (all public pages; not /search/, /latest/ or any noindex page) is split into passages: each
paragraph, list item, table row, institution card, callout, quick-guide line, FAQ item, reference. Each passage gets a
stable id (its own id, or "<section id>-p<n>") that is written into the page's HTML with a data-p attribute, so a
result can take the reader to the exact place (page URL + ?hl=<query> + #<id>).

Index file: {"v", "pages": [[url, title, type, date]], "h": [breadcrumb], "p": [[page, id, text, breadcrumb, keys?]],
"al": aliases}. keys = "acronym|category|English name|Arabic name;..." of the institutions whose own card or row the
passage is (data-k, see guide.py). Aliases come from data/search_aliases.yml plus the institution registry (guide.INST).
Matching and ranking run in the browser (public/assets/js/search.js). No external service, no tracking.
"""
import html, json, os, re
from html.parser import HTMLParser
import yaml
import articles_meta, news, guide
import next as nextdata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIASES = os.path.join(ROOT, 'data', 'search_aliases.yml')
NOT_INDEXED = {'search', 'latest'}  # utility pages (both are also noindex)

# passages: these elements, any element with data-passage, and the callouts. The outermost one wins.
PASSAGE_TAGS = {'p', 'li', 'tr', 'dt', 'dd', 'blockquote', 'figcaption'}
PASSAGE_CLASSES = {'callout', 'g-note'}
# left out of the index: navigation, forms, scripts, figures drawn in SVG, cards that repeat other pages, page furniture
SKIP_TAGS = {'nav', 'form', 'script', 'style', 'svg', 'button', 'noscript', 'template', 'thead', 'select', 'label'}
SKIP_CLASSES = {'post', 'news-card', 'nx-card', 'toc', 'g-toc', 'author', 'disc', 'meta', 'kicker', 'ctas', 'sr',
                'g-anchor', 'g-note-k', 'g-find', 'g-bar', 'cta', 'img-band', 'brief', 'hxo', 'tag', 'nx-chip',
                'link-arrow', 'btn', 'cta-band', 'g-cites', 'g-back', 'nx-quiz-btn'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
CELL_END = {'td', 'th', 'dt', 'summary'}   # parts of a passage joined with " · "
INLINE = {'a', 'b', 'strong', 'em', 'i', 'bdi', 'mark', 'small', 'abbr', 'code', 'sup', 'sub', 'time', 'q', 'u', 's', 'cite'}


class Passages(HTMLParser):
    def __init__(self, src):
        super().__init__(convert_charrefs=True)
        self.src = src
        self.lines = [0]
        for m in re.finditer('\n', src):
            self.lines.append(m.end())
        self.ids = set(re.findall(r'\sid="([^"]+)"', src))
        self.stack, self.skip, self.in_main = [], 0, False
        self.root = dict(scope='top')
        self.cur = None           # passage being read
        self.head = None          # heading being read: [level, text parts]
        self.h1, self.crumb2, self.crumb3 = [], '', ''
        self.count, self.out, self.inserts = {}, [], []

    def _pos(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def scope_entry(self):
        for e in reversed(self.stack):
            if e.get('scope'):
                return e
        return self.root

    def crumbs(self):
        """Breadcrumb of the passage being opened: the h2, then the labels (data-h) of the cards and blocks
        it sits in, or the h3 that follows the h2."""
        hs = [e['h'] for e in self.stack if e.get('h')]
        return [c for c in [self.crumb2] + (hs or [self.crumb3]) if c]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.in_main = True
        if tag in VOID:
            if self.cur is not None and tag == 'br':
                self.cur['parts'].append(' ')
            return
        cls = set((a.get('class') or '').split())
        e = dict(tag=tag)
        if self.cur is not None:  # inside a passage: a collapsed answer (hidden) and its question (button) count
            skip = tag in ('svg', 'script', 'style') or 'data-noindex' in a or a.get('aria-hidden') == 'true' \
                or bool(cls & SKIP_CLASSES)
        else:
            skip = self.in_main and tag != 'main' and (tag in SKIP_TAGS or 'data-noindex' in a or 'hidden' in a
                                                       or a.get('aria-hidden') == 'true' or bool(cls & SKIP_CLASSES))
        if skip:
            e['skip'] = True
            self.skip += 1
        self.stack.append(e)
        if self.skip or not self.in_main:
            return
        if a.get('data-h'):
            e['h'] = re.sub(r'\s+', ' ', a['data-h'].replace('**', '')).strip()
        if a.get('id') and tag != 'main':
            e['scope'] = a['id']
        if self.cur is not None:
            if 'g-chip' in cls:  # a reference number inside a passage: "[21]"
                e['chip'] = True
                self.cur['parts'].append(' [')
            elif tag not in INLINE:
                self.cur['parts'].append(' ')
            return
        if tag in ('h1', 'h2', 'h3') and not any(x.get('h') for x in self.stack[:-1]):
            self.head = [tag, []]
            e['head'] = True
            if tag in ('h2', 'h3') and a.get('id'):  # a heading with an id starts a new scope for the ids that follow
                self.scope_entry_for_heading().update(scope=a['id'][:-2] if a['id'].endswith('-h') else a['id'])
            return
        if tag in PASSAGE_TAGS or 'data-passage' in a or cls & PASSAGE_CLASSES:
            own = a.get('id') or a.get('data-passage') or None
            if not own:
                se = self.scope_entry()
                base = se['scope']
                n = self.count.get(base, 0)
                while True:
                    n += 1
                    own = f'{base}-p{n}'
                    if own not in self.ids:
                        break
                self.count[base] = n
                self.ids.add(own)
                ins = f' id="{own}" data-p'
            else:
                ins = ' data-p'
            raw = self.get_starttag_text()
            off = self._pos()
            assert self.src.startswith(raw, off), (tag, off)
            self.inserts.append((off + 1 + len(tag), ins))
            self.cur = dict(id=own, parts=[], keys=a.get('data-k', ''), crumbs=self.crumbs())
            e['passage'] = True

    def scope_entry_for_heading(self):
        for e in reversed(self.stack[:-1]):
            if e.get('scope'):
                return e
        return self.root

    def handle_startendtag(self, tag, attrs):
        if self.cur is not None and tag == 'br':
            self.cur['parts'].append(' ')

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not any(e['tag'] == tag for e in self.stack):
            return
        while self.stack:
            e = self.stack.pop()
            self._end(e)
            if e['tag'] == tag:
                break
        if tag == 'main':
            self.in_main = False

    def _end(self, e):
        if e.get('skip'):
            self.skip -= 1
            return
        if e.get('head') and self.head:
            text = clean(''.join(self.head[1]))
            lvl = self.head[0]
            self.head = None
            if lvl == 'h1':
                self.h1.append(text)
            elif lvl == 'h2':
                self.crumb2, self.crumb3 = text, ''
            else:
                self.crumb3 = text
            return
        if self.cur is not None:
            if e.get('passage'):
                text = clean(''.join(self.cur['parts']))
                if len(text) > 1:
                    self.out.append(dict(id=self.cur['id'], text=text, crumb=' › '.join(self.cur['crumbs']),
                                         keys=self.cur['keys']))
                self.cur = None
            elif e.get('chip'):
                self.cur['parts'].append(']')
            elif e['tag'] in CELL_END:
                self.cur['parts'].append(' · ')
            elif e['tag'] not in INLINE:
                self.cur['parts'].append(' ')

    def handle_data(self, data):
        if self.skip or not self.in_main:
            return
        if self.head is not None:
            self.head[1].append(data)
        elif self.cur is not None:
            self.cur['parts'].append(data)

    def result(self):
        s = self.src
        for off, ins in sorted(self.inserts, reverse=True):
            s = s[:off] + ins + s[off:]
        return s


def clean(s):
    s = re.sub(r'\s+', ' ', html.unescape(s)).strip()
    s = re.sub(r'(?:\s*·\s*)+$', '', s)
    s = re.sub(r'\s*·\s*(?:·\s*)+', ' · ', s)
    return re.sub(r'\s+([.,;:،؛])', r'\1', s)


def page_meta(key, L, B, h1):
    """(title, type, date) of a page from its route key."""
    i = 0 if L == 'en' else 1
    T = B.C[L].T
    if key.startswith('art-'):
        a = next(x for x in articles_meta.ARTICLES if x['slug'] == key[4:])
        return a['title'][i], 'guide' if a['slug'] in guide.GUIDES else 'insight', a['date']
    if key.startswith('news-'):
        n = next(x for x in news.NEWS if x['slug'] == key[5:])
        return n['title_' + L], 'briefing', n['date']
    if key.startswith('nx-'):
        x = next(x for x in nextdata.NEXT if x['slug'] == key[3:])
        return x['title_' + L], 'next', x['date']
    for s in B.C[L].SERVICES:
        if s['key'] == key:
            return s['name'], 'service', ''
    if key == 'home':
        return T['home'], 'page', ''
    return T['nav'].get(key) or (h1[0] if h1 else key), 'page', ''


def aliases():
    """The aliases file plus the institution registry: every acronym with its English and Arabic names."""
    with open(ALIASES, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    des = {}
    for word, targets in (data.get('designations') or {}).items():
        out = []
        for t in targets:
            t = {'to': t} if isinstance(t, str) else t
            if t['to'] not in guide.INST:
                raise SystemExit(f"ERROR: data/search_aliases.yml: {word} -> {t['to']} is not an institution in guide.INST")
            out.append([t['to'], 1 if t.get('also') else 0, t.get('en', ''), t.get('ar', '')])
        des[str(word)] = out
    syn = [[str(x) for x in g] for g in (data.get('synonyms') or [])]
    syn += [[k] + [n for n in (e[1], e[2]) if n and n != k] for k, e in guide.INST.items() if k != 'AICPA & CIMA']
    return dict(d=des, s=syn)


def index_site(B):
    """Split every indexable page in dist/ into passages, write their ids into the HTML and the two index files.
    Returns the size of each index file."""
    al = aliases()
    sizes = {}
    for L in ('en', 'ar'):
        pages, crumbs, crumb_ix, rows = [], [], {}, []
        for key in B.ROUTES:
            if key in NOT_INDEXED:
                continue
            path = B.path_for(key, L)
            f = os.path.join(B.DIST, path.lstrip('/'), 'index.html')
            src = open(f, encoding='utf-8').read()
            if re.search(r'<meta name="robots" content="noindex', src):
                continue
            p = Passages(src)
            p.feed(src)
            p.close()
            open(f, 'w', encoding='utf-8').write(p.result())
            title, kind, date = page_meta(key, L, B, p.h1)
            pi = len(pages)
            pages.append([path, title, kind, date])
            for r in p.out:
                ci = crumb_ix.setdefault(r['crumb'], len(crumbs))
                if ci == len(crumbs):
                    crumbs.append(r['crumb'])
                rows.append([pi, r['id'], r['text'], ci] + ([r['keys']] if r['keys'] else []))
        os.makedirs(os.path.join(B.DIST, 'assets', 'search'), exist_ok=True)
        out = os.path.join(B.DIST, 'assets', 'search', f'{L}.json')
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(dict(v=2, pages=pages, h=crumbs, p=rows, al=al), fh, ensure_ascii=False, separators=(',', ':'))
        sizes[L] = (len(pages), len(rows), os.path.getsize(out))
    return sizes


def build(L, render, C):
    """The search page of one language (the indexes are written by index_site() once every page is built)."""
    S = C[L].T['search']
    return [render('search.html', 'search', L, S['title'], S['desc'], S=S, noindex=True)]
