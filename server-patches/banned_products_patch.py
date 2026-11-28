#!/usr/bin/env python3
"""يوسّع فلتر المنتجات الممنوعة (أسلحة، جنسي، تدخين وفيب ومخدرات، خمور، تجسس ورادار، قمار، مقلد، أقفال، رموز المثلية)
في بوت نشر علي اكسبرس (~/bot-affiliate/boot.py) والناشر (~/wafferna-publisher/publisher.py).
يحتاج إن فلتر الأسلحة السابق مركّب. ياخذ نسخ احتياطية، يفحص الكود، ثم يعرض الممنوع في الموقع ويعيد تشغيل البوت."""
import os, py_compile, shutil, stat, subprocess, sys, time
from pathlib import Path

H = os.path.expanduser
NEW = 'BLOCK_ALLOW = re.compile(\n    r"مسدس\\s*(?:لل|ال)?(?:مساج|تدليك|غراء|حرار|هواء|رش|طلاء|بخ|سيليكون|لحام|مسامير|ماء|مياه|فقاع|تنظيف|غسيل)"\n    r"|(?:مدلك|مساج|تدليك)\\s*(?:ال)?بندقي\\w*|بندقي\\w*\\s*(?:لل|ال)?(?:مساج|تدليك)|مسدس\\s*(?:ال)?مفك"\n    r"|مضاد\\s*(?:لل)?تجسس|حماية\\s*(?:من\\s*)?(?:ال)?تجسس|ضد\\s*(?:ال)?تجسس"\n    r"|(?:massage|glue|heat|spray|nail|water|bubble|caulking|paint|screwdriver)\\s*guns?|bullet\\s*(?:journal|points?|list|cam\\w*|style)"\n    r"|cigarette\\s*lighter\\s*(?:socket|adapter|plug|charger|port|splitter)|(?:car|vehicle)\\s*cigarette\\s*lighter"\n    r"|(?:anti|no|stop)[\\s-]*spy|privacy\\s*(?:screen|film|protector)|wine[\\s-]*(?:red|colou?r|glass(?:es)?)"\n    r"|weed\\s*(?:eater|trimmer|whacker|puller|killer|barrier|cutter|remover|block)", re.I)\n_AR_STEMS = ("ذخير|أسلح|اسلح|إسلح|مسدس|بندقي|بنادق|خرطوش|خنجر|خناجر|نشاب|ايرسوفت|إيرسوفت|مطواة"\n             "|سجائر|سيجار|معسل|أرجيل|ارجيل|نرجيل|ماريجوان|حشيشة|مخدرات|خمور|نبيذ|ويسكي|فودكا"\n             "|تجسس|تنصت|قمار|كازينو|بوكر|مراهن|مثليين|المثلية")\n_AR_WORDS = "سلاح|سلاحك|سلاحه|جنسي|جنسية|منشطات|رصاصة|رصاصات|طلقات|نبلة|فيب|فيبات|شيشة|تبغ|خمر|بيرة|قنب|مقلد|مقلدة"\n_AR = r"(?<!\\w)[وبلف]?(?:ال|لل)?(?:(?:%s)\\w*|(?:%s))(?!\\w)" % (_AR_STEMS, _AR_WORDS)\nBLOCK_RE = re.compile(\n    _AR +\n    r"|طلقة نارية|كاتم (?:لل)?صوت|قوس ونشاب|صاعق كهرب|(?:بخاخ|رذاذ) (?:ال)?فلفل|قبضة حديد|بلاستر جل"\n    r"|سكاكين (?:قتال|صيد|تكتيك|جيب|عسكري|رمي)|سكين (?:قتال|صيد|تكتيك|جيب|عسكري|رمي)"\n    r"|منشط جنسي|للكبار فقط|(?:ألعاب|العاب) الكبار|حبوب تكبير|تكبير القضيب|واقي ذكري|سيجارة إلكترونية|سيجارة الكترونية"\n    r"|كاميرا (?:مخفية|خفية|سرية|تجسس)|كاشف (?:ال)?رادار|كاشف ساهر|مانع ساهر|تقليد ماركة|فتح (?:ال)?(?:أقفال|اقفال)"\n    r"|\\b(?:ammo|ammunition|bullets?|cartridges? box|firearms?|weapons?|pistols?|rifles?|shotguns?|handguns?|airguns?|bb guns?"\n    r"|holsters?|crossbows?|slingshots?|tasers?|stun guns?|pepper spray|airsoft|gel blasters?|brass knuckles?|daggers?"\n    r"|switchblades?|butterfly knife|tactical knife|combat knife|hunting knife|gun safe"\n    r"|sex|sexy|sexual|erotic|adult toys?|sex toys?|vibrators?|dildos?|masturbat\\w*|fetish|bdsm|condoms?|penis|orgasm\\w*"\n    r"|lingerie|strap[\\s-]?on|anal|viagra|cialis|steroids?|aphrodisiac"\n    r"|vapes?|vaping|vaporizers?|e[\\s-]?cig\\w*|cigarettes?|cigars?|tobacco|hookah|shisha|nargile|weed|cannabis|marijuana|bongs?"\n    r"|thc|cbd|smoking pipes?|rolling papers?|herb grinders?"\n    r"|alcohol(?:ic)? drinks?|liquor|whisk(?:e)?y|vodka|tequila|beer|wine|champagne"\n    r"|spy|hidden cameras?|covert cameras?|nanny cam|listening devices?|bugging|radar detectors?|laser jammers?"\n    r"|casino|poker|gambling|roulette|slot machines?|counterfeit|fake (?:id|passport|money)|prop money"\n    r"|lock ?picks?|lockpick\\w*|lock picking|pride flags?|rainbow flags?|lgbt\\w*)\\b", re.I)\n'
FILES = [(Path(H(os.environ.get("WF_AFF", "~/bot-affiliate"))) / "boot.py", "\ndef weapon_word"),
         (Path(H(os.environ.get("WF_PUB", "~/wafferna-publisher"))) / "publisher.py", "\ndef blocked_word")]
