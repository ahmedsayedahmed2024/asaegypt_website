# ASA Briefing — professional news items (see CLAUDE.md, "Briefing (news)").
# Every item needs an official source link, and its facts and numbers must match that source exactly.
# Items with a note (impact / tech) always go through a pull request for Ahmed's approval.
# "date" is the source's publication date. "added" (YYYY-MM-DD) is the day the item went live on asaegypt.com:
# REQUIRED on every item; the homepage hexagon is ordered by it. "added_at" (optional "HH:MM" UTC) only orders
# items added on the same day (missing = end of that day).
# "image": the item's photo (REQUIRED for new items when a suitable photo exists; see CLAUDE.md, "Images"):
#   dict(source=photo page URL, photographer, site="Unsplash"|"Pexels", licence, alt_en, alt_ar).
#   Files: public/assets/img/content/briefing/<slug>-lg.webp and <slug>-card.webp.

CATEGORIES = {
    'standards': ("Standards & Reporting", "المعايير والتقارير المالية"),
    'tax': ("Egypt Tax", "الضرائب في مصر"),
    'economy': ("Economy & Region", "الاقتصاد والمنطقة"),
    'tech': ("Technology & AI", "التقنية والذكاء الاصطناعي"),
}

REGIONS = {
    'egypt': ("Egypt", "مصر"),
    'gcc': ("GCC", "الخليج"),
    'global': ("Global", "دولي"),
}

