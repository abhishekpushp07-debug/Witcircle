# Tejas Exam Platform — Phase 1 Execution Plan (Landing + Real Practice MVP)

## 1) Objectives

## Execution updates and capacity change
- Core isolation complete: /app/test_reports/iteration_3.json, 43 checks passed using actual supplied PDFs; private storage verified and full 77-page report produced. No content has been academically approved or publicly published.
- Latest user requirement supersedes original capacity goal: architect for **500,000+ concurrent students from launch**. This is an unverified capacity target, not a preview capability claim. Separate API-backed domains, bounded durable heavy-work queue, immutable reviewed content versions, secret isolation, indexed atomic answer writes, frontend route splitting, and module regression gates are required. Production infrastructure provisioning and realistic sustained/burst load tests at this scale remain external release gates. No paid infrastructure purchase or production deployment is authorized.
- Approved Phase 1 is implemented as subphases A core, B full app, C QA. Phases numbered in the execution outline below are work stages, not expansion of the approved feature scope. Approved broader revision and analytics remain future.

- Deliver the full Phase 1 MVP exactly as approved in **/app/plan/plan.md** and **/app/plan/source_review.md** (no scope downgrades; Phase 2/3 remain explicitly future-only).
- Core guarantee: **every question is paired with its correct approved solution** on results and in a **single downloadable Results & Solutions PDF** per attempt.
- Enforce content trust gates: rights confirmation, reviewer approval, publication/withdrawal, immutable attempt snapshots, and **no keys/solutions exposed during active attempts**.
- Private document handling: source PDFs remain private; student reports are private and served only via app authorization.

## 2) Implementation Steps

### Phase 1 — Core POC in isolation (must be rock-solid before full app)
User stories:
1. As an owner, I can upload the Tejas200 questions+solutions PDFs and store them privately.
2. As a reviewer, I can define Q1–75 and bind each to an exact solution entry with source page refs (no ambiguous matches).
3. As a student, I can start an attempt and answer SCQ + numerical (including 5-digit answers) without seeing keys/solutions.
4. As a student, I get correct scoring (+4/−1/0) and per-question review with the matched solution.
5. As a student, I can download a single PDF report containing score + every Q in attempt order + my response + correct answer + marks + matched solution.

Steps:
- **POC-1: Private storage + secure serving**
  - Implement platform object storage integration (init once; DB is source of truth; no public URLs; serve via backend).
  - Validate upload constraints: PDF only, <=50MB, <=300 pages, reject encrypted/password PDFs with actionable error.
- **POC-2: Deterministic content extraction + pairing scaffold (no AI dependency)**
  - Local PDF parsing/rendering pipeline using PyMuPDF/pdfplumber:
    - Extract per-page text + render page images for reviewer source verification.
    - Create “draft question records” for Q1–75 with subject blocks (Math/Phy/Chem) and type (SCQ vs INTEGER) per source.
    - Create “draft solution records” for Q1–75 from solutions PDF; prevent duplicates from answer table.
  - Pairing rule: match by paper identity + question number; flag missing/duplicate/conflicting.
- **POC-3: Attempt snapshot + scoring + deadline correctness**
  - Create attempt start endpoint that snapshots: set version, question order, option order, rules, and deadline (server time).
  - Save answers incrementally with idempotency; mark states (answered/cleared/review).
  - Enforce timed deadline: only server-acknowledged responses before deadline count; late drafts are stored as late but not scored.
  - Submit is idempotent; generate submission receipt.
- **POC-4: Results view model + PDF report generation**
  - Compute score breakdown + accuracy definition (correct/attempted; N/A if attempted=0).
  - Generate downloadable PDF (paginated) that embeds:
    - header: exam + set identity + attempt date + rules
    - summary metrics
    - for each question in original attempt order: question, options (if any), student response, correct answer, marks, matched solution, source refs.
  - Store report PDF privately; allow download only to the owning student (or authorized staff).
- Stop and fix until: (a) all 75 Q have 1:1 solution matches, (b) report PDF renders, (c) no key leakage during attempt.

