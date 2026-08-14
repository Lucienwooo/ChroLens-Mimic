import codecs

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

new_lines = []
in_show_page = False
for line in lines:
    if line.strip() == 'def show_page(self, idx):':
        in_show_page = True
    
    new_lines.append(line)
    
    if in_show_page and line.strip() == 'self.show_page(0)' and len(line) - len(line.lstrip()) == 12:
        if "elif idx == 3:" in "".join(new_lines[-5:]):
            new_lines.append('        self.update_idletasks()\n')
            in_show_page = False

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.writelines(new_lines)
