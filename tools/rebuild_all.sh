#!/usr/bin/env bash
# Rebuild everything that is generated from data/offers.json (used by the workflows).
set -euo pipefail
python3 tools/build_home_cards.py 21
python3 tools/build_store_pages.py
pip install --quiet pillow
python3 tools/seo_postprocess.py
# offer pages without a price must not carry Product markup (Search Console needs offers/review/aggregateRating)
python3 tools/fix_product_schema.py
# offer pages the bot wrote but never added to data/offers.json: noindex them like expired offers
python3 tools/fix_orphan_offers.py
