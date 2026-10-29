"""IndexNow: tell Bing and the other IndexNow search engines which pages changed, after each deploy.
See CLAUDE.md, "SEO, AI search and sharing". Used by .github/workflows/deploy.yml:
  python src/indexnow.py changed   (build job, before deploying) compare dist/sitemap.xml with the sitemap now live on
                                   asaegypt.com and print "urls=<JSON list>" for $GITHUB_OUTPUT: new pages, pages whose
                                   lastmod changed and pages that left the sitemap. Every page if the live one can't be read.
                                   Also the home pages (EN and AR) when the site icon changed (ICON_FILES differ from the
                                   live ones): search engines take the favicon from the home page when they recrawl it.
  python src/indexnow.py submit    (after a successful deploy) send the URLs in $INDEXNOW_URLS to api.indexnow.org.
It never fails the deploy: any error prints a warning and exits 0.
The key below is public by design: search engines check it at https://asaegypt.com/<KEY>.txt (public/<KEY>.txt).
Never delete or rename that file.
"""
import json, os, re, sys, urllib.error, urllib.request

KEY = '0a195d396e647247bae669ec9295b3bb'
HOST = 'asaegypt.com'
SITE = 'https://' + HOST
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.indexnow.org/indexnow'
# the site icon (site_assets.py) and the home pages that declare it
ICON_FILES = ['favicon.ico', 'site.webmanifest', 'assets/img/favicon.svg', 'assets/img/favicon-32.png',
              'assets/img/favicon-48.png', 'assets/img/favicon-96.png', 'assets/img/favicon-192.png',
              'assets/img/favicon-512.png', 'assets/img/apple-touch-icon.png']
HOMES = [SITE + '/', SITE + '/ar/']


def entries(xml):
    """{url: lastmod} of a sitemap."""
    return {m.group(1): m.group(2) for m in re.finditer(r'<loc>([^<]+)</loc>\s*(?:<lastmod>([^<]*)</lastmod>)?', xml)}


def fetch(path):
    req = urllib.request.Request(f'{SITE}/{path}', headers={'User-Agent': 'asaegypt-deploy'})
    return urllib.request.urlopen(req, timeout=20).read()


def icon_changed():
    """True when any icon file in dist/ differs from the one now live (or is not live yet)."""
    for f in ICON_FILES:
        try:
            live = fetch(f)
        except urllib.error.HTTPError:  # 404: a new icon file
            return True
        if live != open(os.path.join(ROOT, 'dist', f), 'rb').read():
            return True
    return False


def changed():
    new = entries(open(os.path.join(ROOT, 'dist', 'sitemap.xml'), encoding='utf-8').read())
    try:
        old = entries(fetch('sitemap.xml').decode('utf-8'))
    except Exception as e:  # first deploy, or the site can't be reached: send every page
        print(f'::warning::IndexNow: could not read the live sitemap ({e}); listing every page', file=sys.stderr)
        old = {}
    urls = [u for u, d in new.items() if old.get(u) != d] + [u for u in old if u not in new]
    try:
        if old and icon_changed():
            print('IndexNow: the site icon changed; adding the home pages', file=sys.stderr)
            urls += [u for u in HOMES if u not in urls]
    except Exception as e:
        print(f'::warning::IndexNow: could not compare the site icon ({e})', file=sys.stderr)
    print(f'IndexNow: {len(urls)} changed URLs', file=sys.stderr)
    print('urls=' + json.dumps(urls[:10000]))


def submit():
    urls = json.loads(os.environ.get('INDEXNOW_URLS') or '[]')
    if not urls:
        print('IndexNow: nothing changed')
        return
    body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': f'{SITE}/{KEY}.txt', 'urlList': urls}).encode()
    req = urllib.request.Request(API, data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f'IndexNow: sent {len(urls)} URLs, HTTP {r.status}')


if __name__ == '__main__':
    try:
        {'changed': changed, 'submit': submit}[sys.argv[1]]()
    except Exception as e:
        print(f'::warning::IndexNow skipped: {e}')
        if sys.argv[1:2] == ['changed']:
            print('urls=[]')
    sys.exit(0)
