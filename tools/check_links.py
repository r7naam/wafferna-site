#!/usr/bin/env python3
"""Daily availability check for the active offers (run by .github/workflows/daily-link-check.yml).

For every active offer it opens the buy link and classifies it:
  dead     HTTP 404/410, or a 200 page that says the product is gone / not found
  ok       HTTP 200 without those signs
  unknown  anything else (403/429/5xx, captcha, timeout): never counts against the offer
An offer is archived only after DEAD_LIMIT dead results in a row (one per daily run), so a
single glitch never hides a live deal. Safety stops: the whole run aborts without changes when
more than MAX_DEAD_SHARE of the checked offers look dead (the stores are probably blocking us),
and at most MAX_ARCHIVE offers are archived per run.

Archiving mirrors what the offers bot does: archived=true in data/offers.json, the offer page gets
<meta robots noindex> instead of its canonical plus the "old offer" note, and its sitemap entry is removed.
Run from the repo root:  python3 tools/check_links.py [--dry-run]"""
import json, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from wf_lib import norm_store

ROOT = Path(__file__).resolve().parent.parent
DEAD_LIMIT, MAX_ARCHIVE, MAX_DEAD_SHARE, TIMEOUT = 3, 5, 0.3, 20
UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
GONE = {
    "Amazon": re.compile(r"Currently unavailable|We don't know when or if this item will be back|Page Not Found|Sorry! We couldn't find that page|غير متوفر حاليًا|غير متوفر حالياً|غير متاح حاليًا|عذرًا! لم نتمكن من العثور على هذه الصفحة", re.I),
    "AliExpress": re.compile(r"page you requested (?:cannot|can't) be found|no longer available|This item is no longer|الصفحة التي طلبتها غير موجودة|المنتج غير متوفر", re.I),
    "Noon": re.compile(r"Product not found|currently unavailable|لم نتمكن من العثور|غير متوفر حاليًا|غير متوفر حالياً", re.I),
}

def classify(store, url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ar,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(400_000).decode("utf-8", "ignore")
            code = r.status
    except urllib.error.HTTPError as e:
        return "dead" if e.code in (404, 410) else "unknown"
    except Exception:
        return "unknown"
    if code != 200:
        return "unknown"
    if re.search(r"captcha|robot check|verify you are human|px-captcha|unusual traffic", body, re.I):
        return "unknown"
    rx = GONE.get(store)
    return "dead" if rx and rx.search(body) else "ok"

NOTE = '<div class="box"><p class="note"><b>تنبيه:</b> هذا عرض قديم نُشر بتاريخ {d} وقد انتهى أو تغيّر سعره. تأكد من السعر الحالي في صفحة المتجر، أو شاهد <a href="/offers/">أحدث العروض</a>.</p></div>\n'

def archive_page(o):
    p = ROOT / "offers" / f'{o["slug"]}.html'
    if p.exists():
        t = p.read_text("utf-8")
        t = re.sub(r'<link rel="canonical"[^>]*>', '<meta name="robots" content="noindex,follow">', t, count=1) if "noindex" not in t else t
        if "هذا عرض قديم" not in t:
            t = re.sub(r'(<p class="meta">[^<]*</p>\n)', lambda m: m.group(1) + "  " + NOTE.format(d=(o.get("created") or "")[:10]), t, count=1)
        p.write_text(t, "utf-8")
    sm = ROOT / "sitemap.xml"
    s = sm.read_text("utf-8")
    s2 = re.sub(r'\s*<url><loc>https://wafferna\.com/offers/' + re.escape(o["slug"]) + r'\.html</loc>.*?</url>', "", s, flags=re.S)
    if s2 != s: sm.write_text(s2, "utf-8")

def main(dry):
    path = ROOT / "data/offers.json"
    offers = json.loads(path.read_text("utf-8"))
    active = [o for o in offers if not o.get("archived") and o.get("link")]
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda o: classify(norm_store(o["store"]), o["link"]), active))
    stat = {k: res.count(k) for k in ("ok", "dead", "unknown")}
    print(f"checked {len(active)}: {stat}")
    if active and stat["dead"] / len(active) > MAX_DEAD_SHARE:
        print("too many dead results, the stores are probably blocking the checker: no changes made"); return 0
    changed = archived = 0
    for o, r in zip(active, res):
        n = o.get("lc_miss", 0)
        if r == "ok" and n: o["lc_miss"] = 0; changed += 1
        elif r == "dead":
            o["lc_miss"] = n + 1; changed += 1
            print(f'dead {o["lc_miss"]}/{DEAD_LIMIT}: {o["slug"]} {o["link"]}')
            if o["lc_miss"] >= DEAD_LIMIT and archived < MAX_ARCHIVE:
                o["archived"] = True; o["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds"); archived += 1
                if not dry: archive_page(o)
                print(f'archived: {o["slug"]}')
    if changed and not dry:
        path.write_text(json.dumps(offers, ensure_ascii=False, indent=1), "utf-8")
    print(f"updated {changed}, archived {archived}" + (" (dry run, nothing written)" if dry else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))
