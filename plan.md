# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, using authoritative guides + owner-supplied content, with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, explicit data ownership, durable async job boundaries for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrently active exam attempts** (not registered users).
  - This remains an **unverified architecture goal** until realistic **load + fault + restore** qualification and operator signoff is performed.
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

### LATEST delivered user priority (P0 — completed)

User required that the **exam section + upload/test organisation** be production-grade, and supplied chapter-wise PDFs.

**P0 requirement:** Build a **chapter-wise BITSAT exam experience** from the owner-supplied chapter books and publish it **Live now** with **1-year validity**.

- Inputs: **3 chapter-wise PDFs** (Physics, Chemistry, Mathematics)
- Output: **94 chapter tests** total (30 + 32 + 32), each:
  - **Exactly 50 questions**
  - **60 minutes** per attempt
  - **BITSAT marking:** +3 correct / −1 wrong / 0 unanswered
  - **Live now + validity 1 year** (availability window), independent from the 60-minute per-attempt timer
  - Immediate results after submission (no competition embargo)
- Content truth: these books contain **ANSWER KEYS ONLY** (no worked solutions). UI must disclose clearly; **no fabricated solutions**.
- Rendering truth: where typed/OCR extraction is unsafe for formulas/diagrams, **use original PDF image** regions (source-faithful) rather than guessing.
- Reliability rule: **each generated test must be independently rechecked** by a testing agent before it is published.

Design references:
- `/app/design_chapter_tests.md`
- `/app/docs/audit/2026-10-17/UX_AUDIT.md`
- `/app/design_exam_refinement.md`

### Auth requirements (non-negotiable)

- **Students**: phone-number only (**no OTP**, no password). This is a convenience profile, not verified phone ownership.
- **Staff/Owner**: secured separately.

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
  - **94 live tests / 4,700 questions** across Physics/Chemistry/Mathematics
  - Validity is set to 365 days, end-to-end exam flow exists.

### Baseline verification (read-only, before premium changes) — COMPLETED

- Baseline regression run recorded: `/app/test_reports/iteration_80.json`.
- **332 isolated tests PASSED** (packet1 suite scope at that checkpoint).
- **94 live chapter tests confirmed** and preserved.
- Visual check in preview:
  - Desktop 1920×800 and mobile 390×844: no horizontal overflow observed.

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
- Backend performance correctness:
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
- `/app/test_reports/refinement-owner-invariants.json` (hard invariant check)

### Testing and build evidence — UPDATED

- **Backend isolated regression**: `/app/test_reports/refinement-full-regression.log`
  - **342 passed**, 0 failed, 200 warnings.
- **Frontend production build**: `/app/test_reports/refinement-final-build.log` (compiled successfully).
- **UI visual verification**: desktop 1920×800 and mobile 390×844, light/dark, no overflow (captured via automation output during verification runs).

### Real attempt, offline and source evidence (critical)

Verified directly in real browser:
- Source canvas loads original pixels; **pan changes pixels**.
- Fit/Readable/Zoom/Fullscreen controls work.
- Keyboard shortcuts work when focus is on `BODY`.
- Offline: select option → UI shows **“Offline · 1 pending”** → reconnect → reload preserves answer.
- Failure mode (TEST ONLY): a browser route fault injects **503** for a source image → answering locks → **Try again** after removing fault unlocks answering.
  - This is a **mocked browser network fault**, not mocked application APIs.

### Results/PDF truth discipline (critical correction)

- **Superseded:** Any earlier acceptance of `iteration_83.json` claims about **2/150** submission and PDF. That report was marked with `verification_override: REJECTED_OVERCLAIM`.
- **Actual main re-run UI verification:**
  - QA87 attempt `52e598cc...` submitted via real UI: **two incorrect = −2/150**, 48 skipped.
  - Real downloaded PDF: **1,510,413 bytes**, **51 pages**, answer-keys header.
  - Saved at: `/app/test_reports/refinement-actual-qa-report.pdf`.
- Additional correctness signal:
  - QA85 (existing attempt) naturally ended by 60-minute deadline and showed **+3/150** (1 correct, 49 skipped), exercising server-side deadline finalization.

### Studio / owner verification (final)

