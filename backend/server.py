"""
JEE Advanced Paper Source Module
FastAPI Backend with MongoDB
"""
from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query, Body
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json

# Services
from services.jea_archive import fetch_archive_html, extract_pdf_links
from services.downloader import (
    sha256_stream_to_file, 
    sha256_from_bytes, 
    count_pdf_pages, 
    get_storage_path,
    ensure_dirs
)
from services.parser import build_yearspec_and_questions
from services.exporter import export_to_json, generate_quality_report

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Storage directory
STORAGE_DIR = os.environ.get("STORAGE_DIR", str(ROOT_DIR / "storage"))
os.environ["STORAGE_DIR"] = STORAGE_DIR
ALLOW_EXTERNAL_FETCH = os.environ.get("ALLOW_EXTERNAL_FETCH", "true").lower() == "true"

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="JEE Advanced Paper Source Module")

# Create routers
api_router = APIRouter(prefix="/api")
admin_router = APIRouter(prefix="/admin/jea", tags=["admin-jea"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== Pydantic Models ==============

class CatalogCreate(BaseModel):
    year: int
    paper_no: int
    language: str = "EN"
    official_url: str

class CatalogOut(BaseModel):
    id: str
    year: int
    paper_no: int
    language: str
    official_url: str
    source_kind: str = "OFFICIAL_ARCHIVE"
    status: str
    created_at: str

class SyncResult(BaseModel):
    created: int
    updated: int
    items: List[CatalogOut]

class DownloadResult(BaseModel):
    file_id: str
    sha256: str
    bytes: int
    pages_count: Optional[int]

class ParseResult(BaseModel):
    yearspec_sections: int
    questions: int
    validation: Dict[str, Any]

class LockResult(BaseModel):
    locked: bool
    reason: Optional[str] = None

class YearSpecUpdate(BaseModel):
    subject: Optional[str] = None
    question_type: Optional[str] = None
    q_count_expected: Optional[int] = None
    marking_rule_json: Optional[str] = None
    evidence_text: Optional[str] = None

class QuestionUpdate(BaseModel):
    subject: Optional[str] = None
    q_type: Optional[str] = None
    stem_text: Optional[str] = None
    options_json: Optional[str] = None
    status: Optional[str] = None

class QuestionFlag(BaseModel):
    flag_type: str  # MISSING_OPTIONS, BROKEN_OCR, MERGE_SUSPECT, SPLIT_SUSPECT
    note: Optional[str] = None


# ============== Helper Functions ==============

def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document for JSON response"""
    if doc is None:
        return None
    doc = dict(doc)
    # Remove MongoDB _id, keep existing id field if present
    if "_id" in doc:
        doc.pop("_id")
    for key, val in doc.items():
        if isinstance(val, datetime):
            doc[key] = val.isoformat()
    return doc


async def create_audit_log(
    entity_type: str,
    entity_id: str,
    action: str,
    before_json: Optional[str] = None,
    after_json: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Create audit log entry"""
    await db.jea_audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "before_json": before_json,
        "after_json": after_json,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc)
    })


# ============== Root Routes ==============

@api_router.get("/")
async def root():
    return {"message": "JEE Advanced Paper Source Module API"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "external_fetch": ALLOW_EXTERNAL_FETCH}


# ============== Catalog Routes ==============

@admin_router.post("/archive/sync", response_model=SyncResult)
async def sync_from_official(
    start_year: int = Query(2021, ge=2021, le=2026),
    end_year: int = Query(2025, ge=2021, le=2026),
    language: str = Query("EN", regex="^(EN|HI)$")
):
    """Sync catalog from official JEE Advanced archive"""
    if not ALLOW_EXTERNAL_FETCH:
        raise HTTPException(
            status_code=400, 
            detail="External fetch disabled. Use manual upload mode."
        )
    
    try:
        html = fetch_archive_html()
        items = extract_pdf_links(html, start_year, end_year, language)
    except Exception as e:
        logger.error(f"Failed to fetch archive: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch archive: {str(e)}")
    
    created, updated = 0, 0
    outs = []
    
    for it in items:
        existing = await db.jea_source_catalog.find_one({
            "year": it["year"],
            "paper_no": it["paper_no"],
            "language": it["language"]
        })
        
        if existing:
            await db.jea_source_catalog.update_one(
                {"_id": existing["_id"]},
                {"$set": {"official_url": it["official_url"]}}
            )
            updated += 1
            row = {**existing, "official_url": it["official_url"]}
        else:
            row = {
                "id": str(uuid.uuid4()),
                "year": it["year"],
                "paper_no": it["paper_no"],
                "language": it["language"],
                "official_url": it["official_url"],
                "source_kind": "OFFICIAL_ARCHIVE",
                "status": "NEW",
                "created_at": datetime.now(timezone.utc)
            }
            await db.jea_source_catalog.insert_one(row)
            created += 1
        
        outs.append(CatalogOut(**serialize_doc(row)))
    
    return SyncResult(created=created, updated=updated, items=outs)


@admin_router.get("/catalog", response_model=List[CatalogOut])
async def list_catalog(
    status: Optional[str] = None,
    year: Optional[int] = None
):
    """List all catalog entries"""
    query = {}
    if status:
        query["status"] = status
    if year:
        query["year"] = year
    
    cursor = db.jea_source_catalog.find(query).sort([("year", 1), ("paper_no", 1)])
    rows = await cursor.to_list(100)
    return [CatalogOut(**serialize_doc(r)) for r in rows]


@admin_router.get("/catalog/{catalog_id}", response_model=CatalogOut)
async def get_catalog(catalog_id: str):
    """Get single catalog entry"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    return CatalogOut(**serialize_doc(cat))


@admin_router.post("/catalog", response_model=CatalogOut)
async def create_catalog(data: CatalogCreate):
    """Manually create catalog entry"""
    existing = await db.jea_source_catalog.find_one({
        "year": data.year,
        "paper_no": data.paper_no,
        "language": data.language
    })
    if existing:
        raise HTTPException(400, "Catalog entry already exists")
    
    row = {
        "id": str(uuid.uuid4()),
        "year": data.year,
        "paper_no": data.paper_no,
        "language": data.language,
        "official_url": data.official_url,
        "source_kind": "MANUAL",
        "status": "NEW",
        "created_at": datetime.now(timezone.utc)
    }
    await db.jea_source_catalog.insert_one(row)
    return CatalogOut(**serialize_doc(row))


# ============== Download/Upload Routes ==============

@admin_router.post("/catalog/{catalog_id}/download", response_model=DownloadResult)
async def download_pdf(catalog_id: str):
    """Download PDF from official URL"""
    if not ALLOW_EXTERNAL_FETCH:
        raise HTTPException(
            status_code=400, 
            detail="External fetch disabled. Use manual upload mode."
        )
    
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot download for LOCKED catalog")
    
    ensure_dirs()
    
    # Get next version number
    latest = await db.jea_source_files.find_one(
        {"catalog_id": catalog_id},
        sort=[("file_version", -1)]
    )
    next_ver = 1 if not latest else latest["file_version"] + 1
    
    dest = get_storage_path(cat["year"], cat["paper_no"], cat["language"], next_ver)
    
    try:
        sha, nbytes, etag, lastmod = sha256_stream_to_file(cat["official_url"], dest)
        pages = count_pdf_pages(dest)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(502, f"Download failed: {str(e)}")
    
    file_doc = {
        "id": str(uuid.uuid4()),
        "catalog_id": catalog_id,
        "file_version": next_ver,
        "sha256": sha,
        "bytes": nbytes,
        "mime": "application/pdf",
        "storage_path": dest,
        "downloaded_at": datetime.now(timezone.utc),
        "http_etag": etag,
        "http_last_modified": lastmod,
        "pages_count": pages
    }
    await db.jea_source_files.insert_one(file_doc)
    
    await db.jea_source_catalog.update_one(
        {"id": catalog_id},
        {"$set": {"status": "DOWNLOADED"}}
    )
    
    await create_audit_log("JeaSourceFile", file_doc["id"], "DOWNLOAD")
    
    return DownloadResult(
        file_id=file_doc["id"],
        sha256=sha,
        bytes=nbytes,
        pages_count=pages
    )


@admin_router.post("/catalog/{catalog_id}/upload", response_model=DownloadResult)
async def upload_pdf(catalog_id: str, file: UploadFile = File(...)):
    """Manually upload PDF for catalog entry"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot upload for LOCKED catalog")
    
    ensure_dirs()
    
    latest = await db.jea_source_files.find_one(
        {"catalog_id": catalog_id},
        sort=[("file_version", -1)]
    )
    next_ver = 1 if not latest else latest["file_version"] + 1
    
    dest = get_storage_path(cat["year"], cat["paper_no"], cat["language"], next_ver)
    
    data = await file.read()
    sha = sha256_from_bytes(data)
    
    with open(dest, "wb") as f:
        f.write(data)
    
    pages = count_pdf_pages(dest)
    
    file_doc = {
        "id": str(uuid.uuid4()),
        "catalog_id": catalog_id,
        "file_version": next_ver,
        "sha256": sha,
        "bytes": len(data),
        "mime": "application/pdf",
        "storage_path": dest,
        "downloaded_at": datetime.now(timezone.utc),
        "http_etag": None,
        "http_last_modified": None,
        "pages_count": pages
    }
    await db.jea_source_files.insert_one(file_doc)
    
    await db.jea_source_catalog.update_one(
        {"id": catalog_id},
        {"$set": {"status": "DOWNLOADED"}}
    )
    
    await create_audit_log("JeaSourceFile", file_doc["id"], "UPLOAD")
    
    return DownloadResult(
        file_id=file_doc["id"],
        sha256=sha,
        bytes=len(data),
        pages_count=pages
    )


