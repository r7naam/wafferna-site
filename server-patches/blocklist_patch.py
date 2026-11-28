#!/usr/bin/env python3
"""فلتر منتجات ممنوعة (أسلحة وذخيرة) في ~/wafferna-publisher/publisher.py:
- أي منتج جديد فيه كلمة ممنوعة ما تنسوى له صفحة في الموقع.
- أمر جديد: python3 publisher.py blocked (يعرض الموجود) و  blocked --delete (يحذفه).
ياخذ نسخة احتياطية، يحافظ على صلاحيات الملف، ويوقف بدون تعديل لو أي نص ما تطابق.
بعد التعديل يحذف الممنوع الموجود ويرفع الموقع."""
import os, py_compile, shutil, stat, subprocess, sys, time
from pathlib import Path

PUB = Path(os.path.expanduser(os.environ.get("WF_PUB", "~/wafferna-publisher")))
P = PUB / "publisher.py"
src = P.read_text(encoding="utf-8")
BLOCK = '# ---------- منتجات ممنوعة (أسلحة وذخيرة وما يشبهها) ----------\nBLOCK_ALLOW = re.compile(\n    r"مسدس\\s*(?:لل|ال)?(?:مساج|تدليك|غراء|حرار|هواء|رش|طلاء|بخ|سيليكون|لحام|مسامير|ماء|مياه|فقاع|تنظيف|غسيل)"\n    r"|(?:مدلك|مساج|تدليك)\\s*(?:ال)?بندقي\\w*|بندقي\\w*\\s*(?:لل|ال)?(?:مساج|تدليك)|مسدس\\s*(?:ال)?مفك"\n    r"|(?:massage|glue|heat|spray|nail|water|bubble|caulking|paint|screwdriver)\\s*guns?|bullet\\s*(?:journal|points?|list)", re.I)\nBLOCK_RE = re.compile(\n    r"ذخير|سلاح|أسلحة|اسلحة|إسلحة|مسدس|مسدسات|بندقي|بنادق|رصاصة|رصاصات|طلقات|طلقة نارية|خرطوش|كاتم صوت|كاتم للصوت"\n    r"|خنجر|خناجر|نبلة|نبال|نشاب|قوس ونشاب|صاعق كهرب|بخاخ فلفل|رذاذ الفلفل|بخاخ الفلفل|ايرسوفت|إيرسوفت|بلاستر|قبضة حديد|مطواة"\n    r"|سكين (?:قتال|صيد|تكتيك|جيب|عسكري|رمي)|سكاكين (?:قتال|صيد|تكتيك|جيب|عسكري|رمي)"\n    r"|\\b(?:ammo|ammunition|bullets?|cartridges? box|firearms?|weapons?|pistols?|rifles?|shotguns?|handguns?|airguns?|bb guns?"\n    r"|holsters?|crossbows?|slingshots?|tasers?|stun guns?|pepper spray|airsoft|gel blasters?|brass knuckles?|daggers?"\n    r"|switchblades?|butterfly knife|tactical knife|combat knife|hunting knife|gun safe)\\b", re.I)\n\ndef blocked_word(o):\n    """يرجع الكلمة الممنوعة لو المنتج له علاقة بالأسلحة أو الذخيرة، وإلا \'\'."""\n    seo = o.get("seo") or {}\n    blob = " ".join([str(o.get("title") or ""), str(o.get("note") or ""), str(o.get("text") or ""), str(o.get("name") or ""),\n                     json.dumps(seo, ensure_ascii=False) if seo else ""])\n    m = BLOCK_RE.search(BLOCK_ALLOW.sub(" ", blob))\n    return m.group(0) if m else ""\n\ndef drop_blocked(delete=False):\n    """يعرض المنتجات الممنوعة الموجودة في الموقع، ومع delete=True يحذفها هي وصفحاتها وصورها."""\n    offers, out, n = load_offers(), [], 0\n    for o in offers:\n        w = blocked_word(o)\n        if not w:\n            out.append(o); continue\n        n += 1\n        print("%s (%s): %s %s" % ("حذفت" if delete else "ممنوع", w, o["slug"], short(o.get("title") or "", 60)))\n        if not delete: continue\n        d = os.path.join(CFG["SITE_DIR"], "offers")\n        for f in [os.path.join(d, o["slug"] + ".html")] + __import__("glob").glob(os.path.join(d, "img", o["slug"] + "*")):\n            try: os.remove(f)\n            except FileNotFoundError: pass\n    if delete and n:\n        save_offers(out); rebuild()\n    print("عدد المنتجات الممنوعة:", n)\n    return n\n\n'
EDITS = [
    ("# ---------- البناء ----------\n", BLOCK + "# ---------- البناء ----------\n"),
    ('        raise ValueError("title و link مطلوبان (ورابط http/https)")\n',
     '        raise ValueError("title و link مطلوبان (ورابط http/https)")\n'
     '    _bw = blocked_word(offer)\n'
     '    if _bw:\n'
     '        raise ValueError("منتج ممنوع (%s)، ما نشرته في الموقع" % _bw)\n'),
    ('    elif cmd == "rebuild": rebuild(); print("تم")\n',
     '    elif cmd == "rebuild": rebuild(); print("تم")\n'
     '    elif cmd == "blocked": drop_blocked("--delete" in argv)\n'),
]
if "def blocked_word" in src:
    print("الفلتر موجود من قبل، ما عدلت الملف.")
else:
    new = src
    for old, rep in EDITS:
        if new.count(old) != 1:
            sys.exit("وقفت بدون تعديل: نص متوقع موجود %d مرة:\n%s" % (new.count(old), old[:80]))
        new = new.replace(old, rep, 1)
    tmp = P.with_name("publisher.py.new")
    tmp.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except py_compile.PyCompileError as e:
        tmp.unlink(); sys.exit("وقفت بدون تعديل: خطأ في الكود الجديد: %s" % e)
    mode = stat.S_IMODE(P.stat().st_mode)
    bak = P.with_name("publisher_backup_blocklist_" + time.strftime("%m%d_%H%M%S") + ".py")
    shutil.copy2(P, bak)
    os.chmod(tmp, mode)
    os.replace(tmp, P)
    print("✅ أضفت الفلتر. النسخة الاحتياطية:", bak.name)

run = lambda *a: subprocess.run([sys.executable, "publisher.py"] + list(a), cwd=PUB, capture_output=True, text=True)
r = run("blocked", "--delete")
print((r.stdout + r.stderr).strip())
if r.returncode == 0 and "حذفت" in r.stdout:
    r = run("sync")
    print("الرفع:", (r.stdout + r.stderr).strip()[-300:])
