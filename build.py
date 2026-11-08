#!/usr/bin/env python3
"""Generate the Tokens and Medals site from data/ and content/.

Run `python3 build.py` and commit the output. Cloudflare Pages deploys the
committed files; there is no build step on the server.

Inputs
  data/library.json      resource entries, grouped into shelves
  data/references.json   catalog references for the decoder
  data/price-guide/*.json price-guide estimates (formula output only; produced in the
                         private analysis folder by tools/export_public_guides.py)
  content/*.html         page bodies; the first line is a JSON comment with
                         path, title, description (and optional nav key)
Outputs
  index.html, <path>/index.html for every content page, sitemap.xml
"""
import hashlib
import html
import json
import os
import re
import sys

# stylesheet version from its content: browsers may keep /styles.css for hours (Cloudflare max-age), so a
# changed stylesheet gets a new URL and loads at once
CSS_V = hashlib.sha256(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.css"), "rb").read()).hexdigest()[:10]
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
    ("/price-guide/", "Price guide", "guide"),
    ("/decoder/", "Decoder", "decoder"),
    ("/colorado/", "Colorado", "colorado"),
    ("/about/", "About", "about"),
]


def shell(*, path, title, description, body, nav="", scripts="", og_title=None, breadcrumbs=None, ld=None):
    url = SITE + path
    full_title = "Tokens and Medals" if path == "/" else f"{title} · Tokens and Medals"
    nav_html = "\n".join(
        f'      <a href="{href}"{" aria-current=\"page\"" if key == nav else ""}>{label}</a>'
        for href, label, key in NAV
    )
    footer_nav = "\n".join(f'      <a href="{href}">{label}</a>' for href, label, key in NAV)
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
  <link rel="stylesheet" href="/styles.css?v={CSS_V}">{ld_html}
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
    <nav class="footer-nav" aria-label="Site sections">
{footer_nav}
    </nav>
    <p>Tokens and Medals &middot; published by <a href="https://pueblointernetpublishing.com/" rel="noopener">Pueblo Internet Publishing LLC</a>, Pueblo, Colorado</p>
    <p>&copy; <span id="year">{date.today().year}</span> Pueblo Internet Publishing LLC &middot; linked sites belong to their owners</p>
    <p>AI assistance was used in building this site; mistakes are possible. <a href="mailto:brian@puebloip.com?subject=Tokens%20and%20Medals%20correction">Tell us</a></p>
  </footer>

  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>{scripts}
</body>
</html>
"""


# ---------------------------------------------------------------- library

def domain_of(url):
    """Short label for the card: the host, plus the path only when it is short."""
    full = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    return full if len(full) <= 36 else full.split("/")[0]


def render_entry(e):
    # "|" separates tags because a tag can be several words ("civil war tokens")
    tags = "|".join(sorted(set(e.get("tags", []))))
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
    # the search box sits in the home-page hero (content/index.html); search.js finds it by id
    return f"""    <section id="library" class="library">
      <div class="library-head">
        <h2>The library</h2>
        <p class="count"><span id="shown">{count}</span> of {count} entries</p>
      </div>
      <details class="subjects">
        <summary>Filter by subject</summary>
        <div class="chips" aria-label="Filter by subject">{chips}</div>
      </details>
      <p class="no-match" id="no-match" hidden>Nothing in the library matches that. Try a broader word, or <a href="mailto:brian@puebloip.com?subject=Tokens%20and%20Medals">tell us what is missing</a>.</p>
{chr(10).join(shelves)}
      <p class="suggest">Know a resource that belongs here? <a href="mailto:brian@puebloip.com?subject=Tokens%20and%20Medals">Send it along</a>.</p>
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


# ---------------------------------------------------------------- price guide

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


def month_name(ym):
    y, m = ym.split("-")[:2]
    return f"{MONTHS[int(m) - 1]} {y}"


def money(v):
    return f"${v:,}"


