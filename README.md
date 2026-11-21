# Heimdall

### The Agent That Watches Your Agents

**A governance layer for the solo founder who has AI workers, but no team to check their work.**

Heimdall is designed to sit between a founder's agents and the outside world: check what they read and propose, catch sensitive-data leaks, unsupported figures and policy breaches, then explain each decision in plain language. The goal is **governance legibility**, not another technical monitoring dashboard.

The PRD's target user is the non-technical owner of **Lumen Studio**, a one-person Singapore design studio delegating Sales, Finance, Marketing, Ops and Support to QwenWork agents. Every owner note should answer: *What did the agent try? What happened? Why, with rule and file evidence? What can I do next?*

Built for the **QwenWork x Hashmeta AI One-Person Company Hackathon**, AvePoint Challenge Track: AI Governance, Security & Decision-Making. The supplied PRD sets a **23 Nov 2026** submission deadline. This repository is a **local simulation**, not a deployed enforcement gateway or a completed submission package.

## Projects

| Directory | Current role |
| --- | --- |
| [heimdall](heimdall/README.md) | Python 3.12 FastAPI API, deterministic policies, synthetic Lumen fixtures, SQLite lifecycle and hash-chain ledger, approvals, and plain log-derived briefings. |
| [heimdall-site](heimdall-site/) | React 19 / TypeScript / Vite showcase: home, docs, and a five-scenario guided demo. No backend connection. |
| [heimdall-owner](heimdall-owner/) | React 19 / TypeScript / Vite console connected to the local API: overview, activity search/tier filters, pending approvals, raw audit events, verification, and briefing. |

Both frontends offer English, Bahasa Melayu, and Chinese UI. There is no root package or combined launcher; install and run each project independently. Generated builds, backups, and visual-check folders are not application source.

## Status

| Capability | Implemented here | PRD goal / remaining gap |
| --- | --- | --- |
| Classification | Four synthetic Lumen JSON fixtures; highest trusted label or explicit marking wins. | Official-kit public / internal / client-confidential / regulated classification, regex hints and model fallback. API calls client-confidential `confidential`. |
| Policy, scope and facts | Deterministic local R01-R19 interpretations, floor enforcement, declared-scope checks and bounded contextual R18 matching. | Official policy/evidence validation, semantic ambiguity handling and trusted scope/destination verification. |
| Single channel | FastAPI proposal review and an advisory agent prompt. | Every QwenWork worker tool call routed through a non-bypassable gateway, including reads. No actual gateway hooks exist here. |
| Owner review | Connected console and persisted single-use HOLD approval/denial. | Authenticated morning queue with at-most-one notification per item. Notifications are simulated today. |
| Audit and briefing | SQLite append-only event triggers, SHA-256 chain and plain log-derived notes. | Supabase log/queue, model-written briefing and 60-second QwenWork video. |
| Deployment | Local React frontends, Dockerfile and nested test workflow. | Cloud Run, Upstash Redis, Supabase, model services, active root CI/CD and Hashmeta AI CMS deployment. Not demonstrated here. |
| Evaluation | Synthetic backend and frontend tests. | Official scenarios/labels and measured latency, tokens and cost. No official 15/15, 95% over 28 files, performance, hosting-cost or compliance result is claimed. |

## Policy And Boundaries

The PRD maps **ALLOW** to proceed, **APPROVE** to **HOLD_FOR_APPROVAL**, and **NEVER** to **BLOCK**. The API uses `ALLOW`, `HOLD`, `BLOCK`; execution remains simulated. **BLOCK > HOLD > ALLOW**, retaining all matching evidence. The owner cannot approve a BLOCK, including a Greenstep quote below the SGD 6,500 floor.

The PRD's S5 combines an unconfirmed reprint order (R12: HOLD) with unnecessary regulated reads (R02: BLOCK), yet lists an overall HOLD. Evaluate reads and order separately: regulated out-of-scope reads must be blocked; if combined into one proposal, BLOCK wins. Local R02 conservatively covers any regulated out-of-scope action. This is not an official S5 benchmark result.

