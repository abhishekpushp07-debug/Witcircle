# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

Deliver a premium landing page + working practice MVP for **JEE Main** and **BITSAT** students, built on the supplied PDFs as the base guide, with:

- **World-class engineering practices**: bounded contexts, strict API boundaries, vaulting/catalog separation, durable job queue for heavy work, immutable attempt snapshots.
- **Scale target**: architect for **500,000 (5 lakh) concurrent students**.
  - This remains an **unverified architecture goal** until realistic load tests + infra provisioning are performed.
  - The MVP must avoid synchronous heavy work (PDF generation, regrade, extraction) on request threads.
- **Core product guarantees**:
  - Exact **question ↔ matched solution pairing** (per question, per attempt).
  - **Single downloadable PDF report** per attempt (results + matched solutions).
  - **Offline answer recovery**: student drafts persist locally; server-acknowledged responses are scored.
  - **No key/solution leakage during an active attempt** (including via direct URL guessing).
- **Auth requirements (non-negotiable)**:
  - **Students**: phone-number only (no OTP, no password).
  - **Staff/Owner**: secure password-based auth, separate entrance and authorization checks.
- **Theme requirement (updated)**:
  - **Matte maroon** theme supersedes all teal requirements (primary `#5C0025`, hover `#4A001E`, focus/ring `#8B1D3D`, soft `#F6E9EE`).

## Execution updates and capacity change

- Core backend architecture already modularized into bounded contexts (`auth`, `catalog`, `content`, `attempts`, `answers`, `packs`, `reports`, `scoring`, `jobs`, `corrections`) to support scale and vaulting.
- Core extraction + 75-question workflow + scoring + PDF report generation have been implemented and validated.
- **Capacity goal** remains: architect for 500,000+ concurrent from launch. This is **not a claim**, only an architectural intent; infra + load tests remain external release gates.
- No environment variables or infrastructure settings will be modified in this phase.

### Latest approved changes and execution evidence

- Student auth is phone-only (no OTP/password/email). Staff login remains secure.
- Offline draft persistence exists (`localStorage` drafts keyed by user + attempt) and is designed to avoid data loss on refresh.
- Report generation is queued via `jobs.py` (durable job records; report download via job download endpoint).
- **Theme change approved**: switch from teal-blue to **matte maroon** across tokens.
  - Binding design spec updated in `/app/design_guidelines.md`.

### Current work status (session continuation)

User confirmed continuation priorities:

A. **Reproduce and fix the Player blocker** (P0) — **COMPLETED**

B. **Verify offline recovery + submission + versioned scoring + matched PDF** end-to-end (P1) — **COMPLETED**

C. **Polish navigation + Exam Details** on desktop/mobile without architecture changes (P1) — **IN PROGRESS**

D. **Withdraw only identified QA fixtures** and record evidence; separate readiness vs unverified concurrency (P2) — **PENDING**

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

User stories:
1. As an owner, I can upload the questions+solutions PDFs and store them privately.
2. As a reviewer, I can define Q1–75 and bind each to an exact solution entry with source page refs (no ambiguous matches).
3. As a student, I can start an attempt and answer SCQ + numerical (including 5-digit answers) without seeing keys/solutions.
4. As a student, I get correct scoring (+4/−1/0) and per-question review with the matched solution.
5. As a student, I can download a single PDF report containing score + every Q in attempt order + my response + correct answer + marks + matched solution.

Steps:

- **POC-1: Private storage + secure serving** (IMPLEMENTED)
  - Platform object storage integration; no public URLs; backend proxies/serves assets.
  - Upload constraints: PDF validation, size and error messages.

- **POC-2: Deterministic content extraction + pairing scaffold (no AI dependency)** (IMPLEMENTED)
  - Extraction/pairing pipeline built; reviewed content stored with per-question solution pairing.
  - Pairing rule: paper identity + question number, with reviewer gating.

- **POC-3: Attempt snapshot + scoring + deadline correctness** (IMPLEMENTED + VERIFIED)
  - Attempt start snapshots content version and rules; server-time deadlines.
  - Incremental answer acknowledgement endpoint uses optimistic revisions and DB-time deadline fencing.
  - Late drafts are retained client-side but are not scored.

- **POC-4: Results view model + PDF report generation** (IMPLEMENTED + VERIFIED)
  - Results compute summary + per-question outcomes.
  - Report generation is queued (`jobs.py`), stored privately, downloadable only by the owning student.

