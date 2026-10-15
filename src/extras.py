import os, sys, datetime
sys.path.insert(0, os.path.dirname(__file__))
import build as B
D = B.DIST
urls = sorted(set(v for k, v in B.ROUTES.items() if k not in B.NO_SITEMAP))
today = datetime.date.today().isoformat()
sm = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for u in urls:
    for L in ('en','ar'):
        loc = B.SITE + (u if L=='en' else '/ar'+u)
        sm.append(f'<url><loc>{loc}</loc><lastmod>{today}</lastmod>'
                  f'<xhtml:link rel="alternate" hreflang="en" href="{B.SITE}{u}"/>'
                  f'<xhtml:link rel="alternate" hreflang="ar" href="{B.SITE}/ar{u}"/></url>')
sm.append('</urlset>')
open(os.path.join(D,'sitemap.xml'),'w').write('\n'.join(sm))
open(os.path.join(D,'robots.txt'),'w').write(f"User-agent: *\nAllow: /\n\nSitemap: {B.SITE}/sitemap.xml\n")
open(os.path.join(D,'CNAME'),'w').write('asaegypt.com\n')
open(os.path.join(D,'.nojekyll'),'w').write('')
if os.path.exists(os.path.join(D,'netlify.toml')): os.remove(os.path.join(D,'netlify.toml'))
print('extras ok', len(urls)*2, 'urls')