- The API accepts read, email, quote, terms, invoice, order, upload, delete, and news proposals. R18 checks eligible text within proposals, not a separate `state_fact` endpoint.
- ALLOW records `simulated`, HOLD records `pending`, and BLOCK records `blocked`. A pending HOLD accepts one approval or denial. Approval re-evaluates current sources against the original policy snapshot; BLOCK cannot be overridden. Identical payload/key submissions return persisted state; changed payloads with the same key return 409.
- The owner console reads actual local ledger data and persists decisions through the API. It does not create proposals. Data loads on entry or manual refresh, not via live subscriptions. Decisions require a connected, verified ledger, pending HOLD state, and a nonblank owner note.
- The showcase uses predefined scenarios and in-memory events, not API decisions or a cryptographic ledger. REWRITE / REDACT are illustrative assistance, not policy tiers. Its contact form validates locally and sends nothing. Language preference is stored in browser local storage.
- All execution and owner notifications are simulated. Nothing sends email, pays invoices, deletes records, uploads files, or intercepts real QwenWork tools. The [agent prompt](heimdall/qwenwork/agent_prompts/local_review.txt) is advisory only.
- Source classification uses trusted fixture labels and explicit markings, not comprehensive semantic detection. R18 uses bounded contextual matching, not a model or general fact checker. Recipient, retention, and scope declarations are not independently verified.
- The unauthenticated API must stay local. SQLite triggers and a hash chain provide local tamper evidence, not tamper-proof storage or authenticated owner identity. Administrators can replace files or recompute a chain. No production enforcement, hosted deployment, official document-kit accuracy, or measured production performance is claimed.

See the [backend README](heimdall/README.md) for trust limitations, [local rules](heimdall/rules/README.md) for provenance, [policy implementation](heimdall/api/tiers/rules.py) for matching logic, and [configuration](heimdall/policies/default.yaml) for local thresholds. The supplied PRD defines intended behavior; the official starter-kit files are not present in this implementation.

## Intended Architecture

```text
QwenWork workers: Sales / Finance / Marketing / Ops / Support
  -> Heimdall gateway on Cloud Run
     -> classification + task scope + deterministic R01-R19 + fact checks
     -> strictest decision + rule/file evidence
     -> Upstash content-hash cache; Supabase audit log and approval queue
  -> plain-language daily briefing + 60-second QwenWork video
  -> owner dashboard and Hashmeta AI CMS landing site
```

This is the **planned architecture**, not today's runtime. The PRD proposes a small Qwen model for ambiguous classification and briefing, Qwen-Max for rare fact disputes, and deterministic checks first. Caching and short extracts are design strategies, not measured savings. Real email, payments and other side effects remain out of scope for the hackathon demo; non-bypassable proposal review still needs integration work.

## Roadmap And Submission

1. Import and validate the unchanged official kit, reconcile policy/scenario expectations, and benchmark decisions, rule citations and evidence. Treat 15/15 and classifier accuracy of at least 95% over 28 files as targets, not results; add the PRD's S6 patient-data forwarding case.
2. Connect five QwenWork workers and scripted rogue runs to the gateway, including read checks. Preserve non-overridable floors and strictest precedence; verify routing rather than relying on prompts.
3. Add tiered models, caching, durable cloud log/queue and one-notification behavior. Measure the PRD targets of under 1.5 seconds added latency, under 800 average tokens per check and approximately S$0/month demo hosting before claiming them.
4. Deliver the submission package: live QwenWork application, generated 60-second briefing video, three-minute demo video, and Hashmeta AI CMS landing site. These are delivery goals, not verified deployed/generated artifacts.
5. Before public operation, add authentication, signed expiring approvals, RLS, rate limits, controlled tool credentials and monitoring. PDPA-oriented handling is design intent, not compliance certification; multi-tenancy, SSO and custom model training are outside the PRD scope.

## Local Setup