@admin_router.get("/catalog/{catalog_id}/files")
async def list_files(catalog_id: str):
    """List all file versions for a catalog entry"""
    files = await db.jea_source_files.find(
        {"catalog_id": catalog_id}
    ).sort("file_version", -1).to_list(100)
    return [serialize_doc(f) for f in files]


# ============== Parse Routes ==============

@admin_router.post("/catalog/{catalog_id}/parse", response_model=ParseResult)
async def parse_latest(catalog_id: str):
    """Parse the latest PDF file for a catalog entry"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot parse LOCKED catalog")
    
    latest_file = await db.jea_source_files.find_one(
        {"catalog_id": catalog_id},
        sort=[("file_version", -1)]
    )
    if not latest_file:
        raise HTTPException(400, "No file downloaded/uploaded yet")
    
    try:
        yearspec, questions, validation = build_yearspec_and_questions(
            latest_file["storage_path"],
            year=cat["year"],
            paper_no=cat["paper_no"]
        )
    except Exception as e:
        logger.error(f"Parse failed: {e}")
        raise HTTPException(500, f"Parse failed: {str(e)}")
    
    # Clear existing data for this year/paper
    await db.jea_yearspec_sections.delete_many({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    })
    await db.jea_questions.delete_many({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    })
    
    # Insert yearspec sections
    for s in yearspec:
        doc = {
            "id": str(uuid.uuid4()),
            "year": s["year"],
            "paper_no": s["paper_no"],
            "section_code": s["section_code"],
            "subject": s["subject"],
            "question_type": s["question_type"],
            "q_count_expected": s["q_count_expected"],
            "marking_rule_json": json.dumps(s["marking_rule"], ensure_ascii=False),
            "rounding_rule_json": json.dumps(s["rounding_rule"]) if s["rounding_rule"] else None,
            "evidence_text": s["evidence_text"],
            "page_refs_json": json.dumps(s["page_refs"]) if s["page_refs"] else None,
            "created_at": datetime.now(timezone.utc)
        }
        await db.jea_yearspec_sections.insert_one(doc)
    
    # Insert questions
    for q in questions:
        doc = {
            "id": str(uuid.uuid4()),
            "year": q["year"],
            "paper_no": q["paper_no"],
            "section_code": q["section_code"],
            "subject": q["subject"],
            "q_no": q["q_no"],
            "q_type": q["q_type"],
            "stem_text": q["stem_text"],
            "options_json": json.dumps(q["options"], ensure_ascii=False) if q["options"] else None,
            "passage_id": None,
            "source_page_range": q["source_page_range"],
            "status": q["status"],
            "flags": [],
            "created_at": datetime.now(timezone.utc)
        }
        await db.jea_questions.insert_one(doc)
    
    await db.jea_source_catalog.update_one(
        {"id": catalog_id},
        {"$set": {"status": "PARSED"}}
    )
    
    await create_audit_log(
        "JeaSourceCatalog", 
        catalog_id, 
        "PARSE",
        after_json=json.dumps(validation)
    )
    
    return ParseResult(
        yearspec_sections=len(yearspec),
        questions=len(questions),
        validation=validation
    )


# ============== YearSpec Routes ==============

@admin_router.get("/yearspec")
async def list_yearspec(
    year: Optional[int] = None,
    paper_no: Optional[int] = None
):
    """List yearspec sections"""
    query = {}
    if year:
        query["year"] = year
    if paper_no:
        query["paper_no"] = paper_no
    
    cursor = db.jea_yearspec_sections.find(query).sort([
        ("year", 1), ("paper_no", 1), ("section_code", 1)
    ])
    rows = await cursor.to_list(500)
    return [serialize_doc(r) for r in rows]


@admin_router.get("/yearspec/{section_id}")
async def get_yearspec(section_id: str):
    """Get single yearspec section"""
    sec = await db.jea_yearspec_sections.find_one({"id": section_id})
    if not sec:
        raise HTTPException(404, "Section not found")
    return serialize_doc(sec)


@admin_router.patch("/yearspec/{section_id}")
async def update_yearspec(section_id: str, data: YearSpecUpdate):
    """Update yearspec section"""
    sec = await db.jea_yearspec_sections.find_one({"id": section_id})
    if not sec:
        raise HTTPException(404, "Section not found")
    
    # Check if catalog is locked
    cat = await db.jea_source_catalog.find_one({
        "year": sec["year"],
        "paper_no": sec["paper_no"]
    })
    if cat and cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot update LOCKED catalog")
    
    before = json.dumps(serialize_doc(sec))
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        await db.jea_yearspec_sections.update_one(
            {"id": section_id},
            {"$set": update_data}
        )
    
    after_sec = await db.jea_yearspec_sections.find_one({"id": section_id})
    await create_audit_log(
        "JeaYearSpecSection",
        section_id,
        "EDIT",
        before_json=before,
        after_json=json.dumps(serialize_doc(after_sec))
    )
    
    return serialize_doc(after_sec)


# ============== Question Routes ==============

@admin_router.get("/questions")
async def list_questions(
    year: Optional[int] = None,
    paper_no: Optional[int] = None,
    section_code: Optional[str] = None,
    subject: Optional[str] = None,
    status: Optional[str] = None,
    has_flags: Optional[bool] = None
):
    """List questions with filters"""
    query = {}
    if year:
        query["year"] = year
    if paper_no:
        query["paper_no"] = paper_no
    if section_code:
        query["section_code"] = section_code
    if subject:
        query["subject"] = subject
    if status:
        query["status"] = status
    if has_flags:
        query["flags"] = {"$ne": []}
    
    cursor = db.jea_questions.find(query).sort([
        ("year", 1), ("paper_no", 1), ("q_no", 1)
    ])
    rows = await cursor.to_list(500)
    return [serialize_doc(r) for r in rows]


@admin_router.get("/questions/{question_id}")
async def get_question(question_id: str):
    """Get single question"""
    q = await db.jea_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(404, "Question not found")
    return serialize_doc(q)


@admin_router.patch("/questions/{question_id}")
async def update_question(question_id: str, data: QuestionUpdate):
    """Update question"""
    q = await db.jea_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(404, "Question not found")
    
    cat = await db.jea_source_catalog.find_one({
        "year": q["year"],
        "paper_no": q["paper_no"]
    })
    if cat and cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot update LOCKED catalog")
    
    before = json.dumps(serialize_doc(q))
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        await db.jea_questions.update_one(
            {"id": question_id},
            {"$set": update_data}
        )
    
    after_q = await db.jea_questions.find_one({"id": question_id})
    await create_audit_log(
        "JeaQuestion",
        question_id,
        "EDIT",
        before_json=before,
        after_json=json.dumps(serialize_doc(after_q))
    )
    
    return serialize_doc(after_q)


@admin_router.post("/questions/{question_id}/flag")
async def add_question_flag(question_id: str, flag: QuestionFlag):
    """Add flag to question"""
    q = await db.jea_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(404, "Question not found")
    
    flag_doc = {
        "type": flag.flag_type,
        "note": flag.note,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.jea_questions.update_one(
        {"id": question_id},
        {"$push": {"flags": flag_doc}}
    )
    
    return {"success": True, "flag": flag_doc}


@admin_router.delete("/questions/{question_id}/flag/{flag_type}")
async def remove_question_flag(question_id: str, flag_type: str):
    """Remove flag from question"""
    q = await db.jea_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(404, "Question not found")
    
    await db.jea_questions.update_one(
        {"id": question_id},
        {"$pull": {"flags": {"type": flag_type}}}
    )
    
    return {"success": True}


@admin_router.post("/questions/split")
async def split_question(
    question_id: str = Body(...),
    split_at: int = Body(..., description="Character position to split at")
):
    """Split a question into two"""
    q = await db.jea_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(404, "Question not found")
    
    cat = await db.jea_source_catalog.find_one({
        "year": q["year"],
        "paper_no": q["paper_no"]
    })
    if cat and cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot split LOCKED catalog")
    
    stem = q["stem_text"]
    if split_at <= 0 or split_at >= len(stem):
        raise HTTPException(400, "Invalid split position")
    
    # Update original question
    await db.jea_questions.update_one(
        {"id": question_id},
        {"$set": {"stem_text": stem[:split_at].strip()}}
    )
    
    # Create new question
    new_q = {
        "id": str(uuid.uuid4()),
        "year": q["year"],
        "paper_no": q["paper_no"],
        "section_code": q["section_code"],
        "subject": q["subject"],
        "q_no": q["q_no"] + 0.5,  # Will need renumbering
        "q_type": q["q_type"],
        "stem_text": stem[split_at:].strip(),
        "options_json": None,
        "passage_id": q.get("passage_id"),
        "source_page_range": q.get("source_page_range"),
        "status": "DRAFT",
        "flags": [{"type": "SPLIT_RESULT", "created_at": datetime.now(timezone.utc).isoformat()}],
        "created_at": datetime.now(timezone.utc)
    }
    await db.jea_questions.insert_one(new_q)
    
    await create_audit_log("JeaQuestion", question_id, "SPLIT", after_json=json.dumps({"new_id": new_q["id"]}))
    
    return {"original_id": question_id, "new_id": new_q["id"]}


@admin_router.post("/questions/merge")
async def merge_questions(
    question_id_1: str = Body(...),
    question_id_2: str = Body(...)
):
    """Merge two questions into one"""
    q1 = await db.jea_questions.find_one({"id": question_id_1})
    q2 = await db.jea_questions.find_one({"id": question_id_2})
    
    if not q1 or not q2:
        raise HTTPException(404, "One or both questions not found")
    
    if q1["year"] != q2["year"] or q1["paper_no"] != q2["paper_no"]:
        raise HTTPException(400, "Questions must be from same paper")
    
    cat = await db.jea_source_catalog.find_one({
        "year": q1["year"],
        "paper_no": q1["paper_no"]
    })
    if cat and cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot merge LOCKED catalog")
    
    # Merge stems
    merged_stem = q1["stem_text"] + "\n\n" + q2["stem_text"]
    
    # Merge options if both have them
    opts1 = json.loads(q1["options_json"]) if q1.get("options_json") else {}
    opts2 = json.loads(q2["options_json"]) if q2.get("options_json") else {}
    merged_opts = {**opts1, **opts2} if (opts1 or opts2) else None
    
    await db.jea_questions.update_one(
        {"id": question_id_1},
        {"$set": {
            "stem_text": merged_stem,
            "options_json": json.dumps(merged_opts) if merged_opts else None,
            "flags": [{"type": "MERGE_RESULT", "created_at": datetime.now(timezone.utc).isoformat()}]
        }}
    )
    
    # Delete second question
    await db.jea_questions.delete_one({"id": question_id_2})
    
    await create_audit_log(
        "JeaQuestion", 
        question_id_1, 
        "MERGE", 
        after_json=json.dumps({"merged_from": question_id_2})
    )
    
    return {"merged_id": question_id_1, "deleted_id": question_id_2}


# ============== Auto-Assign Subject ==============

# Subject keyword mappings
SUBJECT_KEYWORDS = {
    "PHY": [
        # Mechanics
        "momentum", "velocity", "acceleration", "force", "mass", "weight", "friction",
        "kinetic", "potential", "gravitational", "projectile", "collision", "impulse",
        "torque", "angular", "rotation", "oscillation", "pendulum", "spring",
        # Thermodynamics
        "temperature", "heat", "thermal", "entropy", "adiabatic", "isothermal",
        "isobaric", "isochoric", "carnot", "thermodynamic",
        # Waves & Optics
        "wavelength", "frequency", "amplitude", "interference", "diffraction",
        "refraction", "reflection", "lens", "mirror", "optical", "spectrum",
        "polarization", "electromagnetic", "photon",
        # Electricity & Magnetism
        "electric", "magnetic", "capacitor", "inductor", "resistor", "circuit",
        "current", "voltage", "ohm", "faraday", "coulomb", "gauss", "ampere",
        "electromagnetic", "induction", "flux",
        # Modern Physics
        "quantum", "photoelectric", "bohr", "nucleus", "radioactive", "decay",
        "binding energy", "fission", "fusion", "de broglie", "heisenberg",
        # General
        "particle", "joule", "watt", "newton", "meter", "second", "kilogram"
    ],
    "CHEM": [
        # General Chemistry
        "element", "compound", "molecule", "atom", "ion", "electron", "proton",
        "neutron", "orbital", "valence", "bonding", "covalent", "ionic",
        # Organic Chemistry
        "organic", "hydrocarbon", "alkane", "alkene", "alkyne", "benzene",
        "aromatic", "aldehyde", "ketone", "alcohol", "ether", "ester", "amine",
        "carboxylic", "amide", "polymer", "isomer", "stereochemistry", "chiral",
        "functional group", "substitution", "elimination", "addition",
        # Inorganic Chemistry
        "inorganic", "coordination", "ligand", "complex", "metal", "transition",
        "oxidation", "reduction", "redox", "electrochemistry", "galvanic",
        "electrolysis", "corrosion",
        # Physical Chemistry
        "equilibrium", "concentration", "molarity", "molality", "solubility",
        "ph", "buffer", "titration", "indicator", "catalyst", "kinetics",
        "reaction rate", "activation energy", "enthalpy", "gibbs",
        # General
        "periodic table", "molar", "avogadro", "stoichiometry", "empirical",
        "molecular formula", "precipitate", "aqueous", "solution", "reagent"
    ],
    "MATH": [
        # Calculus
        "integral", "derivative", "differentiation", "integration", "limit",
        "continuous", "differential equation", "maxima", "minima", "tangent",
        "normal", "curve", "area under",
        # Algebra
        "matrix", "determinant", "vector", "polynomial", "equation", "quadratic",
        "cubic", "root", "coefficient", "linear", "system of equations",
        "eigenvalue", "eigenvector",
        # Trigonometry
        "sin", "cos", "tan", "trigonometric", "angle", "radian", "degree",
        "triangle", "identity",
        # Coordinate Geometry
        "coordinate", "parabola", "ellipse", "hyperbola", "circle", "conic",
        "locus", "slope", "intercept", "asymptote",
        # Probability & Statistics
        "probability", "permutation", "combination", "factorial", "binomial",
        "mean", "variance", "standard deviation", "distribution",
        # Complex Numbers & Sequences
        "complex number", "imaginary", "argand", "sequence", "series",
        "arithmetic progression", "geometric progression", "convergent",
        # General
        "function", "domain", "range", "inverse", "logarithm", "exponential",
        "inequality", "modulus", "absolute value"
    ]
}


def detect_subject(text: str) -> tuple[str, float]:
    """
    Detect subject from text using keyword matching.
    Returns (subject, confidence_score)
    """
    if not text:
        return "UNKNOWN", 0.0
    
    text_lower = text.lower()
    scores = {"PHY": 0, "CHEM": 0, "MATH": 0}
    
    for subject, keywords in SUBJECT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Longer keywords get higher weight
                weight = 1 + (len(keyword) / 10)
                scores[subject] += weight
    
    total_score = sum(scores.values())
    if total_score == 0:
        return "UNKNOWN", 0.0
    
    best_subject = max(scores, key=scores.get)
    confidence = scores[best_subject] / total_score
    
    # Only assign if confidence is above threshold
    if confidence >= 0.4 and scores[best_subject] >= 2:
        return best_subject, confidence
    
    return "UNKNOWN", confidence


class AutoAssignResult(BaseModel):
    total_questions: int
    assigned: int
    skipped: int
    by_subject: Dict[str, int]
    details: List[Dict[str, Any]]


@admin_router.post("/catalog/{catalog_id}/auto-assign-subjects", response_model=AutoAssignResult)
async def auto_assign_subjects(
    catalog_id: str,
    force: bool = Query(False, description="Force reassign even if already assigned")
):
    """Auto-assign subjects to questions using keyword detection"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot modify LOCKED catalog")
    
    questions = await db.jea_questions.find({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    }).to_list(500)
    
    assigned = 0
    skipped = 0
    by_subject = {"PHY": 0, "CHEM": 0, "MATH": 0}
    details = []
    
    for q in questions:
        # Skip if already assigned and not forcing
        if q.get("subject") != "UNKNOWN" and not force:
            skipped += 1
            continue
        
        # Combine stem and options for detection
        text_to_analyze = q.get("stem_text", "")
        if q.get("options_json"):
            try:
                opts = json.loads(q["options_json"])
                text_to_analyze += " " + " ".join(opts.values())
            except:
                pass
        
        detected_subject, confidence = detect_subject(text_to_analyze)
        
        if detected_subject != "UNKNOWN":
            await db.jea_questions.update_one(
                {"id": q["id"]},
                {"$set": {"subject": detected_subject}}
            )
            assigned += 1
            by_subject[detected_subject] += 1
            details.append({
                "q_no": q["q_no"],
                "subject": detected_subject,
                "confidence": round(confidence, 2)
            })
        else:
            skipped += 1
            details.append({
                "q_no": q["q_no"],
                "subject": "UNKNOWN",
                "confidence": round(confidence, 2),
                "reason": "Low confidence"
            })
    
    # Also update yearspec sections
    yearspecs = await db.jea_yearspec_sections.find({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    }).to_list(100)
    
    for sec in yearspecs:
        if sec.get("subject") != "UNKNOWN" and not force:
            continue
        
        detected_subject, _ = detect_subject(sec.get("evidence_text", ""))
        if detected_subject != "UNKNOWN":
            await db.jea_yearspec_sections.update_one(
                {"id": sec["id"]},
                {"$set": {"subject": detected_subject}}
            )
    
    await create_audit_log(
        "JeaSourceCatalog",
        catalog_id,
        "AUTO_ASSIGN_SUBJECTS",
        after_json=json.dumps({"assigned": assigned, "skipped": skipped, "by_subject": by_subject})
    )
    
    return AutoAssignResult(
        total_questions=len(questions),
        assigned=assigned,
        skipped=skipped,
        by_subject=by_subject,
        details=details[:50]  # Limit details
    )


