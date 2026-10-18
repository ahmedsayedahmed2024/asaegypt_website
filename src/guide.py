"""Reference guide pages (Insights articles with a long, structured body): "The Institutions Behind the Global
Accounting and Auditing Profession" (/insights/global-accounting-auditing-institutions/, same under /ar/).

The approved text lives in guide_en.py / guide_ar.py. This module adds everything around it:
  - INST: the institution registry (category colour, names in both languages, official site from the references),
  - the page model for templates/guide.html (ids for cards and table rows, the "Find an institution" list,
    the contents list, reference chips and back links),
  - the three figures (inline SVG, mirrored for Arabic), and plain text + keywords for the site search.
"""
import re
from markupsafe import Markup, escape
import guide_en, guide_ar

GUIDES = {'global-accounting-auditing-institutions': {'en': guide_en, 'ar': guide_ar}}

# The five institutional categories (one colour each, from the ASA palette). Legend after section 1.
CATS = {
    'std': ("Standard setters", "جهات إصدار المعايير"),
    'reg': ("Regulators and oversight bodies", "الجهات التنظيمية والرقابية"),
    'pao': ("Professional accountancy organisations", "المنظمات والمعاهد المهنية"),
    'lic': ("Registration and licensing authorities", "جهات القيد والترخيص"),
    'net': ("Networks, forums and cooperation bodies", "الشبكات والمنتديات وجهات التعاون"),
}

