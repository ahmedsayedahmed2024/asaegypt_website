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
 dict(slug="imf-world-economic-outlook-october-2026", date="2026-10-13", added="2026-10-19", added_at="04:17", category="economy", region="global",
      title_en="IMF October 2026 World Economic Outlook projects global growth of 3.1% in 2026",
      title_ar="صندوق النقد الدولي يتوقع في تقرير «آفاق الاقتصاد العالمي» لأكتوبر 2026 نمو الاقتصاد العالمي بنسبة 3.1% في 2026",
      short_en="IMF projects 3.1% global growth in 2026",
      short_ar="صندوق النقد يتوقع نمو الاقتصاد العالمي 3.1% في 2026",
      summary_en="The IMF's October 2026 World Economic Outlook, \"Resilience Under Strain, Urgent Choices\", projects global growth of 3.1% in 2026 and 3.4% in 2027, with global headline inflation of 4.7% in 2026 easing to 4.1% in 2027.",
      summary_ar="يتوقع تقرير «آفاق الاقتصاد العالمي» الصادر عن صندوق النقد الدولي في أكتوبر 2026، بعنوان «صمود تحت الضغط وخيارات عاجلة»، أن يبلغ النمو العالمي 3.1% في 2026 و3.4% في 2027، وأن يسجل التضخم الكلي العالمي 4.7% في 2026 قبل أن يتراجع إلى 4.1% في 2027.",
      image=dict(focus="40% 35%", source="https://unsplash.com/photos/skyscrapers-with-reflective-glass-against-a-blue-sky-VR5dx0VJ9PM",
                 photographer="Tom Caillarec", site="Unsplash", licence="Unsplash License",
                 alt_en="Curved glass office towers reflecting a blue sky with scattered clouds",
                 alt_ar="أبراج مكتبية زجاجية منحنية تعكس سماءً زرقاء تتناثر فيها السحب"),
      body_en=[
          "The International Monetary Fund published its October 2026 World Economic Outlook, titled \"Resilience Under Strain, Urgent Choices\", on 13 October 2026. The projections are based on statistical information available through 1 October 2026.",
          "The IMF projects global growth of 3.1% in 2026, rising to 3.4% in 2027. Global headline inflation is projected at 4.7% in 2026, easing to 4.1% in 2027. The report describes the global economy as resilient, but says that this resilience is increasingly uneven and costly, with energy-importing economies outside the technology value chain facing the most difficult outlook.",
          "The IMF sees risks tilted to the downside: escalating conflicts, a reassessment of expectations around artificial intelligence, renewed trade tensions and fiscal vulnerabilities. Upside possibilities include stronger AI investment and productivity gains, and a lasting easing of geopolitical and trade tensions.",
          "On policy, the report calls for rebuilding fiscal space, preserving monetary and financial stability, raising potential growth and deepening international cooperation. A chapter on cost-of-living crises finds that temporary, targeted income support is the most cost-effective protection, and that price-suppressing measures can cost 3 to 22 times more than targeted transfers. A further chapter examines corporate income taxation, including the cross-border effects of debt-financed tax cuts and the role of stronger anti-avoidance rules.",
      ],
      body_ar=[
          "أصدر صندوق النقد الدولي في 13 أكتوبر 2026 تقرير «آفاق الاقتصاد العالمي» لشهر أكتوبر 2026، بعنوان «صمود تحت الضغط وخيارات عاجلة». وتستند توقعات التقرير إلى البيانات الإحصائية المتاحة حتى 1 أكتوبر 2026.",
          "ويتوقع الصندوق أن يبلغ النمو العالمي 3.1% في 2026، ثم يرتفع إلى 3.4% في 2027، وأن يسجل التضخم الكلي العالمي 4.7% في 2026، ثم يتراجع إلى 4.1% في 2027. ويصف التقرير الاقتصاد العالمي بأنه لا يزال صامدًا، غير أن هذا الصمود بات متفاوتًا على نحو متزايد ومرتفع التكلفة، إذ تواجه الاقتصادات المستوردة للطاقة غير المندمجة في سلاسل القيمة التكنولوجية أصعب الآفاق.",
          "ويرى الصندوق أن المخاطر تميل إلى الجانب السلبي، ومنها تصاعد النزاعات، وإعادة تقييم التوقعات المعقودة على الذكاء الاصطناعي، وتجدد التوترات التجارية، ومواطن الضعف في المالية العامة. أما عوامل التحسن المحتملة فتشمل تنامي الاستثمار في الذكاء الاصطناعي وما قد يحققه من مكاسب في الإنتاجية، إلى جانب انحسار دائم للتوترات الجيوسياسية والتجارية.",
          "وعلى صعيد السياسات، يدعو التقرير إلى إعادة بناء الحيز المالي، والحفاظ على الاستقرار النقدي والمالي، ورفع معدلات النمو الممكنة، وتعميق التعاون الدولي. ويخلص فصل مخصص لأزمات غلاء المعيشة إلى أن الدعم المؤقت للدخل الموجّه إلى الفئات الأكثر احتياجًا هو أكثر وسائل الحماية فاعلية من حيث التكلفة، وأن تدابير كبح الأسعار قد تتكلف ما بين 3 و22 ضعف تكلفة التحويلات الموجهة. ويتناول فصل آخر ضريبة دخل الشركات، بما في ذلك الآثار العابرة للحدود للتخفيضات الضريبية الممولة بالدين، ودور قواعد مكافحة التجنب الضريبي الأكثر صرامة.",
      ],
      source_name="International Monetary Fund",
      source_url="https://www.imf.org/en/publications/weo/issues/2026/10/13/world-economic-outlook-october-2026"),
 dict(slug="egypt-moodys-upgrade-b3", date="2026-10-17", added="2026-10-18", added_at="04:17", category="economy", region="egypt",
      title_en="Ministry of Finance responds to Moody's upgrade of Egypt's rating to B3 with a positive outlook",
      title_ar="وزارة المالية تعلّق على رفع «موديز» تصنيف مصر إلى B3 مع نظرة مستقبلية إيجابية",
      short_en="Moody's upgrades Egypt to B3, outlook positive",
      short_ar="«موديز» ترفع تصنيف مصر إلى B3 بنظرة إيجابية",
      summary_en="Following Moody's upgrade of Egypt's credit rating to B3 with a positive outlook, the Ministry of Finance issued a statement setting out the fiscal and external indicators behind the move.",
      summary_ar="عقب رفع مؤسسة «موديز» التصنيف الائتماني لمصر إلى B3 مع نظرة مستقبلية إيجابية، أصدرت وزارة المالية بيانًا استعرضت فيه المؤشرات المالية والخارجية المرتبطة بهذه الخطوة.",
      image=dict(focus="40% 62%", source="https://unsplash.com/photos/the-sun-is-setting-over-a-city-with-tall-buildings-Oh6ZTXzPKe0",
                 photographer="Jens Aber", site="Unsplash", licence="Unsplash License",
                 alt_en="Cairo skyline in silhouette against an orange sunset sky",
                 alt_ar="أفق القاهرة يرتسم ظلًّا داكنًا أمام سماء الغروب البرتقالية"),
      body_en=[
          "Moody's has raised Egypt's credit rating to B3 with a positive outlook. In a statement published by the Egyptian Tax Authority, the Ministry of Finance attributed the upgrade to economic and fiscal reforms that, in its words, have stabilised public finances, strengthened reserves and accelerated economic activity.",
          "The ministry cited three indicators: government debt reduced to 81.9% of GDP in June 2026; net international reserves of USD 57 billion in September 2026; and tax revenues rising to 13% of GDP, an increase of 1.6% of GDP over two years, which it said was achieved without additional burdens.",
          "The statement also acknowledged high debt-service costs and said the ministry will work to reduce them faster, improve the business environment, increase private investment and create fiscal space for more spending on health, education and targeted social protection.",
      ],
      body_ar=[
          "رفعت مؤسسة «موديز» التصنيف الائتماني لمصر إلى B3 مع نظرة مستقبلية إيجابية. وفي بيان نشرته مصلحة الضرائب المصرية، عزت وزارة المالية هذه الخطوة إلى الإصلاحات الاقتصادية والمالية التي أسهمت، بحسب البيان، في استقرار المالية العامة وتعزيز الاحتياطيات وتسريع وتيرة النشاط الاقتصادي.",
          "واستشهدت الوزارة بثلاثة مؤشرات: انخفاض الدين الحكومي إلى 81.9% من الناتج المحلي في يونيو 2026، وارتفاع صافي الاحتياطيات الدولية إلى 57 مليار دولار في سبتمبر 2026، وزيادة الإيرادات الضريبية إلى 13% من الناتج المحلي، بارتفاع قدره 1.6% من الناتج خلال عامين، مؤكدةً أن ذلك تحقق دون أعباء إضافية.",
          "وأقرّ البيان بارتفاع تكلفة خدمة الدين، مشيرًا إلى أن الوزارة ستعمل على خفضها بوتيرة أسرع، وعلى تحسين بيئة الأعمال وزيادة الاستثمارات الخاصة، وإتاحة حيز مالي يسمح بزيادة الإنفاق على الصحة والتعليم والحماية الاجتماعية الموجهة.",
      ],
      source_name="Egyptian Ministry of Finance (via the Egyptian Tax Authority)",
      source_url="https://www.eta.gov.eg/ar/news/alaqtsad-almsry-bat-akthr-qdrt-ly-alnmw-rghm-alsdmat"),
 dict(slug="uae-top-up-tax-scope-registration-guide", date="2026-10-08", added="2026-10-15", added_at="04:15", category="economy", region="gcc",
      title_en="UAE Federal Tax Authority issues guide on scope and registration for the Top-up Tax on multinationals",
      title_ar="الهيئة الاتحادية للضرائب في الإمارات تصدر دليلًا بشأن نطاق الضريبة الإضافية على الشركات متعددة الجنسيات والتسجيل فيها",
      short_en="UAE issues Top-up Tax guide on scope and registration",
      short_ar="الإمارات تصدر دليل نطاق الضريبة الإضافية والتسجيل فيها",
      summary_en="The UAE Federal Tax Authority has published a guide explaining which multinational groups fall within the Qualified Domestic Minimum Top-up Tax (QDMTT) and how in-scope entities register.",
      summary_ar="أصدرت الهيئة الاتحادية للضرائب في الإمارات دليلًا يوضح المجموعات متعددة الجنسيات الخاضعة لضريبة الحد الأدنى التكميلية المحلية المؤهلة (QDMTT)، وإجراءات تسجيل المنشآت الواقعة في نطاقها.",
      image=dict(focus="58% 62%", source="https://unsplash.com/photos/modern-skyscrapers-rise-above-a-blue-ocean-with-boat-YwGd8qGY5BA",
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
      image=dict(focus="52% 55%", source="https://unsplash.com/photos/white-notebook-with-pen-on-top-1ixT36dfuSQ",
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