- Owner login and Studio chapter book view verified.
- Owner preview verified:
  - Actual **Close** action
  - Q1 and Q50 assets load
  - **Zero** `/chapters/null/` asset requests after fix
  - Readable inline canvas enabled inside owner preview.

### Security posture snapshot (frontend) — UPDATED (still blocked)

- `yarn audit` remains: **49 vulnerable dependency paths** (25 unique advisories; 21 high severity paths).
- Several advisories originate from deprecated CRA/webpack dev toolchain dependencies.
- **Policy:** do **safe, compatible** upgrades only; do **not** force unsafe overrides.

Evidence:
- `/tmp/tejas-security-before.jsonl` copied to `/app/test_reports/refinement-dependency-audit.jsonl`
- `/app/test_reports/refinement-compatible-updates.log` contains `yarn outdated` snapshot

### Capacity snapshot (read-only) — UPDATED (still unqualified)

- Preview environment shows **~2 CPU quota** and **8 GiB memory cap** with colocated services.
- MongoDB is **standalone** (no replica set / multi-AZ proof).
- Capacity remains **UNQUALIFIED**.

Measured bounded smoke (NOT scale proof):
- `/app/test_reports/capacity_catalog_smoke.json`
  - 40/40 HTTP200, max 4 workers, max 5 rps
  - p50 **71.91ms**, p95 **107.89ms**, p99 **229.38ms**
  - Includes raw samples + timing method
  - Explicitly labeled **UNQUALIFIED_500K**

Canonical infra verdict:
- `/app/docs/strategy/INFRASTRUCTURE_CAPACITY_VERDICT.md`

### Incidents / hygiene notes (for release truth)

- Credential incident: test tooling leaked owner credential into artifacts earlier in the session; artifacts were redacted locally. **Rotation/revocation is recommended**, but not performed (access-impacting action).
- Synthetic test-data incident: a synthetic `Test Book` briefly appeared in preview DB; it was quarantined by exact fingerprint without touching the original 94. Root cause not proven; **do not claim pytest isolation failed**.

---

## 3) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

**Status:** Stable

- Existing PDF-pair + Excel flows stable.
- Chapter-book parser and APIs stable.
- Offline draft semantics and results/report flows exist.

### Phase 2 — V1 App Development (build full product around proven core)

**Status:** MVP exists; premium polish ✅ delivered; remaining hardening ongoing

- Chapter-wise exams are Live.
- Core attempt flows function.
- UI/UX upgraded significantly toward “premium” while preserving published content.

### Phase 3 — Comprehensive testing, hardening, and regression — UPDATED

#### Step 1: Owner Studio credential update — ✅ COMPLETE

#### Step 2: PDF-pair import repair — ✅ COMPLETE

#### Step 3: Guide04 analytics addendum — ✅ COMPLETE

#### Step 4: Deep testing (autonomous) — ✅ COMPLETE for the premium-refinement scope

Completed evidence includes:
- Production frontend build success.
- Safe isolated backend regression: **342 passing**.
- Real UI flows: preflight, player, offline, submit, results, PDF.
- Owner Studio: checklist + preview + Close + Q1/Q50 asset loading.

**Note:** this does **not** certify all historical flows, competitions, or arbitrary new content formats.

#### Step 5: Phase 3.3 compatible security checkpoint — ✅ COMPLETE (bounded), still a blocker overall

- Audit remains not clean.
- CRA toolchain advisories remain a release blocker until modernization path is proven.

---

## 4) NEW Phase — Premium UX + Capacity Strategy (CURRENT ACTIVE PHASE)

**Goal:** Convert the current MVP into a **premium test-series grade product** while producing an evidence-based capacity strategy and a reproducible load qualification harness.

### 4.1 Premium UX implementation (P0) — ✅ COMPLETED (premium exam refinement)

**Binding references:**
- `/app/docs/audit/2026-10-17/UX_AUDIT.md`
- `/app/design_exam_refinement.md`
- `/app/design_guidelines.md` (premium addendum)

Delivered (verified):
- /exams catalogue density + sticky filters
- Preflight copy truthfulness + mobile sticky CTA
- Player readable original-canvas controls + shortcuts + A–D strip
- Results sealed/key-only disclosures + review jump
- Studio diagnostics + readable owner preview + null-close fix

