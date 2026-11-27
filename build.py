#!/usr/bin/env python3
"""
Builds the website (index, research, publications, teaching and service pages), the CV (Peyman_Jahanbin_CV.pdf and .docx), the share card (og.jpg)
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
from xml.dom import minidom
try:
    import tomllib
except ImportError:  # Python older than 3.11
    sys.exit("This needs Python 3.11 or newer. Install the free current version from https://www.python.org/downloads/ and try again.")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "builder"))
from docxwriter import Doc  # noqa: E402

ROOT = Path(__file__).resolve().parent
BUILDER = ROOT / "builder"
CONTENT = ROOT / "content.toml"
CV_FILE = "Peyman_Jahanbin_CV.pdf"
CV_DOCX = "Peyman_Jahanbin_CV.docx"

ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx", "xxi", "xxii", "xxiii", "xxiv"]
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


def normalize(c):
    """Forgive harmless slips: numbers instead of text, one string instead of a list, odd capitalisation."""
    for p in c.get("publications", []) if isinstance(c.get("publications"), list) else []:
        if not isinstance(p, dict):
            continue
        for k in ("year", "volume", "issue", "pages", "article"):
            if isinstance(p.get(k), (int, float)) and not isinstance(p.get(k), bool):
                p[k] = str(p[k])
        if isinstance(p.get("status"), str):
            p["status"] = p["status"].strip().lower()
        for k in ("topics", "authors"):
            if isinstance(p.get(k), str):
                p[k] = [p[k]]
    for x in c.get("presentations", []) if isinstance(c.get("presentations"), list) else []:
        if isinstance(x, dict):
            if isinstance(x.get("cite_authors"), str):
                x["cite_authors"] = [x["cite_authors"]]
            if isinstance(x.get("cite_year"), str) and x["cite_year"].isdigit():
                x["cite_year"] = int(x["cite_year"])
    return c


def check(c):
    problems, warnings = [], []
    LISTS = ["news", "projects", "education", "appointments", "topics", "publications", "reports", "presentations", "teaching", "methods",
             "leadership", "languages", "honors", "documents", "extra_sections"]
    TABLES = ["person", "seo", "cv", "research", "peer_review", "contact"]
    for k in LISTS:
        if k in c and not (isinstance(c[k], list) and all(isinstance(x, dict) for x in c[k])):
            problems.append(f"[{k}] must be written as blocks that start with [[{k}]]")
            c[k] = []
    for k in TABLES:
        if k in c and not isinstance(c[k], dict):
            problems.append(f"[{k}] must be a section that starts with [{k}]")
            c[k] = {}

    def need(d, keys, where, kind=str):
        for k in keys:
            v = d.get(k)
            if v in (None, "", []):
                problems.append(f"{where}: '{k}' is empty or missing")
            elif kind is str and not isinstance(v, str):
                problems.append(f"{where}: '{k}' must be text in quotes")

    def lst(d, k, where):
        v = d.get(k)
        if v in (None, "", []):
            problems.append(f"{where}: '{k}' is empty or missing")
            return []
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            problems.append(f"{where}: '{k}' must be a list of quoted text, like [\"one\", \"two\"]")
            return []
        return v

    need(c.get("person", {}), ["first_name", "last_name", "status", "institution", "email", "site_url", "portrait"], "[person]")
    need(c.get("seo", {}), ["title", "description"], "[seo]")
    if c.get("person") and not isinstance(c["person"].get("specialties", []), list):
        problems.append("[person]: 'specialties' must be a list of quoted text")
        c["person"]["specialties"] = []
    for i, t in enumerate(c.get("topics", []), 1):
        need(t, ["key", "label"], f"topic #{i}")
    topics = {t.get("key") for t in c.get("topics", [])}
    seen = set()
    for i, p in enumerate(c.get("publications", []), 1):
        w = f"publication #{i} ({str(p.get('id') or p.get('title') or '?')[:40]})"
        need(p, ["id", "status", "year", "title"], w)
        auth = lst(p, "authors", w)
        if p.get("status") not in STATUS_ORDER:
            problems.append(f"{w}: status must be published, review or preprint")
        if p.get("year") and not re.fullmatch(r"\d{4}", str(p["year"])):
            problems.append(f"{w}: year must be four digits, like 2027")
        if p.get("date") and not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", str(p["date"])):
            problems.append(f"{w}: date must look like 2026-10-08, 2026-10 or 2026")
        elif p.get("date") and p.get("year") and str(p["date"])[:4] != str(p["year"]):
            warnings.append(f"{w}: the date and the year do not match")
        if p.get("id") in seen:
            problems.append(f"{w}: the id '{p.get('id')}' is used twice")
        seen.add(p.get("id"))
        for t in p.get("topics", []) if isinstance(p.get("topics", []), list) else []:
            if t not in topics:
                problems.append(f"{w}: unknown topic '{t}' (defined: {', '.join(sorted(x for x in topics if x))})")
        if p.get("cite", True) is not False:
            if not p.get("cite_title"):
                warnings.append(f"{w}: no cite_title, so the cite buttons will use the title as written")
            if p.get("status") == "published" and not (p.get("doi") or p.get("url")):
                warnings.append(f"{w}: published but no doi or url")
        if not (p.get("venue") or p.get("venue_text")):
            problems.append(f"{w}: 'venue' is empty or missing (the journal or server name)")
        for a in auth:
            if "|" in a and "," not in a.split("|", 1)[1]:
                problems.append(f"{w}: author '{a}' should look like \"Fan Qihang | Fan, Qihang\"")
    for i, x in enumerate(c.get("presentations", []), 1):
        need(x, ["date", "title"], f"presentation #{i}")
        if x.get("id") and x.get("cite_title"):
            lst(x, "cite_authors", f"presentation #{i}")
            if not x.get("cite_year"):
                problems.append(f"presentation #{i}: cite_year is missing (needed for the cite buttons)")
    for i, x in enumerate(c.get("reports", []), 1):
        need(x, ["title", "date", "publisher"], f"report #{i}")
        lst(x, "authors", f"report #{i}")
    for i, g in enumerate(c.get("teaching", []), 1):
        need(g, ["group"], f"teaching group #{i}")
        if not isinstance(g.get("courses", []), list) or not all(isinstance(k, dict) for k in g.get("courses", [])):
            problems.append(f"teaching group #{i}: 'courses' must be a list of {{ code = ..., title = ... }} items")
            g["courses"] = []
        for j, k in enumerate(g.get("courses", []), 1):
            need(k, ["code", "title"], f"teaching '{g.get('group', '?')}' course #{j}")
    for i, m in enumerate(c.get("methods", []), 1):
        need(m, ["title"], f"methods block #{i}")
        lst(m, "items", f"methods block #{i}")
    for sec, keys in (("news", ["date", "text"]), ("projects", ["dates", "title"]), ("education", ["dates", "title"]),
                      ("appointments", ["dates", "title"]), ("leadership", ["dates", "role"]), ("languages", ["name", "level"]),
                      ("honors", ["name"]), ("documents", ["title", "file"])):
        for i, x in enumerate(c.get(sec, []), 1):
            need(x, keys, f"{sec} #{i}")
    if c.get("peer_review"):
        need(c["peer_review"], ["dates", "role"], "[peer_review]")
        js = c["peer_review"].get("journals", [])
        if not isinstance(js, list) or not all(isinstance(j, dict) and j.get("name") and j.get("count") for j in js):
            problems.append("[peer_review]: each journal needs a name and a count")
            c["peer_review"]["journals"] = []
    for i, d in enumerate(c.get("documents", []), 1):
        f = d.get("file")
        if f and f != CV_FILE and not (ROOT / f).exists():
            problems.append(f"document #{i}: the file '{f}' is not in this folder")
    for i, e in enumerate(c.get("extra_sections", []), 1):
        need(e, ["title"], f"extra section #{i}")
        if not isinstance(e.get("items", []), list) or not all(isinstance(x, dict) for x in e.get("items", [])):
            problems.append(f"extra section #{i}: items must be blocks that start with [[extra_sections.items]]")
            e["items"] = []
        for j, it in enumerate(e["items"], 1):
            need(it, ["title"], f"extra section #{i} item #{j}")
    mt = c.get("cv", {}).get("methodological_training", [])
    if mt and not (isinstance(mt, list) and all(isinstance(m, dict) and m.get("label") and m.get("text") for m in mt)):
        problems.append("[cv]: each methodological_training item needs a label and a text")
        c["cv"]["methodological_training"] = []
    if c.get("cv") and not isinstance(c["cv"].get("contact_line", []), list):
        problems.append("[cv]: contact_line must be a list of quoted text")
        c["cv"]["contact_line"] = []
    pt = c.get("person", {}).get("portrait")
    if pt and not (ROOT / pt).exists():
        problems.append(f"the portrait file '{pt}' is not in this folder")
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


def pub_date_key(p):
    """(year, month, day) from `date`, or just the year; a missing month or day counts as 0 (so it sorts last within its year)."""
    parts = [int(x) for x in re.findall(r"\d+", str(p.get("date") or p.get("year") or 0))][:3]
    return tuple(parts + [0] * (3 - len(parts)))


def sorted_pubs(c, by_status=True):
    """Newest first. The CV keeps its status groups (by_status=True); the website list is one newest-first list."""
    pubs = list(c.get("publications", []))
    pubs.sort(key=lambda p: tuple(-v for v in pub_date_key(p)))  # stable: ties keep the order in content.toml
    if by_status:
        pubs.sort(key=lambda p: STATUS_ORDER.get(p["status"], 9))
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
    for p in sorted_pubs(c, by_status=False):
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
        wide = " wide" if m.get("featured") else ""
        lead = f'<p class="lead">{inline(m["lead"])}</p>' if m.get("lead") else ""
        parts.append(f'        <div class="mcol{wide} rv"><h3>{esc(m["title"])}</h3>{lead}<ul>\n          {"".join(lis)}</ul></div>')
    parts.append("      </div>")
    return "craft", "Methods", "Methods", "\n".join(parts), True


def review_total(pr):
    if pr.get("total"):
        return str(pr["total"])
    nums = [re.match(r"\s*(\d+)", str(j.get("count", ""))) for j in pr.get("journals", [])]
    return str(sum(int(m.group(1)) for m in nums)) if nums and all(nums) else ""


def s_review(c):
    pr = c["peer_review"]
    total = review_total(pr)
    head = " · ".join(x for x in (pr["role"], pr["dates"], f"{total} manuscript reviews" if total else "") if x)
    parts = [f'      <div class="grp">{esc(head)}</div>']
    for j in pr.get("journals", []):
        name = f'<i>{esc(j["name"])}</i>'
        if j.get("url"):
            parts.append(f'      <a class="award rv" href="{attr(j["url"])}" target="_blank" rel="noopener">{name}<span>{esc(j["count"])}</span></a>')
        else:
            parts.append(f'      <div class="award rv">{name}<span>{esc(j["count"])}</span></div>')
    return "review", "Peer Review", "Peer review", "\n".join(parts), True


def s_service(c):
    parts = ['      <div class="grp">Leadership</div>']
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


def slug(t):
    return "x-" + (re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-") or "section")


def s_extra(e):
    parts = []
    if e.get("intro"):
        parts.append(f'      <p class="statement rv" style="margin-bottom:34px">{inline(e["intro"], "em")}</p>')
    for x in e.get("items", []):
        who = " · ".join(v for v in (x.get("org"), x.get("place")) if v)
        link = ""
        if x.get("link"):
            link = f'\n        <p><a class="doi" href="{attr(x["link"])}" target="_blank" rel="noopener">{esc(x.get("link_label") or "Read")}</a></p>'
        parts.append(f'      <div class="item rv"><div class="when">{esc(get(x, "dates"))}</div><div>\n        <h3>{inline(x["title"], "em")}</h3>'
                     + (f'<div class="who">{esc(who)}</div>' if who else "")
                     + (f'\n        <p>{inline(x["text"])}</p>' if x.get("text") else "") + link + "</div></div>")
    return slug(e["title"]), esc(e["title"]), esc(e["title"]), "\n".join(parts), False


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
    if c.get("peer_review"):
        secs.append(s_review(c))
    if c.get("teaching"):
        secs.append(s_teaching(c))
    if c.get("methods"):
        secs.append(s_methods(c))
    if c.get("leadership"):
        secs.append(s_service(c))
    if c.get("languages"):
        secs.append(s_languages(c))
    if c.get("honors"):
        secs.append(s_honors(c))
    for e in c.get("extra_sections", []):
        if e.get("site", True) is not False:
            secs.append(s_extra(e))

    used = set()
    for n, sc in enumerate(secs):
        sid = sc[0]
        while sid in used:
            sid += "-2"
        used.add(sid)
        secs[n] = (sid,) + tuple(sc[1:])
    main = []
    for n, (sid, label_html, _short, body, tight) in enumerate(secs[:24]):
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
    topics_js = json.dumps([["all", "All topics"]] + [[t["key"], t["label"]] for t in c.get("topics", [])], ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

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
PAGE_DESC = {
    "research.html": "Research by {name}: validity and fairness in automated speaking assessment, explainable machine learning for L2 pronunciation, multilingual learners and policy, and generative AI in education.",
    "publications.html": "Journal articles, preprints, manuscripts in review and talks by {name}.",
    "teaching.html": "Courses {name} has taught at the University of Kansas since 2023, and earlier English teaching in Iran.",
    "service.html": "Peer review and leadership service by {name}.",
}


def page_head(c, page, ttl):
    """The <head> meta for one page: title, description, canonical link, share card and (home only) structured data."""
    p, seo = c["person"], c.get("seo", {})
    full = own_name(c)
    base = p["site_url"] if p["site_url"].endswith("/") else p["site_url"] + "/"
    home = page == "index.html"
    url = base if home else base + page
    title = seo["title"] if home else f"{ttl} | {full}"
    desc = seo["description"] if home else PAGE_DESC.get(page, seo["description"]).format(name=full)
    share_alt = get(seo, "share_alt", full)
    out = f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{attr(desc)}">
<meta property="og:title" content="{attr(full if home else title)}">
<meta property="og:description" content="{attr(get(seo, "share_text", seo["description"]) if home else desc)}">
<meta property="og:type" content="{"profile" if home else "website"}">
<meta property="og:image" content="{attr(base)}og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{attr(share_alt)}">
<meta property="og:url" content="{attr(url)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="{attr(full)}">
<link rel="canonical" href="{attr(url)}">
<meta name="color-scheme" content="light dark">'''
    if home:
        ld = {"@context": "https://schema.org", "@type": "Person", "name": full, "url": base}
        if seo.get("job_title"):
            ld["jobTitle"] = seo["job_title"]
        ld["affiliation"] = {"@type": "CollegeOrUniversity", "name": p["institution"]}
        if seo.get("alumni_of"):
            ld["alumniOf"] = [{"@type": "CollegeOrUniversity", "name": a} for a in seo["alumni_of"]]
        if seo.get("knows_about"):
            ld["knowsAbout"] = seo["knows_about"]
        ld["sameAs"] = [x for x in (p.get("linkedin"), p.get("scholar"), ("https://orcid.org/" + p["orcid"]) if p.get("orcid") else None) if x]
        ld["email"] = "mailto:" + p["email"]
        ld["worksFor"] = {"@type": "CollegeOrUniversity", "name": p["institution"]}
        ld["image"] = base + p.get("portrait", "portrait.jpg")
        out += '\n<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "\n</script>"
    return out


def small_portrait(c):
    """A small copy of the portrait for the home page (the full file is kept for the CV, share card and search data)."""
    src = ROOT / c["person"].get("portrait", "portrait.jpg")
    out = ROOT / "assets" / "img" / "portrait-sm.jpg"
    if src.exists() and (not out.exists() or out.stat().st_mtime < src.stat().st_mtime):
        try:
            subprocess.run(["sips", "-Z", "320", "-s", "format", "jpeg", "-s", "formatOptions", "82", str(src), "--out", str(out)],
                           capture_output=True, check=True)
        except Exception:
            shutil.copy(src, out)                   # not on a Mac: fall back to the full-size photo
    return "assets/img/portrait-sm.jpg" if out.exists() else src.name


def build_pages(c, today):
    """The website: index, research, publications, teaching and service pages. The design lives in builder/web."""
    web = BUILDER / "web"
    g = {"C": c, "CITES": cite_records(c), "UPDATED": month_year(today), "TODAY": today, "PORTRAIT_SM": small_portrait(c),
         "HEAD": lambda page, ttl: page_head(c, page, ttl), "HERE": str(web), "ROOT": str(ROOT), "__name__": "pages"}
    try:
        exec(compile((web / "pages.py").read_text(encoding="utf-8"), str(web / "pages.py"), "exec"), g)
    except Exception as e:                          # say where it broke, so a code problem is not mistaken for a typo
        import traceback
        frames = [f for f in traceback.extract_tb(e.__traceback__) if "builder" in f.filename or f.filename == "<string>"]
        where = f" ({Path(frames[-1].filename).name}, line {frames[-1].lineno}, in {frames[-1].name})" if frames else ""
        raise ContentError(f"The website pages could not be built: {type(e).__name__}: {e}{where}.\n"
                           "This usually means an entry in content.toml is missing a field the page code expects "
                           "(for example an id or a strand), or a problem in builder/web. Undo your last edit and build again, "
                           "or ask for help. Nothing was published.")
    return g["OUT_PAGES"]


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


def cv_pub_parts(x):
    """The venue line of a CV publication as plain text: (italic part, text after it, doi or None)."""
    if x["status"] == "published":
        v = x["venue"] if x.get("venue") else x["venue_text"]
        if x.get("volume"):
            v += ", " + x["volume"] + (f'({x["issue"]})' if x.get("issue") else "")
        if x.get("pages"):
            v += ", " + x["pages"]
        elif x.get("article"):
            v += ", " + x["article"]
        return v, f". {x['year']}", x.get("doi")
    if x["status"] == "review":
        return (x.get("venue") or x.get("venue_text")), f'. {x.get("cv_status") or x.get("label") or "Under review"}', None
    if x.get("venue_text"):
        return x["venue_text"], ("" if x.get("doi") else f". {x['year']}"), x.get("doi")
    return x["venue"], f'. {x["year"]}; {x.get("cv_note") or "Preprint"}', x.get("doi")


def cv_review_text(pr):
    if pr.get("cv_summary"):
        return pr["cv_summary"]
    total = review_total(pr)
    n = len(pr.get("journals", []))
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
    where = f"{words.get(n, n)} journal{'s' if n != 1 else ''}" if n else "peer-reviewed journals"
    return (total + " " if total else "") + f"manuscript reviews for {where}, {cv_dates(pr['dates'])}."


MONTHS = {"January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr", "June": "Jun", "July": "Jul",
          "August": "Aug", "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"}


def gutter_text(s):
    """A date for the CV's left column, with short months."""
    s = cv_dates(s or "")
    for k, v in MONTHS.items():
        s = s.replace(k, v)
    return s


