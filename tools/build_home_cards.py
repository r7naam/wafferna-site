#!/usr/bin/env python3
"""Fill the homepage <!--CARDS-->...<!--/CARDS--> block with the newest N offers (default 21 = 7 rows of 3).
Run from the repo root:  python3 tools/build_home_cards.py [N]"""
import json, html, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 21
E = lambda s: html.escape(str(s), quote=True)
EMOJI = __import__("re").compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]+")
clean = lambda s: " ".join(EMOJI.sub("", str(s)).split()).rstrip("!").strip()
CART = '<svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true"><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M2 3h3l2.6 12.2a1 1 0 0 0 1 .8H18a1 1 0 0 0 1-.8L20.5 8H6"/></svg>'
offers = [o for o in json.loads((ROOT / "data/offers.json").read_text("utf-8")) if not o.get("archived")]
offers.sort(key=lambda o: o.get("created", ""), reverse=True)

def card(o):
    s = o["store"]; k = s.lower()
    old = o.get("old_price")
    sale = old and old > o["price"]
    pill = f'<span class="pill">خصم {round((1 - o["price"] / old) * 100)}%</span>' if sale else ""
    oldh = f'<s class="old">{E(old)} ر.س</s>' if sale else ""
    u = f'/offers/{o["slug"]}.html'
    seo = o.get("seo") or {}
    alt = seo.get("alt") or clean(o["title"])
    name = seo.get("title") or clean(o["title"])
    return (f'<article class="deal"><a class="deal-img" href="{u}" tabindex="-1" aria-hidden="true"><img src="/offers/img/{E(o["slug"])}.jpg" width="{o.get("img_w",720)}" height="{o.get("img_h",720)}" alt="{E(alt)}" loading="lazy" decoding="async">{pill}</a>'
            f'<div class="deal-body"><span class="merchant" data-s="{E(k)}">{E(s)}</span><h3><a href="{u}">{E(name)}</a></h3>'
            f'<div class="pr"><span class="price">{E(o["price"])} ر.س</span>{oldh}</div>'
            f'<a class="obtn st-{E(k)}" href="{E(o["link"])}" target="_blank" rel="sponsored nofollow noopener noreferrer"><span>{E(s)}</span>{CART}</a>'
            f'<a class="go" href="{u}">شوف التفاصيل</a></div></article>')

p = ROOT / "index.html"
t = p.read_text("utf-8")
a, b = t.index("<!--CARDS-->") + len("<!--CARDS-->"), t.index("<!--/CARDS-->")
t = t[:a] + "\n" + "\n".join(card(o) for o in offers[:N]) + "\n" + t[b:]
p.write_text(t, "utf-8")
print(f"{min(N, len(offers))} cards")
