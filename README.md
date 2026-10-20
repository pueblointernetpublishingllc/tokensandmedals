# tokensandmedals.com

Static site for Tokens and Medals, a resource library for collectors of
tokens, medals and so-called dollars.

Deployed with Cloudflare Pages straight from this repo. No build step.

- `index.html` – the page. Resource entries live in the `<section id="library">` lists.
- `styles.css` – all styling.
- `_headers` – security headers for Pages; the `*.pages.dev` hostname is noindexed.
- `favicon.svg`, `og-image.png` – icon and link preview.

Cloudflare Pages settings: framework preset **None**, build command empty,
output directory `/`.


## Holding page (2026-10-20)

The site was replaced by a neutral holding page while Pueblo Internet Publishing LLC is not yet licensed to conduct business. The full site is preserved on branch `archive/pre-holding-20261020` and tag `pre-holding-20261020`; restore with `git checkout archive/pre-holding-20261020 -- .` (keeping this note) and push.
