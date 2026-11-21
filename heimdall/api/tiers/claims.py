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
            # An order's quantity is not itself a delivery promise or price assertion.
            quantity = re.fullmatch(r'Please go ahead with the (\d+) units\.', sentence, re.I)
            if quantity:
                matches += [d['path'] for d in docs if re.search(rf'\b{quantity[1]} (?:extra )?units\b', d['text'])]
            if not matches:
                failures.append({'claim': sentence, 'reason': 'untraceable or contradicted contextual claim',
                                 'source_corrections': [{'path': p, 'fact': f} for p, f in facts]})
    return failures
