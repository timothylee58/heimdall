# Heimdall Local API MVP

Deterministic Python 3.12 FastAPI/Pydantic/YAML local simulation. No dashboard, cloud deployment, video, hosted service, model service, or actual send/pay/delete/upload implementation. All executions and R17 notifications are simulated. The official starter kit is preserved byte-for-byte in `kit/`; its policy is loaded by default through a deterministic adapter. No production enforcement is claimed.

## Run

From this directory:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/uvicorn api.main:create_app --factory --host 127.0.0.1 --port 8000
```

Default SQLite file: `heimdall.sqlite3`; override with `HEIMDALL_DB`. OpenAPI at `http://127.0.0.1:8000/docs`. Bind loopback only for this unauthenticated MVP. Dockerfile is provided, not deployed or runtime-verified. CI assumes this directory is `heimdall` beneath the repository root; adjust working-directory if using it as a standalone repository.

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
