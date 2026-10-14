import importlib, pages_en, pages_ar
import next as nextdata
PC = {'en': pages_en, 'ar': pages_ar}
def build(L, render, next_items, path_for):
    importlib.reload(pages_en); importlib.reload(pages_ar)
    D = PC[L].NEXT_PAGE; out = []
    i = 0 if L == 'en' else 1
    items = next_items(L, path_for('next', L))
    blocks = [(k, v[i], D['blocks'][k], [x for x in items if x['section'] == k]) for k, v in nextdata.SECTIONS.items()]
    out.append(render('next.html', 'next', L, D['title'], D['desc'], section='next', D=D, BLOCKS=blocks))
    for x in nextdata.NEXT:
        key = 'nx-' + x['slug']
        n = [y for y in next_items(L, path_for(key, L)) if y['slug'] == x['slug']][0]
        title = n['title'] + ' | ASA NEXT'
        out.append(render('next_item.html', key, L, title, n['summary'], section='next', D=D, N=n))
    return out
