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
  - **Staff/Owner**: secured separately. A staff credential was leaked in an earlier test artifact; **rotation + session revocation is required** (operator action).
    - **User directive update:** do not repeatedly ask for confirmation during routine work.
    - **Exception (critical/irreversible):** before invalidating staff access (credential rotation/session revocation), ask once with a clear execution window.

- **Theme requirement (updated)**:
  - **Matte maroon** theme stays as-is (`#5C0025`), with light/dark tokens.

### Current top priority

**Execute Packet 1 (IN PROGRESS)** of the approved 10-packet strategy **now that the portable strategy PDF has been delivered**.

- User directive: “Ab kaam start… best do… baar baar mat pucho.”
- Operating mode: proceed autonomously for normal implementation decisions; only interrupt for truly critical/irreversible actions.

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

I. **Packet 1 execution** — 🔧 **IN PROGRESS (FOUNDATION DELIVERED; EXIT STILL BLOCKED)**

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
  - Runtime OpenAPI + route catalogue with explicit LEGACY gaps
  - Dependency baseline inventory
- Implemented in:
  - `/app/docs/packet1/build_baseline.py`
  - `/app/docs/packet1/*` outputs:
    - `coverage_manifest.json` (explicit `zero_orphan_proven=false`)
    - `COVERAGE_MATRIX.md`
    - `requirements.v1.json`
    - `release_gates.v1.json`
    - `source_block_inventory.v1.json`
    - `operation_catalogue.v1.json`
    - `openapi.current.v1.json`
    - `dependency_baseline.json`

5) **Rulebook correction applied**
- Rulebook guidance updated to reflect the errata: **all 60 analyses are mandatory** (no “40 minimum”).

6) **Isolated regression/evidence discipline (now verified)**
- Packet 1 test harness is now stable and truthful:
  - exact UUID DB namespace guard (including Motor Database constructor)
  - single session loop (Motor event-loop binding stabilized)
  - real cookie sessions via auth codepaths (no “pretend staff”) and outbound HTTP blocked
  - cleanup never swallowed; drop only own DB once
  - indexing once per run; `delete_many` only within own namespace
- Independent final verification:
  - `/app/test_reports/iteration_37.json`:
    - **77 tests**, run **3 fresh processes**, each: **71 passed, 6 strict xfailed, 0 fail, 0 error**
    - xfails are **OPEN invariants** (A01–A06) and remain release blockers
  - Hashed (unsigned) evidence bundle:
    - `/app/docs/packet1/evidence/artifact_manifest.json`
    - + preserved `/tmp/packet1_run*.log` copied into evidence folder

✅ **Deliberately BLOCKED (by design) in Packet 1**

- `coverage_manifest.json` still declares: **zero_orphan_proven=false** (indexing != atomic clause coverage)
- Packet 1 exit remains **BLOCKED** pending:
  - full atomic clause registry across all 5 PDFs (0 pages certified fully atomized)
  - owner-approved contracts & failure scope
  - credential incident closure with actual authorized rotation/revocation evidence; recording BLOCKED is not an alternative passing exit condition

✅ **Operational/current behavior changes (student-safe, but visible)**

- User-facing limitation: **source upload / staff source preview / publication / extraction / regrade** are held with **503** (pre-body-parse), including direct calls and dispatch. Normal student pilot attempt flow, grading and report lanes are not held.

### Open defects (no fixes yet; remain release blockers for affected capabilities)

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
  - Still requires **one-time explicit user confirmation before invalidating staff access**

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

- Backend test suite is now stable for Packet 1 evidence discipline (`/app/tests/packet1`).
- Frontend E2E exists; audit identifies remaining UX/correctness defects.
- Security posture remains partial; production requirements (MFA, signing, cells) are not implemented.

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening (bounded tranche)

- Rulebook + capacity worksheet exist; Packet 1 now includes executable workload math and typed planning DTOs.
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

#### Packet 1 — Rules, Safety & Regression Baseline (P01) — **IN PROGRESS (foundation done; exit blocked)**

**Purpose:** Freeze what “correct” means before major refactors; create enforceable safety rails and red regressions for later packets.

**Must deliver (Packet 1 scope only):**

