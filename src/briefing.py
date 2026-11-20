import importlib, news, pages_en, pages_ar, pages_zh, seo
PC = {'en': pages_en, 'ar': pages_ar, 'zh': pages_zh}
def build(L, render, featured, news_items, path_for):
    importlib.reload(pages_en); importlib.reload(pages_ar); importlib.reload(pages_zh)
    D = PC[L].BRIEFING; out = []
    i = {'en': 0, 'ar': 1, 'zh': 2}[L]
    items = news_items(L, path_for('briefing', L))  # Chinese: only the items that have Chinese text
    cats_used, regions_used = {n['cat'] for n in items}, {n['region'] for n in items}
    # Chinese: tabs only for the topics and regions that have Chinese items (English and Arabic show them all)
    cats = [(k, v[i]) for k, v in news.CATEGORIES.items() if L != 'zh' or k in cats_used]
    regions = [(k, v[i]) for k, v in news.REGIONS.items() if L != 'zh' or k in regions_used]
    out.append(render('briefing.html', 'briefing', L, D['title'], D['desc'], section='briefing', D=D,
                      ITEMS=items, CATS=cats, REGIONS=regions, EN_LIST=path_for('briefing', 'en'),
                      IMPACT=L != 'zh' or any(n['note'] for n in items)))
    for slug in [n['slug'] for n in items]:
        key = 'news-' + slug
        n = next(x for x in news_items(L, path_for(key, L)) if x['slug'] == slug)
        rel = featured(L, [n['related']], path_for(key, L)) if n['related'] else []  # Chinese: only a Chinese article
        out.append(render('news.html', key, L, seo.item_title(key, L), seo.item_desc(key, L), section='briefing', D=D, N=n,
                          RELATED=rel[0] if rel else None))
    return out
