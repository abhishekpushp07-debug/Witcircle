# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, using the **5 provided PDFs** as the authoritative base guide, with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, vaulting/catalog separation, durable async job queue for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrent students**.
  - This remains an **unverified architecture goal** until realistic load tests + infra provisioning are performed.
  - The MVP must avoid synchronous heavy work (PDF generation, regrade, extraction) on request threads.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt).
  - **Single downloadable PDF report** per attempt (results + matched solutions).
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored; late/unacknowledged drafts are disclosed.
  - **No key/solution leakage during an active attempt** (including via direct URL guessing).
- **Auth requirements (non-negotiable)**:
  - **Students**: phone-number only (no OTP, no password).
  - **Staff/Owner**: secure password-based auth, separate entrance and authorization checks.
- **Theme requirement (updated)**:
  - **Matte maroon** theme (supersedes teal and PDF-01’s “blue” guidance). Includes light + dark theme tokens and typography refresh.
- **LATEST USER DIRECTIVE (Audit-first rule)**:
  - **No new features or fixes yet.**
  - First **audit the entire architecture and everything coded so far** against the updated rules extracted from all 5 PDFs.
  - Deliver an evidence-backed **PASS / PARTIAL / FAIL / NOT VERIFIED** matrix, with file references and PDF page references, plus remediation priorities.

### Capacity/claims stance (binding)

- We **do not claim** 5 lakh concurrency as “proven” without a measured load campaign (per PDF-05).
- We **do** implement (and test) correctness properties that are prerequisites for scale (idempotency, bounded hot paths, durable receipts, strict privacy, async heavy work), but:
  - Passing small tests **is not** capacity qualification.
- During the **audit-only phase**, we **do not** convert intended architecture into claims.

## Execution updates and capacity stance

- Backend modularized into bounded contexts (`auth`, `catalog`, `content`, `attempts`, `answers`, `packs`, `reports`, `scoring`, `jobs`, `corrections`).
- Core extraction + 75-question workflow + scoring + PDF report generation exists.
- PDFs stored locally with SHA256 manifest:
  - `/app/docs/source_guides/manifest.json` + per-PDF `.txt` extraction for page-level referencing.
- **Capacity goal** remains: architect for 500,000+ concurrent from launch.
  - Current deployment is a **modular monolith** with **standalone MongoDB** (no replica set name), so it is **not** aligned to the PDF-05 “20 independent cells” topology.
- No environment variables or infrastructure settings were modified.

### Latest approved changes and execution evidence (historical; now audited)

- **Student auth** remains phone-only (no OTP/password/email). Staff login remains separate.
- **Offline draft persistence** exists (`localStorage` drafts keyed by user + attempt).
- **Report generation** is queued and downloadable privately.
- UI migrated to **matte maroon** with light/dark theme tokens and typography refresh.
- QA fixture sets were withdrawn; original paper remains in review.

> Note: All prior evidence and “completed” items are **subject to audit classification**. Audit outputs are now the authoritative status.

### Current work status (session continuation)

A. **Reproduce and fix the Player blocker** (P0) — ✅ **COMPLETED (historical)**

B. **Verify offline recovery + submission + versioned scoring + matched PDF** end-to-end (P1) — ✅ **COMPLETED (historical)**

C. **Polish navigation + Exam Details** on desktop/mobile (P1) — ✅ **COMPLETED (historical)**

D. **Withdraw only identified QA fixtures** and record evidence; separate readiness vs unverified concurrency (P2) — ✅ **COMPLETED (historical)**

E. **Architecture Alignment to PDFs + 5-lakh scale hardening** (bounded tranche) — ✅ **COMPLETED (historical; superseded by audit where it disagrees)**
- ❗ Not a “full spec completion”; only a bounded tranche.

F. **Architecture & Full-Code Compliance Audit (against 5 PDFs)** (P0) — ✅ **COMPLETED (AUDIT ONLY, no fixes)**
- Deliverables (verified present):
  - `/app/docs/audit/AUDIT_REPORT.md`
  - `/app/docs/audit/REQUIREMENTS_MATRIX.md` (62 scoped rows)
  - `/app/docs/audit/RULEBOOK_ERRATA.md`
  - `/app/docs/audit/REMEDIATION_PLAN.md`
  - `/app/docs/audit/EVIDENCE_LEDGER.md`
  - `/app/docs/audit/analytics_60_matrix.csv` + `.json`
  - `/app/docs/audit/source_integrity_final.json` (2026-10-12T11:55:19Z)
