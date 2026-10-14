"""Fail the build if any internal link or asset in dist/ points to a missing file."""
import os, re, sys
from urllib.parse import urlparse, unquote

DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dist')
pat = re.compile(r'(?:href|src)="([^"#?]+)')
missing = set()
pages = 0
for root, _, files in os.walk(DIST):
    for f in files:
        if not f.endswith('.html'):
            continue
        pages += 1
        html = open(os.path.join(root, f), encoding='utf-8').read()
        for url in pat.findall(html):
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
if missing:
    for page, url in sorted(missing):
        print(f'BROKEN: {page} -> {url}')
    sys.exit(1)
print('All internal links OK')
