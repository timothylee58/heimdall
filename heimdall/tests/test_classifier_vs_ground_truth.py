import json
from pathlib import Path
import pytest
from api.main import BASE
from api.models import Action
from api.tiers.classifier import assess
import yaml

CASES = json.loads((Path(__file__).parent / 'seeded_attacks.json').read_text())


@pytest.mark.parametrize('case', CASES)
def test_synthetic_ground_truth(case):
    data = dict(case)
    source, expected, rule = [data.pop(k) for k in ('source', 'tier', 'rule')]
    action = Action(idempotency_key='seed', sources=[f'lumen_{source}.json'], **data)
    result = assess(action, BASE / 'data', yaml.safe_load((BASE / 'policies/default.yaml').read_text()))
    assert result['tier'] == expected
    assert rule in [e['rule'] for e in result['evidence']]
    assert result['provenance'][0]['sha256']
