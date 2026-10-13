# tokensandmedals.com

Static site for Tokens and Medals, a resource library for collectors of
tokens, medals and so-called dollars. It will grow into a marketplace.

Deployed with Cloudflare Pages straight from this repo. No build step.

- `index.html` – the page. Resource entries live in the `<section id="library">` lists.
- `styles.css` – all styling.
- `_headers` – security headers for Pages; the `*.pages.dev` hostname is noindexed.
- `favicon.svg`, `og-image.png` – icon and link preview.

Cloudflare Pages settings: framework preset **None**, build command empty,
output directory `/`.
