# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, using the **5 provided PDFs** as authoritative guides, with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, vaulting/catalog separation, explicit data ownership, durable async job boundaries for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrently active exam attempts** (not registered users).
  - This remains an **unverified architecture goal** until realistic **load + fault + restore** qualification and operator signoff is performed (PDF-05).
  - “No lagging” is defined via measurable SLOs (latency, error rate, durability, backlog age), not an unprovable “0 lag” claim.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt).
  - **Single downloadable PDF report** per attempt (results + matched solutions).
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored; late/unacknowledged drafts are disclosed.
  - **No key/solution leakage during an active attempt** (including via direct URL guessing).

### Binding communication preference (critical)

- **Do not ask the user for interim review** before “final product”.
- **No routine confirmations/menus** asking the user to pick next features.
- Progress updates may be informational, but **not approval checkpoints**.
- Only **critical, irreversible, access-impacting actions** (e.g., staff credential rotation + session revocation) may require a single explicit authorization.

### LATEST user priority (product-first execution)

Deliver a simple unified owner workflow:

1) **One place** (Studio) to upload:
   - **Questions PDF + Solutions PDF**, OR
   - **Excel (.xlsx)** import for typed questions/options/answer/solution, including:
     - single workbook (Questions + Solutions), or
     - two workbooks / two sheets with deterministic pairing.
2) System auto-organises into a test draft with strict, auditable pairing (**no guessing**).
3) Only after organisation is complete, prompt owner **only for attempt start date/time** (IST).
4) Provide **manual Live / Unlive toggle**.
5) Deliver **competitions** and **analysis** with evidence-based unavailable states.

**Status:** Implemented and verified for the import/schedule/live pipeline, competitions/embargo, offline recovery, reports, and **Guide04 confidence/reflection/checklist/EV**.

---

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
- Backend bootstrap environment is synced and backend restarted (seed does not recreate old owner).

### Evidence discipline (binding)

- The user-supplied password **must never appear** in plan/docs/source/tests/logs/screenshots.

### Policy alignment (implemented)

- Default staff rotation policy remains **16–64 chars**.
- Added an explicit **owner-only identity-change exception** allowing **min 8 chars** (authorized use only).
- Staff login payload validation/UI now consistently accept **min 8**.

### Verification performed

- Isolated focused tests passed (default-min16 behavior, reviewer denial, duplicate email collision atomicity, CAS winner behavior, and session fencing).
- Frontend build passes.
- Real browser login:
  - New owner login succeeds and redirects to Studio.
  - Previous email is rejected (401).
  - Same owner UUID verified.
  - Desktop (1920×800) + mobile (390×844) show **no horizontal overflow**.

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
- Unified importer/organiser exists for **PDF + Excel**.
- Immutable imported test publication exists.
- Scheduling and Live/Unlive gating exists.
- Competition leaderboard exists with **embargo** (no score/solutions/reports before end time).
- Offline draft recovery + sign-out guard exists.
- Results analytics workspace exists (guide-aligned registry + evidence-gated metrics).
- **Guide04 learner analytics addendum is implemented and verified**:
  - Pre-answer confidence (non-blocking, precommit semantics)
  - Post-result reflections + mistake-review checklist (private)
  - EV “what-if” calculator embedded in A44 evidence drawer
  - Canonical A41/A42/A43/A45/A50 semantics enforced

### Phase 3.3 checkpoint update (bounded security + verification) — COMPLETED

**Status:** ✅ COMPLETED for the bounded Phase 3.3 checkpoint (compatible updates + security assessment)

- **No claim** that frontend security is fully resolved.
- **No claim** that 500k capacity is qualified.

#### What was done

- **Compatible dependency updates** (no env/script/architecture changes):
  - `eslint` + `@eslint/js` updated to **9.39.5**
  - `postcss` updated to **8.5.30**
  - Frontend `yarn build` passes post-update.

- **Audit improvement with evidence**:
  - Before: **26 unique advisories / 299 dependency-path findings**
  - After: **25 unique advisories / 49 dependency-path findings**
  - Remaining paths: 3 low, 25 moderate, 21 high; remaining unique include 10 high.
  - Residual advisories are still heavily coupled to **deprecated CRA/react-scripts toolchain** and remain a **release blocker**.

- **Independent verification** (read-only owner Studio login + core UI after dependency updates):
  - Studio login succeeds (`abhishek@billpe.com`, password sourced from `ADMIN_PASSWORD` without printing).
  - Unified PDF/Excel importer UI renders.
  - Mobile/desktop responsive checks pass.
  - Networkidle-only harness timeouts were triaged as background/edge requests (e.g., RUM) and not blocking readiness.

