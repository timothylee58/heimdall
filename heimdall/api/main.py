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
    mode = os.environ.get('HEIMDALL_MODE', 'local')
    auth = os.environ.get('HEIMDALL_AUTH_MODE', 'local')
    if mode not in ('local', 'production') or auth not in ('local', 'cloud-run-iam'):
        raise ValueError('unsupported deployment mode')
    if auth == 'cloud-run-iam' and mode != 'production':
        raise ValueError('cloud-run-iam requires production mode')
    if os.environ.get('K_SERVICE') or mode == 'production':
        if mode != 'production' or auth != 'cloud-run-iam' or db_path is not None:
            raise ValueError('production requires private Cloud Run IAM and PostgreSQL')
        if not os.environ.get('DATABASE_URL'):
            raise ValueError('production requires DATABASE_URL')
    policy = yaml.safe_load(Path(policy_path or BASE / 'kit/rules/policy.json').read_text())
    if 'owner_floors' in policy:
        if len(policy.get('rules', [])) != 19:
            raise ValueError('incomplete official policy')
        policy = {**policy, 'greenstep_floor': policy['owner_floors']['Greenstep Tuition'], 'invoice_threshold': 1000}
    if not isinstance(policy, dict) or not isinstance(policy.get('version'), str) or policy.get('greenstep_floor') != 6500 or policy.get('invoice_threshold') != 1000:
        raise ValueError('unsupported local MVP policy')
    url = os.environ.get('DATABASE_URL') if db_path is None else None
    if url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme not in ('postgres', 'postgresql'):
            raise ValueError('DATABASE_URL must use PostgreSQL')
        if mode == 'production':
            import re
            from psycopg.conninfo import conninfo_to_dict
            params = conninfo_to_dict(url)
            host = params.get('host', '')
            if host.startswith('/'):
                expected = os.environ.get('INSTANCE_CONNECTION_NAME', '')
                if (not re.fullmatch(r'heimdall-515408:asia-southeast1:[a-z][a-z0-9-]*', expected)
                        or host != '/cloudsql/' + expected
                        or len(host + '/.s.PGSQL.5432') >= 108
                        or params.get('hostaddr') or params.get('port', '5432') != '5432'
                        or params.get('sslmode') != 'disable'):
                    raise ValueError('production requires the exact attached Cloud SQL Unix socket')
                # The attached Auth Proxy validates/encrypts the remote connection;
                # libpq TLS is disabled only for this local Unix socket hop.
            elif (not host or ',' in host or params.get('hostaddr')
                    or params.get('sslmode') != 'verify-full'):
                raise ValueError('production PostgreSQL requires sslmode=verify-full')
            if params.get('service') or any(os.environ.get(key) for key in ('PGSERVICE', 'PGHOSTADDR', 'PGHOST', 'PGPORT')):
                raise ValueError('production PostgreSQL must not use connection routing overrides')
        from .postgres import PostgresLedger
        ledger = PostgresLedger(url)
    else:
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
