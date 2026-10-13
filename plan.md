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

### Binding communication preference (critical)

- **Do not ask the user for interim review** before “final product”.
- **No routine confirmations/menus** asking the user to pick next features.
- Progress updates may be informational, but **not approval checkpoints**.
- Only **critical, irreversible, access-impacting actions** (e.g., staff credential rotation + session revocation) may require a single explicit execution-window authorization.

### LATEST user priority (product-first execution) — CURRENT STATUS: COMPLETED (bounded product feature phase)

Stop repeated confirmation/checkpoint interruptions and deliver a **simple unified owner workflow**:

1) **One place** (Studio) to upload:
   - **Questions PDF + Solutions PDF**, OR
   - **Excel (.xlsx)** import for typed questions/options/answer/solution (to avoid image-only PDFs), including:
     - single workbook (Questions + Solutions), or
     - two workbooks / two sheets with deterministic pairing.
2) System **auto-organises** into a test draft with strict, auditable pairing (no guessing).
3) Only after organisation is complete, prompt owner **only for attempt start date/time** (IST).
4) Provide **manual Live / Unlive toggle** (gated by Ready state; and by schedule if set).
5) Deliver **world-class analysis**, **competitions**, and leaderboards—**evidence-based** with correct “unavailable/processing” states.

**Implemented and verified in this phase** (does *not* imply whole-spec completion):

- Unified PDF + XLSX importer in Studio, templates + strict row errors.
- Sandbox isolation retained (**chroot + low UID + seccomp + resource caps**); PDF codec preload fix applied (**no isolation weakening**).
- Immutable imported test publication.
- “Schedule start date/time only” UI + server gating.
- Live/Unlive toggle.
- Competitions hub + per-competition leaderboard.
- Competition embargo: **scores/solutions/reports/retries locked until test window ends** (early submissions included).
- Descriptive “missed-topic priorities” (evidence-based) added to results.

Implementation must proceed autonomously with sensible defaults—no routine questions—while preserving safety/precision/privacy invariants from the 5 PDFs.

- Unknown/uncertain pairings must **block Ready/Live** with explicit issues; we do **not** fabricate academic truth.
- Existing practice loop (attempt, scoring, PDF report) must remain functional.
- Existing holds on upload/extraction/publication/regrade cannot be removed until their owning defects are repaired.

---

### Auth requirements (non-negotiable)

- **Students**: phone-number only (no OTP, no password). This is a **convenience profile**, not verified phone ownership.
- **Staff/Owner**: secured separately.
  - A staff credential was leaked in an earlier test artifact; **rotation + session revocation is required** (operator action).
  - User directive: proceed autonomously; avoid repeated confirmations.
  - **Exception (critical/irreversible):** before invalidating staff access (credential rotation/session revocation), we will still do **one** explicit execution window authorization.

### Theme requirement

- **Matte maroon** theme stays as-is (`#5C0025`), with light/dark tokens.

### Current top priority — UPDATED

Proceed sequentially through all 10 packets to reach a world-class product and a proven 5-lakh active-attempt target, **but** the current active phase is:

- **FINAL-SCOPE COMPLETION AND DEEP VERIFICATION (IN PROGRESS)**
  - ✅ Repair reproducible correctness defects **A01–A06** and convert regressions from `xfail` into passing tests **without weakening holds**.
    - A06 is resolved by **architecture change**: legacy extraction **never writes to academic destination**; it only stages a fenced `proposal` payload on the job record. The extract route remains held; unified importer is the supported path.
  - ✅ Dependency remediation: **backend dependency audit now shows 0 known advisories and 0 skipped packages**, with `pip check` passing.
    - Removed unused vulnerable dependencies (`python-jose`, `ecdsa`, dormant `emergentintegrations` + `litellm`) while keeping the object storage adapter unchanged.
  - ⏳ Implement **Results Analytics registry A01–A60** derived from source guide 04 with traceability and correct evidence thresholds.
  - ⏳ Implement missing evidence collectors needed for a subset of A01–A60 (timing/cohort/consult events). No artificial metric availability.
  - ⏳ Complete offline-safety UX: late draft quarantine flows, profile-scoped signout guard, and typed option math rendering polish.
  - ⏳ Deep end-to-end tests: imports → attempt → offline recovery → submit → embargo → leaderboard → report download, desktop + mobile.

Notes:
- **Packet 1 remains IN PROGRESS** (foundation expanded significantly; exit blocked).
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

