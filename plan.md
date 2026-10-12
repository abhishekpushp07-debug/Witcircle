# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, using the **5 provided PDFs** as the authoritative base guide, with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, vaulting/catalog separation, explicit data ownership, durable async job boundaries for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrently active exam attempts** (not registered users).
  - This remains an **unverified architecture goal** until realistic **load + fault + restore** qualification and operator signoff is performed (PDF-05).
  - “No lagging” is defined via **measurable SLOs** (latency, error rate, durability, backlog age), not an unprovable “0 lag” claim.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt).
  - **Single downloadable PDF report** per attempt (results + matched solutions).
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored; late/unacknowledged drafts are disclosed.
  - **No key/solution leakage during an active attempt** (including via direct URL guessing).

- **Auth requirements (non-negotiable)**:
  - **Students**: phone-number only (no OTP, no password). This is a **convenience profile**, not verified phone ownership.
  - **Staff/Owner**: secured separately.
    - A staff credential was leaked in an earlier test artifact; **rotation + session revocation is required** (operator action).
    - **User directive update (latest):** “Mujhse kuch mat pucho… final product bna kr do… khud bdhte rho.”
      - We proceed autonomously for routine engineering decisions.
      - We will not repeatedly ask for confirmations.
      - **Exception (critical/irreversible):** before invalidating staff access (credential rotation/session revocation), we will still do **one** explicit execution window confirmation, because it is an irreversible access-impacting security operation.

- **Theme requirement (updated)**:
  - **Matte maroon** theme stays as-is (`#5C0025`), with light/dark tokens.

### Current top priority

Proceed **sequentially through all 10 packets** to reach a world-class product and a proven 5-lakh active-attempt target.

- **Packet 1 is IN PROGRESS** (foundation expanded significantly; exit blocked).
- We will **not stop** for routine confirmations.
- We will **not claim** “final product” or “5 lakh concurrent supported” until the qualification gates (Packet 10 / OPS-R) are met with real evidence.

### Capacity/claims stance (binding)

- We **do not claim** 5 lakh concurrency as “proven” without a measured load + fault + restore campaign (PDF-05).
- We **do** define a **qualification path**: staged load envelopes, explicit SLOs, and measurable gates.
- **Audit outputs remain authoritative** until fixed with verified regression evidence.

### Binding source facts from PDF-05 (must be baked into strategy and qualification)

These are **proposed acceptance targets** requiring measured evidence and operator signoff (PDF-05 p55–58):

- **Commit/save** (server ingress → durable acknowledgement): **p95 ≤ 300ms, p99 ≤ 1,000ms**
- **Submit receipt**: **p99 ≤ 2s**
- **Receipt → correct core grade readiness**: **p95 ≤ 60s, p99 ≤ 120s** (pending grade UI allowed)
- **Server errors**: **≤ 0.1%** overall and within **predeclared critical windows**
- **Integrity constraints**: **zero tolerance** in covered envelope (no wrong grading, no duplicate score effects, no lost acknowledged commits)

Load campaign stages are **exact and non-substitutable** (PDF-05 p58):

- 1,000 actors **15 min**
- 10,000 actors **30 min**
- 50,000 actors **45 min**
- 100,000 actors **60 min**
- 250,000 actors **90 min**
- 500,000 actors **180 min** steady-state soak (excluding warmup/admission)

Other binding workload math to incorporate (PDF-05 p56):

- Baseline live mix = **35k live RPS**, telemetry adds **16,666.7/s** (separate collector) → combined **51,666.7/s** before bursts.
- Start burst: **500k/120s = 4,166.7 starts/s**
- Submit burst: **500k/30s = 16,666.7 submits/s**
- Example grading demand: **500k × 75 / 120s = 312,500 item eval/s**
- Example content wave: **2MB × 500k = 1TB** over 120s ≈ **66.667 Gbps** before overhead.

The spec includes **13 sequential Work Packages (WP01–WP13)** and **12 production blocker gates (OPS-R01–OPS-R12)** (PDF-05 p65–68). We keep these as **nested ordered gates inside the 10 packets**.

---

## Execution updates and capacity stance

- Backend modularized into bounded contexts (`auth`, `catalog`, `content`, `attempts`, `answers`, `packs`, `reports`, `scoring`, `jobs`, `corrections`).
- Core extraction + 75-question workflow + scoring + PDF report generation exists.
- PDFs stored locally with SHA256 manifest:
  - `/app/docs/source_guides/manifest.json` + per-PDF `.txt` extraction.
