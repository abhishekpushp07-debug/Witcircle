# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, using authoritative guides + owner-supplied content, with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, explicit data ownership, durable async job boundaries for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrently active exam attempts** (not registered users).
  - This remains an **unverified architecture goal** until realistic **load + fault + restore** qualification and operator signoff is performed (PDF-05).
  - “No lagging” is defined via measurable SLOs (latency, error rate, durability, backlog age), not an unprovable “0 lag” claim.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt) **when solutions exist**.
  - **Single downloadable PDF report** per attempt (results + matched solutions when available, or answer keys when keys-only content is supplied).
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored; late/unacknowledged drafts are disclosed.
  - **No key/solution leakage during an active attempt** (including via direct URL guessing).

### Binding communication preference (critical)

- **Do not ask the user for interim review** before “final product”.
- **No routine confirmations/menus** asking the user to pick next features.
- Progress updates may be informational, but **not approval checkpoints**.
- Only **critical, irreversible, access-impacting actions** (e.g., staff credential rotation + session revocation) may require a single explicit authorization.

### LATEST user priority (P0 — supersedes security/backlog)

User required that the **exam section + upload/test organisation** be production-grade, and supplied chapter-wise PDFs.

**P0 requirement:** Build a **chapter-wise BITSAT exam experience** from the owner-supplied chapter books and publish it **Live now** with **1-year validity**.

- Inputs: **3 “chapter-wise question book” PDFs** (Physics, Chemistry, Mathematics):
  - `/app/data/chapter50/physics.pdf` (30 chapters / 1500 Q)
  - `/app/data/chapter50/chemistry.pdf` (32 chapters / 1600 Q)
  - `/app/data/chapter50/mathematics.pdf` (32 chapters / 1600 Q)
- Output: **94 chapter tests** total (30 + 32 + 32), each:
  - **Exactly 50 questions**
  - **60 minutes** per attempt
  - **BITSAT marking:** +3 correct / −1 wrong / 0 unanswered
  - **Live now + validity 1 year** (availability window), independent from the 60-minute per-attempt timer
  - Immediate results after submission (no competition embargo)
- Content truth: these books contain **ANSWER KEYS ONLY** (no worked solutions). UI must disclose clearly; **no fabricated solutions**.
- Rendering truth: where typed/OCR extraction is unsafe for formulas/diagrams, **use original PDF image** regions (source-faithful) rather than guessing.
- Reliability rule: **each generated test must be independently rechecked** by a testing agent before it is published.

A dedicated additive design spec for this feature exists:
- `/app/design_chapter_tests.md`

### Auth requirements (non-negotiable)

- **Students**: phone-number only (no OTP, no password). This is a convenience profile, not verified phone ownership.
- **Staff/Owner**: secured separately.

---

## Studio Owner Credential Update (AUTHORIZED) — COMPLETED

**Status:** ✅ COMPLETED

User authorized changing the **Content Studio owner login email** and credential.

### Outcome (verified)

- Owner email is now `abhishek@billpe.com`.
- The **original owner UUID** is preserved: `01eb6f65-69f8-4614-abe8-d9fad1bcf501`.
- Rotation was **atomic** (email + hash + generation) and advanced owner **credential_generation → 1**.
- **97 old owner staff sessions revoked**.
- **199 phone sessions preserved** (student access unaffected).

### Evidence discipline (binding)

- The owner password **must never appear** in plan/docs/source/tests/logs/screenshots.

---

### Theme requirement

- Matte maroon theme stays as-is (`#5C0025`), with light/dark tokens.

---

### Capacity/claims stance (binding)

- We do **not claim** 5 lakh concurrency as proven without measured evidence.
- We define a qualification path (PDF-05 staged load envelopes + explicit SLOs), but until executed it remains **UNQUALIFIED**.

---

## Execution updates and current status

### What is working (verified on current HEAD)

