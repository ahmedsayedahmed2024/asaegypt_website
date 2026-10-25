"""Fail the build if any internal link or asset in dist/ points to a missing file,
or if any image is over the size limit (CLAUDE.md, "Images"): every image in public/, and every image the
build generates into dist/ (e.g. the email signature banners in dist/assets/img/signature/),
or if the same photo is used twice on the site, or comes from a source or licence that is not allowed (photos.py)."""
import os, re, sys
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
pat = re.compile(r'(?:href|src)="([^"#?]+)')  # also matches data-src
srcset = re.compile(r'srcset="([^"]+)"')      # also matches data-srcset
IMG_EXT = ('.webp', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.avif')
IMG_MAX_KB = 300
missing = set()
pages = 0
for root, _, files in os.walk(DIST):
    for f in files:
        if not f.endswith('.html'):
            continue
        pages += 1
        html = open(os.path.join(root, f), encoding='utf-8').read()
        urls = pat.findall(html) + [c.split()[0] for v in srcset.findall(html) for c in v.split(',') if c.strip()]
        for url in urls:
            u = urlparse(url)
            if u.scheme or u.netloc or url.startswith(('mailto:', 'tel:', 'data:')):
                continue
            path = unquote(u.path)
            base = DIST if path.startswith('/') else root
            target = os.path.normpath(os.path.join(base, path.lstrip('/')))
            if os.path.isdir(target):
                target = os.path.join(target, 'index.html')
            if not os.path.exists(target):
                missing.add((os.path.relpath(os.path.join(root, f), DIST), url))
print(f'{pages} pages checked')
big = []
PUBLIC = os.path.join(ROOT, 'public')
for base in (PUBLIC, DIST):
    for root, _, files in os.walk(base):
        for f in files:
            path = os.path.join(root, f)
            if base == DIST and os.path.exists(os.path.join(PUBLIC, os.path.relpath(path, DIST))):
                continue  # copied from public/: already checked
            if f.lower().endswith(IMG_EXT) and os.path.getsize(path) > IMG_MAX_KB * 1024:
                big.append((os.path.relpath(path, ROOT), os.path.getsize(path) // 1024))
for path, kb in big:
    print(f'IMAGE TOO LARGE: {path} is {kb} KB (limit {IMG_MAX_KB} KB)')
if missing:
    for page, url in sorted(missing):
        print(f'BROKEN: {page} -> {url}')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photos
twice = photos.verify()
for e in twice:
    print('PHOTO: ' + e)
if missing or big or twice:
    sys.exit(1)
print(f'All internal links OK; all images in public/ and generated images in dist/ are under {IMG_MAX_KB} KB; no photo is used twice')
