#!/usr/bin/env python3
"""فلتر الأسلحة والذخيرة لبوت نشر القناة (~/bot-affiliate/boot.py):
- يتخطى أي منتج من علي اكسبرس اسمه فيه كلمة ممنوعة، ويحفظه عشان ما ينعاد.
- يفحص نص المنشور بعد ما يكتبه Claude قبل النشر.
- send_post يرفض أي منشور فيه كلمة ممنوعة (حماية أخيرة لكل أنواع المنشورات) ويبلغ الأدمن.
ياخذ نسخة احتياطية، يتحقق من كل نص، يفحص الكود، ثم يعيد تشغيل الخدمة."""
import os, py_compile, shutil, stat, subprocess, sys, time
from pathlib import Path

P = Path(os.path.expanduser(os.environ.get("WF_AFF", "~/bot-affiliate"))) / "boot.py"
src = P.read_text(encoding="utf-8")
WEAPON = '# ---------------------- منتجات ممنوعة (أسلحة وذخيرة) ----------------------\nBLOCK_ALLOW = re.compile(\n    r"مسدس\\s*(?:لل|ال)?(?:مساج|تدليك|غراء|حرار|هواء|رش|طلاء|بخ|سيليكون|لحام|مسامير|ماء|مياه|فقاع|تنظيف|غسيل)"\n    r"|(?:مدلك|مساج|تدليك)\\s*(?:ال)?بندقي\\w*|بندقي\\w*\\s*(?:لل|ال)?(?:مساج|تدليك)|مسدس\\s*(?:ال)?مفك"\n    r"|(?:massage|glue|heat|spray|nail|water|bubble|caulking|paint|screwdriver)\\s*guns?|bullet\\s*(?:journal|points?|list)", re.I)\nBLOCK_RE = re.compile(\n    r"ذخير|سلاح|أسلحة|اسلحة|إسلحة|مسدس|مسدسات|بندقي|بنادق|رصاصة|رصاصات|طلقات|طلقة نارية|خرطوش|كاتم صوت|كاتم للصوت"\n    r"|خنجر|خناجر|نبلة|نبال|نشاب|قوس ونشاب|صاعق كهرب|بخاخ فلفل|رذاذ الفلفل|بخاخ الفلفل|ايرسوفت|إيرسوفت|بلاستر|قبضة حديد|مطواة"\n    r"|سكين (?:قتال|صيد|تكتيك|جيب|عسكري|رمي)|سكاكين (?:قتال|صيد|تكتيك|جيب|عسكري|رمي)"\n    r"|\\b(?:ammo|ammunition|bullets?|cartridges? box|firearms?|weapons?|pistols?|rifles?|shotguns?|handguns?|airguns?|bb guns?"\n    r"|holsters?|crossbows?|slingshots?|tasers?|stun guns?|pepper spray|airsoft|gel blasters?|brass knuckles?|daggers?"\n    r"|switchblades?|butterfly knife|tactical knife|combat knife|hunting knife|gun safe)\\b", re.I)\n\ndef weapon_word(text):\n    """يرجع الكلمة الممنوعة لو النص له علاقة بالأسلحة أو الذخيرة، وإلا \'\'."""\n    m = BLOCK_RE.search(BLOCK_ALLOW.sub(" ", str(text or "")))\n    return m.group(0) if m else ""\n\n\n'
EDITS = [
    ("def pick_product(state):\n", WEAPON + "def pick_product(state):\n"),
    ("            if not pid or pid in posted:\n                continue\n",
     "            if not pid or pid in posted:\n                continue\n"
     "            _bw = weapon_word(p.get(\"product_title\"))\n"
     "            if _bw:\n"
     "                log(f\"تخطيت {pid}: منتج ممنوع ({_bw})\")\n"
     "                state[\"posted\"].append(pid)\n"
     "                save_state(state)\n"
     "                continue\n"),
    ("            return post, pid\n",
     "            _bw = weapon_word(\" \".join(str(post.get(k) or \"\") for k in (\"text\", \"html\", \"name\")))\n"
     "            if _bw:\n"
     "                log(f\"تخطيت {pid}: نص المنشور فيه كلمة ممنوعة ({_bw})\")\n"
     "                state[\"posted\"].append(pid)\n"
     "                save_state(state)\n"
     "                continue\n"
     "            return post, pid\n"),
    ("def send_post(post):\n    global _last_error\n",
     "def send_post(post):\n    global _last_error\n"
     "    _bw = weapon_word(\" \".join(str(post.get(k) or \"\") for k in (\"text\", \"html\", \"name\")))\n"
     "    if _bw:\n"
     "        _last_error = f\"منشور فيه كلمة ممنوعة ({_bw})، ما نشرته\"\n"
     "        log(_last_error)\n"
     "        return False\n"),
]
if "def weapon_word" in src:
    print("الفلتر موجود من قبل، ما عدلت الملف.")
else:
    new = src
    for old, rep in EDITS:
        if new.count(old) != 1:
            sys.exit("وقفت بدون تعديل: نص متوقع موجود %d مرة:\n%s" % (new.count(old), old[:80]))
        new = new.replace(old, rep, 1)
    tmp = P.with_name("boot.py.new")
    tmp.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except py_compile.PyCompileError as e:
        tmp.unlink(); sys.exit("وقفت بدون تعديل: خطأ في الكود الجديد: %s" % e)
    bak = P.with_name("boot.py.bak-" + time.strftime("%Y%m%d-%H%M%S") + "-before-weapons")
    shutil.copy2(P, bak)
    os.chmod(tmp, stat.S_IMODE(P.stat().st_mode))
    os.replace(tmp, P)
    print("✅ أضفت الفلتر. النسخة الاحتياطية:", bak.name)

if os.environ.get("WF_NO_RESTART"):
    sys.exit(0)
r = subprocess.run(["sudo", "-n", "systemctl", "restart", "bot-affiliate"], capture_output=True, text=True)
if r.returncode:
    print("⚠️ ما قدرت أعيد تشغيل البوت:", (r.stderr or "").strip()[-200:])
    print("شغّل بنفسك: sudo systemctl restart bot-affiliate")
else:
    time.sleep(4)
    st = subprocess.run(["systemctl", "is-active", "bot-affiliate"], capture_output=True, text=True).stdout.strip()
    print("حالة البوت بعد إعادة التشغيل:", st, "✅" if st == "active" else "⚠️ أرسل الناتج")
