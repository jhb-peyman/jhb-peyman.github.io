# Research page. Run by pages.py (uses its helpers: C, P, BYID, esc, md, plain, attr, h2, title, shell, apa_authors, initials, venue).
# Projects come from content.toml by their strand; papers and talks are placed below by their id.
# Every claim about a paper below was checked against the paper's own text.

SCORER_FIG = '''<figure class="figure rs-fig"><div class="viz" id="vizB" role="img" aria-label="Animated chart of human and automated scores with decision flips"><canvas id="scope"></canvas><div class="tip" id="tipB"></div></div>
<figcaption>Two scorers, one question. Simulated spoken responses scored by human raters (green) and an automated scorer. Where they fall on opposite sides of the cut score, the decision flips. An illustration, not study data.</figcaption></figure>'''

def page_research():
    R = C['research']
    PROJ = C.get('projects', [])
    TALKS = {t['id']: t for t in C.get('presentations', []) if t.get('id')}

    def link_of(p):
        return f'https://doi.org/{p["doi"]}' if p.get('doi') else p.get('url', '')

    def ref(pid):                                   # APA 7 reference, own name in bold; same details as the Publications page
        p = BYID.get(pid)
        if not p:
            return ''
        L = link_of(p)
        raw = p.get('cite_title') or p['title']
        stop = '' if raw.rstrip().endswith(('?', '!')) else '.'
        t = esc(raw)
        t = f'<a href="{attr(L)}">{t}</a>' if L else t
        if p.get('kind') == 'artifact':
            stop = ''
            tail = ' [Research artifact].'
        else:
            tail = ' ' + venue(p)
        note = ''
        if p['status'] == 'preprint' and p.get('kind') != 'artifact':
            lab = p.get('label', '')
            note = 'Preprint' + (', under review at <i>' + esc(lab.split('under review at ')[1]) + '</i>' if 'under review at' in lab else '') + '.'
        elif p['status'] == 'review':
            note = esc(p.get('label', 'In review')).rstrip('.') + '.'
        note = f' <span class="rstat">{note}</span>' if note else ''
        return f'<li>{apa_authors(pid, p["authors"])} ({p["year"]}). {t}{stop}{tail}{note}</li>'

    def talk(tid):
        t = TALKS.get(tid)
        if not t:
            return ''
        names = ['<b>' + esc(f'{P["last_name"]}, {initials(P["first_name"])}') + '</b>']
        for n in t.get('coauthors', '').replace(' and ', ', ').split(', '):
            n = n.strip()
            if n: names.append(esc(f'{n.split()[-1]}, {initials(" ".join(n.split()[:-1]))}'))
        if len(names) == 1: au = names[0]
        elif len(names) == 2: au = f'{names[0]}, &amp; {names[1]}'
        else: au = ', '.join(names[:-1]) + ', &amp; ' + names[-1]
        m_ = re.match(r'([A-Za-z]+)\s*([\d-]*),?\s*(\d{4})', t.get('cv_date', ''))
        when = f'{m_.group(3)}, {m_.group(1)}' + (f' {m_.group(2)}' if m_.group(2) else '') if m_ else esc(t.get('date', ''))
        tt = esc(t['title'])
        if t.get('doi') and t.get('cite_title'):      # only a talk with its own citation record has its own DOI
            tt = f'<a href="https://doi.org/{attr(t["doi"])}">{tt}</a>'
        event = esc(t.get('event') or t.get('cv_event', ''))
        where = event + (f', {esc(t["place"])}' if t.get('place') else '')
        return f'<li>{au} ({when}). {tt} [{esc(t.get("format", "Presentation"))}]. {where}.</li>'

    def report(r):                                  # reports and white papers from content.toml
        au = apa_authors('', r['authors'])
        mon_ = r.get('cv_date', '').split()[0] if r.get('cv_date') else ''
        t_ = esc(r['title'])
        t_ = f'<a href="{attr(r["url"])}">{t_}</a>' if r.get('url') else t_
        return f'<li>{au} ({r["year"]}{", " + mon_ if mon_ else ""}). {t_} [{esc(r.get("kind", "Report"))}]. {esc(r["publisher"])}.</li>'
    WHITE = ''.join(report(r) for r in C.get('reports', []))

    def refs(items, head='Papers and talks'):
        items = [i for i in items if i]
        if not items:
            return ''
        h = f'<h3>{head}</h3>' if head else ''
        return f'<div class="refs">{h}<ul>{"".join(items)}</ul></div>'

    FIG = {'diss': SCORER_FIG}                      # figures that belong to a project
    def proj(x):
        ttl = esc(x.get('site_title') or plain(x['title']))
        body = f'<p>{md(x.get("site_text") or x.get("text", ""))}</p>'
        if x.get('site_note'):
            body += f'<p class="fund">{md(x["site_note"])}</p>'
        return (f'<div class="pj"><div class="pj-h"><h3>{ttl}</h3><span class="when">{esc(x.get("dates", ""))}</span></div>'
                f'{body}{FIG.get(x.get("id"), "")}</div>')
    def projects(strand):
        return ''.join(proj(x) for x in PROJ if x.get('strand') == strand)

    # ---------------------------------------------------------------- the page
    intro = ('<p class="rs-intro">The question has three parts in my work. One is technical: what an automated scorer '
             'responds to in a recording, and how far its scores can be trusted. One is about policy: which multilingual '
             'students get recognized, and which ones drop out of public data. The newest asks how students and universities '
             'judge the use of generative AI.</p>')

    toc = ('<p class="rs-toc2" aria-label="On this page">' + ' <span aria-hidden="true">·</span> '.join(
        f'<a href="#{k}">{t}</a>' for k, t in [('scoring', 'Scoring spoken English'), ('policy', 'Multilingual learners and policy'),
                                               ('ai', 'Generative AI and academic integrity'), ('other', 'Other work'),
                                               ('methods', 'Methods'), ('data', 'Data'), ('software', 'Software')]) + '</p>')

    s1 = ('<h2 id="scoring">Scoring Spoken English</h2>' + projects('scoring')
          + refs([talk('site27'), talk('ncic26'), ref('acoustic'), ref('arxiv'), ref('rsquare'), ref('pipeline'), talk('scipie25')]))

    s2 = ('<h2 id="policy">Multilingual Learners and Policy</h2>' + projects('policy')
          + refs([ref('beyond'), talk('midtesol26'), WHITE, ref('toofew')]))

    s3 = ('<h2 id="ai">Generative AI and Academic Integrity</h2>' + projects('ai')
          + '<p class="sec-p">With colleagues at Kansas I developed and tested four short instruments for how university students '
            'judge the use of generative AI in their coursework, and presented work at AERA on whether campus climate or individual '
            'factors better predict academic AI integrity. A manuscript with Hyesun Cho, revised and back under review, looks at '
            'raciolinguistic gatekeeping and algorithmic suspicion of Middle Eastern graduate teaching assistants, and I will lead a '
            'roundtable on the same topic at TESOL 2027.</p>'
          + refs([ref('ethics'), ref('accent'), talk('tesol27'), talk('aera')]))

    other_proj = ''.join(proj(x) for x in PROJ if x.get('strand') not in ('scoring', 'policy', 'ai'))
    s4 = ('<h2 id="other">Other Work</h2>' + other_proj
          + '<p class="sec-p">Shorter projects in language testing, classroom learning and academic discourse.</p>'
          + refs([ref('lltm'), ref('dyadic'), ref('corpus'), ref('personality'), ref('achievements'), ref('audio'),
                  talk('midtesol24')], head=''))

    # ---------------------------------------------------------------- methods, each with where it was used
    NAMES = {'ethics': 'GenAI ethics instruments', 'lltm': 'LLTM study', 'acoustic': 'acoustic gaps', 'arxiv': 'MFCC framework',
             'rsquare': 'MFCC pipeline', 'audio': 'audio-assisted reading', 'corpus': 'book-review corpus',
             'personality': 'lecturer creativity', 'dyadic': 'peer-review talk', 'beyond': 'Seal of Biliteracy review'}
    def used(*ids):
        out = ['dissertation' if i == 'diss' else 'Too Few to Count' if i == 'white' else
               f'<a href="{attr(link_of(BYID[i]))}">{NAMES.get(i, i)}</a>' if i in BYID else NAMES.get(i, i) for i in ids]
        return '<span class="used">' + ', '.join(out) + '</span>'
    M = [
      ('Measurement', [
        ('Exploratory and confirmatory factor analysis of ordinal items (polychoric correlations, parallel analysis, WLSMV)', used('ethics')),
        ('Reliability: Cronbach’s alpha, McDonald’s omega, Spearman-Brown', used('ethics')),
        ('Rasch modeling and the linear logistic test model, with a coded Q-matrix of item features', used('lltm')),
        ('Rater agreement and cut-score decision risk, with bootstrap confidence intervals', used('diss')),
      ]),
      ('Statistical modeling', [
        ('Hierarchical regression with heteroskedasticity-robust (HC3) standard errors', used('ethics')),
        ('Crossed random-effects logistic models (lme4); Poisson and negative binomial models for counts', used('acoustic')),
        ('Firth penalized logistic regression for rare and separated outcomes', used('white')),
        ('ANCOVA, MANCOVA and MANOVA with effect sizes, in a pre, post and delayed post-test design', used('audio')),
        ('Group comparisons with Bonferroni correction, MANOVA and canonical discriminant analysis', used('arxiv')),
      ]),
      ('Speech and machine learning', [
        ('MFCC feature extraction and random forest classification, compared with McNemar’s test', used('arxiv', 'rsquare')),
        ('Forced alignment (Montreal Forced Aligner) with acoustic checks in Praat and Parselmouth', used('acoustic')),
        ('Reproducible Python pipelines (librosa, scikit-learn)', used('rsquare')),
      ]),
      ('Corpus and qualitative', [
        ('Corpus analysis with AntConc and WordSmith; chi-square comparisons', used('corpus')),
        ('Integrative literature review, reported with PRISMA 2020 items', used('beyond')),
      ]),
    ]
    meth = ('<h2 id="methods">Methods</h2>' + '<p class="sec-p">Each method links to the study where I used it.</p>'
            + ''.join(f'<div class="mg"><h3>{g}</h3><ul>' + ''.join(f'<li><span>{esc(a)}</span>{b}</li>' for a, b in rows) + '</ul></div>' for g, rows in M)
            )

    body = title('Research') + f'<p class="lead">{md(R["statement"])}</p>' + intro + toc + s1 + s2 + s3 + s4 + meth + data_section(link_of) + software_section()
    return shell('research.html', 'Research', body, figs=True)