@admin_router.post("/questions/{question_id}/detect-subject")
async def detect_question_subject(question_id: str):
    """Detect subject for a single question (preview without saving)"""
    q = await db.jea_questions.find_one({"id": question_id})
    if not q:
        raise HTTPException(404, "Question not found")
    
    text_to_analyze = q.get("stem_text", "")
    if q.get("options_json"):
        try:
            opts = json.loads(q["options_json"])
            text_to_analyze += " " + " ".join(opts.values())
        except:
            pass
    
    detected_subject, confidence = detect_subject(text_to_analyze)
    
    # Find matching keywords for explanation
    text_lower = text_to_analyze.lower()
    matched_keywords = []
    for keyword in SUBJECT_KEYWORDS.get(detected_subject, []):
        if keyword in text_lower:
            matched_keywords.append(keyword)
    
    return {
        "current_subject": q.get("subject"),
        "detected_subject": detected_subject,
        "confidence": round(confidence, 2),
        "matched_keywords": matched_keywords[:10]
    }


# ============== Lock/Export Routes ==============

@admin_router.post("/catalog/{catalog_id}/lock", response_model=LockResult)
async def lock_snapshot(catalog_id: str):
    """Lock catalog after validation"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] == "LOCKED":
        return LockResult(locked=True, reason="Already locked")
    
    if cat["status"] != "PARSED":
        return LockResult(locked=False, reason="Must be PARSED before LOCK")
    
    # Validation gates
    questions = await db.jea_questions.find({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    }).to_list(500)
    
    if not questions:
        return LockResult(locked=False, reason="No questions parsed")
    
    # Check empty stems
    empty = [q["q_no"] for q in questions if not (q.get("stem_text") or "").strip()]
    if empty:
        return LockResult(locked=False, reason=f"Empty stems in Q: {empty[:10]}...")
    
    # Check missing options for SCQ/MCQ
    missing_opts = []
    for q in questions:
        if q.get("q_type") in ("SCQ", "MCQ_MULTI"):
            opts = json.loads(q["options_json"]) if q.get("options_json") else {}
            if len(opts) < 4:
                missing_opts.append(q["q_no"])
    
    if missing_opts:
        return LockResult(locked=False, reason=f"Missing options (need A-D) in Q: {missing_opts[:10]}...")
    
    # Check UNKNOWN subjects
    unknown = [q["q_no"] for q in questions if q.get("subject") == "UNKNOWN"]
    if unknown:
        return LockResult(locked=False, reason=f"UNKNOWN subject in Q: {unknown[:10]}... (must assign PHY/CHEM/MATH)")
    
    # Check yearspec
    yearspec = await db.jea_yearspec_sections.find({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    }).to_list(100)
    
    if not yearspec:
        return LockResult(locked=False, reason="No yearspec sections found")
    
    for sec in yearspec:
        if not (sec.get("evidence_text") or "").strip():
            return LockResult(locked=False, reason=f"Missing evidence_text in section {sec['section_code']}")
        if sec.get("subject") == "UNKNOWN":
            return LockResult(locked=False, reason=f"UNKNOWN subject in section {sec['section_code']}")
    
    # All validations passed - LOCK
    await db.jea_source_catalog.update_one(
        {"id": catalog_id},
        {"$set": {"status": "LOCKED"}}
    )
    
    await create_audit_log("JeaSourceCatalog", catalog_id, "LOCK")
    
    return LockResult(locked=True)


@admin_router.get("/catalog/{catalog_id}/export")
async def export_json_endpoint(catalog_id: str):
    """Export locked catalog to JSON"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] != "LOCKED":
        raise HTTPException(400, "Must be LOCKED before export")
    
    yearspec = await db.jea_yearspec_sections.find({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    }).to_list(100)
    
    questions = await db.jea_questions.find({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    }).sort("q_no", 1).to_list(500)
    
    yearspec_out = [serialize_doc(s) for s in yearspec]
    questions_out = [serialize_doc(q) for q in questions]
    
    quality_report = generate_quality_report(yearspec_out, questions_out)
    
    result = export_to_json(
        serialize_doc(cat),
        yearspec_out,
        questions_out,
        quality_report
    )
    
    await create_audit_log("JeaSourceCatalog", catalog_id, "EXPORT")
    
    return result


