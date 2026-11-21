# Heimdall API Simulation

Deterministic Python 3.12 FastAPI/Pydantic/YAML local simulation. No dashboard, cloud deployment, video, hosted service, model service, or actual send/pay/delete/upload implementation. All executions and R17 notifications are simulated. The official starter kit is preserved byte-for-byte in `kit/`; its policy is loaded by default through a deterministic adapter. Private Cloud Run preparation and a PostgreSQL audit adapter are included; neither is deployed. No real-world action enforcement is claimed.

## Run

Non-secret environment template: `.env.example` (not automatically loaded).

From this directory:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/uvicorn api.main:create_app --factory --host 127.0.0.1 --port 8000
```

Default SQLite file: `heimdall.sqlite3`; override with `HEIMDALL_DB`. OpenAPI at `http://127.0.0.1:8000/docs`. Bind loopback only for this unauthenticated MVP. Dockerfile is provided, not deployed or runtime-verified. CI assumes this directory is `heimdall` beneath the repository root; adjust working-directory if using it as a standalone repository.

## Private Cloud Run Preparation

Target: project `heimdall-515408`, region `asia-southeast1`. Nothing has been deployed.

1. The selected database target is **Google Cloud SQL for PostgreSQL**, replacing the PRD's Supabase proposal. Instance ID, database name, runtime login, secret/version and service account remain unresolved. Select an instance in `heimdall-515408` / `asia-southeast1`; do not treat `[INSTANCE_ID]` as an existing resource. Apply `postgres.sql` with a migration administrator that can create roles/schema and `SET ROLE heimdall_owner`. Cloud SQL administrators are not PostgreSQL superusers: the migration explicitly grants its executing identity membership in `heimdall_owner` before `SET ROLE`; the identity must have permission to grant that membership. This permission is migration-only. The repeatable migration does not import SQLite history; preserve/export it before switching.
2. `heimdall_owner` and `heimdall_runtime` are NOLOGIN owner/permission groups. Provision a separate LOGIN with only `heimdall_runtime` membership, no owner or `cloudsqlsuperuser` membership, superuser, BYPASSRLS, CREATEDB, CREATEROLE, replication or unrelated inherited privileges. Cloud SQL built-in users can receive `cloudsqlsuperuser` by default; explicitly remove it and audit inherited permissions. Never use the default `postgres` login at runtime. Verify the runtime can read events and insert/update permitted lifecycle fields but cannot modify/delete/truncate events or own objects.
3. Use Cloud Run's attached Unix socket `/cloudsql/heimdall-515408:asia-southeast1:[INSTANCE_ID]` with psycopg. Set `INSTANCE_CONNECTION_NAME` to that exact connection name and store the complete PostgreSQL URI (including percent-encoded password) in Secret Manager: `postgresql://[RUNTIME_LOGIN]:[ENCODED_PASSWORD]@/[DATABASE_NAME]?host=/cloudsql/heimdall-515408:asia-southeast1:[INSTANCE_ID]&sslmode=disable`. libpq adds the socket filename. `disable` applies only to the local Unix hop: the attached Cloud SQL Auth Proxy authenticates via IAM and validates/encrypts transport to Cloud SQL. The API rejects other socket paths, project/region mismatches, hostaddr overrides, alternate ports and insecure TCP. Direct TCP still requires `sslmode=verify-full` and a trusted root CA via `sslrootcert`; it is not the selected deployment path. Configuration tests do not prove that a socket is actually Auth Proxy-managed; verify attachment and runtime filesystem permissions.
4. Enable Cloud SQL Admin and Secret Manager APIs separately. Use a dedicated runtime service account with `roles/cloudsql.client` in the instance project and `roles/secretmanager.secretAccessor` only on the database secret. IAM transport authorization is distinct from the restricted password-authenticated database login. The simplest attached-socket path requires the instance public IP; it uses encrypted proxy transport, not public database grants/authorized networks. Private-IP-only networking would need a separately reviewed VPC/connector design. Select second-generation Cloud Run and verify instance CA mode compatibility. Build this directory's Dockerfile with a trusted builder and immutable image digest; it retains `kit/`, runs nonroot and respects `PORT`. Start at concurrency 8 / max instances 2 and capacity-test within Cloud SQL limits; each transaction opens one connection and the audit lock serializes writes. Prepared statements are disabled and settings/locks are transaction-local.

