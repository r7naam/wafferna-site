#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""باتش: صور عروض أمازون تُعرض من رابطها الأصلي (سيرفرات أمازون) بدل نسخها في /offers/img.

يعدّل (بنسخة احتياطية لكل ملف، ويحافظ على الصلاحيات):
  ~/wafferna-publisher/publisher.py   دوال جديدة + كل أماكن عرض الصورة + أمر amazon-remote
  ~/wafferna-publisher/seo_fill.py    ما يرجع ينزّل صور أمازون
  ~/update_home.py                    بطاقات الرئيسية تستخدم رابط أمازون

ما يشغّل شي بعد التعديل. الخطوة التالية يدوية:
  cd ~/wafferna-publisher && python3 publisher.py amazon-remote && python3 publisher.py sync

للتجربة: PUB_DIR=/مسار  HOME_PY=/مسار/update_home.py  python3 amazon_images_patch.py
"""
import os, sys, datetime, py_compile, tempfile

PUB = os.path.expanduser(os.environ.get("PUB_DIR", "~/wafferna-publisher"))
HOME_PY = os.path.expanduser(os.environ.get("HOME_PY", "~/update_home.py"))
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
MARK = "img_remote"

HELPERS = r'''
# ---------- صور أمازون: تُعرض من رابطها الأصلي ولا تُنسخ على الموقع ----------
AMZ_IMG_HOSTS = ("media-amazon.com", "ssl-images-amazon.com", "images-amazon.com")

def is_amazon(store):
    s = str(store or "").lower()
    return "amazon" in s or "أمازون" in s

def amazon_img(o):
    """رابط صورة أمازون الأصلي إذا العرض من أمازون والصورة على سيرفرات أمازون، وإلا ''."""
    u = safe_url(o.get("image"))
    if not u or not is_amazon(o.get("store")): return ""
    h = (urlparse(u).hostname or "").lower()
    return u if any(h == d or h.endswith("." + d) for d in AMZ_IMG_HOSTS) else ""

def image_dims(src):
    """أبعاد صورة من رابط (في الذاكرة فقط، بدون حفظ)."""
    try:
        from PIL import Image
        import requests
        r = requests.get(src, timeout=15, headers={"User-Agent": "Mozilla/5.0 (WaffernaBot)"})
        r.raise_for_status()
        if len(r.content) > 8 * 1024 * 1024: return None
        return Image.open(io.BytesIO(r.content)).size
    except Exception as e:
        print("image dims skipped:", e, file=sys.stderr)
        return None

def drop_local_img(slug):
    """يحذف النسخ المحلية لصورة العرض (jpg و webp بكل المقاسات). يرجع عدد المحذوف."""
    base = os.path.join(CFG["SITE_DIR"], "offers", "img", slug)
    n = 0
    for suf in (".jpg", "-200.webp", "-400.webp", "-720.webp"):
        if os.path.exists(base + suf):
            os.remove(base + suf); n += 1
    return n

def set_remote(o, prev=None, fetch=True):
    """يخلي صورة عرض أمازون تُعرض من رابط أمازون ويحذف النسخة المحلية. يرجع True إذا نجح."""
    u = amazon_img(o)
    if not u: return False
    dims = None
    if prev and prev.get("img_remote") and prev.get("image") == u and prev.get("img_w") and prev.get("img_h"):
        dims = (prev["img_w"], prev["img_h"])
    if not dims and not fetch and o.get("img_w") and o.get("img_h"):
        dims = (o["img_w"], o["img_h"])
    if not dims and fetch:
        dims = image_dims(u)
    if not dims:
        m = re.search(r"_SR(\d+),(\d+)_", u)
        dims = (int(m.group(1)), int(m.group(2))) if m else (500, 500)
    o.pop("img_path", None)
    o["img_remote"] = True
    o["img_w"], o["img_h"] = int(dims[0]), int(dims[1])
    drop_local_img(o["slug"])
    return True

def has_img(o):
    return bool(o.get("img_path")) or (bool(o.get("img_remote")) and bool(safe_url(o.get("image"))))

def img_src(o, absolute=False):
    """مصدر الصورة الرئيسية: رابط أمازون للعروض البعيدة، وإلا /offers/img/<slug>.jpg."""
    if o.get("img_remote") and safe_url(o.get("image")):
        return safe_url(o.get("image"))
    p = "/offers/img/%s.jpg" % o["slug"]
    return CFG["SITE_URL"] + p if absolute else p

def amazon_remote_all():
    """يحوّل كل عروض أمازون الموجودة للصورة البعيدة (بالأبعاد المخزنة، بدون شبكة). يرجع عدد المحوّل."""
    offers = load_offers(); n = 0
    for o in offers:
        if not o.get("img_remote") and set_remote(o, fetch=False):
            n += 1
    save_offers(offers)
    rebuild()
    return n

# ---------- بيانات ----------'''

P = []  # (path, old, new, count)

def rep(path, old, new, count=1):
    P.append((path, old, new, count))

pub = os.path.join(PUB, "publisher.py")
rep(pub, "\n# ---------- بيانات ----------", HELPERS)
rep(pub, 'return seo_words(o) >= CFG["MIN_SEO_WORDS"] and bool(o.get("img_path"))',
         'return seo_words(o) >= CFG["MIN_SEO_WORDS"] and has_img(o)')
rep(pub, '''img_abs = "%s/offers/img/%s.jpg" % (CFG["SITE_URL"], o["slug"]) if o.get("img_path") else ""''',
         '''img_abs = img_src(o, absolute=True) if has_img(o) else ""''')
rep(pub, r'''    imgtag = ('<img class="oimg" src="/offers/img/%s.jpg" width="%d" height="%d" alt="%s" fetchpriority="high" decoding="async">\n'
              % (o["slug"], o["img_w"], o["img_h"], E(alt_txt))) if o.get("img_path") else ""
    if imgtag and os.path.exists(''',
         r'''    imgtag = ('<img class="oimg" src="%s" width="%d" height="%d" alt="%s" fetchpriority="high" decoding="async">\n'
              % (E(img_src(o)), o["img_w"], o["img_h"], E(alt_txt))) if has_img(o) else ""
    if imgtag and not o.get("img_remote") and os.path.exists(''')
rep(pub, '''('<img src="/offers/img/%s.jpg" width="64" height="64" alt="" loading="lazy" decoding="async">' % x["slug"]) if x.get("img_path") else ""''',
         '''('<img src="%s" width="64" height="64" alt="" loading="lazy" decoding="async">' % E(img_src(x))) if has_img(x) else ""''')
rep(pub, '''('<img src="/offers/img/%s.jpg" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">' % (o["slug"], o["img_w"], o["img_h"], E(o["title"]))) if o.get("img_path") else ""''',
         '''('<img src="%s" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">' % (E(img_src(o)), o["img_w"], o["img_h"], E(o["title"]))) if has_img(o) else ""''',
    count=2)
rep(pub, '''"image": ("/offers/img/%s.jpg" % o["slug"]) if o.get("img_path") else (safe_url(o.get("image")) or ""),''',
         '''"image": img_src(o) if has_img(o) else (safe_url(o.get("image")) or ""),''')
rep(pub, '''"<image:image><image:loc>%s/offers/img/%s.jpg</image:loc></image:image></url>"
                            % (CFG["SITE_URL"], o["slug"], o.get("updated", o["created"])[:10], CFG["SITE_URL"], o["slug"]))''',
         '''"<image:image><image:loc>%s</image:loc></image:image></url>"
                            % (CFG["SITE_URL"], o["slug"], o.get("updated", o["created"])[:10], E(img_src(o, absolute=True))))''')
rep(pub, '''    _src = str(offer.get("image") or "").strip()
    dims = fetch_image(_src, os.path.join(CFG["SITE_DIR"], "offers", "img", o["slug"])) if _src else None
    if dims:''',
         '''    _src = str(offer.get("image") or "").strip()
    remote = set_remote(o, prev)   # عروض أمازون: الصورة من رابط أمازون مباشرة، بدون نسخ
    dims = fetch_image(_src, os.path.join(CFG["SITE_DIR"], "offers", "img", o["slug"])) if (_src and not remote) else None
    if remote:
        pass
    elif dims:''')
rep(pub, '''    elif cmd == "rebuild": rebuild(); print("تم")''',
         '''    elif cmd == "rebuild": rebuild(); print("تم")
    elif cmd == "amazon-remote": print("تم تحويل %d عرض أمازون للصورة من رابط أمازون" % amazon_remote_all())''')

seo = os.path.join(PUB, "seo_fill.py")
rep(seo, '''        if o.get("archived") or publisher.is_expired(o) or o.get("img_path"): continue''',
         '''        if o.get("archived") or publisher.is_expired(o) or o.get("img_path") or o.get("img_remote"): continue
        if publisher.set_remote(o):   # عرض أمازون: نعرض صورته من رابط أمازون بدل ما ننزّلها
            o["updated"] = publisher.now().isoformat(timespec="seconds")
            site_job.log("seo_fill: amazon remote image " + o["slug"])
            fixed += 1; continue''')

rep(HOME_PY, '''    if o.get("img_path"):
        img = '<img src="/offers/img/%s.jpg" width="%d" height="%d" alt="" loading="lazy" decoding="async">' % (
            o["slug"], o.get("img_w", 720), o.get("img_h", 720))''',
         '''    if o.get("img_remote") and str(o.get("image") or "").startswith("https://"):
        img = '<img src="%s" width="%d" height="%d" alt="" loading="lazy" decoding="async">' % (
            E(o["image"]), o.get("img_w", 720), o.get("img_h", 720))
    elif o.get("img_path"):
        img = '<img src="/offers/img/%s.jpg" width="%d" height="%d" alt="" loading="lazy" decoding="async">' % (
            o["slug"], o.get("img_w", 720), o.get("img_h", 720))''')


def main():
    files = {}
    for path, *_ in P:
        if path not in files:
            if not os.path.exists(path):
                sys.exit("ما لقيت الملف: " + path)
            files[path] = open(path, encoding="utf-8").read()
    for path, src in files.items():
        if MARK in src:
            sys.exit("الباتش مطبّق قبل على %s (فيه %s). ما غيّرت شي." % (path, MARK))
    new = dict(files)
    for path, old, rp, count in P:
        c = new[path].count(old)
        if c != count:
            sys.exit("النص المتوقع موجود %d مرة بدل %d في %s:\n%s\nما غيّرت أي ملف." % (c, count, path, old[:160]))
        new[path] = new[path].replace(old, rp)
    for path, src in new.items():   # تأكد إن الكود الجديد يترجم قبل ما نكتب أي شي
        fd, tmp = tempfile.mkstemp(suffix=".py"); os.close(fd)
        open(tmp, "w", encoding="utf-8").write(src)
        try:
            py_compile.compile(tmp, doraise=True)
        except py_compile.PyCompileError as e:
            sys.exit("خطأ في الكود الناتج لـ %s: %s\nما غيّرت أي ملف." % (path, e))
        finally:
            os.remove(tmp)
            c = tmp + "c"
            if os.path.exists(c): os.remove(c)
    for path, src in new.items():
        mode = os.stat(path).st_mode & 0o7777
        bak = "%s.bak-%s" % (path, STAMP)
        open(bak, "w", encoding="utf-8").write(files[path])
        os.chmod(bak, 0o444)
        tmp = path + ".tmp-" + STAMP
        open(tmp, "w", encoding="utf-8").write(src)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
        print("عدّلت %s (نسخة احتياطية: %s)" % (path, os.path.basename(bak)))
    print("\nخلصت. الخطوة الجاية:\ncd ~/wafferna-publisher && python3 publisher.py amazon-remote && python3 publisher.py sync")

if __name__ == "__main__":
    main()
