import codecs
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()
content = content.replace('self.images_root = os.path.join(base_dir, \"images\")', 'self.images_root = os.path.join(base_dir, \"scripts\", \"images\")')
content = content.replace('self.images_root = \"images\"', 'self.images_root = os.path.join(\"scripts\", \"images\")')
with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)
print('Done patching')
