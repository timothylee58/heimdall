import os
from concurrent.futures import ThreadPoolExecutor
import pytest
from api.main import create_app, BASE
from api.models import Action, Approval


@pytest.mark.parametrize('settings', [
    {'K_SERVICE': 'test'},
    {'HEIMDALL_MODE': 'production'},
    {'HEIMDALL_MODE': 'production', 'HEIMDALL_AUTH_MODE': 'cloud-run-iam'},
    {'HEIMDALL_MODE': 'unknown'},
    {'HEIMDALL_AUTH_MODE': 'public'},
])
def test_fail_closed(monkeypatch, tmp_path, settings):
    for key in ('K_SERVICE', 'HEIMDALL_MODE', 'HEIMDALL_AUTH_MODE', 'DATABASE_URL'):
        monkeypatch.delenv(key, raising=False)
    for key, value in settings.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        create_app(tmp_path / 'local.db')


def test_tls_required(monkeypatch):
    monkeypatch.setenv('HEIMDALL_MODE', 'production')
    monkeypatch.setenv('HEIMDALL_AUTH_MODE', 'cloud-run-iam')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://invalid/unused?sslmode=require')
    with pytest.raises(ValueError, match='verify-full'):
        create_app()


@pytest.mark.parametrize('suffix', [
    '?sslmode=disable', '?sslmode=require', '',
    '?sslmode=verify-full&host=/tmp',
    '?sslmode=disable&host=/cloudsql/other:asia-southeast1:test',
    '?sslmode=disable&host=/cloudsql/heimdall-515408:us-central1:test',
    '?sslmode=disable&host=/cloudsql/heimdall-515408:asia-southeast1:other',
    '?sslmode=disable&host=/cloudsql/heimdall-515408:asia-southeast1:test/../other',
    '?sslmode=disable&host=/cloudsql/heimdall-515408:asia-southeast1:test&hostaddr=127.0.0.1',
    '?sslmode=disable&host=/cloudsql/heimdall-515408:asia-southeast1:test&port=5433',
    '?sslmode=verify-full&hostaddr=127.0.0.1',
    '?sslmode=verify-full&service=override',
])
def test_unsafe_transport(monkeypatch, suffix):
    monkeypatch.setenv('HEIMDALL_MODE', 'production')
    monkeypatch.setenv('HEIMDALL_AUTH_MODE', 'cloud-run-iam')
    monkeypatch.setenv('INSTANCE_CONNECTION_NAME', 'heimdall-515408:asia-southeast1:test')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://runtime@invalid/test' + suffix)
    with pytest.raises(ValueError):
        create_app()


@pytest.mark.parametrize('url', [
    'postgresql://runtime@db.example/test?sslmode=verify-full&sslrootcert=/certs/root.crt',
    'postgresql://runtime@/test?host=/cloudsql/heimdall-515408:asia-southeast1:test&sslmode=disable',
])
def test_secure_transport_configuration(monkeypatch, url):
    # Only configuration acceptance: no remote TLS/socket/IAM claim.
    import api.postgres
    seen = []
    monkeypatch.setattr(api.postgres, 'PostgresLedger', lambda value: seen.append(value))
    monkeypatch.setenv('HEIMDALL_MODE', 'production')
    monkeypatch.setenv('HEIMDALL_AUTH_MODE', 'cloud-run-iam')
    monkeypatch.setenv('INSTANCE_CONNECTION_NAME', 'heimdall-515408:asia-southeast1:test')
    monkeypatch.setenv('DATABASE_URL', url)
    create_app()
    assert seen == [url]


