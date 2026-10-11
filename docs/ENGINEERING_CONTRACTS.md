# Tejas engineering contracts and capacity boundary

## Capacity requirement (user update)
Target: more than **500,000 simultaneously active students at launch**, not registered users. This preview is NOT provisioned, load-tested or certified for that load. Do not market it as proven. The original 100,000-registration objective is superseded as the planning target.

## Actual feature boundaries
| Domain | Module | Contract |
|---|---|---|
| Accounts / sessions | `backend/tejas/auth.py` | bcrypt, revocable HttpOnly Secure cookies, role allowlists; no reset/email integration |
| Discovery catalogue | `backend/tejas/catalog.py` | indexed bounded source-free projection; no question/solution bodies fetched for listing |
| Content operations | `backend/tejas/content.py` | draft -> approve each question -> owner publish; provenance/rights/audience/expiry; audit |
| Content packing | `backend/tejas/packs.py` | SHA256-addressed compressed immutable private manifests, deduplicated across attempts, bounded process cache; integrity check on load |
| Attempt ledger | `backend/tejas/attempts.py` | compact mutable responses, shared immutable pack, per-question CAS revisions, duplicate prevention, deadline at server, idempotent receipt |
| Evaluation | `backend/tejas_core.py` | deterministic explicit marking; never guesses keys; original order retained |
| Private document vault | `backend/tejas_storage.py` | private platform object storage, server credentials, application authorization before every download; immutable UUID source paths and hashes; no source sharing links |
| Report / extraction jobs | `backend/tejas/jobs.py` | durable job documents, atomic lease, deduplication, bounded pilot execution, failure/retry states and scheduled recovery |
| API contracts | `backend/tejas/contracts.py` | `{data,error,meta:{api_version,request_id}}` for JSON; authorized binary endpoints remain binary; `/api/openapi.json` catalogues actual endpoints |
| Web feature packages | `frontend/src/features/*` | lazy route chunks; shared auth/client/rendering; no keys in active-player bundle or API payload |

'Vault' here means private content storage plus application authorization and environment-only secrets. An external KMS/HSM/managed secret-manager service is NOT configured. This distinction is intentional. Object storage lacks permanent erasure; withdrawal is not physical deletion.

## Locking after validation
No source file is made uneditable. Stable contracts are locked by regression tests and content hashes, not `chmod` or an unchangeable codebase. Content pack documents use insert-only values with SHA256 verification. Reviewed publications are versioned; old attempt snapshots do not drift. A module is release-accepted only after its relevant regression tests pass; every subsequent change requires those tests again.

## Workload math (planning assumptions, not benchmarks)
500,000 concurrent students saving once per 20 seconds => 25,000 acknowledged writes/second. A two-minute submission wave => about 4,167 submissions/second. A synchronized five-second start wave => 100,000 starts/second. Content/asset bandwidth is a separate critical constraint. Real user behavior and burst factors must replace these assumptions in the load model.

## Production gates still required
1. Choose region(s), budget, availability/recovery objectives and data-retention policy. Provision independent autoscaled API pools and isolated content/PDF workers. Current pilot runs two bounded heavy jobs per API process; that is NOT a 500k worker fleet.
2. Load-balanced stateless API fleet, per-domain pool budgets, edge WAF/rate limits, database sharding/replication designed around user/attempt keys, durable queue service plus backpressure and autoscaled report workers. Present Mongo indexes and leases are foundations, not provisioned capacity.
3. Private asset delivery through an authorization-aware CDN (no public keys/solutions); cache only immutable assets with strict release checks. Current private proxy keeps correctness but is not a 500k bandwidth solution.
4. Managed secrets/KMS rotation, encrypted-at-rest guarantees verified with provider, automated backups and restore drills, observability SLOs, privacy/security assessment. Do not infer platform properties that have not been measured or configured.
5. Execute ramp, synchronized-start burst, sustained answer traffic, submission storm, report backlog, regional failure and reconnect tests. Suggested acceptance objectives must be agreed before claiming capacity. Prove no acknowledged response lost, no late response scored, and no private record crossing accounts.
6. Pilot + progressive admission before any broad public launch. Rights and all75 academic/accessibility reviews remain independent publication gates.

## Current scheduling
Platform-managed `.emergent/crons.yml` every15min recovers interrupted processing and finalizes expired attempts. Save rejection uses the server deadline immediately and does not wait for cron. Webhook authenticates by constant-time secret comparison, records duplicate deliveries, and acknowledges before processing. Very large fleets need independently sized processing capacity; no hidden in-app scheduler is installed.

## No fabricated assurances
No invented percentile/rank, dashboard metrics or learner counts. No claim of microservice deployment, 500k load testing, dedicated message broker, managed secret vault, certified accessibility, legal compliance or permanent erasure unless separately implemented and verified.
