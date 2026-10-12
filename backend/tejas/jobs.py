"""Durable heavy-work jobs with atomic leases; no scheduler runs inside the application."""

import os, secrets, asyncio, logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks,
    Request,
    Response,
)
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .db import jobs, sets, files, attempts, db, uid, now, get, audit
from .auth import current
from tejas_core import build_questions, generate_report
from tejas_storage import get_object, put_object

router = APIRouter(prefix="/api", tags=["Processing"])
_capacity = asyncio.Semaphore(2)


async def enqueue(kind, user_id, set_id, payload):
    key = (
        payload["attempt_id"] + "-" + payload.get("score_version", "original")
        if kind == "report"
        else payload.get("key", set_id)
    )
    id = kind + "-" + key
    j = {
        "id": id,
        "kind": kind,
        "user_id": user_id,
        "set_id": set_id,
        "payload": payload,
        "status": "queued",
        "progress": 0,
        "created_at": now(),
        "lease_until": 0,
        "error": "",
    }
    try:
        await jobs.insert_one(j)
    except DuplicateKeyError:
        existing = await get(jobs, id)
        if existing["status"] == "failed" or (
            kind == "extract" and existing["status"] == "done"
        ):
            await jobs.update_one(
                {"id": id},
                {"$set": {k: v for k, v in j.items() if k not in ["id", "_id"]}},
            )
        else:
            return {
                k: v for k, v in existing.items() if k not in ["_id", "path", "payload"]
            }
    return {k: v for k, v in j.items() if k not in ["_id", "path", "payload"]}


