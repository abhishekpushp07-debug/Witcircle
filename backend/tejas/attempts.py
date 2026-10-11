import copy
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool
from .db import attempts, sets, files, db, uid, now, get, audit, clean
from .auth import current
from .packs import hydrate, insert_attempt
from .catalog import page as catalogue_page
from .content import summary, permitted, validate_refs
from tejas_core import public_question, normalize_answer, score_attempt, crop_png
from tejas_storage import get_object

router = APIRouter(prefix="/api", tags=["Practice"])


class Start(BaseModel):
    start_key: str = Field(min_length=8, max_length=100)
    device_checked: bool = False
    preview: bool = False


class Answer(BaseModel):
    value: str = Field(default="", max_length=30)
    marked: bool = False
    revision: int = Field(ge=1)
    request_id: str = Field(min_length=8, max_length=100)


def delivered(q):
    p = public_question(q)
    p["asset_count"] = len(q.get("q_refs", []))
    p.pop("q_refs", None)
    # Native extracted text can be inaccurate. Only reviewed source alt text is exposed in image mode.
    if q.get("render_mode") == "source":
        p["text"] = q.get("accessible_text", "")
    return p


async def owned(id, u):
    a = await get(attempts, id)
    if a["user_id"] != u["id"]:
        raise HTTPException(404, "Attempt not found.")
    return a


async def finalize(id, reason="submitted"):
    t = now()
    # Freeze accepted responses atomically; concurrent saves cannot race into completed ledger.
    a = await attempts.find_one_and_update(
        {"id": id, "status": "active"},
        [
            {
                "$set": {
                    "status": "completed",
                    "submitted_at": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$gt": ["$deadline", 0]},
                                    {"$lte": ["$deadline", t]},
                                ]
                            },
                            "$deadline",
                            t,
                        ]
                    },
                    "reason": reason,
                    "receipt": id,
                }
            }
        ],
        return_document=ReturnDocument.AFTER,
    )
    if not a:
        return await get(attempts, id)
    a = await hydrate(a)
    result = score_attempt(a)
    await attempts.update_one({"id": id}, {"$set": {"summary": result["summary"]}})
    await audit(a["user_id"], "Attempt completed", id, reason)
    a["summary"] = result["summary"]
    return clean(a)


async def expire(a):
    a = await hydrate(a)
    if a["status"] == "active" and a["deadline"] and now() >= a["deadline"]:
        return await finalize(a["id"], "time_limit")
    return a


def attempt_view(a):
    fields = [
        "id",
        "set_id",
        "title",
        "exam",
        "mode",
        "version",
        "rules",
        "started_at",
        "deadline",
        "status",
        "answers",
        "submitted_at",
        "receipt",
        "reason",
        "summary",
    ]
    return {
        **{k: a.get(k) for k in fields},
        "questions": [delivered(q) for q in a["questions"]],
        "server_now": now(),
        "count": len(a["questions"]),
    }


@router.get("/my/sets")
async def my_sets(u=Depends(current)):
    data = await catalogue_page({"status": "published"}, size=100)
    return {"items": [summary(s) for s in data if permitted(s, u)]}


@router.get("/my/sets/{id}")
async def my_set(id: str, u=Depends(current)):
    s = await get(sets, id)
    if s["status"] != "published" or not permitted(s, u):
        raise HTTPException(404, "This set is not available to your account.")
    return summary(s)


@router.post("/sets/{id}/preflight")
async def preflight(id: str, data: dict, u=Depends(current)):
    s = await get(sets, id)
    preview = data.get("preview") and u["role"] in ["owner", "reviewer"]
    if not preview and (s["status"] != "published" or not permitted(s, u)):
        raise HTTPException(404, "This set is not available.")
    if not s["questions"]:
        raise HTTPException(400, "This set has no questions yet.")
    for q in s["questions"]:
        await validate_refs(s, q)
    await db.tejas_preflight.update_one(
        {"user_id": u["id"], "set_id": id},
        {
            "$set": {
                "revision": s["revision"],
                "at": now(),
                "test_response": str(data.get("test_response", ""))[:30],
            }
        },
        upsert=True,
    )
    return {
        "ok": True,
        "message": "Connection, source assets and test response verified. No attempt or timer has started.",
        "server_now": now(),
    }