# Institution registry: acronym -> (category, English name, Arabic name or None, reference number or None).
# Each institution has its MAIN category (when it has several roles). Arabic names are taken from the
# approved Arabic text. The reference gives the card's "Official site" link (from the references list);
# a URL instead of a number links an official site that is not in the references (approved by Ahmed).
INST = {
    'IFAC': ('pao', "International Federation of Accountants", "الاتحاد الدولي للمحاسبين", 1),
    'IAASB': ('std', "International Auditing and Assurance Standards Board", "المجلس الدولي لمعايير المراجعة والتأكيد", 27),
    'IESBA': ('std', "International Ethics Standards Board for Accountants", "المجلس الدولي لمعايير أخلاقيات المهنة للمحاسبين", 4),
    'IFEA': ('std', "International Foundation for Ethics and Audit", "المؤسسة الدولية للأخلاقيات والمراجعة", 26),
    'PIOB': ('reg', "Public Interest Oversight Board", "مجلس الإشراف على المصلحة العامة", 5),
    'MG': ('reg', "Monitoring Group", "مجموعة المراقبة", None),
    'SAC': ('net', "Stakeholder Advisory Council", "المجلس الاستشاري لأصحاب المصلحة", 29),
    'IFRS Foundation': ('std', "IFRS Foundation", "مؤسسة المعايير الدولية للتقرير المالي", 6),
    'IASB': ('std', "International Accounting Standards Board", "مجلس معايير المحاسبة الدولية", 6),
    'ISSB': ('std', "International Sustainability Standards Board", "مجلس معايير الاستدامة الدولية", 6),
    'IFRS IC': ('std', "IFRS Interpretations Committee", "لجنة تفسيرات المعايير الدولية", 6),
    'FASB': ('std', "Financial Accounting Standards Board", "مجلس معايير المحاسبة المالية الأمريكي", 30),
    'GASB': ('std', "Governmental Accounting Standards Board", "مجلس معايير المحاسبة الحكومية الأمريكي", 31),
    'FAF': ('std', "Financial Accounting Foundation", "مؤسسة المحاسبة المالية الأمريكية", 31),
    'PCAOB': ('reg', "Public Company Accounting Oversight Board", "مجلس الرقابة على محاسبة الشركات العامة", 32),
    'SEC': ('reg', "Securities and Exchange Commission", "هيئة الأوراق المالية والبورصات الأمريكية", "https://www.sec.gov/"),
    'IFIAR': ('net', "International Forum of Independent Audit Regulators", "المنتدى الدولي لهيئات الرقابة المستقلة على المراجعة", 8),
    'FRC': ('reg', "Financial Reporting Council", "مجلس التقارير المالية البريطاني", 11),
    'CEAOB': ('reg', "Committee of European Auditing Oversight Bodies", "لجنة الهيئات الأوروبية للرقابة على المراجعة", 42),
    'CPAB': ('reg', "Canadian Public Accountability Board", "مجلس المساءلة العامة الكندي", 43),
    'ASIC': ('reg', "Australian Securities and Investments Commission", "هيئة الأوراق المالية والاستثمارات الأسترالية", 44),
    'AICPA': ('pao', "American Institute of Certified Public Accountants", "المعهد الأمريكي للمحاسبين القانونيين المعتمدين", 45),
    'ICAEW': ('pao', "Institute of Chartered Accountants in England and Wales", "معهد المحاسبين القانونيين في إنجلترا وويلز", 46),
    'ACCA': ('pao', "Association of Chartered Certified Accountants", "جمعية المحاسبين القانونيين المعتمدين", 47),
    'ICAS': ('pao', "Institute of Chartered Accountants of Scotland", "معهد المحاسبين القانونيين في اسكتلندا", 48),
    'CAI': ('pao', "Chartered Accountants Ireland", "المحاسبون القانونيون في أيرلندا", 49),
    'CIMA': ('pao', "Chartered Institute of Management Accountants", "المعهد القانوني للمحاسبين الإداريين", 50),
    'CIPFA': ('pao', "Chartered Institute of Public Finance and Accountancy", "المعهد القانوني للمالية العامة والمحاسبة", 51),
    'CA ANZ': ('pao', "Chartered Accountants Australia and New Zealand", "المحاسبون القانونيون في أستراليا ونيوزيلندا", 52),
    'CPA Australia': ('pao', "CPA Australia", None, 53),
    'IMA': ('pao', "Institute of Management Accountants", "معهد المحاسبين الإداريين", 54),
    'IIA': ('pao', "The Institute of Internal Auditors", "معهد المراجعين الداخليين", 14),
    'ISACA': ('pao', "ISACA (originally Information Systems Audit and Control Association)", None, 55),
    'CFA Institute': ('pao', "CFA Institute", "معهد المحللين الماليين", 56),
    'IIASB': ('std', "International Internal Audit Standards Board", "مجلس معايير المراجعة الداخلية الدولية", None),
    'COSO': ('std', "Committee of Sponsoring Organizations of the Treadway Commission", "لجنة المنظمات الراعية للجنة تريدواي", 15),
    'IPSASB': ('std', "International Public Sector Accounting Standards Board", "المجلس الدولي لمعايير المحاسبة للقطاع العام", 41),
    'IPSAS': ('std', "International Public Sector Accounting Standards", "معايير المحاسبة الدولية للقطاع العام", None),
    'INTOSAI': ('net', "International Organization of Supreme Audit Institutions", "المنظمة الدولية للأجهزة العليا للرقابة المالية والمحاسبة", 16),
    'ISSAI': ('std', "International Standards of Supreme Audit Institutions", "المعايير الدولية للأجهزة العليا للرقابة", None),
    'IFPP': ('std', "INTOSAI Framework of Professional Pronouncements", "إطار الإصدارات المهنية لمنظمة INTOSAI", None),
    'SAI': ('reg', "Supreme Audit Institution", "الجهاز الأعلى للرقابة في الدولة", None),
    'IAESB': ('std', "International Accounting Education Standards Board", "مجلس معايير التعليم المحاسبي الدولي", None),
    'BIS': ('net', "Bank for International Settlements", "بنك التسويات الدولية", 57),
    'BCBS': ('std', "Basel Committee on Banking Supervision", "لجنة بازل للرقابة المصرفية", 58),
    'FSB': ('net', "Financial Stability Board", "مجلس الاستقرار المالي", 59),
    'IOSCO': ('net', "International Organization of Securities Commissions", "المنظمة الدولية لهيئات الأوراق المالية", 60),
    'IAIS': ('std', "International Association of Insurance Supervisors", "الرابطة الدولية لمراقبي التأمين", 61),
    'AAOIFI': ('std', "Accounting and Auditing Organization for Islamic Financial Institutions", "هيئة المحاسبة والمراجعة للمؤسسات المالية الإسلامية", 62),
    'IFSB': ('std', "Islamic Financial Services Board", "مجلس الخدمات المالية الإسلامية", 63),
    'GRI': ('std', "Global Reporting Initiative", "المبادرة العالمية لإعداد تقارير الاستدامة", 17),
    'GSSB': ('std', "Global Sustainability Standards Board", None, 17),
    'EFRAG': ('std', "European Financial Reporting Advisory Group", "المجموعة الاستشارية الأوروبية للتقارير المالية", 64),
    'ESRS': ('std', "European Sustainability Reporting Standards", "المعايير الأوروبية لإعداد تقارير الاستدامة", None),
    'SASB': ('std', "Sustainability Accounting Standards Board", None, 65),
    'FoF': ('net', "Forum of Firms", "منتدى شبكات ومكاتب المراجعة الدولية", 19),
    'TAC': ('net', "Transnational Auditors Committee", "لجنة المراجعين عبر الحدود", None),
    'GPPC': ('net', "Global Public Policy Committee", "لجنة السياسة العامة العالمية", 67),
    'GAA': ('net', "Global Accounting Alliance", None, 66),
    'PAFA': ('net', "Pan African Federation of Accountants", "الاتحاد الأفريقي للمحاسبين", 68),
    'CAPA': ('net', "Confederation of Asian and Pacific Accountants", "اتحاد المحاسبين في آسيا والمحيط الهادئ", 69),
    'Accountancy Europe': ('net', "Accountancy Europe", None, 70),
    'ROSC': ('net', "Reports on the Observance of Standards and Codes", "تقارير تقييم الالتزام بالمعايير والقواعد", 71),
    'MoF': ('lic', "Ministry of Finance (Egypt): General Register of Accountants and Auditors", "وزارة المالية: السجل العام للمحاسبين والمراجعين", 21),
    'SOCPA': ('lic', "Saudi Organization for Chartered and Professional Accountants", "الهيئة السعودية للمراجعين والمحاسبين", 24),
    'State Boards': ('lic', "State Boards of Accountancy", "مجالس المحاسبة في الولايات", 10),
    'NASBA': ('lic', "National Association of State Boards of Accountancy", "الرابطة الوطنية لمجالس المحاسبة بالولايات", 10),
    'RSBs': ('lic', "Recognised Supervisory Bodies", "جهات الإشراف المعترف بها", 11),
    'RQBs': ('pao', "Recognised Qualifying Bodies", None, None),
    'FRA': ('reg', "Financial Regulatory Authority (Egypt)", "الهيئة العامة للرقابة المالية", 22),
    'CBE': ('reg', "Central Bank of Egypt", "البنك المركزي المصري", 73),
    'ESAA': ('pao', "Egyptian Society of Accountants and Auditors", "جمعية المحاسبين والمراجعين المصرية", 72),
    'Syndicate of Commerce': ('pao', "Syndicate of Commerce", "النقابة العامة للتجاريين", None),
    'CMA': ('reg', "Capital Market Authority (Saudi Arabia)", "هيئة السوق المالية", None),
    'SAMA': ('reg', "Saudi Central Bank", "البنك المركزي السعودي", 74),
    'GCA': ('reg', "General Court of Audit (Saudi Arabia)", "الديوان العام للمحاسبة", 76),
    'Accountability State Authority': ('reg', "Accountability State Authority (Egypt)", "الجهاز المركزي للمحاسبات", 75),
    'AICPA & CIMA': ('pao', "Association of International Certified Professional Accountants", None, 50),
}
# "Official site" when the reference is the institution's own website, "Official source" otherwise
SOURCE_NOT_SITE = {'SAC', 'GASB', 'FAF', 'State Boards', 'NASBA', 'RSBs'}
# hexagon badge text on two lines
BADGE_LINES = {'IFRS Foundation': ('IFRS', 'Foundation'), 'IFRS IC': ('IFRS', 'IC'), 'State Boards': ('State', 'Boards')}

