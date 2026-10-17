# jeemains.ai — Phase 1 Execution Plan (Premium Practice MVP + Scale Strategy)

## 1) Objectives

Deliver a premium, simple-to-use practice platform for **JEE Main**, **BITSAT**, and **COMEDK** students with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, explicit data ownership, durable async job boundaries for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrently active exam attempts** (not registered users).
  - This remains an **unverified architecture goal** until realistic **load + fault + restore** qualification and operator signoff is performed.
  - “No lagging” is defined via measurable SLOs (latency, error rate, durability, backlog age), not an unprovable “0 lag” claim.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt) **when solutions exist**.
  - **Single downloadable PDF report** per attempt (results + solutions when available, or answer keys when keys-only content is supplied).
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored; late/unacknowledged drafts are disclosed.
  - **No key/solution leakage during an active attempt** (including via direct URL guessing).

### Branding + positioning updates (confirmed)

- Platform name and branding: **jeemains.ai**
- Pre-login landing: premium posters + strong message **“100% FREE for all students”**.
- Marketing copy requested by user:
  - “AI based PYQ analysed prediction papers…”
  - “60 out of 75 questions in JEE Main 2027 … will have same core concept…”
  - “120 questions or more in BITSAT 2027 … will have same core concept…”

**Truth / compliance constraint (non-negotiable):** the above counts cannot be published as guaranteed outcomes unless backed by verifiable analysis evidence. The landing presents these as **aspirational preparation targets** and only claims “PYQ-analysed” where actual analysis exists.

### Binding communication preference (critical)

- **Do not ask the user for interim review** before “final product”.
- **No routine confirmations/menus** asking the user to pick next features.
- Progress updates may be informational, but **not approval checkpoints**.
- Only **critical, irreversible, access-impacting actions** (e.g., staff credential rotation + session revocation) may require a single explicit authorization.

### UPDATED USER CHECKPOINT (current instruction) — IMPLEMENTATION AUTHORIZED (no routine approvals)

User explicitly authorized implementation and deep testing:

- “Yes and check with an eye of world best programmer and tester”
- “Yes. Make it the world best”
- “But you can always check the infra if its capable if its best”
- “In depth like world best”
- “You need to be world best. Always”

**This checkpoint authorizes:**
- UI/UX polish per `/app/docs/audit/2026-10-17/UX_AUDIT.md`.
- Implementation of premium catalogue density, player readability controls, preflight copy corrections, results disclosure clarity, and owner diagnostics.
- Deep autonomous testing after each meaningful change.
- Read-only infra inventory + capacity strategy + reproducible load harness creation.

**This checkpoint forbids:**
- Any change that mutates the already-published chapter tests’ content/validity windows.
- Infrastructure provisioning/production changes inside this session.
- “500k qualified” claims without staged evidence.
- Large load campaigns against shared preview.

### NEW USER REQUIREMENTS (confirmed) — General uploads + deep analytics + AI solutions + simplified navigation

These supersede earlier assumptions that **every** new upload must become a 50Q/60min/+3/-1/1-year test.

**User requirement (verbatim intent):**
- “Mai PDF upload kru aur PDF se marking scheme utha le system. Na samjh aaye toh puche mujhse.”

**New requirements:**
1. **Admin upload → automatic test creation → automatic Live (only if safe)**
   - Accept **PDF, Excel, Word** sources.
   - System should **infer test structure and rules** (duration, marking scheme, sections, question count) from the document instructions.
   - If rules are ambiguous or missing, the Studio must **ask for clarification** (single-shot targeted form; no endless back-and-forth).
   - Only sets that pass verification become **Live automatically**.
   - Any **missing keys, broken formulas, doubtful pairing** → that specific test stays **private**, with explicit issue list.

2. **Deep results analysis + graphs (world-class)**
   - Results must include **rank + percentile** for the relevant cohort (same test/version/time window), plus graphs.
   - Per-question stats: correct/wrong/skipped %, option distribution.
   - Subject/topic graphs and score distribution.
   - Attempt history browsing: chapter/mock filters, per-exam scoping.