def gutter_date(s):
    """gutter_text as HTML, with a line break allowed after the hyphen."""
    return esc(gutter_text(s)).replace("-", "-<wbr>")


def cv_row(gut, title="", org="", text="", cls=""):
    """One CV line: the date (or year, or code) on the left, the entry on the right."""
    body = f'<div class="t">{title}</div>' if title else ""
    if org:
        body += f'<div class="o">{org}</div>'
    if text:
        body += "".join(f'<div class="x">{t}</div>' for t in text.split("\n"))
    return f'<div class="row{(" " + cls) if cls else ""}"><div class="g">{gut}</div><div class="b">{body}</div></div>'


def stop(t):
    """End a title with a full stop unless it already ends with ? or !."""
    return t if t.rstrip("”’\"'").endswith(("?", "!", ".")) else t + "."


def org_place(x):
    return ", ".join(esc(v) for v in (get(x, "org"), get(x, "place")) if v)


# ----------------------------------------------------------------------------- APA 7 references for the CV
def seg(t, i=False, b=False, u=None):
    return {"t": t, "i": i, "b": b, "u": u}


def seg_md(t):
    """Pieces for text with *italic* markers."""
    return [seg(part, i=bool(k % 2)) for k, part in enumerate(re.split(r"\*(.+?)\*", t)) if part]