- **Capacity goal** remains: architect for 500,000 concurrently active attempts from launch.
  - Current deployment is a **modular monolith** with **standalone MongoDB** (no replica set), so it is **not** aligned to PDF-05 “20 independent cells”.

### Latest approved changes and execution evidence (historical; audited)

- Student auth remains phone-only.
- Offline draft persistence exists.
- Report generation exists.
- UI uses matte maroon light/dark.
- QA fixture sets were withdrawn; original paper remains in review.

> Earlier “done” items are not treated as full compliance; the audit matrix is the current truth.

### Current work status

A. Player module fixture access bug blocking attempts — ✅ completed earlier

B. Verified offline recovery + submission + scoring end-to-end — ✅ completed earlier (scope-limited; not a full spec proof)

C. Matte maroon theme applied across app (`#5C0025`) — ✅ completed earlier

D. Withdraw QA fixtures / clean up audit harness side effects — ✅ completed earlier

E. Rigorous audit against the 5 PDFs — ✅ completed (audit-only)

- Key audit deliverables:
  - `/app/docs/audit/AUDIT_REPORT.md`
  - `/app/docs/audit/REQUIREMENTS_MATRIX.md` (62 scoped rows)
  - `/app/docs/audit/RULEBOOK_ERRATA.md`
  - `/app/docs/audit/REMEDIATION_PLAN.md`
  - `/app/docs/audit/EVIDENCE_LEDGER.md`
  - `/app/docs/audit/analytics_60_matrix.csv` + `.json`

F. 10-packet implementation strategy authored — ✅ completed (strategy-only)

- `/app/docs/strategy/TEN_PACKET_STRATEGY.md`
- `/app/docs/strategy/SLO_AND_WORKLOAD.md`
- `/app/docs/strategy/QUALIFICATION_AND_HANDOFF.md`

G. PDF export generator + snapshot handoff (doc-only; no app UI change) — ✅ completed

- Generator + snapshot files:
  - `/app/docs/strategy/export_strategy_pdf.py`
  - `/app/docs/strategy/CONTEXT_RESTORE_SNAPSHOT.md`
  - `/app/docs/strategy/PDF_EXPORT_README.md`

H. **Portable “10 packets” Strategy PDF export** — ✅ **COMPLETED**

- Delivered PDF:
  - Local: `/app/frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf`
  - URL: https://campus-launch-2.preview.emergentagent.com/downloads/Tejas_10_Packet_Strategy_v1.0.pdf
  - 60 pages; 296,394 bytes; SHA-256 `1868e35fe881051c9436ce530b2a236c253a501bb1f9af3bcc7aaf08dc6fd26f`
- Contents:
  - Full 3 strategy sources + context restore + audit/errata + 62 requirements + 60 analysis records + source hashes.
  - Navigation: 20 bookmarks + clickable TOC.
  - Embedded: 8 safe documentation attachments + sanitized manifest (no `source_url`, no secrets). Original 5 PDFs are *not embedded*.
- Verification scope and limitations:
  - Verified public HTTP 200 `application/pdf` and matching hash by testing-agent iterations 32/33.
  - These tests are **document checks only**. Do **not** treat as application correctness/capacity evidence or Packet 1 exit evidence.

I. **Packet 1 execution** — 🔧 **IN PROGRESS (FOUNDATION EXPANDED; EXIT STILL BLOCKED)**

Packet 1’s intent remains unchanged: **freeze correctness definitions + build enforceable safety rails + establish isolated evidence discipline**, without claiming scale readiness.

#### Packet 1 deliverables — progress snapshot

✅ **Delivered (implemented in repo)**

1) **Contracts/kernel + scale math (planning-only)**
- Versioned strict DTOs for command identity, receipts, exact rational marks, source anchors, and candidate-safe question projection:
  - `/app/backend/tejas/command_contracts.py`
  - Deterministic canonical bytes, scope digest vs intent digest
  - Nested command bodies made immutable (frozen dict/list) to prevent mutation after hashing
- Exact workload calculator using `Fraction` and a typed capacity profile model:
  - `/app/backend/tejas/capacity.py`
  - This returns **PLANNING_ONLY_UNQUALIFIED** (explicitly not load evidence)

