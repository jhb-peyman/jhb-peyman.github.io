# Research page. Run by pages.py (uses its helpers: C, P, BYID, esc, md, attr, h2, title, shell, apa_authors, initials).
# Every claim about a paper below was checked against the paper's own text.

SCORER_FIG = '''<figure class="figure rs-fig"><div class="viz" id="vizB" role="img" aria-label="Animated chart of human and automated scores with decision flips"><canvas id="scope"></canvas><div class="tip" id="tipB"></div></div>
<figcaption>Two scorers, one question. Simulated spoken responses scored by human raters (green) and an automated scorer. Where they fall on opposite sides of the cut score, the decision flips. An illustration, not study data.</figcaption></figure>'''

def page_research():
    R = C['research']
    PR = C['projects']
    TALKS = C['presentations']
    ga = [a for a in C['appointments'] if 'Research' in a['title']][0]

    def link_of(p):
        return f'https://doi.org/{p["doi"]}' if p.get('doi') else p.get('url', '')

    def ref(pid):                                   # APA 7 style reference, own name in bold
        p = BYID[pid]
        t = esc(p['title']); L = link_of(p)
        t = f'<a href="{attr(L)}">{t}</a>' if L else t
        tail = ' [Research artifact].' if p.get('kind') == 'artifact' else f'. <i>{esc(p["venue"])}</i>.'
        note = ''
        if p['status'] == 'preprint' and p.get('kind') != 'artifact':
            lab = p.get('label', '')
            note = 'Preprint' + (', under review at <i>' + esc(lab.split('under review at ')[1]) + '</i>' if 'under review at' in lab else '')
        elif p['status'] == 'review':
            note = esc(p.get('label', 'In review'))
        note = f' <span class="rstat">{note}</span>' if note else ''
        return f'<li>{apa_authors(pid, p["authors"])} ({p["year"]}). {t}{tail}{note}</li>'

    def talk(sub):
        t = [x for x in TALKS if sub in x['title']][0]
        names = ['<b>' + esc(f'{P["last_name"]}, {initials(P["first_name"])}') + '</b>']
        for n in t.get('coauthors', '').replace(' and ', ', ').split(', '):
            n = n.strip()
            if n: names.append(esc(f'{n.split()[-1]}, {initials(" ".join(n.split()[:-1]))}'))
        if len(names) == 1: au = names[0]
        elif len(names) == 2: au = f'{names[0]}, &amp; {names[1]}'
        else: au = ', '.join(names[:-1]) + ', &amp; ' + names[-1]
        mon, yr = t['cv_date'].split()
        tt = esc(t['title'])
        if t.get('doi') and 'Beyond' not in t['title']:       # the MIDTESOL talk shares the article's DOI; only AERA has its own
            tt = f'<a href="https://doi.org/{attr(t["doi"])}">{tt}</a>'
        where = esc(t['cv_event']) + (f', {esc(t["place"])}' if t.get('place') else '')
        return f'<li>{au} ({yr}, {mon}). {tt} [Presentation]. {where}.</li>'

    WHITE = ('<li><b>Jahanbin, P.</b>, Klein-Thibodeau, M., &amp; Brazil, A. M. (2026, August). Too few to count: How a uniform '
             'reporting threshold renders rural English learners invisible in Kansas [White paper]. Center for Educational '
             'Opportunity Programs, University of Kansas.</li>')

    def refs(items, head='Papers and talks'):
        h = f'<h4>{head}</h4>' if head else ''
        return f'<div class="refs">{h}<ul>{"".join(items)}</ul></div>'

    def proj(i, title_txt, inner):
        return (f'<div class="pj"><div class="pj-h"><h3>{title_txt}</h3><span class="when">{esc(PR[i]["dates"])}</span></div>{inner}</div>')

    # ---------------------------------------------------------------- the page
    intro = ('<p class="rs-intro">The question has three parts in my work. One is technical: what an automated scorer '
             'responds to in a recording, and how far its scores can be trusted. One is about policy: which multilingual '
             'students get recognized, and which ones drop out of public data. The newest asks how students and universities '
             'judge the use of generative AI.</p>')

    s1 = ('<h2 id="scoring">Scoring Spoken English</h2>'
          + proj(0, 'Dissertation: validity and fairness of automated speaking assessment',
                 f'<p>{esc(PR[0]["text"])} The focus is decision risk: responses where the human and the automated score land on '
                 'opposite sides of a cut score, so the same answer would pass with one scorer and fail with the other.</p>' + SCORER_FIG)
          + proj(1, 'What a first language leaves in L2 speech',
                 '<p>Before a scorer can be judged, it helps to know what in the signal carries a speaker’s first language. '
                 'Using Speech Accent Archive recordings of Mandarin and English first-language speakers, I describe their English '
                 'with MFCCs, test which coefficients separate the two groups, and show that a random forest built on that small '
                 'set classifies better than one built on all thirteen. A companion study uses forced alignment to locate pauses in '
                 'the same read passage: both groups pause at punctuation about equally, but the Mandarin group pauses far more '
                 'often where the text gives no punctuation cue.</p>')
          + refs([ref('acoustic'), ref('arxiv'), ref('rsquare'), ref('pipeline'), talk('Machine Learning')]))

    s2 = ('<h2 id="policy">Multilingual Learners and Policy</h2>'
          + proj(2, 'The Seal of Biliteracy: access, fidelity and recognition',
                 f'<p>{esc(PR[2]["text"])} With four colleagues I reviewed fifteen years of research on the Seal for <i>TESOL '
                 'Quarterly</i>, asking who can reach it, whether programs stay true to its purpose, and what it is worth to '
                 'students afterward.</p>'
                 '<p class="fund">I worked on this as a graduate research assistant on Project SELILLA, a $2.44 million federally '
                 f'funded project at the Center for Educational Opportunity Programs, University of Kansas ({esc(ga["dates"])}).</p>')
          + proj(3, 'English learners in Kansas public reporting',
                 f'<p>{esc(PR[3]["text"])} Kansas withholds a subgroup result when fewer than ten students are tested. In our white '
                 'paper, districts that publish English learner reading results enroll about 98% of the state\u2019s English learners, '
                 'yet only about 41% of the districts that serve them report: every city district, but only about a quarter of rural '
                 'ones. Once enrollment is taken into account, the rural gap is no longer statistically significant: small numbers under a '
                 'uniform threshold, rather than rurality as such, decide who goes unseen.</p>')
          + refs([ref('beyond'), talk('Beyond Symbolic'), WHITE]))

    s3 = ('<h2 id="ai">Generative AI and Academic Integrity</h2>'
          + '<p class="sec-p">With colleagues at Kansas I developed and tested four short instruments for how university students '
            'judge the use of generative AI in their coursework, and presented work at AERA on whether campus climate or individual '
            'factors better predict academic AI integrity. A manuscript with Hyesun Cho, now in revision, looks at raciolinguistic '
            'gatekeeping and algorithmic suspicion of Middle Eastern graduate teaching assistants.</p>'
          + refs([ref('ethics'), ref('accent'), talk('Campus Climate')]))

    s4 = (h2('Other Work')
          + '<p class="sec-p">Shorter projects in language testing, classroom learning and academic discourse.</p>'
          + refs([ref('lltm'), ref('dyadic'), ref('corpus'), ref('personality'), ref('achievements'), ref('audio'),
                  talk('EFL Learners Excel')], head=''))

    # ---------------------------------------------------------------- methods, each with where it was used
    NAMES = {'ethics': 'GenAI ethics instruments', 'lltm': 'LLTM study', 'acoustic': 'acoustic gaps', 'arxiv': 'MFCC framework',
             'rsquare': 'MFCC pipeline', 'audio': 'audio-assisted reading', 'corpus': 'book-review corpus',
             'personality': 'lecturer creativity', 'dyadic': 'peer-review talk', 'beyond': 'Seal of Biliteracy review'}
    def used(*ids):
        out = ['dissertation' if i == 'diss' else 'Too Few to Count' if i == 'white' else f'<a href="{attr(link_of(BYID[i]))}">{NAMES[i]}</a>' for i in ids]
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
    meth = (h2('Methods') + '<p class="sec-p">Each method links to the study where I used it.</p>'
            + ''.join(f'<div class="mg"><h4>{g}</h4><ul>' + ''.join(f'<li><span>{esc(a)}</span>{b}</li>' for a, b in rows) + '</ul></div>' for g, rows in M)
            )

    body = title('Research') + f'<p class="lead">{md(R["statement"])}</p>' + intro + s1 + s2 + s3 + s4 + meth + data_section(link_of) + software_section()
    return shell('research.html', 'Research', body, figs=True)