async def run_job(id):
    async with _capacity:
        lease = uid()
        j = await jobs.find_one_and_update(
            {
                "id": id,
                "$or": [
                    {"status": "queued"},
                    {"status": "running", "lease_until": {"$lt": now()}},
                ],
            },
            {
                "$set": {
                    "status": "running",
                    "progress": 10,
                    "lease": lease,
                    "lease_until": now() + 900,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if not j:
            return
        try:
            if j["kind"] == "extract":
                qf = await get(files, j["payload"]["qfile"])
                sf = await get(files, j["payload"]["sfile"])
                qraw = await run_in_threadpool(get_object, qf["path"])
                sraw = await run_in_threadpool(get_object, sf["path"])
                qs = await run_in_threadpool(
                    build_questions,
                    qraw,
                    sraw,
                    qf["id"],
                    sf["id"],
                    j["payload"].get("known_tejas", False),
                )
                guard = {"id": j["set_id"]}
                if "revision" in j["payload"]:
                    guard["revision"] = j["payload"]["revision"]
                updated = await sets.update_one(
                    guard,
                    {
                        "$set": {"questions": qs, "status": "review"},
                        "$inc": {"revision": 1},
                    },
                )
                if not updated.modified_count:
                    raise ValueError(
                        "Draft changed during extraction. Existing reviewer edits were preserved; rerun from the current revision."
                    )
                message = (
                    f"{len(qs)} draft questions extracted. Human review is required."
                    if qs
                    else "No question boundaries detected. Add questions manually and select source regions."
                )
            elif j["kind"] == "regrade":
                from .corrections import run_regrade

                message = await run_regrade(j)
            elif j["kind"] == "report":
                from .corrections import with_grade

                a = await with_grade(
                    await get(attempts, j["payload"]["attempt_id"]),
                    j["payload"].get("score_version"),
                )
                ids = {
                    r["file_id"]
                    for q in a["questions"]
                    for r in q.get("q_refs", []) + q.get("s_refs", [])
                }
                sources = {}
                for fid in ids:
                    f = await get(files, fid)
                    sources[fid] = await run_in_threadpool(get_object, f["path"])
                await jobs.update_one(
                    {"id": id, "lease": lease}, {"$set": {"progress": 35}}
                )
                pdf = await run_in_threadpool(
                    generate_report, a, lambda fid: sources[fid]
                )
                await jobs.update_one(
                    {"id": id, "lease": lease}, {"$set": {"progress": 80}}
                )
                path = await run_in_threadpool(
                    put_object, f"tejas/reports/{a['user_id']}/{id}.pdf", pdf
                )
                await jobs.update_one(
                    {"id": id, "lease": lease}, {"$set": {"path": path}}
                )
                message = "Your complete results and matched solutions are ready."
            else:
                raise ValueError("Unknown job type")
            await jobs.update_one(
                {"id": id, "lease": lease},
                {
                    "$set": {
                        "status": "done",
                        "progress": 100,
                        "message": message,
                        "finished_at": now(),
                    }
                },
            )
            await audit(
                j["user_id"], j["kind"].title() + " completed", j["set_id"], message
            )
        except Exception:
            logging.exception("Tejas job failed: %s", id)
            await jobs.update_one(
                {"id": id, "lease": lease},
                {
                    "$set": {
                        "status": "failed",
                        "error": "Processing could not finish. Your original files and saved attempt are safe. Retry this job.",
                        "progress": 0,
                    }
                },
            )


@router.get("/jobs/{id}")
async def status(id: str, u=Depends(current)):
    j = await get(jobs, id)
    if j["user_id"] != u["id"] and not (
        j["kind"] == "extract" and u["role"] in ["owner", "reviewer"]
    ):
        raise HTTPException(404, "Job not found.")
    return {k: v for k, v in j.items() if k not in ["path", "payload", "lease"]}


@router.post("/jobs/{id}/retry")
async def retry_job(id: str, bg: BackgroundTasks, u=Depends(current)):
    j = await status(id, u)
    if j["status"] == "running" and j["lease_until"] > now():
        raise HTTPException(
            409, "This job is still processing. Check its progress shortly."
        )
    await jobs.update_one({"id": id}, {"$set": {"status": "queued", "error": ""}})
    bg.add_task(run_job, id)
    return {"id": id, "status": "queued"}


@router.get("/jobs/{id}/download")
async def download(id: str, u=Depends(current)):
    j = await get(jobs, id)
    if j["kind"] != "report" or j["user_id"] != u["id"]:
        raise HTTPException(404, "Report not found.")
    if j["status"] != "done":
        raise HTTPException(
            409, "The report is not ready yet. Retry generation if needed."
        )
    return Response(
        await run_in_threadpool(get_object, j["path"]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="Tejas-results-and-solutions.pdf"'
        },
    )


async def maintenance():
    from .attempts import finalize

    expired = (
        await attempts.find(
            {"status": "active", "deadline": {"$gt": 0, "$lte": now()}}, {"id": 1}
        )
        .limit(1000)
        .to_list(1000)
    )
    for a in expired:
        await finalize(a["id"], "time_limit")
    pending = (
        await jobs.find(
            {
                "$or": [
                    {"status": "queued"},
                    {"status": "running", "lease_until": {"$lt": now()}},
                ]
            },
            {"id": 1},
        )
        .limit(10)
        .to_list(10)
    )
    for j in pending:
        await run_job(j["id"])
    await db.tejas_operations.update_one(
        {"id": "maintenance"},
        {
            "$set": {
                "last_run": now(),
                "expired": len(expired),
                "recovered_jobs": len(pending),
            }
        },
        upsert=True,
    )


@router.post("/cron/maintenance")
async def cron(request: Request, bg: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    expected = os.environ.get("WEBHOOK_CRON_SECRET", "")
    provided = request.headers.get("authorization", "")
    if not expected or not secrets.compare_digest(provided, "Bearer " + expected):
        raise HTTPException(401, "Unauthorized")
    try:
        body = await request.json()
        rid = request.headers.get("x-webhook-id") or body.get("run_id")
        if (
            not isinstance(body, dict)
            or body.get("event") != "schedule.triggered"
            or not rid
        ):
            raise ValueError()
    except Exception:
        raise HTTPException(400, "Invalid schedule envelope")
    try:
        await db.tejas_cron_receipts.insert_one({"_id": rid, "at": now()})
    except DuplicateKeyError:
        return {"accepted": True, "duplicate": True}
    bg.add_task(maintenance)
    return {"accepted": True}
