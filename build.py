#!/usr/bin/env python3
"""Generate the Tokens and Medals site from data/ and content/.

Run `python3 build.py` and commit the output. Cloudflare Pages deploys the
committed files; there is no build step on the server.

Inputs
  data/library.json      resource entries, grouped into shelves
  data/references.json   catalog references for the decoder
  content/*.html         page bodies; the first line is a JSON comment with
                         path, title, description (and optional nav key)
Outputs
  index.html, <path>/index.html for every content page, sitemap.xml
"""
import html
import json
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://tokensandmedals.com"
TODAY = date.today().isoformat()


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def esc(s):
    return html.escape(s, quote=True)


NAV = [
    ("/#library", "Library", "library"),
    ("/colorado/", "Colorado", "colorado"),
    ("/decoder/", "Decoder", "decoder"),
    ("/#about", "About", "about"),
]


def shell(*, path, title, description, body, nav="", scripts="", og_title=None, breadcrumbs=None, ld=None):
    url = SITE + path
    full_title = "Tokens and Medals" if path == "/" else f"{title} · Tokens and Medals"
    nav_html = "\n".join(
        f'      <a href="{href}"{" aria-current=\"page\"" if key == nav else ""}>{label}</a>'
        for href, label, key in NAV
    )
    crumbs = ""
    if breadcrumbs:
        items = "".join(
            f'<li><a href="{esc(h)}">{esc(t)}</a></li>' if h else f'<li aria-current="page">{esc(t)}</li>'
            for t, h in breadcrumbs
        )
        crumbs = f'\n    <nav class="crumbs" aria-label="Breadcrumb"><ol>{items}</ol></nav>'
    ld_html = ""
    if ld:
        ld_html = '\n  <script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(full_title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/favicon-32x32.png" sizes="32x32" type="image/png">
  <link rel="icon" href="/favicon-16x16.png" sizes="16x16" type="image/png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Tokens and Medals">
  <meta property="og:title" content="{esc(og_title or full_title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Alegreya+Sans:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/styles.css">{ld_html}
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>

  <header class="masthead">
    <a class="wordmark" href="/">Tokens <span class="amp">&amp;</span> Medals</a>
    <nav class="menu" aria-label="Site">
{nav_html}
    </nav>
  </header>{crumbs}

  <main id="main">
{body}
  </main>

  <footer class="colophon">
    <p>Tokens and Medals is a project of <a href="https://pueblointernetpublishing.com/" rel="noopener">Pueblo Internet Publishing LLC</a>, Pueblo, Colorado.</p>
    <p>This site and its contents are &copy; <span id="year">{date.today().year}</span> <a href="https://pueblointernetpublishing.com/" rel="noopener">Pueblo Internet Publishing LLC</a>. All rights reserved. Linked sites belong to their own owners and are not affiliated with us.</p>
    <p>AI assistance was used in researching and building this site. Every fact was checked against the sources cited; the mistakes are ours.</p>
  </footer>

  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>{scripts}
