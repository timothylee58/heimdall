"""PostgreSQL adapter; schema installation is an out-of-band migration."""
from contextlib import contextmanager
import json
import psycopg
from .audit import Ledger, canonical


class Connection:
    def __init__(self, db):
        self.db = db

    def execute(self, sql, params=()):
        return self.db.execute(sql.replace('?', '%s'), params)


class PostgresLedger(Ledger):
    def __init__(self, url):
        self.url = url
        with self.transaction() as db:
            unsafe = db.execute("""SELECT rolsuper OR rolbypassrls OR rolcreaterole OR rolcreatedb OR rolreplication
                OR pg_has_role(current_user, 'heimdall_owner', 'MEMBER')
                OR EXISTS (SELECT FROM pg_roles elevated WHERE elevated.rolname = 'cloudsqlsuperuser'
                    AND pg_has_role(current_user, elevated.oid, 'MEMBER'))
                FROM pg_roles WHERE rolname=current_user""").fetchone()[0]
            if unsafe:
                raise ValueError('PostgreSQL runtime must not be an administrator or schema owner')
            self.require_valid(db)

    @contextmanager
    def transaction(self):
        with psycopg.connect(self.url, connect_timeout=10, prepare_threshold=None) as connection:
            connection.execute('SET LOCAL search_path TO pg_catalog, heimdall')
            connection.execute("SET LOCAL statement_timeout = '60s'")
            connection.execute("SET LOCAL lock_timeout = '30s'")
            # All workers lock before reading state, including idempotency checks.
            connection.execute('SELECT pg_advisory_xact_lock(515408, 1)')
            yield Connection(connection)

    def append(self, db, event):
        db.execute('SELECT heimdall.append_event(?)', (canonical(event),))

    def require_valid(self, db):
        super().require_valid(db)
        rows = db.execute('SELECT key, payload, policy, result, status FROM items').fetchall()
        states = {}
        for (body,) in db.execute('SELECT body FROM events ORDER BY seq').fetchall():
            event = json.loads(body)
            if event.get('type') == 'state':
                states[event['row']['key']] = event['row']
        actual = {r[0]: dict(zip(('key', 'payload', 'policy', 'result', 'status'), r)) for r in rows}
        if actual != states:
            raise ValueError('audit lifecycle integrity failure')

    def read(self):
        with self.transaction() as db:
            verification = self.verify(db)
            if verification['valid']:
                try:
                    self.require_valid(db)
                except ValueError:
                    verification['valid'] = False
                    verification['failure'] = 'lifecycle state mismatch'
            events = []
            for seq, body, previous, digest in db.execute('SELECT seq, body, previous, digest FROM events ORDER BY seq'):
                try:
                    event = json.loads(body)
                except json.JSONDecodeError:
                    event = {'type': 'corrupt', 'body': body}
                events.append({'seq': seq, 'event': event, 'previous': previous, 'digest': digest})
            return {'verification': verification, 'events': events}
