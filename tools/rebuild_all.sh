#!/usr/bin/env bash
# Rebuild everything that is generated from data/offers.json (used by the workflows).
set -euo pipefail
python3 tools/build_home_cards.py 21
python3 tools/build_store_pages.py
pip install --quiet pillow
python3 tools/seo_postprocess.py