# ---------------------------------------------------------------- data
def data_section(link_of):
    def u(pid, nm): return f'<a href="{attr(link_of(BYID[pid]))}">{nm}</a>'
    rows = [
      ('Cambridge Speak &amp; Improve Corpus 2025', 'Spoken responses with human holistic ratings, compared with scores from the released Speak &amp; Improve Challenge 2025 baseline scorer', 'dissertation'),
      ('Speech Accent Archive', 'Recordings of speakers reading the same English paragraph; 115 Mandarin and American English speakers in the gap study',
       u('acoustic', 'acoustic gaps') + ', ' + u('arxiv', 'MFCC framework')),
      ('PELEx reading subtest', '50 calibrated items, ten at each CEFR level from A1 to C1', u('lltm', 'LLTM study')),
      ('Student survey', '149 university students rating seven uses of generative AI', u('ethics', 'GenAI ethics instruments')),
      ('Academic book reviews', '240 reviews in applied linguistics, 2015 to 2020, by native and non-native English-speaking reviewers', u('corpus', 'book-review corpus')),
      ('Kansas public reporting', 'District-level Kansas ELA assessment results with KSDE and NCES enrollment and locale data, 2023-24 and 2024-25', 'Too Few to Count'),
    ]
    return ('<h2 id="data">Data</h2>' + '<p class="sec-p">The main datasets behind the studies above.</p><ul class="data">'
            + ''.join(f'<li><b>{a}</b><span class="dd">{b}</span><span class="used">{c}</span></li>' for a, b, c in rows) + '</ul>')