3. **AI-generated answers + stepwise solutions when keys aren’t provided**
   - If the upload has **no supplied keys/solutions**, platform should generate **answers + detailed stepwise solutions** automatically.
   - **Truth constraints**:
     - Generated content must be labeled **AI-generated** with provenance.
     - Must not be presented as “supplied answer key”.
     - Must include uncertainty handling; ambiguous questions must be blocked or flagged.
   - “10 marks stepwise solution” is interpreted as **explanation depth**, not changing scoring.
   - Must **not** change sealed grades of old attempts; solution versioning must not rewrite history.

4. **Predicted rank “as per 2026 JEE Mains”**
   - Requires verified public data sources + calibration.
   - Must be shown as an **estimate range** with explicit uncertainty and disclaimers.
   - No fabricated mapping or arbitrary conversion from chapter test scores to AIR.

5. **Simple navigation (highest UI priority before expensive AI generation)**
   - Remove **“My Practice”** from header.
   - After login → **Home**.
   - Home shows **three big exam cards**: **JEE Main**, **BITSAT**, **COMEDK**.
   - Clicking an exam opens **Exam Hub** with exactly three cards:
     - **Mock Tests**
     - **Chapter-wise**
     - **Results**
   - Mock Tests lists only **live full-length mocks** for that selected exam.
   - Chapter-wise shows selected exam → subject → chapter tests.
   - Results shows previous attempts for that selected exam with mock/chapter filters, deep analysis and solutions.

6. **Player source default mode fix (explicit bug)**
   - Source images must default to **FIT** for every question.
   - Switching questions (Next/Previous/jump) must **not carry forward** “Readable” as the default.
   - Readable/Zoom remains an optional per-question action; safe controls retained.

**Open gating (not yet implemented):**
- AI provider/model is now chosen as **OpenAI Astra**, with exact model **`gpt-6-astra`**; application runtime support is **UNVERIFIED** (no silent model substitution).
- Use of real “2026 JEE Mains” prediction requires explicit data source selection and calibration plan.

---

## 2) Execution updates and current status

### What is working (verified on current HEAD)

- Backend modularized into bounded contexts (`auth`, `content`, `attempts`, `jobs`, `imports`, `competitions`, `reviews`, `analytics`, `chapter_books`, etc.).
- Unified importer/organiser exists for **PDF pair** and **Excel** (≤300 questions/import).
- Immutable imported set publication exists.
- Scheduling and Live/Unlive gating exists.
- Competition leaderboard exists with embargo.
- Offline draft recovery + sign-out guard exists.
- Results analytics workspace exists (guide-aligned registry + evidence-gated metrics).
- Chapter-book pipeline exists:
  - **94 live tests / 4,700 questions** across Physics/Chemistry/Mathematics (currently BITSAT content)
  - Validity is set to 365 days, end-to-end exam flow exists.

### Baseline verification (read-only, before premium changes) — COMPLETED

- Baseline regression run recorded: `/app/test_reports/iteration_80.json`.
- **332 isolated tests PASSED** (packet1 suite scope at that checkpoint).
- **94 live chapter tests confirmed** and preserved.

**Important correction to earlier testing notes:**
- Prior test-agent claim that student flow is blocked by OTP is **rejected** because the product contract and current code implement **no OTP** (`/api/auth/phone` creates a session directly).

### FINAL DELIVERY CHECKPOINT — Premium exam refinement + local performance/readiness audit — ✅ COMPLETED

This bounded phase is complete. It **does not** mark overall product/security/500k scale as complete.

**Implemented scope (delivered):**
- Catalogue: compact **chapter rows**, **sticky filters**, subject counts/search/reset, clearer “answer keys only” disclosure.
- Player: readable **original source canvas** (Fit/Readable/Zoom/Pan/Fullscreen), safe desktop shortcuts, and a clear **A–D** option strip aligned to original images.
- Preflight: honest copy + scoped disclosure.
- Results: sealed-answer notice, key-only disclosure, review jump.
- Studio: diagnostics checklist, readable owner preview, fixed `/chapters/null/...` requests on close, improved self-service clarity.
- Backend correctness/perf:
  - Studio metadata projection: **97.1% less BSON** transferred for chapter listings.
  - Chapter exams list attempt-history correctness: indexed per-set aggregation (no arbitrary 200-row truncate).
  - Preflight source validation: request-local dedup of identical refs (no cross-request cache).

**Final invariants verified (must remain true):**
- Owner chapter catalogue remains exactly **94 published live chapters / 4,700 questions**.
- All chapters are exactly **50 questions**, numbered 1..50.
- Rules are unchanged: **60 minutes**, **+3 / −1 / 0**.
- Validity windows remain exactly **365 days**.
- Independent evidence flags remain present.

