#!/usr/bin/env python3
"""Builds the crawlable library pages from the DB inside app/index.html.
Run from the repo root: python3 tools/build_pages.py"""
import json,re,html,os,collections as C,datetime as D
from PIL import Image
BASE='https://library.rocketlaunchmedia.com'
MAIN='https://rocketlaunchmedia.com'
OG='https://assets.cdn.filesafe.space/Efz8i2ENy3c5GGhI7Ly9/media/6ae8d0db736386d0dce694cb.png'
TODAY=D.date.today().isoformat()
t=open('app/index.html',encoding='utf8').read()
l=[x for x in t.split('\n') if x.startswith('const DB=')][0]
db=json.loads(l[l.index('['):l.rindex(']')+1])
ga=re.search(r'<script async src="https://www.googletagmanager.com/gtag/js.*?fbq\(\'init\'.*?\n',t,re.S).group(0)
if '</script>' not in ga.split("fbq('init'")[-1]: ga=ga.rstrip()+'</script>\n'
rep={}
for d in db:
    if d['fam'] not in rep or d.get('rep'): rep[d['fam']]=d
ALL=[d for d in rep.values() if not d['facets']['case'][0].startswith('Not imm')]
e=html.escape
n=lambda x:f"{x:,}"
def img(d):
    u=d.get('image') or d.get('thumb') or next((c['i'] for c in d.get('cards') or [] if c.get('i')),'')
    return u if u.startswith('/ads/') else ''
def dims(u):
    try:
        with Image.open('.'+u) as i: return i.size
    except Exception: return (720,720)
def clean(s,m):
    s=re.sub(r'\s+',' ',s or '').strip()
    s=re.sub(r'#\w+','',s).strip()
    return s if len(s)<=m else s[:m].rsplit(' ',1)[0]+'…'
def head(d):
    h=(d.get('headline') or '').strip()
    if len(h)<12 or re.search(r'\.(com|net|org)|^fb\b|whatsapp|Abogad[oa] .*Inmigraci|Law Firm|Law Group|PLLC',h,re.I): h=(d.get('hook') or '').strip()
    if len(h)<12 or re.search(r'\.(com|net|org)$',h): h=(d.get('copy') or '').strip().split('\n')[0]
    return clean(h,90)
def rank(d):
    s=(d.get('score') or {}).get('total') or 60
    return (s,min(d.get('days') or 0,180))
def pick(rows,k=36,cap=3):
    out=[];c=C.Counter()
    for d in sorted([r for r in rows if img(r) and (r.get('copy') or '').strip()],key=rank,reverse=True):
        if c[d['adv']]>=cap: continue
        c[d['adv']]+=1;out.append(d)
        if len(out)==k: break
    return out
def card(d,i):
    u=img(d);w,h=dims(u);title=head(d);lang=d['lang'];fmt=d['fmt'] if d['fmt']!='Dynamic' else 'Image'
    case=d['facets']['case'][0]
    alt=f"{lang} {fmt.lower()} ad from {d['adv']} about {case.lower()}: {title}"
    load='eager' if i<2 else 'lazy'
    days=f"Ran {n(d['days'])} days" if d.get('days') else ''
    meta=' · '.join(x for x in [lang,fmt,'Running' if d['status']=='Active' else 'Stopped',days] if x)
    badge='<span class="tag">Video</span>' if d['fmt']=='Video' else ''
    lib=f'<a href="{e(d["lib"])}" rel="nofollow noopener" target="_blank">See in Meta Ad Library</a>' if d.get('lib') else ''
    return f'''<article class="ad"><div class="thumb">{badge}<img src="{u}" alt="{e(alt)}" width="{w}" height="{h}" loading="{load}" decoding="async"></div><div class="body"><h3 lang="{'es' if lang=='Spanish' else 'en'}">{e(title)}</h3><p class="firm">{e(d['adv'])}</p><p class="copy">{e(clean(d.get('copy'),190))}</p><p class="meta">{e(meta)}</p>{lib}</div></article>'''
def pct(a,b): return round(100*a/b) if b else 0
def stats(rows):
    N=len(rows);lg=C.Counter(d['lang'] for d in rows);hk=C.Counter(d['facets'].get('hook',['?'])[0] for d in rows);hk.pop('?',None)
    fl=C.Counter(f for d in rows for f in d['facets']['flag']);ds=C.Counter(d['facets']['dest'][0] for d in rows);ds.pop('Not in record',None)
    return dict(N=N,firms=len({d['adv'] for d in rows}),lg=lg,hk=hk,fl=fl,ds=ds,act=sum(d['status']=='Active' for d in rows),maxd=max([d.get('days') or 0 for d in rows] or [0]),vid=sum(d['fmt']=='Video' for d in rows))