def curly(t):
    """Straight double quotes to curly ones."""
    out, open_q = [], True
    for ch in t:
        if ch == '"':
            out.append("“" if open_q else "”")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out).replace("'", "’")


def apa_initials(given):
    return " ".join("-".join(x[0].upper() + "." for x in t.split("-") if x) for t in given.split() if "/" not in t)


def apa_author_segs(authors, c):
    fam0, giv0 = c["person"]["last_name"], c["person"]["first_name"]
    names = []
    for a in authors:
        _, fam, giv = split_author(a)
        names.append(seg(f"{fam}, {apa_initials(giv)}", b=(fam == fam0 and giv.startswith(giv0))))
    out = []
    for k, n in enumerate(names):
        if k:
            out.append(seg(", & " if k == len(names) - 1 else ", "))
        out.append(n)
    return out


def apa_title_stop(t):
    return t if t.rstrip("”’\"'").endswith(("?", "!", ".")) else t + "."


def apa_doi(doi):
    return [seg(" "), seg("https://doi.org/" + doi, u="https://doi.org/" + doi)]


def apa_pub(x, c):
    """One publication as an APA 7 reference (journal article, submitted manuscript, preprint or software)."""
    out = apa_author_segs(x["authors"], c) + [seg(f' ({x["year"]}). ')]
    title = curly(x.get("apa_title") or x.get("cite_title") or plain(x["title"]))
    grp = x.get("cv_group") or x["status"]
    if grp == "published":
        out.append(seg(apa_title_stop(title) + " "))
        out.append(seg(x.get("venue") or x.get("venue_text"), i=True))
        if x.get("volume"):
            out += [seg(", "), seg(x["volume"], i=True)] + ([seg(f'({x["issue"]})')] if x.get("issue") else [])
        if x.get("pages"):
            out.append(seg(", " + x["pages"].replace("-", "–")))
        elif x.get("article"):
            out.append(seg(", Article " + x["article"]))
        out.append(seg("."))
        if x.get("online") and not x.get("volume"):
            out.append(seg(" Advance online publication."))
    elif grp == "review":
        out += [seg(title, i=True), seg(" [Manuscript submitted for publication]. ")]
        out += seg_md(x.get("cv_apa") or f'Under review at *{x.get("venue") or x.get("venue_text")}*')
        if not out[-1]["t"].endswith((".", ":")):
            out.append(seg("."))
    elif x.get("kind") == "artifact":
        out += [seg(title, i=True), seg(" [Computer software]. Zenodo.")]
    else:
        lab = x.get("label", "")
        m = re.search(r"under review at (.+)$", lab)
        out += [seg(title, i=True), seg(" [Preprint")]
        if m:
            out += [seg("; under review at "), seg(m.group(1), i=True)]
        out.append(seg(f'].  {x["venue"]}.'.replace("].  ", "]. ")))
    if x.get("doi"):
        out += apa_doi(x["doi"])
    if x.get("osf"):
        out += [seg(" (method registration: "), seg("https://doi.org/" + x["osf"], u="https://doi.org/" + x["osf"]), seg(")")]
    return out