Evidence:
- `/app/test_reports/refinement-owner-invariants.json`

### FINAL PHASE CHECKPOINT — Simple exam navigation + jeemains.ai free landing + Fit-default — ✅ COMPLETED

This bounded phase is complete. It **does not** mark AI publishing, deep cohort analytics, security remediation, or 500k qualification as complete.

**Implemented scope (delivered):**
- Brand + navigation:
  - Pre-login landing: **100% free** hero + student pass + separate exam posters.
  - Post-login: Home has exactly three cards (**JEE Main / BITSAT / COMEDK**).
  - Each exam hub has exactly three cards (**Mock Tests / Chapter-wise / Results**).
  - Header no longer shows **My Practice**; staff + saved drafts remain in account menu.
  - Legacy `/exams` route redirects to the new card-driven exam flow.
- Exam scoping:
  - Two authenticated navigation endpoints:
    - `GET /api/exam-navigation/{slug}/catalogue`
    - `GET /api/exam-navigation/{slug}/history`
  - Server-side audience/QA/expiry filters **before pagination**.
  - Mock classification is explicit (`test_kind='mock'` or `full_length=true`) — never inferred from title/length.
  - Attempt snapshots now store `test_kind`.
  - Supporting index `exam_attempt_history` added.
- Player source bug fix:
  - Source starts in **FIT** mode and resets to FIT on **initial load, Next, Previous, jump, and refresh**.
  - Optional Readable/zoom/pan remains.
  - FIT frame height uses the original image aspect ratio to reduce blank space, improving mobile usability.
- Report cache / branding:
  - Report payload includes `template_version='jeemains-ai-v1'` so a post-rebrand report does not silently reuse pre-rebrand cached renders.
  - PDF/report header now uses **JEEMAINS.AI** branding.
- Marketing truth discipline:
  - “60/75 (JEE Main 2027)” and “120+ (BITSAT 2027)” appear as **aspirational targets with prominent disclaimers**, not guarantees.
  - AI/PYQ features are clearly labeled **in development**, not delivered.

**Canonical evidence:**
- `/app/docs/SIMPLE_NAVIGATION_RELEASE.md`
- PRD checkpoint section updated near top of `/app/memory/PRD.md`

**Content availability (truthful UI):**
- Current non-QA published content is still **only** the **94 BITSAT chapter tests**.
- There are currently **no** published full mocks and **no** JEE Main/COMEDK sets in the real catalogue.
- These sections intentionally show **honest empty states**.

### Testing and build evidence — UPDATED

- **Backend isolated regression**: `/app/test_reports/navigation-final-regression.log`
  - **368 passed**, 0 failed, 232 warnings.
  - (This includes contract-evidence maintenance: operation catalogue updated to 75 routes after adding the two new endpoints.)
- **Frontend production build**: `/app/test_reports/navigation-build.log` (compiled successfully).
- **UI real-browser suites**: `/app/test_reports/navigation-ui-verified/`
  - 10/10 passed, 22 screenshots, 0 overflow offenders, 1 real 51-page branded PDF.
  - Verified: **32 Chemistry tests** pagination (12+12+8), Fit reset behavior across multiple transitions, history filters, BITSAT-only scoping.
- **Owner invariants re-verified**: `/app/test_reports/navigation-owner-invariants.json`

### Results/PDF truth discipline (critical)

- Earlier report `iteration_83.json` contained overclaims; it is explicitly marked `verification_override: REJECTED_OVERCLAIM`.
- Several other historical reports (87–90) were corrected with `main_verification_override` notes where they contained scope mismatch or invalid claims; canonical evidence is in the final release docs.

### Security posture snapshot (frontend) — UPDATED (still blocked)

- `yarn audit` remains: **49 vulnerable dependency paths** (25 unique advisories; 21 high severity paths).
- CRA/webpack toolchain advisories remain unresolved.

Evidence:
- `/app/test_reports/refinement-dependency-audit.jsonl`
- `/app/test_reports/refinement-compatible-updates.log`

### Capacity snapshot (read-only) — UPDATED (still unqualified)

- Preview environment shows **~2 CPU quota** and **8 GiB memory cap** with colocated services.
- MongoDB is **standalone** (no replica set / multi-AZ proof).
- Capacity remains **UNQUALIFIED**.