def est_cell(est, lo, hi):
    return (f'<span class="est">{money(est)}</span>'
            f'<span class="rng">{money(lo)}&ndash;{money(hi)}</span>')


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def render_scd(doc):
    out = []
    for p in doc["pieces"]:
        finish = f" &middot; {esc(p['finish'])}" if p["finish"] else ""
        rows = "".join(
            f'<tr><th scope="row">{esc(g["grade"])}</th><td>{est_cell(*g["pcgs"])}</td><td>{est_cell(*g["ngc"])}</td></tr>'
            for g in p["grades"])
        anchor = slug(f"hk-{p['hk']}-{p['metal']}-{p['finish']}")
        formula = p.get("basis") == "formula"
        keys = f"hk{p['hk']} {p['event']} {p['year']} {p['metal']} {p['finish']}" + (" formula only" if formula else "")
        tag = f' <span class="basis-tag">{scd_tag(p)}</span>' if formula else ""
        out.append(f"""        <div class="g-piece{' formula' if formula else ''}" id="{anchor}" data-g data-basis="{'formula' if formula else 'sales'}" data-k="{esc(keys.lower())}">
          <h3><span class="hk">HK-{esc(p["hk"])}</span> {esc(p["event"])}, {p["year"]} &middot; {esc(p["metal"])}{finish}{tag}</h3>
          <div class="table-wrap"><table class="gtable scd">
            <thead><tr><th scope="col">Grade</th><th scope="col">PCGS slab</th><th scope="col">NGC slab</th></tr></thead>
            <tbody>{rows}</tbody>
          </table></div>
        </div>""")
    return "\n".join(out)


CARR_PARTS = (
    ("Over-strikes", "Fantasy-date over-strikes",
     "Grouped by the design on the maker's over-strike list; each row is a fantasy date, with the privy or set where there is one."),
    ("Catalogue", "Catalogue issues",
     "Grouped by the sections of the Moonlight Mint catalogue. A catalogue number appears where the pieces we studied could be pinned to one; otherwise the row covers the issue as a whole."),
    ("Not in the maker's catalogue", "Other Carr pieces", "Carr pieces that are not in the online catalogue."),
)
CARR_GRADES = (("70", "70 slab"), ("69 or lower", "69 or lower"), ("ungraded", "Raw"))


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def scd_tag(p):
    """Says what we have for the piece and, where it informs the figure, for its HK number and event."""
    t, e = p.get("type_sales", 0), p.get("event_sales", 0)
    tail = (f" &middot; same HK number, other metals: {plural(t, 'sale')}" if t else
            f" &middot; its event: {plural(e, 'sale')}" if e else " &middot; its event: no sales either")
    return "formula only &middot; this piece: no sales in our records" + tail


CARR_KIND = {"issue": ("its issue", "its issue"), "series": ("same design, other years", "same design in other years"),
             "design": ("same design, other dates", "same design at other dates"), "section": ("same catalogue page", "its catalogue page")}


CARR_FROM = {"issue": "its issue", "series": "the same design in other years", "design": "the same design at other dates",
             "section": "its catalogue page"}


# the formula's candidate variables in words; which are used / were only tried comes from the fit itself,
# so the method text stays true when a monthly refit keeps a different set
CARR_VAR_TEXT = {"metal": "the metal a piece is struck in", "mintage": "the maker's published mintage",
                 "grader": "the grading service", "proof": "proof finish", "issue_price": "the maker's issue price",
                 "part": "whether a piece is an over-strike or a catalogue issue", "group_trend": "a separate price trend for each issue",
                 "anacs_pop70": "how many pieces ANACS has graded 70", "anacs_share70": "what share of ANACS-graded pieces reached 70",
                 "top_pop": "whether a piece sits at the top ANACS grade with only a few there",
                 "anacs_share": "what share of the mintage ANACS has graded", "issue_age": "the years since a piece was issued",
                 "format": "how a piece sold", "lot_size": "how many pieces were in the lot"}


def carr_vars(keys, cf, tried=False):
    words = []
    for k in keys:
        w = CARR_VAR_TEXT.get(k, k.replace("_", " "))
        if k == "mintage" and not tried and cf.get("mintage_halving"):
            h = cf["mintage_halving"]
            w += f" (each halving of the mintage {'adds' if h >= 1 else 'takes off'} about {abs(h - 1) * 100:.0f}%)"
        words.append(w)
    s = ", ".join(words[:-1]) + (" and " if len(words) > 1 else "") + (words[-1] if words else "")
    return (s[:1].upper() + s[1:]) if tried else (s or "nothing else")