def insights(s):
    o=[]
    tl,tc=s['lg'].most_common(1)[0]
    o.append(f"<b>{pct(tc,s['N'])}%</b> of these creatives are in {tl}.")
    if s['hk']:
        h,c=s['hk'].most_common(1)[0];o.append(f"The most common hook style is <b>{e(h.lower())}</b>, used in {pct(c,s['N'])}%.")
    o.append(f"<b>{pct(s['fl'].get('Price/offer stated',0),s['N'])}%</b> state a price or offer in the ad.")
    if s['ds']:
        h,c=s['ds'].most_common(1)[0];o.append(f"The most common known destination is <b>{e(h.lower())}</b>.")
    o.append(f"<b>{pct(s['vid'],s['N'])}%</b> are video and <b>{pct(s['N']-s['vid'],s['N'])}%</b> are image or carousel ads.")
    o.append(f"<b>{n(s['act'])}</b> were running when last checked. The longest ran <b>{n(s['maxd'])}</b> days.")
    return '<ul class="ins">'+''.join(f'<li>{x}</li>' for x in o)+'</ul>'
CASES=[
('deportation-defense-ads','Removal defense','Deportation Defense','deportation','Deportation Defense Ad Examples From Real Law Firms','These ads speak to families in a crisis, so most lead with a detention, a court date or a recent policy change. Look at how each one turns fear into one clear next step.',f'{MAIN}/law-firm-ad-library/deportation-defense-ads/'),
('employment-visa-ads','Employment immigration','Employment Visa','employment','Employment Visa Ad Examples From Immigration Firms','This is the most English-heavy group in the library. Many ads speak directly to professionals, founders and sponsors, and they often send people to a landing page or form instead of a chat.',f'{MAIN}/law-firm-ad-library/employment-visa-ads/'),
('marriage-green-card-ads','Marriage/family green card','Marriage Green Card','marriage','Marriage Green Card Ad Examples From Immigration Firms','Family ads usually lead with a couple or a parent and child. Watch how firms handle common worries, like an unlawful entry or a past denial, without promising an outcome.',f'{MAIN}/law-firm-ad-library/marriage-green-card-ads/'),
('t-u-visa-ads','T/U visa','T and U Visa','t-u-visa','T Visa and U Visa Ad Examples From Immigration Firms','These ads have to explain a little-known option to people who may not know they qualify. The better ones open with a plain question about what the person went through.',f'{MAIN}/facebook-ads-for-immigration-law-firms/'),
('vawa-ads','VAWA','VAWA','vawa','VAWA Ad Examples From Immigration Law Firms','VAWA ads need a careful tone. Compare how firms talk about abuse, privacy and self-petitioning without pressure or graphic language.',f'{MAIN}/facebook-ads-for-immigration-law-firms/'),
('asylum-ads','Asylum','Asylum','asylum','Asylum Lawyer Ad Examples From Immigration Firms','Asylum ads tend to focus on deadlines, interviews and preparation. See which firms sell clarity on the process instead of a result.',f'{MAIN}/law-firm-ad-library/asylum-ads/'),
('humanitarian-ads','Humanitarian/other relief','Humanitarian Relief','humanitarian-other-relief','Humanitarian Relief Ad Examples From Immigration Firms','This group covers programs like parole, TPS and DACA, where the news moves fast. Many ads are built around a date or a policy update.',f'{MAIN}/facebook-ads-for-immigration-law-firms/'),
('citizenship-ads','Citizenship','Citizenship','citizenship','Citizenship Lawyer Ad Examples From Immigration Firms','Citizenship ads are often simpler and calmer than other immigration ads. Many lean on a flat fee, a test change or the safety of finishing the process.',f'{MAIN}/law-firm-ad-library/citizenship-ads/'),
('waiver-ads','Waivers','Waiver','waivers','Immigration Waiver Ad Examples From Law Firms','Waiver ads have to explain a hard concept quickly. Note how firms use a simple yes or no question to help people see whether this applies to them.',f'{MAIN}/facebook-ads-for-immigration-law-firms/'),
]
FORMATS=[
('static-ads','Static Immigration Ad Examples','Static Ads',lambda d:d['fmt'] in('Image','Dynamic','Carousel'),'format=image','Image and carousel ads from US immigration firms. Use these when you need a new ad fast and do not have video.',f'{MAIN}/facebook-ads-for-immigration-law-firms/','Read the Facebook ads guide'),
('video-ads','Immigration Lawyer Video Ad Examples','Video Ads',lambda d:d['fmt']=='Video','format=video','Video ads from US immigration firms, from attorney talking heads to client stories. Study the first line, since that is where most of these ads win or lose attention.',f'{MAIN}/video-marketing-for-immigration-law-firms/','Read the video marketing guide'),
('spanish-ads','Spanish Immigration Ad Examples','Spanish Ads',lambda d:d['lang']=='Spanish','lang=es','Spanish is the main language of this library. These examples show how firms speak to Spanish-speaking families in their own words.',f'{MAIN}/spanish-marketing-for-immigration-law-firms/','Read the Spanish marketing guide'),
]
NAV=[(c[0],c[2]) for c in CASES]+[(f[0],f[2]) for f in FORMATS]
CSS=""":root{--ink:#10162f;--tx:#3d4460;--mut:#6b7188;--line:#e7dfd5;--bg:#fff9f3;--pan:#fff;--or:#cf4a12;--or2:#e9702d;--soft:#fdebdc}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.6 "DM Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--or)}img{max-width:100%;height:auto;display:block}h1,h2,h3{color:var(--ink);font-family:Syne,"DM Sans",system-ui,sans-serif;line-height:1.15;margin:0}
.bar{background:var(--or);color:#fff;display:flex;gap:12px;align-items:center;justify-content:center;padding:8px 14px;font-weight:600;font-size:15px;text-align:center;flex-wrap:wrap}.bar a{background:#fff;color:var(--or);padding:4px 12px;border-radius:999px;text-decoration:none;white-space:nowrap}.wrap{max-width:1180px;margin:0 auto;padding:0 20px}header.top{background:var(--ink)}header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:14px;padding-bottom:14px}
.logo{white-space:nowrap;color:#fff;font:700 18px Syne,sans-serif;text-decoration:none}.btn{display:inline-block;background:var(--or);color:#fff;padding:11px 20px;border-radius:999px;font-weight:600;text-decoration:none}.btn.alt{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}header .btn{padding:8px 14px;font-size:14px;white-space:nowrap}
.crumb{font-size:14px;color:var(--mut);padding-top:18px}.crumb a{color:var(--mut)}.hero{padding:30px 0 28px}.hero h1{font-size:clamp(32px,5vw,54px);max-width:900px}.hero p{font-size:19px;max-width:760px;margin:16px 0 22px}.cta{display:flex;gap:12px;flex-wrap:wrap}
.statrow{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:26px 0}.stat{background:var(--pan);border:1px solid var(--line);border-radius:14px;padding:16px}.stat b{display:block;color:var(--ink);font:700 28px Syne,sans-serif}.stat span{font-size:14px;color:var(--mut)}
section{padding:26px 0}section h2{font-size:clamp(24px,3vw,32px);margin-bottom:14px}.ins{margin:0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.ins li{background:var(--pan);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.ins b{color:var(--ink)}
.chips{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}.chip{background:var(--pan);border:1px solid var(--line);border-radius:14px;padding:16px;text-decoration:none;color:var(--ink);font-weight:600;display:flex;justify-content:space-between;gap:10px}.chip span{color:var(--or);white-space:nowrap}
.grid{columns:3 300px;column-gap:16px}.ad{break-inside:avoid;background:var(--pan);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin:0 0 16px}.thumb{position:relative;background:#f3ece4}.tag{position:absolute;left:10px;top:10px;background:var(--ink);color:#fff;font-size:12px;padding:3px 9px;border-radius:999px}.body{padding:14px}.body h3{font:600 17px/1.3 "DM Sans",sans-serif}.firm{margin:6px 0;font-size:14px;color:var(--mut)}.copy{margin:6px 0;font-size:15px}.meta{margin:8px 0;font-size:13px;color:var(--mut)}.body a{font-size:14px}
details{background:var(--pan);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:10px}summary{cursor:pointer;color:var(--ink);font-weight:600}.note{font-size:14px;color:var(--mut)}
footer{background:var(--ink);color:#c8cbd8;margin-top:30px;padding:28px 0;font-size:14px}footer a{color:#fff}footer .links{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:6px 16px;margin-bottom:18px}
@media(max-width:700px){.bar{font-size:13px;padding:6px 10px;gap:8px}.logo{font-size:16px}.statrow{grid-template-columns:repeat(2,1fr)}.ins{grid-template-columns:1fr}.hero{padding-top:18px}.grid{columns:1}}"""
def page(path,title,desc,h1,lead,body,crumbs,faq=None,items=None,cta=None):
    url=BASE+path
    ld=[{"@type":"CollectionPage","@id":url+"#page","url":url,"name":title,"description":desc,"inLanguage":"en","dateModified":TODAY,"isPartOf":{"@type":"WebSite","name":"Law Firm Ad Library","url":BASE+"/"},"publisher":{"@type":"Organization","name":"Rocket Launch Media","url":MAIN+"/"}}]
    ld.append({"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":a,"item":BASE+b} for i,(a,b) in enumerate(crumbs)]})
    if items: ld.append({"@type":"ItemList","numberOfItems":len(items),"itemListElement":[{"@type":"ListItem","position":i+1,"name":head(d),"url":d['lib']} for i,d in enumerate(items) if d.get('lib')]})
    if faq: ld.append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]})
    fq=''
    if faq: fq='<section class="wrap" id="faq"><h2>Questions</h2>'+''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in faq)+'</section>'
    cr=' / '.join((f'<a href="{b}">{e(a)}</a>' if i<len(crumbs)-1 else e(a)) for i,(a,b) in enumerate(crumbs))
    links=''.join(f'<a href="/{s}/">{e(x)}</a>' for s,x in NAV)
    hash_js='<script>if(location.pathname==="/"&&location.hash.length>1)location.replace("/app/"+location.hash);</script>' if path=='/' else ''
    cta=cta or '<a class="btn" href="/app/" data-ev="open_library">Browse all ads</a>'
    doc=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
{hash_js}<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:site_name" content="Law Firm Ad Library"><meta property="og:url" content="{url}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{OG}"><meta property="og:image:width" content="1734"><meta property="og:image:height" content="907"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{OG}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700&family=Syne:wght@600;700&display=swap">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@graph":ld},ensure_ascii=False).replace("</","<\\/")}</script>
{ga}</head><body>
<div class="bar" id="rlmbar"><span>Need more qualified leads for your immigration law firm?</span><a href="{MAIN}/law-marketing/?utm_source=library&amp;utm_medium=announcement_bar&amp;utm_campaign=ad_audit" data-ev="cta_audit">Get your ads audited</a></div>
<header class="top"><div class="wrap"><a class="logo" href="/">Law Firm Ad Library</a><a class="btn" href="/app/" data-ev="open_library">Open the library</a></div></header>
<main><div class="wrap">{'<nav class="crumb" aria-label="Breadcrumb">'+cr+'</nav>' if path!='/' else ''}<div class="hero"><h1>{e(h1)}</h1><p>{lead}</p><div class="cta">{cta}</div></div></div>{body}{fq}</main>
<footer><div class="wrap"><div class="links">{links}<a href="/about/">About this library</a></div><p>Research only. No spend or results data. Ads belong to the advertisers shown. Source: Meta Ad Library, including data via Foreplay. Built by <a href="{MAIN}/">Rocket Launch Media</a>. We use analytics cookies. <a href="{MAIN}/privacy-policy/">Privacy</a></p></div></footer>
<script>document.addEventListener("click",function(e){{var a=e.target.closest("a[data-ev]");if(!a)return;try{{gtag("event",a.dataset.ev,{{page:location.pathname}})}}catch(_){{}}try{{fbq("trackCustom",a.dataset.ev,{{page:location.pathname}})}}catch(_){{}}}});</script>
</body></html>
'''
    d='.'+path
    os.makedirs(d,exist_ok=True)
    open(d+'index.html','w',encoding='utf8').write(doc)
    return path
def gallery(rows,title='Ad examples'):
    return f'<section class="wrap"><h2>{e(title)}</h2><div class="grid">'+''.join(card(d,i) for i,d in enumerate(rows))+'</div></section>'
def statrow(s):
    return f'<div class="wrap"><div class="statrow"><div class="stat"><b>{n(s["N"])}</b><span>unique creatives</span></div><div class="stat"><b>{n(s["firms"])}</b><span>law firms</span></div><div class="stat"><b>{n(s["act"])}</b><span>running when last checked</span></div><div class="stat"><b>{pct(s["lg"].get("Spanish",0),s["N"])}%</b><span>in Spanish</span></div></div></div>'
def related(cur):
    x=[(s,a) for s,a in NAV if s!=cur]
    return '<section class="wrap"><h2>Browse more ad examples</h2><div class="chips">'+''.join(f'<a class="chip" href="/{s}/">{e(a)} <span>→</span></a>' for s,a in x)+'</div></section>'
paths=['/']
tot=len(db);cre=len(rep);firms=len({d['adv'] for d in db})
# case pages
for slug,fac,short,dl,h1,intro,main in CASES:
    rows=[d for d in ALL if d['facets']['case'][0]==fac];s=stats(rows);sel=pick(rows)
    title=h1 if len(h1)<=60 else f'{short} Ad Examples for Law Firms'
    desc=f"See {n(s['N'])} real {short.lower()} ads from {n(s['firms'])} US immigration law firms, with hooks, offers and language trends from the Meta Ad Library."
    deep=f"/app/#swipe?case={dl}"
    body=statrow(s)+f'<section class="wrap"><h2>What stands out</h2>{insights(s)}<p class="note">Based on {n(s["N"])} unique creatives in the library on {TODAY}. Running time is not proof of results.</p></section>'+gallery(sel,f'{len(sel)} {short.lower()} ads to study')+f'<section class="wrap"><h2>Want the strategy behind these ads?</h2><p>This page shows the examples. For the explanation, read <a href="{main}">our guide on Rocket Launch Media</a>. Want a second opinion on your own ads? <a href="{MAIN}/law-marketing/?utm_source=library&amp;utm_medium=page_cta&amp;utm_campaign=ad_audit" data-ev="cta_audit">Book a call</a>.</p></section>'+related(slug)
    faq=[(f"How many {short.lower()} ads are in the library?",f"The library has {n(s['N'])} unique {short.lower()} creatives from {n(s['firms'])} US immigration law firms."),("Do these pages show which ads worked?","No. The Meta Ad Library does not share spend or results for these ads. Running time is shown as a signal to study, not proof of results."),("Can I copy these ads?","Use them for ideas, then write your own. Check your state bar advertising rules before you run anything.")]
    paths.append(page(f'/{slug}/',title,desc[:158],h1,e(intro),body,[('Library','/'),(f'{short} Ads',f'/{slug}/')],faq,sel,f'<a class="btn" href="{deep}" data-ev="open_swipe">Swipe through {e(short.lower())} ads</a><a class="btn alt" href="/app/" data-ev="open_library">Search the full library</a>'))
for slug,h1,short,fn,dl,intro,main,lab in FORMATS:
    rows=[d for d in ALL if fn(d)];s=stats(rows);sel=pick(rows)
    desc=f"Browse {n(s['N'])} real {short.lower().replace(' ads','')} ads from {n(s['firms'])} US immigration law firms, with hook, offer and language trends."
    body=statrow(s)+f'<section class="wrap"><h2>What stands out</h2>{insights(s)}<p class="note">Based on {n(s["N"])} unique creatives in the library on {TODAY}. Running time is not proof of results.</p></section>'+gallery(sel,f'{len(sel)} ads to study')+f'<section class="wrap"><h2>Want the strategy behind these ads?</h2><p><a href="{main}">{e(lab)}</a> on Rocket Launch Media.</p></section>'+related(slug)
    faq=[("Where do these ads come from?","They come from the Meta Ad Library, which shows ads running on Facebook and Instagram."),("Do these pages show which ads worked?","No. There is no spend or results data here. Running time is a signal to study, not proof of results.")]
    paths.append(page(f'/{slug}/',h1,desc[:158],h1,e(intro),body,[('Library','/'),(short,f'/{slug}/')],faq,sel,f'<a class="btn" href="/app/#swipe?{dl}" data-ev="open_swipe">Swipe through {e(short.lower())}</a><a class="btn alt" href="/app/" data-ev="open_library">Search the full library</a>'))
# about
body=f'''<section class="wrap"><h2>What is in the library</h2><ul><li>{n(tot)} ads and {n(cre)} unique creatives from {n(firms)} law firms.</li><li>Ads from US immigration law firms on Facebook and Instagram, plus a small set from other platforms.</li><li>Tags for case type, language, format, hook style and where the ad sends people.</li></ul>
<h2>Where the ads come from</h2><p>Ads come from the Meta Ad Library, including data collected through Foreplay. We group near-identical versions into one creative and check new ads for duplicates.</p>
<h2>What it does not show</h2><p>There is no spend, lead or results data. A long run time can be a useful signal, but it does not prove an ad worked. Case tags and some hook tags are assigned automatically, so a few may be off.</p>
<h2>Remove an ad</h2><p>If you represent an advertiser and want an ad removed, <a href="{MAIN}/contact-us/">contact Rocket Launch Media</a> and include the firm name and ad link.</p></section>'''+related('')
paths.append(page('/about/','About the Law Firm Ad Library',f'How the Law Firm Ad Library works: where {n(tot)} ads come from, what the tags mean, what the data does not show, and how to request removal.','About the Law Firm Ad Library','A free research tool from Rocket Launch Media for law firms that want to see what others are running.',body,[('Library','/'),('About','/about/')]))
# home
s=stats(ALL);sel=pick([d for d in ALL if d['status']=='Active'],24,2)
ch=''.join(f'<a class="chip" href="/{c[0]}/">{e(c[2])} ads <span>{n(sum(d["facets"]["case"][0]==c[1] for d in ALL))}</span></a>' for c in CASES)
ch2=''.join(f'<a class="chip" href="/{f[0]}/">{e(f[2])} <span>{n(sum(1 for d in ALL if f[3](d)))}</span></a>' for f in FORMATS)
body=f'<div class="wrap"><div class="statrow"><div class="stat"><b>{n(tot)}</b><span>ads</span></div><div class="stat"><b>{n(cre)}</b><span>unique creatives</span></div><div class="stat"><b>{n(firms)}</b><span>law firms</span></div><div class="stat"><b>{pct(s["lg"].get("Spanish",0),s["N"])}%</b><span>in Spanish</span></div></div></div>'+f'<section class="wrap"><h2>Browse by case type</h2><div class="chips">{ch}</div></section><section class="wrap"><h2>Browse by format and language</h2><div class="chips">{ch2}</div></section><section class="wrap"><h2>What the library shows</h2>{insights(s)}<p class="note">Based on {n(s["N"])} unique creatives on {TODAY}. Running time is not proof of results.</p></section>'+gallery(sel,'Ads running recently')+f'<section class="wrap"><h2>How to use it</h2><ol><li>Pick a case type or search for a topic.</li><li>Save the ads you like to your swipe file.</li><li>Write your own version for your firm, then check it against your bar rules.</li></ol><p>Want to know what to do with these ideas? Read <a href="{MAIN}/law-firm-ad-library/">our guide to the Law Firm Ad Library</a> or <a href="{MAIN}/law-marketing/?utm_source=library&amp;utm_medium=page_cta&amp;utm_campaign=ad_audit" data-ev="cta_audit">book a call</a>.</p></section>'
faq=[("What is the Law Firm Ad Library?",f"It is a free library of {n(tot)} real ads from {n(firms)} law firms, focused on US immigration firms on Facebook and Instagram."),("Is it free?","Yes. You can browse, filter and swipe through the ads for free."),("Where do the ads come from?","They come from the Meta Ad Library, including data collected through Foreplay."),("Does it show spend or results?","No. There is no spend or results data. Run time is shown as a signal to study."),("Can a firm ask to remove an ad?","Yes. Use the contact details on the About page.")]
page('/','Law Firm Ad Library: Real Immigration Attorney Ads',f'Browse {n(tot)} real law firm ads from {n(firms)} firms. Filter immigration attorney ads by case type, format and language. Free to use.','Law Firm Ad Library: real immigration attorney ads',f'See what US immigration firms are running on Facebook and Instagram. Browse {n(cre)} unique creatives by case type, format and language.',body,[('Library','/')],faq,sel,'<a class="btn" href="/app/" data-ev="open_library">Open the library</a><a class="btn alt" href="/app/#swipe" data-ev="open_swipe">Swipe through ads</a>')
paths.append('/about/') if '/about/' not in paths else None
open('sitemap.xml','w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{BASE}{p}</loc><lastmod>{TODAY}</lastmod></url>\n' for p in paths)+'</urlset>\n')
open('robots.txt','w').write(f'User-agent: *\nAllow: /\nDisallow: /data/\nDisallow: /tools/\n\nSitemap: {BASE}/sitemap.xml\n')
open('llms.txt','w').write(f'# Law Firm Ad Library\n\n> Free library of {n(tot)} real ads from {n(firms)} law firms, focused on US immigration firms. Research only, with no spend or results data.\n\n## Pages\n'+''.join(f'- [{x}]({BASE}/{s}/)\n' for s,x in NAV)+f'- [About]({BASE}/about/)\n\n## Publisher\n- [Rocket Launch Media]({MAIN}/)\n')
print(len(paths),'pages')