- Backend modularized into bounded contexts (`auth`, `content`, `attempts`, `jobs`, etc.).
- Core attempt loop + scoring + PDF report generation exists.
- PDFs stored locally with SHA256 manifest:
  - `/app/docs/source_guides/manifest.json` + per-PDF `.txt` extraction.
- **Capacity goal** remains: architect for 500,000 concurrently active attempts from launch.
  - Current deployment is a **modular monolith** with **standalone MongoDB** (no replica set), so it is **not** aligned to PDF-05 “20 independent cells”.

### Latest approved changes and execution evidence (historical; audited)

- Student auth remains phone-only.
- Offline draft persistence exists.
- Report generation exists.
- UI uses matte maroon light/dark.

> Earlier “done” items are not treated as full compliance; the audit matrix is the current truth.

### Completed work (since the strategy-only phase) — UPDATED

**Portable strategy PDF**
- `/app/frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf` published, verified, and versioned.

**Packet 1 foundation expanded (still exit BLOCKED)**
- Strict command/kernel schemas + exact workload calculator.
- Fail-closed safety holds for upload/source preview/publication/extract/regrade.
- Staff-only engineering endpoints (`/api/internal/capacity/profile`, `/api/internal/safety/status`).
- Safe-by-default testing (`/app/pytest.ini` → runs `tests/packet1`).
- Executable ingress contracts (updated): route contract enumeration fixed to include included routers.
- Staff generation fencing + operator-only credential rotation tooling (not executed live) + runbook.

**Unified Importer + Organiser implemented (PDF + Excel) — DONE + VERIFIED**
- Backend:
  - Importer API + immutable imported set publication
  - Sandbox supports both `pdf` and `xlsx`
  - Excel organiser worker
  - Upload guard middleware (bounded multipart budgets + immutable import freeze)
- Frontend:
  - StudioImportHub + organiser detail view (preview → schedule → live/unlive)
  - Matte maroon design preserved + mobile overflow fixes + toast positioning below header
  - Dark-mode and overflow checks verified at 390px and 1920px
- Design:
  - `/app/design_guidelines.md` updated with binding Excel addendum + Results analytics/offline safety addendum

**PDF organiser sandbox integration fixed (without weakening isolation)**
- RCA corrected: failure was **lazy codec loading** after chroot.
- Fix: **preload required codecs** before sealing chroot; retain chroot + UID drop + seccomp + resource limits.

**Competitions + embargo + descriptive analysis — DONE + VERIFIED (bounded slice)**
- Competition hub + per-competition leaderboard.
- Ranking uses first competition attempt per profile; equal-score rank gaps verified (1,1,3).
- Solutions/results/reports/retries embargoed until competition end.
- Results include evidence-based “missed-topic priorities” (no fabricated percentile/readiness).

**Correctness defect repairs (A01–A06) — DONE + VERIFIED**
- A01 retry alias durability fixed (`bind_retry_alias`) and collision checks enforced.
- A02 publish CAS fixed with a single-winner publication outbox (`publication_pending`) + idempotent archival.
- A03 concurrent edit lost-update fixed using `expected_revision` CAS.
- A04 audience now fails closed; create validates supported audiences.
- A05 queued job draining fixed (`drain_lane`).
- A06 extraction no longer writes to academic destination; it stages a fenced proposal on job record only. Extract route remains held.

**Dependencies and advisories — UPDATED**
- Backend dependency posture now:
  - `pip-audit` shows **0 known advisories** and **0 skipped packages**.
  - Removed unused vulnerable dependencies (`python-jose`, `ecdsa`) and dormant `emergentintegrations` + `litellm`.
  - `pip check` passes.
- Frontend dependency posture:
  - Attempted KaTeX upgrade was blocked by a Node 22 engine requirement via a transitive dependency (`commander@15`).
  - **Policy**: resolve with Node 20 compatible, patched versions (e.g., KaTeX 0.16.x) and do not ignore engines.

**Testing and evidence — UPDATED**
- Isolated suite: now **198 tests passing** with A01–A06 fixed and prior xfails retired.
- Prior real storage verification evidence remains authoritative for import/report flows:
  - `/app/docs/UNIFIED_IMPORTER_VERIFICATION.md`
  - `/app/test_reports/iteration_51_verified.json`

**Analytics registry definitions (guide-aligned) — STARTED**
- Generated a traceable 60-metric definition file from source guide 04:
  - `/app/backend/tejas/analytics_registry.json`
  - Includes source SHA256 for traceability.

