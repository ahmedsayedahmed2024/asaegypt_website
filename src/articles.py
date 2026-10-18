import importlib, json, articles_en, articles_ar, articles_meta, guide
AC = {'en': articles_en, 'ar': articles_ar}

def article_schema(a, A, L, path, og):
    """schema.org Article for a reference guide (author, dates, share image)."""
    d = {"@context": "https://schema.org", "@type": "Article", "headline": A['title'], "description": A['summary'],
         "inLanguage": L, "url": "https://asaegypt.com" + path, "mainEntityOfPage": "https://asaegypt.com" + path,
         "image": "https://asaegypt.com/" + og, "datePublished": a['date'], "dateModified": a.get('reviewed', a['date']),
         "author": {"@type": "Person", "name": a['author_' + L], "jobTitle": a['role_' + L]},
         "publisher": {"@type": "Organization", "name": "ASA Chartered Accountants and Consultants",
                       "logo": {"@type": "ImageObject", "url": "https://asaegypt.com/assets/img/logo_color@3x.png"}}}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace('</', '<\\/') + '</script>'

def build(L, render, featured, path_for):
    importlib.reload(articles_en); importlib.reload(articles_ar); importlib.reload(guide)
    mod = AC[L]; out = []
    i = 0 if L == 'en' else 1
    for a in articles_meta.ARTICLES:
        d = mod.ART[a['slug']]; key = 'art-' + a['slug']
        A = featured(L, [a['slug']], path_for(key, L))[0]
        rel = featured(L, d['related'], path_for(key, L))
        title = a['title'][i] + (' | ASA Insights' if L == 'en' else ' | مقالات ASA')
        if d.get('guide'):
            og = f"assets/img/content/articles/{a['slug']}-og.png"
            out.append(render('guide.html', key, L, title, a['summary'][i], section='insights', A=A, AX=mod.AX,
                              GM=guide.model(a['slug'], L), FIG=guide.figure, F3=guide.FIG3[L], RELATED=rel,
                              og_image='/' + og, og_type='article', schema=article_schema(a, A, L, path_for(key, L), og)))
            continue
        out.append(render('article.html', key, L, title, a['summary'][i], section='insights', A=A, AX=mod.AX,
                          BODY=d['body'], KEY=d['key'], RELATED=rel))
    return out
