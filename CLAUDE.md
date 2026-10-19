# asaegypt.com — instructions for Claude

Website of **ASA Chartered Accountants and Consultants** (أحمد سيد أحمد محاسبون قانونيون ومستشارون), Giza, Egypt.
Owner: Ahmed Sayed, Managing Partner.
**Ahmed's title everywhere: "Managing Partner" / «الشريك المدير» (never "Founder").**

## How the site is built
- `src/` is the source: Python + Jinja2.
  - `build.py`: routes, rendering, and the 404 page.
  - `extras.py`: `sitemap.xml`, `robots.txt`, and `CNAME`.
  - `check_links.py`: fails the build on broken internal links (including image `srcset`) and on any image in `public/` over 300 KB.
  - `config.py`: site switches. `SHOW_IMAGES` turns all content images on or off (see "Images").
  - `search.py`: the search pages and the passage index (it also writes the passage ids into the built pages). See "Site search" below.
  - `signature_banner.py`: the email signature banner and the `/latest/` pages. See "Email signature banner" below.
  - `hexagon.py`: the ASA Hexagon page (diagram, icons, Open Graph images). See "ASA Hexagon" below.
  - `guide.py`: reference guides (long, structured Insights articles). See "Reference guides" below.
  - `logo.py`: writes the vector logo files (`logo-asa.svg`, `logo-asa-dark.svg`, `favicon.svg`; with `--png` also `favicon-32.png`, `apple-touch-icon.png`, `logo_color@3x.png`). Run by hand only when the logo changes; not part of the build.
- `public/` holds static files (`assets/` CSS/JS/fonts/images, `CNAME`). They are copied into `dist/` before the build.
- Content lives in:
  - `content_en.py` / `content_ar.py`: header/footer strings, services, home page.
  - `pages_en.py` / `pages_ar.py`: inner pages.
  - `articles_meta.py` + `articles_en.py` / `articles_ar.py`: Insights. See "Insights (articles)" below.
  - `news.py`: ASA Briefing (news). See "Briefing (news)" below.
  - `next.py`: ASA NEXT (content for juniors). See "ASA NEXT" below.
- Templates are in `src/templates/`.
- English lives at `/` and Arabic at `/ar/`. **Every change must be made in both languages.**
- Build locally:
  ```
  rm -rf dist && mkdir dist && cp -r public/. dist/ && pip install -q -r requirements.txt && python src/build.py && python src/extras.py && python src/check_links.py
  ```
  The signature banner also needs Chromium for Playwright (`python -m playwright install chromium`, once) and, ideally, `gifsicle`. Without them the build still passes and prints a warning (see "Email signature banner").
- Deploy: GitHub Actions (`.github/workflows/deploy.yml`) builds and publishes to GitHub Pages on every push to `main`, and once a day at 05:30 UTC (8:30 AM Cairo) so the email signature banner refreshes even when nothing is pushed. Never commit `dist/`.
- **The site logo is the vector file**: `public/assets/img/logo-asa.svg` (white wordmark, dark backgrounds) and `logo-asa-dark.svg` (grey wordmark, light header). Never replace it with a raster image. The logo is final (to be registered as a trademark): its hexagon and wordmark are traced exactly from the original artwork, so never redraw them or swap in the homepage hexagon from `mark.py` (a slightly different drawing). Keep `logo_color.png` and `email-qr.png` unchanged: the email signature uses them.
- `public/assets/img/signature/logo-sig.png`, `logo_color.png` and `email-qr.png` are used by email signatures: **never delete or rename them**.
- `public/google2c63994b9b91f271.html` is required by Google Search Console to verify the site. It is published as-is at https://asaegypt.com/google2c63994b9b91f271.html. **Never delete, rename or edit it**, and never add it to the sitemap.

## Workflow
- Work on a `claude/...` branch and open a Pull Request. Ahmed approves by merging.
- Never push directly to `main` unless Ahmed explicitly asks in the session.
- Before opening a PR:
  - Run the full build and link check.
  - Make sure both languages render.
