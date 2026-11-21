import re


def normalize(text):
    return ' '.join(text.lower().split())


def check_claims(text, docs):
    failures = []
    facts = [(d['path'], f) for d in docs for f in d.get('facts', [])]
    for sentence in re.split(r'(?<=[.!?])\s+|\n+', text.strip()):
        if not sentence:
            continue
        if re.search(r'\d|\b(will|guarantee|commit|promise)\b', sentence, re.I):
            # Require the complete contextual statement, not a coincidental number.
            matches = [p for p, f in facts if normalize(sentence).rstrip('.!?') == normalize(f).rstrip('.!?')]
            if not matches:
                failures.append({'claim': sentence, 'reason': 'untraceable or contradicted contextual claim',
                                 'source_corrections': [{'path': p, 'fact': f} for p, f in facts]})
    return failures
