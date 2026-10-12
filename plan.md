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
- **LATEST USER DIRECTIVE (architecture rulebook + 5L hardening)**:
  - Update the **rulebook** (architecture guidance) from the 5 PDFs.
  - Audit and close **code-level** architecture gaps to follow best practices for 5L concurrency.
  - **Infrastructure/DB admin/CI/CD/production provisioning is out-of-scope** for direct changes in this repo: produce a **reference architecture + sizing hypotheses + rollout runbooks** and implement **code-level scale enablers**.

### Capacity/claims stance (binding)

- We **do not claim** 5 lakh concurrency as “proven” without a measured load campaign (per PDF-05).
- We **do** implement (and test) correctness properties that are prerequisites for scale: idempotency, bounded hot paths, durable receipts, strict privacy, and async heavy work.

## Execution updates and capacity stance

- Backend modularized into bounded contexts (`auth`, `catalog`, `content`, `attempts`, `answers`, `packs`, `reports`, `scoring`, `jobs`, `corrections`) and hardened for correctness under retry/fault.
- Core extraction + 75-question workflow + scoring + PDF report generation implemented and verified.
- PDFs stored locally with SHA256 manifest:
  - `/app/docs/source_guides/manifest.json` + per-PDF `.txt` extraction for page-level referencing.
- **Capacity goal** remains: architect for 500,000+ concurrent from launch. This is **not a claim**, only an architectural intent; load tests + infra are external release gates.
- No environment variables or infrastructure settings modified.

### Latest approved changes and execution evidence

- **Student auth** remains phone-only (no OTP/password/email). Staff login remains secure.
- **Offline draft persistence** exists (`localStorage` drafts keyed by user + attempt) and prevents data loss on refresh; late/unacked drafts are disclosed in Results.
- **Report generation** is queued and downloadable privately.
- UI migrated to **matte maroon** with light/dark theme tokens and typography refresh:
  - `index.css` uses Figtree + Roboto Mono + shadcn tokens.
  - `App.css` migrated to semantic roles; legacy teal/blue literals mapped to maroon tokens.
  - `SetDetail.js` rebuilt with clearer preflight UX and device check hierarchy.
  - Build passes; screenshot regressions show no mobile overflow.

### Current work status (session continuation)

A. **Reproduce and fix the Player blocker** (P0) — ✅ **COMPLETED**

B. **Verify offline recovery + submission + versioned scoring + matched PDF** end-to-end (P1) — ✅ **COMPLETED**

C. **Polish navigation + Exam Details** on desktop/mobile (P1) — ✅ **COMPLETED**

D. **Withdraw only identified QA fixtures** and record evidence; separate readiness vs unverified concurrency (P2) — ✅ **COMPLETED**
- 50 positively identified QA sets soft-withdrawn via owner API.
- Original `tejas-paper-01` is unchanged (hash unchanged), still `review`, 75 questions; **no approved student paper published**.

E. **Architecture Alignment to PDFs + 5-lakh scale hardening** (P0/P1 mix)
- ✅ **COMPLETED (bounded application-hardening tranche + docs)**
- ❗ **NOT** full five-PDF program completion: remainder remains explicitly **NOT IMPLEMENTED / NOT PROVISIONED / NOT QUALIFIED** (see gap matrix).

**New findings from PDF-05 (79p v2) now binding for the rulebook**
- Proposed topology: **5 planes** and **20×25k “Home Cells”** (proposal, not proof).
- Baseline model: **35,000 live RPS**, **51,666.7 combined**, **2× envelope = 70,000 live + 33,333.3 telemetry = 103,333.3 combined**, pathological **125,000 live RPS**.
- Event overlays: **starts 4,166.7/s** (500k/120s), **submits 16,666.7/s** (500k/30s).