- PR description: a short plain-language summary of what changed, in English.

## Non-negotiable content rules
1. **No names or photos of individual people anywhere on the site, EXCEPT the author name and job title shown as the byline of an Insights article.** The team page stays collective.
2. **No client names.**
3. **No team headcount.** Use "a highly qualified professional team" / «فريق مهني على مستوى عالٍ من الكفاءة».
4. The firm's Arabic name is exactly «أحمد سيد أحمد محاسبون قانونيون ومستشارون».
5. Prior experience is described as Big 4 / international networks. Never name RSM or any specific former firm.
6. Memberships to list:
   - Fellows of the Egyptian Society of Accountants & Auditors
   - Members of the Arab Federation of Accountants & Auditors
   - ACCA, CPA and SOCPA holders
7. ASA operates from Egypt only (no Saudi branch). It serves clients in Egypt, KSA and internationally.
8. **Legal, tax and standards citations** (article, section, paragraph, decree numbers):
   - Never state a specific citation unless it was verified against the original source text.
   - If unverified, describe the rule as established practice and flag the citation for Ahmed's review in the PR.
9. Professional and tax news must come from official or primary sources (Egyptian Tax Authority, FRA, IFRS Foundation, IAASB, ESAA, official gazette, etc.). Link the source.
10. Do not use Netlify (blocked in Egypt). Do not touch DNS email records (MX/TXT).

## The "added" date (articles, Briefing, ASA NEXT)
- **Every new Insights article, Briefing item and ASA NEXT item MUST have `added` = the day it is published on asaegypt.com (YYYY-MM-DD).**
  - `added` is not the same as `date`. For Briefing, `date` is the source's publication date; `added` is the day the item went live on our site.
  - `added_at` (optional, `"HH:MM"` in UTC): the time it was added. It only decides the order of items added on the same day. Set it to the current UTC time when adding an item. An item without it counts as added at the end of its day.
  - Put new items at the top of their list in the data file.
- `image`: see "Images" below. Every new article and Briefing item gets a photo; every new ASA NEXT item gets an illustration.

## Homepage hexagon
- Shows the 8 items most recently **added** to the site, from Insights, Briefing and ASA NEXT together, newest first (sorted by `added`, then `added_at`). 6 seconds per item.
- Built by `brief_slots()` in `src/build.py`; the count is `BRIEF_COUNT`. Briefing items use `short_en/ar` as the headline.
- Size (desktop, wider than 1080px): set from the window height so the whole hexagon, arrows and dashes included, is visible on first load at 100% zoom: height = 100vh − header (84px) − gaps, at least 380px, at most the column width (about 523px). The hero text scales with the height too. Tablet and mobile have their own fixed sizes.
- Controls: previous / next arrows (mirrored in Arabic), progress bars, swipe on touch screens, left/right keys when the hexagon has focus. It pauses on hover and keyboard focus. The intro animation plays once per browser session. With reduced motion it does not rotate.

## Images
Every new Insights article and every new Briefing item MUST get a matching photo under these rules **on the day it is published** (the daily routine follows this). Every new ASA NEXT item MUST get a new original illustration (see "ASA NEXT illustrations" below). If no suitable photo is found, publish without `image` (the logo background and striped placeholder are used) and say so in the PR or final message.

