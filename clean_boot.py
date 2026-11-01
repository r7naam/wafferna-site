#!/usr/bin/env python3
"""تنظيف بقايا تجارب الربط من boot.py. بدون --apply يعرض فقط ما سيُحذف."""
import ast, sys, shutil, py_compile, os

PATH = os.path.expanduser("~/bot-affiliate/boot.py")
TARGETS = {"_site_text", "_to_site_worker"}
apply = "--apply" in sys.argv

src = open(PATH, encoding="utf-8").read()
tree = ast.parse(src)
lines = src.splitlines(keepends=True)

defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in TARGETS]
if not defs:
    print("لا توجد بقايا للحذف."); sys.exit(0)

inside = set()
for d in defs:
    for n in ast.walk(d):
        inside.add(id(n))
used = {}
for n in ast.walk(tree):
    if id(n) in inside: continue
    name = n.id if isinstance(n, ast.Name) else (n.attr if isinstance(n, ast.Attribute) else None)
    if name in TARGETS:
        used.setdefault(name, []).append(getattr(n, "lineno", "?"))

safe = [d for d in defs if d.name not in used]
for d in defs:
    start = min([d.lineno] + [x.lineno for x in d.decorator_list])
    print("%s: الأسطر %d-%d %s" % (d.name, start, d.end_lineno,
          "(مستخدمة في الأسطر %s — لن تُحذف)" % used[d.name] if d.name in used else "(غير مستخدمة)"))
if not safe:
    print("لا شيء آمن للحذف."); sys.exit(0)
if not apply:
    print("\nهذا عرض فقط. لتنفيذ الحذف أضف --apply"); sys.exit(0)

shutil.copy(PATH, PATH.replace(".py", "_backup_before_clean.py"))
drop = set()
for d in safe:
    start = min([d.lineno] + [x.lineno for x in d.decorator_list])
    drop.update(range(start - 1, d.end_lineno))
new = "".join(l for i, l in enumerate(lines) if i not in drop)
tmp = PATH + ".tmp.py"
open(tmp, "w", encoding="utf-8").write(new)
try:
    py_compile.compile(tmp, doraise=True)
except Exception as e:
    os.remove(tmp); print("فشل الفحص، لم يتغير شيء:", e); sys.exit(1)
os.replace(tmp, PATH)
print("تم حذف %d دالة. النسخة الاحتياطية: boot_backup_before_clean.py" % len(safe))
print("أعد تشغيل البوت ليعمل بالنسخة الجديدة: sudo systemctl restart bot-affiliate")
