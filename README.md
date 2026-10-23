# tokensandmedals.com

Static site for Tokens and Medals, a resource library for collectors of
tokens, medals and so-called dollars, with Colorado pages and a
catalog-number decoder.

Deployed with Cloudflare Pages straight from this repo. No build step on the
server: run `python3 build.py` locally and commit the output.

- `data/library.json` – the library entries, grouped into shelves. Edit here,
  not in `index.html`. Each entry has a `checked` date (last time the link was
  verified) and `tags` that drive the subject chips.
- `data/references.json` – the catalog references the decoder knows.
- `content/*.html` – page bodies; the first line is a JSON comment with the
  page's path, title, description and breadcrumbs. `content/colorado/` holds
  the Colorado essays; sources are listed at the foot of each.
- `build.py` – renders `index.html`, `colorado/`, `decoder/` and `sitemap.xml`.
- `search.js` – filters the pre-rendered library (works without it).
- `decoder.js` – the lookup box on `/decoder/` (the table works without it).
- `styles.css` – all styling.
- `_headers` – security headers for Pages; the `*.pages.dev` hostname is noindexed.

Cloudflare Pages settings: framework preset **None**, build command empty,
output directory `/`.

Editorial rules: no marketplace or dealer wording, no sponsored or affiliate
links, link to catalog data rather than reproducing it, and every fact on the
Colorado pages carries a source.
