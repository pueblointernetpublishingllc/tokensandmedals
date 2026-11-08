"""Per-piece pages for the price guides (2026-11-08, SEO): one page per so-called dollar HK number and one per
Daniel Carr over-strike design / catalogue issue / other piece, so a search for a specific piece lands on a page
about that piece. Every figure, label, floor and live-metal hook comes from the same renderers as the full guides
(build.render_scd / build.render_carr on the piece's own rows), so the pages can never disagree with the guides."""
import re

SCD_GUIDE = "/price-guide/so-called-dollars/"
CARR_GUIDE = "/price-guide/daniel-carr/"
CARR_PART_SLUG = {"Over-strikes": "over-strikes", "Catalogue": "catalogue", "Not in the maker's catalogue": "other"}
CARR_PART_NAME = {"Over-strikes": "Fantasy-date over-strikes", "Catalogue": "Catalogue issues", "Not in the maker's catalogue": "Other Carr pieces"}


def slug(s, n=70):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    if len(s) > n:
        s = s[:n].rsplit("-", 1)[0]
    return s or "piece"


def tidy(s):
    """An issue name without the maker's remarks: bracketed notes ('[SOLD OUT]', '(Distributed by ...)', but a
    bracketed year such as '[2023]' stays as 2023), and any description the catalogue runs on after the name
    ('... Restrikes \u201c1850\u201d Early-period Mormon $5 gold half eagles were struck ...', '... NOTE: ...')."""
    t = re.sub(r"\[((?:19|20)\d\d)\]", r"\1", s)
    t = re.split(r"\s+NOTE:|\s+\(SOLD OUT\)", t)[0]
    m = re.search(r"\u201d\s+(?=[A-Z][a-z]+[- ][a-z])", t)        # closing quote, then a sentence
    if m and m.start() > 10:
        t = t[:m.start() + 1]
    t = re.sub(r"\s*\[[^\]]*\]", "", t)
    t = re.sub(r"\s*\((?:Distributed|Not government|Struck|Commissioned|Smooth Edge|Reeded|Most |Private|Invited)[^)]*\)?", "", t)
    return re.sub(r"\s+", " ", t).strip(" .") or s


def scd_url(hk):
    return f"{SCD_GUIDE}hk-{slug(hk)}/"


def carr_name(L):
    part, group = L["part"], L["group"]
    if part == "Catalogue":
        section, _, issue = group.partition(" · ")
        if issue.startswith("(no issue names"):
            return f"{section}: pieces without an issue name", section
        if issue.strip().lower() == "all issues":
            return f"{section}: all issues", section
        return tidy(issue), section
    return group, ""


def carr_urls(carr):
    """(part, group) -> page path, unique and stable for the same data."""
    out, used = {}, set()
    for L in carr["lines"]:
        k = (L["part"], L["group"])
        if k in out:
            continue
        name, section = carr_name(L)
        base = f"{CARR_GUIDE}{CARR_PART_SLUG.get(L['part'], 'other')}/{slug(name)}"
        path, i = base + "/", 2
        while path in used:
            path, i = f"{base}-{i}/", i + 1
        used.add(path)
        out[k] = path
    return out


def short(s, n):
    """At most n characters, cut at a word boundary."""
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(",;:-\u2013") + "\u2026"


def money(v):
    return f"${v:,}"


def _range(vals):
    vals = [v for v in vals if v]
    return (money(min(vals)), money(max(vals))) if vals else ("", "")


def _breadcrumb_ld(crumbs, site):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": t, **({"item": site + h} if h else {})} for i, (t, h) in enumerate(crumbs)]}


def _page(h1, lede, warning_guide, metal_note, table, related_title, related, guide_link):
    rel = ""
    if related:
        rel = (f"\n        <h2>{related_title}</h2>\n        <ul class=\"piece-related\">\n"
               + "\n".join(f'          <li><a href="{u}">{t}</a></li>' for t, u in related) + "\n        </ul>")
    return f"""    <section class="leaf">
      <article class="paper guide">
        <h1>{h1}</h1>
        <p class="lede">{lede}</p>
        <div class="guide-warning" role="note">
          <p>Our opinion of value from a tested formula: not an appraisal, not an offer to buy or sell. Real prices can land above or below the range shown. Figures in blue, marked &ldquo;formula only&rdquo;, are estimates for pieces with no sales in the records we gathered, and are much less certain. <a href="{warning_guide}#method">How we make these figures</a>.</p>
        </div>{metal_note}
{table}{rel}
        <p class="piece-back"><a href="{guide_link[1]}">{guide_link[0]}</a></p>
      </article>
    </section>"""