# ---------------------------------------------------------------- software
def _icon(name):
    svg = open(os.path.join(HERE, 'icons', name + '.svg')).read()
    path = re.search(r'<path d="([^"]+)"', svg).group(1)
    return f'<svg class="logo" viewBox="0 0 24 24" aria-hidden="true"><path d="{path}"/></svg>'

def software_section():
    tools = [
      ('r', 'R', '#276DC3', 'psych, lavaan, semTools, lme4, sandwich, tidyverse, ggplot2'),
      ('python', 'Python', '#3776AB', 'librosa, scikit-learn, Parselmouth'),
      ('quarto', 'Quarto', '#39729E', 'Reproducible reports, with R Markdown'),
      ('scikitlearn', 'scikit-learn', '#F7931E', 'Random forest classification and model comparison'),
    ]
    grid = '<div class="stack">' + ''.join(
        f'<div class="tool" style="--brand:{c}">{_icon(i)}<div><b>{n}</b><span>{d}</span></div></div>' for i, n, c, d in tools) + '</div>'
    also = ('<dl class="also"><div><dt>Speech</dt><dd>Praat, Montreal Forced Aligner</dd></div>'
            '<div><dt>Statistics</dt><dd>SPSS</dd></div><div><dt>Corpus</dt><dd>AntConc, WordSmith</dd></div></dl>')
    icons = {'r': _icon('r').replace('class="logo"', 'class="ti"'), 'py': _icon('python').replace('class="logo"', 'class="ti"')}
    code = ('<figure class="snip-wrap"><div class="snip" id="codeP">'
            '<div class="snip-bar"><div class="snip-tabs" role="tablist" aria-label="Code sketches"></div>'
            '<div class="snip-tools"><span class="snip-stat" id="codeS" aria-live="off"></span>'
            '<button type="button" class="snip-btn" id="codeRun" aria-label="Run again"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg><span>Run</span></button>'
            '<button type="button" class="snip-btn" id="codeCopy" aria-label="Copy code"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 8h11v13H8zM5 3h11v3H7v11H5z"/></svg><span>Copy</span></button></div></div>'
            '<div class="snip-ed"><pre class="snip-gut" id="codeG" aria-hidden="true"></pre><pre class="snip-code"><code id="codeT"></code></pre></div>'
            '<div class="snip-run"><div class="snip-con"><div class="snip-lab">Console</div><pre id="codeO"></pre></div>'
            '<div class="snip-chart"><div class="snip-lab" id="codeH"></div><svg id="codeV" role="img" aria-label="Chart of the reported results"></svg><div class="snip-tip" id="codeTip"></div></div></div>'
            '<div class="snip-foot"><span id="codeEnv"></span><span id="codeRef"></span></div>'
            '</div><figcaption id="codeC"></figcaption></figure>')
    return ('<h2 id="software">Software</h2>' + '<p class="sec-p">What I analyze with. Below, the core model of four studies is written out as a short sketch, '
            'run, and shown with the results the paper reports.</p>'
            + grid + also + code
            + '<script>window.SNIP_ICONS=' + json.dumps(icons) + '</script><script src="assets/codepanel.js"></script>')
