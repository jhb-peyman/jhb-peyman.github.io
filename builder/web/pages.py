# Website pages (index, research, publications, teaching, service).
# build.py runs this file with these names already set:
#   C (content.toml), CITES (citation records), UPDATED ("November 2026"), HEAD(page, title) -> <head> meta,
#   HERE (this folder), ROOT (the repo). It leaves the finished pages in OUT_PAGES = {filename: html}.
# Edit the words in content.toml; edit this folder only to change the design.
import html, re, json, os, hashlib

P = C['person']
ME = f"{P['first_name']} {P['last_name']}"
FA = open(os.path.join(HERE, 'name-fa.svg'), encoding='utf-8').read()
FA = re.sub(r'\swidth="\d+"\sheight="\d+"', '', FA, count=1).replace('<svg ', '<svg class="fa" ', 1)

def esc(s): return html.escape(s, quote=False)
def md(s): return re.sub(r"\*(.+?)\*", r"<em>\1</em>", esc(s))
def plain(s): return s.replace('*', '')
def attr(s): return html.escape(s, quote=True)
def h2(t): return f'<h2>{t}</h2>'
def title(t): return f'<h1 class="pt">{t}</h1>'
def kv(rows): return '<table class="kv">' + ''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in rows) + '</table>'

ICON = {
 'mail': '<path d="M3 6h18v12H3z"/><path d="m3 7 9 6 9-6"/>',
 'cv': '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h7"/>',
 'scholar': '<path d="m2 9 10-5 10 5-10 5z"/><path d="M6 11v5c3 2 9 2 12 0v-5"/>',
 'in': '<path d="M4 9h3v11H4zM5.5 4.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zM10 9h3v1.6c.6-1 1.8-1.8 3.5-1.8 2.6 0 3.5 1.7 3.5 4.5V20h-3v-6c0-1.5-.4-2.6-1.9-2.6S13 12.6 13 14v6h-3z"/>',
 'down': '<path d="M12 4v11m-4.5-4.5L12 15l4.5-4.5M5 19h14"/>',
 'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/>',
 'moon': '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
 'mic': '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7"/>',
}
def ic(k, fill=False):
    st = 'fill="currentColor" stroke="none"' if fill else 'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"'
    return f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" {st}>{ICON[k]}</svg>'

PAGES = [('research.html', 'Research'), ('publications.html', 'Publications'), ('teaching.html', 'Teaching'), ('service.html', 'Service')]

def shell(page, ttl, body, figs=False, cites=False, anims=False, spectro=False):
    nav = ''.join(f'<a href="{h}"{" aria-current=\"page\"" if h == page else ""}>{t}</a>' for h, t in PAGES)
    nav += f'<a class="cv" href="Peyman_Jahanbin_CV.pdf">CV{ic("down")}</a>'
    cj = f'<script type="application/json" id="cites">{json.dumps(CITES, ensure_ascii=False)}</script>' if cites else ''
    js = ('<script src="assets/figures.js"></script>' if figs or anims else '') + ('<script src="assets/anims.js"></script>' if anims else '') + ('<script src="assets/spectro.js"></script>' if spectro else '')
    return f'''<!doctype html>
<!-- GENERATED FILE. Do not edit this by hand: edit content.toml, then double-click Build.command. -->
<html lang="en"><head>{HEAD404 if page == '404.html' else HEAD(page, ttl)}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%231d6b4a'/%3E%3Ctext x='16' y='22' font-family='monospace' font-size='15' font-weight='700' fill='white' text-anchor='middle'%3EPJ%3C/text%3E%3C/svg%3E">
<script>try{{var t=localStorage.getItem('pj-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Albert+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css"></head><body>
<header class="bar"><div class="bar-in"><a class="brand" href="index.html"{' aria-current="page"' if page == 'index.html' else ''}>{ME}</a>
<nav aria-label="Main">{nav}</nav>
<button class="theme" id="theme" type="button" aria-label="Switch light or dark mode">{ic("moon")}{ic("sun")}</button></div></header>
<main class="page">{body}</main>
<footer class="foot"><span>{ME} · {P['institution']} · <a href="mailto:{P['email']}">{P['email']}</a></span><span>Updated {UPDATED}</span></footer>
<div class="sr" id="live" aria-live="polite"></div>{cj}
<script src="assets/site.js"></script>{js}
</body></html>'''