2) **Fail-closed safety containment (Packet 1 hold; not a permanent fix)**
- HTTP-level pre-parse holds + direct-function holds for:
  - upload, source preview/parse, publication, extraction, regrade
- Worker/job dispatch respects holds and does not proceed when held
- Implemented as:
  - `/app/backend/tejas/safety.py`
  - plus targeted guards in `content.py`, `jobs.py`, `corrections.py`
- Hard rule: student practice hotpath unchanged; containment targets unsafe content operations

3) **Staff-only baseline readiness endpoints (no-store, typed, read-only)**
- `/api/internal/capacity/profile` → planning profile
- `/api/internal/safety/status` → current held capabilities + explicit UNQUALIFIED status
- Implemented in:
  - `/app/backend/tejas/engineering.py`
- Verified: anonymous access returns 401 (no accidental disclosure)

4) **Packet 1 baseline evidence tooling (versioned outputs)**
- Inventory builder generates:
  - Source index for **177 pages / 3299 blocks**
  - Requirements subset: **45 reviewed-subset obligations** + **60 analysis feature obligations** (A01–A60)
  - Gate inventory: **13 WP + 12 OPS-R = 25 gates**
  - Runtime OpenAPI + route catalogue with explicit contract metadata
  - Dependency baseline inventory
- Implemented in:
  - `/app/docs/packet1/build_baseline.py`
  - `/app/docs/packet1/*` outputs

5) **Rulebook correction applied**
- Rulebook guidance updated to reflect the errata: **all 60 analyses are mandatory** (no “40 minimum”).

6) **Isolated regression/evidence discipline (now verified, corrected, and made safe-by-default)**
- Packet 1 test harness is stable and truthful.
- **Safe pytest default** added to prevent accidentally running historical audit scripts:
  - `/app/pytest.ini` (defaults to `tests/packet1`)
- Latest accepted suite checkpoint (three fresh-process runs + safe-default run):
  - **149 total cases = 143 passed + 6 strict xfailed**; 0 unexpected failures; 0 errors
  - Logs under: `/app/docs/packet1/evidence/packet1-final-run*.log`
  - Accepted verification report:
    - `/app/test_reports/iteration_43_verified.json`
  - Unsigned hashed artifact manifest:
    - `/app/docs/packet1/evidence/continuation-artifact-manifest.json`
- Strict rule preserved: **no extra xfails** beyond A01–A06.

7) **Executable route contract registry + ingress hardening (expanded and verified)**
- All **49 mounted `/api` operations** now:
  - require explicit catalogue entry (fail-start if unlisted)
  - expose runtime-derived `x-owner-policy`, `x-role-scope`, `x-workload-tier`, `x-idempotency-mode`, `x-body-limit-bytes`
  - enforce strict request DTOs and per-operation budgets
  - fail-closed ingress checks:
    - missing media type still uses the same schema/body budget; incorrect media type → 415
    - duplicate keys/non-finite numbers/invalid unicode/too-deep JSON → 400
    - header ambiguity/length mismatch → 400
    - stream timeout → 408
    - query budget → 414
- ContentSafetyHold remains outside body parsing and continues to deny protected content operations.
- Implemented in:
  - `/app/backend/tejas/request_contracts.py`
  - `/app/backend/tejas/route_contracts.py`
  - `/app/backend/tejas/http_limits.py` (upgraded)
  - wired in `/app/backend/server.py`
- Baseline generator now **copies authoritative runtime metadata** instead of guessing.

8) **Frontend Studio write allowlists (verified by real JS + ASGI, plus mocked UI-only browser proof)**
- StudioEditor sends only allowlisted editable fields for:
  - questions
  - set settings
- Implemented in:
  - `/app/frontend/src/lib/studioContracts.js`
  - wired in `/app/frontend/src/features/StudioEditor.js`
- Verified:
  - Node executes real JS allowlist functions
  - ASGI Studio create/read/save/settings roundtrip passes
  - Browser-only verification uses API interception (MOCKED UI only; no real auth/write)

9) **Source review mechanical ledger + validator (now live with partial exact-span review)**
- Validator enforces:
  - exact codepoint-partition span coverage (gap-free, overlap-free)
  - source hash binding
  - evidence path + hash validation
  - parent-symlink traversal denial + secret/config denial
  - explicit separation: mechanical coverage ≠ semantic approval
