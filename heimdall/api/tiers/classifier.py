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
    tier = max((e['tier'] for e in evidence), key=['ALLOW', 'HOLD', 'BLOCK'].index)
    provenance = [{'path': d['path'], 'sha256': hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()} for d in docs]
    return {'tier': tier, 'sensitivity': sensitivity, 'evidence': evidence,
            'claims': claims, 'provenance': provenance}
