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
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
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
