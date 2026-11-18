#!/usr/bin/env python3
"""Search Console: a Product snippet must have offers, review or aggregateRating.
Offer pages without a price (Amazon items, announcements) are not products with an offer we can state,
so their JSON-LD becomes an Article instead of an invalid Product. Pages whose Product has an offer are untouched.
Idempotent. Run from the repo root:  python3 tools/fix_product_schema.py"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://wafferna.com"
by_slug = {o["slug"]: o for o in json.loads((ROOT / "data/offers.json").read_text("utf-8"))}
LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)

def article(j, o):
    out = {"@context": "https://schema.org", "@type": "Article", "headline": j.get("name", ""),
           "description": j.get("description", ""), "url": j.get("url", ""), "mainEntityOfPage": j.get("url", ""),
           "inLanguage": j.get("inLanguage", "ar"), "image": j.get("image", [])}
    if j.get("keywords"): out["keywords"] = j["keywords"]
    if o.get("created"): out["datePublished"] = o["created"]
    if o.get("updated") or o.get("created"): out["dateModified"] = o.get("updated") or o["created"]
    org = {"@type": "Organization", "name": "Wafferna", "url": SITE + "/"}
    out["author"] = org; out["publisher"] = org
    return out

n = 0
for p in sorted((ROOT / "offers").glob("offer-*.html")):
    t = p.read_text("utf-8")
    def fix(m):
        try: j = json.loads(m.group(2))
        except ValueError: return m.group(0)
        if not isinstance(j, dict) or j.get("@type") != "Product" or any(k in j for k in ("offers", "review", "aggregateRating")):
            return m.group(0)
        return m.group(1) + json.dumps(article(j, by_slug.get(p.stem, {})), ensure_ascii=False) + m.group(3)
    new = LD.sub(fix, t)
    if new != t:
        p.write_text(new, "utf-8"); n += 1
print(f"product schema without offer -> Article: {n} pages")
