# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, using the **5 provided PDFs** as the authoritative base guide, with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, vaulting/catalog separation, proper API boundaries, durable async job queue for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrently active students**.
  - This remains an **unverified architecture goal** until realistic **load + fault + restore** qualification and operator signoff is performed (PDF-05).
  - “No lagging” is defined via **measurable SLOs** (latency, error rate, durability, backlog age), not an unprovable “0 lag” claim.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt).
  - **Single downloadable PDF report** per attempt (results + matched solutions).
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored; late/unacknowledged drafts are disclosed.
  - **No key/solution leakage during an active attempt** (including via direct URL guessing).
- **Auth requirements (non-negotiable)**:
  - **Students**: phone-number only (no OTP, no password). This is a **convenience profile**, not verified phone ownership.
  - **Staff/Owner**: secured separately. A staff credential was leaked in an earlier test artifact; **rotation + session revocation is required** (operator action). Rotation must be confirmed by the user **before invalidating any staff access**.
- **Theme requirement (updated)**:
  - **Matte maroon** theme stays as-is (`#5C0025`), with light/dark tokens.

### Current top priority

**Execute Packet 1** of the approved 10-packet strategy (rules, safety, regression baselines) **now that the portable strategy PDF has been delivered**.

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
- **Capacity goal** remains: architect for 500,000+ concurrent from launch.
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

G. PDF-export styling guidance captured separately (doc-only; no app UI change) — ✅ completed

- PDF export generator + snapshot handoff exists:
  - `/app/docs/strategy/export_strategy_pdf.py`
  - `/app/docs/strategy/CONTEXT_RESTORE_SNAPSHOT.md`
  - `/app/docs/strategy/PDF_EXPORT_README.md`

H. **Portable “10 packets” Strategy PDF export** — ✅ **COMPLETED**

- Delivered PDF:
  - Local: `/app/frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf`
  - URL: https://campus-launch-2.preview.emergentagent.com/downloads/Tejas_10_Packet_Strategy_v1.0.pdf
  - 60 pages; 296,394 bytes; SHA-256 `1868e35fe881051c9436ce530b2a236c253a501bb1f9af3bcc7aaf08dc6fd26f`
- Contents (portable reference only; not a release certificate):
  - Full 3 strategy sources + context restore + audit/errata + 62 requirements + 60 analysis records + source hashes.
  - Navigation: 20 bookmarks + clickable TOC.
  - Embedded: 8 safe documentation attachments + sanitized manifest (no `source_url`, no secrets). Original 5 PDFs are *not embedded*.
- Verification scope and limitations:
  - Verified public HTTP 200 `application/pdf` and matching hash by testing-agent iterations 32/33; main inspected representative renders.
  - These tests are **document checks only**. Do **not** inherit fuzzy helpers/percentages as application correctness/capacity evidence or Packet 1 acceptance. No backend/frontend src/env/dependency/database/credential changes occurred for the PDF phase.

### Open defects (no fixes yet; remain release blockers for affected capabilities)

- Backend (P1):
  - A01 retry-resume idempotency gap
  - A02 concurrent publish duplicates same version archive
  - A03 reviewer lost update
  - A04 invalid audience fails open
  - A05 queued jobs don’t self-drain when capacity frees
  - A06 worker/extraction can write after losing lease (missing destination fence)
  - S01 multipart/form resource budgets not enforced correctly
- Frontend:
  - F03 typed MCQ option LaTeX renders raw (P1)
  - F02 logout clears drafts for other profiles without immediate discard warning (P2)
  - F01 malformed local state recovery is **NOT VERIFIED** (requires correct browser regression)
- Security incident (P0): leaked staff credential in a historical test report artifact
  - **Rotation + session revocation is required by an authorized operator**
  - Must be done **only after separate user confirmation** (do not silently invalidate staff access)

### Known inventory gap (do not invent)

`TEN_PACKET_STRATEGY.md` references `coverage_manifest.json` and `COVERAGE_MATRIX.md`, but they are **not present** in the docs inventory. Status: **UNVERIFIED/ABSENT** until created explicitly. Packet 1 must resolve this by producing the required coverage/traceability artifacts.

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