# Finder entries that point to a card or row of another institution (no card or row of their own)
FIND_ALSO = [('FRA', 'MoF'), ('CBE', 'MoF'), ('ESAA', 'MoF'), ('Syndicate of Commerce', 'MoF'),
             ('CMA', 'SOCPA'), ('SAMA', 'SOCPA'), ('NASBA', 'State Boards'), ('RQBs', 'RSBs'),
             ('IIASB', 'IIA'), ('AICPA & CIMA', 'AICPA'), ('MG', 'MG'),
             ('GCA', 'r-supreme-audit'), ('Accountability State Authority', 'r-supreme-audit'), ('IAESB', 'p-iaesb'),
             ('FASB', 'FASB'), ('GASB', 'GASB'), ('FAF', 'FAF'), ('CEAOB', 'CEAOB'), ('CPAB', 'CPAB'), ('ASIC', 'ASIC')]

UI = {
    'en': dict(contents="Contents", find="Find an institution", find_ph="Acronym or name", find_eg="For example: IFAC, PCAOB, SOCPA, the Financial Regulatory Authority",
               find_none="No institution found", find_hint="Use ↑ ↓ and Enter", legend="Category colours",
               official="Official site", source="Official source", note="ASA note", sources="Related sources",
               refs_show="Show the {n} references", refs_hide="Hide the references", back="Back to the text",
               top="Back to top", copy="Copy the link to this section", copied="Link copied",
               ref_label="Reference {n}", cite_label="References {a} to {b}", reading="Reference guide",
               reviewed="Last reviewed", progress="Reading progress", close="Close", now="You are reading",
               fig_text="In text"),
    'ar': dict(contents="المحتويات", find="ابحث عن جهة", find_ph="اختصار أو اسم", find_eg="مثل IFAC أو PCAOB أو SOCPA أو الهيئة العامة للرقابة المالية",
               find_none="لم نعثر على جهة بهذا الاسم", find_hint="استخدم ↑ ↓ ثم Enter", legend="ألوان التصنيفات",
               official="الموقع الرسمي", source="المصدر الرسمي", note="ملاحظة ASA", sources="المراجع ذات الصلة",
               refs_show="عرض المراجع ({n})", refs_hide="إخفاء المراجع", back="العودة إلى النص",
               top="العودة إلى أعلى الصفحة", copy="نسخ رابط هذا القسم", copied="تم نسخ الرابط",
               ref_label="المرجع {n}", cite_label="المراجع من {a} إلى {b}", reading="دليل مرجعي",
               reviewed="آخر مراجعة", progress="مدى التقدم في القراءة", close="إغلاق", now="تقرأ الآن",
               fig_text="بالنص"),
}

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def cat_of(text):
    """Category of a table cell naming an institution (exact registry key, or the first known acronym in it)."""
    t = re.sub(r'\*', '', text).strip()
    if t == 'Monitoring Group':
        return 'MG'
    if t in INST:
        return t
    for k in sorted(INST, key=len, reverse=True):
        if re.search(r'(?<![A-Za-z])' + re.escape(k) + r'(?![A-Za-z])', t):
            return k
    return None