- **Main post-update runtime checks** (authoritative, evidence-backed):
  - `/results/{id}` loads for the restricted QA attempt.
  - Reflection save works post-update.
  - A44 what-if calculator works post-update; for p=0.2 with +4/-1/0 rules returns **0 marks** (correct EV for those values).
  - Desktop 1920×800 and mobile 390×844 screenshots show `overflow=[]`.
  - Auth session returns HTTP 200; no runtime exceptions.
  - Evidence: `test_reports/iteration_73_verified.json`.

- **Docs & registers updated**:
  - `docs/GUIDE04_INTEGRATION_VERIFICATION.md`
  - `docs/FRONTEND_SECURITY_REMEDIATION.md`
  - `memory/PRD.md` continuation checkpoint + `memory/test_credentials.md` safe handling
  - `docs/packet1/REGRESSION_STATUS.json` updated to reflect that A01–A06 are **currently passing** in scoped test evidence; **capacity remains UNQUALIFIED**.

- **Cleanup completed**:
  - Removed restricted synthetic QA artifacts created solely for automation:
    - exactly **2 QA attempts**, **1 review**, **1 QA test set**, **1 QA session**
    - removed temporary scripts + browser state + downloaded QA report
  - Owner UUID/email and the **original READY unscheduled 75Q import** were preserved.

### P0 user bug — PDF import not extracting direct questions

> **“pdf se nahi le pa rha direct questions”** — Studio PDF upload/organiser was not producing usable extracted questions.

**Status:** ✅ COMPLETED

#### Root cause (reproduced on real provided Tejas200 PDFs)

- Real paper had **75 questions**, but the old PDF organiser miscounted:
  - **77** question anchors (minor false anchors)
  - **338** solution anchors because numbered **solution steps** (1., 2., 3., …) were being treated as new questions.
- This triggered the safety cap behavior and blocked the import.

#### Fixes (bounded, deterministic; no guesswork)

- **Explicit header precedence**: If a PDF contains explicit question headers (e.g., `Q12`, `Question 12`), those dominate; numbered solution steps/continuations are not promoted to new items.
- **Bare-number papers** remain supported when the paper truly has no explicit `Q/Question` prefixes.
- **Ambiguous mixed numbering is blocked** (fail closed): if a document mixes Q-prefixed headers with same-indent bare numbers that are not part of the explicit set, the organiser returns a clear error instead of silently dropping items.
- **Option-block selection fix**: On six questions (Q37/51/56/60/67/70), lettered A–D labels appeared in the stem/diagram, but the actual answer options were numeric 1–4.
  - The organiser now selects the **final ordered option block** (not the first incidental A–D labels).
  - Result: **all 60 MCQs preserve numeric (1–4) options** for this paper.
- **Text-first extraction (safe only)**: Plain ASCII, layout-faithful content may be flattened into typed text.
  - Math fonts, superscripts, Unicode notation, and figures retain **faithful PDF-region rendering** (`render_mode='source'`).
  - No OCR/scans claim.
- **Preview overlap fix**: fixed inherited fixed-height source-image buttons causing overlaps.
  - Verified containment + no overflow on desktop (1920×800) and mobile (390×844), including zoom dialog.

#### Verified outcome

- Actual browser upload produced a correct READY import:
  - **Import ID:** `2a830c16-2da1-5687-9d2e-18d3211236de`
  - **75 questions**, **0 issues**, **191 private source assets**
  - **All 75 literal keys** exactly match an **independent extraction** of the first-page key table.
  - Remains **UNSCHEDULED** and **NOT LIVE** (owner chooses the start date/time; nothing is auto-scheduled).
- Old unscheduled diagnostic import `047ee1d9-…` is superseded/hidden.
- Synthetic QA fixture used during development is removed; nothing remains live.

**Evidence:**
- `/app/docs/PDF_IMPORT_REPAIR.md`
- `/app/test_reports/iteration_67_verified.json`

**Explicit non-claim:** We do **not** claim a full student attempt/report was run on this newly uploaded, currently-unscheduled Tejas200 paper.

---

## Completed work (since the strategy-only phase) — UPDATED

### Portable strategy PDF

- `/app/frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf` published.

### Unified Importer + Organiser (PDF + Excel) — IMPLEMENTED; Excel verified

- Backend:
  - Importer API + immutable imported set publication
  - Sandbox supports `pdf` and `xlsx`
  - Excel organiser worker
  - Upload guard middleware (bounded multipart budgets + immutable import freeze)
- Frontend:
  - StudioImportHub + organiser detail view (preview → schedule → live/unlive)
  - Mobile overflow + toast positioning fixes
  - Studio primary CTA guides to importer; manual editor is secondary.

### Competitions + embargo — DONE + VERIFIED

- Competition hub + per-competition leaderboard.
- Ranking: first competition attempt per phone profile; equal-score ranks verified.
- Embargo: scores/solutions/reports/retries locked until competition end.

