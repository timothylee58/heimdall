import json
from .audit import canonical
from .models import Action
from .tiers.classifier import assess


class Conflict(ValueError):
    pass


class Service:
    def __init__(self, ledger, root, policy):
        self.ledger, self.root, self.policy = ledger, root, policy

    def submit(self, action):
        payload = canonical(action.model_dump())
        with self.ledger.transaction() as db:
            self.ledger.require_valid(db)
            old = db.execute('SELECT payload, result FROM items WHERE key=?', (action.idempotency_key,)).fetchone()
            if old:
                if old[0] != payload:
                    raise Conflict('idempotency key bound to another payload')
                return json.loads(old[1])
            policy = canonical(self.policy)
            result = assess(action, self.root, json.loads(policy))
            result.update({'key': action.idempotency_key, 'status': {'ALLOW': 'simulated', 'HOLD': 'pending', 'BLOCK': 'blocked'}[result['tier']],
                           'execution': 'simulated only; no external side effects'})
            if any(e['rule'] == 'R17' for e in result['evidence']) and result['tier'] == 'ALLOW':
                result['notification'] = 'simulated owner notification: contract-directed erroneous regulated deletion'
            db.execute('INSERT INTO items VALUES (?, ?, ?, ?, ?)', (action.idempotency_key, payload, policy, canonical(result), result['status']))
            self.ledger.append(db, {'type': 'action', 'payload': action.model_dump(), 'policy': json.loads(policy), 'result': result})
            return result

    def decide(self, key, decision):
        with self.ledger.transaction() as db:
            self.ledger.require_valid(db)
            row = db.execute('SELECT payload, policy, result, status FROM items WHERE key=?', (key,)).fetchone()
            if not row:
                raise KeyError(key)
            if row[3] != 'pending':
                raise Conflict('only pending HOLD items accept a single decision')
            action = Action.model_validate_json(row[0])
            result = assess(action, self.root, json.loads(row[1]))
            status = 'denied' if decision.decision == 'deny' else ('blocked' if result['tier'] == 'BLOCK' else 'approved_simulated')
            result.update({'key': key, 'status': status, 'owner_note': decision.owner_note,
                           'execution': 'simulated only; no external side effects'})
            db.execute('UPDATE items SET result=?, status=? WHERE key=?', (canonical(result), status, key))
            self.ledger.append(db, {'type': 'approval', 'key': key, 'decision': decision.model_dump(), 'result': result})
            return result
