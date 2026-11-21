import hashlib
import json
import sqlite3
from contextlib import contextmanager


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


class Ledger:
    def __init__(self, path):
        self.path = str(path)
        with self.transaction() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY, body TEXT NOT NULL,
                    previous TEXT NOT NULL, digest TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'append-only'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'append-only'); END;
                CREATE TABLE IF NOT EXISTS items (
                    key TEXT PRIMARY KEY, payload TEXT NOT NULL, policy TEXT NOT NULL,
                    result TEXT NOT NULL, status TEXT NOT NULL);
            ''')

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def append(self, db, event):
        last = db.execute('SELECT seq, digest FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        seq, previous = (last[0] + 1, last[1]) if last else (1, '0' * 64)
        body = canonical(event)
        digest = hashlib.sha256(f'{seq}:{previous}:{body}'.encode()).hexdigest()
        db.execute('INSERT INTO events VALUES (?, ?, ?, ?)', (seq, body, previous, digest))

    def verify(self, db):
        previous = '0' * 64
        rows = db.execute('SELECT seq, body, previous, digest FROM events ORDER BY seq').fetchall()
        for expected, (seq, body, prev, digest) in enumerate(rows, 1):
            calculated = hashlib.sha256(f'{seq}:{prev}:{body}'.encode()).hexdigest()
            if seq != expected or prev != previous or calculated != digest:
                return {'valid': False, 'count': len(rows), 'failure_seq': seq}
            previous = digest
        return {'valid': True, 'count': len(rows), 'head': previous}

    def require_valid(self, db):
        if not self.verify(db)['valid']:
            raise ValueError('audit chain integrity failure')

    def read(self):
        with self.transaction() as db:
            return {'verification': self.verify(db), 'events': [
                {'seq': r[0], 'event': json.loads(r[1]), 'previous': r[2], 'digest': r[3]}
                for r in db.execute('SELECT seq, body, previous, digest FROM events ORDER BY seq')]}