Stop and fix until:
- (a) all 75 Q have 1:1 solution matches, (b) report PDF renders and downloads, (c) no key leakage during attempt.

### Phase 2 — V1 App Development (build full product around proven core)

User stories:
1. As a visitor, I can view a premium landing page and understand practice → results → solutions → improve.
2. As a visitor, I can browse published sets for JEE Main/BITSAT without an account and see honest availability.
3. As a student, I can sign in with **phone-number only** and see a simple home + attempt history.
4. As a student, I can do a full-paper attempt with navigator, mark-for-review, clear response, autosave state, and submit confirmation.
5. As a reviewer, I can upload PDFs, review/correct extracted content with source-page evidence, approve/publish/withdraw sets with audit trail.

Steps (current MVP already has most of these; remaining work is stabilization/polish):

- **Backend (FastAPI + Mongo)**
  - Keep bounded contexts intact.
  - Student APIs: list published sets (public + authenticated “my sets”), start/resume attempt, save answer, submit, results, report job enqueue + download.
  - Staff APIs: Studio CRUD, review/approve, publish/withdraw, regrade job enqueue.

- **Frontend (React SPA)**
  - Keep existing information architecture:
    - Landing (public)
    - Explore sets (public)
    - Login (student phone-only) + Owner login (staff)
    - Student: Home, Set detail, Player, Results
    - Staff: Studio dashboard + set editor
  - Apply updated design tokens: **matte maroon** (supersedes teal-blue).
  - Player UX: quiet workspace, clear save state, robust navigator, submission confirmation, no solutions shown.
  - BITSAT: keep honest empty state if no published sets.

- **Publication gates**
  - Rights confirmation required before publish.
  - Block publish if missing any approved question/answer/solution pairing.
  - Preserve immutability: published content changes create new versions; attempts retain original snapshots.

Conclude Phase 2 only after:
- At least 1 complete end-to-end run: browse → login → set detail preflight → attempt → results → report generation → report download.

### Phase 3 — Comprehensive testing, hardening, and regression

User stories:
1. As a student, I never see solutions/keys during an active attempt.
2. As a student, refresh/reconnect doesn’t lose saved answers; timer/deadline stays correct.
3. As a reviewer, withdraw removes set for new attempts without altering past attempts.
4. As a student, my downloadable report is private and cannot be accessed by other students.
5. As an owner, I can see an audit trail for uploads, edits, publish/withdraw, scoring/report jobs.

Steps:
- Automated backend tests:
  - Auth/role checks; object storage proxy; upload validation.
  - Catalogue restriction logic: `audience=restricted` including allowed phones.
  - Attempt lifecycle: idempotent start/submit; deadline fence; answer write conflicts.
  - Scoring: MCQ + INTEGER; +4/−1/0; five-digit and signed integer acceptance.
  - Immutability: attempts are not mutated by later content edits.
- Frontend E2E tests (Playwright or existing screenshot/testing harness):
  - Public browse → student phone login → open set detail → device check → start attempt → answer a few questions → offline simulation → submit → results filters → report download.
- Security review:
  - No public file URLs; no keys/solutions in active attempt payload; strict CORS; basic rate limiting.
- Performance sanity:
  - Report generation uses job queue; retry works; large PDF handling within constraints.

## 3) Next Actions

**Continuation Phases (explicit priority order):**

### A) Reproduce + fix Player blocker / fixture access (P0) — COMPLETED
1. ✅ Reproduced iteration-10 reported issue and validated current behavior.
2. ✅ Verified access control correctness:
   - restricted fixture appears for authenticated allowed phone via `/api/my/sets` and `/api/my/sets/{id}`.
   - public `/api/sets/{id}` remains correctly blocked.
3. ✅ Confirmed SetDetail “Start Attempt” reaches `/preflight` then `/start` reliably.
4. ✅ Confirmed Player start-to-first-question and full submission works on desktop.

**Evidence**
- `/app/test_reports/iteration_11.json`.

### B) Offline recovery + submission + versioned scoring + matched PDF validation (P1) — COMPLETED
Scope covered:
1. ✅ Disconnect while answering:
   - drafts persist to localStorage;
   - periodic flush + on-online flush;
   - UI reflects pending vs saved.
2. ✅ Refresh/reload mid-attempt:
   - drafts survive refresh;
   - attempt reload merges acknowledged answers and retains unacknowledged drafts.