def apa_report(x, c):
    out = apa_author_segs(x["authors"], c) + [seg(f' ({x["year"]}). ')]
    out += [seg(curly(x.get("cite_title") or x["title"]), i=True), seg(f' [{x.get("kind", "Report")}]. {x["publisher"]}.')]
    if x.get("url"):
        out += [seg(" "), seg(x["url"], u=x["url"])]
    return out


def apa_talk(x, c):
    """A conference presentation in APA 7: authors (year, month day). Title [format]. Conference, City, ST, United States."""
    if x.get("cite_authors"):
        authors = x["cite_authors"]
    else:
        authors = [own_name(c)] + [n.strip() for n in re.split(r",\s*|\s+and\s+", x.get("coauthors", "")) if n.strip()]
    if x.get("cite_date") and x.get("cite_year"):
        when = f'{x["cite_year"]}, {x["cite_date"]}'
    else:
        m = re.match(r"(\w+)(?: ([\d-]+))?,? (\d{4})$", x.get("cv_date") or "")
        when = f'{m.group(3)}, {m.group(1)}' + (f' {m.group(2).replace("-", "–")}' if m.group(2) else "") if m else str(x.get("date", ""))
    title = curly(x.get("apa_title") or x.get("cite_title") or x["title"])
    event = x.get("event") or (x.get("cv_event") or x.get("site_venue", "")).partition(". ")[0]
    place = x.get("place", "")
    if re.search(r", [A-Z]{2}$", place):
        place += ", United States"
    out = apa_author_segs(authors, c) + [seg(f" ({when}). "), seg(title, i=True),
                                          seg(f' [{x.get("apa_format") or x.get("cite_format") or "Conference presentation"}]. {event}' + (f", {place}" if place else "") + ".")]
    if x.get("doi") and x.get("cite_title"):
        out += apa_doi(x["doi"])
    return out