The following is an operator template, NOT executed. Replace every bracketed value and provision the instance, restricted login, migration, secret and image separately before deployment. Pin a numeric secret version; its URI contains the database password. Startup refuses SQLite in Cloud Run (`K_SERVICE`), missing configuration, unsafe transport and database administrators.

```sh
gcloud run deploy heimdall --project=heimdall-515408 --region=asia-southeast1 \
  --image='[IMMUTABLE_IMAGE_DIGEST]' --service-account='[RUNTIME_SERVICE_ACCOUNT_EMAIL]' \
  --no-allow-unauthenticated --ingress=all --concurrency=8 --max-instances=2 \
  --execution-environment=gen2 \
  --add-cloudsql-instances='heimdall-515408:asia-southeast1:[INSTANCE_ID]' \
  --set-env-vars='HEIMDALL_MODE=production,HEIMDALL_AUTH_MODE=cloud-run-iam,INSTANCE_CONNECTION_NAME=heimdall-515408:asia-southeast1:[INSTANCE_ID]' \
  --set-secrets='DATABASE_URL=[DATABASE_SECRET]:[PINNED_NUMERIC_VERSION]'
gcloud run services add-iam-policy-binding heimdall \
  --project=heimdall-515408 --region=asia-southeast1 \
  --member='serviceAccount:[AUTHORIZED_CALLER_EMAIL]' --role=roles/run.invoker
```

`ingress=all` allows externally hosted agents to reach the IAM-protected endpoint; it is not public authorization. Verify the resulting service has its Invoker IAM check enabled and no `allUsers` or `allAuthenticatedUsers` binding, including inherited bindings. `--no-allow-unauthenticated` alone is not proof of the resulting policy on an existing service.

Cloud Run, not this FastAPI process, validates Google identity tokens and enforces transport IAM on every route. Local TestClient tests cannot prove IAM behavior. The production mode flag is a deployment contract, not an in-process token validator: never host it behind public bypass ingress. Agents use short-lived Google ID tokens with audience equal to the Cloud Run service URL; use workload identity federation for external agents, not browser-held keys. Every invoker currently has all API permissions, including approvals: grant invocation only to trusted callers authorized to approve, or separate approval authorization before admitting untrusted agents. Owner notes are caller declarations, not independently authenticated end-user attribution.

The public Hashmeta dashboard cannot call this private gateway directly. It needs a server-side proxy that authenticates dashboard users, authorizes owner operations, and obtains Google ID tokens with a dedicated invoker identity. No proxy was built because its hosting and identity provider are undecided. Never place DATABASE_URL, service-account keys, Google tokens or proxy shared secrets in frontend bundles. No QW Page publishing is involved.

PostgreSQL persists every action/approval and trigger-generated lifecycle snapshot in one transaction, with a global advisory lock for idempotency and single-use approvals. Events deny runtime UPDATE/DELETE/TRUNCATE and are appended through a restricted SECURITY DEFINER function with a pinned search path and full chain validation. Item updates automatically append state events; immutable payload/policy and terminal transition guards apply. API writes verify both the hash chain and latest state snapshots. `/ledger` includes state records and sequence numbers for a complete verifiable history; briefing omits internal snapshots. Invalid attempts/conflicts are not accepted lifecycle events and do not append records.