- Key reproduced findings (audit only; **open**, no fixes):
  - **Backend (6 reproduced defects; report 26):** retry-resume idempotency gap; concurrent publish duplicates same version; silent reviewer lost update; invalid audience fail-open; queued jobs don’t self-drain when capacity frees; stale extraction worker can still mutate after lease replacement.
  - **Frontend:** typed MCQ option LaTeX renders as raw text (report 28); logout clears drafts for other profiles without explicit per-profile warning (report 27).
  - **Multipart/body budget:** local ASGI evidence that a 2MiB non-file multipart field bypasses JSON limits and hits parser path (report 30). Not treated as a live DoS/exploit proof.
  - **Local-storage corruption UI:** remains **NOT VERIFIED**; no false “fixed” claim.
- Other audited facts:
  - Seven real custom scorer fixtures pass (correctness for current supported practice types), but this is **not** capacity or full-exam-format proof.
  - All 60 analyses are mandatory (V4 p1, V5 p64). Internal “40 minimum” was a rulebook error. Implementation matrix: **10 partial**, **50 not implemented**; **no readiness percentage**.
  - Dependency alerts are not automatically exploits; advisories were recorded.
  - Credential-in-test-output incident: report artifact redacted; **actual staff password rotation + session revocation still REQUIRED, not done**.
  - Original paper: 75 questions, `review`, v1/r3; 50 QA sets withdrawn.

**New findings from PDF-05 (79p v2) binding for future implementation (not satisfied today)**
- Proposed topology: **5 planes** and **20×25k “Home Cells”** (proposal, not proof).
- Baseline model: **35,000 live RPS**, **51,666.7 combined**, **2× envelope = 70,000 live + 33,333.3 telemetry = 103,333.3 combined**, pathological **125,000 live RPS**.
- Event overlays: **starts 4,166.7/s** (500k/120s), **submits 16,666.7/s** (500k/30s).

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

User stories:
1. As an owner, I can upload the questions+solutions PDFs and store them privately.
2. As a reviewer, I can define Q1–75 and bind each to an exact solution entry with source page refs.
3. As a student, I can start an attempt and answer SCQ + numerical (including 5-digit answers) without seeing keys/solutions.
4. As a student, I get correct scoring (+4/−1/0) and per-question review with the matched solution.
5. As a student, I can download a single PDF report containing score + every Q in attempt order + my response + correct answer + marks + matched solution.

Steps:

- **POC-1: Private storage + secure serving** (✅ IMPLEMENTED; ✅ AUDITED)
- **POC-2: Deterministic content extraction + pairing scaffold** (✅ IMPLEMENTED; ✅ AUDITED)
- **POC-3: Attempt snapshot + scoring + deadline correctness** (✅ IMPLEMENTED; ✅ AUDITED)
- **POC-4: Results view model + PDF report generation** (✅ IMPLEMENTED; ✅ AUDITED)

Stop and fix until:
- (a) all 75 Q have 1:1 solution matches, (b) report PDF renders and downloads, (c) no key leakage during attempt.

### Phase 2 — V1 App Development (build full product around proven core)

User stories:
1. Visitor can understand practice loop via premium landing.
2. Visitor can browse published sets for JEE Main/BITSAT.
3. Student can sign in with **phone-number only**.
4. Student can complete full attempt with autosave + submit.
5. Reviewer can upload/review/approve/publish/withdraw with audit.

Steps (already implemented; now audited):

- **Backend (FastAPI + Mongo)**
  - Student APIs: catalogue, start/resume, save answer, submit, results, report job + download.
  - Staff APIs: Studio CRUD, review/approve, publish/withdraw, regrade job.

- **Frontend (React SPA)**
  - Matte maroon theme default + dark mode.
  - Player is “quiet workspace”; solutions only after submit.