def segs_html(segs):
    out = []
    for g in segs:
        t = esc(g["t"])
        if g["i"]:
            t = f"<i>{t}</i>"
        if g["b"]:
            t = f"<b>{t}</b>"
        if g["u"]:
            t = f'<a href="{attr(g["u"])}">{t}</a>'
        out.append(t)
    return "".join(out)


def segs_docx(d, segs, sz=10):
    return [d.run(g["t"], i=g["i"], b=g["b"], sz=sz, color=NAVY if g["u"] else None, link=g["u"]) for g in segs]


def honor_parts(h):
    """(name, giver, year) for one honor; the year comes off the end of the note."""
    note = (h.get("cv_note") or h.get("note") or "").replace("  |  ", ", ").replace(" · ", ", ")
    m = re.search(r",?\s*\b((?:19|20)\d\d)\s*$", note)
    return h["name"], (note[:m.start()] if m else note).strip(), (m.group(1) if m else "")


def method_items(m):
    items = []
    for it in m.get("items", []):
        if "|" in it:
            a, b = it.split("|", 1)
            items.append(f"{a.strip()} ({b.strip()})")
        else:
            items.append(lowfirst(it))
    out = human_join(items)
    return out[:1].upper() + out[1:]


def cv_pub_groups(c):
    """The CV's publication groups, in order: (heading, list of pieces per reference)."""
    pubs = sorted_pubs(c)
    groups = []
    for st, head in (("published", "Peer-Reviewed Journal Articles"), ("review", "Manuscripts in Review"),
                     ("preprint", "Preprints and Research Artifacts")):
        items = [x for x in pubs if (x.get("cv_group") or x["status"]) == st and x.get("cv_section") != "other"]
        items.sort(key=lambda x: not x.get("cv_first"))        # stable: cv_first entries move to the top
        if items:
            groups.append((head, [apa_pub(x, c) for x in items]))
    if c.get("reports"):
        groups.append(("Reports and White Papers", [apa_report(x, c) for x in c["reports"]]))
    others = [x for x in pubs if x.get("cv_section") == "other"]
    if others:
        groups.append((c.get("cv", {}).get("other_publications_heading", "Other Publications"), [apa_pub(x, c) for x in others]))
    return groups