def test_postgres_integration(monkeypatch):
    # Explicit disposable database only; never read production DATABASE_URL.
    url = os.environ.get('HEIMDALL_TEST_POSTGRES_URL')
    if not url:
        pytest.skip('requires disposable migrated PostgreSQL database')
    import psycopg
    from api.postgres import PostgresLedger
    from api.approvals import Conflict
    with psycopg.connect(url) as db:
        db.execute('DROP SCHEMA IF EXISTS heimdall CASCADE')
        db.execute((BASE / 'postgres.sql').read_text())
        db.execute('DROP ROLE IF EXISTS heimdall_test_login')
        db.execute("CREATE ROLE heimdall_test_login LOGIN PASSWORD 'disposable-test-only' IN ROLE heimdall_runtime")
    from urllib.parse import urlsplit, urlunsplit
    parsed = urlsplit(url)
    runtime = urlunsplit(parsed._replace(netloc='heimdall_test_login:disposable-test-only@' + parsed.netloc.split('@')[-1]))
    with pytest.raises(ValueError, match='administrator'):
        PostgresLedger(url)
    for attribute in ('CREATEROLE', 'CREATEDB', 'BYPASSRLS', 'REPLICATION'):
        with psycopg.connect(url) as db:
            db.execute('ALTER ROLE heimdall_test_login ' + attribute)
        with pytest.raises(ValueError, match='administrator'):
            PostgresLedger(runtime)
        with psycopg.connect(url) as db:
            db.execute('ALTER ROLE heimdall_test_login NO' + attribute)
    with psycopg.connect(url) as db:
        db.execute('GRANT heimdall_owner TO heimdall_test_login')
    with pytest.raises(ValueError, match='administrator'):
        PostgresLedger(runtime)
    with psycopg.connect(url) as db:
        db.execute('REVOKE heimdall_owner FROM heimdall_test_login')
        # Simulate Cloud SQL's elevated role on this disposable local cluster.
        db.execute("DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='cloudsqlsuperuser') THEN CREATE ROLE cloudsqlsuperuser NOLOGIN; END IF; END $$")
        db.execute('GRANT cloudsqlsuperuser TO heimdall_test_login')
    with pytest.raises(ValueError, match='administrator'):
        PostgresLedger(runtime)
    with psycopg.connect(url) as db:
        db.execute('REVOKE cloudsqlsuperuser FROM heimdall_test_login')
    ledger = PostgresLedger(runtime)
    monkeypatch.setenv('DATABASE_URL', runtime)
    service = create_app().state.service
    # Migration is repeatable without erasing history.
    with psycopg.connect(url) as db:
        db.execute((BASE / 'postgres.sql').read_text())
    action = Action(idempotency_key='pg-hold', kind='email', sources=['lumen_public.json'],
                    recipient='unknown', text='Lumen list price is 8000.')
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: service.submit(action), range(16)))
    assert all(r['status'] == 'pending' for r in results)
    assert len(ledger.read()['events']) == 2
    assert ledger.read()['verification']['count'] == 2
    def decide(_):
        try:
            return service.decide(action.idempotency_key, Approval(decision='deny', owner_note='Reviewed'))
        except Conflict:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(r is not None for r in pool.map(decide, range(8))) == 1
    assert PostgresLedger(runtime).read()['verification']['valid']
    assert service.submit(action)['status'] == 'denied'
    changed = action.model_copy(update={'text': 'Changed'})
    with pytest.raises(Conflict):
        service.submit(changed)
    before = ledger.read()['verification']['head']
    with pytest.raises(RuntimeError):
        with ledger.transaction() as db:
            ledger.append(db, {'type': 'rollback'})
            raise RuntimeError('rollback')
    assert ledger.read()['verification']['head'] == before
    with pytest.raises(RuntimeError):
        with ledger.transaction() as db:
            db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)", ('rollback-item', '{}', '{}', '{}', 'pending'))
            raise RuntimeError('rollback state and trigger event')
    assert ledger.read()['verification']['head'] == before
    assert ledger.read()['verification']['valid']
    for sql in ('DELETE FROM heimdall.events', 'TRUNCATE heimdall.events',
                "UPDATE heimdall.events SET body='changed'", 'DELETE FROM heimdall.items',
                "UPDATE heimdall.items SET payload='changed'"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(runtime) as db:
                db.execute(sql)
    # Even direct runtime lifecycle writes are audited; invalid transitions fail.
    with pytest.raises(psycopg.Error):
        with psycopg.connect(runtime) as db:
            db.execute("UPDATE heimdall.items SET status='pending'")
    # State mismatch survives a valid event chain and must still fail closed.
    with psycopg.connect(url) as db:
        db.execute('ALTER TABLE heimdall.items DISABLE TRIGGER record_state')
        db.execute("UPDATE heimdall.items SET result='{}'")
    assert not ledger.read()['verification']['valid']
    with pytest.raises(ValueError, match='lifecycle'):
        service.submit(action)
    with psycopg.connect(url) as db:
        db.execute("UPDATE heimdall.items SET result=(SELECT (body::json->'row'->>'result') FROM heimdall.events WHERE body::json->>'type'='state' ORDER BY seq DESC LIMIT 1)")
    assert ledger.read()['verification']['valid']
    # Administrator bypass is possible, but unrecomputed mutation is detected.
    with psycopg.connect(url) as db:
        db.execute('ALTER TABLE heimdall.events DISABLE TRIGGER protect_events')
        db.execute("UPDATE heimdall.events SET body='{}' WHERE seq=1")
    assert not ledger.read()['verification']['valid']
    with pytest.raises(ValueError, match='integrity'):
        service.submit(action)
