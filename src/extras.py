import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build as B
import seo
D = B.DIST
# sitemap.xml (public pages only, real lastmod dates), robots.txt (AI crawlers named) and llms.txt: see seo.py
sm, n = seo.sitemap(B)
open(os.path.join(D, 'sitemap.xml'), 'w', encoding='utf-8').write(sm)
open(os.path.join(D, 'robots.txt'), 'w', encoding='utf-8').write(seo.robots())
open(os.path.join(D, 'llms.txt'), 'w', encoding='utf-8').write(seo.llms(B))
open(os.path.join(D,'CNAME'),'w').write('asaegypt.com\n')
open(os.path.join(D,'.nojekyll'),'w').write('')
if os.path.exists(os.path.join(D,'netlify.toml')): os.remove(os.path.join(D,'netlify.toml'))
print('extras ok', n, 'urls')
