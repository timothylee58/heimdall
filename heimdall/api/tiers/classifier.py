import hashlib
import json
from .sensitivity import load_sources, classify
from .claims import check_claims
from .rules import evaluate


def assess(action, root, policy):
    docs = load_sources(root, action.sources)
    sensitivity = classify(docs)
    claims = check_claims(action.text, docs)
    evidence = evaluate(action, sensitivity, docs, claims, policy)
    context = []
    # Oversight-only context does not become outbound content or change its label.
    for name in action.sources:
        if name.endswith('.csv'):
            sidecar = name[:-4] + '.README.md'
            if (root / sidecar).is_file():
                context.extend(load_sources(root, [sidecar]))
    if action.kind == 'delete' and any('UNPAID' in d['text'].upper() for d in docs):
        cashflow = 'finance/cashflow_notes_nov2026.md'
        if (root / cashflow).is_file():
            context.extend(load_sources(root, [cashflow]))
    tier = max((e['tier'] for e in evidence), key=['ALLOW', 'HOLD', 'BLOCK'].index)
    provenance = [{'path': d['path'], 'sha256': hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()} for d in docs + context]
    return {'tier': tier, 'sensitivity': sensitivity, 'evidence': evidence,
            'source_evidence': [{'path': d['path'], 'excerpt': d['text'], 'role': 'oversight-context' if d in context else 'action-source'} for d in docs + context],
            'claims': claims, 'provenance': provenance}
