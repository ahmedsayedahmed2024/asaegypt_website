import importlib, pages_en, pages_ar, pages_zh, articles_meta
PC = {'en': pages_en, 'ar': pages_ar, 'zh': pages_zh}

def all_articles(L, featured, path_for, from_path):
    return featured(L, [a['slug'] for a in articles_meta.ARTICLES], from_path)  # Chinese: only those with Chinese text

def insight_tabs(L, slugs=None):
    """Category tabs for /insights/: only categories used by at least one article (of `slugs` when given: the Chinese
    list counts only its own articles), most articles first (ties keep the order of articles_meta.CATEGORIES).
    Labels come from that one list."""
    i = {'en': 0, 'ar': 1, 'zh': 2}[L]
    keys = list(articles_meta.CATEGORIES)
    count = {}
    for a in articles_meta.ARTICLES:
        if slugs is not None and a['slug'] not in slugs:
            continue
        count[a['category']] = count.get(a['category'], 0) + 1
    used = sorted(count, key=lambda k: (-count[k], keys.index(k)))
    return [(k, articles_meta.CATEGORIES[k][i]) for k in used]

def build_all(L, render, featured, path_for, C, ROUTES):
    importlib.reload(pages_en); importlib.reload(pages_ar); importlib.reload(pages_zh)
    D = PC[L]; mod = C[L]; out = []
    H = D.SERVICES_HUB
    out.append(render('services.html', 'services', L, H['title'], H['desc'], section='services', D=H))
    for s in mod.SERVICES:
        d = D.SVC[s['key']]
        rel = featured(L, d['related'], path_for(s['key'], L)) if L != 'zh' else []  # Chinese service pages: no article cards yet
        out.append(render('service.html', s['key'], L, d['title'], d['desc'], section='services', D=d, S=s, X=D.X, RELATED=rel))
    for key, tpl, sec, obj in [('about', 'about.html', 'about', D.ABOUT), ('who', 'who.html', 'who', D.WHO),
                               ('approach', 'approach.html', 'about', D.APPROACH), ('people', 'people.html', 'people', D.PEOPLE),
                               ('contact', 'contact.html', 'contact', D.CONTACT), ('privacy', 'privacy.html', None, D.PRIVACY)]:
        out.append(render(tpl, key, L, obj['title'], obj['desc'], section=sec, D=obj))
    # Services for Chinese companies (/who-we-serve/chinese-companies/), in all three languages
    D_ = D.CHINA
    out.append(render('china.html', 'china', L, D_['title'], D_['desc'], section='china', D=D_))
    # Insights: on Chinese pages only the articles that have Chinese text (articles_zh.ART_ZH), and a link to the English list
    I = D.INSIGHTS
    arts = all_articles(L, featured, path_for, path_for('insights', L))
    out.append(render('insights.html', 'insights', L, I['title'], I['desc'], section='insights', D=I, ALL=arts,
                      TABS=insight_tabs(L, [a['slug'] for a in arts]), EN_LIST=path_for('insights', 'en')))
    try:
        import articles
        importlib.reload(articles)
        out += articles.build(L, render, featured, path_for)
    except ImportError:
        pass
    return out
