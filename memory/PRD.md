# JEE Advanced Paper Source Module - PRD

## Project Overview
Production-grade system for managing JEE Advanced question papers from official archive.

## PASS REPORT - Step 1 FROZEN

### Golden Workflow Test: 2025 Paper 1 English
| Step | Description | Status | Proof |
|------|-------------|--------|-------|
| A | Sync Archive | PASS | 10 catalogs (2021-2025 P1/P2 EN) |
| B | Download PDF | PASS | SHA256: 563a68ebca24815d..., 31 pages, 5.26MB |
| C | Parse PDF | PASS | 12 sections, 48 questions, 0 empty stems |
| D | YearSpec Review | PASS | Evidence text visible, marking rules extracted |
| E | Question Review | PASS | Edit stem/options, flags working |
| F | Assign Subjects | PASS | 0 UNKNOWN remaining (34 auto + 14 manual) |
| G | LOCK | PASS | All validation gates passed |
| H | Export JSON | PASS | /app/storage/export_2025_p1.json |

### Screenshots Captured
1. step_c_catalog.png - Catalog with 2025 P1 PARSED
2. step_d_yearspec.png - YearSpec Review with evidence text
3. step_e_questions.png - Questions Review with edit panel
4. step_g_locked.png - 2025 P1 LOCKED with Export button
5. pdf_preview.png - PDF Preview Modal (31 pages, SHA256)
6. bulk_download_modal.png - Bulk Download Modal
7. all_downloaded.png - All 10 papers DOWNLOADED

### Export Artifacts
- `/app/storage/export_2025_p1.json` - Full export with yearspec + questions + quality_report
- Backend logs: All downloads with SHA256 verified

### Bulk Download Results (All 10 Papers)
| Year | Paper | Status | SHA256 (first 16) | Pages |
|------|-------|--------|-------------------|-------|
| 2021 | P1 | SUCCESS | 513d0c9bd4bb602f | 29 |
| 2021 | P2 | SUCCESS | 7c0efd42ce0ebc37 | 29 |
| 2022 | P1 | SUCCESS | ff67ab84597e45dd | 31 |
| 2022 | P2 | SUCCESS | 19fb87de938f6e45 | 26 |
| 2023 | P1 | SUCCESS | 7823ad451ebd269f | 30 |
| 2023 | P2 | SUCCESS | cef4c09da7aeebaa | 31 |
| 2024 | P1 | SUCCESS | d0f3ffd739772b80 | 30 |
| 2024 | P2 | SUCCESS | 2f01767b18f95ff9 | 26 |
| 2025 | P1 | SUCCESS | 563a68ebca2481... | 31 |
| 2025 | P2 | SUCCESS | bdc7e174f608718a | 21 |

## Admin Routes (All require admin access)

### Catalog Management
- `POST /api/admin/jea/archive/sync` - Sync from official JEE archive
- `GET /api/admin/jea/catalog` - List all catalogs
- `GET /api/admin/jea/catalog/{id}` - Get single catalog
- `POST /api/admin/jea/catalog` - Manual catalog entry
- `POST /api/admin/jea/catalog/{id}/download` - Download PDF from official URL
- `POST /api/admin/jea/catalog/{id}/upload` - Manual PDF upload
- `POST /api/admin/jea/catalog/{id}/parse` - Parse PDF to extract data
- `POST /api/admin/jea/catalog/{id}/lock` - Lock with validation
- `GET /api/admin/jea/catalog/{id}/export` - Export locked catalog to JSON
- `GET /api/admin/jea/catalog/{id}/preview-pdf` - Stream PDF for preview
- `GET /api/admin/jea/catalog/{id}/pdf-info` - Get PDF metadata

### Bulk Operations
- `POST /api/admin/jea/bulk-download` - Download all NEW catalogs (max 2 concurrent)

### YearSpec Management
- `GET /api/admin/jea/yearspec` - List yearspec sections
- `GET /api/admin/jea/yearspec/{id}` - Get single section
- `PATCH /api/admin/jea/yearspec/{id}` - Update section (subject, type)

### Question Management  
- `GET /api/admin/jea/questions` - List questions with filters
- `GET /api/admin/jea/questions/{id}` - Get single question
- `PATCH /api/admin/jea/questions/{id}` - Update question
- `POST /api/admin/jea/questions/{id}/flag` - Add flag
- `DELETE /api/admin/jea/questions/{id}/flag/{type}` - Remove flag
- `POST /api/admin/jea/questions/{id}/detect-subject` - Detect subject (preview)
- `POST /api/admin/jea/questions/split` - Split question
- `POST /api/admin/jea/questions/merge` - Merge questions

### Subject Suggestions (Assistive)
- `GET /api/admin/jea/catalog/{id}/suggest-subjects` - Get suggestions (no auto-apply)
- `POST /api/admin/jea/catalog/{id}/apply-suggestions` - Apply selected suggestions

### Audit & Stats
- `GET /api/admin/jea/audit-logs` - View audit trail
- `GET /api/admin/jea/stats` - Get statistics

## Known Limitations
1. Parser heuristics may miss some questions in unusual PDF formats
2. OCR quality depends on PDF source quality
3. Subject auto-detection ~70% accuracy, requires manual review
4. INTEGER type questions don't have A-D options (by design)

## Step-1: READY TO FREEZE
- All golden workflow steps PASS
- All 10 papers downloadable and parseable
- Bulk download working (max 2 concurrent)
- PDF preview modal working
- Subject suggestions assistive-only (not autopilot)
- Lock validation gates enforced
- Export JSON with quality report
- Audit logs complete