</body>
</html>
"""


# ---------------------------------------------------------------- library

def domain_of(url):
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


def render_entry(e):
    tags = " ".join(sorted(set(e.get("tags", []))))
    rel = "noopener"
    note = ""
    if e.get("note"):
        note = f'\n            <span class="note">{esc(e["note"])}</span>'
    checked = e.get("checked", "")
    return f"""          <li data-tags="{esc(tags)}" data-checked="{esc(checked)}">
            <a href="{esc(e["url"])}" rel="{rel}">{esc(e["name"])}</a>
            <p>{e["desc"]}</p>
            <span class="domain">{esc(domain_of(e["url"]))}</span>{note}
          </li>"""


def render_library(lib):
    all_tags = {}
    for shelf in lib["shelves"]:
        for e in shelf["entries"]:
            for t in e.get("tags", []):
                all_tags[t] = all_tags.get(t, 0) + 1
    chips = "".join(
        f'<button type="button" class="chip" data-tag="{esc(t)}" aria-pressed="false">{esc(t)}</button>'
        for t in sorted(all_tags)
    )
    shelves = []
    for shelf in lib["shelves"]:
        entries = "\n".join(render_entry(e) for e in shelf["entries"])
        blurb = f'\n          <p class="shelf-note">{shelf["note"]}</p>' if shelf.get("note") else ""
        shelves.append(f"""      <div class="shelf" id="{esc(shelf["id"])}">
        <div class="shelf-head">
          <h3>{esc(shelf["title"])}</h3>{blurb}
        </div>
        <ul class="entries">
{entries}
        </ul>
      </div>""")
    count = sum(len(s["entries"]) for s in lib["shelves"])
    return f"""    <section id="library" class="library">
      <div class="library-head">
        <h2>The library</h2>
        <p class="count"><span id="shown">{count}</span> of {count} entries</p>
      </div>
      <form class="finder" role="search" onsubmit="return false">
        <label for="q" class="visually-hidden">Search the library</label>
        <input id="q" type="search" placeholder="Search the library: a society, a catalog, a kind of token…" autocomplete="off">
        <div class="chips" aria-label="Filter by subject">{chips}</div>
      </form>
      <p class="no-match" id="no-match" hidden>Nothing on the shelves matches that. Try a broader word, or <a href="mailto:brian@puebloip.com?subject=Tokens%20and%20Medals">tell us what is missing</a>.</p>
{chr(10).join(shelves)}
      <p class="suggest">Know a resource that belongs here? <a href="mailto:brian@puebloip.com?subject=Tokens%20and%20Medals">Send it along</a>. Every link is checked by hand; the date on each card is the last time we looked.</p>
    </section>"""


# ---------------------------------------------------------------- decoder

def render_references(refs):
    rows = []
    for r in refs:
        abbr = ", ".join(f"<code>{esc(a)}</code>" for a in r["abbr"])
        lookup = (
            f'<a href="{esc(r["lookup_url"])}" rel="noopener">{esc(r["lookup_label"])}</a>'
            if r.get("lookup_url") else "<span class=\"muted\">Printed only</span>"
        )
        find = ""
        if r.get("find_url"):
            find = f'<a href="{esc(r["find_url"])}" rel="noopener">{r["find_label"]}</a>'
        if r.get("find_note"):
            find += ("<br>" if find else "") + f'<span class="cite">{r["find_note"]}</span>'
        rows.append(f"""        <tr id="ref-{esc(r["id"])}">
          <th scope="row">{abbr}</th>
          <td><strong>{esc(r["title"])}</strong><br><span class="cite">{esc(r["citation"])}</span></td>
          <td>{r["covers"]}<br><span class="example">as in <code>{esc(r["example"])}</code></span></td>
          <td>{lookup}</td>
          <td>{find}</td>
        </tr>""")
    return "\n".join(rows)


# ---------------------------------------------------------------- pages

def parse_content(raw):
    m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        raise SystemExit("content file needs a leading JSON comment")
    meta = json.loads(m.group(1))
    return meta, raw[m.end():]


def main():
    lib = json.loads(read("data/library.json"))
    refs = json.loads(read("data/references.json"))
    pages = []  # (path, lastmod)

    placeholders = {
        "{{LIBRARY}}": render_library(lib),
        "{{REFERENCE_ROWS}}": render_references(refs),
        "{{REFERENCES_JSON}}": json.dumps(refs, ensure_ascii=False),
        "{{LIBRARY_COUNT}}": str(sum(len(s["entries"]) for s in lib["shelves"])),
    }

    for name in sorted(os.listdir(os.path.join(ROOT, "content"))) + [
        os.path.join("colorado", n) for n in sorted(os.listdir(os.path.join(ROOT, "content", "colorado")))
    ]:
        if not name.endswith(".html"):
            continue
        meta, body = parse_content(read(os.path.join("content", name)))
        for k, v in placeholders.items():
            body = body.replace(k, v)
        # Wide tables scroll sideways on phones instead of pushing the page out
        body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
        scripts = "".join(f'\n  <script src="{s}" defer></script>' for s in meta.get("scripts", []))
        out = shell(
            path=meta["path"], title=meta["title"], description=meta["description"], body=body,
            nav=meta.get("nav", ""), scripts=scripts, og_title=meta.get("og_title"),
            breadcrumbs=[tuple(b) for b in meta.get("breadcrumbs", [])] or None, ld=meta.get("ld"),
        )
        target = "index.html" if meta["path"] == "/" else meta["path"].strip("/") + "/index.html"
        write(target, out)
        pages.append((meta["path"], meta.get("updated", TODAY), meta.get("priority", "0.7")))

    urls = "\n".join(
        f"  <url><loc>{SITE}{p}</loc><lastmod>{d}</lastmod><changefreq>monthly</changefreq><priority>{pr}</priority></url>"
        for p, d, pr in sorted(pages)
    )
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')
    print(f"built {len(pages)} pages, {placeholders['{{LIBRARY_COUNT}}']} library entries, {len(refs)} references")


if __name__ == "__main__":
    main()