### Guide04 learner confidence + reflections/checklist + EV — DONE + VERIFIED

**Status:** ✅ COMPLETED end-to-end

**Frontend:**
- `PlayerConfidencePanel` integrated into `Player.js` (non-blocking; no attempt-flow delay).
- `ResultsReflectionStrip` integrated into per-question expanded Results view.
- `A44ExpectedValueCalculator` embedded inside the analytics evidence drawer.
- Responsive CSS added using existing tokens (no theme changes). Light/dark + mobile/desktop verified without overflow.

**Backend:**
- Analytics formulas and evidence gates aligned to canonical Guide04 + `analytics_registry.json`:
  - **A41**: calibration-by-bin requires ≥20 rated overall AND ≥10 items per displayed bin.
  - **A42**: binary Brier requires ≥20 rated binary items.
  - **A43**: low-confidence negative-mark exposure requires ≥10 rated; configurable threshold `c` default 0.20.
  - **A45**: labeled **WRONG** only ≥5; unlabeled wrong reported separately.
  - **A50**: deliberately unavailable without verified first-exposure tasks; review progress shown separately as a workflow indicator (not mastery).
- Review save is idempotent (`request_id`) + revision CAS (409 on conflict).
- Two-tab conflict behavior verified: second tab gets conflict and can reload saved state without losing local draft.

**User-visible behavior verified (real browser):**
- Confidence: normal answer with no rating; 0% and 100% ratings; clear; offline 10% draft saved+reload; submit.
- Results: reflection panel save+reload; offline save failure retains edits; retry works; CAS conflict shows error and “Reload saved version”.
- EV: probability p=0/0.2/1 works; correct expected marks and break-even probability; A43 threshold updates dynamically.
- Real PDF report download returns a true PDF (`%PDF` header) via the Results download button.

**Evidence:**
- `/app/test_reports/iteration_72.json` (Guide04 completion)
- `/app/test_reports/iteration_73_verified.json` (post-security-update re-verification)
- `tests/packet1`: **294 passed**
- Full suite log: `/app/test_reports/guide04_full_packet1.log`
- Frontend build: `/app/test_reports/frontend_security_build.log`

### Guide04 metric alignment correction (design + source-of-truth)

A major mismatch was found between the earlier confidence/reflection addendum and the canonical **Guide04 source text + registry**.

- A scoped correction addendum was produced and inserted without removing any existing guideline sections:
  - `/app/design_guidelines.md` includes `scoped_correction_addendum_guide04_metrics_alignment`

This plan treats the **Guide04 source + `backend/tejas/analytics_registry.json`** as canonical.

### Dependencies and advisories — UPDATED (bounded checkpoint)

- Backend: `pip-audit` 0 advisories; `pip check` passes.
- Frontend: compatible updates applied; build passes; audit improved materially.
  - Residual CRA/react-scripts transitive advisories remain a **release blocker**.
- Fonts: Google Fonts removed; local fonts bundled.

---

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

User stories:

1. Owner uploads PDFs privately.
2. Owner can alternatively upload Excel to import typed questions/options/answer/solution.
3. System pairs questions and solutions exactly and blocks on ambiguity.
4. Student can attempt (MCQ + numerical).
5. Accurate scoring.
6. Downloadable matched-solution PDF report.

**Status:** Excel end-to-end is verified. For the provided Tejas200 PDF pair, organisation, exact keys, private source assets and preview are verified; a student attempt/report on this newly unscheduled import remains pending its start window.

### Phase 2 — V1 App Development (build full product around proven core)

User stories:

1. Premium landing.
2. Browse sets.
3. Phone-only login.
4. Attempt loop.
5. Unified Studio importer/organiser (PDF + Excel) + schedule + live/unlive.
6. Competitions and leaderboards.
7. Evidence-based descriptive insights.
8. Guide04 learner analytics (confidence, reflections, checklists, EV tool).

**Status:** ✅ Achieved and verified for Phase-1 MVP scope.

### Phase 3 — Comprehensive testing, hardening, and regression — UPDATED

#### Step 1: Owner Studio credential update — ✅ COMPLETE

(Completed; see above.)

#### Step 2: P0 — Fix PDF import: “direct questions not extracted” — ✅ COMPLETE

(Completed; see above; do not alter the sensitive PDF numbering regex unless strictly necessary.)

#### Step 3: Guide04 confidence/reflection/checklist/EV implementation + canonical alignment — ✅ COMPLETE

- Integration complete (Player + Results + Analytics drawer)
- Canonical semantics applied and verified
- Offline retry + CAS conflict UX verified
- Competition embargo enforcement verified by regression tests (403)