def scd_pages(scd, render_scd, esc, ph, site):
    by = {}
    for p in scd["pieces"]:
        by.setdefault(p["hk"], []).append(p)
    by_event = {}
    for hk, ps in by.items():
        by_event.setdefault(ps[0]["event"], []).append(hk)
    edition = ph.get("{{SCD_THROUGH}}", "")
    pages = []
    for hk, ps in by.items():
        p0 = ps[0]
        metals = sorted({p["metal"].lower() for p in ps})
        finishes = sorted({p["finish"] for p in ps if p["finish"]})
        lo, hi = _range([v for p in ps for g in p["grades"] for v in (g["pcgs"][0], g["ngc"][0])])
        grades = [g["grade"] for g in p0["grades"]]
        what = f"{p0['year']} {p0['event']} so-called dollar"
        title = f"HK-{hk} {short(p0['event'], 42)} ({p0['year']}) so-called dollar value"
        desc = (f"Estimated value of HK-{hk}, the {what} in {' and '.join(metals)}"
                + (f" ({', '.join(f.lower() for f in finishes)})" if finishes else "")
                + f", by grade in PCGS and NGC slabs ({grades[0]}–{grades[-1]}): {lo} to {hi}. Our opinion of value from a tested formula.")
        formula = all(p.get("basis") == "formula" for p in ps)
        lede = (f"HK-{esc(hk)} is a {esc(what)} in {esc(' and '.join(metals))}"
                + (f", also listed in {esc(', '.join(f.lower() for f in finishes))} finish" if finishes else "") + ". "
                + f"Our estimated values below run from {lo} to {hi} by grade, in PCGS and NGC slabs"
                + (" (formula only: we have no sales of this piece in our records)" if formula else "")
                + (f". Edition of {esc(edition)}." if edition else "."))
        metal_note = ""
        scripts = ""
        if any(p.get("oz_au") or p.get("oz_ag") for p in ps):
            metal_note = (f'\n        <p class="metal-live" id="metal-live"><strong>Gold {ph["{{SCD_GOLD_SPOT}}"]} &middot; silver {ph["{{SCD_SILVER_SPOT}}"]} an ounce</strong>: '
                          f'the Chainlink price on {ph["{{SCD_SPOT_DATE}}"]}, when this edition was built. With JavaScript on, the page updates the figures to the live price; they never go below the metal.</p>')
            scripts = '\n  <script src="/metal.js" defer></script>'
        table = render_scd({**scd, "pieces": ps})
        others = [h for h in by_event.get(p0["event"], []) if h != hk]
        related = [(f"HK-{esc(h)} &middot; {esc(str(by[h][0]['year']))} &middot; {esc(', '.join(sorted({x['metal'] for x in by[h]})))}", scd_url(h)) for h in others[:24]]
        crumbs = [("Home", "/"), ("Price guide", "/price-guide/"), ("So-called dollars", SCD_GUIDE), (f"HK-{hk}", None)]
        body = _page(f"HK-{esc(hk)} {esc(p0['event'])} so-called dollar, {esc(str(p0['year']))}", lede, SCD_GUIDE, metal_note, table,
                     f"Other {esc(p0['event'])} so-called dollars", related, ("The full so-called dollar price guide", SCD_GUIDE))
        pages.append({"path": scd_url(hk), "title": title, "description": desc, "body": body, "crumbs": crumbs,
                      "ld": _breadcrumb_ld(crumbs, site), "scripts": scripts})
    return pages