### Source
- Real photos only, from **Unsplash** (unsplash.com) or **Pexels** (pexels.com), under their free licences that allow commercial use. Never Unsplash+ (premium) photos. Never any other website.
- If a site needs an API key or blocks the download, do not use another website: stop and report exactly what is needed.
- Store in the item's data: `image=dict(focus="x% y%", source=<photo page URL>, photographer=<name as shown on the photo page>, site="Unsplash"|"Pexels", licence="Unsplash License"|"Pexels License", alt_en=..., alt_ar=...)`.
- **Every new image (photo or illustration) gets a focus point**: `focus` is the main subject's position as CSS `object-position` ("x% y%", e.g. `"70% 50%"`; 0% 0% is the top-left corner). It keeps the subject in view where the image is cropped: the wide image band on item pages (crops top and bottom), the cards, and the near-square homepage hexagon (crops the sides). Pick the sharp, recognisable part (e.g. the sharp edge of a paper stack, not its blurred middle) and check the band, a card and the hexagon in the browser. Without `focus` the centre is used; an invalid value stops the build.
- Alt text: describe what the photo shows, in both languages (Arabic in فصحى, not a literal translation).

### Content (very strict)
- Calm, professional, neutral images that clearly match the topic: documents, calculators, charts on paper or screens, modern office interiors, architecture, city skylines (Cairo, Gulf cities, global finance districts), servers, chips and abstract technology, ports and trade, etc.
- Prefer NO identifiable people. If people appear: business attire, modest, seen from behind, from a distance or hands only. Never close-up faces.
- NEVER: anything suggestive or revealing, alcohol, smoking, gambling, weapons, violence, religious symbols, political symbols, flags, politicians, protests, maps with disputed borders, logos or brands of any company (including other audit firms), visible text or numbers that could be read as real data, AI-art style images, money piles or "get rich" clichés.
- Check every photo at full size before using it (small logos, signs, names on papers, readable numbers). A small crop or a soft blur of a minor detail is fine; mention it in the PR.
- Each image must be different from the images already used on the site.

### Size and format
- WebP, two versions per photo: `<slug>-lg.webp` (1600px wide, target under 180 KB) and `<slug>-card.webp` (800px wide, target under 70 KB).
- Path: `public/assets/img/content/<section>/` with section `articles`, `briefing` or `next`.
- Never commit the original full-size download. Never commit an image over 300 KB (the build fails).

### ASA NEXT illustrations (no photos)
- One original SVG per item: `public/assets/img/content/next/<slug>.svg`, data `image=dict(focus="x% y%", kind="illustration", alt_en=..., alt_ar=...)`.
- Style: dark #23262B background, lime #C3D648, the logo blues (#80CAE3, #A6D8EE, #B2DCF2), the Spark star, hexagon and stripe motifs. Flat, modern, no people, no text (no letters or numerals).

### Where images appear (built automatically from the data)
- Homepage hexagon: the item's image clipped to the hexagon under dark glass and the logo stripes (fades in, slow zoom; only the current and next image are loaded). Items without an image show the logo background.
- Insights, Briefing and ASA NEXT cards: the card image (800px); striped placeholder when there is no image.
- Article, Briefing and ASA NEXT item pages: a wide image band under the dark header, with the credit "Photo: <name> / Unsplash" / «تصوير: <name> / Unsplash» (no credit for illustrations).

### Switch
- `SHOW_IMAGES` in `src/config.py`. `False` makes the site look exactly as it did before images (logo background in the hexagon, striped card placeholders, no image band). Files and data stay in place.

## Insights (articles)
- Metadata in `src/articles_meta.py` → `ARTICLES`; text in `articles_en.py` / `articles_ar.py` → `ART[slug]`.
- Each article has `added` (see above) and `category`: a key of `CATEGORIES` in `articles_meta.py`.
- Byline: the default for articles not signed by a person is **"ASA Insights Team" / «فريق ASA»**: `author_en="ASA Insights Team"`, `author_ar="فريق ASA"`, `role_en=""`, `role_ar=""`. It shows as "By ASA Insights Team" / «بقلم فريق ASA». Articles signed by a person keep their name and job title (e.g. "By Ahmed Sayed Ahmed, Managing Partner" / «بقلم أحمد سيد أحمد، الشريك المدير»).
- `CATEGORIES` is the one place for Insights categories (EN + AR names). The tabs on `/insights/` are built from it automatically: a tab appears only when at least one article uses that category; order is All, then categories by number of articles (most first).
- **When a new article needs a category that does not exist yet, add it to `CATEGORIES` in both languages.** Its tab then appears automatically. Never hard-code tabs in the template.
- `short` (optional, `(en, ar)`): a shorter title used in the homepage hexagon, the cards and the email banner; the article page keeps the full title.

