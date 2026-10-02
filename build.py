#!/usr/bin/env python3
"""
Builds the website (index.html), the CV (Peyman_Jahanbin_CV.pdf), the share card (og.jpg)
and sitemap.xml from content.toml.

    python3 build.py            build everything
    python3 build.py --check    only check content.toml for mistakes, write nothing
    python3 build.py --no-pdf   build the website only (skips the PDF and the share card)

You normally never run this by hand: double-click Build.command instead.
"""
import datetime
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
try:
    import tomllib
except ImportError:  # Python older than 3.11
    sys.exit("This needs Python 3.11 or newer. Install the free current version from https://www.python.org/downloads/ and try again.")
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILDER = ROOT / "builder"
CONTENT = ROOT / "content.toml"
CV_FILE = "Peyman_Jahanbin_CV.pdf"

ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"]
STATUS_ORDER = {"published": 0, "review": 1, "preprint": 2}
STATUS_KEY = {"published": "pub", "review": "rev", "preprint": "pre"}
CITE_KIND = {"published": "article", "review": "submitted", "preprint": "preprint"}
PROPER = {"Python", "Microsoft", "Excel", "IBM", "SPSS", "MATLAB", "Stata", "Java", "JavaScript", "SQL", "Praat",
          "Mplus", "Qualtrics", "Zotero", "NVivo", "Google", "English", "Spanish", "Arabic", "Farsi", "Persian"}


class ContentError(Exception):
    pass


# ----------------------------------------------------------------------------- text helpers
def esc(s):
    return html.escape(str(s), quote=False)


def attr(s):
    return html.escape(str(s), quote=True)


def inline(s, tag="i"):
    """Escape, then turn *stars* into italics and line breaks into <br>."""
    s = esc(s)
    s = re.sub(r"\*(.+?)\*", lambda m: f"<{tag}>{m.group(1)}</{tag}>", s)
    return s.replace("\n", "<br>")


def plain(s):
    return str(s).replace("*", "")


def cv_dates(s):
    return s.replace(" to ", "-")


def get(d, k, default=""):
    v = d.get(k, default)
    return default if v is None else v


def split_author(a):
    """'Given Family' or 'Display | Family, Given' -> (display, family, given)"""
    if "|" in a:
        disp, cite = a.split("|", 1)
        fam, _, giv = cite.partition(",")
        return disp.strip(), fam.strip(), giv.strip()
    parts = a.strip().split()
    return a.strip(), parts[-1], " ".join(parts[:-1])


def month_year(d):
    return d.strftime("%B %Y")


