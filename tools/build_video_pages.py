#!/usr/bin/env python3
"""Generate one page per video (video-*.html in the site root) from data/videos.json.
Run from the repo root:  python3 tools/build_video_pages.py
Uses offers/under-100.html as the shell (head, header, drawer, footer)."""
import json, html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://wafferna.com"
videos = json.loads((ROOT / "data/videos.json").read_text("utf-8"))
shell = (ROOT / "offers/under-100.html").read_text("utf-8")
head_end = shell.index("</head>")
main_start = shell.index("<main")
main_end = shell.index("</main>") + len("</main>")
head, middle, tail = shell[:head_end], shell[head_end:main_start], shell[main_end:]
for pat in (r'<title>.*?</title>\n?', r'<meta name="description"[^>]*>\n?', r'<link rel="canonical"[^>]*>\n?',
            r'<meta property="og:(title|description|url|image|image:width|image:height|type)"[^>]*>\n?',
            r'<script type="application/ld\+json">.*?</script>\n?'):
    head = re.sub(pat, '', head, flags=re.S)

E = lambda s: html.escape(str(s), quote=True)
absu = lambda u: u if u.startswith(("/", "http")) else "/" + u
abs_srcset = lambda s: ", ".join(absu(p.strip().split(" ")[0]) + " " + p.strip().split(" ")[1] for p in s.split(","))

def cut(s, n):
    if len(s) <= n: return s
    return s[:n].rsplit(" ", 1)[0].rstrip("،,.: ") + "…"

CSS = ('<style>.vid{position:relative;aspect-ratio:16/9;border-radius:18px;overflow:hidden;background:#E9DFC9;margin-top:14px;border:1px solid var(--line)}'
 '.vid-btn,.vid iframe{position:absolute;inset:0;width:100%;height:100%;border:0;padding:0;background:none;cursor:pointer}.vid-btn img{width:100%;height:100%;object-fit:cover;display:block}'
 '.vid-play{position:absolute;left:50%;top:50%;width:76px;height:76px;margin:-38px 0 0 -38px;border-radius:50%;background:#C15F3C;box-shadow:0 8px 24px rgba(61,57,41,.35)}'
 '.vid-play:after{content:"";position:absolute;left:30px;top:22px;border-style:solid;border-width:16px 0 16px 26px;border-color:transparent transparent transparent #EEECE2}.vid-btn:focus-visible{outline:3px solid #C15F3C;outline-offset:-3px}'
 '.vp-sum{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:6px 20px 16px;margin-top:22px}.vp-sum h2{margin-top:14px}'
 '.vp-more{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:12px}'
 '.vp-card{display:flex;flex-direction:column;background:#E9DFC9;color:#3D3929;border:1px solid rgba(61,57,41,.14);border-radius:18px;overflow:hidden;text-decoration:none;box-shadow:0 10px 20px -14px rgba(61,57,41,.5)}'
 '.vp-card img{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;display:block}.vp-card b{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;padding:10px 12px 12px;font-size:14px;line-height:1.6}'
 '.vp-card:hover{border-color:var(--accent)}.vp-back{display:inline-flex;align-items:center;min-height:48px;margin-top:18px;font-weight:800}'
 '@media(max-width:700px){.vp-more{grid-template-columns:1fr}.vp-card{flex-direction:row}.vp-card img{width:40%;aspect-ratio:16/9}.vp-card b{padding:8px 12px;font-size:13.5px}}</style>\n')
JS = ("<script>document.querySelectorAll('.vid .vid-btn').forEach(function(b){b.addEventListener('click',function(){var w=b.parentNode,f=document.createElement('iframe');"
      "f.src='https://www.youtube-nocookie.com/embed/'+w.dataset.id+'?autoplay=1&rel=0';f.title=w.dataset.t;f.allow='accelerometer; autoplay; encrypted-media; picture-in-picture';f.allowFullscreen=true;w.replaceChild(f,b)})})</script>\n")

for i, v in enumerate(videos):
    url = f'{SITE}/{v["slug"]}.html'
    short = cut(v["title"], 52)
    title = f'{v["title"]} | Wafferna' if len(v["title"]) <= 50 else f'{short} | Wafferna'
    ldd = v["ld"]["description"]
    desc = cut(ldd, 157)
    if len(desc) < 110: desc += " شاهد الفيديو مع الملخص والروابط على وفّرنا."
    thumb = (v["ld"].get("thumbnailUrl") or [SITE + "/covers/og-tips.jpg"])[0]
    if not (ROOT / thumb.replace(SITE + "/", "")).exists(): thumb = SITE + "/covers/og-tips.jpg"
    ld = dict(v["ld"]); ld["url"] = url
    bc = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"الرئيسية","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"فيديوهات وفّرنا","item":SITE+"/videos.html"},
        {"@type":"ListItem","position":3,"name":v["title"],"item":url}]}
    h = head + (f'<title>{E(title)}</title>\n<meta name="description" content="{E(desc)}">\n<link rel="canonical" href="{url}">\n'
                f'<meta property="og:title" content="{E(v["title"])}">\n<meta property="og:description" content="{E(desc)}">\n<meta property="og:type" content="video.other">\n'
                f'<meta property="og:url" content="{url}">\n<meta property="og:image" content="{thumb}">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n')
    h += "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in (ld, bc))
    dur = f' · مدة الفيديو: {E(v["duration"])}' if v["duration"] else ""
    note = (f'<p class="note">{"مدة الفيديو: " + E(v["duration"]) + ". " if v["duration"] else ""}'
            f'<a href="https://www.youtube.com/watch?v={E(v["id"])}" rel="noopener" target="_blank">شاهده على يوتيوب</a>.</p>')
    others = [videos[(i + k) % len(videos)] for k in (1, 2, 3)]
    more = "".join(f'<a class="vp-card" href="/{o["slug"]}.html"><img src="{E(absu(o["img"]))}" srcset="{E(abs_srcset(o["srcset"]))}" sizes="(max-width:700px) 40vw, 240px" width="{o["w"]}" height="{o["h"]}" alt="{E(o["alt"])}" loading="lazy" decoding="async"><b>{E(o["title"])}</b></a>' for o in others)
    main = f'''<main class="wrap article">
  <p class="crumbs"><a href="/">الرئيسية</a> › <a href="/videos.html">فيديوهات وفّرنا</a> › {E(short)}</p>
  <h1>{E(v["title"])}</h1>
  <p class="meta">فريق وفّرنا · فيديو قصير</p>
  <div class="vid" data-id="{E(v["id"])}" data-t="{E(v["title"])}">
    <button type="button" class="vid-btn" aria-label="تشغيل الفيديو: {E(v["title"])}"><img src="{E(absu(v["img"]))}" srcset="{E(abs_srcset(v["srcset"]))}" sizes="(max-width:760px) 92vw, 728px" width="{v["w"]}" height="{v["h"]}" alt="{E(v["alt"])}" fetchpriority="high" decoding="async"><span class="vid-play" aria-hidden="true"></span></button>
  </div>
  {note}
  <section class="vp-sum">
  <h2>ملخص الفيديو والروابط</h2>
  {v["body"]}
  </section>
  <h2>فيديوهات أخرى</h2>
  <div class="vp-more">{more}</div>
  <a class="vp-back" href="/videos.html">← كل الفيديوهات</a>
</main>'''
    (ROOT / f'{v["slug"]}.html').write_text(h + CSS + middle + main + tail.replace("</body>", JS + "</body>", 1), "utf-8")
    print(v["slug"], len(desc), len(title))