def cv_body(c, today):
    p, cv = c["person"], c.get("cv", {})
    own = own_name(c)
    out = []

    # ---- header: name and title on the left, contact on the right
    lines, profiles = [], []
    for it in cv.get("contact_line", []):
        low = it.lower()
        if "@" in it:
            lines.append(f'<a href="mailto:{attr(it)}">{esc(it)}</a>')
        elif low.startswith("linkedin") and p.get("linkedin"):
            profiles.append(f'<a href="{attr(p["linkedin"])}">LinkedIn</a>')
        elif "scholar" in low and p.get("scholar"):
            profiles.append(f'<a href="{attr(p["scholar"])}">{esc(it)}</a>')
        elif low.startswith("orcid") and p.get("orcid"):
            profiles.append(f'<a href="https://orcid.org/{attr(p["orcid"])}">{esc(it)}</a>')
        elif p.get("site_url") and it.rstrip("/") in p["site_url"]:
            lines.append(f'<a href="{attr(p["site_url"])}">{esc(it)}</a>')
        else:
            lines.append(esc(it))
    if profiles:
        lines.append(" &nbsp;|&nbsp; ".join(profiles))
    out.append(f'<header class="top"><div class="head-l"><h1>{esc(own)}</h1>'
               f'<div class="sub">{esc(cv.get("headline") or get(cv, "subtitle"))}</div></div>'
               f'<div class="head-r">{"<br>".join(lines)}</div></header>')

    if cv.get("research_interests"):
        out.append(f'<h2>Research Interests</h2><p class="lede">{inline(cv["research_interests"])}</p>')

    def appt(x):
        return cv_row(gutter_date(x.get("cv_dates") or x["dates"]), esc(plain(x.get("cv_title") or x["title"])), org_place(x),
                      inline(x.get("cv_text") or get(x, "text")))
    if c.get("education"):
        out.append("<h2>Education</h2>" + "".join(appt(x) for x in c["education"]))
    academic = [x for x in c.get("appointments", []) if not x.get("cv_section")]
    if academic:
        out.append("<h2>Academic Appointments</h2>" + "".join(appt(x) for x in academic))

    # ---- publications and presentations, in APA 7
    groups = cv_pub_groups(c)
    if groups:
        out.append("<h2>Publications</h2>")
    for head, refs in groups:
        out.append(f"<h3>{esc(head)}</h3>" + "".join(f'<p class="apa">{segs_html(r)}</p>' for r in refs))
    if c.get("presentations"):
        out.append("<h2>Conference Presentations</h2>" + "".join(f'<p class="apa">{segs_html(apa_talk(x, c))}</p>' for x in c["presentations"]))

    if c.get("projects"):
        out.append("<h2>Research Projects</h2>" + "".join(
            cv_row(gutter_date(x["dates"]), esc(plain(x.get("cv_title") or x["title"])), esc(get(x, "org")), inline(x.get("cv_text") or get(x, "text")))
            for x in c["projects"]))

    # ---- teaching: KU courses, then Iran
    iran = [x for x in c.get("appointments", []) if x.get("cv_section") == "teaching_iran"]
    if c.get("teaching") or iran:
        out.append("<h2>Teaching Experience</h2>")
    if c.get("teaching"):
        if cv.get("teaching_header"):
            out.append(f'<h3>{esc(cv["teaching_header"])}</h3>')
        role_shown = set()
        for g in c["teaching"]:
            ta = g["group"] == "Teaching Assistant"
            role = cv.get("teaching_ta" if ta else "teaching_ior")
            if role and id(role) not in role_shown:
                role_shown.add(id(role))
                out.append(cv_row(gutter_date(role.get("dates", "")), esc(role["title"]), esc(role.get("org", "")), inline(role.get("text", "")), "role"))
            if not (ta and role):
                out.append(f'<h4>{esc(g["group"])} courses</h4>' if g["group"] in ("Graduate", "Undergraduate") else f'<h4>{esc(g["group"])}</h4>')
            for k in g.get("courses", []):
                terms = k.get("cv_terms") or cv_dates(k.get("terms", "")).replace(" · ", "; ").replace("\n", " ")
                note = k.get("cv_detail") or k.get("cv_practicum")
                out.append(f'<div class="row crs"><div class="g">{esc(k["code"])}</div><div class="b"><div class="ln"><span>{esc(k.get("cv_title") or k["title"])}</span>'
                           f'<span class="tm">{esc(terms)}</span></div>' + (f'<div class="nt">{esc(note)}</div>' if note else "") + "</div></div>")
    if iran:
        out.append(f'<h3>{esc(cv.get("iran_teaching_heading_short", "English Language Teaching, Iran"))}</h3>' + "".join(appt(x) for x in iran))

    # ---- service: peer review and leadership
    pr = c.get("peer_review")
    if pr or c.get("leadership"):
        out.append("<h2>Service</h2>")
    if pr:
        js = ", ".join(f'<i>{esc(j["name"])}</i> ({esc(j["count"].split()[0])})' for j in pr.get("journals", []))
        total = review_total(pr)
        n = len(pr.get("journals", []))
        words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
        lead = f'{total} manuscript reviews for {words.get(n, n)} journals: ' if total else ""
        out.append("<h3>Peer Review</h3>" + cv_row(gutter_date(pr["dates"]), esc(pr.get("cv_role") or pr["role"]), "", lead + js + "."))
        for x in pr.get("conferences", []):
            out.append(cv_row(gutter_date(x.get("date", "")), esc(f'{x.get("role", "Proposal reviewer").title()}, {x["name"]}'), esc(get(x, "org"))))
    if c.get("leadership"):
        out.append("<h3>Leadership</h3>" + "".join(
            cv_row(gutter_date(x["dates"]), esc(x.get("cv_role") or x["role"]), ", ".join(esc(v) for v in (x.get("cv_org") or x.get("org", ""), get(x, "place")) if v),
                   esc(get(x, "text")))
            for x in c["leadership"]))

    # ---- undated sections: a short label on the left instead of a date
    def lab_row(label, body):
        return f'<div class="row lab"><div class="g">{label}</div><div class="b">{body}</div></div>'
    if c.get("honors"):
        rows = []
        for h in c["honors"]:
            name, org, yr = honor_parts(h)
            rows.append(f'<div class="hn"><span><b>{esc(name)}</b>{", " + esc(org) if org else ""}</span><span class="tm">{yr}</span></div>')
        out.append('<h2>Awards and Honors</h2><div class="hon">' + "".join(rows) + "</div>")
    if c.get("methods") or cv.get("methodological_training"):
        out.append("<h2>Research Methods and Training</h2>")
    for m in c.get("methods", []):
        out.append(f'<p class="plain"><b>{esc(m.get("cv_title") or m["title"])}:</b> {esc(lowfirst(method_items(m)))}.</p>')
    if cv.get("methodological_training"):
        out.append("<h3>Graduate Methods Coursework</h3>" + "".join(
            f'<p class="plain"><b>{esc(m["label"])}:</b> {esc(m["text"])}</p>' for m in cv["methodological_training"]))

    for e in c.get("extra_sections", []):
        if e.get("cv", True) is False or not e.get("items"):
            continue
        out.append(f"<h2>{esc(e.get('cv_title') or e['title'])}</h2>" + "".join(appt(x) for x in e["items"]))
    if c.get("languages"):
        out.append("<h2>Languages</h2>" + "".join(lab_row(esc(l["name"]), esc(l.get("cv_level") or l["level"])) for l in c["languages"]))
    return "\n".join(out)

NAVY, GRAY = "1F4E79", "5C6975"


def rich(d, s, **kw):
    """Runs for text with *italic* markers."""
    out = []
    for k, part in enumerate(re.split(r"\*(.+?)\*", str(s))):
        if part:
            out.append(d.run(part, **{**kw, "i": True if k % 2 else kw.get("i", False)}))
    return out


def docx_author_runs(d, authors, own):
    names = [split_author(a)[0] for a in authors]
    runs = []
    for k, n in enumerate(names):
        if k:
            runs.append(d.run(" & " if (len(names) == 2) else (", & " if k == len(names) - 1 else ", ")))
        runs.append(d.run(n, b=(n == own)))
    return runs


