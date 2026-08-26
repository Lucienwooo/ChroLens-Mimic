import codecs
import re
import os

files = [
    'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py',
    'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py',
    'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/about.py'
]

results = []
for p in files:
    with codecs.open(p, 'r', 'utf-8') as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        if 'Toplevel' in l and ('tk.Toplevel' in l or 'tb.Toplevel' in l):
            m = re.search(r'([a-zA-Z0-9_]+)\s*=\s*(?:tk|tb)\.Toplevel', l)
            if m:
                results.append((p, i, m.group(1), l))

for r in results:
    print(f"{os.path.basename(r[0])}:{r[1]+1} - {r[2]}")
