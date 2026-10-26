"""IndexNow: tell Bing and the other IndexNow search engines which pages changed, after each deploy.
See CLAUDE.md, "SEO, AI search and sharing". Used by .github/workflows/deploy.yml:
  python src/indexnow.py changed   (build job, before deploying) compare dist/sitemap.xml with the sitemap now live on
                                   asaegypt.com and print "urls=<JSON list>" for $GITHUB_OUTPUT: new pages, pages whose
                                   lastmod changed and pages that left the sitemap. Every page if the live one can't be read.
  python src/indexnow.py submit    (after a successful deploy) send the URLs in $INDEXNOW_URLS to api.indexnow.org.
It never fails the deploy: any error prints a warning and exits 0.
The key below is public by design: search engines check it at https://asaegypt.com/<KEY>.txt (public/<KEY>.txt).
Never delete or rename that file.
"""
import json, os, re, sys, urllib.request

KEY = '0a195d396e647247bae669ec9295b3bb'
HOST = 'asaegypt.com'
SITE = 'https://' + HOST
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.indexnow.org/indexnow'


def entries(xml):
    """{url: lastmod} of a sitemap."""
    return {m.group(1): m.group(2) for m in re.finditer(r'<loc>([^<]+)</loc>\s*(?:<lastmod>([^<]*)</lastmod>)?', xml)}


def changed():
    new = entries(open(os.path.join(ROOT, 'dist', 'sitemap.xml'), encoding='utf-8').read())
    try:
        req = urllib.request.Request(SITE + '/sitemap.xml', headers={'User-Agent': 'asaegypt-deploy'})
        old = entries(urllib.request.urlopen(req, timeout=20).read().decode('utf-8'))
    except Exception as e:  # first deploy, or the site can't be reached: send every page
        print(f'::warning::IndexNow: could not read the live sitemap ({e}); listing every page', file=sys.stderr)
        old = {}
    urls = [u for u, d in new.items() if old.get(u) != d] + [u for u in old if u not in new]
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