def build_docx(c, today, path):
    """The Word CV, in the same layout as the PDF: dates on the left, entries on the right."""
    d = Doc(10166)
    p, cv = c["person"], c.get("cv", {})
    own = own_name(c)
    GUT, BODY = 1720, 10166 - 1720

    def h2(text):
        d.para([d.run(text, b=True, caps=True, color=NAVY, sz=10.5, sp=19)], before=200, after=100, border=True, border_sz=5, keep_next=True)

    def h3(text, before=150):
        d.para([d.run(text, b=True, color=NAVY)], left=GUT, before=before, after=70, keep_next=True)

    def h4(text):
        d.para([d.run(text, i=True, color=GRAY, sz=9.5)], left=GUT, before=110, after=50, keep_next=True)

    def lines(body, runs):
        return body + ([d.br()] if body else []) + runs

    def row(gut, title="", org="", text="", runs=None, after=80, keep=False):
        body = []
        if title:
            body = [d.run(title, b=True)]
        if org:
            body = lines(body, [d.run(org, i=True, color=GRAY, sz=9.5)])
        for t in (text.split("\n") if text else []):
            body = lines(body, rich(d, t))
        if runs:
            body = lines(body, runs)
        d.table([([([d.run(gut, color=GRAY, sz=9.5)], None), (body, None)], after)], [GUT, BODY], keep_next=keep)

    def place(x):
        return ", ".join(v for v in (get(x, "org"), get(x, "place")) if v)

    def appt(x):
        row(gutter_text(x.get("cv_dates") or x["dates"]), plain(x.get("cv_title") or x["title"]), place(x), x.get("cv_text") or get(x, "text"))

    # ---- header: name and title on the left, contact on the right
    right, profiles = [], []
    for it in cv.get("contact_line", []):
        low = it.lower()
        if "@" in it:
            right.append(d.run(it, color=GRAY, sz=9.5, link="mailto:" + it))
        elif low.startswith("linkedin") and p.get("linkedin"):
            profiles.append(d.run("LinkedIn", color=GRAY, sz=9.5, link=p["linkedin"]))
        elif "scholar" in low and p.get("scholar"):
            profiles.append(d.run(it, color=GRAY, sz=9.5, link=p["scholar"]))
        elif low.startswith("orcid") and p.get("orcid"):
            profiles.append(d.run(it, color=GRAY, sz=9.5, link="https://orcid.org/" + p["orcid"]))
        elif p.get("site_url") and it.rstrip("/") in p["site_url"]:
            right.append(d.run(it, color=GRAY, sz=9.5, link=p["site_url"]))
        else:
            right.append(d.run(it, color=GRAY, sz=9.5))
    rr = []
    for k, r in enumerate(right):
        rr += ([d.br()] if k else []) + [r]
    if profiles:
        prof = []
        for k, r in enumerate(profiles):
            prof += ([d.run("  |  ", color=GRAY, sz=9.5)] if k else []) + [r]
        rr += [d.br()] + prof
    left = [d.run(own, b=True, color=NAVY, sz=25), d.br(), d.run(cv.get("headline") or get(cv, "subtitle"), sz=10.5)]
    d.table([([(left, None), (rr, "right")], 0)], [7166, 3000])
    d.para([d.run("", sz=4)], border=True, border_color=NAVY, border_sz=12, after=60)

    if cv.get("research_interests"):
        h2("Research Interests")
        d.para(rich(d, cv["research_interests"]), left=GUT, after=60)
    if c.get("education"):
        h2("Education")
        for x in c["education"]:
            appt(x)
    academic = [x for x in c.get("appointments", []) if not x.get("cv_section")]
    if academic:
        h2("Academic Appointments")
        for x in academic:
            appt(x)

    # ---- publications and presentations, in APA 7
    def apa_para(segs):
        d.para(segs_docx(d, segs), left=GUT + 360, hanging=360, after=80, keep_lines=True)
    groups = cv_pub_groups(c)
    if groups:
        h2("Publications")
    for k, (head, refs) in enumerate(groups):
        h3(head, before=20 if k == 0 else 150)
        for r in refs:
            apa_para(r)
    if c.get("presentations"):
        h2("Conference Presentations")
        for x in c["presentations"]:
            apa_para(apa_talk(x, c))

    if c.get("projects"):
        h2("Research Projects")
        for x in c["projects"]:
            row(gutter_text(x["dates"]), plain(x.get("cv_title") or x["title"]), get(x, "org"), x.get("cv_text") or get(x, "text"))

    # ---- teaching
    iran = [x for x in c.get("appointments", []) if x.get("cv_section") == "teaching_iran"]
    if c.get("teaching") or iran:
        h2("Teaching Experience")
    if c.get("teaching"):
        if cv.get("teaching_header"):
            h3(cv["teaching_header"], before=20)
        role_shown = set()
        for g in c["teaching"]:
            ta = g["group"] == "Teaching Assistant"
            role = cv.get("teaching_ta" if ta else "teaching_ior")
            if role and id(role) not in role_shown:
                role_shown.add(id(role))
                if ta:
                    d.para([d.run("", sz=4)], after=80)
                row(gutter_text(role.get("dates", "")), role["title"], role.get("org", ""), role.get("text", ""), after=40 if not ta else 80, keep=True)
            if not (ta and role):
                h4(f'{g["group"]} courses' if g["group"] in ("Graduate", "Undergraduate") else g["group"])
            for k in g.get("courses", []):
                terms = k.get("cv_terms") or cv_dates(k.get("terms", "")).replace(" · ", "; ").replace("\n", " ")
                note = k.get("cv_detail") or k.get("cv_practicum")
                mid = [d.run(k.get("cv_title") or k["title"])] + ([d.br(), d.run(note, color=GRAY, sz=9.5)] if note else [])
                d.table([([([d.run(k["code"], b=True, color="3C4650", sz=9.5)], None), (mid, None), ([d.run(terms, color=GRAY, sz=9.5)], "right")], 60)],
                        [GUT, BODY - 3000, 3000])
    if iran:
        h3(cv.get("iran_teaching_heading_short", "English Language Teaching, Iran"))
        for x in iran:
            appt(x)

    # ---- service
    pr = c.get("peer_review")
    if pr or c.get("leadership"):
        h2("Service")
    if pr:
        h3("Peer Review", before=20)
        total = review_total(pr)
        n = len(pr.get("journals", []))
        words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
        runs = [d.run(f'{total} manuscript reviews for {words.get(n, n)} journals: ' if total else "")]
        for k, j in enumerate(pr.get("journals", [])):
            runs += ([d.run(", ")] if k else []) + [d.run(j["name"], i=True), d.run(f' ({j["count"].split()[0]})')]
        runs.append(d.run("."))
        row(gutter_text(pr["dates"]), pr.get("cv_role") or pr["role"], runs=runs)
        for x in pr.get("conferences", []):
            row(gutter_text(x.get("date", "")), f'{x.get("role", "Proposal reviewer").title()}, {x["name"]}', get(x, "org"))
    if c.get("leadership"):
        h3("Leadership")
        for x in c["leadership"]:
            row(gutter_text(x["dates"]), x.get("cv_role") or x["role"],
                ", ".join(v for v in (x.get("cv_org") or x.get("org", ""), get(x, "place")) if v), get(x, "text"))

    # ---- undated sections: a short label on the left instead of a date
    def lab_row(label, runs, after=60):
        d.table([([([d.run(label, b=True, color="3C4650", sz=9.5)], None), (runs, None)], after)], [GUT, BODY])
    if c.get("honors"):
        h2("Awards and Honors")
        for h in c["honors"]:
            name, org, yr = honor_parts(h)
            d.table([([([], None), ([d.run(name, b=True)] + ([d.run(", " + org)] if org else []), None),
                       ([d.run(yr, color=GRAY, sz=9.5)], "right")], 30)], [GUT, BODY - 900, 900])
    if c.get("methods") or cv.get("methodological_training"):
        h2("Research Methods and Training")
    for m in c.get("methods", []):
        d.para([d.run((m.get("cv_title") or m["title"]) + ":", b=True), d.run(" " + lowfirst(method_items(m)) + ".")], left=GUT, after=60, keep_lines=True)
    if cv.get("methodological_training"):
        h3("Graduate Methods Coursework")
        for m in cv["methodological_training"]:
            d.para([d.run(m["label"] + ":", b=True), d.run(" " + m["text"])], left=GUT, after=60, keep_lines=True)

    for e in c.get("extra_sections", []):
        if e.get("cv", True) is False or not e.get("items"):
            continue
        h2(e.get("cv_title") or e["title"])
        for x in e["items"]:
            appt(x)
    if c.get("languages"):
        h2("Languages")
        for l in c["languages"]:
            lab_row(l["name"], [d.run(l.get("cv_level") or l["level"])], after=30)
        d.para([d.run("", sz=1)], line=24)              # Word needs a paragraph after a final table; keep it tiny so it never starts a page
    foot = f"{own} | Academic Curriculum Vitae | Updated {month_year(today)} | Page "
    return d.save(path, f"{own}, Curriculum Vitae", own, d.run(foot, color=GRAY, sz=9))

