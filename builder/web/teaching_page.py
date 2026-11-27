# Teaching page. Run by pages.py (uses its helpers: C, esc, md, attr, h2, title, shell, TODAY).
# The course data comes from content.toml: [[teaching]] courses (taught, short, summary, next, note),
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
        def nxt_reg(k):
            y, se = k
            return (y, 2) if se == 0 else (y + 1, 0)
        keys = [term_key(t) for t in ts]
        unbroken = all(nxt_reg(keys[i]) == keys[i + 1] for i in range(len(keys) - 1))
        if len(ts) >= 4 and regular and unbroken:
            txt = f'Every fall and spring, {ts[0]} to {ts[-1]}'
        else:
            parts = [t + (f' ({WORD.get(k["taught"].count(t), k["taught"].count(t))} sections)' if t in multi else '') for t in ts]
            txt = parts[0] if len(parts) == 1 else ', '.join(parts[:-1]) + ' and ' + parts[-1]
        return txt

    # ---------------------------------------------------------------- opening paragraph
    ncw = WORD.get(len(courses), str(len(courses)))
    repeated = sum(1 for k in courses if done(k) > 1)
    often = ('most of them' if repeated > len(courses) / 2 else 'several of them' if repeated > 1 else '')
    lead = ('<p class="lead">I have taught since 2014: English to school and university students in Iran, and since 2023 '
            'teacher education and graduate TESOL courses at the University of Kansas. '
            f'At Kansas I have taught {ncw} courses as instructor of record, {total} sections so far'
            + (f', {often} more than once' if often else '') + '.'
            + (f' {WORD.get(upcoming, str(upcoming)).capitalize()} more {"section is" if upcoming == 1 else "sections are"} assigned for {nxt}.' if nxt else '')
            + '</p>')

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
                said = f'{c_} section' + ('s' if c_ > 1 else '') + (' (assigned)' if term_key(t) > now else '')
                cells += (f'<td class="{tcls(t)}"><span class="cell" title="{attr(lab)}" aria-hidden="true">{"<i class=\"sq\"></i>" * c_}</span>'
                          f'<span class="sr">{said}</span></td>')
            else:
                cells += f'<td class="{tcls(t)}"></td>'
        cid = k['code'].replace('&', '').replace(' ', '').lower()
        rows += (f'<tr><th scope="row" class="tr-c"><a href="#{cid}">{esc(k["code"])}<span>{esc(k.get("short", ""))}</span></a></th>{cells}'
                 f'<td class="tt"><span class="tn">{n(k)}</span></td></tr>')
    record = (h2('University of Kansas')
              + (f'<p class="sec-role">Instructor of record and graduate teaching assistant, {esc(ku["org"].replace(", University of Kansas", ""))}, {esc(ku["dates"]).replace("Present", "present")}.</p>' if ku else '')
              + '<p class="sec-p">The table shows every course I have taught at Kansas, term by term. Each square is one section'
              + (f'; {nxt} ({term_code(nxt)}) is next term, already assigned' if nxt else '')
              + ', and the shaded column is the current term.</p>'
              + f'<div class="rec-wrap"><table class="rec" id="rec"><thead>{head}</thead><tbody>{rows}</tbody></table></div>')

    # ---------------------------------------------------------------- practicum schools (grouped by city, each with its website and a map link)
    def schools_html(k):
        sch = k.get('schools')
        if not sch: return ''
        from urllib.parse import quote_plus
        pin = ('<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false"><path d="M8 1.5a4.5 4.5 0 0 0-4.5 4.5c0 3.2 4.5 8.5 4.5 8.5s4.5-5.3 4.5-8.5A4.5 4.5 0 0 0 8 1.5Z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>'
               '<circle cx="8" cy="6" r="1.6" fill="currentColor"/></svg>')
        cities = []
        for x in sch:
            if x['city'] not in cities: cities.append(x['city'])
        out = (f'<details class="sch"><summary class="sch-h"><b>Practicum schools</b><span>{len(sch)} schools in {len(cities)} cities</span></summary>')
        for city in cities:
            items = ''
            for x in (x for x in sch if x['city'] == city):
                m = x.get('map') or 'https://www.google.com/maps/search/?api=1&query=' + quote_plus(f'{x["name"]} School, {x["city"]}, Kansas')
                nm = esc(x['name'])
                items += (f'<li><a class="sch-n" href="{attr(x["site"])}" rel="noopener" target="_blank">{nm}<span class="sr"> website, opens in a new tab</span></a>'
                          f'<a class="sch-p" href="{attr(m)}" rel="noopener" target="_blank" title="Map">{pin}<span class="sr">Map of {nm}, opens in a new tab</span></a></li>')
            out += f'<div class="sch-g"><h5>{esc(city)}</h5><ul>{items}</ul></div>'
        return out + '</details>'

    # ---------------------------------------------------------------- Kansas: the courses, most taught first
    blocks = '<h3 class="grp">Instructor of record</h3>'
    for k in sorted(courses, key=lambda k: (-n(k), -done(k), min(term_key(t) for t in k['taught']))):
        cid = k['code'].replace('&', '').replace(' ', '').lower()
        sq = '<i class="sq"></i>' * n(k)
        note = f'<p class="c-formerly">{md(k["note"])}</p>' if k.get('note') else ''
        blocks += (f'<article class="crs2{" rep" if n(k) > 1 else ""}" id="{cid}"><div class="crs2-code">{esc(k["code"])}'
                   f'<div class="crs2-count"><span class="big">{n(k)}</span>{"section" if n(k) == 1 else "sections"}</div>'
                   f'<div class="crs2-sq">{sq}</div></div><div class="crs2-body">'
                   f'<h4>{esc(k["title"]).replace("K-12", "K&#8209;12")}</h4>'
                   f'<p class="c-meta"><span>{k["level"]}</span><span>{when(k)}</span></p>{note}'
                   f'<p>{esc(k.get("summary", "")).replace("K-12", "K&#8209;12")}</p>'
                   + (f'<p class="c-prac">{esc(k["practicum"])}</p>' if k.get('practicum') else '') + schools_html(k) + '</div></article>')

    # ---------------------------------------------------------------- Kansas: courses where I assist (no sections table, no counts)
    ta = [k for g in C['teaching'] for k in g['courses'] if not k.get('taught') and k.get('role')]
    if ta:
        blocks += '<h3 class="grp">Teaching assistant</h3>'
        for k in ta:
            cid = k['code'].replace('&', '').replace(' ', '').lower()
            blocks += (f'<article class="crs2" id="{cid}"><div class="crs2-code">{esc(k["code"])}'
                       f'<div class="crs2-count">{esc(k.get("terms", ""))}</div></div><div class="crs2-body">'
                       f'<h4>{esc(k["title"])}</h4>'
                       + (f'<p>{esc(k["summary"])}</p>' if k.get('summary') else '') + '</div></article>')
        grp = next((g for g in C['teaching'] if g.get('partners')), None)
        if grp:
            imgs = ''.join(f'<li><a href="{attr(x["url"])}" rel="noopener" target="_blank">'
                           f'<img src="{attr(x["logo"])}" alt="" width="140" height="34" loading="lazy">'
                           f'<span class="sr">{esc(x["name"])}, opens in a new tab</span></a></li>' for x in grp['partners'])
            blocks += f'<div class="crs2 partners"><div class="crs2-code"></div><div class="crs2-body"><ul>{imgs}</ul></div></div>'

    # ---------------------------------------------------------------- teaching in Iran
    iran = sorted((a for a in C['appointments'] if a.get('site_text') and 'Iran' in a.get('place', '')),
                  key=lambda a: (not a.get('courses'), -int(re.findall(r'\d{4}', a['dates'])[0])))
    def place(a):
        lis = ''.join(f'<li><span class="c-code">{esc(x["code"])}</span> {esc(x["title"])}, {esc(x["level"])}, {esc(x["dates"])}</li>' for x in a.get('courses', []))
        aw = ''
        for h in C.get('honors', []):
            m = re.search(r'(\d{4})', h.get('note', ''))
            if m and a['org'] in h.get('note', ''):
                aw = ('<span class="aw"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">'
                      '<path d="M8.5 13.5 6.5 21l5.5-3 5.5 3-2-7.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>'
                      '<circle cx="12" cy="9" r="6" fill="currentColor"/></svg>'
                      f'<span><span class="sr">Award: </span>{esc(h["name"])}, {m.group(1)}</span></span>')
        parts = ''
        if a.get('parts'):
            parts = '<dl class="parts">' + ''.join(f'<div><dt>{esc(x["label"])}</dt><dd>{md(x["text"])}</dd></div>' for x in a['parts']) + '</dl>'
        return (f'<div class="place"><div class="p-head"><h3>{esc(a["org"])} <span class="p-when">{esc(a["dates"])}</span></h3>{aw}</div>'
                f'<p>{md(a["site_text"])}</p>' + parts
                + (f'<ul class="old">{lis}</ul>' if lis else '') + '</div>')
    iran_html = (h2('Teaching in Iran') + ''.join(place(a) for a in iran)) if iran else ''

    body = title('Teaching') + lead + record + blocks + iran_html
    return shell('teaching.html', 'Teaching', body)