**QA hygiene**
- QA imports hidden (`qa_only`) from normal Studio lists.
- Credential literals in test artifacts redacted; temporary/broken helpers removed.
- Rotation/session revocation NOT executed (operator action required).

### Current work status — UPDATED

- Unified owner workflow + competitions + descriptive analysis are **implemented and verified**.
- Sandbox protection remains in place.
- A01–A06 correctness regressions are **fixed and verified** (198 isolated tests passing).
- Backend dependency advisories are **cleared**.
- Not “production ready” / not “500k proven” because:
  - Packet 1 exit remains blocked by credential-incident operational closure + remaining registry closures.
  - Scale/load qualification and distributed infra are not provisioned.
  - Full A01–A60 analytics implementation requires additional evidence collectors and UI/registry gating; only definitions exist so far.

---

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

User stories:

1. Owner uploads PDFs privately.
2. Owner can alternatively upload Excel to import typed questions/options/answer/solution.
3. System pairs questions and solutions **exactly** and blocks on ambiguity.
4. Student can attempt (MCQ + numerical).
5. Student gets accurate scoring.
6. Student can download complete matched-solution PDF report.

Status recap:
- ✅ POC private storage + attempt loop + scoring + report exist.
- ✅ Importer/organiser pipeline is integrated.
- ✅ Competition embargo + leaderboard + descriptive priorities exist.

Stop and fix until:
- (a) 1:1 pairing, (b) report PDF downloads, (c) no key leakage.

**Status:** achieved for bounded feature scope (verified).

### Phase 2 — V1 App Development (build full product around proven core)

User stories:

1. Premium landing.
2. Browse sets.
3. Phone-only login.
4. Attempt loop.
5. Unified Studio importer/organiser flow (PDF + Excel) with schedule + live/unlive.
6. Competitions and leaderboards.
7. Evidence-based descriptive insights.

Status:
- ✅ Unified Studio importer flow implemented.
- ✅ Legacy Studio editor remains available as fallback.
- ✅ Competitions and embargo implemented.
- ✅ Descriptive priorities implemented.

### Phase 3 — Comprehensive testing, hardening, and regression — UPDATED

Mandatory closures before any “ready/secure/scale proven” claims:

- **Evidence test closures**
  - ✅ `test_no_content_type_valid_body` regression fixed.
  - ✅ Operation catalogue regenerated/validated against current runtime routes.
  - ✅ A01–A06 fixed and verified (198 passing tests). A06 resolution is an intentional architecture change.

- **Security evidence refresh**
  - ✅ Backend: `pip-audit` now 0 advisories, 0 skipped; `pip check` passes.
  - ⏳ Frontend: resolve KaTeX upgrade path within Node 20 constraints; run dependency scan and document results.

- **Front-end evidence**
  - ✅ Desktop + mobile importer screens verified (PDF + Excel hub, organiser detail, schedule, live/unlive).
  - ✅ Mobile toasts verified below header; no overflow in organiser/competitions/insights.
  - ⏳ Add offline-safety UX: draft quarantine recovery surfaces + signout guard dialog.
  - ⏳ Typed options math rendering polish and test coverage.

- **Object storage end-to-end evidence (non-mocked)**
  - ✅ Real PDF pair upload → READY → schedule → attempt → embargo release → report download verified.
  - ✅ Real Excel upload → READY → schedule → attempt → embargo release → report download verified.

**NEXT deep-verification tranche (now active; no user review prompts)**

- **Results analytics (Packet 08 aligned, but implemented incrementally):**
  1) Commit the **A01–A60 metric registry** as a runtime-visible structure with:
     - definition, formula text, required evidence inputs, denominators, gating thresholds.
     - strict “Unavailable with reason” states.
  2) Implement only the metrics supported by **current stored evidence** (ledger + attempt metadata).
  3) Add evidence collectors for missing inputs (do not fake):
     - **Per-question timing** (server-side events; not client-only timers)
     - **Solution consulted / hint events** (explicitly captured)
     - **Cohort window sizes** and minimum thresholds (source guide rule: **>=100**) before percentile/rank displays.
  4) Drillthrough/evidence drawer patterns per updated `/app/design_guidelines.md` addendum.

- **Offline safety & typed math UX (Packet 07 aligned):**
  - Late draft quarantine list + resume/discard flows.
  - Profile-scoped signout guard dialog (keep/discard) when unsynced drafts exist.
  - Typed option math rendering: ensure KaTeX output doesn’t overflow mobile; apply consistent wrapping.

