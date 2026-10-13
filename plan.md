# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, using the **5 provided PDFs** as the authoritative base guide, with:

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
   - **Excel (.xlsx)** import for typed questions/options/answer/solution (to avoid image-only PDFs), including:
     - single workbook (Questions + Solutions), or
     - two workbooks / two sheets with deterministic pairing.
2) System auto-organises into a test draft with strict, auditable pairing (no guessing).
3) Only after organisation is complete, prompt owner **only for attempt start date/time** (IST).
4) Provide **manual Live / Unlive toggle**.
5) Deliver **competitions** and **analysis** with evidence-based unavailable states.

**Status:** Implemented and verified.

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
- We do define a qualification path (PDF-05 staged load envelopes + explicit SLOs).

---

## Execution updates and current status

### What is working (verified)

- Backend modularized into bounded contexts (`auth`, `content`, `attempts`, `jobs`, `imports`, `competitions`, etc.).
- Unified importer/organiser exists for **PDF + Excel**.
- Immutable imported test publication exists.
- Scheduling and Live/Unlive gating exists.
- Competition leaderboard exists with **embargo** (no score/solutions/reports before end time).
- Offline draft recovery + sign-out guard exists.
- Results analytics workspace exists (guide-aligned registry + evidence-gated metrics).

### NEW P0 user bug (must fix now)

> **“pdf se nahi le pa rha direct questions”** — Studio PDF upload/organiser is not producing usable extracted questions.

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
- Synthetic QA fixture is hidden from normal lists.

**Evidence:**
- `/app/docs/PDF_IMPORT_REPAIR.md`
- `/app/test_reports/iteration_67_verified.json`
- Packet1 isolated suite: **257 passed** (0 failed, 0 xfail). Log: `/app/test_reports/pdf_fix_full_regression.log`

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

### Correctness defect repairs (A01–A06) — DONE + VERIFIED

- A01 retry alias durability.
- A02 publish CAS with publication outbox + idempotent archival.
- A03 concurrent edit lost-update fixed via `expected_revision` CAS.
- A04 audience fails closed.
- A05 queued job draining.
- A06 legacy extraction no longer mutates academic destination; stages fenced proposal only.

### Results analytics + offline safety + typed math — IMPLEMENTED and smoke-verified

- Guide04 registry definitions generated with source hash.
- Evidence-gated analytics: do not invent values when evidence is missing.
- Offline drafts:
  - Profile-scoped draft recovery panel
  - Sign-out guard prevents accidental draft loss
- Typed math options render with KaTeX and do not overflow mobile.

### Dependencies and advisories — UPDATED

- Backend: `pip-audit` now 0 advisories, 0 skipped; `pip check` passes.
- Frontend: advisory scan still reports vulnerabilities (CRA/react-scripts toolchain); remediation/disposition remains a release blocker.
- Fonts: Google Fonts removed; local fonts bundled to eliminate external font fetch stalls.

### Testing and evidence — UPDATED

- Isolated suite: `tests/packet1` passes **257 tests**.
- Real browser deep verification performed for:
  - Offline draft persistence + recovery
  - Sign-out guard keep/cancel flows
  - Analytics drillthrough to question evidence
  - Real PDF report download (existing test flows)
  - Real Tejas200 import preview: Q37 source/solution images (desktop+mobile), no overlap/overflow.
- Importer/storage/report evidence:
  - `/app/docs/UNIFIED_IMPORTER_VERIFICATION.md`
  - `/app/test_reports/iteration_51_verified.json`
  - `/app/docs/PDF_IMPORT_REPAIR.md`
  - `/app/test_reports/iteration_67_verified.json`

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

**Status:** ✅ Achieved for the majority of flows; Tejas200 PDF authoring is unblocked.

### Phase 3 — Comprehensive testing, hardening, and regression — UPDATED

#### Step 1: Owner Studio credential update — ✅ COMPLETE

(Completed; see above.)

#### Step 2: NEW P0 — Fix PDF import: “direct questions not extracted” — ✅ COMPLETE

**Goal:** PDF upload must produce a **usable organised test** from the real provided PDFs.

**Non-negotiables:**
- Keep sandbox isolation (chroot + low UID + seccomp + resource caps).
- No guessed answers/solutions.
- Preserve diagram/math fidelity via source regions, but also support **text-first extraction** when reliable.

**Delivered:**
- Real-paper reproduction + fix + browser verification, with independent key-table cross-check.
- Layout fidelity: plain typed only when safe; otherwise PDF regions.
- Mobile/desktop preview overlap fixed.

#### Step 3: Resume deferred items AFTER PDF import is fixed

- **Confidence/review analytics addendum implementation** (design is done; code is paused).
- **Frontend dependency remediation/disposition** (CRA toolchain advisories).
- **Scale qualification work (PDF-05)** — not claimed complete.
- **Run a full student attempt + PDF report on the newly imported Tejas200 paper** AFTER the owner schedules it (no auto schedule).

---

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening

- Keep PDF-05 staged qualification path intact.
- No “500k proven” claims without OPS-R gates and measured evidence.

---

## 3) Next Actions

### A) Immediate (P0): PDF import bug

✅ Completed.

### B) After P0 PDF fix (current mission)

1) **Run end-to-end attempt + report for the real Tejas200 import AFTER scheduling**
   - Owner sets start date/time.
   - Verify student attempt within window.
   - Verify post-window embargo release and report download.

2) **Frontend dependency advisories**
   - Document dev-only vs prod-impacting.
   - Decide and execute migration off CRA/react-scripts or apply vetted mitigations.

3) **Evidence-backed analytics collectors only**
   - Add collectors only where guide requirements are met; keep unavailable states elsewhere.

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

- Deep regression suite passes.
- Real browser offline + report flows pass.
- PDF import works for at least the provided Tejas200 paper pair.
- Frontend dependency posture is documented with explicit dispositions.

---

## Explicit Release Blockers (remain blockers until qualified)

- **PDF importer robustness** beyond the provided supported PDFs (no OCR/scans claim).
- 20×25k home-cell fleet and routing.
- Multi-AZ durability + failover + restore proofs.
- Full load + chaos + restore qualification campaign.
- Frontend dependency advisories without explicit disposition.
- Staff credential incident closure beyond the authorized owner update (MFA/step-up, etc.).
- Any unperformed mandatory WP/OPS-R gate (PDF-05 p65–68).