plan = []
for P, nxt in FILES:
    src = P.read_text(encoding="utf-8")
    if "_AR_STEMS" in src:
        print("موجود من قبل:", P.name); continue
    a, b = src.find("BLOCK_ALLOW = re.compile("), src.find(nxt)
    if a < 0 or b < a or src.count("BLOCK_ALLOW = re.compile(") != 1:
        sys.exit("وقفت بدون تعديل: ما لقيت الفلتر القديم في %s (لازم فلتر الأسلحة يكون مركّب)" % P)
    new = src[:a] + NEW + src[b:]
    tmp = P.with_name(P.name + ".new")
    tmp.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except py_compile.PyCompileError as e:
        tmp.unlink(); sys.exit("وقفت بدون تعديل: خطأ في %s: %s" % (P.name, e))
    plan.append((P, tmp))
for P, tmp in plan:   # نبدّل الملفين بعد ما يمر الاثنين من الفحص
    bak = P.with_name(P.name + ".bak-" + time.strftime("%Y%m%d-%H%M%S") + "-before-banned")
    shutil.copy2(P, bak)
    os.chmod(tmp, stat.S_IMODE(P.stat().st_mode))
    os.replace(tmp, P)
    print("✅ حدّثت الفلتر في", P.name, "| النسخة الاحتياطية:", bak.name)

if os.environ.get("WF_NO_RESTART"):
    sys.exit(0)
pub = FILES[1][0].parent
r = subprocess.run([sys.executable, "publisher.py", "blocked"], cwd=pub, capture_output=True, text=True)
print("\nالممنوع الموجود في الموقع (ما حذفت شي):\n" + (r.stdout + r.stderr).strip())
r = subprocess.run(["sudo", "-n", "systemctl", "restart", "bot-affiliate"], capture_output=True, text=True)
if r.returncode:
    print("⚠️ ما قدرت أعيد تشغيل البوت، شغّل: sudo systemctl restart bot-affiliate")
else:
    time.sleep(4)
    st = subprocess.run(["systemctl", "is-active", "bot-affiliate"], capture_output=True, text=True).stdout.strip()
    print("حالة بوت النشر:", st, "✅" if st == "active" else "⚠️ أرسل الناتج")
