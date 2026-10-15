# asaegypt.com — instructions for Claude

Website of **ASA Chartered Accountants and Consultants** (أحمد سيد أحمد محاسبون قانونيون ومستشارون), Giza, Egypt.
Owner: Ahmed Sayed, Founder & Managing Partner.

## How the site is built
- `src/` is the source: Python + Jinja2.
  - `build.py`: routes, rendering, and the 404 page.
  - `extras.py`: `sitemap.xml`, `robots.txt`, and `CNAME`.
  - `check_links.py`: fails the build on broken internal links.
  - `search.py`: the search pages and the search index. See "Site search" below.
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
  rm -rf dist && mkdir dist && cp -r public/. dist/ && python src/build.py && python src/extras.py && python src/check_links.py
  ```
- Deploy: GitHub Actions (`.github/workflows/deploy.yml`) builds and publishes to GitHub Pages on every push to `main`. Never commit `dist/`.
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
- `image` (optional, all three): leave it out for now. Images come in a later phase; without it everything looks as today.

## Homepage hexagon
- Shows the 8 items most recently **added** to the site, from Insights, Briefing and ASA NEXT together, newest first (sorted by `added`, then `added_at`). 6 seconds per item.
- Built by `brief_slots()` in `src/build.py`; the count is `BRIEF_COUNT`. Briefing items use `short_en/ar` as the headline.
- Controls: previous / next arrows (mirrored in Arabic), progress bars, swipe on touch screens, left/right keys when the hexagon has focus. It pauses on hover and keyboard focus. The intro animation plays once per browser session. With reduced motion it does not rotate.

## Insights (articles)
- Metadata in `src/articles_meta.py` → `ARTICLES`; text in `articles_en.py` / `articles_ar.py` → `ART[slug]`.
- Each article has `added` (see above) and `category`: a key of `CATEGORIES` in `articles_meta.py`.
- `CATEGORIES` is the one place for Insights categories (EN + AR names). The tabs on `/insights/` are built from it automatically: a tab appears only when at least one article uses that category; order is All, then categories by number of articles (most first).
- **When a new article needs a category that does not exist yet, add it to `CATEGORIES` in both languages.** Its tab then appears automatically. Never hard-code tabs in the template.

## Site search
- Header search button on every page (EN "Search" / AR «بحث»), shortcuts "/" and Ctrl+K, and the search pages `/search/` and `/ar/search/` (`?q=`). The 404 page has a search box.
- The index is built automatically at build time by `src/search.py` from the site data (articles, Briefing, ASA NEXT, services and main pages): `dist/assets/search/en.json` and `ar.json`. Nothing to update by hand when content is added.
- Matching and ranking run in the browser (`public/assets/js/search.js`): Arabic normalisation, «ال» ignored, prefix matching, light typo tolerance for English. No external services, no tracking, no CDN.
- If a new section or main page is added, add it to `build_index()` in `src/search.py` (and its group label in `content_en.py` / `content_ar.py` → `T['search']['groups']`).

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
- In Arabic, attach «و» to the English word that follows, with no space: «ACCA وCPA وSOCPA», «Excel 2021 وMicrosoft 365». A separate «و» can end up alone at the end of a line.
