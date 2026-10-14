# asaegypt.com — instructions for Claude

Website of **ASA Chartered Accountants and Consultants** (أحمد سيد أحمد محاسبون قانونيون ومستشارون), Giza, Egypt.
Owner: Ahmed Sayed, Founder & Managing Partner.

## How the site is built
- `src/` is the source: Python + Jinja2.
  - `build.py`: routes, rendering, and the 404 page.
  - `extras.py`: `sitemap.xml`, `robots.txt`, and `CNAME`.
  - `check_links.py`: fails the build on broken internal links.
- `public/` holds static files (`assets/` CSS/JS/fonts/images, `CNAME`). They are copied into `dist/` before the build.
- Content lives in:
  - `content_en.py` / `content_ar.py`: header/footer strings, services, home page.
  - `pages_en.py` / `pages_ar.py`: inner pages.
  - `articles_meta.py` + `articles_en.py` / `articles_ar.py`: Insights.
- Templates are in `src/templates/`.
- English lives at `/` and Arabic at `/ar/`. **Every change must be made in both languages.**
- Build locally:
  ```
  rm -rf dist && mkdir dist && cp -r public/. dist/ && python src/build.py && python src/extras.py && python src/check_links.py
  ```
- Deploy: GitHub Actions (`.github/workflows/deploy.yml`) builds and publishes to GitHub Pages on every push to `main`. Never commit `dist/`.

## Workflow
- Work on a `claude/...` branch and open a Pull Request. Ahmed approves by merging.
- Never push directly to `main` unless Ahmed explicitly asks in the session.
- Before opening a PR:
  - Run the full build and link check.
  - Make sure both languages render.
- PR description: a short plain-language summary of what changed, in English.

## Non-negotiable content rules
1. **No names or photos of individual people anywhere on the site.** The team is described collectively.
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

## Writing style
- English: clear, professional, Big-4 tone, no hype.
- Arabic: eloquent Modern Standard Arabic (فصحى), not a literal translation of the English.
- Write mixed Latin terms with spaces, e.g. «ACCA و CPA و SOCPA» (avoids bidi issues).
