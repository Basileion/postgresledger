import json, os, shutil, html, itertools, datetime
ROOT = '/workspace/postgresledger'; D = ROOT + '/dist'
SITE = os.environ.get('SITE', 'https://basileion.github.io/postgresledger'); BASE = os.environ.get('BASE', '/postgresledger')
CHECKED = '2026-11-20'
V = json.load(open(ROOT + '/data/vendors.json')); BYID = {v['id']: v for v in V}
for v in V: v['co'] = v['id'] == 'planetscale'
e = html.escape
PROFILES = [
 ('hobby-1gb-10gb', 'Hobby: 1 GB RAM, 10 GB storage', 1, 10, False),
 ('small-4gb-50gb', 'Small production: 4 GB RAM, 50 GB storage', 4, 50, False),
 ('medium-8gb-100gb', 'Medium: 8 GB RAM, 100 GB storage', 8, 100, False),
 ('large-16gb-250gb', 'Large: 16 GB RAM, 250 GB storage', 16, 250, False),
 ('xl-32gb-500gb', 'XL: 32 GB RAM, 500 GB storage', 32, 500, False),
 ('ha-4gb-50gb', 'High availability: 4 GB RAM, 50 GB storage', 4, 50, True),
 ('ha-16gb-250gb', 'High availability: 16 GB RAM, 250 GB storage', 16, 250, True)]
MORE = [('TxMailCost', 'https://basileion.github.io/txmailcost/', 'transactional email API pricing by volume'),
        ('VPSLedger', 'https://vpsledger.pages.dev/', 'VPS true monthly cost'),
        ('AuthCost', 'https://authcost.pages.dev/', 'auth and identity pricing by MAU')]

def cost(p, R, S, ha):
    if p['ram'] is None or p['ram'] < R: return None
    if ha and not p['ha']: return None
    if p['incl'] is None: return p['base']
    if S <= p['incl']: return p['base']
    if p['extra'] is None or (p['maxs'] is not None and S > p['maxs']): return None
    return round(p['base'] + (S - p['incl']) * p['extra'], 2)
def best(v, R, S, ha):
    r = [(cost(p, R, S, ha), p) for p in v['plans']]; r = [x for x in r if x[0] is not None]
    if not r: return None
    r.sort(key=lambda x: x[0]); return r[0]
def money(x):
    if x is None: return '—'
    return f'${x:,.0f}' if abs(x - round(x)) < 0.005 else f'${x:,.2f}'
def dag(v): return '<sup title="See notes: part of the bill is not published as text">†</sup>' if v['read'] == 'partial' else ''