### 4.2 Frontend security posture (P1) — NOT COMPLETE (blocked)

Work done:
- Deep audit snapshot recorded and compatible updates reviewed.

Remaining:
- Controlled toolchain modernization (CRA → supported stack), with regression proof.
- Re-audit to materially reduce high-severity paths.

### 4.3 Capacity strategy + infra inventory (read-only) (P0/P1) — PARTIALLY COMPLETE (planning + bounded smoke only)

Completed:
- Read-only infra inventory and explicit **UNQUALIFIED_500K** verdict.
- Guarded, reproducible read-only smoke harness.
- Application-level hot-path improvements that reduce payload and remove truncation.

Remaining:
- True staged stateful load, burst, failure, restore qualification on representative infrastructure.

### 4.4 Release gates and truth discipline — IN PROGRESS

- Keep **capacity_qualification = UNQUALIFIED** until staged evidence exists.
- Keep CRA advisories as explicit release blockers.
- Maintain strict preservation of:
  - 94 live tests
  - 1-year validity windows
  - question/key pairing integrity
  - phone-only login contract

---

## 5) Next Actions (post-premium refinement)

### A) Security modernization (P0/P1)

- Produce a controlled CRA → supported toolchain migration plan + execution:
  - Preserve routing, shadcn/ui, env wiring, and current tests.
  - Re-run build + full regression + `yarn audit` and record delta.
  - Do not force unsafe resolutions.

### B) True 500k qualification work (P0)

- Build the real campaign (operator-owned infrastructure):
  - Dedicated topology (stateless API tier, asset tier, jobs tier, replicated DB)
  - Statefully simulate: login, preflight, start, answer writes, offline/reconnect, submit, grade, report.
  - Run staged: 1k → 10k → 50k → 100k → 250k → 500k.
  - Include bursts, failover, restore drills.
  - Record SLO evidence, offered vs admitted load, queue age, error budgets.

### C) Studio self-service expansion (P1)

- Improve owner-side validation without weakening publication discipline:
  - Surface missing/damaged formulas and ambiguous keys per question.
  - Provide “fix source and re-upload” guidance and diff awareness.
  - Keep “independent evidence” gating for new/unrecognised books.

### D) Evidence hygiene (P0)

- Credential rotation/revocation (access-impacting):
  - Recommended before wider release due to prior artifact leakage.
  - Requires explicit authorization.
- Prevent ad-hoc live DB writes in test tooling:
  - Enforce guardrails: all test inserts must occur only under the isolated Packet1 DB fixture.

---

## 6) Success Criteria

### Product-first owner flow success

- Upload via PDF-pair, Excel, and chapter-book modes remains stable.
- Deterministic organization, verifiable content, safe publication gating.
- Published content stays immutable for existing student attempts.

### Student exam section success

- Student sees `/exams` catalogue with subject filters and fast navigation.
- Can start/resume attempts with offline recovery.
- Gets immediate results after submit.
- Can download PDF report.
- No answer keys/solutions leak during active attempts.
- Mobile formula/source readability is usable and does not cause overflow.

### “World best” readiness (requires audit + evidence)

- Premium UX gap list closed via measurable acceptance criteria and screenshots.
- Hot-path SLOs met under staged workload in a representative environment.
- Observability in place (metrics + traces) enabling “no lag” validation.

---

## Explicit Release Blockers (remain blockers until qualified)

- **CRA/react-scripts dependency advisories** until controlled migration + re-audit (or proven mitigation via safe upgrades).
- **500,000 concurrent user qualification** until staged load/fault/restore campaign is executed with evidence.
- **Preview-infra is not representative**: 2 CPU quota / 8GiB cap / colocated services / standalone MongoDB do not prove fleet readiness.
- **PDF importer robustness** beyond the provided supported PDFs (no OCR/scans claim).
- Multi-AZ durability + failover + restore proofs (operator-owned).
- Full load + chaos + restore qualification campaign.
- New-book independent verification autonomy (still requires independent evidence; no fabricated approvals).
- Any unperformed mandatory WP/OPS-R gate (as referenced in strategy docs).