# ------------------------------------------------------------- publications data
def datekey(p):
    parts = (str(p.get('date', p['year'])).split('-') + ['00', '00'])[:3]
    return '-'.join(x.zfill(2) for x in parts)
PUBS = sorted(C['publications'], key=datekey, reverse=True)
BYID = {p['id']: p for p in PUBS}

def initials(given):
    return ' '.join('-'.join(x[0].upper() + '.' for x in t.split('-')) for t in given.split() if '/' not in t)
def apa_authors(pid, raw):
    names = CITES[pid]['a'] if pid in CITES else [[n.split()[-1], ' '.join(n.split()[:-1])] for n in raw]
    out = []
    for fam, giv in names:
        s = esc(f'{fam}, {initials(giv)}')
        out.append(f'<b>{s}</b>' if fam == P['last_name'] else s)
    if len(out) == 1: return out[0]
    if len(out) == 2: return f'{out[0]}, &amp; {out[1]}'
    return ', '.join(out[:-1]) + ', &amp; ' + out[-1]

def venue(p):
    if p.get('kind') == 'artifact': return ''
    v = f'<i>{esc(p["venue"])}</i>'
    if p['status'] == 'published':
        if p.get('online'): return v + '. Advance online publication.'
        if p.get('volume'): v += f', <i>{esc(p["volume"])}</i>' + (f'({esc(p["issue"])})' if p.get('issue') else '')
        if p.get('pages'): v += f', {esc(p["pages"])}'
        if p.get('article'): v += f', Article {esc(p["article"])}'
    return v + '.'

def kind(p):
    if p.get('kind') == 'artifact': return ['Research artifact']
    if p['status'] == 'published': return ['Journal article']
    if p['status'] == 'review': return ['Manuscript', esc(p.get('label', 'In review'))]
    k = ['Preprint']
    if p.get('label') and 'under review' in p['label']:
        k.append(re.sub(r'.*?under review at (.*)', lambda m: 'Under review at <i>' + m.group(1) + '</i>', esc(p['label'])))
    return k

# Live sketches of each paper's method (anims.js). Papers without a drawable method stay text only.
ANIM = {
  'ethics': ('ethics', 'Bar chart of mean seriousness ratings for seven GenAI behaviours, from the paper'),
  'acoustic': ('gap', 'Line chart of the share of speakers pausing at each of 68 positions, English and Mandarin L1, after the paper\u2019s Fig 1'),
  'lltm': ('lltm', 'Bar chart of the LLTM predictor weights reported in the paper'),
  'corpus': ('hedge', 'Bar chart of hedges per category for native and Malaysian reviewers, from the paper'),
  'audio': ('aar', 'Bar chart of post-test and delayed post-test means for the two groups, from the paper'),
  'arxiv': ('mfcc', 'A speech spectrogram turned frame by frame into 13 MFCCs and averaged into one speaker vector'),
  'rsquare': ('term', 'The steps of the reproducible Python pipeline typed out in a terminal'),
}
THUMB = {'beyond': ('assets/img/tq-thumb.jpg', 'Banner and title of the article in TESOL Quarterly')}
def anim(pid):
    if pid in THUMB:
        img, lab = THUMB[pid]; p = BYID[pid]
        return f'<a class="anim pic" href="https://doi.org/{p["doi"]}"><img src="{img}" alt="{attr(lab)}" loading="lazy"></a>'
    if pid not in ANIM: return ''
    k, lab = ANIM[pid]
    return f'<canvas class="anim" data-anim="{k}" role="img" aria-label="{attr(lab)}"></canvas>'

