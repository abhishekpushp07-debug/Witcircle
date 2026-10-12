"""Hot-path answer acknowledgement: compact schema, optimistic revision and DB-time fence."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from .auth import current
from .db import attempts, get, now
from tejas_core import normalize_answer

router = APIRouter(prefix="/api/attempts", tags=["Acknowledged answers"])


class AnswerWrite(BaseModel):
    value: str = Field(default="", max_length=30)
    marked: bool = False
    revision: int = Field(ge=1)
    request_id: str = Field(min_length=8, max_length=100)


@router.put("/{id}/answers/{qid}")
async def save_answer(id: str, qid: str, data: AnswerWrite, u=Depends(current)):
    try:
        UUID(qid)
    except ValueError:
        raise HTTPException(404, "Question not found.")
    a = await attempts.find_one(
        {"id": id, "user_id": u["id"]},
        {
            "_id": 0,
            "id": 1,
            "user_id": 1,
            "status": 1,
            "deadline": 1,
            "pack_id": 1,
            f"answers.{qid}": 1,
            f"response_schema.{qid}": 1,
        },
    )
    if not a:
        raise HTTPException(404, "Attempt not found.")
    q = a.get("response_schema", {}).get(qid)
    if not q:
        # Compatibility only for attempts created before compact response schemas existed.
        full = await get(attempts, id)
        q = next((x for x in full["questions"] if x["id"] == qid), None)
    if not q:
        raise HTTPException(404, "Question does not belong to this attempt.")
    old = a.get("answers", {}).get(qid, {})
    if old.get("request_id") == data.request_id:
        if old.get("value") != data.value or old.get("marked") != data.marked:
            raise HTTPException(
                409, "This save identifier was already used for different content."
            )
        return {"accepted": old, "server_now": now()}
    if a["status"] != "active" or (a["deadline"] and now() >= a["deadline"]):
        from .attempts import expire

        await expire(a)
        raise HTTPException(
            409, "The attempt has ended. Late drafts are not accepted or scored."
        )
    try:
        value = normalize_answer(data.value, q["type"])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if value and q["type"] == "mcq" and value not in q["options"]:
        raise HTTPException(400, "Choose an available option.")
    if data.revision != old.get("revision", 0) + 1:
        raise HTTPException(
            409,
            "Another tab or device changed this answer. Reload the saved response before editing.",
        )
    entry = {**data.model_dump(), "normalized_value": value}
    epoch = {"$divide": [{"$toLong": "$$NOW"}, 1000]}
    guard = {
        "id": id,
        "status": "active",
        "$expr": {"$or": [{"$eq": ["$deadline", 0]}, {"$gt": ["$deadline", epoch]}]},
        "$or": [{f"answers.{qid}.revision": data.revision - 1}]
        + ([{f"answers.{qid}": {"$exists": False}}] if data.revision == 1 else []),
    }
    updated = await attempts.find_one_and_update(
        guard,
        [
            {"$set": {f"answers.{qid}": {"$literal": entry}}},
            {
                "$set": {
                    f"answers.{qid}.accepted_at": epoch,
                    "visited": {"$setUnion": [{"$ifNull": ["$visited", []]}, [qid]]},
                }
            },
        ],
        projection={"_id": 0, f"answers.{qid}": 1},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(
            409,
            "Save conflict or deadline reached. Reconnect to check the accepted response.",
        )
    return {"accepted": updated["answers"][qid], "server_now": now()}