This is tamper evidence, not administrator-proof storage: a database administrator can disable protections or rewrite/recompute the full chain or truncate its tail. Configure and recovery-test Cloud SQL backups/PITR and separately protected periodic head/count exports for retention and external anchoring; neither has been configured here. Audits contain source/policy/result content and owner notes; restrict read access and determine retention before real data use. Full-chain verification is linear per transaction and needs capacity testing before high throughput.

Disposable integration test (destructive schema reset, never target an existing Cloud SQL or other production database): set `HEIMDALL_TEST_POSTGRES_URL` to an isolated administrator PostgreSQL URI and run `.venv/bin/python -m pytest -q`. It creates a restricted login and tests concurrent submissions/approvals, restart persistence, rollback, denied privileges and administrator tamper detection. Without that explicit test URI the integration test is skipped. CI provisions a disposable PostgreSQL 17 service so this test runs rather than skips. Local PostgreSQL does not establish Cloud SQL proxy/TLS connectivity or Cloud Run IAM. Before deployment acceptance, verify the attached socket, proxy certificate validation, runtime IAM/database permissions, migration permissions, anonymous and wrong-audience rejection, authorized invocation, persistence across revisions, concurrent replicas, secret rotation, backup recovery and image startup.

Setup references verified against current Google documentation: [Cloud SQL PostgreSQL from Cloud Run](https://cloud.google.com/sql/docs/postgres/connect-run), [Cloud Run secrets](https://cloud.google.com/run/docs/configuring/services/secrets), [Cloud Run service identity tokens](https://cloud.google.com/run/docs/authenticating/service-to-service). No cloud command in this guide was executed.

## API

- `POST /actions`: validated action; returns tier, every matching rule's evidence, source provenance, claim corrections, and lifecycle status.
- `POST /approvals/{key}`: `{"decision":"approve","owner_note":"Reviewed"}` or denial. Only pending HOLD items accept one decision. Re-evaluates original policy snapshot against current sources; BLOCK cannot be overridden.
- `GET /ledger`: events, hashes, and verification result.
- `GET /ledger/verify`: hash-chain verification.
- `GET /briefing`: plain log-derived owner notes, not generated/model commentary.
- `GET /health`: simulation status and policy version.

Example:

```sh
curl http://127.0.0.1:8000/actions -H 'Content-Type: application/json' -d '{"idempotency_key":"review-1","kind":"email","sources":["lumen_public.json"],"recipient":"unknown","text":"Lumen list price is 8000."}'
curl http://127.0.0.1:8000/approvals/review-1 -H 'Content-Type: application/json' -d '{"decision":"approve","owner_note":"Synthetic recipient reviewed"}'
```

An identical payload/key returns persisted current state without execution or another event; a changed payload conflicts (409). Terminal actions/approvals cannot be repeated. Missing item is 404; invalid request fields are 422; invalid source/integrity is 400.

## Policy

Strictest wins: BLOCK > HOLD > ALLOW, preserving all evidence. Outside declared scope regulated actions BLOCK (R02); reads otherwise ALLOW (R01). Other outside-scope actions conservatively HOLD. Declared task scope is caller metadata, not a security assurance.

Known public/internal emails ALLOW; confidential/regulated or unknown recipients HOLD. List quotes ALLOW; below-list quotes HOLD; Greenstep below 6500 BLOCK, exactly 6500 does not trigger the floor. Above-list quotes conservatively HOLD. Changed terms HOLD. Matching invoice amounts strictly below 1000 ALLOW; missing, mismatched, or >=1000 HOLD. Orders without trusted written confirmation HOLD.

Public external uploads ALLOW. Internal nonretaining external uploads HOLD; internal retaining external uploads BLOCK, an explicitly conservative R14 interpretation. Confidential/regulated external uploads BLOCK. Local uploads are simulations only. Deletes HOLD except trusted contract-directed erroneous regulated records, which ALLOW with a simulated owner notification. Other BLOCK evidence still wins. Unannounced news BLOCK.

R18 conservatively checks sentences containing digits or the commitment keywords `will`, `guarantee`, `commit`, `promise` against complete contextual facts in trusted sources. Case/whitespace and terminal punctuation are normalized. A number occurring elsewhere is never sufficient. Unsupported contextual claims BLOCK and return supplied source facts as corrections, not invented facts. This is deliberately bounded matching: paraphrases may falsely block; spelled-out numbers, implicit dates, indirect commitments, and arbitrary natural-language contradictions are not comprehensively detected. No general semantic accuracy claim is made.

## Data And Trust

Four fictional Lumen JSON fixtures cover public, internal, confidential, regulated; facts, invoice/order/announcement metadata, and the deletion exception are synthetic. Highest source label or explicit `[PUBLIC]`, `[INTERNAL]`, `[CONFIDENTIAL]`, `[REGULATED]` marking wins. Agent-provided tiers are rejected. Relative paths must resolve to files within the trusted data root; absolute/traversal paths and escaping symlinks are rejected. Trusted source files must be administrator-controlled. Provenance hashes canonical parsed source content plus its relative path, not raw bytes. Content classification is labels/markings, not semantic detection of all regulated information. Recipient/retention/scope claims are caller declarations; there is no directory or actual destination verification.

SQLite events prohibit UPDATE/DELETE with triggers and hash-chain sequence/body/previous digest. BEGIN IMMEDIATE serializes item decisions, idempotency, and append operations transactionally. Verification detects chain mutation; writes fail closed on a broken chain. This is local tamper evidence, not tamper-proof storage: a database/file administrator can remove triggers, replace/recompute the entire chain, or modify lifecycle tables. No external signed anchor, authenticated owner identity, retention guarantees, or filesystem race-hardening exists. Source resolution is not a defense against an administrator replacing files during reads. Protect the data and database locally; do not expose the API publicly.

`qwenwork/agent_prompts/local_review.txt` is advisory only and cannot intercept actual QwenWork calls. There is no tool adapter or enforcement hook. Approval records do not authorize real-world tool execution.

## Layout

```text
api/main.py models.py audit.py approvals.py briefing.py
api/tiers/rules.py classifier.py claims.py sensitivity.py
policies/default.yaml
data/lumen_{public,internal,confidential,regulated}.json
rules/README.md
qwenwork/agent_prompts/local_review.txt
tests/seeded_attacks.json test_tiers.py test_classifier_vs_ground_truth.py
Dockerfile requirements.txt .github/workflows/tests.yml
```

Run `.venv/bin/python official_checks.py` to replay the official proposals through the API and save `official-check-results.json`. Initial unadapted result: 0/15 and 0/27 (Markdown/CSV unsupported). Final: 15/15 and 27/27 labeled files, no mismatches. The kit contains 28 data files but only 27 ground-truth entries; `00_README.md` has neither a sensitivity header nor an expected label, so no 28/28 claim is made. S5 scores the held outbound order separately from three R02 BLOCK read events; a blocked read cannot be approved. Evidence scores require runtime excerpts/provenance, with relevance inspected manually. S3 oversight-only cash-flow context is not outbound content. S2 remains an email, with price-commitment rules; S4 uses actual contract, invoice and dispute sources. Source labels/CSV schema are legitimate inputs; ground truth is evaluator-only. Markdown facts use conservative contextual matching, not general semantic understanding. API source root defaults to the legacy fixtures for compatibility; use `create_app(data_root=BASE / 'kit/data')` for official sources. Default policy is the preserved official JSON with adapter thresholds. Docker includes the kit, but has not been built or deployed.

Tests include official replay and deterministic synthetic assertions. Coverage includes R01-R19, price/invoice boundaries, all-evidence strictest wins, contextual false matches, source traversal/symlinks, persisted approvals, denial, source-change re-evaluation, single-use decisions, payload binding, concurrent writes, and trigger/hash tampering.
