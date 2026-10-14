import importlib, articles_en, articles_ar, articles_meta
AC = {'en': articles_en, 'ar': articles_ar}
def build(L, render, featured, path_for):
    importlib.reload(articles_en); importlib.reload(articles_ar)
    mod = AC[L]; out = []
    i = 0 if L == 'en' else 1
    for a in articles_meta.ARTICLES:
        d = mod.ART[a['slug']]; key = 'art-' + a['slug']
        A = featured(L, [a['slug']], path_for(key, L))[0]
        rel = featured(L, d['related'], path_for(key, L))
        title = a['title'][i] + (' | ASA Insights' if L == 'en' else ' | مقالات ASA')
        out.append(render('article.html', key, L, title, a['summary'][i], section='insights', A=A, AX=mod.AX,
                          BODY=d['body'], KEY=d['key'], RELATED=rel))
    return out
