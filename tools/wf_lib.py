#!/usr/bin/env python3
"""Shared helpers for the Wafferna build tools (build_home_cards.py, build_store_pages.py).

1. norm_store(): one spelling per store. The bots sometimes send the Arabic name
   ("أمازون"), which used to hide the offer from /offers/amazon.html and give it the
   wrong badge/button colour on the homepage.
2. load_picks(): every explained Amazon product page (amazon-*.html in the repo root,
   except amazon-picks*.html) as a small dict, newest first. Upload a new amazon-*.html
   page and it joins the latest offers on the homepage and on /offers/amazon.html after the next rebuild.
3. fix_drawer(): side menu without the "منتجات أمازون" link and with the three store shortcuts.
"""
import html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_STORES = {
    "amazon": "Amazon", "amazon.sa": "Amazon", "أمازون": "Amazon", "امازون": "Amazon",
    "أمازون السعودية": "Amazon", "امازون السعودية": "Amazon",
    "noon": "Noon", "نون": "Noon",
    "aliexpress": "AliExpress", "ali express": "AliExpress", "علي اكسبرس": "AliExpress",
    "علي إكسبرس": "AliExpress", "على اكسبرس": "AliExpress",
}

def norm_store(s):
    """'أمازون' / 'amazon' / ' Amazon ' -> 'Amazon'. Unknown names are returned unchanged."""
    k = " ".join(str(s or "").split())
    return _STORES.get(k.lower(), k)

def store_key(s):
    """CSS key used in class names and data-s: amazon / noon / aliexpress / other."""
    k = norm_store(s).lower()
    return k if k in ("amazon", "noon", "aliexpress") else "other"

_unesc = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def load_picks():
    out = []
    for p in sorted(ROOT.glob("amazon-*.html")):
        if p.name.startswith("amazon-picks"):
            continue
        t = p.read_text("utf-8")
        a, b = t.find("<main"), t.find("</main>")
        if a < 0 or b < 0:
            continue
        m = t[a:b]
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", m, re.S)
        tag = re.search(r"<img\b[^>]*>", m)
        at = dict(re.findall(r'([a-z-]+)="([^"]*)"', tag.group(0))) if tag else {}
        img = at if all(k in at for k in ("src", "width", "height", "alt")) else None
        link = re.search(r'<a href="(https://(?:www\.)?amazon\.sa/[^"]+|https://amzn\.[^"]+|https://link\.amazon/[^"]+)"[^>]*>(.*?)</a>', m, re.S)
        date = re.search(r'<time datetime="([^"]+)"', m)
        if not (h1 and img and link):
            print(f"picks: skipped {p.name} (needs h1, product image and Amazon link)")
            continue
        name = re.sub(r"^شاهد\s+", "", _unesc(link.group(2)))
        name = re.sub(r"\s+على أمازون السعودية$", "", name) or _unesc(h1.group(1))
        small = img["src"][:-5] + "-480.webp" if img["src"].endswith(".webp") else ""
        w = int(img["width"])
        srcset = f'{small} 480w, {img["src"]} {w}w' if small and w > 480 and (ROOT / small.lstrip("/")).exists() else ""
        out.append(dict(page="/" + p.name, title=name, h1=_unesc(h1.group(1)), img=img["src"], srcset=srcset,
                        w=w, h=int(img["height"]), alt=html.unescape(img["alt"]),
                        link=html.unescape(link.group(1)), date=date.group(1) if date else ""))
    out.sort(key=lambda x: x["page"])
    out.sort(key=lambda x: x["date"], reverse=True)
    return out

_CART = ('<svg viewBox="0 0 24 24" width="16" height="16" focusable="false"><circle cx="9" cy="20" r="1.4"/>'
         '<circle cx="18" cy="20" r="1.4"/><path d="M2 3h3l2.6 12.2a1 1 0 0 0 1 .8H18a1 1 0 0 0 1-.8L20.5 8H6"/></svg>')
DRAWER_OLD = '<li><a href="/amazon-picks.html">منتجات أمازون</a></li>'
DRAWER_NEW = '<li class="dr-stores">' + "".join(
    f'<a class="dst" href="/offers/{k}.html" aria-label="عروض {ar}"><span class="sdot st-{k}" aria-hidden="true">{_CART}</span>{en}</a>'
    for k, en, ar in (("amazon", "Amazon", "أمازون"), ("noon", "Noon", "نون"), ("aliexpress", "AliExpress", "علي اكسبرس"))) + '</li>'

def fix_drawer(t):
    t = t.replace('<img src="/wordmark-light.png" alt="Wafferna"', '<img src="/wordmark-light.png" alt=""')  # brand name is already in the link\'s aria-label
    return t.replace(DRAWER_OLD, DRAWER_NEW)

def fmt_price(v):
    """1899.0 -> '1899', 87.3 -> '87.30', 375.34 -> '375.34' (whole numbers without decimals, fractions with 2)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f == int(f) else f"{f:.2f}"

def is_deal(o):
    """Announcements (no price, non-Amazon) are not deals: keep them off the deal grids. Amazon offers may omit prices on purpose."""
    return not (o.get("price") is None and store_key(norm_store(o.get("store"))) != "amazon")