NEWS = [
 dict(slug="uae-top-up-tax-scope-registration-guide", date="2026-10-08", added="2026-10-15", added_at="04:15", category="economy", region="gcc",
      title_en="UAE Federal Tax Authority issues guide on scope and registration for the Top-up Tax on multinationals",
      title_ar="الهيئة الاتحادية للضرائب في الإمارات تصدر دليلًا بشأن نطاق الضريبة الإضافية على الشركات متعددة الجنسيات والتسجيل فيها",
      short_en="UAE issues Top-up Tax guide on scope and registration",
      short_ar="الإمارات تصدر دليل نطاق الضريبة الإضافية والتسجيل فيها",
      summary_en="The UAE Federal Tax Authority has published a guide explaining which multinational groups fall within the Qualified Domestic Minimum Top-up Tax (QDMTT) and how in-scope entities register.",
      summary_ar="أصدرت الهيئة الاتحادية للضرائب في الإمارات دليلًا يوضح المجموعات متعددة الجنسيات الخاضعة لضريبة الحد الأدنى التكميلية المحلية المؤهلة (QDMTT)، وإجراءات تسجيل المنشآت الواقعة في نطاقها.",
      image=dict(source="https://unsplash.com/photos/modern-skyscrapers-rise-above-a-blue-ocean-with-boat-YwGd8qGY5BA",
                 photographer="raghul ayyasamy", site="Unsplash", licence="Unsplash License",
                 alt_en="Abu Dhabi skyline across the water under a clear blue sky",
                 alt_ar="أفق مدينة أبوظبي عبر المياه تحت سماء زرقاء صافية"),
      body_en=[
          "The UAE Federal Tax Authority (FTA) has issued a Top-up Tax Guide on Scope and Registration for multinational enterprise (MNE) groups. It covers how to determine whether a group is within the scope of the Qualified Domestic Minimum Top-up Tax (QDMTT) legislation, which entities are and are not subject to the tax, and the registration process and timelines.",
          "The guide includes worked examples on permanent establishments, joint ventures, flow-through and hybrid entities, the location of entities, and the filing of the Pillar Two Information Return. It is aimed at those responsible for the tax affairs of group entities and at tax agents.",
          "According to the FTA, the QDMTT applies for fiscal years beginning on or after 1 January 2025 to UAE constituent entities of MNE groups with annual revenue of EUR 750 million or more in the ultimate parent's consolidated financial statements in at least two of the four preceding fiscal years. Groups operating only within the UAE are outside its scope, whatever their revenue.",
      ],
      body_ar=[
          "أصدرت الهيئة الاتحادية للضرائب في دولة الإمارات دليلًا إرشاديًا بشأن نطاق الضريبة الإضافية والتسجيل فيها، موجّهًا إلى مجموعات الشركات متعددة الجنسيات. ويبيّن الدليل كيفية تحديد خضوع المجموعة لتشريع ضريبة الحد الأدنى التكميلية المحلية المؤهلة (QDMTT)، والمنشآت الخاضعة للضريبة وغير الخاضعة لها، فضلًا عن إجراءات التسجيل ومواعيده.",
          "ويتضمن الدليل أمثلة تطبيقية تتناول المنشآت الدائمة، والمشروعات المشتركة، والمنشآت الشفافة ضريبيًا والمنشآت الهجينة، وتحديد موقع المنشآت، وتقديم إقرار معلومات الركيزة الثانية. وهو موجّه إلى القائمين على الشؤون الضريبية لمنشآت المجموعات، وإلى الوكلاء الضريبيين.",
          "ووفقًا للهيئة، تسري هذه الضريبة على الفترات الضريبية التي تبدأ في 1 يناير 2025 أو بعده، وتنطبق على المنشآت المكوِّنة الكائنة في الإمارات والتابعة لمجموعات متعددة الجنسيات تبلغ إيراداتها السنوية 750 مليون يورو أو أكثر في القوائم المالية الموحدة للمنشأة الأم النهائية، وذلك في سنتين على الأقل من السنوات المالية الأربع السابقة. أما المجموعات التي يقتصر نشاطها على داخل الإمارات فلا تخضع لها أيًّا كان حجم إيراداتها.",
      ],
      source_name="UAE Federal Tax Authority",
      source_url="https://tax.gov.ae/en/media.centre/news/federal.tax.authority.issues.new.guide.on.scope.and.registration.for.topup.tax.on.multinational.enterprises.aspx"),
 dict(slug="ifrs-18-effective-2027", date="2026-10-14", added="2026-10-14", added_at="17:13", category="standards", region="global",
      title_en="IFRS 18 applies from 1 January 2027 — comparatives must be restated",
      title_ar="المعيار IFRS 18 يسري اعتبارًا من 1 يناير 2027 مع إعادة عرض أرقام المقارنة",
      short_en="IFRS 18 applies from 2027: plan the restatement now",
      short_ar="IFRS 18 يسري من 2027: خطط لإعادة العرض الآن",
      summary_en="IFRS 18 replaces IAS 1 for annual reporting periods beginning on or after 1 January 2027, with new defined subtotals in the statement of profit or loss.",
      summary_ar="يحل المعيار IFRS 18 محل المعيار IAS 1 للفترات المالية السنوية التي تبدأ في 1 يناير 2027 أو بعده، ويستحدث مجاميع فرعية محددة في قائمة الأرباح أو الخسائر.",
      image=dict(source="https://unsplash.com/photos/white-notebook-with-pen-on-top-1ixT36dfuSQ",
                 photographer="Diana Polekhina", site="Unsplash", licence="Unsplash License",
                 alt_en="Blank spiral notebook with a pen on a grey surface",
                 alt_ar="دفتر حلزوني فارغ وقلم على سطح رمادي"),
      body_en=[
          "IFRS 18 Presentation and Disclosure in Financial Statements replaces IAS 1 for annual reporting periods beginning on or after 1 January 2027, with early application permitted.",
          "It introduces two defined subtotals in the statement of profit or loss — operating profit and profit before financing and income taxes — requires disclosure of management-defined performance measures, and sets new principles for aggregation and disaggregation.",
      ],
      body_ar=[
          "يحل المعيار IFRS 18 «العرض والإفصاح في القوائم المالية» محل المعيار IAS 1، ويسري على الفترات المالية السنوية التي تبدأ في 1 يناير 2027 أو بعده، مع جواز التطبيق المبكر.",
          "ويستحدث المعيار مجموعين فرعيين محددين في قائمة الأرباح أو الخسائر، هما: الربح التشغيلي، والربح قبل التمويل وضرائب الدخل. كما يُلزم بالإفصاح عن مقاييس الأداء التي تحددها الإدارة، ويرسي مبادئ جديدة لتجميع المعلومات وتفصيلها.",
      ],
      source_name="IFRS Foundation",
      source_url="https://www.ifrs.org/issued-standards/list-of-standards/ifrs-18-presentation-and-disclosure-in-financial-statements/",
      note=dict(type="impact",
                who_en="Entities reporting under IFRS, including Egyptian subsidiaries reporting to foreign groups.",
                who_ar="المنشآت التي تعد قوائمها وفق المعايير الدولية، ومنها الشركات التابعة المصرية التي ترفع تقاريرها لمجموعات أجنبية.",
                accounting_en="For December year-end entities, the 2026 comparative statement of profit or loss is restated, and first-quarter 2027 interim statements already use the new structure.",
                accounting_ar="بالنسبة للمنشآت التي تنتهي سنتها المالية في 31 ديسمبر، يُعاد عرض قائمة الأرباح أو الخسائر المقارنة لسنة 2026، ويُطبَّق الهيكل الجديد بدءًا من القوائم الدورية للربع الأول من 2027.",
                auditor_en="Plan procedures over category classification, new subtotals and comparative reclassifications.",
                auditor_ar="التخطيط لإجراءات المراجعة على تصنيف الفئات والمجاميع الفرعية الجديدة وإعادة تبويب أرقام المقارنة."),
      related="ifrs-18-egypt-what-changes"),
]