CSS = open('/workspace/txmailcost/dist/style.css').read().replace('--acc:#1d4e89', '--acc:#2f6b3a').replace('--acc2:#e8eef7', '--acc2:#e9f2ea')
URLS = []
def page(path, title, desc, body, noindex=False):
    canon = SITE + path
    rob = '<meta name="robots" content="noindex">' if noindex else ''
    more = ' · '.join(f'<a href="{u}">{n}</a> ({d})' for n, u, d in MORE)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canon}">{rob}
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}"><meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="PostgresLedger price log" href="/changes/feed.xml"><link rel="stylesheet" href="/style.css"></head><body>
<header><div class="w"><a class="brand" href="/">Postgres<span>Ledger</span></a><nav><a href="/#calc">Calculator</a><a href="/cost/small-4gb-50gb/">By workload</a><a href="/compare/">Compare</a><a href="/vendors/">Providers</a><a href="/changes/">Price log</a><a href="/about/">Methodology</a></nav></div></header>
<main class="w">{body}</main>
<footer><div class="w"><p><b>PostgresLedger</b> tracks published managed PostgreSQL prices for {len(V)} providers. Every price links to the vendor page it came from. Last checked {CHECKED}. Not affiliated with any provider; no paid placements. Verify on the vendor's page before you buy.</p>
<p><a href="/about/">Methodology</a> · <a href="/api/plans.json">JSON data</a> · <a href="/changes/feed.xml">RSS</a> · <a href="mailto:basileion.ops@gmail.com?subject=PostgresLedger%20correction">Report a wrong price</a></p>
<p>More pricing trackers: {more}</p></div></footer></body></html>"""
    doc = doc.replace('href="/', 'href="' + BASE + '/')
    out = D + path + ('index.html' if path.endswith('/') else '')
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w').write(doc)
    if not noindex: URLS.append(path)

def prof_table(vs=None, profs=PROFILES):
    vs = vs or V
    h = '<div class="tw"><table><thead><tr><th>Provider</th>' + ''.join(f'<th title="{e(p[1])}">{p[2]:g} GB / {p[3]} GB{" HA" if p[4] else ""}</th>' for p in profs) + '</tr></thead><tbody>'
    mins = {}
    for p in profs:
        c = [best(v, p[2], p[3], p[4]) for v in vs if not v['co']]; c = [x[0] for x in c if x]; mins[p[0]] = min(c) if c else None
    for v in vs:
        h += f'<tr><td><a href="/vendors/{v["id"]}/">{e(v["short"])}</a>{dag(v)}</td>'
        for p in profs:
            b = best(v, p[2], p[3], p[4])
            cls = ' class="best"' if b and b[0] == mins[p[0]] else ''
            h += f'<td{cls} title="{e(b[1]["plan"]) if b else "no published plan fits"}">{(money(b[0]) + (" + storage" if v["co"] else "")) if b else "—"}</td>'
        h += '</tr>'
    return h + '</tbody></table></div>'
def ranked(R, S, ha):
    r = [(best(v, R, S, ha), v) for v in V if not v['co']]; r = [(b[0], b[1], v) for b, v in r if b]; r.sort(key=lambda t: t[0]); return r
def psline(R, S, ha):
    b = best(BYID['planetscale'], R, S, ha)
    return f'<p class="card"><b>PlanetScale Postgres</b> compute for this workload: {money(b[0])}/mo ({e(b[1]["plan"])}), plus storage at a rate not printed on its pricing page, so it is not ranked. <a href="/vendors/planetscale/">Details</a>.</p>' if b else ''

shutil.rmtree(D, ignore_errors=True); os.makedirs(D); open(D + '/style.css', 'w').write(CSS)
NOTE = '<p class="note"><sup>†</sup> PlanetScale bills are compute only (extra storage rate not printed), so it is shown but not ranked. Aiven and DigitalOcean rows cover only the plans printed as text; see each provider page. Neon rows assume compute always on (730 h/mo). Prices are list, monthly, USD, before tax and egress.</p>'

# home
r_small = ranked(4, 50, False); r_ha = ranked(4, 50, True)
calc = """<script>const D=%s;function c(p,R,S,ha){if(p.ram===null||p.ram<R)return null;if(ha&&!p.ha)return null;if(p.incl===null)return p.base;if(S<=p.incl)return p.base;if(p.extra===null||(p.maxs!==null&&S>p.maxs))return null;return p.base+(S-p.incl)*p.extra}
function run(){const R=parseFloat(document.getElementById('r').value)||0,S=parseFloat(document.getElementById('s').value)||0,ha=document.getElementById('h').checked;const rows=D.map(d=>{let b=null;for(const p of d.plans){const x=c(p,R,S,ha);if(x!==null&&(b===null||x<b.c))b={c:x,p:p.plan}}return{n:d.short,id:d.id,co:d.co,b}});
rows.sort((a,b)=>((a.b&&!a.co)?a.b.c:1e12+(a.b?a.b.c:1e11))-((b.b&&!b.co)?b.b.c:1e12+(b.b?b.b.c:1e11)));const f=x=>'$'+x.toLocaleString('en-US',{minimumFractionDigits:x%%1?2:0,maximumFractionDigits:2});
document.getElementById('out').innerHTML='<table><thead><tr><th>#</th><th>Provider</th><th style="text-align:left">Cheapest fitting plan</th><th>Per month</th><th>Per year</th></tr></thead><tbody>'+rows.map((r,i)=>'<tr'+(i==0&&r.b&&!r.co?' class="best"':'')+'><td>'+(i+1)+'</td><td style="text-align:left"><a href="BASE/vendors/'+r.id+'/">'+r.n+'</a></td><td style="text-align:left">'+(r.b?r.b.p:'no published plan fits')+'</td><td>'+(r.b?f(Math.round(r.b.c*100)/100)+(r.co?' + storage':''):'—')+'</td><td>'+(r.b&&!r.co?f(Math.round(r.b.c*1200)/100):'—')+'</td></tr>').join('')+'</tbody></table>'}
['r','s','h'].forEach(i=>document.getElementById(i).addEventListener('input',run));run();</script>""" % json.dumps([{'short': v['short'], 'id': v['id'], 'co': v['co'], 'plans': v['plans']} for v in V])
calc = calc.replace('BASE/', BASE + '/')
body = f"""<p class="eb" style="margin-top:34px">Managed PostgreSQL pricing · checked {CHECKED}</p>
<h1>What a managed Postgres database really costs</h1>
<p class="lede">Published prices for {len(V)} managed PostgreSQL providers, normalized to one monthly bill for the RAM, storage and availability you need. Every number links to the vendor's own pricing page.</p>
<div class="grid">
<div class="card"><div class="mut">Cheapest for 4 GB RAM / 50 GB</div><div class="big">{money(r_small[0][0])}</div><div>{e(r_small[0][2]['short'])}, {e(r_small[0][1]['plan'])}</div></div>
<div class="card"><div class="mut">Priciest for the same workload</div><div class="big">{money(r_small[-1][0])}</div><div>{e(r_small[-1][2]['short'])}, {e(r_small[-1][1]['plan'])}</div></div>
<div class="card"><div class="mut">Cheapest HA, 4 GB RAM / 50 GB</div><div class="big">{money(r_ha[0][0])}</div><div>{e(r_ha[0][2]['short'])}, {e(r_ha[0][1]['plan'])}</div></div></div>
<h2 id="calc">Calculator</h2><p class="mut">Minimum RAM and storage you need. Picks each provider's cheapest published plan that fits.</p>
<label>RAM (GB)<input id="r" inputmode="decimal" value="4"></label><label>Storage (GB)<input id="s" inputmode="decimal" value="50"></label><label style="flex-direction:row;align-items:center;gap:6px"><input id="h" type="checkbox" style="min-width:0"> High availability</label>
<div id="out" class="tw" style="margin-top:14px"></div>{NOTE}
<h2>Monthly bill by workload</h2>{prof_table()}<p class="note">Green = cheapest for that workload. Hover a cell for the plan used. — = no published plan fits.</p>
<h2>Popular comparisons</h2><ul class="links">{''.join(f'<li><a href="/compare/{"-vs-".join(sorted([a,b]))}/">{e(BYID[a]["short"])} vs {e(BYID[b]["short"])}</a></li>' for a,b in [('neon','supabase'),('digitalocean','render'),('heroku','render'),('planetscale','neon'),('supabase','render'),('aiven','digitalocean'),('heroku','digitalocean'),('planetscale','supabase')])}</ul>
<h2>Workloads</h2><ul class="links">{''.join(f'<li><a href="/cost/{p[0]}/">{e(p[1])}</a></li>' for p in PROFILES)}</ul>{calc}"""
page('/', 'Managed Postgres Pricing Compared (Nov 2026): Neon, Supabase, RDS alternatives | PostgresLedger'.replace(', RDS alternatives', ', DigitalOcean, Render, Heroku'),
     f'Monthly cost of managed PostgreSQL on {len(V)} providers for the RAM, storage and HA you need, from published pricing checked {CHECKED}.', body)

# vendors
lis = ''
for v in V:
    rows = ''.join(f'<tr><td>{e(p["plan"])}</td><td>{p["ram"]:g} GB</td><td>{e(str(p["vcpu"]))}</td><td>{("starting volume" if p["incl"] is None else (str(p["incl"])+" GB"))}</td><td>{("$%.3g/GB" % p["extra"]) if p["extra"] is not None else "—"}</td><td>{"Yes" if p["ha"] else "No"}</td><td>{money(p["base"])}</td></tr>' for p in v['plans'])
    costs = ''.join(f'<tr><td><a href="/cost/{p[0]}/">{e(p[1])}</a></td><td>{money(best(v,p[2],p[3],p[4])[0]) if best(v,p[2],p[3],p[4]) else "—"}</td><td>{e(best(v,p[2],p[3],p[4])[1]["plan"]) if best(v,p[2],p[3],p[4]) else "no published plan fits"}</td></tr>' for p in PROFILES)
    alts = ''.join(f'<li><a href="/compare/{"-vs-".join(sorted([v["id"], o["id"]]))}/">{e(v["short"])} vs {e(o["short"])}</a></li>' for o in V if o['id'] != v['id'])
    body = f"""<p class="eb" style="margin-top:34px"><a href="/vendors/">Providers</a> · checked {v['checked']}</p><h1>{e(v['name'])} pricing</h1>