# ============== Audit Log Routes ==============

@admin_router.get("/audit-logs")
async def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """List audit logs"""
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if action:
        query["action"] = action
    
    cursor = db.jea_audit_logs.find(query).sort("created_at", -1).limit(limit)
    rows = await cursor.to_list(limit)
    return [serialize_doc(r) for r in rows]


# ============== Stats Route ==============

@admin_router.get("/stats")
async def get_stats():
    """Get overall statistics"""
    total_catalogs = await db.jea_source_catalog.count_documents({})
    by_status = {}
    for status in ["NEW", "DOWNLOADED", "PARSED", "LOCKED"]:
        by_status[status] = await db.jea_source_catalog.count_documents({"status": status})
    
    total_questions = await db.jea_questions.count_documents({})
    total_yearspec = await db.jea_yearspec_sections.count_documents({})
    
    flagged_questions = await db.jea_questions.count_documents({"flags": {"$ne": []}})
    unknown_subject = await db.jea_questions.count_documents({"subject": "UNKNOWN"})
    
    return {
        "catalogs": {
            "total": total_catalogs,
            "by_status": by_status
        },
        "questions": {
            "total": total_questions,
            "flagged": flagged_questions,
            "unknown_subject": unknown_subject
        },
        "yearspec_sections": total_yearspec
    }