**Architecture/code gap audit → status after hardening**
- Inline grading in `finalize()` occurred on request path → ✅ **FIXED** (atomic seal + durable grading outbox + background grade job; Results can return 202 pending).
- Answer save retry semantics were request-id-only → ✅ **FIXED** (single-document command receipt: payload hash + monotonic server sequence + per-attempt cap).
- `start_key` idempotency not payload-scoped → ✅ **FIXED** (payload fingerprint check + durable **resume alias** binding; unique alias index).
- Excessive hydration/pack loading on some endpoints → ✅ **FIXED** (compact `history` and `visit` projections).
- Extraction/report shared same small worker capacity → ✅ **FIXED** (bounded **pilot lanes** by kind; not a worker fleet).
- Client retries fixed-interval and unbounded → ✅ **FIXED** (jitter/backoff + Retry-After support; Results polling for grading; ReportButton bounded jitter polling + explicit failed-job retry).
- JSON request risks at scale → ✅ **FIXED** (<=1MB JSON, max depth 40, reject duplicate keys + non-finite numbers).
- Staff auth throttle race and missing Retry-After → ✅ **FIXED** (atomic counter, accurate Retry-After for staff/phone; concurrent test: 8→5×401+3×429).
- Large portions of PDF-05 are **not implementable without infra** (cells, relational seal protocol, KMS/MFA PIN/SSO, CDN/WAF, multi-AZ durability proofs) → **UNCHANGED** as explicit release blockers.

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)

User stories:
1. As an owner, I can upload the questions+solutions PDFs and store them privately.
2. As a reviewer, I can define Q1–75 and bind each to an exact solution entry with source page refs.
3. As a student, I can start an attempt and answer SCQ + numerical (including 5-digit answers) without seeing keys/solutions.
4. As a student, I get correct scoring (+4/−1/0) and per-question review with the matched solution.
5. As a student, I can download a single PDF report containing score + every Q in attempt order + my response + correct answer + marks + matched solution.

Steps:

- **POC-1: Private storage + secure serving** (✅ IMPLEMENTED)
  - Platform object storage integration; no public URLs; backend proxies/serves assets.
  - Upload constraints: PDF validation, size and error messages.

- **POC-2: Deterministic content extraction + pairing scaffold** (✅ IMPLEMENTED)
  - Extraction/pairing pipeline built; reviewed content stored with per-question solution pairing.

- **POC-3: Attempt snapshot + scoring + deadline correctness** (✅ IMPLEMENTED + VERIFIED)
  - Attempt start snapshots content version and rules; server-time deadlines.
  - Incremental answer acknowledgement uses optimistic revisions + DB-time fence.
  - Late drafts remain client-side and are not scored.

- **POC-4: Results view model + PDF report generation** (✅ IMPLEMENTED + VERIFIED)
  - Results compute summary + per-question outcomes.
  - Report generation queued; stored privately; downloadable only by owning student.

Stop and fix until:
- (a) all 75 Q have 1:1 solution matches, (b) report PDF renders and downloads, (c) no key leakage during attempt.

### Phase 2 — V1 App Development (build full product around proven core)

User stories:
1. Visitor can understand practice loop via premium landing.
2. Visitor can browse published sets for JEE Main/BITSAT.
3. Student can sign in with **phone-number only**.
4. Student can complete full attempt with autosave + submit.
5. Reviewer can upload/review/approve/publish/withdraw with audit.

Steps:

- **Backend (FastAPI + Mongo)**
  - Keep bounded contexts intact.
  - Student APIs: catalogue, start/resume, save answer, submit, results, report job + download.
  - Staff APIs: Studio CRUD, review/approve, publish/withdraw, regrade job.

- **Frontend (React SPA)**
  - Keep existing IA and routes.
  - Matte maroon theme is default, with optional dark mode.
  - Player is “quiet workspace”; solutions only after submit.

### Phase 3 — Comprehensive testing, hardening, and regression