- Implemented in:
  - `/app/docs/packet1/source_review.py`
  - `/app/docs/packet1/review_ledger.v1.json`
  - `/app/docs/packet1/SOURCE_REVIEW_CONTRACT.md`
- **Current truth (updated):**
  - Exact-span agent review completed for **PDF-05 pages 3 and 55** only:
    - **2 pages / 38 blocks / 65 bound obligations**
  - Remaining: **3261 blocks**
  - `semantic_completeness_proven=false` and `operator_approval_present=false`

10) **Staff credential generation fencing + operator-only rotation primitive (strengthened; still not executed live)**
- Generation-based staff session fencing:
  - sessions store `credential_generation`
  - auth validates session generation vs user generation for staff `current()` + `refresh()`
  - `new_session()` rechecks latest user generation before finalizing issuance
- Operator-only rotation primitive:
  - CAS update by expected generation
  - majority+journal acknowledgement, **server UTC** timestamp
  - deletes stale staff sessions (cleanup)
  - delayed old-session insert cannot regain access (generation fencing is authoritative)
- Implemented in:
  - `/app/backend/tejas/staff_credentials.py`
  - `/app/backend/tools/rotate_staff_credential.py`
  - runbook: `/app/docs/packet1/STAFF_ROTATION_RUNBOOK.md`
- CLI safety strengthened:
  - dry-run default
  - requires `--apply --confirm-revoke --confirm-fenced-deployment` plus protected TTY
  - does not accept secrets in argv
- **LIVE rotation is NOT executed** and the incident is NOT closed.

11) **Dependency scans + triage recorded (OPEN; not remediated yet)**
- Python scan (pip-audit):
  - scanned 143 dependency rows; 23 affected packages; 191 advisory records
  - 2 skipped packages: `emergentintegrations`, `litellm`
- Frontend scan (yarn audit):
  - 26 unique advisories: 10 high, 14 moderate, 2 low
- Stored evidence and triage:
  - `/app/docs/packet1/dependency_triage.v1.json`
  - scan artifacts under `/app/docs/packet1/evidence/`
- **Status:** OPEN; no auto-upgrades and no reachability/compatibility claims.

12) **Mobile toast overflow + resize clipping fixed (UI-safe)**
- Sonner/toast container was overflowing/clipping on mobile resize.
- Fixed by geometry constraints and disabling transitions for toaster container.
- No color/token/theme changes.

✅ **Deliberately BLOCKED (by design) in Packet 1**

- `coverage_manifest.json` still declares: **zero_orphan_proven=false** (indexing != atomic clause coverage)
- Packet 1 exit remains **BLOCKED** pending:
  - full atomic clause registry across all 5 PDFs
  - owner-approved contracts & failure scope
  - credential incident closure with actual authorized rotation/revocation evidence
  - remaining audit reproductions (S01/A04b/A05b/A07/A08 + frontend defects plan)
  - dependency advisory remediation/attestation readiness

✅ **Operational/current behavior changes (student-safe, but visible)**

- User-facing limitation: **source upload / staff source preview / publication / extraction / regrade** are held with **503** (pre-body-parse), including direct calls and dispatch. Normal student pilot attempt flow, grading and report lanes are not held.

### Open defects (no permanent fixes yet; remain release blockers for affected capabilities)

- Backend (P1 audit findings; still OPEN):
  - **A01** retry-resume idempotency gap (owned by Packet 06)
  - **A02** concurrent publish duplicates same version archive (Packet 05)
  - **A03** reviewer lost update (Packet 05)
  - **A04** invalid audience fails open (Packet 05)
  - **A05** queued jobs don’t self-drain when capacity frees (Packet 04)
  - **A06** worker/extraction can write after losing lease (Packet 04)
  - **S01** multipart/form resource budgets not enforced correctly (Packet 04)
  - Additional audit IDs (A04b, A05b, A07, A08) remain to be ported into Packet 1 red reproductions.
- Frontend:
  - **F03** typed MCQ option LaTeX renders raw (Packet 07)
  - **F02** logout clears drafts for other profiles without immediate discard warning (Packet 07)
  - **F01** malformed local state recovery is **NOT VERIFIED** (Packet 07)
