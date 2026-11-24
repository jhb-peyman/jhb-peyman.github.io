# Service page. Run by pages.py (uses its helpers: C, esc, attr, h2, title, shell).
# Same language as the Teaching page: sections opened by a strong rule, count blocks with one square each.

def page_service():
    pr = C['peer_review']
    js = [(j, int(j['count'].split()[0])) for j in pr['journals']]
    words = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
    total = sum(n for _, n in js)

    confs = pr.get('conferences', [])
    lead = (f'<p class="lead">I review for {words.get(len(js), str(len(js)))} journals' + (' and for TESOL International Association' if any('TESOL' in x.get('org', '') for x in confs) else '')
            + ', and have served on student and institutional boards at the University of Kansas and in Isfahan.</p>')

    blocks = ''
    for j, n in sorted(js, key=lambda x: -x[1]):
        sq = ''.join('<i class="sq"></i>' for _ in range(n))
        blocks += (f'<article class="crs2 rep"><div class="crs2-code"><div class="crs2-count"><span class="big">{n}</span>{"review" if n == 1 else "reviews"}</div>'
                   f'<div class="crs2-sq">{sq}</div></div><div class="crs2-body">'
                   f'<h3 class="jh">' + (f'<img class="jlogo" src="{attr(j["logo"])}" alt="" width="28" height="28" loading="lazy">' if j.get('logo') else '')
                   + f'<a class="jn" href="{attr(j["url"])}"><i>{esc(j["name"])}</i></a></h3>'
                   f'<p class="c-meta"><span>{esc(j.get("about", ""))}</span></p></div></article>')
    review = ('<section class="tsec">' + h2('Peer Review')
              + f'<p class="sec-role">{esc(pr["role"]).capitalize()}, {esc(pr["dates"])}: {total} manuscript reviews for {words.get(len(js), str(len(js)))} journals.</p>'
              + f'<div class="sv-rev">{blocks}</div>'
              + (('<h3 class="grp">Conference proposals</h3><div class="sv-conf">' + ''.join(
                    f'<div class="place"><h4 class="jh">' + (f'<img class="jlogo" src="{attr(x["logo"])}" alt="" width="28" height="28" loading="lazy">' if x.get('logo') else '')
                    + (f'<a class="jn" href="{attr(x["url"])}">{esc(x["name"])}</a>' if x.get('url') else esc(x['name']))
                    + f' <span class="p-when">{esc(x.get("date", ""))}</span></h4>'
                    f'<p class="sv-org">{esc(x.get("role", "Proposal reviewer"))}, {esc(x.get("org", ""))}</p></div>' for x in confs) + '</div>') if confs else '')
              + '</section>')

    def entry(l):
        txt = f'<p>{esc(l["text"])}</p>' if l.get('text') else ''
        return (f'<div class="place"><h3>{esc(l["role"])} <span class="p-when">{esc(l["dates"])}</span></h3>'
                f'<p class="sv-org">{esc(l["site_who"])}</p>{txt}</div>')
    lead_sec = ('<section class="tsec">' + h2('Leadership') + ''.join(entry(l) for l in C['leadership']) + '</section>')

    body = title('Service') + lead + review + lead_sec
    return shell('service.html', 'Service', body)