# ---------------------------------------------------------------- data
def data_section(link_of):
    def u(pid, nm): return f'<a href="{attr(link_of(BYID[pid]))}">{nm}</a>'
    rows = [
      ('Cambridge Speak &amp; Improve corpus', 'Spoken responses with human audio ratings and transcript-based automated scores', 'dissertation'),
      ('Speech Accent Archive', 'Recordings of speakers reading the same English paragraph; 115 Mandarin and American English speakers in the gap study',
       u('acoustic', 'acoustic gaps') + ', ' + u('arxiv', 'MFCC framework')),
      ('PELEx reading subtest', '50 calibrated items, ten at each CEFR level from A1 to C1', u('lltm', 'LLTM study')),
      ('Student survey', '149 university students rating seven uses of generative AI', u('ethics', 'GenAI ethics instruments')),
      ('Academic book reviews', '240 reviews in applied linguistics, 2015 to 2020, by native and non-native English-speaking reviewers', u('corpus', 'book-review corpus')),
      ('Kansas public reporting', 'District-level Kansas ELA assessment results with KSDE and NCES enrollment and locale data, 2023-24 and 2024-25', 'Too Few to Count'),
    ]
    return (h2('Data') + '<p class="sec-p">The main datasets behind the studies above.</p><ul class="data">'
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
    return (h2('Software') + '<p class="sec-p">What I analyse with. Below, the core model of four studies is written out as a short sketch, '
            'run, and shown with the results the paper reports.</p>'
            + grid + also + code
            + '<script>window.SNIP_ICONS=' + json.dumps(icons) + '</script><script src="assets/codepanel.js"></script>')
