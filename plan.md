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

### LATEST user priority (product-first execution) — CURRENT STATUS: COMPLETED (bounded product feature phase)

Deliver a simple unified owner workflow:

1) **One place** (Studio) to upload:
   - **Questions PDF + Solutions PDF**, OR
   - **Excel (.xlsx)** import for typed questions/options/answer/solution (to avoid image-only PDFs), including:
     - single workbook (Questions + Solutions), or
     - two workbooks / two sheets with deterministic pairing.
2) System auto-organises into a test draft with strict, auditable pairing (no guessing).
3) Only after organisation is complete, prompt owner **only for attempt start date/time** (IST).
4) Provide **manual Live / Unlive toggle**.
5) Deliver **world-class analysis** and **competitions** with evidence-based unavailable states.

**Implemented and verified in this phase** (does *not* imply whole-spec completion):

- Unified PDF + XLSX importer in Studio, templates + strict row errors.
- Sandbox isolation retained (**chroot + low UID + seccomp + resource caps**); PDF codec preload fix applied (no isolation weakening).
- Immutable imported test publication.
- Schedule start date/time UI + server gating.
- Live/Unlive toggle.
- Competitions hub + per-competition leaderboard.
- Competition embargo: scores/solutions/reports/retries locked until test window ends.
- Descriptive missed-topic priorities (evidence-based) added to results.

Implementation proceeds autonomously with sensible defaults—no routine questions—while preserving safety/precision/privacy invariants from the 5 PDFs.

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

- Isolated focused tests passed (including default-min16 behavior, reviewer denial, duplicate email collision atomicity, CAS winner behavior, and session fencing).
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

## Execution updates and capacity stance

- Backend modularized into bounded contexts (`auth`, `content`, `attempts`, `jobs`, `imports`, `competitions`, etc.).
- Core attempt loop + scoring + PDF report generation exists.
- Unified importer/organiser flow exists for PDF+Excel.
- Competition/leaderboard + embargo exists.
- Results analytics workspace added with guide04 evidence gating (partial availability by collected evidence).

---

## Completed work (since the strategy-only phase) — UPDATED

### Portable strategy PDF

- `/app/frontend/public/downloads/Tejas_10_Packet_Strategy_v1.0.pdf` published.

### Unified Importer + Organiser (PDF + Excel) — DONE + VERIFIED

- Backend:
  - Importer API + immutable imported set publication
  - Sandbox supports both `pdf` and `xlsx`
  - Excel organiser worker
  - Upload guard middleware (bounded multipart budgets + immutable import freeze)
- Frontend:
  - StudioImportHub + organiser detail view (preview → schedule → live/unlive)
  - Mobile overflow + toast positioning fixes

### Competitions + embargo — DONE + VERIFIED

- Competition hub + per-competition leaderboard.
- Ranking: first competition attempt per phone profile; equal-score ranks verified.
- Embargo: scores/solutions/reports/retries locked until competition end.

### Correctness defect repairs (A01–A06) — DONE + VERIFIED

- A01 retry alias durability fixed (`bind_retry_alias`).
- A02 publish CAS fixed with publication outbox (`publication_pending`) + idempotent archival.
- A03 concurrent edit lost-update fixed using `expected_revision` CAS.
- A04 audience fails closed.
- A05 queued job draining implemented.
- A06 extraction path no longer mutates academic destination; stages fenced proposal only.

### Results analytics + offline safety + typed math (bounded tranche) — DONE + VERIFIED

- Guide04 registry definitions generated with source hash: `/app/backend/tejas/analytics_registry.json`.
- Analytics computation implements only evidence-backed metrics; others show unavailable reasons.
- Offline drafts:
  - Profile-scoped draft recovery panel
  - Sign-out guard prevents accidental draft loss
  - Late/quarantined drafts can be exported/discarded without changing sealed scores
- Typed math options render with KaTeX and do not overflow mobile.

### Dependencies and advisories — UPDATED

- Backend: `pip-audit` now 0 advisories, 0 skipped; `pip check` passes.
- Frontend: advisory scan still reports vulnerabilities via tooling (yarn audit); remediation remains a release blocker.
- Fonts: external Google Fonts replaced with locally bundled font packages to eliminate browser-tool hangs and remove external runtime dependency.

### Testing and evidence — UPDATED

- Isolated suite: `tests/packet1` passes **232 tests** (warnings only).
- Real browser deep verification performed for:
  - Offline draft persistence + recovery
  - Sign-out guard keep/cancel flows
  - Analytics drillthrough to question evidence
  - Real PDF report download
- Importer/storage/report evidence:
  - `/app/docs/UNIFIED_IMPORTER_VERIFICATION.md`
  - `/app/test_reports/iteration_51_verified.json`

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

**Status:** achieved for bounded feature scope (verified).

### Phase 2 — V1 App Development (build full product around proven core)

User stories:

1. Premium landing.
2. Browse sets.
3. Phone-only login.
4. Attempt loop.
5. Unified Studio importer/organiser (PDF + Excel) + schedule + live/unlive.
6. Competitions and leaderboards.
7. Evidence-based descriptive insights.

**Status:** achieved for bounded feature scope (verified).

### Phase 3 — Comprehensive testing, hardening, and regression — UPDATED

#### Step 1: Owner Studio credential update — ✅ COMPLETE

- In-place owner record update (UUID preserved).
- Atomic email+hash+generation rotation.
- Owner staff session revocation only.
- Bootstrap sync + backend restart.
- Real browser verification + isolated tests.

#### Step 2: Continue deep-verification tranche (remaining)

- Frontend dependency remediation/disposition under Node 20 constraints.
- Expand analytics collectors only where strictly necessary (timing/cohort/etc.) — **do not fabricate**.
- Extend deep end-to-end tests to include:
  - PDF+Excel imports, attempt idempotency, offline recovery, embargo behavior, leaderboard, report downloads.

---

### Phase 4 — Architecture Alignment to PDFs + 5-lakh scale hardening

- Keep PDF-05 staged qualification path intact.
- No “500k proven” claims without OPS-R gates and measured evidence.

---

## 3) Next Actions

### A) Immediate: Post-credential-change validation (non-blocking confirmation)

- Keep monitoring auth/session fencing under real traffic.
- Ensure no synthetic QA fixtures appear in production lists.

### B) Resume final-scope deep verification

- Frontend dependency remediation/disposition and evidence.
- Maintain safety holds.
- Continue Packets 2–10 only after Packet 1 exit gates allow.

---

## 4) Success Criteria

### Product-first owner flow success — ✅ achieved for bounded feature phase

- Owner can upload PDFs or Excel, auto-organise, schedule start time only, Live/Unlive.
- Students can attempt within schedule and live window.
- Competitions exist with embargo until end.
- Offline drafts are recoverable and never silently overwrite sealed scores.

### Owner Studio credential change success — ✅ achieved

- Existing owner UUID retains ownership; only email+hash+generation changed.
- New email can log in successfully.
- Old email is rejected.
- Prior owner sessions revoked; student sessions unaffected.
- No password content appears in any artifact.

### Final-scope completion success (not 500k certification)

- Deep regression suite passes.
- Real browser offline + report flows pass.
- Frontend dependency posture is documented with explicit dispositions.

---

## Explicit Release Blockers (remain blockers until qualified)

- 20×25k home-cell fleet and routing.
- Multi-AZ durability + failover + restore proofs.
- Full load + chaos + restore qualification campaign.
- Frontend dependency advisories without explicit disposition.
- Staff credential incident closure beyond this authorized owner update (MFA/step-up, etc.).
- Any unperformed mandatory WP/OPS-R gate (PDF-05 p65–68).