- **Deep end-to-end testing suite (not a 500k certification):**
  - PDF import and Excel import (templates + error CSV).
  - Phone login, attempt start, answer save idempotency, reload/resume.
  - Offline draft recovery messaging (network failures, late ack) + signout guard.
  - Submit receipt idempotency and grading delay handling.
  - Competition: shared window, late join cutoff, embargo until end, leaderboard ranks.
  - Reports: storage download, access control, embargo enforcement.
  - Cross-profile isolation: ensure user A cannot see user B attempts or reports.
  - Desktop + mobile (390px) and light/dark.
  - Bounded synthetic concurrency (hundreds/thousands) for hotspot endpoints with safety holds; not a 500k proof.

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening (bounded tranche)

- Rulebook + capacity worksheet exist; Packet 1 includes executable workload math and typed planning DTOs.
- This does **not** provision live cells or validate throughput.

Immediate next hardening targets (without blocking the now-working product flow):
- Complete frontend dependency remediation/disposition under Node 20 constraints.
- Implement missing evidence collectors needed for A01–A60 (without fabricating values).
- Close credential incident operationally (rotation + revocation) when authorized.
- Move toward official-year presets only after engine verification and evidence gates.

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

---

#### Packet 1 — Rules, Safety & Regression Baseline (P01) — **IN PROGRESS (foundation expanded; exit blocked)**

**Purpose:** Freeze what “correct” means before major refactors; create enforceable safety rails and red regressions for later packets.

**Must deliver (Packet 1 scope only):**

- **Atomic requirement registry**: expand beyond the current partial review into atomic MUST/acceptance clauses from all five PDFs.
- **Contract-first API & permission catalogue**:
  - strict input DTOs, typed errors, idempotency scope, payload budgets.
- **Data ownership map**:
  - vaulting/sourcing boundaries, content truth vs analytics projections, job/outbox boundaries.
- **Regression baseline & evidence discipline**:
  - ✅ A01–A06 are now repaired with regression evidence.
  - Keep new red regressions for remaining known risks (e.g., offline/session UX gaps) until fixed.
- **Containment (not permanent fixes):**
  - fail-closed containment around unsafe upload/publication/job paths until owning packets repair them.
- **Credential incident handling (planning + safe execution path; not executed yet):**
  - tooling/runbook exists;
  - actual rotation + session revocation remains blocked until authorized.
- **Dependency/advisory triage evidence**:
  - ✅ Backend advisories cleared.
  - ⏳ Frontend advisories still require full disposition.

**Packet 1 additions (within scope; CURRENT)**

- Importer, competitions and insights flow reflected in operation catalogue and ingress contracts.
- Evidence updated and verified via `/app/docs/UNIFIED_IMPORTER_VERIFICATION.md`.
- Results analytics/offline safety addendum incorporated into `design_guidelines.md`.
- A01–A60 definitions generated in `backend/tejas/analytics_registry.json` with source hash.

**Exit gate (unchanged; do not weaken):**

- Owner-approved contracts and failure scope.
- Zero orphan mandatory clauses in the detailed registry.
- All current findings have a red regression or explicit reproduction plan.
- Safe test isolation and credential containment evidence.
- With explicit operator authorization and one-time user execution-window authorization: **actual persisted credential rotation + session revocation evidence**.

**Fix ownership mapping (from audit):**

- Permanent fixes by packet (do not do early):
  - P04 owns A05/A06/S01
  - P05 owns A02/A03/A04
  - P06 owns A01
  - P07 owns F01/F02/F03

---

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

### B) Product-First Owner Flow (Unified Importer + Organiser) — ✅ COMPLETED (bounded feature phase)

Delivered the user’s requested workflow while respecting packet boundaries:

- ✅ Studio: PDF pair or Excel import + templates.
- ✅ Auto pairing + explicit issue lists; blocked state prevents scheduling.
- ✅ Prompt only for start date/time.
- ✅ Live/Unlive toggle.
- ✅ Competitions hub + leaderboard.
- ✅ Embargo keys/solutions/reports until end.
- ✅ Descriptive missed-topic priorities in results.

Evidence:
- `/app/docs/UNIFIED_IMPORTER_VERIFICATION.md`
- `/app/test_reports/iteration_51_verified.json`

### C) FINAL-SCOPE COMPLETION AND DEEP VERIFICATION — IN PROGRESS