# ============== Bulk Download ==============

class BulkDownloadItem(BaseModel):
    catalog_id: str
    year: int
    paper_no: int
    status: str
    error: Optional[str] = None
    sha256: Optional[str] = None
    pages_count: Optional[int] = None


class BulkDownloadResult(BaseModel):
    total: int
    success: int
    failed: int
    skipped: int
    items: List[BulkDownloadItem]


@admin_router.post("/bulk-download", response_model=BulkDownloadResult)
async def bulk_download(
    force: bool = Query(False, description="Force re-download even if already downloaded"),
    max_concurrent: int = Query(2, ge=1, le=5, description="Max concurrent downloads")
):
    """
    Bulk download all catalogs that are in NEW status.
    If force=True, re-downloads all creating new file_version.
    Resumable: if one fails, rest continue.
    """
    if not ALLOW_EXTERNAL_FETCH:
        raise HTTPException(400, "External fetch disabled")
    
    # Get all catalogs
    query = {} if force else {"status": "NEW"}
    catalogs = await db.jea_source_catalog.find(query).sort([("year", 1), ("paper_no", 1)]).to_list(100)
    
    results = []
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    import asyncio
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def download_one(cat):
        nonlocal success_count, failed_count, skipped_count
        
        async with semaphore:
            item = BulkDownloadItem(
                catalog_id=cat["id"],
                year=cat["year"],
                paper_no=cat["paper_no"],
                status="PENDING"
            )
            
            # Skip if already downloaded and not forcing
            if cat["status"] != "NEW" and not force:
                item.status = "SKIPPED"
                skipped_count += 1
                return item
            
            try:
                ensure_dirs()
                
                # Get next version
                latest = await db.jea_source_files.find_one(
                    {"catalog_id": cat["id"]},
                    sort=[("file_version", -1)]
                )
                next_ver = 1 if not latest else latest["file_version"] + 1
                
                dest = get_storage_path(cat["year"], cat["paper_no"], cat["language"], next_ver)
                
                # Download with timeout
                sha, nbytes, etag, lastmod = sha256_stream_to_file(cat["official_url"], dest, timeout=120)
                pages = count_pdf_pages(dest)
                
                # Store file record
                file_doc = {
                    "id": str(uuid.uuid4()),
                    "catalog_id": cat["id"],
                    "file_version": next_ver,
                    "sha256": sha,
                    "bytes": nbytes,
                    "mime": "application/pdf",
                    "storage_path": dest,
                    "downloaded_at": datetime.now(timezone.utc),
                    "http_etag": etag,
                    "http_last_modified": lastmod,
                    "pages_count": pages
                }
                await db.jea_source_files.insert_one(file_doc)
                
                # Update catalog status
                await db.jea_source_catalog.update_one(
                    {"id": cat["id"]},
                    {"$set": {"status": "DOWNLOADED"}}
                )
                
                logger.info(f"Downloaded {cat['year']} P{cat['paper_no']}: sha256={sha[:16]}..., pages={pages}")
                
                item.status = "SUCCESS"
                item.sha256 = sha
                item.pages_count = pages
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to download {cat['year']} P{cat['paper_no']}: {e}")
                item.status = "FAILED"
                item.error = str(e)[:200]
                failed_count += 1
            
            return item
    
    # Run downloads with controlled concurrency
    tasks = [download_one(cat) for cat in catalogs]
    results = await asyncio.gather(*tasks)
    
    await create_audit_log(
        "BulkDownload",
        "ALL",
        "BULK_DOWNLOAD",
        after_json=json.dumps({"success": success_count, "failed": failed_count, "skipped": skipped_count})
    )
    
    return BulkDownloadResult(
        total=len(catalogs),
        success=success_count,
        failed=failed_count,
        skipped=skipped_count,
        items=results
    )


# ============== PDF Preview ==============

from fastapi.responses import FileResponse