- Backend modularized into bounded contexts (`auth`, `content`, `attempts`, `jobs`, `imports`, `competitions`, `reviews`, `analytics`, etc.).
- Unified importer/organiser exists for **PDF pair** and **Excel** (≤300 questions/import).
- Immutable imported set publication exists.
- Scheduling and Live/Unlive gating exists.
- Competition leaderboard exists with embargo.
- Offline draft recovery + sign-out guard exists.
- Results analytics workspace exists (guide-aligned registry + evidence-gated metrics).
- **Guide04 learner analytics addendum is implemented and verified**:
  - Pre-answer confidence (non-blocking, precommit semantics)
  - Post-result reflections + mistake-review checklist (private)
  - EV “what-if” calculator embedded in A44 evidence drawer
  - Canonical A41/A42/A43/A45/A50 semantics enforced

### Phase 3.3 checkpoint update (bounded security + verification) — COMPLETED

**Status:** ✅ COMPLETED for the bounded security checkpoint

- Compatible dependency updates (eslint/@eslint/js/postcss) applied.
- Frontend build passes.
- Audit improved but remains **not clean**; CRA toolchain still a blocker.
- Capacity remains **UNQUALIFIED**.

### P0 user bug — PDF import not extracting direct questions (legacy paper pair)

**Status:** ✅ COMPLETED

- PDF organiser now parses the sensitive TEJAS200 paper pair correctly (75 questions) and does not confuse numbered solution steps.

### P0 — Chapter-book exam experience for BITSAT

**Status:** ✅ COMPLETED + ✅ PUBLISHED LIVE + ✅ VERIFIED END-TO-END

#### What is completed

- New sandbox parser isolated from the sensitive PDF-pair regex (untouched):
  - `backend/tejas/chapter_book_organiser_worker.py`
- New backend chapter-book pipeline + APIs:
  - `backend/tejas/chapter_books.py` and supporting updates.
  - Source stored once (private object storage); per-question refs render as needed.
- All 3 books uploaded via owner HTTPS API; IDs:
  - Physics: `f11ab410-5ff9-5fc7-8d1f-e9353701603f`
  - Chemistry: `75ee1d71-4bd1-58f9-a821-0ebec0e11f91`
  - Mathematics: `0f0fb45f-197f-5fae-9377-ce5c317f3201`
- 94 chapter sets created (4700 questions) with:
  - Source-image question regions (formula-safe)
  - Individual key crops (admin-only)
  - `solution_kind='answer_key_only'` with clear disclosure messaging
  - `competition=false`
- Independent verification gate produced and validated:
  - `test_reports/chapter50_recheck.json` shows **94 PASS** with strict per-chapter evidence (source SHA256 + parsed-manifest SHA256 binding).
- Publication:
  - ✅ **Published LIVE** with exact validity evidence:
    - `test_reports/chapter50_publication.json`
    - Availability: **2026-10-17 through 2027-10-17 (UTC)**
    - Counts: Physics 30, Chemistry 32, Mathematics 32 (total 94)
  - Idempotency safety:
    - Re-uploading the Physics PDF via Studio file input re-opens the **same** book (30/1500) and **does not extend expiry**.
- Mobile/desktop UX safety fixes:
  - True **canvas zoom + pan** for source images (100%–500%), touch + mouse + keyboard arrows.
  - Owner private preview dialog background fixed to be fully opaque.
  - Dark-mode catalog contrast validated with real populated data.
- Score/report truth fixes:
  - Answer-key-only labeling preserved end-to-end (frozen packs + public attempt/result DTO + report generation).
  - PDF report title and button label switch to **“Answer keys”** for answer-key-only content.

#### Verified real owner flow

- Studio defaults to **Chapter book · 1 PDF** mode.
- Upload is stored privately.
- Processing produces 50Q chapters + key crops, then publication becomes available only after per-test independent recheck.
- Owner can preview Q1..Q50 and key crops (private), and toggle Live/Unlive per chapter without mutating validity.

#### Verified real student flow (main browser)