# ----------------------------------------------------------------------------- loading and checking
def load():
    try:
        with open(CONTENT, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ContentError(
            f"content.toml has a typing mistake: {e}\n"
            "  Usual causes: a missing closing quote, a missing [ or ], or a double quote inside text\n"
            "  (use single quotes around text that contains double quotes)."
        )


def check(c):
    problems, warnings = [], []

    def need(d, keys, where):
        for k in keys:
            if not get(d, k):
                problems.append(f"{where}: '{k}' is empty or missing")

    need(c.get("person", {}), ["first_name", "last_name", "status", "institution", "email", "site_url", "portrait"], "[person]")
    need(c.get("seo", {}), ["title", "description"], "[seo]")
    topics = {t["key"] for t in c.get("topics", [])}
    seen = set()
    for i, p in enumerate(c.get("publications", []), 1):
        w = f"publication #{i} ({get(p, 'id', get(p, 'title', '?'))[:40]})"
        need(p, ["id", "status", "year", "title", "authors"], w)
        if p.get("status") not in STATUS_ORDER:
            problems.append(f"{w}: status must be published, review or preprint")
        if p.get("id") in seen:
            problems.append(f"{w}: the id '{p.get('id')}' is used twice")
        seen.add(p.get("id"))
        for t in p.get("topics", []):
            if t not in topics:
                problems.append(f"{w}: unknown topic '{t}' (defined: {', '.join(sorted(topics))})")
        if p.get("cite", True) is not False:
            if not get(p, "cite_title"):
                warnings.append(f"{w}: no cite_title, so the cite buttons will use the title as written")
            if p.get("status") == "published" and not (p.get("doi") or p.get("url")):
                warnings.append(f"{w}: published but no doi or url")
        if p.get("status") == "published" and not (p.get("venue") or p.get("venue_text")):
            problems.append(f"{w}: no venue")
    for i, x in enumerate(c.get("presentations", []), 1):
        need(x, ["date", "title"], f"presentation #{i}")
    for g in c.get("teaching", []):
        for j, k in enumerate(g.get("courses", []), 1):
            need(k, ["code", "title"], f"teaching '{g.get('group', '?')}' course #{j}")
    for sec in ("education", "appointments", "projects", "news"):
        for i, x in enumerate(c.get(sec, []), 1):
            need(x, ["dates" if sec != "news" else "date", "title" if sec != "news" else "text"], f"{sec} #{i}")
    for i, d in enumerate(c.get("documents", []), 1):
        need(d, ["title", "file"], f"document #{i}")
        f = get(d, "file")
        if f and f != CV_FILE and not (ROOT / f).exists():
            problems.append(f"document #{i}: the file '{f}' is not in this folder")
    if not (ROOT / get(c.get("person", {}), "portrait", "portrait.jpg")).exists():
        problems.append("the portrait file named in [person] is not in this folder")
    return problems, warnings


# ----------------------------------------------------------------------------- authors
def own_name(c):
    return f"{c['person']['first_name']} {c['person']['last_name']}"


def site_authors(authors, own):
    disp = [split_author(a)[0] for a in authors]
    n = len(disp)
    pos = disp.index(own) + 1 if own in disp else 0
    if n <= 5:
        shown, etal = disp, False
    else:
        k = max(3, pos)
        shown, etal = disp[:k], k < n
    names = [f"<b>{esc(d)}</b>" if d == own else esc(d) for d in shown]
    if len(names) == 1 and not etal:
        return names[0]
    if etal:
        return ", ".join(names) + " et al."
    if len(names) == 2:
        return " &amp; ".join(names)
    return ", ".join(names[:-1]) + " &amp; " + names[-1]


def cv_authors(authors, own):
    disp = [split_author(a)[0] for a in authors]
    names = [f"<b>{esc(d)}</b>" if d == own else esc(d) for d in disp]
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return " &amp; ".join(names)
    return ", ".join(names[:-1]) + ", &amp; " + names[-1]


def cite_authors(authors):
    out = []
    for a in authors:
        _, fam, giv = split_author(a)
        out.append([fam, giv])
    return out


def doi_link(doi, text="DOI"):
    return f'<a class="doi" href="https://doi.org/{attr(doi)}" target="_blank" rel="noopener">{text}</a>'


# ----------------------------------------------------------------------------- website sections
def sec_wrap(sid, num, label_html, body, tight=True):
    cls = ' class="tight"' if tight else ""
    return (f'<section id="{sid}"{cls}>\n  <div class="sec">\n    <div class="lab rv"><span class="n">{num}</span><h2>{label_html}</h2></div>\n'
            f'    <div class="body">\n{body}\n    </div>\n  </div>\n</section>')


def row(code, text_html, right_html="", extra=""):
    return f'<div class="row rv"{extra}><div class="code">{code}</div><div class="t">{text_html}</div><div class="r">{right_html}</div></div>'


def s_news(c):
    rows = []
    for n in c["news"]:
        link = ""
        if n.get("link"):
            link = f'<a class="doi" href="{attr(n["link"])}" target="_blank" rel="noopener">Read</a>'
        rows.append("      " + row(esc(n["date"]), inline(n["text"]), link))
    return "recent", "Recent", "Recent", "\n".join(rows), True


def s_research(c):
    r, p = c.get("research", {}), c["person"]
    parts = []
    w, h = image_size(ROOT / p["portrait"])
    parts.append('      <div class="intro">')
    if r.get("statement"):
        parts.append(f'        <p class="statement rv">{inline(r["statement"], "em")}</p>')
    parts.append(f'        <div class="pframe rv"><figure class="portrait"><img src="{attr(p["portrait"])}" width="{w}" height="{h}" '
                 f'alt="Portrait of {attr(own_name(c))}" loading="lazy"></figure></div>')
    parts.append("      </div>")
    if r.get("themes"):
        parts.append('      <p class="themes rv">' + "".join(f"<span>{esc(t)}</span>" for t in r["themes"]) + "</p>")
    parts.append(FIGURE)
    if c.get("projects"):
        parts.append('      <div class="items">')
        for x in c["projects"]:
            parts.append(f'        <div class="item rv"><div class="when">{esc(x["dates"])}</div><div>\n'
                         f'          <h3>{inline(x["title"], "em")}</h3>\n          <p>{inline(get(x, "text"))}</p></div></div>')
        parts.append("      </div>")
    return "research", "Research", "Research", "\n".join(parts), False


def item_html(x, indent="      "):
    who = x.get("site_who") or " · ".join(v for v in (x.get("org"), x.get("place")) if v)
    s = f'{indent}<div class="item rv"><div class="when">{esc(x["dates"])}</div><div>\n{indent}  <h3>{inline(x["title"], "em")}</h3>'
    if who:
        s += f'<div class="who">{esc(who)}</div>'
    if x.get("text"):
        s += f'\n{indent}  <p>{inline(x["text"])}</p>'
    return s + "</div></div>"


def s_path(c):
    parts = []
    if c.get("education"):
        parts.append('      <div class="grp">Education</div>')
        parts += [item_html(x) for x in c["education"]]
    if c.get("appointments"):
        style = ' style="margin-top:70px"' if c.get("education") else ""
        parts.append(f'\n      <div class="grp"{style}>Appointments</div>')
        parts += [item_html(x) for x in c["appointments"]]
    return "path", "Education<br>&amp; Appointments", "Background", "\n".join(parts), False


def pub_ven(p):
    label = p.get("label") or ("Preprint" if p["status"] == "preprint" and not p.get("venue_text") else "")
    s = f'<span class="st">{esc(label)}</span>' if label else ""
    if p.get("venue_text"):
        s += esc(p["venue_text"])
    else:
        s += f'<i>{esc(p["venue"])}</i>'
    if p.get("volume"):
        s += ", " + esc(p["volume"]) + (f'({esc(p["issue"])})' if p.get("issue") else "")
    if p.get("pages"):
        s += f', <span class="nb">{esc(p["pages"])}</span>'
    elif p.get("article"):
        s += ", " + esc(p["article"])
    if p.get("doi"):
        s += doi_link(p["doi"])
    return s


def sorted_pubs(c):
    pubs = list(c.get("publications", []))
    pubs.sort(key=lambda p: (STATUS_ORDER.get(p["status"], 9), -int(p["year"])))
    return pubs


def s_publications(c):
    own = own_name(c)
    parts = ['''      <div class="tabs" role="group" aria-label="Filter publications by status">
        <button class="tab" data-f="all" aria-pressed="true">All</button>
        <button class="tab" data-f="pub" aria-pressed="false">Peer-reviewed</button>
        <button class="tab" data-f="rev" aria-pressed="false">In review</button>
        <button class="tab" data-f="pre" aria-pressed="false">Preprints</button>
      </div>
      <div class="topics" id="topics" role="group" aria-label="Filter publications by topic"><span class="toplab">Topic</span></div>
      <p class="none" id="pubnone" hidden>No papers match that combination.</p>
''']
    for p in sorted_pubs(c):
        parts.append(
            f'      <article class="pub rv" data-k="{STATUS_KEY[p["status"]]}" data-id="{attr(p["id"])}" data-topics="{attr(" ".join(p.get("topics", [])))}">'
            f'<div class="yr">{esc(p["year"])}</div><div>\n'
            f'        <h3>{esc(p["title"])}</h3>\n'
            f'        <div class="au">{site_authors(p["authors"], own)}</div>\n'
            f'        <div class="ven">{pub_ven(p)}</div></div></article>\n')
    scholar = c["person"].get("scholar")
    if scholar:
        parts.append(f'      <p class="more rv links"><a href="{attr(scholar)}" target="_blank" rel="noopener">Full list and citations on Google Scholar</a></p>\n')
    if c.get("presentations"):
        parts.append('      <div class="sub rv">Selected presentations</div>')
        for x in c["presentations"]:
            has_cite = bool(x.get("id") and x.get("cite_title"))
            with_ = ""
            if x.get("coauthors") or x.get("doi"):
                with_ = '<span class="with">'
                if x.get("coauthors"):
                    with_ += "With " + esc(x["coauthors"])
                if x.get("doi"):
                    with_ += doi_link(x["doi"], "Paper")
                with_ += "</span>"
            extra = f' data-id="{attr(x["id"])}"' if has_cite else ""
            parts.append("      " + row(esc(x["date"]), esc(x["title"]) + with_,
                                        esc(x.get("site_venue", "")), extra))
    return "publications", "Publications", "Publications", "\n".join(parts), False


def s_teaching(c):
    parts = ["      <div>"]
    for g in c["teaching"]:
        parts.append(f'        <div class="grp">{esc(g["group"])}</div>')
        for k in g.get("courses", []):
            parts.append("        " + row(esc(k["code"]), esc(k["title"]), esc(k.get("terms", "")).replace("\n", "<br>")))
    parts.append("      </div>")
    return "teaching", "Teaching", "Teaching", "\n".join(parts), False


def s_methods(c):
    parts = ['      <div class="meth">']
    for m in c["methods"]:
        lis = []
        for it in m.get("items", []):
            if "|" in it:
                a, b = it.split("|", 1)
                lis.append(f"<li>{esc(a.strip())} <small>{esc(b.strip())}</small></li>")
            else:
                lis.append(f"<li>{esc(it)}</li>")
        parts.append(f'        <div class="mcol rv"><h3>{esc(m["title"])}</h3><ul>\n          {"".join(lis)}</ul></div>')
    parts.append("      </div>")
    return "craft", "Methods", "Methods", "\n".join(parts), True


def s_service(c):
    parts = []
    pr = c.get("peer_review")
    if pr:
        parts.append('      <div class="grp">Peer review</div>')
        tally = ""
        if pr.get("journals"):
            tally = '\n        <ul class="tally">' + "".join(
                f'<li><i>{esc(j["name"])}</i><span>{esc(j["count"])}</span></li>' for j in pr["journals"]) + "</ul>"
        parts.append(f'      <div class="svc rv"><div class="yrs">{esc(pr["dates"])}</div><div>\n        <h3>{esc(pr["role"])}</h3>\n'
                     f'        <div class="who">{esc(get(pr, "summary"))}</div>{tally}</div></div>\n')
    if c.get("leadership"):
        parts.append('      <div class="grp">Leadership</div>')
        for x in c["leadership"]:
            who = x.get("site_who") or x.get("org", "")
            txt = f'\n        <p>{inline(x["text"])}</p>' if x.get("text") else ""
            parts.append(f'      <div class="svc rv"><div class="yrs">{esc(x["dates"])}</div><div>\n        <h3>{esc(x["role"])}</h3>\n'
                         f'        <div class="who">{esc(who)}</div>{txt}</div></div>')
    return "service", "Service", "Service", "\n".join(parts), True


def s_languages(c):
    parts = ['      <div class="langs">']
    for l in c["languages"]:
        parts.append(f'        <div class="lang rv"><div class="nm">{esc(l["name"])}</div><div class="lv">{esc(l["level"])}</div></div>')
    parts.append("      </div>")
    return "languages", "Languages", "Languages", "\n".join(parts), True


def s_honors(c):
    parts = []
    for h in c["honors"]:
        parts.append(f'      <div class="award rv">{esc(h.get("site_name") or h["name"])}<span>{esc(get(h, "note"))}</span></div>')
    return "honors", "Honors", "Honors", "\n".join(parts), True


def contact_html(c):
    p, ct = c["person"], c.get("contact", {})
    docs = ""
    for d in c.get("documents", []):
        docs += (f'\n        <div class="row"><div class="code">PDF</div><div class="t">{esc(d["title"])}</div>'
                 f'<div class="r"><a class="doi" href="{attr(d["file"])}" download>Download</a></div></div>')
    dossier = ""
    if docs:
        dossier = (f'    <div class="dossier">\n      <div class="caps">Dossier</div>\n'
                   f'      <p class="dnote">{inline(get(ct, "dossier_note"))}</p>\n      <div class="drows">{docs}\n      </div>\n    </div>\n')
    links = []
    if p.get("linkedin"):
        links.append(f'      <a href="{attr(p["linkedin"])}" target="_blank" rel="noopener">LinkedIn</a>')
    if p.get("scholar"):
        links.append(f'      <a href="{attr(p["scholar"])}" target="_blank" rel="noopener">Google Scholar</a>')
    return (f'<section class="contact" id="contact">\n  <div class="rv">\n    <div class="caps" style="margin-bottom:26px">Contact</div>\n'
            f'    <h2 class="big">{inline(get(ct, "heading", "Get in *touch.*"), "em")}</h2>\n'
            f'    <a class="mail" href="mailto:{attr(p["email"])}">{esc(p["email"])}</a>\n{dossier}'
            f'    <div class="links">\n' + "\n".join(links) + "\n    </div>\n  </div>\n</section>")


FIGURE = '''      <figure class="fig rv">
        <div class="figt">Where human and automated scores part ways</div>
        <div class="scope" id="vizB" role="img" aria-label="Animated chart of a human rater and an automated scorer scoring the same spoken responses. The two lines usually agree and sometimes part ways. Gold shading marks the moments when the gap puts them on opposite sides of the cut score, so the decision changes."><canvas id="scope"></canvas><div class="tip" id="tipB"></div></div>
        <figcaption>An illustration of the question behind my dissertation. The gold line is a human rater and the ivory line an automated scorer. They usually agree, but a gap matters most when it falls across the cut score and changes the decision. This is a simulation, not study data.</figcaption>
      </figure>'''


def image_size(path):
    try:
        b = path.read_bytes()
        i = 2
        while i < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                return int.from_bytes(b[i + 7:i + 9], "big"), int.from_bytes(b[i + 5:i + 7], "big")
            i += 2 + int.from_bytes(b[i + 2:i + 4], "big")
    except Exception:
        pass
    return 1400, 1379


# ----------------------------------------------------------------------------- cites
def cite_records(c):
    rec = {}
    for p in sorted_pubs(c):
        if p.get("cite", True) is False:
            continue
        auth = p["authors"]
        r = {"key": p.get("bibkey") or auto_key(p), "kind": CITE_KIND[p["status"]], "y": int(p["year"]), "v": get(p, "venue")}
        for src, dst in (("volume", "vol"), ("issue", "iss"), ("pages", "pp"), ("article", "art"), ("doi", "doi")):
            if p.get(src):
                r[dst] = str(p[src])
        r["t"] = p.get("cite_title") or p["title"]
        r["a"] = cite_authors(auth)
        if p.get("online"):
            r["online"] = True
        if p.get("url"):
            r["url"] = p["url"]
        if p.get("eprint"):
            r["eprint"] = p["eprint"]
        rec[p["id"]] = r
    for x in c.get("presentations", []):
        if not (x.get("id") and x.get("cite_title")):
            continue
        rec[x["id"]] = {
            "key": x.get("bibkey") or auto_key({"authors": x.get("cite_authors", []), "year": x.get("cite_year", ""), "title": x["cite_title"]}),
            "kind": "talk", "y": int(x.get("cite_year", 0)), "date": get(x, "cite_date"), "fmt": get(x, "cite_format"),
            "v": get(x, "cite_event"), "bt": get(x, "cite_booktitle"), "loc": get(x, "cite_location"), "month": get(x, "cite_month"),
            **({"doi": x["doi"]} if x.get("doi") else {}),
            "t": x["cite_title"], "a": cite_authors(x.get("cite_authors", []))}
    return rec


def auto_key(p):
    fam = split_author(p["authors"][0])[1] if p.get("authors") else "anon"
    fam = re.sub(r"[^a-z]", "", fam.lower()) or "anon"
    w = next((w for w in re.findall(r"[A-Za-z]+", p.get("cite_title") or p["title"]) if len(w) > 3 and w.lower() not in ("with", "from", "that", "this")), "x")
    return f"{fam}{p['year']}{w.lower()}"


# ----------------------------------------------------------------------------- website assembly
def build_site(c, today):
    p, seo = c["person"], c.get("seo", {})
    full = own_name(c)
    url = p["site_url"]
    secs = []
    if c.get("news"):
        secs.append(s_news(c))
    if c.get("research") or c.get("projects"):
        secs.append(s_research(c))
    if c.get("education") or c.get("appointments"):
        secs.append(s_path(c))
    if c.get("publications") or c.get("presentations"):
        secs.append(s_publications(c))
    if c.get("teaching"):
        secs.append(s_teaching(c))
    if c.get("methods"):
        secs.append(s_methods(c))
    if c.get("peer_review") or c.get("leadership"):
        secs.append(s_service(c))
    if c.get("languages"):
        secs.append(s_languages(c))
    if c.get("honors"):
        secs.append(s_honors(c))

    main = []
    for n, (sid, label_html, _short, body, tight) in enumerate(secs):
        main.append(sec_wrap(sid, ROMAN[n], label_html, body, tight))
    main.append(contact_html(c))

    ids = [s[0] for s in secs]
    first_id = ids[0] if ids else "contact"
    cue_id = "research" if "research" in ids else first_id
    nav_labels = {"research": "Research", "path": "Background", "publications": "Publications", "teaching": "Teaching"}
    nav_items = [(i, nav_labels[i]) for i in ids if i in nav_labels] + [("contact", "Contact")]
    nav = (f'<nav id="nav">\n  <div class="wrap">\n    <a href="#top" class="mono" aria-label="{attr(full)}, home">{esc(p.get("initials", "P. J."))}</a>\n    <ul>\n'
           + "\n".join(f'      <li><a href="#{i}">{l}</a></li>' for i, l in nav_items)
           + '\n    </ul>\n    <button class="menu" id="menu" type="button" aria-expanded="false" aria-controls="sheet"><span>Menu</span></button>\n  </div>\n</nav>')
    sheet_items = [(s[0], s[2]) for s in secs] + [("contact", "Contact")]
    sheet = ('<div class="sheet" id="sheet">\n  <ul>\n' + "\n".join(f'    <li><a href="#{i}">{l}</a></li>' for i, l in sheet_items) + "\n  </ul>\n</div>")

    links = []
    cv_doc = next((d for d in c.get("documents", []) if d["file"] == CV_FILE), None)
    links.append(f'        <a href="{CV_FILE}" download>Curriculum Vitae</a>')
    if p.get("scholar"):
        links.append(f'        <a href="{attr(p["scholar"])}" target="_blank" rel="noopener">Scholar</a>')
    if p.get("linkedin"):
        links.append(f'        <a href="{attr(p["linkedin"])}" target="_blank" rel="noopener">LinkedIn</a>')
    hero = f'''<header class="hero" id="top">
  <div class="wrap hero-top">
    <div class="mast">
      <div class="caps">{esc(p["status"])} · {esc(p["institution"])}</div>
      <i class="mrule" aria-hidden="true"></i>
      <span class="mmeta">{esc(" · ".join(p.get("specialties", [])))}</span>
    </div>
    <div class="title">
      <h1><span class="ln"><span>{esc(p["first_name"])}</span></span><span class="ln"><span><em>{esc(p["last_name"])}</em></span></span></h1>
      <p class="lede">{inline(get(p, "tagline"))}</p>
    </div>
  </div>
  <div class="viz" id="vizA" role="img" aria-label="Animated spectrogram of synthesized speech, with the formants and pauses labelled"><canvas id="spec"></canvas><canvas id="ovA" class="ov"></canvas><div class="tip" id="tipA"></div></div>
  <div class="wrap hero-foot">
    <div class="hero-bot">
      <div class="links">
{chr(10).join(links)}
      </div>
      <a class="cue" href="#{cue_id}" aria-label="Scroll to the content"><span>Scroll</span><i aria-hidden="true"></i></a>
    </div>
  </div>
</header>'''

    initials = (p["first_name"][:1] + p["last_name"][:1]).upper()
    favicon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%230a0a0a'/%3E"
               f"%3Ctext x='50' y='67' font-size='56' text-anchor='middle' fill='%23b99a5b' font-family='Georgia' font-style='italic'%3E{initials}%3C/text%3E%3C/svg%3E")
    ld = {"@context": "https://schema.org", "@type": "Person", "name": full, "url": url}
    if seo.get("job_title"):
        ld["jobTitle"] = seo["job_title"]
    ld["affiliation"] = {"@type": "CollegeOrUniversity", "name": p["institution"]}
    if seo.get("alumni_of"):
        ld["alumniOf"] = [{"@type": "CollegeOrUniversity", "name": a} for a in seo["alumni_of"]]
    if seo.get("knows_about"):
        ld["knowsAbout"] = seo["knows_about"]
    ld["sameAs"] = [x for x in (p.get("linkedin"), p.get("scholar")) if x]
    share_alt = get(seo, "share_alt", f"{full}. " + (", ".join(p.get("specialties", [])) or ""))
    head = f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(seo["title"])}</title>
