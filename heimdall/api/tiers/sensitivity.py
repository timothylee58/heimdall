import json
from pathlib import Path

LEVELS = ['public', 'internal', 'confidential', 'regulated']


def load_sources(root: Path, names: list[str]):
    root = root.resolve()
    docs = []
    for name in names:
        candidate = Path(name)
        if candidate.is_absolute() or '..' in candidate.parts:
            raise ValueError('source path must be relative without traversal')
        path = (root / candidate).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('source outside trusted data root or missing')
        doc = json.loads(path.read_text())
        if doc.get('sensitivity') not in LEVELS or not isinstance(doc.get('text'), str):
            raise ValueError('invalid trusted source')
        docs.append({'path': name, **doc})
    return docs


def classify(docs):
    # Structured labels and explicit content markings are both trusted source evidence.
    levels = [d['sensitivity'] for d in docs]
    for d in docs:
        for level in LEVELS:
            if f'[{level.upper()}]' in d['text']:
                levels.append(level)
    return max(levels, key=LEVELS.index)
