"""Photos for Insights articles and Briefing items (CLAUDE.md, "Images"): the private backup library and the registry
of every photo ever used on the site. Rule above all: no photo is ever used twice.

  photo_library/index.yml      the backup library: one entry per photo (files photo_library/<id>-lg.webp, -card.webp)
  photo_library/registry.yml   every photo used on the site (library and live photos), by source URL and image hash

The library is never published: the build copies into dist/ only the photos that an item uses
(image=dict(library=<id>, ...), see build.image_for). Live photos are stored in public/assets/img/content/ as before.

  python src/photos.py check                 registry vs. site data, licences, library photos left per category
  python src/photos.py sync                  add every photo used on the site to the registry (hashes from the files)
  python src/photos.py add FILE --category C --source URL --photographer NAME --site SITE --licence L
                           --alt-en TEXT --alt-ar TEXT [--focus "x% y%"]
                                             add a downloaded photo to the library (WebP 1600px + 800px)
  python src/photos.py live FILE --section briefing|articles --slug SLUG --source URL --photographer NAME --site SITE
                           --licence L --alt-en TEXT --alt-ar TEXT [--focus "x% y%"]
                                             a photo found on a live source, for one item: writes its two WebP files
                                             into public/, registers it and prints the item's image=dict(...)
  python src/photos.py pick CATEGORY         unused library photos of a category
  python src/photos.py use ID --section briefing|articles --slug SLUG
                                             take a library photo for an item: marks it used, registers it and prints
                                             the item's image=dict(...)

Every command refuses a photo already in the registry or the library (same source URL, or an image hash within
HASH_NEAR bits: the same photo resized or re-encoded).
"""
import argparse, hashlib, io, os, re, sys
from urllib.parse import urlsplit
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'photo_library')
INDEX = os.path.join(LIB, 'index.yml')
REGISTRY = os.path.join(LIB, 'registry.yml')
CONTENT = os.path.join(ROOT, 'public', 'assets', 'img', 'content')

# library categories (folders of photo_library/)
CATEGORIES = {
    'reporting': "Financial reporting & standards",
    'tax': "Tax (Egypt)",
    'economy': "Economy & region",
    'tech': "Technology & AI",
    'audit': "Audit & assurance",
    'careers': "Careers / ASA NEXT",
    'guides': "Guides",
}
LOW = 20  # report a category with fewer unused photos than this

# sources, in the order the daily routine tries them, with the only licence accepted from each
# (free for commercial use, no payment, no attribution condition that the site cannot meet)
SOURCES = {
    'Unsplash': "Unsplash License",            # never Unsplash+
    'Pexels': "Pexels License",
    'Pixabay': "Pixabay Content License",
    'StockSnap': "CC0",
    'Burst': "Burst License",                  # Burst by Shopify
    'Kaboompics': "Kaboompics License",
    'Wikimedia Commons': ("CC0", "Public Domain"),  # never CC BY / CC BY-SA
}
SIZES = {'lg': (1600, 180), 'card': (800, 70)}  # width (px), target size (KB): the sizes the site already uses
LIB_MAX_KB = 150                                # library target for each file
HASH_NEAR = 6                                   # image hashes this close (bits of 64) are the same photo


# ---------------------------------------------------------------- data files

INDEX_HEAD = """# ASA photo library (private): backup photos for Insights articles and Briefing items, used when no live source
# works (CLAUDE.md, "Images"). Never published as a page or folder: the build copies into dist/ only the photos an
# item uses. Files: photo_library/<id>-lg.webp (1600px) and <id>-card.webp (800px), id = <category>/<name>.
# Add photos with `python src/photos.py add ...`; take one with `python src/photos.py use ...` (fills used_by).
# Fields: id, category, file, alt_en, alt_ar, photographer, site, source, licence, focus, dhash, used_by.
"""
REGISTRY_HEAD = """# Every photo used on asaegypt.com, from the library or from a live source (CLAUDE.md, "Images").
# A photo is never used twice: before using one, `python src/photos.py` checks its source URL and its image hash
# (dhash) against this list. Written by `python src/photos.py live|use|sync`; do not remove entries.
# Fields: used_by (kind:slug), site, source, photographer, licence, library (id, when from the library), dhash, sha256.
"""


