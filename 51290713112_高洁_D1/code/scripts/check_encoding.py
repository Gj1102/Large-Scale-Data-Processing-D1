from pathlib import Path
import re
roots = [Path('D1-DDP'), Path('51290713112_高洁_D1')]
extensions = {'.py', '.md', '.yaml', '.yml', '.txt', '.json', '.csv'}
errors = []
question_marks = []
count = 0
for root in roots:
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in extensions or 'data' in path.parts:
            continue
        count += 1
        try:
            text = path.read_text(encoding='utf-8-sig')
            if re.search(r'\?{4,}', text):
                question_marks.append(str(path))
        except UnicodeDecodeError:
            errors.append(str(path))
print('text files:', count, 'invalid UTF-8:', errors, 'question sequences:', question_marks)