3. ✅ Conflict handling:
   - second tab can cause 409 conflict;
   - conflict UI + discard restores server truth while retaining local drafts until user decides.
4. ✅ Deadline/late behavior:
   - forced deadline expiry + reconnect;
   - late drafts retained but not accepted/scored;
   - Results shows clear disclosure for late/unacknowledged drafts.
   - Important schema note: timed duration uses **`rules.minutes`** (not a top-level `duration`).
5. ✅ Submission idempotency:
   - repeated submit returns stable receipt/attempt state.
6. ✅ Versioned scoring validation:
   - original score + corrected key score both supported;
   - Results UI does not keep stale score/report CTA when `score_version` changes or is invalid (AbortController + clearing old state).
7. ✅ PDF report proof:
   - report job queued and downloaded;
   - contains full attempt in order with matched solutions;
   - privacy enforced: other phone cannot access attempt/results/report.

**Key implementation hardening already applied (frontend correctness)**
- Results fetch uses AbortController and clears old data on `scoreVersion` change.
- Report download component is keyed per attempt+scoreVersion and guarded on unmount.
- `useAttempt` reconnect recovery loads attempt if missing then flushes; prevents initial-load race.

**Evidence**
- Offline/reload/conflict: `/app/test_reports/iteration_13.json`.
- Versioned scoring + report immutability + privacy: `/app/test_reports/iteration_14.json`.
- Timed late draft scenario (real browser run) includes attempt id `ce6d7a7e-0d8a-4c83-b9c2-b4e6f03ccaf3` and shows `?late=true` with disclosure; late-draft UI now has `data-testid="late-draft-notice"` for reliable QA.

### C) Matte maroon theme + navigation/Exam Details polish (P1) — IN PROGRESS
Goals (no architecture changes, no auth changes):
1. Apply matte maroon tokens in `/frontend/src/App.css` and `/frontend/src/index.css`.
2. Sweep and replace remaining teal/blue hard-codes using mapping in `/app/design_guidelines.md`.
3. Polish SetDetail (Exam Details): font sizing, spacing, CTA hierarchy, responsive layout (mobile-first clarity).
4. Navigation polish:
   - simplify top-nav labels;
   - consistent back links;
   - remove visual noise, keep “quiet workspace” feel.
5. Regression gates while polishing:
   - **must not** break phone-only login,
   - **must not** expose keys/solutions,
   - **must not** introduce synchronous heavy work.

Validation for Phase C:
- Desktop + mobile screenshots on Landing, Explore, SetDetail, Player, Results.
- Ensure no horizontal overflow on mobile.

### D) Withdraw QA fixtures + seal evidence (P2) — PENDING
1. Identify QA-only fixtures precisely (no accidental removal of real reviewed sets).
2. Withdraw or restrict them per policy.
3. Record evidence: what was withdrawn, why, and what remains published.
4. Update readiness notes clearly separating:
   - Architecture readiness (bounded contexts + job queue) vs
   - Proven scale (requires load test).

**Known fixture to withdraw**
- `qa-timed-browser-4f80a7eb-b74e-4b6d-8bdb-f586487ba564` (temporary restricted set created for timed offline test).

**Note on earlier false alarm**
- Iteration-15 “duration bug” was a test harness schema error; correct field is `rules.minutes`.

## 4) Success Criteria

- Player unblocked: a student can open a permitted published set and complete an attempt in the UI. ✅ (iteration_11)
- Offline recovery: refresh/disconnect does not lose drafts; server-acknowledged saves are consistent; late drafts are clearly disclosed and not scored. ✅ (iteration_13 + timed late draft proof)
- Results: correct metrics (marks, accuracy definition, skipped handling) and per-question matched solutions. ✅ baseline verified; ✅ versioned corrections validated (iteration_14)
- Download: one PDF per attempt containing the complete attempt in order with question + response + correct answer + marks + matched solution; private access enforced. ✅ (iteration_12/14)
- Landing + explore: honest availability, no fabricated claims; BITSAT empty state handled. ✅ baseline; **polish in progress**
- Reviewer gates: rights confirmation required; publish/withdraw + audit; past attempts unchanged by later edits. ✅ baseline; **fixture withdrawal pending**
- Theme: **matte maroon** applied consistently; typography/spacing polished; navigation simple and elegant. **IN PROGRESS (Phase C)**
- Capacity: plan explicitly states 500k concurrency is **architectural intent only**, not proven without load tests. ✅ maintained