<p class="lede">Published plans read from <a href="{v['source']}" rel="nofollow noopener">{e(v['source'])}</a> on {v['checked']}.</p><div class="card"><b>Free tier:</b> {e(v['free'])}</div>
<h2>Monthly bill by workload</h2><div class="tw"><table><thead><tr><th>Workload</th><th>Bill{dag(v)}</th><th style="text-align:left">Plan used</th></tr></thead><tbody>{costs}</tbody></table></div>
<h2>Published plans</h2><div class="tw"><table><thead><tr><th>Plan</th><th>RAM</th><th>vCPU</th><th>Storage incl.</th><th>Extra storage</th><th>HA</th><th>$/mo</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Notes</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in v['notes'])}</ul><h2>Compare {e(v['short'])}</h2><ul class="links">{alts}</ul>"""
    page(f'/vendors/{v["id"]}/', f'{v["name"]} Pricing (Nov 2026): Plans, Storage, HA | PostgresLedger', f'{v["name"]} plan prices, RAM, included storage and HA, with monthly cost for common workloads. Source checked {v["checked"]}.', body)
    lis += f'<li><a href="/vendors/{v["id"]}/">{e(v["name"])}</a></li>'
page('/vendors/', 'Managed Postgres Providers | PostgresLedger', 'Pricing pages for each tracked managed PostgreSQL provider.', f'<h1>Providers</h1><ul class="links">{lis}</ul>')

# compare
cl = ''
for a, b in itertools.combinations(sorted(BYID), 2):
    A, B = BYID[a], BYID[b]; lines = []
    for p in PROFILES:
        ba, bb = best(A, p[2], p[3], p[4]), best(B, p[2], p[3], p[4])
        if ba and bb:
            if abs(ba[0] - bb[0]) < 0.005: lines.append(f'<li>{e(p[1])}: tie at {money(ba[0])}.</li>')
            else:
                w, wl, ll = (A, ba, bb) if ba[0] < bb[0] else (B, bb, ba)
                lines.append(f'<li>{e(p[1])}: {e(w["short"])} is cheaper, {money(wl[0])} ({e(wl[1]["plan"])}) vs {money(ll[0])}.</li>')
        elif ba or bb:
            w = A if ba else B; lines.append(f'<li>{e(p[1])}: only {e(w["short"])} publishes a plan that fits.</li>')
    body = f"""<p class="eb" style="margin-top:34px"><a href="/compare/">Compare</a> · checked {CHECKED}</p><h1>{e(A['short'])} vs {e(B['short'])} Postgres pricing</h1>
