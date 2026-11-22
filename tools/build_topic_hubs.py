#!/usr/bin/env python3
"""Builds the 4 topic hub (pillar) pages from tips.html's header/footer. Idempotent.
Run from the repo root:  python3 tools/build_topic_hubs.py

Each hub: an intro written for the topic, "start here" steps, grouped cards (guides, then short videos),
CollectionPage + ItemList + BreadcrumbList JSON-LD. Card titles/images come from the linked pages themselves,
so a hub never drifts from the page it points to.
Video pages that have a matching article are left out on purpose (the article embeds the same video).
"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://wafferna.com"
UPDATED, UPDATED_AR = "2026-11-22", "22 نوفمبر 2026"
E = lambda s: html.escape(s, quote=True)
LF = chr(10)  # write LF line endings on Windows too (the repo is LF)

HUBS = [
  {
    "slug": "tools", "name": "أدوات التسوق الذكي",
    "title": "حاسبات التسوق: الجمارك والضريبة والخصم | Wafferna",
    "h1": "أدوات التسوق الذكي: احسب قبل ما تدفع",
    "desc": "حاسبات مجانية تحسب لك قبل الشراء: الجمارك والضريبة على طلبك الخارجي، ضريبة 15%، الخصم الحقيقي، ومقارنة السعر النهائي بين نون وأمازون وعلي إكسبرس.",
    "cover": "og-customs-calculator",
    "lead": "السعر المكتوب على المنتج نادراً ما يكون اللي تدفعه فعلاً. الشحن وضريبة القيمة المضافة والجمارك ورسوم المعالجة تنضاف في آخر خطوة، والخصم المعلن قد يكون محسوباً من سعر مرفوع. هذي الأدوات تعطيك الرقم الحقيقي قبل ما تضغط «ادفع».",
    "steps": [
      "طلبك من متجر خارج السعودية؟ ابدأ بـ<a href=\"customs-calculator.html\">حاسبة الجمارك والضريبة</a> لتعرف الإجمالي بعد وصوله.",
      "تشوف سعراً بدون ضريبة أو تبي تعرف كم الضريبة داخل سعر شامل؟ استخدم <a href=\"vat-calculator.html\">حاسبة ضريبة 15%</a>.",
      "العرض يقول خصم كبير؟ أدخل السعرين في <a href=\"discount-calculator.html\">حاسبة الخصم الحقيقي</a> بعد إضافة الشحن.",
      "نفس المنتج في أكثر من متجر؟ قارن السعر النهائي في <a href=\"noon-amazon-aliexpress-comparison.html\">مقارنة نون وأمازون وعلي إكسبرس</a>.",
    ],
    "groups": [
      ("الحاسبات", ["customs-calculator", "vat-calculator", "discount-calculator", "noon-amazon-aliexpress-comparison"]),
      ("أدوات قبل الشراء وبعده", ["running-shoes-size-guide", "aliexpress-tracking-status"]),
    ],
    "members": ["vat-calculator", "discount-calculator", "noon-amazon-aliexpress-comparison", "running-shoes-size-guide", "customs-calculator"],
    "note": "الحاسبات تعطي تقديراً مبنياً على القواعد المنشورة، والرقم النهائي هو ما يظهر في صفحة الدفع أو في فاتورة شركة الشحن.",
  },
  {
    "slug": "customs-shipping", "name": "دليل الجمارك والشحن والاسترجاع",
    "title": "دليل الجمارك والشحن والاسترجاع في السعودية | Wafferna",
    "h1": "دليل الجمارك والشحن والاسترجاع في السعودية",
    "desc": "كل ما يخص طلبك بعد الدفع: الحد المعفى من الجمارك، حساب رسوم الطلب الخارجي، تتبع الشحنة ومعنى حالاتها، وحقك في الإلغاء والاسترجاع عند التأخير أو التلف.",
    "cover": "og-customs-exemption-limit",
    "lead": "بعد الدفع تبدأ مرحلة ثانية: الشحنة تمر بالجمارك، وتتنقل بين شركات الشحن، وقد تتأخر أو توصل تالفة. هذا الدليل يجمع لك ما تحتاجه في كل مرحلة، من حساب الرسوم قبل الطلب إلى حقك في الاسترجاع بعد الاستلام.",
    "steps": [
      "قبل الطلب: اعرف <a href=\"customs-exemption-limit.html\">الحد المعفى من الجمارك</a> (1000 ريال شاملة الشحن) وأن الضريبة تبقى مستحقة حتى تحته.",
      "احسب الإجمالي بـ<a href=\"customs-calculator.html\">حاسبة الجمارك</a> أو بالخطوات في <a href=\"aliexpress-customs-guide.html\">طريقة حساب الجمارك</a>.",
      "بعد الشحن: تابع طلبك بـ<a href=\"shipment-tracking.html\">دليل تتبع الشحنات</a>، وترجم أي رسالة غريبة في <a href=\"aliexpress-tracking-status.html\">قاموس حالات التتبع</a>.",
      "عند الاستلام: افتح الطرد قبل إعطاء رمز الاستلام، واعرف مدة الاسترجاع وحقك إذا تأخر الطلب.",
    ],
    "groups": [
      ("الجمارك والرسوم", ["customs-exemption-limit", "aliexpress-customs-guide", "customs-calculator"]),
      ("تتبع الشحنة", ["shipment-tracking", "aliexpress-tracking-status"]),
      ("فيديوهات: الاستلام والاسترجاع", ["video-1111-hidden-costs", "video-open-parcel-before-code", "video-damaged-product-return", "video-late-order-refund", "video-return-7-days"]),
    ],
    "members": ["customs-exemption-limit", "aliexpress-customs-guide", "shipment-tracking", "aliexpress-tracking-status"],
    "note": "الأنظمة والرسوم قد تتغير. نذكر المصدر الرسمي داخل كل دليل، وإن وجدت معلومة تغيّرت فراسلنا على info@wafferna.com.",
  },
  {
    "slug": "scam-protection", "name": "دليل الحماية من الاحتيال",
    "title": "الحماية من الاحتيال والخصم الوهمي أونلاين | Wafferna",
    "h1": "الحماية من الاحتيال والخصم الوهمي عند التسوق أونلاين",
    "desc": "اكشف المتجر الوهمي والرابط المزيف ورسائل الشحن الاحتيالية والتقييمات المدفوعة والخصم المضخّم قبل ما تدفع، بأدلة وفيديوهات قصيرة بخطوات عملية.",
    "cover": "fake-stores",
    "lead": "أغلب الخسائر في التسوق أونلاين ما تجي من منتج سيئ، بل من متجر غير حقيقي، أو رابط مزيف، أو خصم محسوب من سعر مرفوع. المحتال يعتمد على الاستعجال، فهذا الدليل يعطيك فحوصات قصيرة تسويها في دقائق قبل أي دفع.",
    "steps": [
      "متجر ما تعرفه؟ <a href=\"fake-stores.html\">تحقق منه</a> قبل الدفع، من بياناته الرسمية إلى طرق الدفع اللي يقبلها.",
      "رسالة فيها رابط وعرض ينتهي اليوم أو رسوم شحن صغيرة؟ لا تضغطها قبل الفحوصات في الفيديوهات تحت.",
      "تقييمات ممتازة بشكل مبالغ فيه؟ اقرأها بالطريقة في <a href=\"fake-reviews.html\">كشف التقييمات المزيفة</a>.",
      "خصم كبير؟ تأكد أنه <a href=\"real-discount.html\">خصم حقيقي</a> بمقارنة السعر قبل العرض.",
    ],
    "groups": [
      ("الأدلة", ["fake-stores", "fake-reviews", "real-discount"]),
      ("فيديوهات: متجر ورابط ورسالة", ["video-trusted-store", "video-new-store-5-checks", "video-fake-link-check", "video-fake-shipping-sms", "video-fake-reviews-amazon"]),
      ("فيديوهات: حيل الأسعار", ["video-price-history", "video-dark-patterns", "video-personalized-pricing", "video-store-tricks"]),
    ],
    "members": ["fake-stores", "fake-reviews", "real-discount"],
    "note": "لو دفعت لمتجر أو رابط احتيالي: تواصل مع بنكك فوراً لإيقاف البطاقة، ثم بلّغ عن الحساب أو المتجر عبر القنوات الرسمية.",
  },
  {
    "slug": "payment-installments", "name": "دليل الدفع والتقسيط",
    "title": "الدفع الآمن والتقسيط والاشتراكات أونلاين | Wafferna",
    "h1": "الدفع الآمن والتقسيط: قبل ما تضغط «ادفع»",
    "desc": "احمِ بطاقتك عند الشراء أونلاين، واحسب مجموع أقساط تابي وتمارا قبل ما تقسّط، وتجنّب الخصم التلقائي بعد التجربة المجانية، مع فحوصات سريعة قبل الدفع.",
    "cover": "safe-payment",
    "lead": "لحظة الدفع هي آخر فرصة توقف فيها الخطأ: بطاقة تنحفظ في موقع غير آمن، أو قسط صغير ينضاف لأقساط ثانية، أو تجربة مجانية تتحول لاشتراك. هذا الدليل يجمع الفحوصات اللي تسويها في هذي اللحظة.",
    "steps": [
      "قبل إدخال البطاقة: راجع قواعد <a href=\"safe-payment.html\">الدفع الآمن</a>، ولا تعطِ رمز التحقق (OTP) لأي أحد.",
      "تفكر تقسّط؟ اجمع أقساطك الحالية والجديدة في <a href=\"tabby-tamara-installments.html\">حاسبة أقساط تابي وتمارا</a>.",
      "تسجّل في تجربة مجانية؟ اتبع خطوات <a href=\"free-trial-auto-charge.html\">تجنّب الخصم التلقائي</a> وسجّل موعد الإلغاء.",
      "قبل التأكيد: راجع <a href=\"shopping-mistakes.html\">أخطاء تخليك تدفع أكثر</a>.",
    ],
    "groups": [
      ("الأدلة", ["safe-payment", "tabby-tamara-installments", "free-trial-auto-charge", "shopping-mistakes"]),
      ("فيديوهات: قرار الشراء", ["video-before-you-pay", "video-24h-rule", "video-impulse-buying"]),
    ],
    "members": ["safe-payment", "tabby-tamara-installments", "free-trial-auto-charge", "shopping-mistakes"],
    "note": "شروط التقسيط والرسوم المتأخرة تحددها كل شركة وتتغير. ارجع دائماً لشروط الشركة قبل الموافقة.",
  },
]

def page_info(slug):
    s = (ROOT / f"{slug}.html").read_text("utf-8")
    g = lambda pat: (re.search(pat, s, re.S) or [None, ""])[1]
    h1 = html.unescape(re.sub(r"<[^>]+>", "", g(r"<h1[^>]*>(.*?)</h1>"))).strip()
    desc = html.unescape(g(r'name="description" content="([^"]*)'))
    cover = g(r'og:image" content="https://wafferna.com/covers/([^"]+)\.jpg')
    alt = html.unescape(g(r'og:image:alt" content="([^"]*)')) or h1
    return {"slug": slug, "h1": h1, "desc": desc, "cover": cover, "alt": alt, "video": slug.startswith("video-")}

def short(t, n=110):
    t = re.split(r"(?<=[.؟!])\s", t)[0]
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"

def webp_set(cover):
    """Ensure -600/-1000 WebP copies exist; return (src, srcset, w, h)."""
    from PIL import Image
    jpg = ROOT / "covers" / f"{cover}.jpg"
    im = Image.open(jpg); w, h = im.size
    for size in (600, 1000):
        out = ROOT / "covers" / f"{cover}-{size}.webp"
        if not out.exists():
            c = im.convert("RGB")
            if c.width > size:
                c = c.resize((size, round(c.height * size / c.width)), Image.LANCZOS)
            c.save(out, "WEBP", quality=78, method=6)
    big = min(1000, w)
    return (f"covers/{cover}-600.webp", f"covers/{cover}-600.webp 600w, covers/{cover}-1000.webp {big}w", w, h)

def card(p, first):
    src, srcset, w, h = webp_set(p["cover"])
    load = 'fetchpriority="high"' if first else 'loading="lazy"'
    tag = "فيديو قصير" if p["video"] else ("أداة" if "calculator" in p["slug"] or p["slug"] in ("aliexpress-tracking-status", "running-shoes-size-guide", "noon-amazon-aliexpress-comparison") else "دليل")
    return (f'    <a class="tip" href="{p["slug"]}.html"><img src="{src}" srcset="{srcset}" sizes="(max-width:600px) 90vw, 360px" '
            f'width="{w}" height="{h}" alt="{E(p["alt"])}" {load} decoding="async"><span class="tag">{tag}</span>'
            f'<b>{E(p["h1"])}</b><span>{E(short(p["desc"]))}</span></a>')

def build(hub, tpl, all_hubs):
    url = f"{SITE}/{hub['slug']}.html"
    items, body, first = [], [], True
    for gname, slugs in hub["groups"]:
        body.append(f'  <h2>{E(gname)}</h2>\n  <div class="tips">')
        for s in slugs:
            p = page_info(s)
            body.append(card(p, first)); first = False
            items.append({"@type": "ListItem", "position": len(items) + 1, "name": p["h1"], "url": f"{SITE}/{s}.html"})
        body.append("  </div>")
    others = " · ".join(f'<a href="{h["slug"]}.html">{E(h["name"])}</a>' for h in all_hubs if h is not hub)
    steps = "\n".join(f"    <li>{s}</li>" for s in hub["steps"])
    main = f'''<main class="wrap article tips-page">
  <p class="crumbs"><a href="/">الرئيسية</a> › <a href="tips.html">نصائح</a> › {E(hub["name"])}</p>
  <h1>{E(hub["h1"])}</h1>
  <p class="meta"><a href="/about.html#editorial">فريق وفّرنا</a> · آخر تحديث: <time datetime="{UPDATED}">{UPDATED_AR}</time></p>
  <p class="lead">{E(hub["lead"])}</p>
  <h2>ابدأ من هنا</h2>
  <ol>
{steps}
  </ol>
{chr(10).join(body)}
  <p class="note">{E(hub["note"])}</p>
  <p class="note">أدلة أخرى: {others} · <a href="tips.html">كل النصائح</a></p>
</main>'''
    cover_src = f"{SITE}/covers/{hub['cover']}.jpg"
    ld_page = {"@context": "https://schema.org", "@type": "CollectionPage", "name": hub["name"], "url": url, "inLanguage": "ar",
               "description": hub["desc"], "dateModified": UPDATED, "image": cover_src,
               "isPartOf": {"@type": "WebSite", "name": "وفّرنا", "url": SITE + "/"},
               "publisher": {"@type": "Organization", "name": "Wafferna", "url": SITE + "/", "logo": {"@type": "ImageObject", "url": SITE + "/logo.png"}},
               "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items}}
    ld_bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "نصائح", "item": SITE + "/tips.html"},
        {"@type": "ListItem", "position": 3, "name": hub["name"], "item": url}]}
    t = tpl
    rep = [
        (r"<title>.*?</title>", f"<title>{E(hub['title'])}</title>"),
        (r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{E(hub["desc"])}">'),
        (r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">'),
        (r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{E(hub["name"])}">'),
        (r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{E(hub["desc"])}">'),
        (r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">'),
        (r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{cover_src}">'),
        (r'<meta property="og:image:alt" content="[^"]*">', f'<meta property="og:image:alt" content="{E(hub["name"])} من وفّرنا">'),
        (r'<meta name="twitter:image" content="[^"]*">', f'<meta name="twitter:image" content="{cover_src}">'),
    ]
    for pat, new in rep:
        t, n = re.subn(pat, lambda m: new, t, count=1)
        assert n == 1, pat
    t = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", t, flags=re.S)
    t = t.replace("</head>", "<script type=\"application/ld+json\">" + json.dumps(ld_page, ensure_ascii=False) + "</script>\n"
                  "<script type=\"application/ld+json\">" + json.dumps(ld_bc, ensure_ascii=False) + "</script>\n</head>", 1)
    t, n = re.subn(r"<main .*?</main>", lambda m: main, t, count=1, flags=re.S)
    assert n == 1
    (ROOT / f"{hub['slug']}.html").write_text(t, "utf-8", newline=LF)
    print("built", hub["slug"], len(items), "items")

LD_RE = re.compile(r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)', re.S)

def link_member(slug, hub):
    """Put the article under its hub: breadcrumb (visible + JSON-LD) and a link in the byline. Idempotent."""
    p = ROOT / f"{slug}.html"; t = o = p.read_text("utf-8")
    href, name, url = f'{hub["slug"]}.html', hub["name"], f'{SITE}/{hub["slug"]}.html'
    link = f'<a href="{href}">{E(name)}</a>'
    m = re.search(r'<p class="crumbs">(.*?)</p>', t)
    if m and href not in m.group(1):
        c = m.group(1)
        tips = '<a href="tips.html">نصائح</a>'
        c = c.replace(tips, f"{tips} › {link}", 1) if tips in c else c.replace('<a href="/">الرئيسية</a>', f'<a href="/">الرئيسية</a> › {link}', 1)
        t = t[:m.start(1)] + c + t[m.end(1):]
    m = re.search(r'<p class="meta">(.*?)</p>', t)
    if m and href not in m.group(1):
        t = t[:m.end(1)] + f" · ضمن {link}" + t[m.end(1):]
    def fix(mm):
        d = json.loads(mm.group(2))
        if not (isinstance(d, dict) and d.get("@type") == "BreadcrumbList"): return mm.group(0)
        items = d["itemListElement"]
        if any(i.get("item") == url for i in items): return mm.group(0)
        at = next((k + 1 for k, i in enumerate(items) if str(i.get("item", "")).endswith("/tips.html")), 1)
        items.insert(at, {"@type": "ListItem", "position": 0, "name": name, "item": url})
        for k, i in enumerate(items): i["position"] = k + 1
        return mm.group(1) + json.dumps(d, ensure_ascii=False) + mm.group(3)
    t = LD_RE.sub(fix, t)
    if t != o:
        p.write_text(t, "utf-8", newline=LF); print("  linked", slug, "->", hub["slug"])

if __name__ == "__main__":
    tpl = (ROOT / "tips.html").read_text("utf-8")
    for h in HUBS:
        build(h, tpl, HUBS)
    for h in HUBS:
        for s in h["members"]:
            link_member(s, h)