The following end-to-end path was verified with real browser execution (no mocks):

- `/exams` catalog shows **94** and subject counts.
- Student phone login via `/login` works and redirects back to the set.
- Preflight “device check” passes; attempt starts with **3600s** timer.
- Active attempt payload contains **no keys**; solution/key asset endpoint returns **403** before submission.
- Offline answer save shows “pending”, then reconnect restores “saved”; reload preserves server-acknowledged answers; deadline unchanged.
- Resume from catalog works.
- Submit leads to immediate results (no competition embargo).
- Known scenario validated: **1 correct + 1 wrong + 48 skipped → score 2 / 150**.
- Actual PDF download validated:
  - `test_reports/chapter_pdf_verification.json` proves:
    - `%PDF` header
    - 51 pages
    - ordered Question 1..50 headings
    - 50 “Supplied answer key (no worked solution)” labels
    - “RESULTS & ANSWER KEYS” header and explicit “No worked solutions were supplied.” disclosure

#### Testing status (truthful)

- Full automated run: **396 passed**
  - Evidence: `test_reports/chapter_final_full_regression.log`
- Frontend build: ✅ passes
  - Evidence: `test_reports/chapter_frontend_final_build.log`
- Independent final UX/document check: ✅ pass
  - Evidence: `test_reports/iteration_79.json`
- Release summary doc:
  - `docs/CHAPTER50_RELEASE.md`
  - `test_reports/chapter50_final_verified.json`

#### Cleanup discipline

- Removed exactly 2 QA attempts + 2 browser sessions and temporary local token/PDF artifacts.
- Preserved all **94 published tests** and all **3 stored chapter books**.
- Preserved original owner UUID and the original 75Q ready/unscheduled import.

---

## Completed work (since the strategy-only phase) — UPDATED

### Portable strategy PDF

- `/app/frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf` published.

### Unified Importer + Organiser (PDF + Excel) — IMPLEMENTED; verified

- Backend importer API + immutable import freeze.
- Sandbox workers:
  - `pdf_organiser_worker.py` for PDF-pair (questions+solutions)
  - `excel_organiser_worker.py` for Excel
- StudioImportHub supports PDF and Excel modes.

### Competitions + embargo — DONE + VERIFIED

- Competition hub + leaderboard.
- Embargo prevents early results/solutions.

### Guide04 learner confidence + reflections/checklist + EV — DONE + VERIFIED

- Confidence (optional) + reflections/checklist + EV calculator are integrated and tested.
- Backend tests: packet1 and integration suites passing per evidence logs.

### NEW: Chapter-wise tests (BITSAT) — IMPLEMENTED + VERIFIED + LIVE

- Additive design spec:
  - `/app/design_chapter_tests.md`
- Parser + chapter-book pipeline:
  - Strict chapter splitting and **two independent key extraction methods**
  - Source-region rendering (formula-safe)
  - Independent per-chapter recheck required for publication
- Publication evidence:
  - `test_reports/chapter50_publication.json` (Live through 2027-10-17 UTC)
- UI:
  - Studio chapter-book import + private preview
  - Student `/exams` catalog

---

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

**Status:** Existing PDF-pair + Excel flows stable; chapter-book parser and APIs stable.

### Phase 2 — V1 App Development (build full product around proven core)

**Status:** Existing MVP works for imports/competitions/practice; chapter-wise exams are Live and functional.

### Phase 3 — Comprehensive testing, hardening, and regression — UPDATED

#### Step 1: Owner Studio credential update — ✅ COMPLETE

#### Step 2: PDF-pair import repair — ✅ COMPLETE

#### Step 3: Guide04 analytics addendum — ✅ COMPLETE

#### Step 4: Deep testing (autonomous) — ✅ COMPLETE for existing features

- Backend packet suite passing.
- Browser checks for Player/Results + report download verified (general + chapter tests).

#### Step 5: Phase 3.3 compatible security checkpoint — ✅ COMPLETE (bounded)

