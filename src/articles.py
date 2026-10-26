import importlib, articles_en, articles_ar, articles_meta, guide, seo
AC = {'en': articles_en, 'ar': articles_ar}

def build(L, render, featured, path_for):
    importlib.reload(articles_en); importlib.reload(articles_ar); importlib.reload(guide)
    mod = AC[L]; out = []
    for a in articles_meta.ARTICLES:
        d = mod.ART[a['slug']]; key = 'art-' + a['slug']
        A = featured(L, [a['slug']], path_for(key, L))[0]
        rel = featured(L, d['related'], path_for(key, L))
        title = seo.item_title(key, L)  # the page's own title and summary (seo.py); Article schema and share image too
        desc = seo.item_desc(key, L, d.get('key'))
        if d.get('guide'):
            out.append(render('guide.html', key, L, title, desc, section='insights', A=A, AX=mod.AX,
                              GM=guide.model(a['slug'], L), FIG=guide.figure, F3=guide.FIG3[L], RELATED=rel))
            continue
        out.append(render('article.html', key, L, title, desc, section='insights', A=A, AX=mod.AX,
                          BODY=d['body'], KEY=d['key'], RELATED=rel))
    return out