<p class="lede">Monthly bill for the same workload on each, using the cheapest published plan that fits.</p>{prof_table([A, B])}
<h2>Verdict by workload</h2>{"<p class='mut'>PlanetScale figures are compute only; its extra storage rate is not printed, so verdicts involving it understate its bill.</p>" if (A['co'] or B['co']) else ""}<ul>{''.join(lines)}</ul>
<div class="grid"><div class="card"><h3>{e(A['name'])}</h3><p><b>Free:</b> {e(A['free'])}</p><ul>{''.join(f'<li>{e(x)}</li>' for x in A['notes'])}</ul></div>
<div class="card"><h3>{e(B['name'])}</h3><p><b>Free:</b> {e(B['free'])}</p><ul>{''.join(f'<li>{e(x)}</li>' for x in B['notes'])}</ul></div></div>{NOTE}"""
    page(f'/compare/{a}-vs-{b}/', f'{A["short"]} vs {B["short"]} Postgres Pricing (Nov 2026) | PostgresLedger', f'{A["short"]} vs {B["short"]} managed Postgres: monthly cost for hobby to XL and HA workloads, from published pricing checked {CHECKED}.', body)
    cl += f'<li><a href="/compare/{a}-vs-{b}/">{e(A["short"])} vs {e(B["short"])}</a></li>'
page('/compare/', 'Managed Postgres Pricing Comparisons | PostgresLedger', 'Head-to-head managed Postgres pricing for every pair of tracked providers.', f'<h1>Compare providers</h1><ul class="links">{cl}</ul>')

# cost pages
for p in PROFILES:
    r = ranked(p[2], p[3], p[4])
    rows = ''.join(f'<tr{" class=best" if i==0 else ""}><td>{i+1}</td><td><a href="/vendors/{v["id"]}/">{e(v["short"])}</a>{dag(v)}</td><td style="text-align:left">{e(pl["plan"])}</td><td>{money(c)}</td><td>{money(round(c*12,2))}</td></tr>' for i, (c, pl, v) in enumerate(r))
    missing = [v['short'] for v in V if not v['co'] and not best(v, p[2], p[3], p[4])]
    nav = ' · '.join(f'<a href="/cost/{q[0]}/">{q[2]:g} GB{" HA" if q[4] else ""}</a>' for q in PROFILES)
    body = f"""<p class="eb" style="margin-top:34px">By workload · checked {CHECKED}</p><h1>Managed Postgres cost: {e(p[1])}</h1>