Work proceeds autonomously (no user review prompts) to:

1) ✅ Fix A01–A06 regressions per owning packet scope (verified via 198 passing tests).
2) ✅ Reduce backend advisory surface area to 0 with tested removals/upgrades (verified).
3) ⏳ Resolve frontend dependency posture under Node 20 constraints; rerun scans and record disposition.
4) ⏳ Implement A01–A60 analytics registry + UI with strict evidence gating and drillthrough.
5) ⏳ Add missing evidence collectors (timing/consult/cohort) and only then enable dependent metrics.
6) ⏳ Implement offline safety UX and typed option math polish.
7) ⏳ Execute deep end-to-end tests and publish a final verification report (code + evidence logs + screenshots + real storage downloads) **without claiming 500k certification**.

### D) Continue Packet 1 completion work (still required)

1. Extend atomic clause registry across all five PDFs.
2. Close credential incident (operator action + one-time explicit execution-window authorization).
3. Complete frontend dependency advisories and explicitly disposition any remaining scan output.
4. Keep safety holds until P04/P05 fixes exist.

### E) Continue sequentially through Packets 2–10

- Proceed sequentially as Packet 1 exits and dependencies are met.
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

- Packet 1 deliverables completed per `TEN_PACKET_STRATEGY.md`.
- Student login remains phone-only; UI remains matte maroon.
- Credential incident handling:
  - rotation tool + runbook prepared;
  - execution only with one-time explicit execution-window authorization and operator authorization;
  - no credentials leak in artifacts.
- Dependency advisories recorded honestly; no clean scan claim.
- Evidence is honest: known audit defects stay red until repaired.
- Operation catalogue and baseline evidence match actual runtime routes.

### Product-first owner flow success (updated) — ✅ achieved for bounded feature phase

- Owner can create a test in **one place** via:
  - **PDF mode**: upload Questions PDF + Solutions PDF, OR
  - **Excel mode**: upload .xlsx using template (single workbook or two files).
- System auto-organises a Draft Test and clearly reports ambiguity/issues.
- **Excel** import provides:
  - downloadable template
  - strict header parsing
  - deterministic pairing by question_id/question_no
  - row-level errors + downloadable error report
- Owner is asked **only start date/time** after organisation is Ready.
- Owner can toggle Live/Unlive; students can attempt only when Live and within windows.
- Competition features:
  - first attempt per profile, equal-score ranks (1,1,3)
  - embargo scores/solutions/reports until end
  - no fabricated percentiles or participants
- Evidence includes:
  - real object storage upload proof
  - real browser screenshots desktop + mobile
  - no secrets/tokens in any artifacts.

### Final-scope completion success (current active target; not 500k certification)

- ✅ A01–A06 regressions repaired (xfails converted to passing tests; A06 fixed by removing destination writes).
- ✅ Backend dependency advisories reduced to 0 and fully scanned (no skipped packages).
- ⏳ A01–A60 analytics registry + UI exists; each metric has:
  - formula/version, required evidence, denominators, unavailable reason; no fabricated values.
- ⏳ Evidence collectors exist for metrics requiring new data (timing/consult/cohort). Metrics remain unavailable until collectors exist.
- ⏳ Deep end-to-end tests cover:
  - PDF+Excel imports, phone login, start/resume, save idempotency, offline recovery, submit, grading, embargo, leaderboard, and report download.
  - Desktop + mobile + light/dark + auth isolation.
- ⏳ Frontend dependency posture is remediated and scanned under Node 20 constraints.

### Product success (post-strategy; future)

- Phone-only student entry preserved.
- Secure staff publishing and locked truth.
- Full official exam engines + 60 analyses.
- Measured and qualified concurrency envelope, not assumed.

## Explicit Release Blockers (remain blockers until qualified)

- 20×25k home-cell fleet and routing
- Multi-AZ durability + failover + restore proofs
- Transactional admission + writer fencing + explicit commit protocol
- Independent worker fleet and sandboxed parsing (Tier A isolation proof)
- Staff MFA/step-up + signing/KMS + WORM/ObjectLock
- Authorization-aware CDN distribution
- Full 60-analytics pipeline (implementation + evidence collectors + UI)
- Full load + chaos + restore qualification campaign
- Any OPEN audit P1 correctness defect (A01–A06, S01, F03)
- Any unperformed mandatory WP/OPS-R gate (PDF-05 p65–68)
- Any unresolved dependency advisory or skipped package without explicit tested disposition