## Reference guides
- A reference guide is an Insights article with a long, structured body: "The Institutions Behind the Global Accounting and Auditing Profession" (`/insights/global-accounting-auditing-institutions/`). Its entry in `ART` has `guide=True`; its approved text is in `src/guide_en.py` / `guide_ar.py` (never rewrite it); `src/guide.py` builds the page (`templates/guide.html`, `public/assets/js/guide.js`).
- Page: sticky contents with scroll-spy and reading progress (sheet on tablet and phone; `sub=[(id, label)]` on a section adds entries under it), "Find an institution" / «ابحث عن جهة» (the site search engine on this page: an "Institutions" group, then every other match "In this article", and a find bar to step through them), section links, `[text](#id)` links inside the text, a quick guide block (`'quick'`: country cards, a "Common questions" accordion with FAQPage structured data, a disclaimer), institution cards, tables that become stacked cards under 768px, "ASA note" / «ملاحظة ASA» callouts, reference chips and a collapsible references list, three figures (inline SVG, mirrored in Arabic).
- `INST` in `guide.py` is the institution registry: main category (one of the five colours in `CATS`), English and Arabic names, and the reference number used for the card's "Official site" link. Add any new institution there. No organisation logos anywhere.
- Cover: original, drawn by `python src/guide_cover.py --png` (`<slug>.svg` for the image band, `<slug>-card.webp`, `<slug>-og.png` share image); `image=dict(kind="cover", ...)`.
- Each institution's own card or row carries `data-k` (acronym, category, names) so that the site search and the finder put it first for its acronym or name. The reading time is computed from the English text (`guide.minutes()`).
- ASA NEXT links to it from `/next/` through `REFS` in `src/next.py`.

## Email signature banner
- The email signature banner (`dist/assets/img/signature/banner-en.gif`, `banner-ar.gif`, `banner-en.png`, `banner-ar.png`) is generated by `src/signature_banner.py` on every build (called from `build.py`; the site is rebuilt at least daily) from the 3 latest Briefing + Insights items (same `added` order as the homepage hexagon; ASA NEXT is not included). **Never edit or commit it by hand. Its URLs must never change, because sent emails point to them.**
- The banner shows each item's own `date` (for Briefing, the source's publication date), never the `added` date.
- Only professional published content may appear in the banner: it is generated from the site data, nothing else.
- The banner links to `/latest/` and `/ar/latest/` (`?utm_source=email&utm_medium=signature`): the same 3 items as cards. These pages are `noindex` and stay out of the sitemap and the menu.
- Under the hexagon mark: a small "ASA HEXAGON" tag (lime, letter-spaced), in every frame and in both languages.
- How it works: headless Chromium (Playwright) draws each frame from an HTML/SVG template with the site's fonts embedded; Pillow builds the GIF; gifsicle shrinks it. Frame 1 must always be item 1, complete (Outlook on Windows shows only the first frame). Each GIF must stay under 290 KB (`check_links.py` fails the build on any image over 300 KB, generated banners included; no exceptions); if it is too big, the script uses fewer animation steps first, then lossy compression.
- If rendering fails, the build does not fail: it keeps the banners currently on asaegypt.com, or writes a simple static banner, and prints a warning.
- `public/assets/img/signature/logo-sig.png` (the signature logo, 450x134, from `logo-asa-dark.svg`) is written by `python src/logo.py --png`.