# ---------- inline text: **bold**, links to www. addresses, Arabic bidi ----------
LATIN_RUN = re.compile(r"[A-Za-z][A-Za-z0-9’']*(?:(?: ?[—–/&+]| ?[(]|[.:,)\-])? ?[A-Za-z0-9(][A-Za-z0-9’')]*)*\)?")
WWW = re.compile(r'(www\.[a-z0-9.-]+\.[a-z]{2,})')

def _bidi(s, L):
    if L != 'ar':
        return escape(s)
    out, last = [], 0
    for m in LATIN_RUN.finditer(s):
        run, end = m.group(), m.end()
        while run.endswith(')') and run.count(')') > run.count('('):  # a bracket opened in the Arabic text
            run, end = run[:-1], end - 1
        cls = ' class="lt"' if len(run) <= 22 else ''  # short runs never break; long English titles may wrap
        out += [escape(s[last:m.start()]), Markup(f'<bdi{cls}>'), escape(run), Markup('</bdi>')]
        last = end
    out.append(escape(s[last:]))
    return Markup('').join(out)

def rich(s, L):
    parts = s.split('**')
    html = Markup('')
    for i, p in enumerate(parts):
        if not p:
            continue
        frag = _bidi(p, L)
        frag = Markup(WWW.sub(lambda m: f'<a href="https://{m.group(1)}/" target="_blank" rel="noopener">{m.group(1)}</a>',
                              str(frag)))
        html += Markup('<strong>') + frag + Markup('</strong>') if i % 2 else frag
    return html

