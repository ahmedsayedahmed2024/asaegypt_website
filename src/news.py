# ASA Briefing — professional news items (see CLAUDE.md, "Briefing (news)").
# Every item needs an official source link, and its facts and numbers must match that source exactly.
# Items with a note (impact / tech) always go through a pull request for Ahmed's approval.

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
 dict(slug="ifrs-18-effective-2027", date="2026-10-14", category="standards", region="global",
      title_en="IFRS 18 applies from 1 January 2027 — comparatives must be restated",
      title_ar="المعيار IFRS 18 يسري اعتبارًا من 1 يناير 2027 مع إعادة عرض أرقام المقارنة",
      short_en="IFRS 18 applies from 2027: plan the restatement now",
      short_ar="IFRS 18 يسري من 2027: خطط لإعادة العرض الآن",
      summary_en="IFRS 18 replaces IAS 1 for annual reporting periods beginning on or after 1 January 2027, with new defined subtotals in the statement of profit or loss.",
      summary_ar="يحل المعيار IFRS 18 محل المعيار IAS 1 للفترات المالية السنوية التي تبدأ في 1 يناير 2027 أو بعده، ويستحدث مجاميع فرعية محددة في قائمة الأرباح أو الخسائر.",
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