def pub_li(p, filt=True):
    link = f'https://doi.org/{p["doi"]}' if p.get('doi') else p.get('url', '')
    t = esc(p.get('cite_title') or p['title'])
    t = f'<a class="tl" href="{attr(link)}">{t}</a>' if link else f'<span class="tl">{t}</span>'
    acts = []
    if p.get('doi'): acts.append(f'<a href="https://doi.org/{attr(p["doi"])}">DOI</a>')
    elif p.get('url'): acts.append(f'<a href="{attr(p["url"])}">Article</a>')
    cite = f' data-cite="{p["id"]}"' if p['id'] in CITES and p.get('cite', True) else ''
    meta = f'<div class="meta"><span class="kind">{" · ".join(kind(p))}</span><span class="acts"{cite}>{"".join(acts)}</span></div>'
    extra = f' {esc(p.get("venue_text", ""))}.' if p.get('kind') == 'artifact' else ''
    a = anim(p['id'])
    data = f' data-status="{p["status"]}" data-topics="{" ".join(p.get("topics", []))}"' if filt else ''
    return (f'<li class="pub{" has-anim" if a else ""}"{data}>{a}<div>{apa_authors(p["id"], p["authors"])} ({p["year"]}). {t}. {venue(p)}{extra}{meta}</div></li>')

# ------------------------------------------------------------- pages
def page_home():
    links = [('mail', 'Email', f'mailto:{P["email"]}', False), ('cv', 'CV', 'Peyman_Jahanbin_CV.pdf', False),
             ('scholar', 'Google Scholar', P['scholar'], False), ('in', 'LinkedIn', P['linkedin'], True)]
    lk = ''.join(f'<a href="{attr(u)}">{ic(k, f)}<span>{t}</span></a>' for k, t, u, f in links)
    hero = f'''<section class="hero"><img class="avatar" src="portrait.jpg" alt="Portrait of {ME}">
<div class="hero-r"><div class="names"><h1>{ME}</h1>{FA}</div>
<p class="role">{P['status']} in Curriculum &amp; Instruction (TESOL)<br>{P['institution']}, {esc(P['location'])}</p>
<p class="hook">{md(P['tagline'])}</p>
<div class="hlinks">{lk}</div></div></section>'''
    fig = f'''<figure class="figure spectro"><div class="sp-head"><span class="sp-title">Live spectrogram</span><span class="sp-mode" id="modeS">simulated speech</span>
<button class="sp-mic" id="micS" type="button">{ic("mic")}<span>Try your own voice</span></button></div>
<div class="viz" id="vizS" role="img" aria-label="Animated spectrogram with pitch, formants and word and phone tiers"><canvas id="specS"></canvas><canvas id="ovS" class="ov"></canvas><div class="tip" id="tipS"></div></div>
<figcaption id="statS"><span class="lg"><i class="lg-f0"></i>pitch (f0)</span><span class="lg"><i class="lg-fm"></i>formants</span> A synthetic voice reading my research question, drawn as it speaks. Low sounds sit at the bottom, high ones at the top, and the newest is on the right. Hover anywhere to see the pitch, the formants and which sound is being made.</figcaption></figure>'''
    strands = [('scoring', 'Scoring spoken English', 'Where automated scores of spoken English agree with human raters, where they do not, and what in the recording carries a speaker\u2019s first language.'),
               ('policy', 'Multilingual learners and policy', 'Who can earn the Seal of Biliteracy, and which English learners drop out of public data.'),
               ('ai', 'Generative AI and academic integrity', 'How students and universities judge the use of generative AI.')]
    research = (h2('Research') + '<ul class="strands">' + ''.join(
        f'<li><a href="research.html#{k}">{t}</a><p>{d}</p></li>' for k, t, d in strands)
        + '</ul><p class="more"><a href="research.html">Projects, papers and methods</a></p>')
    news = h2('News') + '<table class="kv news">' + ''.join(
        f'<tr><th>{esc(n["date"])}</th><td>{md(n["text"])}' + (f' <a href="{attr(n["link"])}">Read</a>' if n.get('link') else '') + '</td></tr>' for n in C['news'][:5]) + '</table>'
    return shell('index.html', 'Home', hero + fig + research + news, figs=True, spectro=True)

