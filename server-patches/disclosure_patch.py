# One-off patch for ~/wafferna-publisher/publisher.py (runs on the bot server, not part of the site).
# Pages without a price (all Amazon pages) get a disclosure line that does not mention a publish-time price.
import shutil, sys, time, os
p = "publisher.py"
s = open(p, encoding="utf-8").read()
if "_disclosure" in s:
    print("already patched"); sys.exit(0)
old_txt = 'السعر المعروض هو سعر وقت النشر ({date_txt}) وقد يتغير، والسعر النهائي هو المكتوب في صفحة المتجر.'
anchor = '    date_txt = parse_dt(o["created"]).strftime("%Y-%m-%d")\n'
if s.count(old_txt) != 1 or s.count(anchor) != 1:
    print("NOT patched: text=%d anchor=%d" % (s.count(old_txt), s.count(anchor))); sys.exit(1)
add = anchor + '''    if "amazon" in str(store).lower() or "أمازون" in str(store) or not price:
        _disclosure = "السعر والتوفر يحددهما المتجر، فتأكد منهما في صفحة المنتج قبل الشراء."
    else:
        _disclosure = "السعر المعروض هو سعر وقت النشر (%s) وقد يتغير، والسعر النهائي هو المكتوب في صفحة المتجر." % date_txt
'''
bak = "publisher_backup_disclosure_%s.py" % time.strftime("%m%d_%H%M%S")
if not os.access(p, os.W_OK):
    print("NOT patched: publisher.py is not writable by this user (try with sudo)"); sys.exit(1)
shutil.copyfile(p, bak); print("backup:", bak)
s = s.replace(anchor, add).replace(old_txt, '{_disclosure}')
open(p, "w", encoding="utf-8").write(s)
print("patched")
