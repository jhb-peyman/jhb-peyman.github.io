# Teaching page. Run by pages.py (uses its helpers: C, esc, md, attr, h2, title, shell, TODAY).
# Everything comes from content.toml: [[teaching]] courses (taught, short, summary, next, note),
# the appointments with a site_text, and the honors. Edit content.toml, not this file.
import datetime

SEASON = {'Spring': 0, 'Summer': 1, 'Fall': 2}
ABBR = {'Spring': 'S', 'Summer': 'Su', 'Fall': 'F'}
NUM = {1: 'once', 2: 'twice', 3: 'three times', 4: 'four times', 5: 'five times', 6: 'six times', 7: 'seven times', 8: 'eight times',
       9: 'nine times', 10: 'ten times'}
WORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}

def term_key(t):
    season, year = t.split()
    return (int(year), SEASON[season])

def term_code(t):
    season, year = t.split()
    return f'{ABBR[season]}{year[2:]}'

def current_term(d):
    return (d.year, 0 if d.month <= 5 else 1 if d.month <= 7 else 2)

def page_teaching():
    now = current_term(TODAY)
    courses = []
    for g in C['teaching']:
        level = g['group'][0] + g['group'][1:].lower() if g['group'].isupper() else g['group'].capitalize()
        level = {'Teacher education foundations': 'Teacher education foundations'}.get(level, level)
        for k in g['courses']:
            if not k.get('taught'):
                continue
            courses.append(dict(k, level=level))
    terms = sorted({t for k in courses for t in k['taught']}, key=term_key)
    def done(k): return sum(1 for t in k['taught'] if term_key(t) <= now)
    def ahead(k): return sum(1 for t in k['taught'] if term_key(t) > now)
    def n(k): return len(k['taught'])
    total, upcoming = sum(done(k) for k in courses), sum(ahead(k) for k in courses)
    next_terms = sorted({t for k in courses for t in k['taught'] if term_key(t) > now}, key=term_key)
    nxt = next_terms[0] if next_terms else None

    def when(k):
        ts = sorted(set(k['taught']), key=term_key)
        multi = [t for t in ts if k['taught'].count(t) > 1]
        regular = all(t.split()[0] != 'Summer' for t in ts)
        if len(ts) >= 4 and regular:
            txt = f'Every fall and spring, {ts[0]} to {ts[-1]}'
        else:
            parts = [t + (f' ({WORD.get(k["taught"].count(t), k["taught"].count(t))} sections)' if t in multi else '') for t in ts]
            txt = parts[0] if len(parts) == 1 else ', '.join(parts[:-1]) + ' and ' + parts[-1]
        return txt

    # ---------------------------------------------------------------- opening paragraph
    top = max(courses, key=n)
    repeat = sum(1 for k in courses if n(k) > 1)
    ncw = WORD.get(len(courses), str(len(courses)))
    s1 = (f'I have taught since 2014: English to school and university students in Iran, and since 2023 teacher education and '
          f'graduate TESOL at the University of Kansas, where I have been instructor of record for {ncw} courses and {total} course '
          f'sections so far' + (f', with {WORD.get(upcoming, upcoming)} more assigned for {nxt}' if nxt else '') + '.')
    s2 = []
    tts = sorted(set(top['taught']), key=term_key)
    if len(tts) >= 4 and all(t.split()[0] != 'Summer' for t in tts):
        s2.append(f'I have taught {esc(top["code"])} every fall and spring since {tts[0]}')
    if repeat > 1:
        s2.append(f'{WORD.get(repeat, repeat)} of my {ncw} Kansas courses more than once' + (f', counting {nxt}' if nxt else ''))
    s2t = (' ' + (s2[0] + ', and ' + s2[1] if len(s2) == 2 else ('I have taught ' + s2[0] if not s2[0].startswith('I ') else s2[0])) + '.') if s2 else ''
    lead = f'<p class="lead">{s1}{s2t}</p>'

    # ---------------------------------------------------------------- Kansas: the term-by-term record
    ku = next((a for a in C['appointments'] if 'Instructor of Record' in a['title']), None)
    order = sorted(courses, key=lambda k: (min(term_key(t) for t in k['taught']), k['code']))
    def tcls(t): return 'now' if term_key(t) == now else ''
    head = ('<tr><th scope="col" class="tr-c"><span class="sr">Course</span></th>'
            + ''.join(f'<th scope="col" class="{tcls(t)}"><abbr title="{t}">{term_code(t)}</abbr></th>' for t in terms)
            + '<th scope="col" class="tt">Sections</th></tr>')
    mx = max(n(k) for k in courses)
    rows = ''
    for k in order:
        cells = ''
        for t in terms:
            c_ = k['taught'].count(t)
            if c_:
                lab = f'{k["code"]}, {t}' + (f', {c_} sections' if c_ > 1 else '') + (' (assigned)' if term_key(t) > now else '')
                cells += f'<td class="{tcls(t)}"><span class="cell" title="{attr(lab)}" aria-label="{attr(lab)}">{"<i class=\"sq\"></i>" * c_}</span></td>'
            else:
                cells += f'<td class="{tcls(t)}"><span class="sr">not taught</span></td>'
        cid = k['code'].replace('&', '').replace(' ', '').lower()
        rows += (f'<tr><th scope="row" class="tr-c"><a href="#{cid}">{esc(k["code"])}<span>{esc(k.get("short", ""))}</span></a></th>{cells}'
                 f'<td class="tt"><span class="tn">{n(k)}</span><span class="tbar"><span style="width:{100 * n(k) / mx:.0f}%"></span></span></td></tr>')
    next_courses = sorted((k for k in courses if ahead(k)), key=lambda k: k['code'])
    def next_txt(k): return f'{esc(k["code"])} {esc(k.get("next", ""))}'.strip()
    next_p = ''
    if nxt and next_courses:
        items = [next_txt(k) for k in next_courses]
        next_p = (f'<p class="rec-next">In {nxt} I will teach '
                  + (items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1]) + '.</p>')
    record = (h2('University of Kansas')
              + (f'<p class="sec-role">Instructor of record and graduate teaching assistant, {esc(ku["org"].replace(", University of Kansas", ""))}, {esc(ku["dates"]).replace("Present", "present")}.</p>' if ku else '')
              + '<p class="sec-p">The table shows every course I have taught at Kansas, term by term. Each square is one section'
              + (f'; {nxt} ({term_code(nxt)}) is next term, already assigned' if nxt else '')
              + ', and the shaded column is the current term.</p>'
              + f'<div class="rec-wrap"><table class="rec" id="rec"><thead>{head}</thead><tbody>{rows}</tbody></table></div>' + next_p)

    # ---------------------------------------------------------------- Kansas: the courses, most taught first
    blocks = '<h3 class="grp">Courses, most taught first</h3>'
    for k in sorted(courses, key=lambda k: (-n(k), -done(k), min(term_key(t) for t in k['taught']))):
        cid = k['code'].replace('&', '').replace(' ', '').lower()
        sq = '<i class="sq"></i>' * n(k)
        note = f'<p class="c-formerly">{md(k["note"])}</p>' if k.get('note') else ''
        blocks += (f'<article class="crs2{" rep" if n(k) > 1 else ""}" id="{cid}"><div class="crs2-code">{esc(k["code"])}'
                   f'<div class="crs2-count"><span class="big">{n(k)}</span>{"section" if n(k) == 1 else "sections"}</div>'
                   f'<div class="crs2-sq">{sq}</div></div><div class="crs2-body">'
                   f'<h4>{esc(k["title"]).replace("K-12", "K&#8209;12")}</h4>'
                   f'<p class="c-meta"><span>{k["level"]}</span><span>{when(k)}</span></p>{note}'
                   f'<p>{esc(k.get("summary", "")).replace("K-12", "K&#8209;12")}</p></div></article>')

    # ---------------------------------------------------------------- teaching in Iran
    iran = sorted((a for a in C['appointments'] if a.get('site_text') and 'Iran' in a.get('place', '')),
                  key=lambda a: (not a.get('courses'), -int(re.findall(r'\d{4}', a['dates'])[0])))
    def place(a):
        lis = ''.join(f'<li><span class="c-code">{esc(x["code"])}</span> {esc(x["title"])}, {esc(x["level"])}, {esc(x["dates"])}</li>' for x in a.get('courses', []))
        return (f'<div class="place"><h3>{esc(a["org"])} <span class="p-when">{esc(a["dates"])}</span></h3><p>{md(a["site_text"])}</p>'
                + (f'<ul class="old">{lis}</ul>' if lis else '') + '</div>')
    iran_html = (h2('Teaching in Iran') + ''.join(place(a) for a in iran)) if iran else ''

    # ---------------------------------------------------------------- timeline, at the end
    MON = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}
    def ydate(s, end):
        s = s.strip()
        if s.lower() == 'present':
            last = sorted({t for k in courses for t in k['taught']}, key=term_key)[-1] if courses else None
            if last:
                y, se = term_key(last)
                return y + (0.37, 0.58, 0.95)[se]
            return TODAY.year + TODAY.month / 12
        parts = s.split()
        if len(parts) == 2 and parts[0][:3] in MON:
            return int(parts[1]) + (MON[parts[0][:3]] + (1 if end else 0)) / 12
        return int(parts[-1]) + (0.9 if end else 0)
    lanes = []
    for a in ([ku] if ku else []) + [a for a in C['appointments'] if a.get('site_text')]:
        a0, a1 = (x for x in a['dates'].split(' to '))
        aw = None
        for h in C.get('honors', []):
            m = re.search(r'(\d{4})', h.get('note', ''))
            if m and a['org'] in h.get('note', ''):
                aw = (int(m.group(1)) + 0.5, f'{h["name"]}, {a["org"]}, {m.group(1)}')
        city = 'Lawrence' if a is ku else a.get('place', '').split(',')[0]
        name = 'University of Kansas' if a is ku else a['org']
        lanes.append((name, city, ydate(a0, False), ydate(a1, True), aw))
    timeline = ''
    if lanes:
        Y0 = int(min(l[2] for l in lanes)); Y1 = max(l[3] for l in lanes) + 0.15
        def pct(y): return f'{100 * (y - Y0) / (Y1 - Y0):.2f}%'
        today_y = TODAY.year + (TODAY.month - 0.5) / 12
        step = 2 if Y1 - Y0 > 8 else 1
        yrs = ''.join(f'<span style="left:{pct(y)}">{y}</span>' for y in range(Y0, int(Y1) + 1, step))
        grid = ''.join(f'<i style="left:{pct(y)}"></i>' for y in range(Y0, int(Y1) + 1))
        lane_html = ''.join(
            f'<li><span class="tl-n">{esc(nm)}<em>{esc(pl)}</em></span><span class="tl-tr">{grid}'
            f'<b class="tl-b{" ku" if i == 0 and ku else ""}" style="left:{pct(a)};width:calc({pct(b)} - {pct(a)})"></b>'
            + (f'<s class="tl-a" style="left:{pct(aw[0])}" title="{attr(aw[1])}"></s>' if aw else '')
            + f'<u class="tl-now" style="left:{pct(today_y)}"></u></span></li>'
            for i, (nm, pl, a, b, aw) in enumerate(lanes))
        awards = [l[4][1] for l in lanes if l[4]]
        timeline = (h2('Timeline') + f'<p class="sec-p">Where I have taught since {Y0}. The dashed line is today.</p>'
                    + f'<div class="ttl" role="img" aria-label="Teaching timeline, {Y0} to {int(Y1)}, at {len(lanes)} institutions">'
                    + f'<div class="tl-yrs"><span class="tl-n"></span><span class="tl-tr">{yrs}</span></div><ul>{lane_html}</ul></div>'
                    + ''.join(f'<p class="tl-foot"><s class="tl-a"></s> {esc(w)}</p>' for w in awards))

    body = title('Teaching') + lead + record + blocks + iran_html + timeline
    return shell('teaching.html', 'Teaching', body)