def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return (yaml.safe_load(f) or {}).get('photos') or []


def _save(path, head, photos):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = yaml.safe_dump({'photos': photos}, allow_unicode=True, sort_keys=False, width=1000) if photos else 'photos: []\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(head + body)


def library():
    return _load(INDEX)


def registry():
    return _load(REGISTRY)


def library_files(pid):
    """(lg, card) files of a library photo."""
    return tuple(os.path.join(LIB, f'{pid}-{s}.webp') for s in ('lg', 'card'))


# ---------------------------------------------------------------- images

def norm_url(u):
    """Source URL without query, fragment, trailing slash, "www." or letter case: the photo page's identity."""
    p = urlsplit((u or '').strip())
    host = p.netloc.lower()
    host = host[4:] if host.startswith('www.') else host
    return (host + p.path.rstrip('/')).lower()


def dhash(path_or_img):
    """64-bit difference hash: the same for a photo resized or re-encoded."""
    from PIL import Image
    im = path_or_img if hasattr(path_or_img, 'convert') else Image.open(path_or_img)
    g = im.convert('L').resize((9, 8), Image.LANCZOS)
    px = g.tobytes()  # one byte per pixel (mode L)
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = bits << 1 | (px[y * 9 + x] > px[y * 9 + x + 1])
    return f'{bits:016x}'


def near(a, b):
    return bool(a and b) and bin(int(a, 16) ^ int(b, 16)).count('1') <= HASH_NEAR


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def write_webp(im, out, width, max_kb):
    """Resize to `width` (never up) and save as WebP, lowering the quality until the file is under max_kb."""
    from PIL import Image
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    for q in range(82, 45, -4):
        buf = io.BytesIO()
        im.save(buf, 'WEBP', quality=q, method=6)
        if buf.tell() <= max_kb * 1024:
            break
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(buf.getvalue())
    return buf.tell() // 1024


def open_photo(path):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    if im.width <= im.height:
        sys.exit(f'ERROR: {path} is not landscape ({im.width}x{im.height})')
    if im.width < SIZES['lg'][0]:
        print(f'WARNING: {path} is only {im.width}px wide (the image band uses 1600px)')
    return im


# ---------------------------------------------------------------- checks

def licence_ok(site, licence):
    ok = SOURCES.get(site)
    return ok is not None and licence in (ok if isinstance(ok, tuple) else (ok,))


def seen(url, h, skip_item=None, skip_lib=None):
    """Where a photo (source URL, dhash) is already used or stored, or None."""
    nu = norm_url(url)
    for r in registry():
        if r.get('used_by') == skip_item:
            continue
        if (nu and norm_url(r.get('source')) == nu) or near(h, r.get('dhash')):
            return f"registry ({r.get('used_by')}: {r.get('source')})"
    for p in library():
        if p['id'] == skip_lib:
            continue
        if (nu and norm_url(p.get('source')) == nu) or near(h, p.get('dhash')):
            return f"library ({p['id']}: {p.get('source')})"
    return None