# ---------- page model ----------
def model(slug_, L, ref_urls=None):
    G = GUIDES[slug_][L].GUIDE
    U = UI[L]
    i = 0 if L == 'en' else 1
    ids = {}            # acronym -> element id of its card or table row (first occurrence)
    rows_seen = []
    refs = {n: dict(n=n, title=t, url=u, host=h, back=None) for n, t, u, h in G['refs']}
    chip_no = [0]

    def inst_name(acr, lang):
        e = INST[acr]
        return e[1] if lang == 'en' else (e[2] or e[1])

    def card(c):
        acr = c['acr']
        e = INST[acr]
        cid = 'i-' + slug(acr)
        ids.setdefault(acr, cid)
        ref = dict(url=e[3]) if isinstance(e[3], str) else refs.get(e[3]) if e[3] else None
        other = c['other'] or (e[2] if L == 'en' else e[1])
        return dict(kind='inst', id=cid, acr=acr, cat=e[0], n=c['n'], name=c['name'], other=other,
                    badge=BADGE_LINES.get(acr, (acr,)), blocks=[block(b) for b in c['blocks']],
                    link=ref and dict(url=ref['url'], label=U['source'] if acr in SOURCE_NOT_SITE else U['official']))

    def table(t, sid):
        head, rows = t['head'], t['rows']
        badge_col = None
        if head and head[0] in ('Acronym', 'الاختصار', 'Institution'):
            badge_col = 0
        elif len(head) > 1 and head[1] == 'الجهة':
            badge_col = 1
        rowcats = ['std', 'reg', 'reg', 'pao', 'lic'] if sid == 'institution-types' else None
        out = []
        for r_i, r in enumerate(rows):
            acr = cat_of(r[badge_col]) if badge_col is not None else None
            cat = INST[acr][0] if acr else (rowcats[r_i] if rowcats else None)
            rid = None
            if acr and acr not in ids and acr not in rows_seen:
                rid = 'r-' + slug(acr)
                rows_seen.append(acr)
            if sid == 'egypt-saudi' and r_i == 9:
                rid = 'r-supreme-audit'  # supreme audit institutions row: target of the finder for the national bodies
            out.append(dict(cells=r, acr=acr, cat=cat, id=rid))
        short = None
        if sid == 'egypt-saudi':
            short = [head[0]] + (["International", "Egypt", "Saudi Arabia"] if L == 'en' else ["دوليًا", "مصر", "السعودية"])
        return dict(kind='table', head=head, rows=out, badge_col=badge_col, short=short or head,
                    wide=len(head) >= 4)

    def block(b):
        k = b[0]
        if k == 'inst':
            return card(b[1])
        if k == 'table':
            return table(b[1], cur_sid[0])
        if k == 'cites':
            chips = []
            for a, z in b[1]:
                chip_no[0] += 1
                cid = f'cite-{chip_no[0]}'
                for n in range(a, z + 1):
                    if refs[n]['back'] is None:
                        refs[n]['back'] = cid
                chips.append(dict(id=cid, a=a, z=z, label=str(a) if a == z else f"{a}–{z}",
                                  aria=U['ref_label'].format(n=a) if a == z else U['cite_label'].format(a=a, b=z)))
            return dict(kind='cites', chips=chips)
        if k == 'fig':
            return dict(kind='fig', n=b[1], caption=b[2], text=b[3])
        if k == 'p' and '**IAESB' in b[1]:
            return dict(kind='p', text=b[1], id='p-iaesb')
        return dict(kind=k, text=b[1] if isinstance(b[1], str) else None, list=b[1] if not isinstance(b[1], str) else None)

    cur_sid = [None]
    sections = []
    for s in G['sections']:
        cur_sid[0] = s['id']
        sections.append(dict(id=s['id'], n=s['n'], title=s['title'], toc=s['toc'] or s['title'],
                             blocks=[block(b) for b in s['blocks']]))
    # cards come before rows for the same institution (e.g. the IIA row in section 5 and its card in section 6):
    # rows only take an id when no card exists
    for s in sections:
        for b in walk(s['blocks']):
            if b['kind'] == 'table':
                for r in b['rows']:
                    if r['id'] and r['id'].startswith('r-') and r['acr'] in ids:  # the institution has a card
                        r['id'] = None
                    elif r['id'] and r['acr']:
                        ids.setdefault(r['acr'], r['id'])
    # finder: every card and institution row, plus the bodies that only appear inside another card
    find, seen = [], set()
    def add(acr, target):
        if acr in seen or not target:
            return
        seen.add(acr)
        e = INST[acr]
        label = "AICPA & CIMA" if acr == 'AICPA & CIMA' else acr
        find.append(dict(a=label, n=e[1], m=e[2] or '', c=e[0], t=target))
    for s in sections:
        for b in walk(s['blocks']):
            if b['kind'] == 'inst':
                add(b['acr'], b['id'])
            elif b['kind'] == 'table':
                for r in b['rows']:
                    if r['id'] and r['acr']:
                        add(r['acr'], r['id'])
    all_ids = {b.get('id') for s in sections for b in walk(s['blocks'])} | \
              {r['id'] for s in sections for b in walk(s['blocks']) if b['kind'] == 'table' for r in b['rows']}
    for acr, to in FIND_ALSO:
        target = to if to in all_ids else ids.get(to)
        add(acr, target)
    num = iter(range(1, 100))
    toc = [dict(id=s['id'], num=next(num) if s['n'] else None, label=s['toc']) for s in sections]
    legend = [dict(key=k, label=v[i]) for k, v in CATS.items()]
    return dict(G=G, U=U, sections=sections, refs=[refs[n] for n in sorted(refs)], find=find, toc=toc,
                legend=legend, nrefs=len(refs), cats={k: v[i] for k, v in CATS.items()})

def walk(blocks):
    for b in blocks:
        yield b
        if b.get('kind') == 'inst':
            yield from walk(b['blocks'])