<p class="lede">Cheapest published plan on each provider with at least {p[2]:g} GB RAM and {p[3]} GB storage{", with high availability" if p[4] else ""}.</p><p>Other workloads: {nav}</p>
<div class="tw"><table><thead><tr><th>#</th><th>Provider</th><th style="text-align:left">Plan</th><th>Per month</th><th>Per year</th></tr></thead><tbody>{rows}</tbody></table></div>
{psline(p[2], p[3], p[4])}{"<p class='mut'>No published plan fits on: " + e(", ".join(missing)) + ".</p>" if missing else ""}{NOTE}"""
    page(f'/cost/{p[0]}/', f'Managed Postgres Cost for {p[2]:g} GB RAM, {p[3]} GB Storage{" (HA)" if p[4] else ""}: {len(r)} Providers | PostgresLedger',
         f'Monthly cost of managed PostgreSQL with {p[2]:g} GB RAM and {p[3]} GB storage{" in high availability" if p[4] else ""}. Cheapest published: {r[0][2]["short"]} at {money(r[0][0])}.', body)

# changes + rss
chg = [{'date': CHECKED, 'title': f'Baseline: {len(V)} providers, {sum(len(v["plans"]) for v in V)} plan rows', 'text': 'First published snapshot. Future price changes will be logged here with old and new values.'}]
page('/changes/', 'Managed Postgres Price Change Log | PostgresLedger', 'Dated log of managed PostgreSQL price changes.', '<h1>Price log</h1><p class="mut">Subscribe via <a href="/changes/feed.xml">RSS</a>.</p>' + ''.join(f'<div class="card"><div class="note">{c["date"]}</div><h3>{e(c["title"])}</h3><p>{e(c["text"])}</p></div>' for c in chg))
open(D + '/changes/feed.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>PostgresLedger price log</title><link>' + SITE + '/changes/</link><description>Managed PostgreSQL price changes</description>' + ''.join(f'<item><title>{e(c["title"])}</title><link>{SITE}/changes/</link><guid isPermaLink="false">{c["date"]}-{i}</guid><pubDate>{datetime.datetime.strptime(c["date"],"%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 -0500")}</pubDate><description>{e(c["text"])}</description></item>' for i, c in enumerate(chg)) + '</channel></rss>')
page('/about/', 'Methodology | PostgresLedger', 'How PostgresLedger reads and normalizes managed Postgres prices.', f"""<h1>Methodology</h1><ul>
<li>Prices come from each provider's public pricing page and are stored with the source URL and check date ({CHECKED}).</li>
<li>For a workload (minimum RAM, storage, optional HA), each plan with enough RAM is priced as its monthly price plus any published per-GB storage beyond what it includes. Plans that cannot reach the storage are skipped. The cheapest plan per provider is shown.</li>
<li>Usage-billed compute (Neon) is priced always-on at 730 hours a month; scale-to-zero lowers real bills for idle databases.</li>
<li>Where part of a bill is not printed as text (PlanetScale extra storage, larger Aiven plans, DigitalOcean standby nodes) the row is marked <sup>†</sup> and the limitation is stated on the provider page.</li>
<li>Monthly list price, USD, before tax, backups beyond defaults, and egress. No estimated or invented numbers.</li></ul>""")
os.makedirs(D + '/api', exist_ok=True)
json.dump({'checked': CHECKED, 'unit': 'USD per month', 'providers': V}, open(D + '/api/plans.json', 'w'), indent=1)
open(D + '/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{u}</loc><lastmod>{CHECKED}</lastmod></url>' for u in URLS) + '</urlset>')
open(D + '/llms.txt', 'w').write(f'# PostgresLedger\n> Published managed PostgreSQL pricing for {len(V)} providers, normalized to monthly cost by RAM, storage and HA. Checked {CHECKED}.\n\n- Data: {SITE}/api/plans.json\n' + ''.join(f'- {p[1]}: {SITE}/cost/{p[0]}/\n' for p in PROFILES) + ''.join(f'- {v["name"]}: {SITE}/vendors/{v["id"]}/ (source {v["source"]})\n' for v in V))
K = open(ROOT + '/indexnow.key').read().strip(); open(D + f'/{K}.txt', 'w').write(K)
open(D + '/.nojekyll', 'w').write('')
page('/404/', 'Not found | PostgresLedger', 'Not found', '<h1>Page not found</h1><p><a href="/">Back to the calculator</a></p>', noindex=True)
shutil.move(D + '/404/index.html', D + '/404.html'); os.rmdir(D + '/404')
print('pages', len(URLS))
for p in PROFILES: print(p[0], [(round(c,2), v['short']) for c, pl, v in ranked(p[2], p[3], p[4])])