<meta name="description" content="{attr(seo["description"])}">
<meta property="og:title" content="{attr(full)}">
<meta property="og:description" content="{attr(get(seo, "share_text", seo["description"]))}">
<meta property="og:type" content="profile">
<meta property="profile:first_name" content="{attr(p["first_name"])}">
<meta property="profile:last_name" content="{attr(p["last_name"])}">
<meta property="og:image" content="{attr(url)}og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{attr(share_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="{attr(full)}">
<meta property="og:url" content="{attr(url)}">
<link rel="canonical" href="{attr(url)}">
<meta name="theme-color" content="#0a0a0a">
<meta name="color-scheme" content="dark">
<link rel="icon" href="{favicon}">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}
</script>'''

    footer = (f'<footer>\n  <div class="wrap"><span>{esc(full)}</span><span>{esc(get(p, "location"))}</span>'
              f'<span>Updated {month_year(today)}</span><a href="#top">Back to top &uarr;</a></div>\n</footer>')
    cites = json.dumps(cite_records(c), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    cites_block = f'<script type="application/json" id="cites">{cites}</script>'
    topics_js = json.dumps([["all", "All topics"]] + [[t["key"], t["label"]] for t in c.get("topics", [])], ensure_ascii=False, separators=(",", ":"))

    tpl = (BUILDER / "site.html").read_text(encoding="utf-8")
    out = (tpl.replace("@@HEAD@@", head).replace("@@SKIP@@", f'<a class="skip" href="#{first_id}">Skip to content</a>')
           .replace("@@NAV@@", nav).replace("@@SHEET@@", sheet).replace("@@HERO@@", hero)
           .replace("@@MAIN@@", "\n\n".join(main) + "\n").replace("@@FOOTER@@", footer)
           .replace("@@CITES@@", cites_block).replace("@@TOPICS@@", topics_js))
    banner = "<!-- GENERATED FILE. Do not edit this by hand: edit content.toml, then double-click Build.command. -->\n"
    out = out.replace("<!doctype html>\n", "<!doctype html>\n" + banner, 1)
    assert "@@" not in out, "unfilled placeholder in site template"
    return out


# ----------------------------------------------------------------------------- CV
def cv_entry(title, dates="", sub_l="", sub_r="", text=""):
    s = f'<div class="ent"><div class="r1"><span class="l">{title}</span><span class="d">{dates}</span></div>'
    if sub_l or sub_r:
        s += f'<div class="r2"><span>{sub_l}</span><span class="p">{sub_r}</span></div>'
    if text:
        s += f"<p>{text}</p>"
    return s + "</div>"


def lowfirst(t):
    w = t.split(" ")[0]
    if w in PROPER or len(w) == 1 or any(ch.isupper() for ch in w[1:]):
        return t
    return t[:1].lower() + t[1:]


def human_join(items):
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def cv_body(c, today):
    p, cv = c["person"], c.get("cv", {})
    own = own_name(c)
    out = []
    contact = []
    for it in cv.get("contact_line", []):
        if "@" in it:
            contact.append(f'<a href="mailto:{attr(it)}">{esc(it)}</a>')
        elif it.lower().startswith("linkedin") and p.get("linkedin"):
            contact.append(f'<a href="{attr(p["linkedin"])}">{esc(it)}</a>')
        elif "scholar" in it.lower() and p.get("scholar"):
            contact.append(f'<a href="{attr(p["scholar"])}">{esc(it)}</a>')
        else:
            contact.append(esc(it))
    out.append(f'<header class="top"><h1>{esc(own)}</h1><div class="sub">{esc(get(cv, "subtitle"))}</div>'
               f'<div class="contact">{"<span class=sep>|</span>".join(contact)}</div></header>')
    if cv.get("research_interests"):
        out.append(f'<h2>Research Interests</h2><p>{inline(cv["research_interests"])}</p>')
    if c.get("education"):
        out.append("<h2>Education</h2>" + "".join(
            cv_entry(esc(plain(x.get("cv_title") or x["title"])), esc(x.get("cv_dates") or cv_dates(x["dates"])), esc(get(x, "org")), esc(get(x, "place")),
                     inline(x.get("cv_text") or get(x, "text"))) for x in c["education"]))
    if c.get("appointments"):
        out.append("<h2>Academic Appointments</h2>" + "".join(
            cv_entry(esc(plain(x.get("cv_title") or x["title"])), esc(x.get("cv_dates") or cv_dates(x["dates"])), esc(get(x, "org")), esc(get(x, "place")),
                     inline(x.get("cv_text") or get(x, "text"))) for x in c["appointments"]))
    groups = [("published", "Peer-Reviewed Publications &amp; Accepted Manuscripts"),
              ("review", "Manuscripts in Review / Editorial Processing"),
              ("preprint", "Preprints &amp; Reproducible Research")]
    pubs = sorted_pubs(c)
    for st, head in groups:
        items = [x for x in pubs if x["status"] == st]
        if not items:
            continue
        out.append(f"<h2>{head}</h2>")
        for x in items:
            if x["status"] == "published":
                v = esc(x["venue"]) + (", " + esc(x["volume"]) + (f'({esc(x["issue"])})' if x.get("issue") else "") if x.get("volume") else "")
                v += (", " + esc(x["pages"])) if x.get("pages") else (", " + esc(x["article"])) if x.get("article") else ""
                line = f"<i>{v}</i>. {esc(x['year'])}"
                if x.get("doi"):
                    line += f'. DOI: <a href="https://doi.org/{attr(x["doi"])}">{esc(x["doi"])}</a>'
            elif x["status"] == "review":
                line = f'<i>{esc(x["venue"])}</i>. {esc(x.get("cv_status") or x.get("label") or "Under review")}'
            elif x.get("venue_text"):
                line = f'<i>{esc(x["venue_text"])}</i>. {esc(x["year"])}'
            else:
                line = f'<i>{esc(x["venue"])}</i>. {esc(x["year"])}; {esc(x.get("cv_note") or "Preprint")}'
                if x.get("doi"):
                    line += f'. DOI: <a href="https://doi.org/{attr(x["doi"])}">{esc(x["doi"])}</a>'
            out.append(f'<div class="pub"><div class="t">{esc(plain(x["title"]))}</div><div class="au">{cv_authors(x["authors"], own)}</div><div class="vn">{line}</div></div>')
    if c.get("projects"):
        out.append("<h2>Research Projects</h2>" + "".join(
            cv_entry(esc(plain(x.get("cv_title") or x["title"])), esc(cv_dates(x["dates"])), esc(get(x, "org")), "", inline(x.get("cv_text") or get(x, "text")))
            for x in c["projects"]))
    if c.get("teaching"):
        out.append("<h2>Teaching Experience</h2>")
        if cv.get("teaching_header"):
            out.append(f'<div class="tuni">{esc(cv["teaching_header"])}</div>')
        if cv.get("teaching_summary"):
            out.append(f'<div class="tsum">{esc(cv["teaching_summary"])}</div>')
        for g in c["teaching"]:
            out.append(f'<h3 class="grp">{esc(g["group"])} Courses</h3>' if g["group"] in ("Graduate", "Undergraduate") else f'<h3 class="grp">{esc(g["group"])}</h3>')
            for k in g.get("courses", []):
                terms = k.get("cv_terms") or cv_dates(k.get("terms", "")).replace(" · ", "; ").replace("\n", " ")
                out.append(f'<div class="crs"><div class="n"><b>{esc(k["code"])} {esc(k.get("cv_title") or k["title"])}</b></div><div class="tm">{esc(terms)}</div></div>')
    if c.get("presentations"):
        out.append("<h2>Selected Conference Presentations</h2>" + "".join(
            cv_entry(esc(x["title"]), esc(x.get("cv_date") or x["date"]), esc(x.get("cv_event") or x.get("site_venue", "")), esc(get(x, "place")))
            for x in c["presentations"]))
    pr = c.get("peer_review")
    if pr:
        out.append("<h2>Peer Review Service</h2>" + cv_entry(esc(pr.get("cv_role") or pr["role"]), esc(cv_dates(pr["dates"])), "", "", esc(pr.get("cv_summary") or get(pr, "summary"))))
    if c.get("methods"):
        lis = []
        for m in c["methods"]:
            items = []
            for it in m.get("items", []):
                if "|" in it:
                    a, b = it.split("|", 1)
                    items.append(f"{a.strip()} ({b.strip()})")
                else:
                    items.append(lowfirst(it))
            lis.append(f'<li><b>{esc(m.get("cv_title") or m["title"])}:</b> {esc(human_join(items))}.</li>')
        out.append('<h2>Research Methods &amp; Technical Skills</h2><ul class="b">' + "".join(lis) + "</ul>")
    if cv.get("methodological_training"):
        out.append('<h2>Methodological Training</h2><ul class="b">' + "".join(
            f'<li><b>{esc(m["label"])}:</b> {esc(m["text"])}</li>' for m in cv["methodological_training"]) + "</ul>")
    if c.get("leadership"):
        out.append("<h2>Academic &amp; Professional Service</h2>" + "".join(
            cv_entry(esc(x.get("cv_role") or x["role"]), esc(cv_dates(x["dates"])), esc(x.get("cv_org") or x.get("org", "")), esc(get(x, "place")), esc(get(x, "text")))
            for x in c["leadership"]))
    if c.get("honors"):
        out.append("<h2>Awards, Scholarships &amp; Honors</h2>" + "".join(
            f'<div class="hon"><b>{esc(h["name"])}</b>{", " + esc(h.get("cv_note") or h["note"]) if (h.get("cv_note") or h.get("note")) else ""}</div>'
            for h in c["honors"]))
    if c.get("languages"):
        out.append('<h2>Languages</h2><p class="langs">' + '<span class="sep">|</span>'.join(
            f'<b>{esc(l["name"])}</b> ({esc(l.get("cv_level") or l["level"])})' for l in c["languages"]) + "</p>")
    return "\n".join(out)


def build_cv_html(c, today):
    tpl = (BUILDER / "cv.html").read_text(encoding="utf-8")
    full = own_name(c)
    foot = f"{full} | Academic Curriculum Vitae | Updated {month_year(today)} | Page "
    foot = foot.replace("\\", "\\\\").replace('"', '\\"')
    return (tpl.replace("@@TITLE@@", esc(f"{full}, Curriculum Vitae")).replace("@@AUTHOR@@", attr(full))
            .replace("@@FOOTER@@", foot).replace("@@BODY@@", cv_body(c, today)))


def build_og_html(c):
    p, seo = c["person"], c.get("seo", {})
    tpl = (BUILDER / "og.html").read_text(encoding="utf-8")
    line = "<br>".join(esc(x) for x in get(seo, "share_image_line", "").split("\n"))
    return (tpl.replace("@@CAPS@@", esc(f'{p["status"]} · {p["institution"]}')).replace("@@FIRST@@", esc(p["first_name"]))
            .replace("@@LAST@@", esc(p["last_name"])).replace("@@LINE@@", line))


# ----------------------------------------------------------------------------- Chrome
def find_chrome():
    for cand in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if Path(cand).exists():
            return cand
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")


def chrome(args, output, timeout=120):
    """Run headless Chrome until it has written `output`. Chrome sometimes lingers after finishing, so we stop it ourselves."""
    import time
    exe = find_chrome()
    if not exe:
        raise ContentError("Google Chrome was not found, so the PDF could not be made. Install Chrome (it is free) and run the build again.")
    output = Path(output)
    output.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as prof:
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars", f"--user-data-dir={prof}"] + args
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        end, last = time.time() + timeout, -1
        try:
            while time.time() < end:
                size = output.stat().st_size if output.exists() else -1
                if size > 0 and size == last:
                    break
                last = size
                if proc.poll() is not None:
                    break
                time.sleep(1.0)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()


def stamp_ok(name, digest, outputs):
    f = BUILDER / ".stamps" / name
    return f.exists() and f.read_text() == digest and all((ROOT / o).exists() for o in outputs)


def stamp_write(name, digest):
    d = BUILDER / ".stamps"
    d.mkdir(exist_ok=True)
    (d / name).write_text(digest)


def make_pdf(c, today, say):
    body = build_cv_html(c, today)
    digest = hashlib.sha256((body + (BUILDER / "fonts" / "fonts.css").read_text()).encode()).hexdigest()
    if stamp_ok("cv", digest, [CV_FILE]):
        say("  CV PDF: nothing changed, kept the existing file")
        return
    src = BUILDER / "_cv.html"
    src.write_text(body, encoding="utf-8")
    tmp = ROOT / "_cv_tmp.pdf"
    try:
        chrome(["--no-pdf-header-footer", f"--print-to-pdf={tmp}", "--virtual-time-budget=8000", src.as_uri()], tmp)
        if not tmp.exists() or tmp.stat().st_size < 10_000:
            raise ContentError("The PDF could not be created.")
        pages = len(re.findall(rb"/Type\s*/Page[^s]", tmp.read_bytes()))
        shutil.move(str(tmp), ROOT / CV_FILE)
        stamp_write("cv", digest)
        say(f"  CV PDF: made ({pages} pages)")
    finally:
        src.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)


def make_og(c, say):
    body = build_og_html(c)
    digest = hashlib.sha256((body + (BUILDER / "fonts" / "fonts.css").read_text()).encode()).hexdigest()
    if stamp_ok("og", digest, ["og.jpg"]):
        say("  Share card (og.jpg): nothing changed, kept the existing file")
        return
    src = BUILDER / "_og.html"
    src.write_text(body, encoding="utf-8")
    png = ROOT / "_og_tmp.png"
    try:
        chrome([f"--screenshot={png}", "--window-size=1200,630", "--default-background-color=0a0a0aff", "--virtual-time-budget=6000", src.as_uri()], png)
        if not png.exists():
            raise ContentError("The share card (og.jpg) could not be created.")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "88", str(png), "--out", str(ROOT / "og.jpg")], capture_output=True, check=True)
        stamp_write("og", digest)
        say("  Share card (og.jpg): made")
    finally:
        src.unlink(missing_ok=True)
        png.unlink(missing_ok=True)


# ----------------------------------------------------------------------------- main
def main(argv):
    only_check = "--check" in argv
    no_pdf = "--no-pdf" in argv
    say = print
    try:
        c = load()
        problems, warnings = check(c)
        for w in warnings:
            say("  note: " + w)
        if problems:
            say("\nPlease fix these in content.toml, then run the build again:\n")
            for pr in problems:
                say("  - " + pr)
            return 1
        if only_check:
            say("content.toml looks good.")
            return 0
        today = datetime.date.today()
        if c["person"].get("updated"):
            today = datetime.datetime.strptime(c["person"]["updated"], "%B %Y").date()
        (ROOT / "index.html").write_text(build_site(c, today), encoding="utf-8")
        say("  Website (index.html): made")
        site = c["person"]["site_url"]
        (ROOT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url>\n'
            f'    <loc>{esc(site)}</loc>\n    <lastmod>{datetime.date.today().isoformat()}</lastmod>\n  </url>\n</urlset>\n', encoding="utf-8")
        if not no_pdf:
            make_pdf(c, today, say)
            make_og(c, say)
        say("\nDone.")
        return 0
    except ContentError as e:
        say("\n" + str(e))
        return 1
    except KeyError as e:
        say(f"\nA required field is missing in content.toml: {e}. Check the entry you edited last.")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