def page_pubs():
    st = [('all', 'All'), ('published', 'Published'), ('review', 'In review'), ('preprint', 'Preprints')]
    tp = [('all', 'All')] + [(t['key'], t['label']) for t in C['topics']]
    btn = lambda k, v, on: f'<button type="button" data-v="{k}" aria-pressed="{"true" if on else "false"}">{esc(v)}</button>'
    filt = (f'<div class="filters"><div class="frow" data-f="status"><span class="k">Status</span>{"".join(btn(k, v, k == "all") for k, v in st)}</div>'
            f'<div class="frow" data-f="topic"><span class="k">Topic</span>{"".join(btn(k, v, k == "all") for k, v in tp)}</div><p class="count" id="count"></p></div>')
    years = {}
    for p in PUBS: years.setdefault(p['year'], []).append(p)
    ys = ''.join(f'<section class="yr"><div class="y">{y}</div><ul class="pubs">{"".join(pub_li(p) for p in ps)}</ul></section>' for y, ps in sorted(years.items(), reverse=True))
    talks = []
    for t in C['presentations']:
        acts = f'<a href="https://doi.org/{attr(t["doi"])}">{"DOI" if t.get("id") == "aera" else "Related paper"}</a>' if t.get('doi') else ''
        cite = f' data-cite="{t["id"]}"' if t.get('id') in CITES else ''
        who = f' With {esc(t["coauthors"])}.' if t.get('coauthors') else ''
        talks.append(f'<tr><th>{esc(t["date"])}</th><td><span class="tl2">{esc(t["title"])}</span>. <i>{esc(t["site_venue"])}</i>.{who}'
                     + (f'<div class="meta"><span class="acts"{cite}>{acts}</span></div>' if acts or cite else '') + '</td></tr>')
    body = (title('Publications') + f'<p class="lead">Journal articles, preprints and manuscripts in review. The same list is on <a href="{attr(P["scholar"])}">Google Scholar</a>.</p>'
            + h2('Papers') + filt + ys + h2('Talks') + '<table class="kv news talks">' + ''.join(talks) + '</table>')
    return shell('publications.html', 'Publications', body, cites=True, anims=True)

exec(open(os.path.join(HERE, 'research_page.py')).read())   # defines page_research

exec(open(os.path.join(HERE, 'teaching_page.py')).read())   # defines page_teaching

exec(open(os.path.join(HERE, 'service_page.py')).read())   # defines page_service

HEAD404 = f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="/">
<meta name="robots" content="noindex">
<title>Page not found | {ME}</title>
<meta name="color-scheme" content="light dark">'''

def page_404():
    body = (title('Page not found') + '<p class="lead">The page you were looking for does not exist or has moved.</p>'
            + '<p class="more"><a href="index.html">Go to the homepage</a></p>')
    return shell('404.html', 'Page not found', body)

ASSETS = ['site.css', 'site.js', 'figures.js', 'anims.js', 'spectro.js', 'codepanel.js']
VER = {f: hashlib.md5(open(os.path.join(ROOT, 'assets', f), 'rb').read()).hexdigest()[:8] for f in ASSETS}
OUT_PAGES = {}
for n, fn in [('index.html', page_home), ('research.html', page_research), ('publications.html', page_pubs),
              ('teaching.html', page_teaching), ('service.html', page_service), ('404.html', page_404)]:
    page = re.sub(r'(src|href)="assets/(' + '|'.join(re.escape(f) for f in ASSETS) + ')"', lambda m: f'{m.group(1)}="assets/{m.group(2)}?v={VER[m.group(2)]}"', fn())   # version tags: browsers always load the newest file
    page = re.sub(r'<a (?![^>]*target=)([^>]*href="https?://[^"]*"[^>]*)>', r'<a \1 target="_blank" rel="noopener">', page)   # outside links open in a new tab
    OUT_PAGES[n] = page
