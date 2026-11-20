#!/usr/bin/env python3
"""Archive orphan offer pages (run by tools/rebuild_all.sh). Idempotent.

Sometimes the offers bot writes offers/offer-<slug>.html but never adds <slug> to data/offers.json
(seen 2026-11-19: offer-1005011960861391 and offer-4000118191927). Such a page is indexable, has no
sitemap entry and nothing links to it, and no job ever archives it because check_links.py only
looks at offers.json.

This script gives every offer page that is missing from offers.json, and whose publish date is at
least GRACE_DAYS old (so a bot run that is still in progress is never touched), the same treatment
check_links.py gives a dead offer: <meta robots noindex,follow> instead of the canonical, plus the
"old offer" note. Pages are never deleted, so old links keep working.
Run from the repo root:  python3 tools/fix_orphan_offers.py
"""
import json, re, sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_links import archive_page  # same noindex + note + sitemap removal as a dead offer

ROOT = Path(__file__).resolve().parent.parent
GRACE_DAYS = 1

def main():
    known = {o["slug"] for o in json.loads((ROOT / "data/offers.json").read_text("utf-8"))}
    limit = date.today() - timedelta(days=GRACE_DAYS)
    n = 0
    for p in sorted((ROOT / "offers").glob("offer-*.html")):
        slug = p.stem
        if slug in known:
            continue
        t = p.read_text("utf-8")
        if 'name="robots" content="noindex' in t:
            continue
        m = re.search(r'<p class="meta">[^<]*?(\d{4}-\d{2}-\d{2})', t)
        if not m or date.fromisoformat(m.group(1)) > limit:
            continue
        archive_page({"slug": slug, "created": m.group(1)})
        n += 1
        print(f"orphan archived: {slug}")
    print(f"orphans: {n} archived")

if __name__ == "__main__":
    main()
