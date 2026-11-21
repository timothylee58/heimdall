import os
from pathlib import Path
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from .models import Action, Approval
from .audit import Ledger
from .approvals import Service, Conflict
from .briefing import briefing

BASE = Path(__file__).resolve().parent.parent


def create_app(db_path=None, data_root=None, policy_path=None):
    policy = yaml.safe_load(Path(policy_path or BASE / 'kit/rules/policy.json').read_text())
    if 'owner_floors' in policy:
        if len(policy.get('rules', [])) != 19:
            raise ValueError('incomplete official policy')
        policy = {**policy, 'greenstep_floor': policy['owner_floors']['Greenstep Tuition'], 'invoice_threshold': 1000}
    if not isinstance(policy, dict) or not isinstance(policy.get('version'), str) or policy.get('greenstep_floor') != 6500 or policy.get('invoice_threshold') != 1000:
        raise ValueError('unsupported local MVP policy')
    ledger = Ledger(db_path or os.environ.get('HEIMDALL_DB', str(BASE / 'heimdall.sqlite3')))
    service = Service(ledger, Path(data_root or BASE / 'data'), policy)
    app = FastAPI(title='Heimdall Synthetic Local API', version='0.1.0')
    app.state.service = service
    app.state.ledger = ledger

    @app.exception_handler(Conflict)
    async def conflict_handler(request, error):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409, content={'detail': str(error)})

    @app.exception_handler(ValueError)
    async def value_handler(request, error):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={'detail': str(error)})

    @app.post('/actions')
    def submit(action: Action):
        try:
            return service.submit(action)
        except (OSError, yaml.YAMLError) as error:
            raise HTTPException(400, 'invalid source') from error

    @app.post('/approvals/{key}')
    def decide(key: str, decision: Approval):
        try:
            return service.decide(key, decision)
        except KeyError as error:
            raise HTTPException(404, 'item not found') from error
        except OSError as error:
            raise HTTPException(400, 'invalid source') from error

    @app.get('/ledger')
    def read_ledger():
        return ledger.read()

    @app.get('/ledger/verify')
    def verify():
        return ledger.read()['verification']

    @app.get('/briefing', response_class=PlainTextResponse)
    def owner_briefing():
        return briefing(ledger)

    @app.get('/health')
    def health():
        return {'status': 'local-simulation', 'policy': policy['version']}

    return app


# Uvicorn factory avoids database side effects on module import.
