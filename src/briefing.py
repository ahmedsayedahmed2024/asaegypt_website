import importlib, news, pages_en, pages_ar, seo
PC = {'en': pages_en, 'ar': pages_ar}
def build(L, render, featured, news_items, path_for):
    importlib.reload(pages_en); importlib.reload(pages_ar)
    D = PC[L].BRIEFING; out = []
    i = 0 if L == 'en' else 1
    cats = [(k, v[i]) for k, v in news.CATEGORIES.items()]
    regions = [(k, v[i]) for k, v in news.REGIONS.items()]
    out.append(render('briefing.html', 'briefing', L, D['title'], D['desc'], section='briefing', D=D,
                      ITEMS=news_items(L, path_for('briefing', L)), CATS=cats, REGIONS=regions))
    for slug in [n['slug'] for n in news.NEWS]:
        key = 'news-' + slug
        n = next(x for x in news_items(L, path_for(key, L)) if x['slug'] == slug)
        rel = featured(L, [n['related']], path_for(key, L)) if n['related'] else []
        out.append(render('news.html', key, L, seo.item_title(key, L), seo.item_desc(key, L), section='briefing', D=D, N=n,
                          RELATED=rel[0] if rel else None))
    return out
