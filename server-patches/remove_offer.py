#!/usr/bin/env python3
"""يحذف عرض من الموقع نهائياً: من data/offers.json، وصفحته، وصوره، ثم يعيد البناء ويرفع.
الاستخدام: curl ... | python3 - offer-XXXX   (أضف --dry-run للتجربة بدون حذف)"""
import glob, json, os, re, subprocess, sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dry = "--dry-run" in sys.argv
if len(args) != 1 or not re.fullmatch(r"offer-[A-Za-z0-9]+", args[0]):
    sys.exit("اكتب اسم الصفحة بعد الأمر، مثل: offer-amzB079GV6RX7")
slug = args[0]
site = os.path.expanduser(os.environ.get("WF_SITE", "~/wafferna-site"))
pub = os.path.expanduser(os.environ.get("WF_PUB", "~/wafferna-publisher"))
dp = os.path.join(site, "data", "offers.json")
offers = json.load(open(dp, encoding="utf-8"))
hit = [o for o in offers if o.get("slug") == slug]
if not hit:
    sys.exit("ما لقيت %s في data/offers.json، ما حذفت شي." % slug)
print("بحذف:", hit[0].get("title", "")[:80])
files = [os.path.join(site, "offers", slug + ".html")] + glob.glob(os.path.join(site, "offers", "img", slug + "*"))
files = [f for f in files if os.path.exists(f)]
print("الملفات:", ", ".join(os.path.relpath(f, site) for f in files) or "(ولا ملف)")
if dry:
    sys.exit("تجربة فقط، ما حذفت شي.")
tmp = dp + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump([o for o in offers if o.get("slug") != slug], f, ensure_ascii=False, indent=1)
os.replace(tmp, dp)
for f in files:
    os.remove(f)
for cmd in ("rebuild", "sync"):
    r = subprocess.run([sys.executable, "publisher.py", cmd], cwd=pub, capture_output=True, text=True)
    print(cmd + ":", (r.stdout + r.stderr).strip()[-300:])
left = subprocess.run(["grep", "-rl", slug, "--include=*.html", "--include=*.json", "--include=*.xml", site],
                      capture_output=True, text=True).stdout.split()
print("خلصت ✅ انحذف من الموقع." if not left else
      "انحذف، وباقي ذكره في: %s (تتحدث بعد دقايق لما يخلص بناء GitHub)" % ", ".join(os.path.relpath(f, site) for f in left))