@router.post("/sets/{id}/start")
async def start(id: str, data: Start, u=Depends(current)):
    existing = await attempts.find_one(
        {"user_id": u["id"], "start_key": data.start_key}, {"_id": 0}
    )
    if existing:
        return attempt_view(await expire(existing))
    s = await get(sets, id)
    preview = data.preview and u["role"] in ["owner", "reviewer"]
    mode = "preview" if preview else "practice"
    active = await attempts.find_one(
        {"user_id": u["id"], "set_id": id, "mode": mode, "status": "active"}, {"_id": 0}
    )
    if active:
        return attempt_view(await expire(active))
    if not preview and (s["status"] != "published" or not permitted(s, u)):
        raise HTTPException(404, "This set is not available to start.")
    if not data.device_checked:
        raise HTTPException(400, "Complete the device and content check first.")
    pf = await db.tejas_preflight.find_one(
        {
            "user_id": u["id"],
            "set_id": id,
            "revision": s["revision"],
            "at": {"$gt": now() - 1800},
        }
    )
    if not pf:
        raise HTTPException(
            400, "Run the connection and content check again before starting."
        )
    if not s["questions"]:
        raise HTTPException(400, "No questions are available.")
    a = {
        "id": uid(),
        "user_id": u["id"],
        "set_id": id,
        "start_key": data.start_key,
        "title": s["title"],
        "exam": s["exam"],
        "version": s["version"],
        "rules": copy.deepcopy(s["rules"]),
        "questions": copy.deepcopy(s["questions"]),
        "attribution": s.get("attribution", ""),
        "report_allowed": bool(s.get("rights_report")),
        "mode": mode,
        "status": "active",
        "answers": {},
        "started_at": now(),
        "deadline": 0,
        "parent_attempt": None,
    }
    if a["rules"]["minutes"]:
        a["deadline"] = a["started_at"] + a["rules"]["minutes"] * 60
    try:
        await insert_attempt(a)
    except DuplicateKeyError:
        a = await attempts.find_one(
            {"user_id": u["id"], "set_id": id, "mode": mode, "status": "active"}
        )
        if not a:
            a = await attempts.find_one(
                {"user_id": u["id"], "start_key": data.start_key}
            )
    await audit(u["id"], "Attempt started", a["id"], mode)
    return attempt_view(await hydrate(a))


@router.get("/attempts")
async def history(page: int = 1, u=Depends(current)):
    data = (
        await attempts.find({"user_id": u["id"]}, {"_id": 0})
        .sort("started_at", -1)
        .skip((max(1, page) - 1) * 20)
        .limit(20)
        .to_list(20)
    )
    result = []
    for a in data:
        a = await expire(a)
        v = attempt_view(a)
        v.pop("questions")
        v.pop("answers")
        result.append(v)
    return {"items": result, "page": page}


@router.get("/attempts/{id}")
async def read_attempt(id: str, u=Depends(current)):
    return attempt_view(await expire(await owned(id, u)))


@router.put("/attempts/{id}/answers/{qid}")
async def save_answer(id: str, qid: str, data: Answer, u=Depends(current)):
    a = await owned(id, u)
    q = next((q for q in a["questions"] if q["id"] == qid), None)
    if not q:
        raise HTTPException(404, "Question does not belong to this attempt.")
    old = a.get("answers", {}).get(qid, {})
    if old.get("request_id") == data.request_id:
        return {"accepted": old, "server_now": now()}
    if a["status"] != "active" or (a["deadline"] and now() >= a["deadline"]):
        await expire(a)
        raise HTTPException(
            409, "The attempt has ended. Late local drafts are not accepted or scored."
        )
    try:
        value = normalize_answer(data.value, q["type"])
    except ValueError as e:
        raise HTTPException(400, str(e))
    if value and q["type"] == "mcq" and value not in q["options"]:
        raise HTTPException(400, "Choose an available option.")
    if data.revision != old.get("revision", 0) + 1:
        raise HTTPException(
            409,
            "Another tab or device changed this answer. Reload the saved response before editing.",
        )
    entry = {**data.model_dump(), "value": data.value.strip(), "accepted_at": now()}
    # Compare-and-swap at the DB boundary: no in-process lock or last-write-wins.
    f = {
        "id": id,
        "status": "active",
        "$and": [
            {"$or": [{"deadline": 0}, {"deadline": {"$gt": now()}}]},
            {
                "$or": [{f"answers.{qid}.revision": data.revision - 1}]
                + (
                    [{f"answers.{qid}": {"$exists": False}}]
                    if data.revision == 1
                    else []
                )
            },
        ],
    }
    res = await attempts.update_one(f, {"$set": {f"answers.{qid}": entry}})
    if not res.modified_count:
        raise HTTPException(
            409,
            "Save conflict or deadline reached. Reconnect to check the accepted response.",
        )
    return {"accepted": entry, "server_now": now()}