## ASA Hexagon
- Page `/hexagon/` and `/ar/hexagon/`: text in `pages_en.py` / `pages_ar.py` → `HEXAGON` (approved by Ahmed: never add to it or "improve" it); diagram, icons and Open Graph images in `src/hexagon.py`; animation in `public/assets/js/hexagon.js`.
- **Fixed, never change:** the six pillars (1 Independence / الاستقلالية, 2 Quality & professional behaviour / الجودة والسلوك المهني, 3 Integrity / النزاهة, 4 Objectivity / الموضوعية, 5 Confidentiality / السرية, 6 Competence & due care / الكفاءة والعناية المهنية); the three balances (top line 1–2 Balance of credibility / ميزان المصداقية, middle dashed line 3–4 Balance of judgement / ميزان الحكم, bottom line 5–6 Balance of responsibility / ميزان المسؤولية); and the corner order: Arabic 1 top-right, 2 top-left, 3 right, 4 left, 5 bottom-right, 6 bottom-left; English mirrored (1 top-left, 2 top-right, 3 left, 4 right, 5 bottom-left, 6 bottom-right).
- The diagram's hexagon outline and stripes come from the traced logo geometry (`logo.py`); never redraw them.
- **Never** add religious references, self-praise or any personal story to this page or anywhere on the site. **Never** publish internal methodology details (internal file names, codes, templates or quality routes).
- "ASA Hexagon" is always written in Latin letters, with capital A-S-A and capital H, in both languages (never «هيكساجون ASA» or «ASA هيكساجون»). In the menu: "ASA" in the menu colour and "Hexagon" in the logo blue #80CAE3 (#1C7AA6 on the white header).
- Header: "ASA Hexagon" comes right after About / «من نحن». Contact / «تواصل معنا» is not in the top menu (it stays in the mobile menu and the footer); the whole header stays on one line from 1081px up.
- Open Graph images (`public/assets/img/og-hexagon-en.png`, `og-hexagon-ar.png`, 1200x630): redraw them with `python src/hexagon.py --og` (after a build) whenever the page title or the diagram changes.

## Site search
- Header search button on every page (EN "Search" / AR «بحث»), shortcuts "/" and Ctrl+K, and the search pages `/search/` and `/ar/search/` (`?q=`). The 404 page has a search box.
- **One engine** (`public/assets/js/search.js`) serves the header search, the search pages and the in-article finder of the reference guide (`guide.js` uses it through `window.ASASearch`).
- **Passages, not pages.** After every page is built, `index_site()` in `src/search.py` reads each public page in `dist/` (not `/search/`, `/latest/` or any noindex page) and splits it into passages: paragraphs, list items, table rows, institution cards, callouts, quick-guide lines, FAQ items and references. Each passage keeps its own id or gets a stable one (`<section id>-p<n>`), written into the HTML with `data-p`. Index files: `dist/assets/search/en.json` and `ar.json` (page URL, title, type, date; passage id, text and breadcrumb). Nothing to update by hand when content is added.
- What is left out: navigation, forms, cards that repeat other pages, page furniture. Mark any other block with `data-noindex`; mark a block that must be one passage with `data-passage`, and give a card or block a breadcrumb label with `data-h`.
- A result opens `<page>?hl=<query>#<passage id>`: the page opens anything that hides the passage (references list, FAQ answer), scrolls it below the header, outlines it and lights up the matching words for about 3 seconds, then removes `?hl=` from the address bar. An old id falls back to the first match on the page.
- **Aliases: `data/search_aliases.yml`** (the only file to edit): designations (CA → ICAS, CA ANZ…; CMA → IMA and the Saudi CMA, labelled) and synonyms in both languages (ESAA ↔ «جمعية المحاسبين والمراجعين المصرية», VAT ↔ «ضريبة القيمة المضافة»…). Every institution in `INST` (`guide.py`) is added automatically with its English and Arabic names.
- Matching: case and accents ignored; Arabic diacritics, tatweel and letter forms unified; «ال» and a leading «و» optional; one wrong letter allowed in words of 5+ letters; words typed in capitals (acronyms) match whole words in the text. Ranking: an institution's own card or row for its acronym or alias, then page title, then section heading, then passage text; ties newest first.
- The index is loaded only when a search box first gets focus. No external services, no tracking, no CDN. Keep each index under 300 KB gzipped (the build prints its size).

