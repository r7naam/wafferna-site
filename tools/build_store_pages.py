#!/usr/bin/env python3
"""Generate /offers/aliexpress.html, /offers/amazon.html, /offers/noon.html
from data/offers.json. Run from the repo root:  python3 tools/build_store_pages.py
Uses offers/under-100.html as the shell (head, header, drawer, footer)."""
import json, html, re, sys
from pathlib import Path
from wf_lib import norm_store, store_key, load_picks, fix_drawer, fmt_price, is_deal

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://wafferna.com"
offers = [o for o in json.loads((ROOT / "data/offers.json").read_text("utf-8")) if not o.get("archived") and is_deal(o)]
for o in offers:
    o["store"] = norm_store(o["store"])  # أمازون -> Amazon, so the offer lands on its store page
PICKS = load_picks()
shell = (ROOT / "offers/under-100.html").read_text("utf-8")

head_end = shell.index("</head>")
main_start = shell.index("<main")
main_end = shell.index("</main>") + len("</main>")
head, middle, tail = shell[:head_end], shell[head_end:main_start], shell[main_end:]

# drop page-specific head tags from the shell; they are rebuilt per store
for pat in (r'<title>.*?</title>\n?', r'<meta name="description"[^>]*>\n?', r'<link rel="canonical"[^>]*>\n?',
            r'<meta property="og:(title|description|url|image|image:width|image:height)"[^>]*>\n?',
            r'<script type="application/ld\+json">.*?</script>\n?'):
    head = re.sub(pat, '', head, flags=re.S)

E = lambda s: html.escape(str(s), quote=True)
STORES = {
 "aliexpress": dict(db="AliExpress", ar="علي اكسبرس", page="aliexpress.html", cls="st-aliexpress",
   cover="/covers/og-aliexpress-customs-guide.jpg",
   h1="عروض علي اكسبرس: منتجات مختارة بأسعار محدّثة",
   title="عروض علي اكسبرس للسعودية | منتجات مختارة | Wafferna",
   desc="منتجات مختارة من علي اكسبرس مع السعر وقت النشر، وطريقة حساب الجمارك والضريبة قبل الطلب. كل عرض له صفحة بتفاصيله ورابط المتجر.",
   lead="هنا كل العروض المنشورة من علي اكسبرس في وفّرنا، الأحدث أولاً. السعر المكتوب هو سعر وقت النشر، وقد يتغير في صفحة المتجر.",
   tips=["الشحن الدولي قد يضيف ضريبة القيمة المضافة ورسوماً على الطلب، فاحسب الإجمالي بـ<a href=\"/customs-calculator.html\">حاسبة الجمارك والضريبة</a> قبل الدفع.",
         "راجع تقييم المنتج وعدد الطلبات وسمعة البائع، ولا تكتفِ بالسعر.",
         "تأكد من الموديل والتوافق مع جهازك، خصوصاً الكابلات والشواحن وقطع الغيار.",
         "اقرأ <a href=\"/aliexpress-customs-guide.html\">دليل جمارك علي اكسبرس</a> و<a href=\"/aliexpress-tracking-status.html\">معاني حالات تتبع الشحنة</a>."],
   faq=[("هل أسعار علي اكسبرس هنا نهائية؟","لا، هي سعر وقت النشر. السعر النهائي هو المكتوب في صفحة المتجر عند الدفع، وقد يختلف الشحن والضريبة."),
        ("هل تُحسب جمارك على الطلبية؟","تختلف الرسوم حسب قيمة الطلب ونوع المنتج وطريقة الشحن. استخدم حاسبة الجمارك والضريبة في وفّرنا لتقدير التكلفة قبل الطلب."),
        ("هل تحصلون على عمولة؟","بعض الروابط تسويقية، وقد نحصل على عمولة صغيرة دون أي تكلفة إضافية عليك. راجع صفحة من نحن.")]),
 "amazon": dict(db="Amazon", ar="أمازون", page="amazon.html", cls="st-amazon",
   cover="/covers/og-amazon-picks.jpg",
   h1="عروض أمازون: منتجات مختارة بأسعار محدّثة",
   title="عروض أمازون السعودية | منتجات مختارة | Wafferna",
   desc="منتجات مختارة من أمازون مع السعر وقت النشر والسعر السابق إن وُجد. كل عرض له صفحة بتفاصيله، وروابط أخرى لاختيارات أمازون المشروحة.",
   lead="هنا العروض المنشورة من أمازون في وفّرنا، الأحدث أولاً. السعر المكتوب هو سعر وقت النشر، وقد يتغير في صفحة المتجر.",
   tips=["قارن السعر الحالي بتاريخه في صفحة المنتج قبل الاعتماد على نسبة الخصم، وتعلّم <a href=\"/real-discount.html\">كيف تكشف الخصم الحقيقي</a>.",
         "راجع مدة التوصيل وسياسة الإرجاع المذكورة في صفحة المنتج.",
         "اطلع على <a href=\"/amazon-picks.html\">اختيارات أمازون المشروحة</a> لمنتجات مع شرح لكل منتج."],
   faq=[("هل السعر هنا نهائي؟","لا، هو سعر وقت النشر. السعر النهائي هو المعروض في صفحة أمازون عند الدفع."),
        ("هل تحصلون على عمولة؟","نعم، بصفتنا مشاركين في برنامج أمازون للعمولة نكسب من عمليات الشراء المؤهلة دون أي تكلفة إضافية عليك.")]),
 "noon": dict(db="Noon", ar="نون", page="noon.html", cls="st-noon",
   cover="/covers/og-store-comparison.jpg",
   h1="عروض نون: منتجات مختارة بأسعار محدّثة",
   title="عروض نون السعودية | منتجات مختارة | Wafferna",
   desc="منتجات مختارة من نون مع السعر وقت النشر والسعر السابق إن وُجد. كل عرض له صفحة بتفاصيله، ومقارنة بين نون وأمازون وعلي اكسبرس.",
   lead="هنا العروض المنشورة من نون في وفّرنا، الأحدث أولاً. السعر المكتوب هو سعر وقت النشر، وقد يتغير في صفحة المتجر.",
   tips=["قارن السعر نفسه في أمازون ونون قبل الشراء، واقرأ <a href=\"/noon-amazon-aliexpress-comparison.html\">مقارنة نون وأمازون وعلي اكسبرس</a>.",
         "تحقق من اسم البائع وسياسة الإرجاع في صفحة المنتج.",
         "إن كنت ستقسّط، راجع <a href=\"/tabby-tamara-installments.html\">دليل التقسيط مع تابي وتمارا</a> قبل الدفع."],
   faq=[("هل السعر هنا نهائي؟","لا، هو سعر وقت النشر. السعر النهائي هو المعروض في صفحة نون عند الدفع."),
        ("هل تحصلون على عمولة؟","بعض الروابط تسويقية، وقد نحصل على عمولة صغيرة دون أي تكلفة إضافية عليك. راجع صفحة من نحن.")]),
}

