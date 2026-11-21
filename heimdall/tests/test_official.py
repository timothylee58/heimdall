import json
import inspect
import subprocess
import sys
import official_checks
import pytest
from fastapi.testclient import TestClient
from api.main import BASE, create_app
from official_checks import run, proposals


@pytest.mark.parametrize('mutation, expected_exit', [('', 0), ("; result['scenario_score'] = 14", 1), ("; result['classifier']['mismatches'] = [{}]", 1)])
def test_official_cli(tmp_path, mutation, expected_exit):
    script = inspect.getsource(official_checks).replace('result = run()', 'result = run()' + mutation)
    output = tmp_path / 'results.json'
    completed = subprocess.run([sys.executable, '-c', script, '--output', str(output)], cwd=BASE, check=False)
    assert completed.returncode == expected_exit
    assert output.is_file()


def test_official_replay():
    result = run()
    assert result['scenario_score'] == 15
    assert result['classifier']['correct'] == result['classifier']['total'] == 27
    assert result['classifier']['mismatches'] == []
    assert result['data_file_count'] == 28
    assert result['ledger_verification']['valid']
    s4 = result['scenarios'][3]['events'][-1]['result']
    assert len(s4['claims']) == 3
    assert any('20%' in e['excerpt'] for e in s4['source_evidence'])
    assert any('5,040' in e['excerpt'] for e in s4['source_evidence'])
    assert any('8,040' in e['excerpt'] for e in result['scenarios'][2]['events'][0]['result']['source_evidence'])


def test_official_blocks_not_overrideable(tmp_path):
    client = TestClient(create_app(tmp_path / 'db', BASE / 'kit/data'))
    for spec, actions in proposals(BASE / 'kit'):
        for i, action in enumerate(actions):
            key = f"{spec['id']}-{i}"
            result = client.post('/actions', json=dict(idempotency_key=key, **action)).json()
            if result['tier'] == 'BLOCK':
                assert client.post('/approvals/' + key, json=dict(decision='approve', owner_note='Cannot override NEVER')).status_code == 409


def test_no_label_leakage(tmp_path):
    from api.tiers.sensitivity import classify, load_sources
    (tmp_path / 'contact.csv').write_text('contact,email,phone\nPerson,person@example,000\n')
    (tmp_path / 'ground_truth_labels.json').write_text('invalid and must never be read')
    assert classify(load_sources(tmp_path, ['contact.csv'])) == 'regulated'


@pytest.mark.parametrize('text', ['Other total is 5,040.', 'The deadline moved by 5 days.', 'Rush surcharge is 25%.'])
def test_contextual_number_not_coincidence(tmp_path, text):
    client = TestClient(create_app(tmp_path / 'db', BASE / 'kit/data'))
    result = client.post('/actions', json=dict(idempotency_key='claim', kind='email', recipient='known', sources=['finance/invoice_2026-036_ferro_logistics.md', 'clients/contract_ferro_logistics_2026.md'], text=text)).json()
    assert result['tier'] == 'BLOCK'
    assert result['claims'][0]['source_corrections']
