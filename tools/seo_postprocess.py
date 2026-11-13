#!/usr/bin/env python3
"""SEO/performance post-processing. Runs after the offers bot and the rebuild tools.
Safe to run repeatedly (idempotent). Run from the repo root:  python3 tools/seo_postprocess.py

1. Builds small WebP copies of every offer image (-400.webp for cards, -200.webp for 64px thumbs).
2. Adds srcset/sizes to offer card images and points 64px thumbs at the 200px WebP.
3. Fills empty alt text on homepage cards (from seo.alt / title, emojis removed).
4. Adds ItemList + BreadcrumbList JSON-LD to offers/index.html when the bot rewrites it.
5. Keeps sitemap <lastmod> of the homepage and listing pages equal to the newest offer date.
"""
import json, html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "offers/img"
SITE = "https://wafferna.com"
SIZES = "(max-width:700px) 31vw, 300px"
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]+")
clean = lambda s: re.sub(r"\s+", " ", EMOJI.sub("", str(s))).strip()

offers = json.loads((ROOT / "data/offers.json").read_text("utf-8"))
by_slug = {o["slug"]: o for o in offers}

def alt_for(slug):
    o = by_slug.get(slug) or {}
    return clean((o.get("seo") or {}).get("alt") or o.get("title") or "")

# 1) WebP copies
def make_webp():
    try:
        from PIL import Image
    except ImportError:
        print("Pillow missing: skipped WebP generation"); return
    n = 0
    for jpg in sorted(IMG.glob("*.jpg")):
        for w in (400, 200):
            out = IMG / f"{jpg.stem}-{w}.webp"
            if out.exists() and out.stat().st_mtime >= jpg.stat().st_mtime:
                continue
            im = Image.open(jpg).convert("RGB")
            if im.width > w:
                im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            im.save(out, "WEBP", quality=78, method=6); n += 1
    print(f"webp: {n} new")

# 2+3) images in HTML
IMG_RE = re.compile(r'<img src="/offers/img/([^"/]+?)\.jpg"([^>]*)>')
def fix_img(m):
    slug, rest = m.group(1), m.group(2)
    has = lambda w: (IMG / f"{slug}-{w}.webp").exists()
    if 'width="64"' in rest:
        return f'<img src="/offers/img/{slug}-200.webp"{rest}>' if has(200) else m.group(0)
    # main product image and LCP images (the homepage ticket swaps its src by script): keep the plain JPG
    if 'class="oimg"' in rest or 'fetchpriority="high"' in rest:
        return m.group(0)
    if 'alt=""' in rest and alt_for(slug):
        rest = rest.replace('alt=""', f'alt="{html.escape(alt_for(slug), quote=True)}"')
    if "srcset=" not in rest and has(400):
        rest = f' srcset="/offers/img/{slug}-400.webp 400w, /offers/img/{slug}.jpg 720w" sizes="{SIZES}"' + rest
    return f'<img src="/offers/img/{slug}.jpg"{rest}>'

# 4) JSON-LD for offers/index.html
MARK = '<script type="application/ld+json" id="wf-list">'
def offers_index_ld(t):
    if MARK in t:
        t = re.sub(re.escape(MARK) + r".*?</script>\n?", "", t, flags=re.S)
    slugs = list(dict.fromkeys(re.findall(r'<a class="ocard" href="/offers/([^"]+)\.html"', t)))
    items = [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}/offers/{s}.html",
              "name": clean(((by_slug.get(s) or {}).get("seo") or {}).get("title") or (by_slug.get(s) or {}).get("title") or s)}
             for i, s in enumerate(slugs)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "العروض", "item": SITE + "/offers/"}]},
        {"@type": "ItemList", "name": "أحدث العروض", "numberOfItems": len(items), "itemListElement": items}]}
    return t.replace("</head>", MARK + json.dumps(ld, ensure_ascii=False) + "</script>\n</head>", 1)

# 5) sitemap lastmod
def sitemap():
    p = ROOT / "sitemap.xml"; t = p.read_text("utf-8")
    newest = max((o.get("updated") or o.get("created") or "")[:10] for o in offers)
    if not newest: return
    for path in ("", "offers/", "offers/under-100.html", "offers/under-50.html", "offers/big-discounts.html",
                 "offers/amazon.html", "offers/noon.html", "offers/aliexpress.html"):
        t = re.sub(r"(<loc>" + re.escape(f"{SITE}/{path}") + r"</loc><lastmod>)[^<]*", r"\g<1>" + newest, t)
    p.write_text(t, "utf-8")

make_webp()
changed = 0
for p in [ROOT / "index.html"] + sorted((ROOT / "offers").glob("*.html")):
    t = p.read_text("utf-8"); n = IMG_RE.sub(fix_img, t)
    if p == ROOT / "offers/index.html":
        n = offers_index_ld(n)
    if n != t:
        p.write_text(n, "utf-8"); changed += 1
sitemap()
print(f"html: {changed} files updated")