## Briefing (news)
- Items live in `src/news.py` → `NEWS` (list page `/briefing/`, item pages `/briefing/<slug>/`, same under `/ar/`). Recently added items also rotate in the homepage hexagon (see above).
- Each item is a dict:
  - `slug`, `date` (YYYY-MM-DD, the source's publication date)
  - `added` (YYYY-MM-DD, the day it went live on our site; **required**), `added_at` (optional, "HH:MM" UTC). See "The added date" above.
  - `category`: `"standards"` | `"tax"` | `"economy"` | `"tech"` (labels in `CATEGORIES`)
  - `region`: `"egypt"` | `"gcc"` | `"global"` (labels in `REGIONS`)
  - `title_en`, `title_ar`
  - `short_en`, `short_ar`: banner headline, max ~10 words
  - `summary_en`, `summary_ar`: 1–2 sentences
  - `body_en`, `body_ar`: list of paragraphs
  - `source_name`, `source_url`: official source (required)
  - `note` (optional): `{type: "impact" | "tech", who_en, who_ar, accounting_en, accounting_ar, auditor_en, auditor_ar}`
  - `related` (optional): slug of a related Insights article
- **Every item needs an official source link** (see rule 9 above).
- **Facts and numbers must match the source exactly.** Do not add facts, dates or figures that are not in the source.
- **Items with a `note` (impact or tech) always go through a pull request for Ahmed's approval.**

## ASA NEXT
- Content for juniors in their first five years in audit, tax and advisory.
- Items live in `src/next.py` → `NEXT`. Each item: `slug`, `section` (`"first5"` or `"desk"`), `added` (**required**) and `added_at` (optional; see "The added date" above), `title_en/ar`, `summary_en/ar`, `body_en/ar` (list of blocks; the block types are listed at the top of the file), `date`, `byline_en/ar` ("ASA Team" / «فريق ASA»).
- Pages: landing `/next/` (blocks "First 5" / «أول 5 سنين» and "Junior Desk" / «ركن الجونيور»), items `/next/<slug>/`, same under `/ar/`. Built by `src/asanext.py`.
- Lockup: Spark icon (`public/assets/img/asa-next-spark.svg`) + wordmark "ASA NEXT", always in English on both sites (never «نكست»), weight 800. Tagline: "Your next step" / «الخطوة التالية».
  - On dark (#23262B): "ASA" #C5C9CF, "NEXT" #C3D648.
  - On light: "ASA" #5F646C, "NEXT" #8FA21A.
- Humour (Junior Desk only): tasteful. No jokes about people, clients or other firms. No slang, no politics, no religion.
- Professional qualifications: link the official body (ACCA, AICPA, SOCPA, ESAA: https://esaa.org.eg/); never state exam dates, fees, pass rates or entry requirements. Say "check the official website for current requirements".

## Writing style
- English: clear, professional, Big-4 tone, no hype.
- Arabic: eloquent Modern Standard Arabic (فصحى), not a literal translation of the English.
- Arabic reading times (built by `read_time()` in `src/build.py`): 3–10 minutes take «دقائق» («7 دقائق قراءة»); 11–99 take «دقيقة» («18 دقيقة قراءة»).
- Fixed terms:
  - Share-based payments in Arabic: always «المدفوعات المبنية على أسهم» (never «المبنية على الأسهم» or «على أساس الأسهم»).
  - QDMTT = Qualified Domestic Minimum Top-up Tax / «ضريبة الحد الأدنى التكميلية المحلية المؤهلة (QDMTT)». Use the full name with the abbreviation.
- In Arabic, attach «و» to the English word that follows, with no space: «ACCA وCPA وSOCPA», «Excel 2021 وMicrosoft 365». A separate «و» can end up alone at the end of a line.
