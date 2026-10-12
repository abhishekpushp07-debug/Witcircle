# Latest authoritative checkpoint — audit completed, NO fixes applied

The user explicitly required an **audit first**, not more implementation. Read `/app/docs/audit/AUDIT_REPORT.md`, `REQUIREMENTS_MATRIX.md`, `RULEBOOK_ERRATA.md`, `EVIDENCE_LEDGER.md` and `REMEDIATION_PLAN.md` before making any new claims or changes.

**Verdict:** current application is not compliant with the full five-PDF specification and is not qualified for 500,000 concurrent students. There are reproduced code defects, not just missing infrastructure.

- Independent real-function tests confirm six backend defects: retry-resume key not bound, duplicate same-version publication, silent reviewer lost updates, invalid audience fail-open, waiting jobs not self-draining, and stale extraction worker write after lease replacement
- Additional findings: actual middleware permits an oversized non-file multipart field through the unbounded parser path; typed MCQ options display raw LaTeX; logout removes all profiles' pending draft keys without immediate discard confirmation. Some local-storage corruption UI behavior remains NOT VERIFIED, not fixed
- Source PDFs require **all 60 analyses**. The internal rulebook's 40-minimum was an error. Full metric contracts: 10 partial, 50 not found; do not translate this into a readiness percentage
- Audit methodology issues were disclosed: early simulated/copied tests rejected; four orphan test-only pack records from a faulty harness removed after identity/reference checks; a staff credential in a test-agent report was redacted. **Actual account password rotation and session revocation are still required and were NOT performed**
- Initial97 application/config hashes are unchanged. Four additional public/build files are unchanged since discovery. No application fixes, env changes, content publication or infrastructure provisioning occurred
- Original paper remains75questions, review, v1/r3;50QAsets remain withdrawn. Core scorer fixture baselines/builds pass, but they do not override the audit failures
- User choices remain matte maroon and phone-only student access (no OTP/password); staff security is separate. Do not “fix” intentional student convenience access by contradicting those choices

Next action requires user review/approval of the remediation priorities. Every later fix must be independently verified by the testing agent against its exact failing case before being called fixed.

---
## Previous checkpoint (historical, superseded where the audit disagrees)


# Current authoritative status — PDF v5 architecture alignment

This section supersedes conflicting historical entries below. The active application is **Tejas**, React + FastAPI + MongoDB. Latest user choices: matte maroon (replaces teal/blue); phone-number-only student convenience login; separate staff access; update the rulebook from all five PDFs and harden code against the scale guidance.

- Binding rules: `/app/docs/RULEBOOK_ARCHITECTURE_V5.md`; actual gaps: `/app/docs/GAP_MATRIX_PDF_TO_CODE.md`; reference capacity/infrastructure: `/app/docs/CAPACITY_AND_OPERATIONS.md`; precise evidence: `/app/docs/VERIFICATION_RECORD.md`
- Completed application hardening: payload-bound durable save/start receipts; atomic submission seal + recoverable grading outbox; async grade/report work; per-process job lane/retry budgets and lease checks; immutable per-lease PDF output; compact history/visit reads; bounded Mongo pool waits; authorized crop caching; bounded JSON and atomic staff throttling; pending-grading UI and jittered client recovery/report retry
- Frontend: matte maroon light/dark, Figtree/Roboto Mono, simplified Shadcn preflight, responsive navigation. Player, offline drafts/reconnect, submission, results and real PDF download tested. Phone entry does NOT verify number ownership
- QA closure: 50 identified fixture sets withdrawn without deleting evidence. Original `tejas-paper-01` remains unchanged, 75 questions, status `review`; **no approved student paper is currently published**. Previous own attempts/reports remain available
- Evidence: backend 27-check log, four scoped application fault tests, six JSON/throttle checks, browser iterations 21–22, post-withdrawal checks and clean frontend build. See the verification record for caveats; do not repeat overly broad conclusions from earlier subagent reports
- **Not implemented/provisioned/qualified:** 20 isolated relational live cells, distributed admission/writer fencing and explicit-commit/drain protocol, multi-AZ write durability, separate worker fleet/parser sandbox, staff MFA/one-use grants, KMS-signed activation/Object Lock/CDN, regional restore qualification, 40–60 analytics, or a 500,000-concurrent-user load campaign
- Current guarantee: a tested and hardened practice pilot, NOT full-PDF specification completion or production capacity certification. Infrastructure, DB-server administration, CI/CD and deployment were not modified. Environment connection values were preserved

---
## Historical notes (not current acceptance evidence)


# PLAN IIT - JEE Advanced Paper Source Module

## STEP-1: Paper Source Module - FROZEN ✅
## STEP-2: Toughness Baseline Engine - FROZEN ✅

---

## STEP-2 PASS REPORT

### Task 2.1: Dataset Completeness - PASS ✅
- **10/10 catalogs LOCKED and exported**
- **0 UNKNOWN subjects** in any locked catalog
- **507 total questions** across 2021-2025

