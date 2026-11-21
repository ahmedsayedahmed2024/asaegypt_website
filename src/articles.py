import importlib, articles_en, articles_ar, articles_zh, articles_meta, guide, seo
AC = {'en': articles_en, 'ar': articles_ar, 'zh': articles_zh}


def zh_related(slug, featured, from_path):
    """Related articles on a Chinese article page: the English article's related articles that have Chinese text, then
    the other Chinese articles (newest first), three at most."""
    own = articles_zh.ART_ZH[slug].get('related') or articles_en.ART[slug]['related']
    pool = [a['slug'] for a in featured('zh', [x['slug'] for x in articles_meta.ARTICLES], from_path)]
    order = [s for s in own if s in pool and s != slug] + [s for s in pool if s not in own and s != slug]
    return [featured('zh', [s], from_path)[0] for s in order[:3]]


def build(L, render, featured, path_for):
    importlib.reload(articles_en); importlib.reload(articles_ar); importlib.reload(articles_zh); importlib.reload(guide)
    mod = AC[L]; out = []
    for a in articles_meta.ARTICLES:
        key = 'art-' + a['slug']
        if L == 'zh':
            if a['slug'] not in articles_zh.ART_ZH:  # not published in Chinese yet
                continue
            d = articles_zh.ART_ZH[a['slug']]
        else:
            d = mod.ART[a['slug']]
        A = featured(L, [a['slug']], path_for(key, L))[0]
        rel = zh_related(a['slug'], featured, path_for(key, L)) if L == 'zh' else featured(L, d['related'], path_for(key, L))
        title = seo.item_title(key, L)  # the page's own title and summary (seo.py); Article schema and share image too
        desc = seo.item_desc(key, L, d.get('key'))
        if d.get('guide'):
            out.append(render('guide.html', key, L, title, desc, section='insights', A=A, AX=mod.AX,
                              GM=guide.model(a['slug'], L), FIG=guide.figure, F3=guide.FIG3[L], RELATED=rel))
            continue
        out.append(render('article.html', key, L, title, desc, section='insights', A=A, AX=mod.AX,
                          BODY=d['body'], KEY=d['key'], RELATED=rel))
    return out
