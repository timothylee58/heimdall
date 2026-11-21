import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from api.main import create_app, BASE
from api.models import Action
from api.approvals import Conflict


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / 'audit.db'))


def payload(**kw):
    return {'idempotency_key': 'item', 'kind': 'email', 'sources': ['lumen_public.json'], **kw}


def test_approval_persistence_single_use(tmp_path):
    path = tmp_path / 'audit.db'
    c = TestClient(create_app(path))
    assert c.post('/actions', json=payload()).json()['status'] == 'pending'
    c = TestClient(create_app(path))
    assert c.post('/approvals/item', json={'decision': 'approve', 'owner_note': 'Reviewed locally'}).json()['status'] == 'approved_simulated'
    assert c.post('/approvals/item', json={'decision': 'deny', 'owner_note': 'Again'}).status_code == 409
    assert c.post('/actions', json=payload()).json()['status'] == 'approved_simulated'
    assert c.get('/ledger/verify').json()['count'] == 2
    assert 'Reviewed locally' in c.get('/briefing').text


def test_denial_block_and_binding(client):
    client.post('/actions', json=payload())
    assert client.post('/approvals/item', json={'decision': 'deny', 'owner_note': 'No'}).json()['status'] == 'denied'
    assert client.post('/actions', json=payload(text='different')).status_code == 409
    assert client.post('/approvals/missing', json={'decision': 'approve', 'owner_note': 'Yes'}).status_code == 404
    client.post('/actions', json=payload(idempotency_key='block', kind='upload', sources=['lumen_regulated.json']))
    assert client.post('/approvals/block', json={'decision': 'approve', 'owner_note': 'Yes'}).status_code == 409


def test_re_evaluation_original_policy(tmp_path):
    root = tmp_path / 'data'
    root.mkdir()
    doc = root / 'doc.json'
    doc.write_text(json.dumps({'sensitivity': 'internal', 'text': 'internal'}))
    app = create_app(tmp_path / 'db', root)
    c = TestClient(app)
    assert c.post('/actions', json=payload(kind='upload', sources=['doc.json'])).json()['tier'] == 'HOLD'
    app.state.service.policy['invoice_threshold'] = 999999
    doc.write_text(json.dumps({'sensitivity': 'regulated', 'text': '[REGULATED]'}))
    r = c.post('/approvals/item', json={'decision': 'approve', 'owner_note': 'Review'}).json()
    assert r['tier'] == 'BLOCK' and r['status'] == 'blocked'


@pytest.mark.parametrize('source', ['../README.md', '/etc/passwd', 'missing.json'])
def test_source_escape(client, source):
    assert client.post('/actions', json=payload(sources=[source])).status_code == 400


def test_symlink_escape(tmp_path):
    root = tmp_path / 'data'
    root.mkdir()
    (root / 'escape.json').symlink_to(BASE / 'data/lumen_public.json')
    c = TestClient(create_app(tmp_path / 'db', root))
    assert c.post('/actions', json=payload(sources=['escape.json'])).status_code == 400


@pytest.mark.parametrize('text,tier', [('Lumen list price is 8000.', 'ALLOW'), ('Other list price is 8000.', 'BLOCK'), ('Lumen list price is 9000.', 'BLOCK'), ('Lumen will deliver tomorrow.', 'BLOCK'), ('Lumen launch date is 2026-12-01.', 'ALLOW'), ('Lumen launch date is 2026-12-02.', 'BLOCK')])
def test_contextual_facts(client, text, tier):
    result = client.post('/actions', json=payload(recipient='known', text=text)).json()
    assert result['tier'] == tier
    if tier == 'BLOCK':
        assert result['claims'][0]['source_corrections']


def test_all_evidence_strictest(client):
    r = client.post('/actions', json=payload(sources=['lumen_regulated.json'], scope='outside', text='Revenue is 8000.')).json()
    assert r['tier'] == 'BLOCK'
    assert {'R02', 'R04', 'R05', 'R18'} <= {e['rule'] for e in r['evidence']}


@pytest.mark.parametrize('amount,tier', [(6499.99, 'BLOCK'), (6500, 'HOLD'), (8000, 'ALLOW')])
def test_floor(client, amount, tier):
    assert client.post('/actions', json=payload(kind='quote', amount=amount, list_price=8000, customer='Greenstep')).json()['tier'] == tier


@pytest.mark.parametrize('amount', [None, 1000, 1001, 998])
def test_invoice_missing_or_mismatch(client, amount):
    assert client.post('/actions', json=payload(kind='invoice', amount=amount, invoice_matches=True, sources=['lumen_internal.json'])).json()['tier'] == 'HOLD'


def test_trusted_assertions(client):
    assert client.post('/actions', json=payload(kind='order', written_confirmation=True)).json()['tier'] == 'HOLD'
    assert client.post('/actions', json=payload(idempotency_key='news', kind='news', announced=True)).json()['tier'] == 'ALLOW'
    assert client.post('/actions', json=payload(idempotency_key='delete', kind='delete', contract_directed_error=True, sources=['lumen_regulated.json'])).json()['notification']


def test_highest_content_and_provenance(tmp_path):
    doc = tmp_path / 'doc.json'
    doc.write_text(json.dumps({'sensitivity': 'public', 'text': '[REGULATED] content'}))
    c = TestClient(create_app(tmp_path / 'db', tmp_path))
    r = c.post('/actions', json=payload(kind='upload', sources=['doc.json'])).json()
    assert r['sensitivity'] == 'regulated' and r['tier'] == 'BLOCK'


@pytest.mark.parametrize('extra', [{'tier': 'ALLOW'}, {'amount': -1}, {'kind': 'send'}, {'kind': 'quote'}, {'sources': []}])
def test_validation(client, extra):
    assert client.post('/actions', json=payload(**extra)).status_code == 422


def test_append_only_and_tamper(tmp_path):
    path = tmp_path / 'db'
    c = TestClient(create_app(path))
    c.post('/actions', json=payload())
    with sqlite3.connect(path) as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE events SET body='{}'")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('DELETE FROM events')
        db.execute('DROP TRIGGER events_no_update')
        db.execute("UPDATE events SET body='{}'")
    assert not c.get('/ledger/verify').json()['valid']
    assert c.post('/actions', json=payload(idempotency_key='next')).status_code == 400


def test_concurrent_writes_and_duplicate(tmp_path):
    app = create_app(tmp_path / 'db')
    service = app.state.service
    def send(i):
        return service.submit(Action(**payload(idempotency_key=str(i), recipient='known')))
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(send, range(30)))
        list(pool.map(send, [30] * 8))
    assert app.state.ledger.read()['verification']['count'] == 31
    assert app.state.ledger.read()['verification']['valid']


def test_concurrent_approval_once(tmp_path):
    from api.models import Approval
    service = create_app(tmp_path / 'db').state.service
    service.submit(Action(**payload()))
    def decide(_):
        try:
            return service.decide('item', Approval(decision='approve', owner_note='review'))['status']
        except Conflict:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(decide, range(4)))
    assert results.count('approved_simulated') == 1
    assert results.count('conflict') == 3