def carr_tag(L):
    n, k = L.get("group_sales", 0), L.get("group_kind", "issue")
    with_, none_ = CARR_KIND.get(k, CARR_KIND["issue"])
    many = "these pieces" if L.get("n", 1) > 1 else "this piece"
    if L.get("sib") and n:                     # priced from those sales, not from the formula alone
        return f"from {plural(n, 'sale')} of {CARR_FROM.get(k, 'its issue')} and the formula &middot; {many}: no sales in our records"
    tail = f" &middot; {with_}: {plural(n, 'sale')}" if n else f" &middot; {none_}: no sales either"
    return f"formula only &middot; {many}: no sales in our records" + tail


def render_carr(doc):
    out = []
    for part, title, note in CARR_PARTS:
        lines = [L for L in doc["lines"] if L["part"] == part]
        groups = {}
        for L in lines:
            links = L.get("links") or []

            def linked(lab, url, code=False):
                inner = f"<code>{esc(lab)}</code>" if code else esc(lab)
                return f'<a href="{esc(url)}" rel="noopener">{inner}</a>' if url else inner
            if part == "Catalogue":
                head, _, issue = L["group"].partition(" \u00b7 ")
                if L["item"]:      # each catalogue number links to its row in the maker's catalogue
                    pairs = ([(L["item"], linked(L["item"], links[0][1], True))] if len(links) == 1
                             else [(lab, linked(lab, url, True)) for lab, url in links] if links
                             else [(x, f"<code>{esc(x)}</code>") for x in L["item"].split(", ")])
                    st = dict(L.get("store") or [])   # and, where matched, to that product on the maker's store
                    nums = [h + (f' <a class="g-store" href="{esc(st[n])}" rel="noopener" '
                                 f'aria-label="{esc(n)} on the maker\'s store">store</a>' if st.get(n) else "")
                            for n, h in pairs]
                    label = f"{esc(issue)} &middot; " + ", ".join(nums)
                else:
                    url = links[0][1] if links else None
                    label = linked(issue, url) + ' <span class="muted">(number not stated)</span>'
            elif part == "Over-strikes":
                head = L["group"]      # each fantasy date links to the maker's write-up
                label = ", ".join(linked(lab, url) for lab, url in links) if links else esc(L["item"])
            else:
                head, label = "", esc(L["group"])
            groups.setdefault(head, []).append((label, L))
        blocks = []
        for head, rows in groups.items():
            trs = []
            for label, L in rows:
                by = {g["grade"]: g for g in L["grades"]}
                def td(k, h):
                    if k not in by:
                        return f'<td class="na" data-label="{esc(h)}">&mdash;</td>'
                    g = by[k]
                    dp = (f' data-p="{g["p"][0]},{g["p"][1]},{g["p"][2]}"' if g.get("p")           # metal + premium (live)
                          else f' data-f="{g["f"][0]},{g["f"][1]},{g["f"][2]}"' if g.get("f") else "")  # floored at live melt
                    if dp and g.get("ip"):                     # live re-pricing never goes under the maker's issue price
                        dp += f' data-ip="{g["ip"]}"'
                    return f'<td data-label="{esc(h)}"{dp}>{est_cell(g["estimate"], g["low"], g["high"])}</td>'
                cells = "".join(td(k, h) for k, h in CARR_GRADES)
                metal = ((f' data-ag="{L["oz_ag"]}"' if L.get("oz_ag") else "") + (f' data-au="{L["oz_au"]}"' if L.get("oz_au") else "")
                         + (f' data-pt="{L["oz_pt"]}"' if L.get("oz_pt") else "") + (f' data-pd="{L["oz_pd"]}"' if L.get("oz_pd") else ""))
                formula = L.get("basis") == "formula"
                keys = f"{head} {L['group']} {L['item']}".lower() + (" formula only" if formula else "")
                ipr = [g["ip"] for g in L["grades"] if g.get("ipr")]
                ip_note = f"floor: the maker&rsquo;s issue price, ${min(ipr):,.2f}".replace(".00", "") if ipr else ""
                tag = (f' <span class="basis-tag">{carr_tag(L)}{" &middot; " + ip_note if ip_note else ""}</span>' if formula
                       else f' <span class="basis-tag">{ip_note}</span>' if ip_note else "")
                trs.append(f'<tr{" class=\"formula\"" if formula else ""} data-g data-basis="{"formula" if formula else "sales"}"{metal} data-k="{esc(keys)}"><th scope="row">{label}{tag}</th>{cells}</tr>')
            heads = "".join(f'<th scope="col">{esc(h)}</th>' for _, h in CARR_GRADES)
            src = doc.get("section_links", {}).get(head if part == "Catalogue" else ("Over-strikes" if part == "Over-strikes" else ""), {})
            srcs = " &middot; ".join(f'<a href="{esc(src[k])}" rel="noopener">{lab}</a>' for k, lab in (("catalogue", "maker's catalogue"), ("store", "maker's store")) if src.get(k))
            h3 = (f"<h3>{esc(head)}</h3>" if head else "") + (f'\n            <p class="g-src">{srcs}</p>' if srcs and part == "Catalogue" else "")
            blocks.append(f"""          <div class="g-group" data-gg>
            {h3}
            <div class="table-wrap"><table class="gtable carr">
              <thead><tr><th scope="col">Piece</th>{heads}</tr></thead>
              <tbody>{"".join(trs)}</tbody>
            </table></div>
          </div>""")
        psrc = doc.get("section_links", {}).get("Over-strikes", {}) if part == "Over-strikes" else {}
        plinks = " &middot; ".join(f'<a href="{esc(psrc[k])}" rel="noopener">{lab}</a>' for k, lab in (("catalogue", "maker's over-strike list"), ("store", "maker's store")) if psrc.get(k))
        out.append(f"""        <section class="g-part" data-gp id="{slug(title)}">
          <h2>{esc(title)}</h2>
          <p class="muted">{esc(note)}</p>{f'{chr(10)}          <p class="g-src">{plinks}</p>' if plinks else ""}
{chr(10).join(blocks)}
        </section>""")
    return "\n".join(out)