- Security incident (P0): leaked staff credential in a historical test report artifact
  - **Rotation + session revocation is required by an authorized operator**
  - **NOT executed** yet
  - Still requires **one-time explicit execution window confirmation before invalidating staff access**

Services status (informational only; not a capacity claim): frontend/backend/mongodb are running in this environment.

---

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

User stories:

1. Owner uploads PDFs privately.
2. Reviewer binds questions and solutions exactly with source refs.
3. Student can attempt (MCQ + numerical).
4. Student gets accurate scoring.
5. Student can download complete matched-solution PDF.

Steps:

- POC-1: Private storage + secure serving — ✅ implemented; ✅ audited
- POC-2: Deterministic content extraction + pairing scaffold — ✅ implemented; ✅ audited
- POC-3: Attempt snapshot + scoring + deadline correctness — ✅ implemented; ✅ audited
- POC-4: Results view + PDF report generation — ✅ implemented; ✅ audited

Stop and fix until:

- (a) 1:1 pairing, (b) report PDF downloads, (c) no key leakage.

### Phase 2 — V1 App Development (build full product around proven core)

User stories:

1. Premium landing.
2. Browse sets.
3. Phone-only login.
4. Attempt loop.
5. Reviewer workflow.

(✅ implemented; audited as partial compliance.)

### Phase 3 — Comprehensive testing, hardening, and regression

- Backend Packet 1 suite is stable and now safe-by-default (`/app/pytest.ini` + `/app/tests/packet1`).
- Frontend browser-only allowlist verification exists and is explicitly MOCKED (no real auth/write).
- Security posture remains partial; production requirements (MFA, signing, cells) are not implemented.

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening (bounded tranche)

- Rulebook + capacity worksheet exist; Packet 1 includes executable workload math and typed planning DTOs.
- This does **not** provision live cells or validate throughput.

---

### Phase 5 — Strategy-First: **10-Packet Full-Spec Implementation Strategy**

Status: ✅ Strategy authored; ❌ packets 2–10 NOT STARTED; **Packet 1 IN PROGRESS**.

**Global invariants (must be preserved in all packets)**

- Matte maroon theme stays.
- Student login stays phone-only (no OTP/password). Do not silently turn phone into verified identity.
- Staff/owner security is strengthened separately.
- No “0 lag” claims; define and prove SLOs.
- No “500k proven” claims until qualification campaign passes.
- **Builder scope** = application code/design/docs/tests only.
- **Operator scope** = DB servers, cloud/IaC, CI/CD, SSL, deployments, WAF/CDN, KMS/HSM, backups/restore, identity provider.

**Dependencies are forward-only:** each packet may depend only on earlier packets.

Each packet will contain:

- Scope and out-of-scope
- Interfaces/contracts (API and data boundaries)
- Deliverables (code, infra, docs, tests)
- Dependencies (previous packets, operator actions)
- Acceptance tests + exit gates (latency/error/backlog/durability metrics)
- Ownership split: **application code vs operator-provisioned infrastructure**

#### Packet 1 — Rules, Safety & Regression Baseline (P01) — **IN PROGRESS (foundation expanded; exit blocked)**

**Purpose:** Freeze what “correct” means before major refactors; create enforceable safety rails and red regressions for later packets.

**Must deliver (Packet 1 scope only):**

- **Atomic requirement registry**: expand beyond the current 62-row audit matrix into atomic MUST/acceptance clauses from all five PDFs.
  - The current exact-span review is **partial**: only PDF-05 pp3 & 55 are partitioned/bound.
- **Contract-first API & permission catalogue**:
  - strict input/output DTOs, field allowlists, canonical body hashing, typed errors, idempotency scope,
  - ETags/If-Match semantics, status/Location/Retry-After, payload budgets, UTC/monotonic units.
  - **Now includes**: executable ingress contracts for all 49 mounted operations.
- **Data ownership map**:
  - vaulting/sourcing boundaries, content truth vs analytics projections, job/outbox boundaries.
- **Regression baseline & evidence discipline**:
  - real-function regressions for A01–A06 are implemented and correctly RED (strict xfail) until repaired by their owning packets.
  - isolated test data access; tests fail closed if pointed at production namespaces.
  - secret-safe outputs (no credentials in reports), dependency inventory baseline.
  - safe-by-default pytest scope.
- **Containment (not permanent fixes):**
  - fail-closed containment around unsafe upload/publication/job paths until owning packets repair them.