# ---------- search ----------
def keywords(slug_, L):
    """Institution acronyms and names for the site search (so searching "PCAOB" or «هيئة السوق المالية» finds the guide)."""
    G = GUIDES[slug_][L].GUIDE
    text = str(G)
    out = []
    for k, e in INST.items():
        if k == 'AICPA & CIMA':
            continue
        if re.search(r'(?<![A-Za-z])' + re.escape(k) + r'(?![A-Za-z])', text) or (e[2] and e[2] in text):
            out.append(k)
            out.append(e[1] if L == 'en' else (e[2] or e[1]))
    return ' '.join(out)

# ---------- figures ----------
# Figure 1 and 2: inline SVG drawn from boxes, lines and labels laid out in a left-to-right coordinate system;
# the Arabic figures are the mirror image (x -> W - x). Two layouts each: "w" (tablet and desktop) and "n" (phone).
FIG_TEXT = {
 1: {'en': dict(MG=("Monitoring Group", "System governance monitoring", ("System governance", "monitoring")),
                IFEA=("IFEA", "International Foundation for Ethics and Audit", ("International Foundation", "for Ethics and Audit")),
                PIOB=("PIOB", "Public interest oversight", ("Public interest", "oversight")),
                IAASB=("IAASB", "Audit, assurance and quality", ("Audit, assurance", "and quality")),
                IESBA=("IESBA", "Ethics and independence", ("Ethics and", "independence")),
                SAC=("SAC", "Stakeholder Advisory Council", ("Stakeholder Advisory Council",)),
                IFAC=("IFAC", "Global professional federation", ("Global professional federation",)),
                gov=("Governance monitoring", ("Governance", "monitoring")), home=("Institutional home", ("Institutional", "home")),
                ovs=("Independent oversight and appointments", ("Independent oversight", "and appointments")),
                adv="Advice", ifac_note="IFAC does not approve technical standards",
                solid="Solid lines: institutional relationship", dashed="Dashed lines: oversight or advice"),
        'ar': dict(MG=("Monitoring Group", "متابعة المنظومة ككل", ("متابعة المنظومة", "ككل")),
                IFEA=("IFEA", "المؤسسة الدولية للأخلاقيات والمراجعة", ("المؤسسة الدولية", "للأخلاقيات والمراجعة")),
                PIOB=("PIOB", "رقابة المصلحة العامة", ("رقابة المصلحة", "العامة")),
                IAASB=("IAASB", "المراجعة والتأكيد والجودة", ("المراجعة والتأكيد", "والجودة")),
                IESBA=("IESBA", "الأخلاقيات والاستقلالية", ("الأخلاقيات", "والاستقلالية")),
                SAC=("SAC", "المجلس الاستشاري لأصحاب المصلحة", ("المجلس الاستشاري لأصحاب المصلحة",)),
                IFAC=("IFAC", "التعاون والتمثيل المهني", ("التعاون والتمثيل المهني",)),
                gov=("متابعة الحوكمة", ("متابعة", "الحوكمة")), home=("المظلة المؤسسية", ("المظلة", "المؤسسية")),
                ovs=("الرقابة المستقلة والتعيينات", ("الرقابة المستقلة", "والتعيينات")),
                adv="المشورة", ifac_note="IFAC لا يعتمد المعايير الفنية",
                solid="الخطوط المتصلة: علاقة مؤسسية", dashed="الخطوط المتقطعة: رقابة أو مشورة")},
 2: {'en': dict(MB=("IFRS Foundation Monitoring Board", "Public accountability", ("Public accountability",)),
                TR=("IFRS Foundation Trustees", "Governance, strategy and funding", ("Governance, strategy and funding",)),
                IASB=("IASB", "IFRS Accounting Standards", ("IFRS Accounting", "Standards")),
                ISSB=("ISSB", "IFRS Sustainability Disclosure Standards", ("IFRS Sustainability", "Disclosure Standards")),
                IC=("IFRS Interpretations Committee", "Supports consistent application", ("Supports consistent application",)),
                ovs="Oversight and accountability", tech="Technical support",
                n1="Two independent standard-setting boards", n2="A separate structure from the IFEA system"),
        'ar': dict(MB=("IFRS Foundation Monitoring Board", "المساءلة العامة", ("المساءلة العامة",)),
                TR=("IFRS Foundation Trustees", "الحوكمة والاستراتيجية والتمويل", ("الحوكمة والاستراتيجية والتمويل",)),
                IASB=("IASB", "معايير IFRS للمحاسبة", ("معايير IFRS", "للمحاسبة")),
                ISSB=("ISSB", "معايير IFRS لإفصاحات الاستدامة", ("معايير IFRS", "لإفصاحات الاستدامة")),
                IC=("IFRS Interpretations Committee", "دعم التطبيق المتسق للمعايير", ("دعم التطبيق المتسق للمعايير",)),
                ovs="الإشراف والمساءلة", tech="دعم فني",
                n1="مجلسان مستقلان لوضع المعايير", n2="منظومة منفصلة عن منظومة IFEA")},
}
FIG3 = {
 'en': dict(steps=["Professional qualification", "Membership where required", "Statutory registration or practice licence",
                   "Sector-specific eligibility"],
            end="Authority to perform the relevant statutory audit",
            end_sub="Verify the firm, the signing individual and the engagement scope",
            note="Illustrative pathway: conditions and their sequence vary by jurisdiction"),
 'ar': dict(steps=["التأهيل العلمي والمهني", "العضوية المهنية حيث تُشترط", "القيد أو الترخيص القانوني",
                   "الأهلية لمراجعة فئة معينة من المنشآت"],
            end="الحق في تنفيذ المراجعة القانونية المعنية",
            end_sub="تحقَّق من المكتب، والشخص الموقِّع، ونطاق الارتباط",
            note="مسار توضيحي؛ تختلف الشروط وترتيبها من دولة إلى أخرى"),
}