### Phase 3 — Comprehensive testing, hardening, and regression

(Existing tests exist; audit now classifies which are valid evidence.)

- Automated backend tests (executed evidence now tracked under `/app/docs/audit/` and test reports):
  - Auth/role checks; vault proxy; upload validation.
  - Attempt lifecycle: idempotent start/submit; deadline fence; answer conflicts.
  - Jobs: bounded attempts, lease fencing, outbox recovery.
  - JSON/body guardrails (JSON only; multipart/file budgets remain a gap).
  - Throttling + accurate Retry-After.

- Frontend E2E (executed evidence):
  - Public → login → set detail → preflight → attempt → results (including **202 grading pending**) → report download.
  - Offline: pending drafts survive reconnect + refresh; late drafts disclosed.

- Security review (audited):
  - No key leaks detected in current active-attempt API allowlists.
  - However, rights gating and publication integrity defects remain open.

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening (bounded tranche)

**Purpose**: Convert the 5 PDFs into a binding engineering rulebook, run a gap audit, implement the highest-risk **code-level** improvements, and produce a **reference infra plan** (doc-only) for PDF-05 topology.

#### Phase 4.1 — Rulebook & traceability (binding docs)

Deliverables — ✅ **COMPLETED (historical; audited with errata)**:
- `/app/docs/RULEBOOK_ARCHITECTURE_V5.md`
- `/app/docs/GAP_MATRIX_PDF_TO_CODE.md`
- `/app/docs/CAPACITY_AND_OPERATIONS.md`
- `/app/docs/VERIFICATION_RECORD.md`
- `/app/docs/TESTING_RUNBOOK.md`
- Provenance: `/app/docs/source_guides/manifest.json` + extracted `.txt` pages.

**Audit correction:** PDF-04 mandates **ALL 60 analyses** (V4 p1, V5 p64). Any internal “40+” relaxation is incorrect and logged in `/app/docs/audit/RULEBOOK_ERRATA.md`.

#### Phase 4.2 — Code-level scale enablers (in-scope, previously implemented)

Implemented — ✅ **COMPLETED (historical; audit does not treat as full compliance)**:
- Async grading outbox (pilot)
- Durable command receipts (pilot)
- Start-key idempotency and resume alias binding (ordinary start path)
- Hot-path query slimming
- Bounded job lanes
- Retry/backoff + Retry-After
- Derivative cache + preflight reuse
- Mongo pool bounds + write concern configuration (note: standalone Mongo topology)
- JSON limits middleware
- Atomic staff/phone throttling

#### Phase 4.3 — Reference infrastructure (doc-only, per PDF-05)

- Reference design documented — ✅ **COMPLETED**
  - edge CDN + authorization-aware delivery
  - WAF/rate limiting
  - stateless API fleet + separate worker fleet
  - home-cell partitioning (20×25k proposal)
  - multi-AZ durability + DR runbooks
  - load-test plan and fault matrix

### Phase 5 — Architecture & Full-Code Compliance Audit (AUDIT ONLY)

**Goal:** Provide a defensible, evidence-backed audit of the current system against the 5 PDFs and the updated rules.

**Constraints (hard):**
- No application behavior changes (no fixes) during this phase.
- No environment variable modifications.
- No infrastructure changes or provisioning.
- No content publication, no loosening of rights gates.
- Only **documentation updates** and **non-mutating or isolated tests** are allowed.

#### Phase 5.1 — Inventory & traceability map — ✅ COMPLETE
- Source baseline captured: `/app/docs/audit/source_baseline.json` (97 app/config files)
- Supplemental inventory captured: `/app/docs/audit/supplemental_source_inventory.json` (4 additional public/build files)
- PDF page inventory captured: `/app/docs/audit/pdf_page_inventory.json` (177 pages)
- API route inventory (AST-based): `/app/docs/audit/api_inventory.json` (46 routes; only 2 with explicit response models; 27 mutation handlers; 10 endpoints accept `dict` bodies)

#### Phase 5.2 — Backend audit (FastAPI + Mongo) — ✅ COMPLETE
- Reproduced backend defects: see `/app/docs/audit/AUDIT_REPORT.md` and testing-agent report 26.

