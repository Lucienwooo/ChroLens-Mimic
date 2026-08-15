import os
import re
import ast

def scan_file(filepath):
    results = {
        'classes': [],
        'titles': []
    }
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                results['classes'].append(node.name)
    except SyntaxError:
        pass
        
    title_matches = re.findall(r'\.title\(([\'"])([^\'"]+)\1\)', content)
    for match in title_matches:
        results['titles'].append(match[1])
        
    return results

repo_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main'
report = []

for root, dirs, files in os.walk(repo_path):
    if 'archive_patches' in root or 'scratch' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, repo_path)
            res = scan_file(filepath)
            if res['classes'] or res['titles']:
                report.append(f"## {relpath}")
                if res['titles']:
                    report.append(f"- **視窗/介面標題**: {', '.join(set(res['titles']))}")
                if res['classes']:
                    report.append(f"- **主要類別**: {', '.join(res['classes'])}")
                report.append("")

with open('c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/feature_report.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
print('Scan complete.')