def carr_pages(carr, render_carr, urls, esc, ph, site):
    groups = {}
    for L in carr["lines"]:
        groups.setdefault((L["part"], L["group"]), []).append(L)
    edition = ph.get("{{CARR_THROUGH}}", "")
    by_part = {}
    for (part, group), Ls in groups.items():
        by_part.setdefault((part, carr_name(Ls[0])[1]), []).append((part, group))
    pages = []
    for (part, group), Ls in groups.items():
        name, section = carr_name(Ls[0])
        n = sum(L.get("n", 1) for L in Ls)
        lo, hi = _range([g["estimate"] for L in Ls for g in L["grades"]])
        formula = all(L.get("basis") == "formula" for L in Ls)
        tail = " (formula only: we have no sales of these pieces in our records)" if formula else ""
        if part == "Over-strikes":
            h1 = f"Daniel Carr {esc(name)} fantasy over-strikes"
            title = f"Daniel Carr {short(name, 42)} over-strike values"
            lede = (f"Daniel Carr's fantasy-date over-strikes of the {esc(name)} design, from the Moonlight Mint over-strike list: "
                    f"{n} {'line' if n == 1 else 'lines'} below, with our estimated value raw and in slabs, from {lo} to {hi}{tail}.")
        elif part == "Catalogue":
            h1 = f"{esc(name)} &middot; Daniel Carr / Moonlight Mint"
            title = f"{short(name, 52)}: Daniel Carr value"
            lede = (f"{esc(name)}: a Moonlight Mint issue by Daniel Carr, in the {esc(section)} section of the maker's catalogue. "
                    f"{n} {'piece' if n == 1 else 'pieces'} below, with our estimated value raw and in slabs, from {lo} to {hi}{tail}.")
        else:
            h1 = f"{esc(name)} &middot; Daniel Carr"
            title = f"{short(name, 52)}: Daniel Carr value"
            lede = (f"{esc(name)}: a Daniel Carr piece that is not in the maker's online catalogue. "
                    f"Our estimated value raw and in slabs runs from {lo} to {hi}{tail}.")
        desc = re.sub(r"<[^>]+>|&[a-z]+;", "", lede)[:300] + " Our opinion of value from a tested formula."
        if edition:
            lede += f" Edition of {esc(edition)}."
        metal_note, scripts = "", ""
        if any(L.get("oz_ag") or L.get("oz_au") or L.get("oz_pt") or L.get("oz_pd") for L in Ls):
            metal_note = (f'\n        <p class="metal-live" id="metal-live" data-pt-price="{ph["{{CARR_PT_RAW}}"]}" data-pd-price="{ph["{{CARR_PD_RAW}}"]}">'
                          f'<strong>Gold {ph["{{CARR_GOLD_SPOT}}"]} &middot; silver {ph["{{CARR_SILVER_SPOT}}"]} &middot; platinum {ph["{{CARR_PT_SPOT}}"]} &middot; palladium {ph["{{CARR_PD_SPOT}}"]} an ounce</strong>: '
                          f'the price when this edition was built ({ph["{{CARR_SPOT_DATE}}"]}). With JavaScript on, the page updates pieces that contain precious metal to the live price.</p>')
            scripts = '\n  <script src="/metal.js" defer></script>'
        html = render_carr({**carr, "lines": Ls}, urls)
        html = re.sub(r'\s*<h2>[^<]*</h2>\s*<p class="muted">[^<]*</p>', "", html, count=1)   # the part heading and note belong to the full guide
        sibs = [k for k in by_part.get((part, section), []) if k != (part, group)]
        related = [(esc(carr_name(groups[k][0])[0]), urls[k]) for k in sibs[:30]]
        part_name = CARR_PART_NAME.get(part, "Other Carr pieces")
        crumbs = [("Home", "/"), ("Price guide", "/price-guide/"), ("Daniel Carr", CARR_GUIDE), (name if len(name) < 60 else name[:57] + "…", None)]
        body = _page(h1, lede, CARR_GUIDE, metal_note, html,
                     f"More {esc(section) + ' issues' if section else esc(part_name.lower())}", related,
                     ("The full Daniel Carr / Moonlight Mint price guide", CARR_GUIDE))
        pages.append({"path": urls[(part, group)], "title": title, "description": desc, "body": body, "crumbs": crumbs,
                      "ld": _breadcrumb_ld(crumbs, site), "scripts": scripts, "full": name})
    seen = {}
    for pg in pages:                     # two names that shorten to the same title: keep more of each name
        seen.setdefault(pg["title"], []).append(pg)
    for same in seen.values():
        if len(same) > 1:
            for pg in same:
                pg["title"] = f"{short(pg['full'], 100)}: Daniel Carr value"
    return pages


def norm_carr(s):
    """A Moonlight Mint catalogue number as typed ('csa 2011 bs1', 'CSA-2011-BS1') -> 'CSA_2011_BS1'."""
    return re.sub(r"[\s\-_]+", "_", s.strip().upper()).strip("_")


def _plain(s):
    """Tag HTML as plain text for the decoder card."""
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("&middot;", "·"), ("&rsquo;", "’"), ("&ldquo;", "“"), ("&rdquo;", "”"), ("&amp;", "&")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def decoder_index(scd, carr, urls, scd_tag, carr_tag):
    """What the catalog-number decoder can show beyond the reference book: so-called dollars by HK number and
    Daniel Carr pieces by Moonlight Mint catalogue number, each with its page and our estimate range."""
    hk = {}
    by = {}
    for p in scd["pieces"]:
        by.setdefault(p["hk"], []).append(p)
    for h, ps in by.items():
        lo, hi = _range([v for p in ps for g in p["grades"] for v in (g["pcgs"][0], g["ngc"][0])])
        metals = ", ".join(sorted({p["metal"].lower() for p in ps}))
        f = [p for p in ps if p.get("basis") == "formula"]
        basis = ("from sales of this piece in our records" if not f else _plain(scd_tag(f[0])) if len(f) == len(ps)
                 else "from sales in our records for some finishes; formula only for others")
        hk[re.sub(r"[^a-z0-9]", "", h.lower())] = [scd_url(h), f"HK-{h} · {ps[0]['event']}, {ps[0]['year']} · {metals}",
                                                    lo, hi, basis, "PCGS and NGC slabs", any(p.get("oz_au") or p.get("oz_ag") for p in ps)]
    cn = {}
    for L in carr["lines"]:
        if L["part"] != "Catalogue" or not L["item"]:
            continue
        lo, hi = _range([g["estimate"] for g in L["grades"]])
        name = carr_name(L)[0]
        for no in [x.strip() for x in L["item"].split(",") if x.strip()]:
            if re.search(r"[_\d]", no):                       # catalogue numbers, not merchant names
                basis = _plain(carr_tag(L)) if L.get("basis") == "formula" else "from sales in our records"
                cn[norm_carr(no)] = [urls[(L["part"], L["group"])], f"{no} · {name}", lo, hi, basis, "raw and in slabs",
                                     bool(L.get("oz_ag") or L.get("oz_au") or L.get("oz_pt") or L.get("oz_pd"))]
    return {"hk": hk, "carr": cn}