#### Phase 5.3 — Content/vault/sourcing audit — ✅ COMPLETE
- Rights/publication pipeline audited; status confirmed: 50 QA sets withdrawn; original paper remains review.

#### Phase 5.4 — Frontend audit (React) — ✅ COMPLETE
- Reproduced UI defects: typed option math rendering, logout draft scope; landing template title + small targets; PostHog config reviewed read-only.

#### Phase 5.5 — Testing & evidence audit — ✅ COMPLETE
- Earlier copied/incorrect harness outputs rejected.
- Corrected harness and credential redaction completed.
- `source_integrity_final.json` confirms **no application changes** during audit.

#### Phase 5.6 — Deliverables — ✅ COMPLETE
- Audit outputs are under `/app/docs/audit/` (see section F above).

#### Phase 5.7 — Independent verification — ✅ COMPLETE
- Testing-agent reproduction reports:
  - Backend defects reproduction: `/app/test_reports/iteration_26_corrected_audit.json`
  - Frontend math issue reproduction: `/app/test_reports/iteration_28_frontend_audit.json`
  - Multipart size bypass verification (local ASGI): `/app/test_reports/iteration_30.json`

## 3) Next Actions

### A) Present audit outputs (P0) — ✅ DONE
Audit outputs exist and are the new source of truth:
- `/app/docs/audit/AUDIT_REPORT.md`
- `/app/docs/audit/REQUIREMENTS_MATRIX.md`
- `/app/docs/audit/RULEBOOK_ERRATA.md`
- `/app/docs/audit/REMEDIATION_PLAN.md`
- `/app/docs/audit/EVIDENCE_LEDGER.md`

### B) Await user review and approve remediation priorities (P0) — CURRENT
No fixes are authorized until the user agrees on ordering. Immediate recommended decisions:
- Approve Gate 1 fixes for the 6 backend defects (A01–A06) and the P1 frontend math defect (F03)
- Approve the security action: rotate staff password + revoke sessions (operator task; not performed here)
- Decide policy for analytics/tracking (PostHog): disable, consent-gate, or minimization plan

### C) After approval: remediation implementation (P0/P1)
Only after user reviews the audit and agrees on priorities:
- Fix A01–A06 (backend correctness + publication integrity + fencing/dispatch)
- Fix S01 (multipart/form budgets; starlette multipart advisories)
- Fix F03 (typed option math rendering)
- Fix F02 (draft deletion scope/UX)
- Explicitly verify F01 (malformed local storage recovery) with real browser tests
- Correct rulebook claims to align with “all 60 analyses” and implement analytics roadmap (PDF-04)

Every fix must include:
- explicit acceptance criteria
- updated regression tests
- a new **testing_agent** report verifying the exact reported bug/gap

## 4) Success Criteria

### Audit phase success — ✅ MET
- Requirement-to-code inventory exists.
- Independently reproduced findings documented.
- No new application fixes shipped; source integrity verified.

### Product success (post-audit, future)
- Maintain:
  - Phone-only student access (no OTP)
  - Matte maroon theme
  - Offline recovery and exact solution pairing
  - Stable results + report pipeline
- Align fully with all 5 PDFs including PDF-04’s **all 60 analyses**.

## Explicit Release Blockers (must remain stated as blockers, per PDFs)

Not implemented / not provisioned / not qualified in this repo:
- 20×25k **home-cell** fleet, thin router, allocator/trust plane separation.
- Multi-AZ relational acceptance/sealing protocol and durability proofs.
- Transactional admission reservations, writer fencing/generation epochs, explicit-commit + drain protocol.
- Separate worker fleet and sandboxed parsing/extraction.
- SSO+MFA+PIN step-up, one-use transaction grants, KMS/HSM signing, and full secrets rotation.
- CDN authorization-aware delivery for protected assets at terabyte-per-minute scale.
- WAF quota validation and hostile-traffic mixed tests.
- Full **60-analysis** snapshot pipeline and cohort privacy gates at scale.
- Full load-test + chaos-test + restore-drill evidence package required for launch claims.

These remain documented and treated as launch gates, not silently “assumed.”