EMOJI = __import__("re").compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]+")
clean = lambda s: " ".join(EMOJI.sub("", str(s)).split()).rstrip("!").strip()

# side-menu store shortcuts: kept inline so the page does not depend on which style.css version is cached
DR_CSS = ('.drawer .dr-list>li.dr-stores{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;padding:10px 0}'
          '.drawer .dr-list a.dst{flex-direction:column;justify-content:center;gap:6px;min-height:76px;margin:0;padding:8px 2px;border:1.5px solid var(--dline);border-radius:14px;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:800}'
          '.sdot{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;flex:none}.sdot svg{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}'
          '.sdot.st-amazon{background:#131921;color:#fff}.sdot.st-noon{background:#FEEE00;color:#20201f}.sdot.st-aliexpress{background:#DC2A00;color:#fff}')

def card(o):
    seo = o.get("seo") or {}
    alt = seo.get("alt") or clean(o["title"])
    old = o.get("old_price")
    price = o.get("price")
    sale = bool(old and price and old > price)
    pct = f'<span class="pill">خصم {round((1-price/old)*100)}%</span>' if sale else ""
    oldh = f' <s class="old">{fmt_price(old)} ر.س</s>' if sale else ""
    prh = f'<span class="p">{fmt_price(price)} ر.س{oldh}</span>' if price is not None else ""
    local = ROOT / "offers/img" / f'{o["slug"]}.jpg'
    src = f'/offers/img/{o["slug"]}.jpg' if local.exists() else (o.get("image") or f'/offers/img/{o["slug"]}.jpg')
    return (f'<a class="ocard" href="/offers/{E(o["slug"])}.html">'
            f'<img src="{E(src)}" width="{o.get("img_w",720)}" height="{o.get("img_h",720)}" alt="{E(alt)}" loading="lazy" decoding="async">'
            f'<span class="tag" data-s="{E(store_key(o["store"]))}">{E(o["store"])}</span><b>{E(seo.get("title") or clean(o["title"]))}</b>{prh}{pct}</a>')