def site_photos():
    """Every photo used by an item on the site: [(kind:slug, image dict, card file)]. Drawn images are left out."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import articles_meta, news
    out = []
    for kind, section, data in (('article', 'articles', articles_meta.ARTICLES), ('news', 'briefing', news.NEWS)):
        for x in data:
            im = x.get('image')
            if not im or im.get('kind') in ('illustration', 'cover'):
                continue
            card = library_files(im['library'])[1] if im.get('library') else os.path.join(CONTENT, section, f"{x['slug']}-card.webp")
            out.append((f"{kind}:{x['slug']}", im, card))
    return out


def verify(quiet=False):
    """Errors (a photo used twice, a licence that is not allowed) and warnings (a photo missing from the registry,
    a library photo used but not marked). Used by check_links.py; returns the list of errors."""
    errors, warns = [], []
    items = []
    for who, im, card in site_photos():
        if not licence_ok(im.get('site'), im.get('licence')):
            errors.append(f"{who}: photo from {im.get('site')!r} with licence {im.get('licence')!r} is not allowed (see SOURCES in src/photos.py)")
        h = dhash(card) if os.path.exists(card) else None
        items.append((who, im, h))
    for i, (a, ima, ha) in enumerate(items):
        for b, imb, hb in items[i + 1:]:
            if norm_url(ima.get('source')) == norm_url(imb.get('source')) or near(ha, hb):
                errors.append(f"the same photo is used twice: {a} and {b} ({ima.get('source')})")
    reg = registry()
    by_url = {norm_url(r.get('source')): r for r in reg}
    lib = {p['id']: p for p in library()}
    for who, im, h in items:
        r = by_url.get(norm_url(im.get('source')))
        if not r:
            warns.append(f"{who}: photo not in photo_library/registry.yml (run: python src/photos.py sync)")
        elif r.get('used_by') != who:
            errors.append(f"{who}: its photo is registered as used by {r.get('used_by')}")
        if im.get('library'):
            p = lib.get(im['library'])
            if not p:
                errors.append(f"{who}: library photo {im['library']!r} is not in photo_library/index.yml")
            elif p.get('used_by') != who:
                errors.append(f"{who}: library photo {im['library']!r} is marked used_by {p.get('used_by')!r}")
    if not quiet:
        for w in warns:
            print('WARNING: ' + w)
    return errors


def unused_by_category():
    n = {c: 0 for c in CATEGORIES}
    for p in library():
        if not p.get('used_by'):
            n[p['category']] = n.get(p['category'], 0) + 1
    return n


# ---------------------------------------------------------------- commands

def image_dict(src):
    keys = ('library', 'focus', 'source', 'photographer', 'site', 'licence', 'alt_en', 'alt_ar')
    return 'image=dict(' + ', '.join(f'{k}={src[k]!r}' for k in keys if src.get(k)) + ')'


def check_meta(a):
    if not licence_ok(a.site, a.licence):
        sys.exit(f'ERROR: {a.site!r} / {a.licence!r} is not an allowed source and licence: {SOURCES}')
    if not re.fullmatch(r'(100|[1-9]?\d)% (100|[1-9]?\d)%', a.focus):
        sys.exit(f'ERROR: invalid focus {a.focus!r} (expected e.g. "70% 50%")')


def register(who, meta, files, library_id=None):
    reg = registry()
    reg.append(dict(used_by=who, site=meta['site'], source=meta['source'], photographer=meta['photographer'],
                    licence=meta['licence'], **({'library': library_id} if library_id else {}),
                    dhash=dhash(files[1]), sha256=sha256(files[0])))
    _save(REGISTRY, REGISTRY_HEAD, reg)


def cmd_add(a):
    check_meta(a)
    if a.category not in CATEGORIES:
        sys.exit(f'ERROR: category must be one of {", ".join(CATEGORIES)}')
    im = open_photo(a.file)
    h = dhash(im)
    dup = seen(a.source, h)
    if dup:
        sys.exit(f'ERROR: this photo is already in the {dup}')
    lib = library()
    name = a.name or re.sub(r'[^a-z0-9]+', '-', norm_url(a.source).rsplit('/', 1)[-1])[:60].strip('-') or 'photo'
    pid = f'{a.category}/{name}'
    if any(p['id'] == pid for p in lib):
        sys.exit(f'ERROR: {pid} already exists')
    lg, card = library_files(pid)
    kb = [write_webp(im, lg, SIZES['lg'][0], LIB_MAX_KB), write_webp(im, card, SIZES['card'][0], SIZES['card'][1])]
    lib.append(dict(id=pid, category=a.category, file=os.path.relpath(lg, ROOT), alt_en=a.alt_en, alt_ar=a.alt_ar,
                    photographer=a.photographer, site=a.site, source=a.source, licence=a.licence, focus=a.focus,
                    dhash=h, used_by=''))
    _save(INDEX, INDEX_HEAD, lib)
    print(f'added {pid} ({kb[0]} KB + {kb[1]} KB)')


def cmd_live(a):
    check_meta(a)
    who = f"{'article' if a.section == 'articles' else 'news'}:{a.slug}"
    im = open_photo(a.file)
    dup = seen(a.source, dhash(im))
    if dup:
        sys.exit(f'ERROR: this photo is already used: {dup}. Pick another one.')
    files = [os.path.join(CONTENT, a.section, f'{a.slug}-{s}.webp') for s in ('lg', 'card')]
    kb = [write_webp(im, f, *SIZES[s]) for f, s in zip(files, ('lg', 'card'))]
    meta = dict(focus=a.focus, source=a.source, photographer=a.photographer, site=a.site, licence=a.licence,
                alt_en=a.alt_en, alt_ar=a.alt_ar)
    register(who, meta, files)
    print(f'wrote {os.path.relpath(files[0], ROOT)} ({kb[0]} KB) and -card ({kb[1]} KB); registered as {who}')
    print(image_dict(meta))


def cmd_use(a):
    who = f"{'article' if a.section == 'articles' else 'news'}:{a.slug}"
    lib = library()
    p = next((x for x in lib if x['id'] == a.id), None)
    if not p:
        sys.exit(f'ERROR: no library photo {a.id!r}')
    if p.get('used_by'):
        sys.exit(f"ERROR: {a.id} is already used by {p['used_by']}; pick another one")
    dup = seen(p['source'], p.get('dhash'), skip_lib=p['id'])
    if dup:
        sys.exit(f'ERROR: this photo is already used: {dup}. Pick another one.')
    p['used_by'] = who
    _save(INDEX, INDEX_HEAD, lib)
    register(who, p, library_files(p['id']), library_id=p['id'])
    print(f'{a.id} is now used by {who} (the build copies it into dist/)')
    print(image_dict(dict(p, library=p['id'])))
    left = unused_by_category()[p['category']]
    if left < LOW:
        print(f"NOTE: only {left} unused photos left in the library category '{p['category']}' (fewer than {LOW})")


def cmd_pick(a):
    for p in library():
        if p['category'] == a.category and not p.get('used_by'):
            print(f"{p['id']}  {p['alt_en']}  ({p['site']}, {p['photographer']})")


def cmd_sync(a):
    reg = registry()
    have = {norm_url(r.get('source')) for r in reg}
    n = 0
    for who, im, card in site_photos():
        if norm_url(im.get('source')) in have:
            continue
        section = 'articles' if who.startswith('article:') else 'briefing'
        slug = who.split(':', 1)[1]
        files = library_files(im['library']) if im.get('library') else \
            [os.path.join(CONTENT, section, f'{slug}-{s}.webp') for s in ('lg', 'card')]
        reg.append(dict(used_by=who, site=im.get('site'), source=im.get('source'), photographer=im.get('photographer'),
                        licence=im.get('licence'), **({'library': im['library']} if im.get('library') else {}),
                        dhash=dhash(files[1]), sha256=sha256(files[0])))
        n += 1
    _save(REGISTRY, REGISTRY_HEAD, reg)
    print(f'registry: {n} photos added, {len(reg)} in total')


def cmd_check(a):
    errors = verify()
    for e in errors:
        print('ERROR: ' + e)
    print(f'{len(site_photos())} photos used on the site; {len(registry())} in the registry; {len(library())} in the library')
    for c, n in unused_by_category().items():
        print(f"  library {c:<10} {n:>3} unused" + (f'  (below {LOW})' if n < LOW else ''))
    sys.exit(1 if errors else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('check').set_defaults(f=cmd_check)
    sub.add_parser('sync').set_defaults(f=cmd_sync)
    sp = sub.add_parser('pick'); sp.add_argument('category'); sp.set_defaults(f=cmd_pick)
    sp = sub.add_parser('use'); sp.add_argument('id'); sp.add_argument('--section', required=True, choices=('articles', 'briefing'))
    sp.add_argument('--slug', required=True); sp.set_defaults(f=cmd_use)
    for name, f in (('add', cmd_add), ('live', cmd_live)):
        sp = sub.add_parser(name)
        sp.add_argument('file')
        if name == 'add':
            sp.add_argument('--category', required=True); sp.add_argument('--name', help='file name (default: from the source URL)')
        else:
            sp.add_argument('--section', required=True, choices=('articles', 'briefing')); sp.add_argument('--slug', required=True)
        for k in ('source', 'photographer', 'site', 'licence', 'alt-en', 'alt-ar'):
            sp.add_argument('--' + k, required=True)
        sp.add_argument('--focus', default='50% 50%')
        sp.set_defaults(f=f)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