- Backend tests exist, but audit found scope/quality issues in earlier reports; corrected reproductions are tracked.
- Frontend E2E exists; audit identifies remaining UX/correctness defects.
- Security posture is partial; production requirements (MFA, signing, cells) are not implemented.

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening (bounded tranche)

- Rulebook + capacity worksheet exist, but audit issued errata and still-open correctness defects.

---

### Phase 5 — Strategy-First: **10-Packet Full-Spec Implementation Strategy**

Status: ✅ Strategy authored; ❌ **Implementation NOT STARTED**.

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

#### Packet 1 — Rules, Safety & Regression Baseline (P01)

- **User-approved to implement** — ✅ Approved; ❌ **NOT STARTED**.
- Purpose: freeze what “correct” means and establish safety rails.
- Includes:
  - Rulebook consolidation, precedence rules, and errata (including **all 60 analyses** requirement).
  - Measurable SLO definitions (commit/submit/grade/error thresholds from PDF-05 p55).
  - Test strategy baseline: no fix is closed without an independent testing-agent report.
  - Security containment tasks that must happen before real work (operator-owned): rotate leaked staff credential + revoke sessions (**requires separate user confirmation** before invalidation).
  - Define evidence artifacts and versioning (run manifests, workload calculators, golden datasets).
  - Resolve missing strategy-referenced artifacts: `coverage_manifest.json` and `COVERAGE_MATRIX.md` (do not invent; build correctly).
- Exit gate (do not weaken):
  - Owner-approved contracts and failure scope
  - Zero orphan mandatory clauses in the detailed registry
  - All current findings have a red regression or explicitly unverified reproduction task
  - Safe test isolation and credential containment evidence, including (with explicit operator authorization) **actual persisted credential rotation** + relevant session revocation evidence.

**Fix ownership mapping (from audit):**

- Permanent fix owners by packet (no work executed yet):
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
- Exit gate: autonomous draining; destination fencing; multipart budgets enforced.

#### Packet 5 — Content Sourcing & Publication (P05)

- Purpose: safe editorial workflow and immutable publication semantics.
- Includes fixes: A02, A03, A04.

#### Packet 6 — Exam Engines & Durable Sessions (P06)

- Purpose: explicit commit/seal/drain attempt protocol + official adapters.
- Includes fix: A01.

#### Packet 7 — Frontend & Offline Experience at Scale (P07)

- Purpose: correct UX under poor networks and scale constraints.
- Includes fixes: F03, F02, and verified handling for F01.

#### Packet 8 — All 60 Analyses & Study Plans (P08)

- Purpose: implement **A01–A60** with correct unavailable states.

#### Packet 9 — Results, Solutions & PDF Reports (P09)

- Purpose: snapshot-consistent results/solutions/report exports.

#### Packet 10 — Full-Scale Qualification & Operations (P10)

- Purpose: prove the 5-lakh target via the exact staged campaign and release gates.

---

## 3) Next Actions

### A) Portable Strategy PDF export — ✅ COMPLETED

- Artifact delivery recorded in:
  - `/app/docs/strategy/PDF_EXPORT_README.md`
- Do not treat its verification reports as application readiness evidence.

### B) Now start: Execute Packet 1 implementation (P0)

- Resume by re-reading:
  - `/app/docs/strategy/TEN_PACKET_STRATEGY.md`
  - `/app/docs/audit/AUDIT_REPORT.md`
  - `/app/docs/RULEBOOK_ARCHITECTURE_V5.md`
  - `/app/docs/strategy/QUALIFICATION_AND_HANDOFF.md` (decision register + gates)
- Implement **Packet 1 only** (rules/registries/contracts/regression baselines/documentation corrections/security containment evidence).
- Keep student auth phone-only; keep matte maroon UI.
- For staff credential rotation/session revocation: **investigate + propose exact rotation steps**, then request user confirmation **before** invalidating access.

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

### Packet 1 success (next phase)

- Packet 1 deliverables completed per `TEN_PACKET_STRATEGY.md` (rules/registries/contracts/regression baselines) with no false closure of issues owned by later packets.
- Student login remains phone-only; UI remains matte maroon.
- Credential incident handled safely with explicit user confirmation and authorized operator execution; no credentials in outputs.

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
