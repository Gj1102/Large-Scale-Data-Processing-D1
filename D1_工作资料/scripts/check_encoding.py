from pathlib import Path
import re
root = Path(__file__).resolve().parents[2]
extensions = {'.py', '.md', '.yaml', '.yml', '.txt', '.json', '.csv'}
errors, question_marks = [], []
count = 0
for path in root.rglob('*'):
    if not path.is_file() or path.suffix.lower() not in extensions or 'data' in path.relative_to(root).parts:
        continue
    count += 1
    try:
        text = path.read_text(encoding='utf-8-sig')
        if re.search(r'\?{4,}', text):
            question_marks.append(str(path))
    except UnicodeDecodeError:
        errors.append(str(path))
print('text files:', count, 'invalid UTF-8:', errors, 'question sequences:', question_marks)
if errors or question_marks:
    raise SystemExit(1)