### Phase 2 — V1 App Development (build full product around proven core)
User stories:
1. As a visitor, I can view a premium landing page and understand practice → results → solutions → improve.
2. As a visitor, I can browse published sets for JEE Main/BITSAT without an account and see honest availability.
3. As a student, I can sign up/sign in (email+password) and see a simple home + attempt history.
4. As a student, I can do a full-paper attempt with navigator, mark-for-review, clear response, autosave state, and submit confirmation.
5. As a reviewer, I can upload PDFs, review/correct extracted content with source-page evidence, approve/publish/withdraw sets with audit trail.

Steps:
- Replace legacy JEE Advanced admin module entrypoints with Tejas MVP app (archive legacy code but do not expose it publicly).
- **Backend (FastAPI + Mongo)**
  - Auth: email/password JWT; role-based access (student vs reviewer/admin); bootstrap owner/reviewer creds (stored securely; displayed once).
  - Data model (minimal but complete): users, files, content_sets, questions, solutions, pairings, set_versions, attempts, attempt_answers, reports, audit_logs.
  - Content Studio APIs: upload, parse status, review/edit fields, pairing status, publish/withdraw, versioning.
  - Student APIs: list published sets, start/resume attempt, save answer, submit, results, download report.
- **Frontend (React)**
  - New information architecture:
    - Landing (public)
    - Explore sets (public)
    - Auth (signup/login)
    - Student: Home, Set detail, Player, Results, Attempt history
    - Reviewer: Content Studio dashboard, Set editor (Q list + solution pairing), Publish/Withdraw, Audit
  - Apply design tokens: #2563EB #0B1F3A #F5F9FF #14243A #52637A #D7E2F0 #1D4ED8; accessible focus + reduced motion.
  - Player UX: quiet workspace, clear save state, robust navigator, submission confirmation, no solutions shown.
  - BITSAT: show category but honest “no published papers yet”.
- **Publication gates**
  - Require rights confirmation fields (including permission for downloadable personal reports) before publish.
  - Block publish if missing any approved question/answer/solution pairing.
- Conclude with 1 full end-to-end run: upload → review/pair → publish → student attempt → results → download PDF.

### Phase 3 — Comprehensive testing, hardening, and regression
User stories:
1. As a student, I never see solutions/keys during an active attempt (even via direct URL guessing).
2. As a student, refresh/reconnect doesn’t lose saved answers, and timer/deadline stays correct.
3. As a reviewer, I can withdraw a set and it disappears for new attempts without altering past attempts.
4. As a student, my downloadable report is private and cannot be accessed by other students.
5. As an owner, I can see an audit trail for uploads, edits, publish/withdraw, and scoring/report generation.

Steps:
- Automated backend tests:
  - auth/role checks; object storage proxy serving; upload validation; pairing validation; idempotent start/submit.
  - timing: deadline enforcement + late answer handling.
  - scoring: SCQ + INTEGER, +4/−1/0, five-digit numeric acceptance.
  - immutability: attempt snapshot not mutated by later edits.
- Frontend E2E tests (Playwright): public browse, signup/login, attempt flow, results filters, download report.
- Security review: no public file URLs; no keys in frontend payloads; strict CORS; rate limits basic.
- Performance sanity: report generation progress + retry; large PDF handling within constraints.

## 3) Next Actions
1. Implement Phase 1 POC scripts/endpoints to prove: private storage, 75 Q↔75 solutions pairing, attempt scoring, and report PDF generation.
2. Run POC with the supplied Tejas200 Paper01 PDFs and fix until all checks pass.
3. Build V1 app UI/UX around the proven core (landing → explore → auth → player → results → report; reviewer studio).
4. Execute testing agent runs and iterate until stable.

## 4) Success Criteria
- POC: 75 questions imported as drafts; 75 solutions imported; **100% unambiguous pairings** or explicit holds; no duplicates from answer table.
- Student attempt: autosave works across refresh; timed deadline enforced server-side; submit idempotent with receipt.
- Results: correct metrics (marks, accuracy definition, skipped handling) and per-question matched solutions.
- Download: one PDF per attempt containing the complete attempt in order with question + response + correct answer + marks + matched solution; private access enforced.
- Landing + explore: honest availability, no fabricated claims, BITSAT empty state handled.
- Reviewer gates: rights confirmation required; publish/withdraw + audit; past attempts unchanged by later edits.