Use Python 3.12 and Node.js 24 with npm (Node 24 was used for verification). Site tests import TypeScript directly through Node's native support; older Node versions may not run them. Both frontends have committed npm lockfiles.

### Backend

Run from `heimdall/`:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/uvicorn api.main:create_app --factory --host 127.0.0.1 --port 8766
```

Open API docs at <http://127.0.0.1:8766/docs>. This guide uses 8766 to match the owner proxy; the backend-only README uses 8000. The default database is `heimdall/heimdall.sqlite3`; set `HEIMDALL_DB` on the server process to select another file. Sources default to `heimdall/data/`, and policy to `heimdall/policies/default.yaml`. The factory also accepts `db_path`, `data_root`, and `policy_path` programmatically.

### Showcase

Run from `heimdall-site/`:

```sh
npm ci
npm test
npm run typecheck
npm run build
npm exec vite -- --host 127.0.0.1 --port 4175 --strictPort
```

Open <http://127.0.0.1:4175/>. Hash routes include `#/`, `#/demo`, and `#/docs`. There is no `dev` script, so invoke Vite directly. The build runs `tsc -b && vite build`, writes `dist/`, and uses relative asset paths (`base: './'`). No API is needed.

### Owner Console

Keep the backend running, then run from `heimdall-owner/`:

```sh
npm ci
npm test
npm run build
npm run dev
```

Open <http://127.0.0.1:4176/>. The dev script binds loopback on port 4176 with strict port checking. The build runs `tsc --noEmit && vite build` and writes `build-owner-20261120-connected/`; the config does not empty that directory before building.

## API Integration

The owner defaults to `VITE_API_BASE=/api`. During Vite development, `/api` is proxied to `HEIMDALL_API_ORIGIN` (default `http://127.0.0.1:8766`), removing the `/api` prefix. To use the backend README's port instead, run from `heimdall-owner/`:

```sh
HEIMDALL_API_ORIGIN=http://127.0.0.1:8000 npm run dev
```

`VITE_API_BASE` changes the browser request base and is embedded at build time. The Vite proxy is development-only: serving the built owner files requires a same-origin reverse proxy for `/api`, or another deliberately configured API route. The backend does not configure CORS. Do not expose this unauthenticated simulation publicly.

| Endpoint | Purpose |
| --- | --- |
| `POST /actions` | Submit a validated proposal; return tier, evidence, provenance, claim corrections, and lifecycle state. |
| `POST /approvals/{key}` | Approve or deny a pending HOLD using `decision` and `owner_note`. |
| `GET /ledger` | Read events, digests, and verification. |
| `GET /ledger/verify` | Read hash-chain verification. |
| `GET /briefing` | Read plain-text notes derived from the ledger. |
| `GET /health` | Read `local-simulation` status and policy version. |

To populate an empty owner console, submit a synthetic HOLD to the running API, then refresh the console and review it under Approvals:

```sh
curl http://127.0.0.1:8766/actions \
  -H 'Content-Type: application/json' \
  -d '{"idempotency_key":"review-1","kind":"email","sources":["lumen_public.json"],"recipient":"unknown","text":"Lumen list price is 8000."}'
```

Source paths are relative to the trusted data root; absolute paths, traversal, and escaping symlinks are rejected. Use a new idempotency key for a different proposal. Approval changes local simulated state only.

## Verification And Operations

Backend pytest tests cover synthetic policy boundaries, contextual claims, source path protections, approvals, idempotency, concurrent writes, and ledger tampering. Site Node tests cover demo transitions, form validation, and configured translations; owner Node tests cover ledger projection, decision eligibility, and filtering. These are not production or full browser end-to-end tests.

A [Dockerfile](heimdall/Dockerfile) is provided but is not deployment evidence; it binds `0.0.0.0` inside the container and stores its database under `/state`. Restrict host port publishing to loopback and provide persistence deliberately. The backend [workflow](heimdall/.github/workflows/tests.yml) is nested under the project rather than root `.github/workflows/`, so it is not an active root GitHub Actions workflow as laid out here.