def pick_card(k):
    srcset = f' srcset="{E(k["srcset"])}" sizes="(max-width:700px) 31vw, 300px"' if k["srcset"] else ""
    return (f'<a class="ocard" href="{E(k["page"])}">'
            f'<img src="{E(k["img"])}"{srcset} width="{k["w"]}" height="{k["h"]}" alt="{E(k["alt"])}" loading="lazy" decoding="async">'
            f'<span class="tag" data-s="amazon">Amazon</span><b>{E(k["title"])}</b></a>')

def build(key, s):
    items = sorted([o for o in offers if o["store"] == s["db"]], key=lambda o: o.get("created", ""), reverse=True)
    url = f'{SITE}/offers/{s["page"]}'
    picks = PICKS if key == "amazon" else []
    # one grid, newest first: the store's offers and (Amazon only) the explained product pages
    rows = ([(o.get("created", ""), card(o), {"url": f'{SITE}/offers/{o["slug"]}.html', "name": (o.get("seo") or {}).get("title") or clean(o["title"])}) for o in items]
            + [(k["date"], pick_card(k), {"url": SITE + k["page"], "name": k["title"]}) for k in picks])
    rows.sort(key=lambda r: r[0], reverse=True)
    listed = [r[2] for r in rows]
    grid = chr(10).join("    " + r[1] for r in rows).strip()
    others = "".join(f'<a href="/offers/{v["page"]}">{v["ar"]}</a> · ' for k, v in STORES.items() if k != key)
    ld = [
      {"@context":"https://schema.org","@type":"CollectionPage","name":s["h1"],"url":url,"inLanguage":"ar","description":s["desc"],
       "mainEntity":{"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":x["url"],"name":x["name"]} for i,x in enumerate(listed)]}},
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"الرئيسية","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"العروض","item":SITE+"/offers/"},
        {"@type":"ListItem","position":3,"name":s["h1"],"item":url}]},
      {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in s["faq"]]},
    ]
    h = head + (f'<title>{E(s["title"])}</title>\n<meta name="description" content="{E(s["desc"])}">\n'
                f'<link rel="canonical" href="{url}">\n<meta property="og:title" content="{E(s["h1"])}">\n'
                f'<meta property="og:description" content="{E(s["desc"])}">\n<meta property="og:url" content="{url}">\n'
                f'<meta property="og:image" content="{SITE}{s["cover"]}">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n')
    h += "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    body = f'''<main class="wrap article">
  <p class="crumbs"><a href="/">الرئيسية</a> › <a href="/offers/">العروض</a> › {E(s["ar"])}</p>
  <h1>{E(s["h1"])}</h1>
  <p class="lead">{E(s["lead"])}</p>
  <div class="storenav" role="group" aria-label="تصفح العروض حسب المتجر">{"".join(f'<a class="stab {v["cls"]}{" on" if k==key else ""}" href="/offers/{v["page"]}"{" aria-current=\"page\"" if k==key else ""}>{v["db"]}</a>' for k,v in STORES.items())}</div>
  <div class="ogrid">
    {grid}
  </div>
  <h2>قبل ما تشتري من {E(s["ar"])}</h2>
  <ul>{"".join(f"<li>{t}</li>" for t in s["tips"])}</ul>
  <h2>أسئلة شائعة</h2>
  {"".join(f"<h3>{E(q)}</h3><p>{E(a)}</p>" for q,a in s["faq"])}
  <p style="margin-top:20px">{others}<a href="/offers/">كل العروض</a> · <a href="/tips.html">نصائح التسوق الذكي</a></p>
</main>'''
    mid = fix_drawer(middle)  # header/drawer from the shell, with the store shortcuts in the side menu
    style = ('<style>' + DR_CSS + '.storenav{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 4px}.stab{display:inline-flex;align-items:center;min-height:48px;padding:0 20px;border-radius:999px;font-family:Arial,Helvetica,sans-serif;font-weight:800;text-decoration:none;border:2px solid transparent}'
             '.stab.on{opacity:1;border-color:var(--ink)}.stab.st-aliexpress{background:#DC2A00;color:#fff}.stab.st-amazon{background:#131921;color:#fff}.stab.st-noon{background:#FEEE00;color:#20201f}'
             '.ocard{position:relative}.ocard .pill{position:absolute;inset-inline-start:20px;top:20px;background:var(--gold);color:var(--ink);padding:0 10px;border-radius:8px;font-weight:800;font-size:14px}.ocard .old{color:var(--muted);font-weight:400;margin-inline-start:6px}</style>\n')
    out = h + style + mid + body + tail
    (ROOT / "offers" / s["page"]).write_text(out, "utf-8")
    print(f'{s["page"]}: {len(rows)} cards')

for k, s in STORES.items():
    build(k, s)