- Automated backend tests:
  - Auth/role checks; vault proxy; upload validation.
  - Attempt lifecycle: idempotent start/submit; deadline fence; answer conflicts.
  - Idempotency: body-bound receipts and replay semantics.
  - Async grading: seal→202 pending→ready, and outbox crash recovery.
  - Jobs: lease fencing, bounded attempts, no done-job reset.
  - JSON/body guardrails.
  - Throttling + accurate Retry-After.
- Frontend E2E:
  - Public → login → set detail → preflight → attempt → results (including **202 grading pending**) → report download.
  - Offline: pending drafts survive reconnect + refresh; late drafts disclosed.
- Security review:
  - No key leaks; strict concealment behavior (404 vs 403); rate limits.

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening (bounded tranche)

**Purpose**: Convert the 5 PDFs into a binding engineering rulebook, run a gap audit, implement the highest-risk **code-level** improvements in the current FastAPI+Mongo system, and produce a **reference infra plan** (doc-only) for the full PDF-05 topology.

#### Phase 4.1 — Rulebook & traceability (binding docs)

Deliverables — ✅ **COMPLETED**:
1. **Rulebook update**
   - `/app/docs/RULEBOOK_ARCHITECTURE_V5.md`
   - `/app/docs/GAP_MATRIX_PDF_TO_CODE.md`
   - `/app/docs/CAPACITY_AND_OPERATIONS.md`
   - `/app/docs/VERIFICATION_RECORD.md`
   - `/app/docs/TESTING_RUNBOOK.md`
   - Provenance: `/app/docs/source_guides/manifest.json` + extracted `.txt` pages.
2. **Scale readiness rubric**
   - Implemented/tested vs not implemented/blocked on infra/load.
3. **Capacity worksheet**
   - Baselines copied from PDF-05 and documented.

#### Phase 4.2 — Code-level scale enablers (in-scope, implement now)

Implemented — ✅ **COMPLETED**:

1. **Async grading outbox (remove inline grading on submit path)**
   - `finalize()` seals attempt atomically, sets `grading_status=queued`, and does **not** compute ledger on request path.
   - Results endpoint can return **202 grading pending** until ledger exists.
   - Grade job runs in dedicated pilot lane; maintenance recovers missed enqueue.

2. **Durable command receipt semantics (best-effort within Mongo single-document constraints)**
   - Answers store payload hash, accepted receipt, `server_seq` and a per-attempt command cap.
   - Exact-body retries are idempotent; mismatched body under same request_id conflicts.

3. **Scope `start_key` idempotency to payload + durable resume aliases**
   - Start payload fingerprint checked on replay.
   - If a start_key is used to resume an active attempt, the alias is persisted so future mismatched replays correctly 409.
   - Unique alias index prevents cross-attempt reuse.

4. **Hot-path query slimming**
   - Compact `history` and `visit` endpoints (no pack hydration, projections only).

5. **Isolated bounded job lanes (pilot bounds)**
   - Separate lanes for `grade`, `report`, `extract`, `regrade`.
   - Lease fencing, bounded retry attempts, `next_run_at` exponential backoff, and immutable per-lease PDF object paths.
   - Done-job retry cannot reset output; ReportButton explicitly calls `/jobs/{id}/retry` on failed jobs.

6. **Retry/backoff + Retry-After**
   - Server propagates Retry-After for 503/429 and respects HTTPException headers.
   - Frontend uses jittered backoff for load/flush/deadline confirmation.
   - Results UI shows pending grading state with manual refresh/retry.

7. **Authorized immutable derivative cache + preflight reuse**
   - Rendered crops cached by immutable keys (source digest + ref + scale + render version).
   - Preflight validates refs with cached metadata and avoids repeated object fetches.

8. **Mongo configuration honesty + bounds**
   - Bounded pool size and wait timeout.
   - Write concern requested as majority+j **but preview is standalone**; no multi-AZ durability claim.

9. **HTTP request-body guardrails**
   - JSON limits middleware: <=1MB, max depth 40, rejects duplicate keys and non-finite numbers.