- **Atomic requirement registry**: expand beyond the current 62-row audit matrix into atomic MUST/acceptance clauses from all five PDFs.
- **Contract-first API & permission catalogue**:
  - strict input/output DTOs, field allowlists, canonical body hashing, typed errors, idempotency scope,
  - ETags/If-Match semantics, status/Location/Retry-After, payload budgets, UTC/monotonic units.
- **Data ownership map**:
  - vaulting/sourcing boundaries, content truth vs analytics projections, job/outbox boundaries.
- **Regression baseline & evidence discipline**:
  - real-function regressions for A01–A06 are now implemented and correctly RED (strict xfail) until repaired by their owning packets.
  - isolated test data access; tests fail closed if pointed at production namespaces.
  - secret-safe outputs (no credentials in reports), dependency inventory baseline.
- **Containment (not permanent fixes):**
  - fail-closed containment around unsafe upload/publication/job paths until owning packets repair them.
- **Credential incident handling (planning + safe execution path):**
  - investigate where the leaked staff credential lives and how to rotate it safely.
  - produce an operator-run rotation + session revocation runbook.
  - **Do not execute rotation/revocation without one-time explicit user confirmation**, because it invalidates access.

**What Packet 1 MUST NOT do:**

- Must not silently implement fixes owned by Packet 4/5/6/7.
- Must not provision infrastructure (DB clusters, queues, cells) or change production environment wiring.
- Must not claim 5-lakh readiness; must not weaken Packet 1 exit gates.

**Exit gate (unchanged; do not weaken):**

- Owner-approved contracts and failure scope
- Zero orphan mandatory clauses in the detailed registry
- All current findings have a red regression or explicitly unverified reproduction task
- Safe test isolation and credential containment evidence
- With explicit operator authorization and user confirmation: actual persisted credential rotation + session revocation evidence. Packet 1 remains BLOCKED until this evidence exists; a runbook or blocked label does not pass the gate.

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

1. **Lock in Packet 1 evidence checkpoint** — ✅ DONE
   - Verified stable suite: `/app/test_reports/iteration_37.json` (3 fresh-process runs)
   - Preserved hashed (unsigned) evidence: `/app/docs/packet1/evidence/artifact_manifest.json`
   - Note: per-run DB UUID names are intentionally not exported; harness enforces them internally.

2. **Expand atomic clause coverage workflow (still Packet 1, still BLOCKED)**
   - Promote `source_block_inventory.v1.json` into a reviewed atomic registry queue.
   - Track review status per PDF page/block → per atomic MUST clause.
   - No claims until `zero_orphan_proven=true` is justified and approved.

3. **Finish the per-operation contract catalogue (still Packet 1)**
   - For every `/api` operation: ownership, roles, lane, idempotency, body budgets, typed errors.
   - Identify which legacy routes need replacement vs compatibility shims.
   - Decide retention/deletion policies and add decision register entries (remain BLOCKED until approved).

4. **Port remaining audit reproductions (still Packet 1; do NOT fix them here)**
   - Add red reproductions (or explicit “unverified” tasks) for:
     - S01 multipart/form parsing budgets
     - A04b / A05b / A07 / A08
     - Frontend defects F01/F02/F03: at least reproducible evidence plan, owned by Packet 7

5. **Credential incident runbook (planning only; execution remains gated)**
   - Document exact persisted rotation steps:
     - rotate hash in `tejas_users` + revoke entries in `tejas_sessions`
     - ensure race-safe session issuance boundaries
   - Prepare one-time confirmation prompt and execution window plan.

6. **Dependency/advisory triage (Packet 1 baseline, not full release SBOM)**
   - Current environment includes test-support deps (pytest/pytest-asyncio/Markdown from earlier doc-check tooling).
   - Create an explicit separation plan:
     - keep test-only deps out of production images
     - add signed SBOM + advisory status in Packet 10

### C) Packets 2–10

Proceed sequentially only after Packet 1 exit gate evidence is complete.

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
  - safe containment (where allowed).
- Student login remains phone-only; UI remains matte maroon.
- Credential incident handling:
  - rotation plan + runbook prepared;
  - execution only with one-time explicit user confirmation and operator authorization;
  - no credentials leak in artifacts.
- **Evidence is honest**:
  - green tests are truly green,
  - known audit defects remain red (strict expected failures) until repaired by their owning packets,
  - no “100%/critical_bugs=[]” report language is treated as closure.

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