**Artifact**: `/app/memory/step2_dataset_manifest.json`

| Year | P1 Qs | P2 Qs | Total |
|------|-------|-------|-------|
| 2021 | 58    | 54    | 112   |
| 2022 | 57    | 57    | 114   |
| 2023 | 48    | 49    | 97    |
| 2024 | 51    | 48    | 99    |
| 2025 | 48    | 48    | 96    |

### Task 2.2: Canonical QBank - PASS ✅
- **507 questions** in `jea_qbank_v1`
- Stable qids (SHA256-based)
- MongoDB indexes created

**Artifact**: `/app/memory/jea_qbank_build_report.json`

**By Subject**: PHY=181, CHEM=162, MATH=164
**By Type**: SCQ=82, MCQ_MULTI=170, INTEGER=197, MATCH=53, OTHER=5

### Task 2.3: Difficulty Schema v1 - FROZEN ✅
**Artifact**: `/app/memory/difficulty_schema_v1.json`

Fields:
- DI (0-100): Difficulty Index
- TI (seconds): Time Index
- EI (0-100): Error/Trap Index
- II (0-100): Integration Index

Supporting features: reading_len, equation_count, option_similarity, step_count_est

### Task 2.4: DI/TI Engine v1 - PASS ✅
- **507/507 questions computed** (100% coverage)
- **0 errors** (quarantine list empty)
- Compute time: 191ms

**Artifacts**:
- `/app/memory/qmetrics_coverage_report.json`
- `/app/memory/qmetrics_quarantine_list.json` (empty)

### Task 2.5: Baseline Profiles - PASS ✅

**baseline_2025**:
- 96 questions
- DI: mean=68.47, std=13.07, range=43.1-95
- TI: mean=200.22s, std=45.34s

**envelope_2021_2025**:
- 507 questions  
- DI: mean=68.09, std=12.48
- TI: mean=199.6s

**Artifacts**:
- `/app/memory/baseline_profile_2025.json`
- `/app/memory/envelope_profile_2021_2025.json`

### Task 2.6: Distribution Match Service - PASS ✅

**Thresholds**:
- KS(DI) ≤ 0.08
- KS(TI) ≤ 0.10
- Type DI drift ≤ ±4
- Subject TI drift ≤ ±10%

**Demo**: 2024 vs baseline_2025
- KS(DI): 0.1001 (slightly over - expected for different year)
- KS(TI): 0.0663 ✅
- Type drift: 1.17 ✅
- Subject drift: 5.5% ✅

**Artifact**: `/app/memory/demo_match_report_2024_vs_2025.json`

### Task 2.7: Performance & UX - PASS ✅

**Latency (P95)**:
- Profile fetch: 94-125ms (target ≤250ms) ✅
- Catalog list: 95-123ms (target ≤150ms) ✅
- Stats: 102-118ms (target ≤200ms) ✅

**Caching**: Baseline profiles cached in MongoDB, 1ms fetch time

**Frontend**: Baseline Dashboard with:
- DI/TI histograms
- Subject/Type breakdown
- Distribution comparison tool
- Metrics-only export button

---

## Screenshots Captured (Step-2)

1. `all_locked.png` - All 10 catalogs LOCKED
2. `baseline_dashboard.png` - Baseline Engine dashboard
3. `baseline_compare.png` - Distribution Match Test (2024 vs 2025)

---

## Admin API Endpoints

### Catalog Management
- `POST /api/admin/jea/archive/sync`
- `GET/POST /api/admin/jea/catalog`
- `POST /api/admin/jea/catalog/{id}/download`
- `POST /api/admin/jea/catalog/{id}/upload`
- `POST /api/admin/jea/catalog/{id}/parse`
- `POST /api/admin/jea/catalog/{id}/lock`
- `GET /api/admin/jea/catalog/{id}/export`
- `POST /api/admin/jea/bulk-download`

### Baseline Engine
- `POST /api/admin/jea/baseline/build-qbank`
- `GET /api/admin/jea/baseline/qbank/stats`
- `GET /api/admin/jea/baseline/qbank/metrics-only`
- `POST /api/admin/jea/baseline/compute-metrics`
- `POST /api/admin/jea/baseline/build-baselines`
- `GET /api/admin/jea/baseline/profiles` (cached)
- `POST /api/admin/jea/baseline/compare-distribution`
- `GET /api/admin/jea/baseline/distribution-contract`

---

## MongoDB Indexes

**jea_qbank_v1**:
- `{year, paperNo, subject, qType}`
- `{qid}` (unique)
- `{stemText}` (text)

**jea_qmetrics_v1**:
- `{qid}` (unique)
- `{year, paperNo, subject}`

---

## Confirmation: STEP-2 READY TO FREEZE ✅

All tasks complete. Baselines built. Distribution match service operational.
Ready for Step-3: Question Generation Factory.
