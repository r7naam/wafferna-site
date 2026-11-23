#!/usr/bin/env python3
"""Tell Bing / Yandex / other IndexNow engines which pages changed in a push (Bing also feeds ChatGPT search and Copilot).
Run from the repo root:  python3 tools/indexnow.py <before_sha> <after_sha> [--dry-run]

Sent: every added, modified or deleted page outside offers/. Everything under offers/ is left to the server:
~/wafferna-publisher/indexnow_submit.py runs in cron after each publisher sync and sends what changed in
sitemap.xml lastmod (offers and their lists). Hand-edited pages (articles, hubs, tools, videos) usually keep
their lastmod, so the server does not send them; this script does.
The key file is the one already in the site root; IndexNow checks it at https://wafferna.com/<key>.txt.
"""
import json, subprocess, sys, urllib.request, urllib.error

HOST = "wafferna.com"
KEY = "f24185cfc22d8279706172234f689ef7"
SKIP = {"404.html", "amazon-picks.html"}
LIMIT = 1000

def changed(before, after):
    if not before or set(before) == {"0"}:  # first push of a branch: nothing to compare with
        before = after + "~1"
    out = subprocess.run(["git", "diff", "--name-status", "--no-renames", before, after],
                         capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        status, path = line.split("\t", 1)
        yield status[0], path

def url_for(path):
    if path == "index.html": return f"https://{HOST}/"
    if path.endswith("/index.html"): return f"https://{HOST}/{path[:-len('index.html')]}"
    return f"https://{HOST}/{path}"

def pick(files):
    urls = []
    for status, path in files:
        name = path.rsplit("/", 1)[-1]
        if not path.endswith(".html") or name in SKIP or name.startswith(("google", "yandex")):
            continue
        if path.startswith(".") or path.startswith("tools/"):
            continue
        if path.startswith("offers/"):  # sent by the server's indexnow_submit.py
            continue
        urls.append(url_for(path))
    return list(dict.fromkeys(urls))[:LIMIT]

def send(urls):
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

if __name__ == "__main__":
    before, after = sys.argv[1], sys.argv[2]
    urls = pick(changed(before, after))
    print(f"{len(urls)} url(s)"); print("\n".join(urls))
    if not urls or "--dry-run" in sys.argv:
        sys.exit(0)
    code = send(urls)
    # 200 OK / 202 Accepted (key check pending) are success; 400/403/422/429 are reported but do not fail the site push
    print(f"IndexNow answered {code}")