Canonical infra verdict:
- `/app/docs/strategy/INFRASTRUCTURE_CAPACITY_VERDICT.md`

---

## 3) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

**Status:** Stable

- Existing PDF-pair + Excel flows stable.
- Chapter-book parser and APIs stable.
- Offline draft semantics and results/report flows exist.

### Phase 2 — V1 App Development (build full product around proven core)

**Status:** MVP exists; premium polish ✅ delivered; simple navigation + brand + FIT default ✅ delivered

- Chapter-wise BITSAT tests are Live.
- Core attempt flows function.
- UI/UX upgraded significantly toward “premium” while preserving published content.
- Navigation is now exam-first and card-driven.

### Phase 3 — Comprehensive testing, hardening, and regression — UPDATED

#### Step 1: Owner Studio credential update — ✅ COMPLETE

#### Step 2: PDF-pair import repair — ✅ COMPLETE

#### Step 3: Guide04 analytics addendum — ✅ COMPLETE

#### Step 4: Deep testing (autonomous) — ✅ COMPLETE for premium-refinement + simple-navigation scope

Completed evidence includes:
- Production frontend build success.
- Safe isolated backend regression: **368 passing** (latest).
- Real UI flows: login, navigation, preflight, player, offline, submit, results, PDF.

**Note:** this does **not** certify all historical flows, competitions, or arbitrary new content formats.

#### Step 5: Security checkpoint — NOT COMPLETE (blocked)

- CRA toolchain advisories remain a release blocker.

---

## 4) NEW Phase — Upload→Auto-Live + Deep Results + AI Solutions (NEXT)

**Goal:** make Studio fully self-service for new uploads, deliver world-class analytics and solution quality, and then qualify infrastructure and security.

### 4.0 P0: Simple navigation overhaul + Player FIT default — ✅ COMPLETE

Delivered and verified.

### 4.0.1 P0: Pre-login landing page for jeemains.ai — ✅ COMPLETE

Delivered and verified (with disclaimers and “in development” disclosures).

### 4.1 P0: Admin upload → automatic test creation → safe auto-Live (NOT STARTED)

**Key change:** stop forcing default 50Q/60min/+3/-1/1-year on all uploads.

**Pipeline design:**
1. **Source ingestion**
   - Support: PDF, Excel, Word.
   - Store source, compute SHA, create immutable “source record”.

2. **Rule inference engine**
   - Parse instructions pages/headers (e.g., “Time: 180 minutes”, “+4/-1”).
   - Detect sections (Physics/Chem/Math, etc.), question numbering patterns.
   - Produce an inference report with confidence + evidence anchors.

3. **Clarification prompt (only if ambiguous)**
   - Minimal Studio form only for missing fields: duration, correct/wrong, question count policy, section weights.
   - Owner decision becomes part of an immutable “rules decision” record.

4. **Organisation + verification**
   - Exact question identification and pairing.
   - If supplied keys exist: dual extraction checks must agree.
   - Formula safety: use original crops where typed extraction unsafe.

5. **Auto-Live gating**
   - Only sets with: complete question structure + valid rules + (supplied keys OR AI-generated keys flagged) + safe source refs become eligible.
   - Partial failures: only affected sets stay private; the rest can go Live.

**Non-negotiables:**
- Never guess missing keys as “supplied”.
- Never publish a set with unverified ambiguous key pairing.
- Preserve existing 94 published tests unchanged.

### 4.2 P0/P1: AI-generated answers + stepwise solutions (OpenAI Astra) (NOT STARTED)

**User decision (locked):** **OpenAI Astra**

**Exact chosen model:** `gpt-6-astra`

**Critical constraint:** App runtime access to Astra via managed integration is **UNVERIFIED**.

**Implementation plan (bounded, safe):**
1. **Provider canary**
   - Add a minimal backend canary job that calls the existing integrations path and asserts the exact model `gpt-6-astra` is being used.
   - Fail closed if the model is unavailable; do not silently substitute.

2. **Data model + provenance**
   - `solution_provider` per question: `supplied_key`, `supplied_solution`, `ai_generated`, `none`.
   - `solution_version` + `generated_at` stored per published set version.
   - Never rewrite sealed attempt grades.