#### Step 4: Deep testing (autonomous; both frontend + backend) — ✅ COMPLETE

- Backend: `tests/packet1` now **294 passed**.
- Frontend: real-browser + responsive checks verified (desktop 1920×800; mobile 390×844; light+dark; no overflow).

#### Step 5: Phase 3.3 compatible update + security assessment checkpoint — ✅ COMPLETE

- Compatible updates applied (eslint/@eslint/js/postcss), builds still pass.
- Audit improved (26/299 → 25/49), but **not clean**.
- Post-update runtime checks for reflection save + A44 calculator confirmed.
- Residual CRA advisories are explicitly documented with evidence.

#### Step 6: Frontend security full closure (CRA toolchain) — **NOT STARTED / REQUIRED (P1 release blocker)**

**Status:** NOT COMPLETE (release blocker)

**Required next work (separate, controlled packet):**

- Controlled migration away from deprecated CRA/react-scripts toolchain to a maintained build/dev-server tool (e.g., Vite/Rspack/Next-like static export), preserving:
  - existing routing, env contract, asset handling, PDF/source rendering, and styling tokens.
- Re-run:
  - `yarn audit` (must be clean or explicitly justified with minimised remaining surface)
  - build + full browser regression (Studio import, Player, Results, competitions, report download)
- Document dev-only vs prod-only runtime exposure, and ensure production serves static build artifacts rather than an exposed dev server.

#### Step 7: 500k qualification remains out of scope for Phase-1 “final product” claim

- Maintain explicit separation:
  - MVP correctness vs infrastructure qualification.
  - No “supported 500k” claim without load/fault/restore campaign.

**Capacity readiness assessment:** completed **as planning only** (equations/SLOs exist). The following remain **NOT IMPLEMENTED / NOT EXECUTED**:

- Distributed load-test harness (k6/locust) with realistic traffic mix.
- Dedicated staging/prod-like topology (multi-cell DB routing, quotas, queue budgets).
- Measured SLO evidence (p95/p99, error ppm, durability and integrity oracles).

**Important constraint:** Do not run high-scale stress tests against the shared preview environment.

---

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening

- Keep PDF-05 staged qualification path intact.
- No “500k proven” claims without OPS-R gates and measured evidence.

---

## 3) Next Actions

### A) Immediate (P1): Frontend security posture (CRA advisories) — PARTIALLY COMPLETE

Completed:
1) Captured/attached audit evidence and build logs.
2) Applied compatible low-risk updates; re-verified build and runtime flows.
3) Produced explicit residual-risk disposition (`docs/FRONTEND_SECURITY_REMEDIATION.md`).

Remaining:
4) Execute a **controlled CRA toolchain replacement** packet and re-audit until clean (or minimized and justified) with full regression.

### B) Capacity qualification readiness (P1) — PLANNING ONLY

Completed:
- Readiness assessment against existing workload equations/SLO documents; status remains UNQUALIFIED.

Remaining:
1) Prepare load-test harness + reporting template (k6/locust).
2) Stand up isolated staging topology + instrumentation.
3) Execute staged campaign (1k→10k→50k→100k→250k→500k) with fault injection + restore as per PDF-05.

---

## 4) Success Criteria

### Product-first owner flow success

- Owner can upload **PDF pair** and get a working organised test from the provided Tejas200 PDFs.
- Owner can upload **Excel** and get direct typed questions.
- Organisation → only start date/time → Live/Unlive.
- Students can attempt within scheduled window.
- Competitions and embargo behave correctly.
- Reports download correctly.

### Final-scope completion success (not 500k certification)

- Deep regression suite passes (backend + frontend where applicable).
- Real browser offline + report flows pass.
- PDF import works for at least the provided Tejas200 paper pair.
- Confidence/reflection flows work, are non-blocking, and correctly aligned to canonical Guide04 + registry (especially A41/A42/A43/A45/A50).
- Frontend dependency posture is **improved** and residual CRA risk is **explicitly documented** with scan evidence.

---

## Explicit Release Blockers (remain blockers until qualified)

- **Frontend dependency advisories** rooted in deprecated CRA/react-scripts toolchain until a controlled migration + re-audit is completed.
- **500,000 concurrent user qualification** until staged load/fault/restore campaign is executed with evidence.
- **PDF importer robustness** beyond the provided supported PDFs (no OCR/scans claim).
- 20×25k home-cell fleet and routing.
- Multi-AZ durability + failover + restore proofs.
- Full load + chaos + restore qualification campaign.
- Staff credential incident closure beyond the authorized owner update (MFA/step-up, etc.).
- Any unperformed mandatory WP/OPS-R gate (PDF-05 p65–68).
- Any historical “verified” claim that cannot be reproduced on current HEAD with attached evidence (must be reconciled before release messaging).
