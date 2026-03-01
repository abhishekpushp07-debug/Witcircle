# JEE Advanced Paper Source Module - PRD

## Project Overview
Production-grade system for managing JEE Advanced question papers from official archive.

## Original Problem Statement
Build a FastAPI + React admin module that:
- Syncs/Downloads PDFs from JEE Advanced official archive (2021-2025, English, Paper 1 & 2)
- Parses PDFs to extract sections, instructions, questions, options
- Provides YearSpec Review UI with evidence-first approach
- Provides Question Review UI with flags, split/merge, edit capabilities
- Implements validation gates before LOCK
- Maintains immutable LOCK snapshots with versioning
- Records audit logs for all actions
- Exports data as JSON

## User Choices
- **Database**: MongoDB (Emergent default)
- **Frontend**: React admin dashboard
- **External Fetch**: Enabled with manual upload fallback
- **Scope**: 2021-2025 English Papers only

## Core Requirements (Static)
1. Catalog management (sync, download, upload)
2. PDF parsing (sections, questions, options)
3. YearSpec section review (marking rules, evidence)
4. Question review (edit, flags, split/merge)
5. Validation gates before LOCK
6. Immutable snapshots after LOCK
7. Audit logging
8. JSON export

## Architecture
- **Backend**: FastAPI with Motor (async MongoDB)
- **Frontend**: React 19 + Tailwind CSS + Sonner
- **Database**: MongoDB collections:
  - jea_source_catalog
  - jea_source_files
  - jea_yearspec_sections
  - jea_questions
  - jea_audit_logs

## What's Been Implemented (Jan 2026)

### Backend Services
- `/app/backend/services/jea_archive.py` - Archive HTML parsing, PDF link extraction
- `/app/backend/services/downloader.py` - PDF download with SHA256 verification
- `/app/backend/services/parser.py` - PDF parsing (sections, questions, options)
- `/app/backend/services/exporter.py` - JSON export with quality report

### Backend API Endpoints
- `POST /api/admin/jea/archive/sync` - Sync from official archive
- `GET/POST /api/admin/jea/catalog` - Catalog CRUD
- `POST /api/admin/jea/catalog/{id}/download` - Download PDF
- `POST /api/admin/jea/catalog/{id}/upload` - Manual upload
- `POST /api/admin/jea/catalog/{id}/parse` - Parse PDF
- `POST /api/admin/jea/catalog/{id}/lock` - Lock with validation
- `GET /api/admin/jea/catalog/{id}/export` - Export JSON
- `GET/PATCH /api/admin/jea/yearspec` - YearSpec CRUD
- `GET/PATCH /api/admin/jea/questions` - Questions CRUD
- `POST /api/admin/jea/questions/{id}/flag` - Add flag
- `POST /api/admin/jea/questions/split` - Split question
- `POST /api/admin/jea/questions/merge` - Merge questions
- `GET /api/admin/jea/audit-logs` - Audit logs
- `GET /api/admin/jea/stats` - Statistics

### Frontend Pages
- Dashboard - Stats overview, quick actions
- Catalog - Sync/download/parse/lock controls
- YearSpec - Section review with subject/type editing
- Questions - Question review with filters, edit, flags
- Audit Logs - Action history table

## Validation Gates (Before LOCK)
1. Sections must exist
2. Marking rules + evidence must be non-empty
3. No empty question stems
4. SCQ/MCQ questions must have options A-D
5. Subject cannot be UNKNOWN

## Testing Status
- Backend: 100% (7/7 tests passed)
- Frontend: 95% (minor React hydration warnings)

## Prioritized Backlog

### P0 (Critical)
- ✅ Catalog sync from archive
- ✅ PDF download/upload
- ✅ PDF parsing
- ✅ YearSpec review
- ✅ Question review
- ✅ Lock validation
- ✅ JSON export

### P1 (Important)
- Bulk download all catalogs
- Progress tracking for long operations
- PDF preview in browser
- Better OCR handling for images in PDFs

### P2 (Nice to Have)
- Hindi language support
- Answer key integration
- Difficulty tagging
- Subject auto-detection

## Next Tasks
1. Test full workflow: Sync → Download → Parse → Review → Lock → Export
2. Add PDF preview modal
3. Implement bulk operations
4. Add progress indicators for downloads