@router.post("/attempts/{id}/submit")
async def submit(id: str, u=Depends(current)):
    a = await owned(id, u)
    if a["status"] == "active":
        a = await finalize(
            id,
            "time_limit" if a["deadline"] and now() >= a["deadline"] else "submitted",
        )
    return {
        "id": id,
        "receipt": id,
        "status": a["status"],
        "submitted_at": a["submitted_at"],
    }


@router.get("/attempts/{id}/results")
async def results(id: str, u=Depends(current)):
    a = await expire(await owned(id, u))
    if a["status"] != "completed":
        raise HTTPException(403, "Solutions are released only after submission.")
    result = score_attempt(a)
    for q in result["questions"]:
        q["asset_count"] = len(q.get("q_refs", []))
        q["solution_asset_count"] = len(q.get("s_refs", []))
    return {
        **attempt_view(a),
        **result,
        "report_allowed": a.get("report_allowed", False),
        "attribution": a.get("attribution", ""),
    }


@router.get("/attempts/{id}/questions/{qid}/asset/{kind}/{index}")
async def asset(id: str, qid: str, kind: str, index: int, u=Depends(current)):
    a = await expire(await owned(id, u))
    if kind not in ["question", "solution"] or (
        kind == "solution" and a["status"] != "completed"
    ):
        raise HTTPException(403, "Solution assets remain private until submission.")
    q = next((q for q in a["questions"] if q["id"] == qid), None)
    if not q:
        raise HTTPException(404, "Question not found.")
    refs = q.get("q_refs" if kind == "question" else "s_refs", [])
    if not 0 <= index < len(refs):
        raise HTTPException(404, "Asset not found.")
    f = await get(files, refs[index]["file_id"])
    raw = await run_in_threadpool(get_object, f["path"])
    return Response(
        await run_in_threadpool(crop_png, raw, refs[index]), media_type="image/png"
    )


@router.post("/attempts/{id}/retry")
async def retry(id: str, data: dict, u=Depends(current)):
    a = await expire(await owned(id, u))
    if a["status"] != "completed":
        raise HTTPException(400, "Complete the original attempt first.")
    qs = [
        q
        for q in score_attempt(a)["questions"]
        if q["outcome"] in ["incorrect", "skipped"]
    ]
    if not qs:
        raise HTTPException(
            400, "There are no incorrect or skipped questions to retry."
        )
    start_key = str(data.get("start_key", ""))
    if len(start_key) < 8:
        raise HTTPException(400, "A retry request identifier is required.")
    existing = await attempts.find_one({"user_id": u["id"], "start_key": start_key})
    if existing:
        return {"id": existing["id"]}
    active = await attempts.find_one(
        {"user_id": u["id"], "set_id": a["set_id"], "mode": "retry", "status": "active"}
    )
    if active:
        return {"id": active["id"]}
    a.update(
        {
            "id": uid(),
            "title": a["title"] + " — Mistake retry",
            "parent_attempt": id,
            "start_key": start_key,
            "questions": qs,
            "rules": {**a["rules"], "minutes": 0},
            "mode": "retry",
            "status": "active",
            "answers": {},
            "started_at": now(),
            "deadline": 0,
        }
    )
    for k in ["_id", "summary", "submitted_at", "receipt", "reason"]:
        a.pop(k, None)
    try:
        await insert_attempt(a)
    except DuplicateKeyError:
        a = await attempts.find_one(
            {
                "user_id": u["id"],
                "set_id": a["set_id"],
                "mode": "retry",
                "status": "active",
            }
        )
    await audit(
        u["id"],
        "Mistake retry started",
        a["id"],
        f"Original {id}; untimed; repeated exposure",
    )
    return {"id": a["id"]}


@router.post("/attempts/{id}/report")
async def report(id: str, bg: BackgroundTasks, u=Depends(current)):
    a = await expire(await owned(id, u))
    if a["status"] != "completed":
        raise HTTPException(403, "Submit before generating your report.")
    if not a.get("report_allowed"):
        raise HTTPException(
            403,
            "Personal report redistribution rights have not been confirmed for this source.",
        )
    from .jobs import enqueue, run_job

    j = await enqueue("report", u["id"], a["set_id"], {"attempt_id": id})
    bg.add_task(run_job, j["id"])
    return j