- **Credential incident handling (planning + safe execution path; not executed yet):**
  - persistently rotate hash in `tejas_users` + revoke entries in `tejas_sessions`
  - race-safe session issuance boundaries
  - operator-only tool and runbook
  - **Do not execute rotation/revocation without one-time explicit execution window confirmation**, because it invalidates access.
- **Dependency/advisory triage evidence**:
  - record vulnerabilities/skips honestly
  - do not claim clean scans

**What Packet 1 MUST NOT do:**

- Must not silently implement fixes owned by Packet 4/5/6/7.
- Must not provision infrastructure (DB clusters, queues, cells) or change production environment wiring.
- Must not claim 5-lakh readiness; must not weaken Packet 1 exit gates.

**Exit gate (unchanged; do not weaken):**

- Owner-approved contracts and failure scope
- Zero orphan mandatory clauses in the detailed registry
- All current findings have a red regression or explicitly unverified reproduction task
- Safe test isolation and credential containment evidence
- With explicit operator authorization and user confirmation: **actual persisted credential rotation + session revocation evidence**. Packet 1 remains BLOCKED until this evidence exists; a runbook or blocked label does not pass the gate.

**Fix ownership mapping (from audit):**

- Permanent fixes by packet (do not do early):
  - P04 owns A05/A06/S01
  - P05 owns A02/A03/A04
  - P06 owns A01
  - P07 owns F01/F02/F03

#### Packet 2 — Database & Live-Cell Foundation (P02)

- Purpose: establish data-platform decision needed for 20×25k cells and durable commitments.
- Exit gate: chosen + provisioned data platform for one canary cell + validated pools + documented durability policy.

#### Packet 3 — Identity, Permissions & Locked Trust (P03)

- Purpose: make staff/owner actions safe without changing student phone-only entry.
- Exit gate: protected publication requires MFA/step-up grant; grants payload-bound + single-use + auditable; student login unchanged.

#### Packet 4 — Durable Workers & Safe Processing Kernel (P04)

- Purpose: create real worker/queue plane and safe processing model.
- Includes fixes: A05, A06, S01.

#### Packet 5 — Content Sourcing & Publication (P05)

- Purpose: safe editorial workflow and immutable publication semantics.
- Includes fixes: A02, A03, A04.

#### Packet 6 — Exam Engines & Durable Sessions (P06)

- Purpose: explicit commit/seal/drain attempt protocol + official adapters.
- Includes fix: A01.

#### Packet 7 — Frontend & Offline Experience at Scale (P07)

- Purpose: correct UX under poor networks and scale constraints.
- Includes fixes: F01/F02/F03.

#### Packet 8 — All 60 Analyses & Study Plans (P08)

- Purpose: implement **A01–A60** with correct unavailable states.

#### Packet 9 — Results, Solutions & PDF Reports (P09)

- Purpose: snapshot-consistent results/solutions/report exports.

#### Packet 10 — Full-Scale Qualification & Operations (P10)

- Purpose: prove the 5-lakh target via the exact staged campaign and release gates.

---

## 3) Next Actions

### A) Portable Strategy PDF export — ✅ COMPLETED

- Delivery record: `/app/docs/strategy/PDF_EXPORT_README.md`
- PDF download: https://campus-launch-2.preview.emergentagent.com/downloads/Tejas_10_Packet_Strategy_v1.0.pdf

### B) Execute Packet 1 implementation — 🔧 IN PROGRESS

Immediate work order (autonomous; no repeated confirmation requests):

1. **Lock in Packet 1 evidence checkpoint** — ✅ DONE (updated)
   - Safe default: `/app/pytest.ini`
   - Stable suite: `/app/tests/packet1`
   - Accepted verification:
     - `/app/test_reports/iteration_43_verified.json`
     - `143 passed, 6 strict xfailed` repeated 3× plus safe-default run

2. **Per-operation contract catalogue (ingress discipline)** — ✅ DONE (expanded)
   - Executable route registry for all 49 operations (fail-start if unlisted)
   - Strict request DTOs + per-operation budgets
   - Baseline generator copies authoritative runtime metadata

3. **Atomic clause coverage workflow (still Packet 1, still BLOCKED)** — 🔧 IN PROGRESS
   - Exact-span ledger + validator in place:
     - `/app/docs/packet1/review_ledger.v1.json`
     - `/app/docs/packet1/source_review.py`
   - Partial exact-span review completed for PDF-05 pp3 and p55.
   - Next: expand exact-span binding beyond these two pages; keep semantic approval false until independent approvals exist.

