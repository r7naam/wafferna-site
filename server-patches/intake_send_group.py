#!/usr/bin/env python3
"""يضيف لبوت الاستقبال (~/amazon-bot/intake_bot.py) أمر «ارسال للقروب»: ينشر المسودة فوراً مثل «نشر الحين».
ياخذ نسخة احتياطية، ويتأكد من كل نص قبل التغيير، ويفحص إن الكود يشتغل. بعدها يعرض سطور الكرون الخاصة بالبوت."""
import os, py_compile, shutil, subprocess, sys, time
from pathlib import Path

P = Path.home() / "amazon-bot" / "intake_bot.py"
src = P.read_text(encoding="utf-8")

SEND = r"(?:نشر\s*(?:الحين|الآن|الان)|[اإأ]رس(?:ا)?ل\s*(?:لل|ل|ال|في\s*ال|على\s*ال)?\s*(?:قروب|جروب|قناة|قناه))"
EDITS = [
    ('m = re.fullmatch(r"نشر\\s*(?:الحين|الآن|الان)\\s*(\\d*)", text)',
     'm = re.fullmatch(r"' + SEND + r'\s*(\d*)", text)'),
    ('    "   • نشر الحين ← ينزل في القناة والموقع فوراً، ويرد عليك برابط الصفحة\\n\\n"',
     '    "   • نشر الحين (أو: ارسال للقروب) ← ينزل في القناة والموقع فوراً، ويرد عليك برابط الصفحة\\n\\n"'),
    ('"تبيه ينزل الحين؟ أرسل: نشر الحين\\nولعرض القائمة: القائمة"',
     '"تبيه ينزل الحين؟ أرسل: نشر الحين (أو: ارسال للقروب)\\nولعرض القائمة: القائمة"'),
]

if "قروب" in src:
    print("التعديل موجود من قبل، ما غيرت شي.")
else:
    new = src
    for old, rep in EDITS:
        n = new.count(old)
        if n != 1:
            sys.exit("وقفت بدون تعديل: نص متوقع موجود %d مرة بدل مرة وحدة:\n%s" % (n, old[:90]))
        new = new.replace(old, rep)
    tmp = P.with_name(P.name + ".new")
    tmp.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except py_compile.PyCompileError as e:
        tmp.unlink(); sys.exit("وقفت بدون تعديل: الكود الجديد فيه خطأ: %s" % e)
    bak = P.with_name(P.name + ".bak_" + time.strftime("%m%d_%H%M%S"))
    shutil.copy2(P, bak)
    shutil.copymode(P, tmp)
    os.replace(tmp, P)
    print("خلصت ✅ النسخة الاحتياطية:", bak.name)

import re
rx = re.compile(r"(?:نشر\s*(?:الحين|الآن|الان)|[اإأ]رس(?:ا)?ل\s*(?:لل|ل|ال|في\s*ال|على\s*ال)?\s*(?:قروب|جروب|قناة|قناه))\s*(\d*)")
for t in ("ارسال للقروب", "إرسال للقروب", "ارسل للقروب", "ارسل القروب", "نشر الحين", "نشر الحين 2"):
    assert rx.fullmatch(t), t
assert not rx.fullmatch("نشر")

try:
    cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
except FileNotFoundError:
    cron = ""
lines = [l for l in cron.splitlines() if "intake_bot" in l and not l.lstrip().startswith("#")]
print("\nسطور الكرون للبوت:")
print("\n".join(lines) if lines else "  (ولا سطر! البوت ما يشتغل من الكرون)")
if not any("--publish-next" in l for l in lines):
    print("⚠️ ما فيه سطر --publish-next، يعني اللي تحطه بـ«نشر» يبقى في القائمة وما ينزل.")
if not any("--publish-next" not in l for l in lines):
    print("⚠️ ما فيه سطر استقبال الرسائل، يعني البوت ما يقرا رسائلك أصلاً.")
