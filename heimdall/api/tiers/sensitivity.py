import hashlib
import csv
import io
import json
import re
import yaml
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
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        if path.suffix == '.json':
            doc = json.loads(text)
        elif path.suffix == '.md':
            parts = text.split('---', 2)
            if len(parts) != 3 or parts[0].strip():
                raise ValueError('missing source sensitivity header')
            header = yaml.safe_load(parts[1])
            level = header.get('sensitivity')
            level = 'confidential' if level == 'client-confidential' else level
            body = parts[2].strip()
            doc = dict(sensitivity=level, text=body, facts=[body] + [line.strip() for line in body.splitlines() if line.strip()], format='markdown')
            total = re.search(r'\|\s*\*\*Total\*\*\s*\|\s*\*\*([\d,]+)\*\*', body)
            if total:
                doc['invoice_amount'] = float(total[1].replace(',', ''))
        elif path.suffix == '.csv':
            rows = list(csv.DictReader(io.StringIO(text)))
            fields = set(rows[0]) if rows else set()
            if not {'contact', 'email', 'phone'} <= fields:
                raise ValueError('CSV requires trusted personal-contact schema')
            doc = dict(sensitivity='regulated', text=text, facts=[], format='csv')
        else:
            raise ValueError('unsupported source format')
        doc['raw_sha256'] = hashlib.sha256(raw).hexdigest()
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