4. **Port remaining audit reproductions (still Packet 1; do NOT fix them here)** — ⏭️ NEXT
   - Add strict red reproductions (or explicit “unverified” tasks) for:
     - S01 multipart/form parsing budgets (original failure reproduction remains pending; upload hold is not proof)
     - A04b / A05b / A07 / A08
     - Frontend defects F01/F02/F03: reproducible evidence plan, owned by Packet 7
   - Maintain registry:
     - `/app/docs/packet1/REGRESSION_STATUS.json`

5. **Credential incident closure tooling (Packet 1: tool + fencing; execution remains gated)** — ✅ Tooling delivered; ⏭️ closure pending
   - Tooling & fencing delivered:
     - `/app/backend/tejas/staff_credentials.py`
     - `/app/backend/tools/rotate_staff_credential.py`
     - `/app/docs/packet1/STAFF_ROTATION_RUNBOOK.md`
   - Next (gated): authorized operator executes rotation + session revocation; record evidence.

6. **Dependency/advisory triage (Packet 1 baseline; not remediation yet)** — ✅ Baseline evidence recorded; ⏭️ remediation strategy pending
   - Evidence:
     - `/app/docs/packet1/dependency_triage.v1.json`
   - No auto-upgrades; no reachability/compatibility claims.

7. **Frontend Studio allowlist visual smoke** — ✅ DONE (with explicit scope)
   - Node + ASGI roundtrip tests prove allowlists.
   - Browser-only proof is explicitly MOCKED UI (API intercepted; no real auth/write) and preserved as evidence.

### C) Continue sequentially through Packets 2–10

- Proceed **sequentially** once Packet 1 exit gate evidence is complete.
- Do not “skip ahead” to later packets without meeting dependencies.
- Do not claim production readiness until OPS-R gates and load/fault/restore evidence exist.

---

## 4) Success Criteria

### Portable PDF phase success — ✅ complete

- A single portable PDF exists and can be downloaded.
- PDF contains full 10-packet strategy + SLO/workload + qualification/handoff + audit/errata + R01–R62 + A01–A60 inventory + source hashes.
- PDF has clickable TOC/bookmarks and is readable/printable.
- PDF verified by independent testing agent for completeness and no secrets (document scope only).
- No code/env/DB/credential changes happened in this phase.

### Packet 1 success (current phase; must not be overclaimed)

- Packet 1 deliverables completed per `TEN_PACKET_STRATEGY.md`:
  - atomic requirement registry + coverage artifacts,
  - contract-first API/permission catalogue,
  - data ownership map,
  - red regressions + isolated evidence discipline,
  - safe containment (where allowed),
  - ingress contract enforcement and per-operation budgets.
- Student login remains phone-only; UI remains matte maroon.
- Credential incident handling:
  - rotation tool + runbook prepared;
  - execution only with one-time explicit user confirmation and operator authorization;
  - no credentials leak in artifacts.
- Dependency advisories recorded honestly; no clean scan claim.
- **Evidence is honest**:
  - green tests are truly green,
  - known audit defects remain red (strict expected failures) until repaired by their owning packets,
  - no “critical_bugs=[]” report language is treated as closure,
  - scope violations in earlier testing-agent work are recorded and superseded rather than hidden.

### Product success (post-strategy; future)

- Phone-only student entry preserved.
- Secure staff publishing and locked truth.
- Full official exam engines + 60 analyses.
- Measured and qualified concurrency envelope, not assumed.

## Explicit Release Blockers (remain blockers until qualified)

- 20×25k home-cell fleet and routing
- Multi-AZ durability + failover + restore proofs
- Transactional admission + writer fencing + explicit commit protocol
- Independent worker fleet and sandboxed parsing
- Staff MFA/step-up + signing/KMS + WORM/ObjectLock
- Authorization-aware CDN distribution
- Full 60-analytics pipeline
- Full load + chaos + restore qualification campaign
- Any OPEN audit P1 correctness defect (A01–A06, S01, F03)
- Any unperformed mandatory WP/OPS-R gate (PDF-05 p65–68)
- Any unresolved dependency advisory or skipped package without explicit tested disposition