- Audit improved but not clean.

---

## Phase 3.P0 — Chapter-book Import + Exams Catalog (COMPLETED)

### P0.1 — Backend: Chapter-book pipeline (single PDF with answer keys)

**Goal:** Convert each subject chapter book into chapter tests safely and deterministically.

**Status:** ✅ COMPLETE

### P0.2 — Publishing model: Practice sets (not competitions)

**Goal:** Published chapter tests behave like practice tests (immediate results).

**Status:** ✅ COMPLETE + ✅ PUBLISHED

- Evidence: `test_reports/chapter50_publication.json`

### P0.3 — Frontend: Studio “Chapter book (single PDF)” mode

**Goal:** Upload and chapter/test generation feel product-first.

**Status:** ✅ COMPLETE

### P0.4 — Frontend: Student “Exams” catalog

**Goal:** Clean student-facing chapter exam section.

**Status:** ✅ COMPLETE

### P0.5 — Recheck / Independent verification gate (mandatory)

**Goal:** “Har test banane ke baad recheck new agent se” enforced.

**Status:** ✅ COMPLETE

- Evidence: `test_reports/chapter50_recheck.json` (94 PASS)

### P0.6 — End-to-end deep testing (backend + frontend)

**Goal:** Ship this as a stable student experience.

**Status:** ✅ COMPLETE

- Full automated run: 396 passed (evidence: `test_reports/chapter_final_full_regression.log`).
- Full real-browser/real-download evidence captured (see `docs/CHAPTER50_RELEASE.md`).

---

## 3) Next Actions

### A) Immediate (P0): NONE — Chapter50 scope shipped

- The Chapter50 phase is complete and published live with verified UX + score + PDF.

### B) Frontend security posture (CRA advisories) — deferred (P1)

- Residual CRA/react-scripts advisories remain a release blocker.
- Controlled migration is required.
- Evidence basis remains in `docs/FRONTEND_SECURITY_REMEDIATION.md`.

### C) Capacity qualification readiness (P1) — planning only

- Maintain explicit UNQUALIFIED status.
- Do not run large load against shared preview.

### D) Extend “Chapter book” support beyond the supplied PDFs (P2)

- Supported structure is currently intentionally strict and fails closed.
- New/unrecognised books remain **private** until independent per-test recheck is available.
- No OCR/scans performance claims.

---

## 4) Success Criteria

### Product-first owner flow success (UPDATED)

- Owner can upload **PDF pair** and **Excel** as before.
- Owner can upload **chapter book single PDF** and auto-generate chapter tests.
- Each generated chapter test is:
  - 50 questions
  - 60 min
  - +3/−1/0
  - Live now with **1-year validity**
  - No solutions fabricated; answer keys used only for scoring
  - Source-faithful rendering for formulas/diagrams via images
  - Independently rechecked before publication

### Student exam section success (UPDATED)

- Student sees `/exams` catalog with subject filters.
- Can start/resume attempts with offline recovery.
- Gets immediate results after submit.
- Can download PDF report.
- No answer keys/solutions leak during active attempts.
- **Mobile formula zoom is actually usable** (zoom + pan) and does not cause overflow.

### Final-scope completion success (not 500k certification)

- Deep regression suite passes (backend + frontend where applicable).
- Real browser offline + report flows pass.
- Chapter tests published without key leakage.
- Guide04 confidence/reflection flows still working.

---

## Explicit Release Blockers (remain blockers until qualified)

- **CRA/react-scripts dependency advisories** until controlled migration + re-audit.
- **500,000 concurrent user qualification** until staged load/fault/restore campaign is executed with evidence.
- **PDF importer robustness** beyond the provided supported PDFs (no OCR/scans claim).
- Multi-AZ durability + failover + restore proofs.
- Full load + chaos + restore qualification campaign.
- Any unperformed mandatory WP/OPS-R gate (PDF-05 p65–68).