3. **Generation jobs**
   - Durable async jobs: rule-extract, question-solve, independent recheck (same model with blind prompt), deterministic validation.
   - If uncertain/disagree: mark `needs_review` and keep the set private.

4. **UX truth labels**
   - UI labels AI-generated solutions and status: `verified`, `needs_review`.

5. **No bulk backfill**
   - Start with small canary batches only; no automatic 4,700-question backfill.

### 4.3 P0: Deep results analysis with cohort rank/percentile + graphs (NOT STARTED)

Deliver:
- Rank + percentile for same set/version cohort.
- Participant counts + status (provisional/final).
- Per-question analytics:
  - correct/wrong/skipped %
  - option distribution (A/B/C/D)
  - time spent buckets (if available)
- Subject/topic breakdown and score distribution graphs.

**Data model:**
- Aggregations keyed by `{set_id, version, window}`.
- Store per-question response counts in an analytics collection with periodic backfill.

**Performance:**
- Updates must be incremental and cheap. Avoid full rescans per result view.

### 4.4 P1/P2: Predicted rank “as per 2026 JEE Mains” (NOT STARTED)

**Reality constraint:** cannot be done honestly without verified datasets.

**Plan:**
- Add Prediction panel only after:
  - dataset ingestion,
  - calibration,
  - error bounds,
  - explicit disclaimers.

---

## 5) Next Actions (updated)

### A) ✅ COMPLETE: Brand rename + landing posters + simple navigation

- Brand identity updated to **jeemains.ai** (UI title/meta/branding + PDF/report branding).
- Pre-login landing: “100% FREE for all students” + premium posters + disclaimers.
- Home (3 exam cards) → Exam Hub (3 cards).
- Removed “My Practice” from header.
- Enforced exam scoping: BITSAT chapters do not appear under JEE/COMEDK.
- Fixed Player source mode default to **FIT** on every question change.

### B) P0: Upload→Auto-Live inference pipeline

- Build rule inference report + evidence anchors.
- Build single-shot clarification form.
- Build safe auto-Live gating.
- Add Word ingestion.

### C) P0/P1: OpenAI Astra solutions (bounded canary first)

- Verify runtime support for `gpt-6-astra` (no silent model substitution).
- Build durable generation + blind recheck + deterministic validation.
- Implement UI labeling and versioning; never rewrite sealed grades.

### D) P0: Deep results analytics + graphs

- Implement aggregation + caching.
- Add rank/percentile + question-level correctness/option distribution.
- Render graphs and drilldown per exam.

### E) Capacity and security remain explicit blockers (P0)

- Full 500k stateful qualification on representative infra.
- CRA toolchain modernization.

---

## 6) Success Criteria

### Owner / Studio success

- Uploads can become Live with minimal manual work.
- System infers rules; only asks when ambiguous.
- Any failed extraction/verification blocks only the affected tests.
- AI-generated answers/solutions are clearly labeled, reviewed, and never misrepresented.

### Student success

- Simple navigation: **Login → Home (JEE/BITSAT/COMEDK) → Exam Hub (Mock/Chapter/Results)**.
- Player defaults to **FIT** every time; readable/zoom is optional.
- Deep results: rank/percentile, question-wise stats, graphs.
- Immediate post-exam results + analysis.
- Landing clearly communicates **100% FREE** and exam focus.

### Engineering success

- No regressions to existing 94 live tests.
- Measured and reproducible analytics performance.
- AI generation is bounded, versioned, and provenance-labelled; **no silent substitution** of chosen model.
- Capacity remains truthfully labeled until dedicated qualification is complete.

---

## Explicit Release Blockers (remain blockers until qualified)

- **CRA/react-scripts dependency advisories** until controlled migration + re-audit.
- **500,000 concurrent user qualification** until staged load/fault/restore campaign is executed with evidence.
- **Preview-infra is not representative**: 2 CPU quota / 8GiB cap / colocated services / standalone MongoDB do not prove fleet readiness.
- **OpenAI Astra runtime availability** must be verified via a minimal canary; no silent model substitution.
- **AI-generated solutions** cannot be treated as “supplied keys”; must remain provenance-labeled with uncertainty and review gates.
- **Predicted 2026 JEE Mains rank** cannot be shown as authoritative without verified datasets + calibration + error bounds.
- Any unperformed mandatory WP/OPS-R gate (as referenced in strategy docs).