def build_cv_html(c, today):
    tpl = (BUILDER / "cv.html").read_text(encoding="utf-8")
    full = own_name(c)
    foot = f"{full} | Academic Curriculum Vitae | Updated {month_year(today)} | Page "
    foot = foot.replace("\\", "\\\\").replace('"', '\\"')
    return (tpl.replace("@@TITLE@@", esc(f"{full}, Curriculum Vitae")).replace("@@AUTHOR@@", attr(full))
            .replace("@@FOOTER@@", foot).replace("@@BODY@@", cv_body(c, today)))


def build_og_html(c):
    """The share card shown when the site is posted on social media or in chats (og.jpg), in the website's style."""
    p = c["person"]
    tpl = (BUILDER / "og.html").read_text(encoding="utf-8")
    url = p["site_url"].replace("https://", "").rstrip("/")
    return (tpl.replace("@@PORTRAIT@@", (ROOT / p.get("portrait", "portrait.jpg")).as_uri()).replace("@@NAME@@", esc(own_name(c)))
            .replace("@@ROLE@@", esc(f'{p["status"]}, {p["institution"]}')).replace("@@LINE@@", inline(get(p, "tagline"), "em"))
            .replace("@@URL@@", esc(url)))


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


def make_docx(c, today, say):
    tmp = ROOT / "_cv_tmp.docx"
    try:
        doc_xml = build_docx(c, today, tmp)
        digest = hashlib.sha256(doc_xml.encode()).hexdigest()
        if stamp_ok("docx", digest, [CV_DOCX]):
            say("  CV Word file: nothing changed, kept the existing file")
            return
        minidom.parseString(doc_xml)  # raises if the document is malformed
        shutil.move(str(tmp), ROOT / CV_DOCX)
        stamp_write("docx", digest)
        say("  CV Word file: made")
    finally:
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
        chrome([f"--screenshot={png}", "--window-size=1200,630", "--default-background-color=ffffffff", "--virtual-time-budget=6000", src.as_uri()], png)
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
        c = normalize(load())
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
        pages = build_pages(c, today)
        for name, page in pages.items():
            (ROOT / name).write_text(page, encoding="utf-8")
        say("  Website (" + ", ".join(pages) + "): made")
        site = c["person"]["site_url"] if c["person"]["site_url"].endswith("/") else c["person"]["site_url"] + "/"
        stamp = datetime.date.today().isoformat()
        (ROOT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f'  <url>\n    <loc>{esc(site if n == "index.html" else site + n)}</loc>\n    <lastmod>{stamp}</lastmod>\n  </url>\n' for n in pages if n != "404.html")
            + '</urlset>\n', encoding="utf-8")
        if not no_pdf:
            make_pdf(c, today, say)
            make_docx(c, today, say)
            make_og(c, say)
        say("\nDone.")
        return 0
    except ContentError as e:
        say("\n" + str(e))
        return 1
    except KeyError as e:
        say(f"\nA required field is missing in content.toml: {e}. Check the entry you edited last.")
        return 1
    except Exception as e:  # never show a wall of code to a non-programmer
        say(f"\nSomething in content.toml could not be understood ({type(e).__name__}: {e}).\n"
            "Undo your last edit (or compare with the previous version) and build again. Nothing was published.")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