class Canvas:
    def __init__(self, W, H, rtl):
        self.W, self.H, self.rtl, self.out = W, H, rtl, []
    def X(self, x):
        return self.W - x if self.rtl else x
    def text(self, x, y, s, cls, extra=''):
        d = ' direction="rtl"' if self.rtl else ''
        self.out.append(f'<text x="{self.X(x)}" y="{y}" class="{cls}"{d}{extra}>{escape(s)}</text>')
    def box(self, x, y, w, h, title, subs, cls=''):
        rx = self.X(x + w) if self.rtl else x
        self.out.append(f'<rect x="{rx}" y="{y}" width="{w}" height="{h}" rx="8" class="fb {cls}"/>')
        cx = x + w / 2
        n = len(subs)
        top = y + h / 2 - (n * 17) / 2 - 2
        self.text(cx, top + 6, title, 'ft')
        for k, s in enumerate(subs):
            self.text(cx, top + 26 + k * 17, s, 'fs')
    def line(self, pts, kind='solid', arrow=True):
        d = 'M' + ' L'.join(f'{self.X(x)} {y}' for x, y in pts)
        m = f' marker-end="url(#ah-{kind}-{{fid}})"' if arrow else ''
        self.out.append(f'<path d="{d}" class="fl fl-{kind}"{m}/>')
    def label(self, x, y, lines, cls='fla'):
        if isinstance(lines, str):
            lines = (lines,)
        for k, s in enumerate(lines):
            self.text(x, y + k * 15, s, cls)
    def svg(self, fid, title):
        defs = ''.join(f'<marker id="ah-{k}-{fid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                       f'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10z" class="fm fm-{k}"/></marker>' for k in ('solid', 'dashed'))
        body = '\n'.join(self.out).replace('{fid}', fid)
        return (f'<svg viewBox="0 0 {self.W} {self.H}" role="img" aria-label="{escape(title)}" class="gfig-svg">'
                f'<defs>{defs}</defs>{body}</svg>')

def fig1(L, v):
    T = FIG_TEXT[1][L]; rtl = L == 'ar'
    if v == 'w':
        c = Canvas(820, 640, rtl)
        c.box(20, 20, 300, 78, T['MG'][0], (T['MG'][1],))
        c.box(400, 20, 400, 78, T['IFEA'][0], (T['IFEA'][1],))
        c.box(20, 170, 300, 78, T['PIOB'][0], (T['PIOB'][1],))
        c.box(380, 300, 200, 86, T['IAASB'][0], (T['IAASB'][1],), 'key')
        c.box(600, 300, 200, 86, T['IESBA'][0], (T['IESBA'][1],), 'key')
        c.box(20, 470, 300, 78, T['IFAC'][0], (T['IFAC'][1],))
        c.box(450, 470, 280, 78, T['SAC'][0], (T['SAC'][1],))
        c.line([(170, 98), (170, 168)], 'dashed'); c.label(170, 138, T['gov'][0])
        c.line([(600, 98), (600, 230)], 'solid', False); c.line([(480, 230), (720, 230)], 'solid', False)
        c.line([(480, 230), (480, 298)]); c.line([(700, 230), (700, 298)]); c.label(600, 160, T['home'][0])
        c.line([(170, 248), (170, 268), (720, 268)], 'dashed', False)
        c.line([(500, 268), (500, 298)], 'dashed'); c.line([(720, 268), (720, 298)], 'dashed')
        c.label(270, 262, T['ovs'][0])
        c.line([(530, 470), (530, 428), (480, 428), (480, 388)], 'dashed')
        c.line([(650, 470), (650, 428), (700, 428), (700, 388)], 'dashed')
        c.label(590, 432, T['adv'])
        c.label(170, 574, T['ifac_note'], 'fno')
        c.line([(150, 616), (190, 616)], 'solid', False); c.label(200, 620, T['solid'], 'fle' + (' rtl' if rtl else ''))
        c.line([(470, 616), (510, 616)], 'dashed', False); c.label(520, 620, T['dashed'], 'fle')
        return c
    c = Canvas(360, 770, rtl)
    c.box(10, 10, 160, 92, T['MG'][0], T['MG'][2])
    c.box(190, 10, 160, 92, T['IFEA'][0], T['IFEA'][2])
    c.line([(90, 102), (90, 148)], 'dashed'); c.label(90, 122, T['gov'][1])
    c.box(10, 150, 160, 92, T['PIOB'][0], T['PIOB'][2])
    c.line([(250, 102), (250, 328)]); c.label(250, 168, T['home'][1])
    c.line([(110, 242), (110, 328)], 'dashed')
    c.line([(110, 264), (290, 264), (290, 328)], 'dashed')
    c.line([(250, 304), (70, 304), (70, 328)])
    c.label(180, 282, T['ovs'][1], 'fla small')
    c.box(10, 330, 160, 92, T['IAASB'][0], T['IAASB'][2], 'key')
    c.box(190, 330, 160, 92, T['IESBA'][0], T['IESBA'][2], 'key')
    c.line([(90, 480), (90, 424)], 'dashed'); c.line([(270, 480), (270, 424)], 'dashed')
    c.label(180, 456, T['adv'])
    c.box(10, 480, 340, 78, T['SAC'][0], T['SAC'][2])
    c.box(10, 590, 340, 78, T['IFAC'][0], T['IFAC'][2])
    c.label(180, 694, T['ifac_note'], 'fno')
    c.line([(40, 728), (76, 728)], 'solid', False); c.label(86, 732, T['solid'], 'fle')
    c.line([(40, 752), (76, 752)], 'dashed', False); c.label(86, 756, T['dashed'], 'fle')
    return c

def fig2(L, v):
    T = FIG_TEXT[2][L]; rtl = L == 'ar'
    if v == 'w':
        c = Canvas(820, 600, rtl)
        c.box(190, 20, 440, 80, T['MB'][0], (T['MB'][1],))
        c.line([(410, 100), (410, 168)]); c.label(410, 140, T['ovs'])
        c.box(190, 170, 440, 80, T['TR'][0], (T['TR'][1],))
        c.line([(410, 250), (410, 285)], 'solid', False); c.line([(200, 285), (620, 285)], 'solid', False)
        c.line([(200, 285), (200, 328)]); c.line([(620, 285), (620, 328)])
        c.box(40, 330, 320, 80, T['IASB'][0], (T['IASB'][1],), 'key')
        c.box(460, 330, 320, 80, T['ISSB'][0], (T['ISSB'][1],), 'key')
        c.box(40, 500, 320, 80, T['IC'][0], (T['IC'][1],))
        c.line([(200, 500), (200, 412)], 'dashed'); c.label(200, 460, T['tech'])
        c.label(620, 532, T['n1'], 'fnb'); c.label(620, 556, T['n2'], 'fno')
        return c
    c = Canvas(360, 590, rtl)
    c.box(10, 10, 340, 78, T['MB'][0], T['MB'][2])
    c.line([(180, 88), (180, 138)]); c.label(180, 118, T['ovs'])
    c.box(10, 140, 340, 78, T['TR'][0], T['TR'][2])
    c.line([(180, 218), (180, 240)], 'solid', False); c.line([(90, 240), (270, 240)], 'solid', False)
    c.line([(90, 240), (90, 268)]); c.line([(270, 240), (270, 268)])
    c.box(10, 270, 160, 92, T['IASB'][0], T['IASB'][2], 'key')
    c.box(190, 270, 160, 92, T['ISSB'][0], T['ISSB'][2], 'key')
    c.line([(90, 430), (90, 364)], 'dashed'); c.label(90, 402, T['tech'])
    c.box(10, 430, 340, 78, T['IC'][0], T['IC'][2])
    c.label(180, 544, T['n1'], 'fnb'); c.label(180, 566, T['n2'], 'fno')
    return c

def figure(n, L, v, title):
    c = (fig1 if n == 1 else fig2)(L, v)
    return Markup(c.svg(f'f{n}{v}', title))