def guide_placeholders():
    scd = json.loads(read("data/price-guide/scd.json"))
    carr = json.loads(read("data/price-guide/carr.json"))
    pct = lambda x: f"{round(x * 100)}%"
    sf, cf = scd["factors"], carr["factors"]
    ca = carr["accuracy"]
    return {
        "{{SCD_GUIDE}}": render_scd(scd),
        "{{SCD_COUNT}}": str(len(scd["pieces"])),
        "{{SCD_SALES_COUNT}}": str(sum(1 for p in scd["pieces"] if p.get("basis") != "formula")),
        "{{SCD_FORMULA_COUNT}}": str(sum(1 for p in scd["pieces"] if p.get("basis") == "formula")),
        "{{SCD_FORMULA_TESTED}}": str(scd["accuracy"]["formula_tested"]),
        "{{SCD_FORMULA_MISS}}": pct(scd["accuracy"]["formula_median_miss"]),
        "{{SCD_FORMULA_INSIDE}}": pct(scd["accuracy"]["formula_inside"]),
        "{{SCD_THROUGH}}": month_name(scd["sales_through"]),
        "{{SCD_GENERATED}}": scd["generated"],
        "{{SCD_MISS}}": pct(scd["accuracy"]["median_miss"]),
        "{{SCD_INSIDE}}": pct(scd["accuracy"]["inside_range"]),
        "{{SCD_NEWEST_INSIDE}}": pct(scd["accuracy"]["newest_inside_range"]),
        "{{SCD_NEWEST_SINCE}}": scd["accuracy"]["newest_since"][:4],
        "{{SCD_FLOOR}}": pct(scd["accuracy"]["floor"]),
        "{{SCD_WEEKLY}}": pct(1 - scd["venue_factors"]["weekly online auction"]),
        "{{SCD_EBAY}}": pct(1 - scd["venue_factors"]["eBay"]),
        "{{CARR_GUIDE}}": render_carr(carr),
        "{{CARR_COUNT}}": str(sum(L.get("n", 1) for L in carr["lines"])),
        "{{CARR_LINES}}": str(len(carr["lines"])),
        "{{CARR_SALES_COUNT}}": str(sum(L.get("n", 1) for L in carr["lines"] if L.get("basis") != "formula")),
        "{{CARR_FORMULA_COUNT}}": str(sum(L.get("n", 1) for L in carr["lines"] if L.get("basis") == "formula")),
        "{{CARR_FORMULA_TESTED}}": str(carr["accuracy"]["formula_tested"]),
        "{{CARR_FORMULA_MISS}}": pct(carr["accuracy"]["formula_median_miss"]),
        "{{CARR_FORMULA_INSIDE}}": pct(carr["accuracy"]["formula_inside"]),
        "{{CARR_THROUGH}}": month_name(carr["sales_through"]),
        "{{CARR_THROUGH_YEAR}}": carr["sales_through"][:4],
        "{{CARR_GENERATED}}": carr["generated"],
        "{{CARR_MISS}}": pct(carr["accuracy"]["median_miss"]),
        "{{CARR_NEWEST_INSIDE}}": pct(carr["accuracy"]["newest_inside_range"]),
        # the formula's own factors, so the method text always matches this edition
        "{{SCD_GRADE_PT}}": pct(sf["grade_point"] - 1),
        "{{SCD_YEAR}}": pct(sf["year"] - 1),
        "{{SCD_NGC}}": pct(1 - sf["ngc"]),
        "{{SCD_SEASON}}": pct(1 - sf["spring_summer"]),
        "{{SCD_SILVER}}": f"{sf['silver']:.1f}",
        "{{SCD_GOLD}}": f"{sf['gold']:.1f}",
        "{{SCD_RARITY}}": pct(1 - sf["double_appearances"]),
        "{{CARR_70}}": pct(cf["slab70"] - 1),
        "{{CARR_69}}": pct(cf["slab69"] - 1),
        "{{CARR_MONTH}}": f"{(1 - cf['month']) * 100:.1f}%",
        "{{CARR_SILVER}}": f"{cf['silver']:.1f}",
        "{{CARR_SOFT}}": pct(1 - cf["newest_actual_over_estimate"]),
        "{{CARR_SILVER_SPOT}}": f"${cf['silver_spot']:.2f}",
        "{{CARR_GOLD_SPOT}}": f"${cf.get('gold_spot', 0):,.2f}",
        "{{CARR_METAL_PIECES}}": str(sum(L.get("n", 1) for L in carr["lines"] if L.get("oz_ag") or L.get("oz_au") or L.get("oz_pt") or L.get("oz_pd"))),
        "{{CARR_PT_SPOT}}": f"${cf.get('platinum_spot', 0):,.2f}",
        "{{CARR_PD_SPOT}}": f"${cf.get('palladium_spot', 0):,.2f}",
        "{{CARR_PT_RAW}}": f"{cf.get('platinum_spot', 0):.2f}",
        "{{CARR_PD_RAW}}": f"{cf.get('palladium_spot', 0):.2f}",
        "{{CARR_IP_RESALES}}": str(ca.get("ip_resales", "")),
        "{{CARR_IP_BELOW}}": f"{ca.get('ip_below') or 0:.0%}",
        "{{CARR_IP_LINES}}": str(ca.get("ip_lines_raised", "")),
        "{{CARR_VARS_USED}}": carr_vars(cf.get("vars_used", []), cf),
        "{{CARR_VARS_TRIED}}": carr_vars(cf.get("vars_tried", []), cf, tried=True),
        "{{CARR_SIB_SALES}}": str(ca.get("sib_tested_sales", "")),
        "{{CARR_SIB_PIECES}}": str(ca.get("sib_tested_pieces", "")),
        "{{CARR_SIB_MISS}}": f"{ca.get('sib_median_miss', 0) * 100:.0f}%",
        "{{CARR_SIB_PLAIN}}": f"{ca.get('sib_plain_miss', 0) * 100:.0f}%",
        "{{CARR_PGM_SOURCE}}": ("the Hyperliquid perpetual futures price" if cf.get("pgm_source") == "Hyperliquid" else "the open daily dataset's price"),
        "{{CARR_SPOT_DATE}}": cf["spot_date"],
        "{{CARR_LOT5}}": f"{cf['lot5']:.1f}",
        "{{CARR_AUCTION}}": pct(1 - cf["auction"]),
    }


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
        **guide_placeholders(),
    }

    names = sorted(os.listdir(os.path.join(ROOT, "content")))
    for sub in ("colorado", "price-guide"):
        names += [os.path.join(sub, n) for n in sorted(os.listdir(os.path.join(ROOT, "content", sub)))]
    for name in names:
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