10. **Staff/phone throttling correctness**
   - Staff login counter is atomic pre-hash; 5 attempts/window; accurate Retry-After.
   - Phone throttling includes accurate Retry-After.

#### Phase 4.3 — Reference infrastructure (doc-only, per PDF-05)

- Reference design documented — ✅ **COMPLETED (doc-only)**
  - edge CDN + authorization-aware delivery
  - WAF/rate limiting
  - stateless API fleet + separate worker fleet
  - home-cell partitioning (20×25k proposal)
  - multi-AZ durability + DR runbooks
  - load-test plan and fault matrix (required before capacity claims)

## 3) Next Actions

This plan checkpoint is a **bounded tranche complete**. Next actions are **explicitly Phase 5+** and remain release blockers until executed outside this repo.

### A) Verification packet & handoff (P1)
✅ Completed evidence packet exists:
- Backend: 27/27 checks (`/app/test_reports/v5_final_backend.log`).
- Fault tests executed individually (iteration 19). 
- JSON/throttle 6/6 (`/app/test_reports/v5_json_limits_final.log`) and post-cleanup 14/14 (`/app/test_reports/v5_post_cleanup_final.log`).
- Browser regressions (iterations 21–22) incl offline/reconnect, abort retry, confirm submit, **202 grading pending**, real PDF download, and failed PDF explicit retry.
- Main screenshots: session `20261012_094650` and `20261012_094751` (desktop/mobile overflow[] + dark header contrast).
- QA withdrawal: `/app/test_reports/qa_withdrawal.json`.

### B) Next tranche — “PDF-05 Full Home-Cell Program” (P0, OUTSIDE this repo’s provisioning)
- Provision relational home-cell writer topology, admission reservations, writer fencing/generation protocol.
- Implement explicit-commit + drain/watermark register semantics for official simulations.
- Build independent worker fleet + parser isolation sandbox.
- Add staff SSO/MFA, one-use transaction grants, signing KMS/HSM, Object Lock, private CDN.
- Execute staged load + DR qualification campaign and publish qualified envelope (not aspirational).

## 4) Success Criteria

✅ MVP correctness and UX (completed):
- Player unblocked: student can start and complete attempt in UI.
- Offline recovery: drafts persist; acknowledged responses scored; late drafts disclosed.
- Results + corrections: correct metrics; versioned scores and PDFs; no stale CTAs.
- Download: one private PDF report per attempt with matched solutions.
- Theme + UX: matte maroon applied; typography improved; navigation simple; no mobile overflow.
- Rulebook: architecture + scale + security guidance updated from all 5 PDFs, with traceability.
- Code-level scale hardening: async grading outbox, receipts/seq, scoped start idempotency (including resume aliases), slim hot paths, isolated job lanes, Retry-After + backoff, JSON limits, atomic throttling.
- QA closure: identified fixture sets withdrawn; original source paper unchanged and kept in review.

✅ Claims stance preserved:
- Scale claim: 500k concurrency remains **architectural intent only**, not proven without load tests and infra.

## Explicit Release Blockers (must remain stated as blockers, per PDFs)

Not implemented / not provisioned / not qualified in this repo:
- 20×25k **home-cell** fleet, thin router, allocator/trust plane separation.
- Multi-AZ relational acceptance/sealing protocol and durability proofs.
- Transactional admission reservations, writer fencing/generation epochs, explicit-commit + drain protocol.
- Separate worker fleet and sandboxed parsing/extraction.
- SSO+MFA+PIN step-up, one-use transaction grants, KMS/HSM signing, and full secrets rotation.
- CDN authorization-aware delivery for protected assets at terabyte-per-minute scale.
- WAF quota validation and hostile-traffic mixed tests.
- Full 40–60 analysis snapshot pipeline and cohort privacy gates at scale.
- Full load-test + chaos-test + restore-drill evidence package required for launch claims.

These remain documented and treated as launch gates, not silently “assumed.”