@admin_router.get("/catalog/{catalog_id}/preview-pdf")
async def preview_pdf(catalog_id: str):
    """Get the latest PDF file for preview"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    latest_file = await db.jea_source_files.find_one(
        {"catalog_id": catalog_id},
        sort=[("file_version", -1)]
    )
    if not latest_file:
        raise HTTPException(404, "No PDF file available")
    
    file_path = latest_file["storage_path"]
    if not os.path.exists(file_path):
        raise HTTPException(404, "PDF file not found on disk")
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"JEA_{cat['year']}_P{cat['paper_no']}_{cat['language']}.pdf"
    )


@admin_router.get("/catalog/{catalog_id}/pdf-info")
async def get_pdf_info(catalog_id: str):
    """Get PDF file metadata for preview"""
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    latest_file = await db.jea_source_files.find_one(
        {"catalog_id": catalog_id},
        sort=[("file_version", -1)]
    )
    if not latest_file:
        return {"has_pdf": False}
    
    return {
        "has_pdf": True,
        "file_id": latest_file["id"],
        "file_version": latest_file["file_version"],
        "sha256": latest_file["sha256"],
        "bytes": latest_file["bytes"],
        "pages_count": latest_file["pages_count"],
        "downloaded_at": latest_file["downloaded_at"].isoformat() if isinstance(latest_file["downloaded_at"], datetime) else latest_file["downloaded_at"]
    }


# ============== Subject Suggestions (Assistive Only) ==============

class SubjectSuggestion(BaseModel):
    question_id: str
    q_no: int
    current_subject: str
    suggested_subject: str
    confidence: float
    matched_keywords: List[str]
    applied: bool = False


class SuggestSubjectsResult(BaseModel):
    total_questions: int
    suggestions: List[SubjectSuggestion]
    summary: Dict[str, int]


@admin_router.get("/catalog/{catalog_id}/suggest-subjects", response_model=SuggestSubjectsResult)
async def suggest_subjects(catalog_id: str):
    """
    Generate subject suggestions for questions (ASSISTIVE ONLY).
    Does NOT auto-apply. Returns suggestions for manual review.
    """
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot suggest for LOCKED catalog")
    
    questions = await db.jea_questions.find({
        "year": cat["year"],
        "paper_no": cat["paper_no"]
    }).to_list(500)
    
    suggestions = []
    summary = {"PHY": 0, "CHEM": 0, "MATH": 0, "UNKNOWN": 0, "ALREADY_ASSIGNED": 0}
    
    for q in questions:
        # Skip if already assigned
        if q.get("subject") != "UNKNOWN":
            summary["ALREADY_ASSIGNED"] += 1
            continue
        
        # Combine stem and options for detection
        text_to_analyze = q.get("stem_text", "")
        if q.get("options_json"):
            try:
                opts = json.loads(q["options_json"])
                text_to_analyze += " " + " ".join(opts.values())
            except:
                pass
        
        detected_subject, confidence = detect_subject(text_to_analyze)
        
        # Find matched keywords
        text_lower = text_to_analyze.lower()
        matched = []
        for kw in SUBJECT_KEYWORDS.get(detected_subject, []):
            if kw in text_lower:
                matched.append(kw)
        
        suggestions.append(SubjectSuggestion(
            question_id=q["id"],
            q_no=q["q_no"],
            current_subject=q.get("subject", "UNKNOWN"),
            suggested_subject=detected_subject,
            confidence=round(confidence, 2),
            matched_keywords=matched[:10]
        ))
        
        summary[detected_subject] += 1
    
    return SuggestSubjectsResult(
        total_questions=len(questions),
        suggestions=suggestions,
        summary=summary
    )


class ApplySuggestionsRequest(BaseModel):
    suggestions: List[Dict[str, Any]]  # List of {question_id, subject}


@admin_router.post("/catalog/{catalog_id}/apply-suggestions")
async def apply_subject_suggestions(catalog_id: str, request: ApplySuggestionsRequest):
    """
    Apply selected subject suggestions (manual review step).
    Only applies suggestions explicitly passed.
    """
    cat = await db.jea_source_catalog.find_one({"id": catalog_id})
    if not cat:
        raise HTTPException(404, "Catalog not found")
    
    if cat["status"] == "LOCKED":
        raise HTTPException(400, "Cannot modify LOCKED catalog")
    
    applied = 0
    for sugg in request.suggestions:
        q_id = sugg.get("question_id")
        subject = sugg.get("subject")
        
        if not q_id or not subject or subject not in ["PHY", "CHEM", "MATH"]:
            continue
        
        result = await db.jea_questions.update_one(
            {"id": q_id, "year": cat["year"], "paper_no": cat["paper_no"]},
            {"$set": {"subject": subject}}
        )
        if result.modified_count > 0:
            applied += 1
    
    await create_audit_log(
        "JeaSourceCatalog",
        catalog_id,
        "APPLY_SUGGESTIONS",
        after_json=json.dumps({"applied": applied})
    )
    
    return {"applied": applied, "total_submitted": len(request.suggestions)}


# ============== BASELINE ENGINE ROUTER ==============

baseline_router = APIRouter(prefix="/baseline", tags=["baseline-engine"])


# ============== Task 2.2: Canonical QBank ==============

class QBankBuildResult(BaseModel):
    total_questions: int
    by_year: Dict[int, int]
    by_subject: Dict[str, int]
    by_type: Dict[str, int]
    build_time_ms: int


@baseline_router.post("/build-qbank")
async def build_canonical_qbank():
    """
    Build jea_qbank_v1 from all locked exports.
    Creates a canonical collection with stable qids.
    """
    import hashlib
    import time
    
    start = time.time()
    
    # Get all locked catalogs
    cats = await db.jea_source_catalog.find({"status": "LOCKED"}).to_list(100)
    
    if not cats:
        raise HTTPException(400, "No locked catalogs found")
    
    # Clear existing qbank
    await db.jea_qbank_v1.delete_many({})
    
    stats = {"by_year": {}, "by_subject": {}, "by_type": {}}
    total = 0
    
    for cat in cats:
        year = cat["year"]
        paper_no = cat["paper_no"]
        
        # Get file sha256
        file_doc = await db.jea_source_files.find_one(
            {"catalog_id": cat["id"]},
            sort=[("file_version", -1)]
        )
        file_sha = file_doc["sha256"] if file_doc else "unknown"
        
        # Get questions
        questions = await db.jea_questions.find({
            "year": year,
            "paper_no": paper_no
        }).to_list(500)
        
        # Get yearspec for marking rules
        yearspecs = await db.jea_yearspec_sections.find({
            "year": year,
            "paper_no": paper_no
        }).to_list(100)
        yearspec_map = {(s["section_code"], i): s for i, s in enumerate(yearspecs)}
        
        for q in questions:
            # Generate stable qid - include full question info for uniqueness
            qid_raw = f"{year}_{paper_no}_{q['section_code']}_{q['q_no']}_{q['id']}_{file_sha[:16]}"
            qid = hashlib.sha256(qid_raw.encode()).hexdigest()[:24]
            
            # Find matching yearspec
            matching_ys = None
            for (sec, idx), ys in yearspec_map.items():
                if sec == q["section_code"]:
                    matching_ys = ys
                    break
            
            qbank_doc = {
                "qid": qid,
                "year": year,
                "paperNo": paper_no,
                "sectionCode": q["section_code"],
                "subject": q["subject"],
                "qType": q["q_type"],
                "qNo": q["q_no"],
                "markingRuleRef": matching_ys["id"] if matching_ys else None,
                "stemText": q["stem_text"],
                "options": json.loads(q["options_json"]) if q.get("options_json") else None,
                "evidenceRef": matching_ys["id"] if matching_ys else None,
                "source": {
                    "sha256": file_sha,
                    "pageRefs": q.get("source_page_range")
                },
                "status": "LOCKED_ONLY",
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.jea_qbank_v1.insert_one(qbank_doc)
            total += 1
            
            # Update stats
            stats["by_year"][year] = stats["by_year"].get(year, 0) + 1
            stats["by_subject"][q["subject"]] = stats["by_subject"].get(q["subject"], 0) + 1
            stats["by_type"][q["q_type"]] = stats["by_type"].get(q["q_type"], 0) + 1
    
    # Create indexes
    await db.jea_qbank_v1.create_index([("year", 1), ("paperNo", 1), ("subject", 1), ("qType", 1)])
    await db.jea_qbank_v1.create_index([("qid", 1)], unique=True)
    await db.jea_qbank_v1.create_index([("stemText", "text")])
    
    elapsed = int((time.time() - start) * 1000)
    
    # Save build report
    report = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": total,
        "by_year": stats["by_year"],
        "by_subject": stats["by_subject"],
        "by_type": stats["by_type"],
        "build_time_ms": elapsed
    }
    
    with open("/app/memory/jea_qbank_build_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return QBankBuildResult(
        total_questions=total,
        by_year=stats["by_year"],
        by_subject=stats["by_subject"],
        by_type=stats["by_type"],
        build_time_ms=elapsed
    )


@baseline_router.get("/qbank/stats")
async def get_qbank_stats():
    """Get qbank statistics"""
    total = await db.jea_qbank_v1.count_documents({})
    
    # Aggregate by year
    by_year = {}
    for year in range(2021, 2026):
        by_year[year] = await db.jea_qbank_v1.count_documents({"year": year})
    
    # Aggregate by subject
    by_subject = {}
    for subj in ["PHY", "CHEM", "MATH"]:
        by_subject[subj] = await db.jea_qbank_v1.count_documents({"subject": subj})
    
    # Aggregate by type
    pipeline = [
        {"$group": {"_id": "$qType", "count": {"$sum": 1}}}
    ]
    by_type = {}
    async for doc in db.jea_qbank_v1.aggregate(pipeline):
        by_type[doc["_id"]] = doc["count"]
    
    return {
        "total": total,
        "by_year": by_year,
        "by_subject": by_subject,
        "by_type": by_type
    }


@baseline_router.get("/qbank/metrics-only")
async def get_metrics_only_export():
    """Export qbank without stems/options (privacy safe)"""
    docs = await db.jea_qbank_v1.find({}, {
        "_id": 0,
        "stemText": 0,
        "options": 0
    }).to_list(1000)
    
    return {
        "count": len(docs),
        "questions": docs
    }


# ============== Task 2.4: DI/TI Engine ==============

import re
import math

def compute_reading_len(stem: str, options: dict) -> int:
    """Compute total reading length"""
    total = len(stem or "")
    if options:
        total += sum(len(v) for v in options.values())
    return total


def compute_equation_count(text: str) -> int:
    """Count equations/formulas (heuristic)"""
    if not text:
        return 0
    # Count common math patterns
    patterns = [
        r'=',  # equations
        r'\^',  # exponents
        r'\\frac',  # fractions (LaTeX)
        r'\d+/\d+',  # fractions
        r'√|∫|∑|∏|∂',  # math symbols
        r'sin|cos|tan|log|ln|exp',  # functions
    ]
    count = 0
    for p in patterns:
        count += len(re.findall(p, text, re.IGNORECASE))
    return min(count, 20)  # Cap at 20


def compute_option_similarity(options: dict) -> float:
    """Compute how similar options are (0-1)"""
    if not options or len(options) < 2:
        return 0.0
    
    vals = list(options.values())
    # Simple: compare character overlap
    total_sim = 0
    pairs = 0
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            # Jaccard similarity on words
            words_i = set(vals[i].lower().split())
            words_j = set(vals[j].lower().split())
            if words_i or words_j:
                sim = len(words_i & words_j) / len(words_i | words_j) if (words_i | words_j) else 0
                total_sim += sim
                pairs += 1
    
    return total_sim / pairs if pairs > 0 else 0.0


def estimate_difficulty_heuristic(
    q_type: str,
    reading_len: int,
    equation_count: int,
    option_similarity: float,
    subject: str
) -> dict:
    """
    Estimate DI/TI/EI/II using deterministic heuristics.
    This is a baseline - can be enhanced with ML later.
    """
    # Base difficulty by type
    type_base_di = {
        "SCQ": 40,
        "MCQ_MULTI": 60,
        "INTEGER": 55,
        "MATCH": 65,
        "COMP_SET": 50,
        "OTHER": 50
    }
    
    # Base time by type (seconds)
    type_base_ti = {
        "SCQ": 120,
        "MCQ_MULTI": 180,
        "INTEGER": 150,
        "MATCH": 240,
        "COMP_SET": 180,
        "OTHER": 150
    }
    
    base_di = type_base_di.get(q_type, 50)
    base_ti = type_base_ti.get(q_type, 150)
    
    # Adjust for reading length (longer = harder)
    reading_factor = min(reading_len / 500, 2.0)  # Cap at 2x
    di_reading = reading_factor * 10
    ti_reading = reading_factor * 30
    
    # Adjust for equations (more = harder)
    eq_factor = min(equation_count / 5, 2.0)
    di_eq = eq_factor * 8
    ti_eq = eq_factor * 20
    
    # Adjust for option similarity (higher = trickier = higher EI)
    ei = option_similarity * 60 + 20  # Base 20, max 80
    
    # Integration index (heuristic based on reading + equations)
    ii = min((reading_len / 200 + equation_count) * 10, 100)
    
    # Final values
    di = min(max(base_di + di_reading + di_eq, 10), 95)
    ti = base_ti + ti_reading + ti_eq
    
    # Step count estimate
    step_count = max(2, int(equation_count * 1.5 + reading_len / 200))
    
    return {
        "DI": round(di, 1),
        "TI": round(ti, 1),
        "EI": round(ei, 1),
        "II": round(ii, 1),
        "features": {
            "reading_len": reading_len,
            "equation_count": equation_count,
            "option_similarity": round(option_similarity, 3),
            "step_count_est": step_count
        }
    }


@baseline_router.post("/compute-metrics")
async def compute_all_metrics():
    """
    Compute DI/TI/EI/II for all questions in qbank.
    Stores in jea_qmetrics_v1 collection.
    """
    import time
    start = time.time()
    
    # Get all questions from qbank
    questions = await db.jea_qbank_v1.find({}).to_list(1000)
    
    if not questions:
        raise HTTPException(400, "QBank is empty. Build qbank first.")
    
    # Clear existing metrics
    await db.jea_qmetrics_v1.delete_many({})
    
    computed = 0
    errors = []
    
    for q in questions:
        try:
            # Compute features
            reading_len = compute_reading_len(q.get("stemText", ""), q.get("options"))
            equation_count = compute_equation_count(q.get("stemText", ""))
            option_sim = compute_option_similarity(q.get("options"))
            
            # Estimate metrics
            metrics = estimate_difficulty_heuristic(
                q.get("qType", "OTHER"),
                reading_len,
                equation_count,
                option_sim,
                q.get("subject", "UNKNOWN")
            )
            
            # Store
            metric_doc = {
                "qid": q["qid"],
                "year": q["year"],
                "paperNo": q["paperNo"],
                "subject": q["subject"],
                "qType": q["qType"],
                "DI": metrics["DI"],
                "TI": metrics["TI"],
                "EI": metrics["EI"],
                "II": metrics["II"],
                "features": metrics["features"],
                "compute_version": "v1_heuristic",
                "computed_at": datetime.now(timezone.utc)
            }
            
            await db.jea_qmetrics_v1.insert_one(metric_doc)
            computed += 1
            
        except Exception as e:
            errors.append({"qid": q.get("qid"), "error": str(e)})
    
    # Create indexes
    await db.jea_qmetrics_v1.create_index([("qid", 1)], unique=True)
    await db.jea_qmetrics_v1.create_index([("year", 1), ("paperNo", 1), ("subject", 1)])
    
    elapsed = int((time.time() - start) * 1000)
    
    # Save coverage report
    coverage = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(questions),
        "computed": computed,
        "errors": len(errors),
        "coverage_pct": round(computed / len(questions) * 100, 2),
        "compute_time_ms": elapsed
    }
    
    with open("/app/memory/qmetrics_coverage_report.json", "w") as f:
        json.dump(coverage, f, indent=2)
    
    with open("/app/memory/qmetrics_quarantine_list.json", "w") as f:
        json.dump({"errors": errors}, f, indent=2)
    
    return {
        "computed": computed,
        "total": len(questions),
        "errors": len(errors),
        "time_ms": elapsed
    }


# ============== Task 2.5: Baseline Profiles ==============

import statistics

@baseline_router.post("/build-baselines")
async def build_baseline_profiles():
    """Build baseline_2025 and envelope_2021_2025 profiles"""
    
    # Get all metrics
    all_metrics = await db.jea_qmetrics_v1.find({}).to_list(1000)
    
    if not all_metrics:
        raise HTTPException(400, "No metrics computed. Run compute-metrics first.")
    
    # Separate 2025 and full envelope
    metrics_2025 = [m for m in all_metrics if m["year"] == 2025]
    
    def build_profile(metrics, name):
        """Build profile from list of metrics"""
        if not metrics:
            return None
        
        dis = [m["DI"] for m in metrics]
        tis = [m["TI"] for m in metrics]
        
        # DI histogram (10 bins)
        di_bins = [0] * 10
        for d in dis:
            bin_idx = min(int(d / 10), 9)
            di_bins[bin_idx] += 1
        
        # TI histogram (bins: 0-60, 60-120, 120-180, 180-240, 240-300, 300+)
        ti_bins = [0] * 6
        ti_bounds = [60, 120, 180, 240, 300, float('inf')]
        for t in tis:
            for i, bound in enumerate(ti_bounds):
                if t <= bound:
                    ti_bins[i] += 1
                    break
        
        # Subject-wise means
        by_subject = {}
        for subj in ["PHY", "CHEM", "MATH"]:
            subj_metrics = [m for m in metrics if m["subject"] == subj]
            if subj_metrics:
                by_subject[subj] = {
                    "count": len(subj_metrics),
                    "DI_mean": round(statistics.mean([m["DI"] for m in subj_metrics]), 2),
                    "TI_mean": round(statistics.mean([m["TI"] for m in subj_metrics]), 2),
                    "DI_std": round(statistics.stdev([m["DI"] for m in subj_metrics]) if len(subj_metrics) > 1 else 0, 2),
                    "TI_std": round(statistics.stdev([m["TI"] for m in subj_metrics]) if len(subj_metrics) > 1 else 0, 2)
                }
        
        # Type-wise means
        by_type = {}
        types = set(m["qType"] for m in metrics)
        for qtype in types:
            type_metrics = [m for m in metrics if m["qType"] == qtype]
            if type_metrics:
                by_type[qtype] = {
                    "count": len(type_metrics),
                    "DI_mean": round(statistics.mean([m["DI"] for m in type_metrics]), 2),
                    "TI_mean": round(statistics.mean([m["TI"] for m in type_metrics]), 2)
                }
        
        return {
            "name": name,
            "total_questions": len(metrics),
            "DI": {
                "mean": round(statistics.mean(dis), 2),
                "std": round(statistics.stdev(dis) if len(dis) > 1 else 0, 2),
                "min": round(min(dis), 2),
                "max": round(max(dis), 2),
                "histogram": di_bins
            },
            "TI": {
                "mean": round(statistics.mean(tis), 2),
                "std": round(statistics.stdev(tis) if len(tis) > 1 else 0, 2),
                "min": round(min(tis), 2),
                "max": round(max(tis), 2),
                "histogram": ti_bins
            },
            "by_subject": by_subject,
            "by_type": by_type
        }
    
    # Build profiles
    baseline_2025 = build_profile(metrics_2025, "baseline_2025")
    envelope_2021_2025 = build_profile(all_metrics, "envelope_2021_2025")
    
    # Add year breakdown to envelope
    if envelope_2021_2025:
        envelope_2021_2025["by_year"] = {}
        for year in range(2021, 2026):
            year_metrics = [m for m in all_metrics if m["year"] == year]
            if year_metrics:
                envelope_2021_2025["by_year"][str(year)] = {
                    "count": len(year_metrics),
                    "DI_mean": round(statistics.mean([m["DI"] for m in year_metrics]), 2),
                    "TI_mean": round(statistics.mean([m["TI"] for m in year_metrics]), 2)
                }
    
    # Save profiles
    baseline_2025["generated_at"] = datetime.now(timezone.utc).isoformat()
    envelope_2021_2025["generated_at"] = datetime.now(timezone.utc).isoformat()
    
    with open("/app/memory/baseline_profile_2025.json", "w") as f:
        json.dump(baseline_2025, f, indent=2)
    
    with open("/app/memory/envelope_profile_2021_2025.json", "w") as f:
        json.dump(envelope_2021_2025, f, indent=2)
    
    # Cache in DB - convert dict keys to strings for MongoDB
    def stringify_keys(d):
        if isinstance(d, dict):
            return {str(k): stringify_keys(v) for k, v in d.items()}
        return d
    
    await db.jea_baselines.delete_many({})
    await db.jea_baselines.insert_one({**stringify_keys(baseline_2025), "_type": "baseline_2025"})
    await db.jea_baselines.insert_one({**stringify_keys(envelope_2021_2025), "_type": "envelope_2021_2025"})
    
    return {
        "baseline_2025": baseline_2025,
        "envelope_2021_2025": envelope_2021_2025
    }


@baseline_router.get("/profiles")
async def get_cached_profiles():
    """Get cached baseline profiles (fast)"""
    import time
    start = time.time()
    
    baseline = await db.jea_baselines.find_one({"_type": "baseline_2025"}, {"_id": 0})
    envelope = await db.jea_baselines.find_one({"_type": "envelope_2021_2025"}, {"_id": 0})
    
    elapsed = int((time.time() - start) * 1000)
    
    return {
        "baseline_2025": baseline,
        "envelope_2021_2025": envelope,
        "fetch_time_ms": elapsed
    }


# ============== Task 2.6: Distribution Match ==============

def ks_test_statistic(sample1, sample2):
    """Compute two-sample Kolmogorov-Smirnov statistic"""
    if not sample1 or not sample2:
        return 1.0
    
    # Sort both samples
    s1 = sorted(sample1)
    s2 = sorted(sample2)
    n1, n2 = len(s1), len(s2)
    
    # Compute ECDF and max difference
    all_vals = sorted(set(s1 + s2))
    max_diff = 0
    
    for v in all_vals:
        ecdf1 = sum(1 for x in s1 if x <= v) / n1
        ecdf2 = sum(1 for x in s2 if x <= v) / n2
        max_diff = max(max_diff, abs(ecdf1 - ecdf2))
    
    return round(max_diff, 4)


@baseline_router.post("/compare-distribution")
async def compare_distribution(
    year_a: int = Query(..., description="Year to compare"),
    paper_a: Optional[int] = Query(None, description="Paper number (optional, both if not specified)")
):
    """
    Compare distribution of year_a against baseline_2025.
    Returns PASS/FAIL with KS statistics.
    """
    # Get baseline metrics (2025)
    baseline_metrics = await db.jea_qmetrics_v1.find({"year": 2025}).to_list(500)
    
    # Get comparison metrics
    query = {"year": year_a}
    if paper_a:
        query["paperNo"] = paper_a
    compare_metrics = await db.jea_qmetrics_v1.find(query).to_list(500)
    
    if not baseline_metrics or not compare_metrics:
        raise HTTPException(400, "Insufficient data for comparison")
    
    # Extract DI and TI values
    baseline_di = [m["DI"] for m in baseline_metrics]
    baseline_ti = [m["TI"] for m in baseline_metrics]
    compare_di = [m["DI"] for m in compare_metrics]
    compare_ti = [m["TI"] for m in compare_metrics]
    
    # KS tests
    ks_di = ks_test_statistic(compare_di, baseline_di)
    ks_ti = ks_test_statistic(compare_ti, baseline_ti)
    
    # Type-wise DI drift
    type_drift = {}
    types = set(m["qType"] for m in compare_metrics)
    for qtype in types:
        base_type = [m["DI"] for m in baseline_metrics if m["qType"] == qtype]
        comp_type = [m["DI"] for m in compare_metrics if m["qType"] == qtype]
        if base_type and comp_type:
            drift = statistics.mean(comp_type) - statistics.mean(base_type)
            type_drift[qtype] = round(drift, 2)
    
    # Subject-wise TI drift
    subject_drift = {}
    for subj in ["PHY", "CHEM", "MATH"]:
        base_subj = [m["TI"] for m in baseline_metrics if m["subject"] == subj]
        comp_subj = [m["TI"] for m in compare_metrics if m["subject"] == subj]
        if base_subj and comp_subj:
            base_mean = statistics.mean(base_subj)
            comp_mean = statistics.mean(comp_subj)
            drift_pct = (comp_mean - base_mean) / base_mean if base_mean else 0
            subject_drift[subj] = round(drift_pct, 4)
    
    # Thresholds
    KS_DI_THRESHOLD = 0.08
    KS_TI_THRESHOLD = 0.10
    TYPE_DRIFT_THRESHOLD = 4
    SUBJ_DRIFT_THRESHOLD = 0.10
    
    # Check pass/fail
    ks_di_pass = ks_di <= KS_DI_THRESHOLD
    ks_ti_pass = ks_ti <= KS_TI_THRESHOLD
    type_pass = all(abs(d) <= TYPE_DRIFT_THRESHOLD for d in type_drift.values())
    subj_pass = all(abs(d) <= SUBJ_DRIFT_THRESHOLD for d in subject_drift.values())
    
    overall_pass = ks_di_pass and ks_ti_pass and type_pass and subj_pass
    
    result = {
        "comparison": f"{year_a} P{paper_a or 'all'} vs baseline_2025",
        "overall": "PASS" if overall_pass else "FAIL",
        "metrics": {
            "KS_DI": {"value": ks_di, "threshold": KS_DI_THRESHOLD, "pass": ks_di_pass},
            "KS_TI": {"value": ks_ti, "threshold": KS_TI_THRESHOLD, "pass": ks_ti_pass},
            "type_DI_drift": {"values": type_drift, "threshold": TYPE_DRIFT_THRESHOLD, "pass": type_pass},
            "subject_TI_drift": {"values": subject_drift, "threshold": SUBJ_DRIFT_THRESHOLD, "pass": subj_pass}
        },
        "sample_sizes": {
            "baseline_2025": len(baseline_metrics),
            "comparison": len(compare_metrics)
        }
    }
    
    return result


@baseline_router.get("/distribution-contract")
async def get_distribution_contract():
    """Get the distribution match contract/thresholds"""
    contract = {
        "version": "v1",
        "thresholds": {
            "KS_DI": {"max": 0.08, "description": "Kolmogorov-Smirnov stat for DI distribution"},
            "KS_TI": {"max": 0.10, "description": "Kolmogorov-Smirnov stat for TI distribution"},
            "type_DI_drift": {"max": 4, "description": "Max DI mean drift per question type"},
            "subject_TI_drift": {"max": 0.10, "description": "Max TI mean drift % per subject"}
        },
        "baseline": "2025",
        "envelope": "2021-2025"
    }
    
    with open("/app/memory/distribution_match_contract_v1.json", "w") as f:
        json.dump(contract, f, indent=2)
    
    return contract


# Include baseline router
admin_router.include_router(baseline_router)


# Include routers
api_router.include_router(admin_router)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
