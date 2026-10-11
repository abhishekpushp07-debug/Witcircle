"""Content-addressed, immutable private question packs shared across attempts.
Students never receive this payload directly: delivered-question allowlists gate all reads.
"""

import json, zlib, hashlib
from collections import OrderedDict
from .db import db, now

_cache = OrderedDict()
_CACHE_MAX_BYTES = 32 * 1024 * 1024
_cache_bytes = 0


def remember(key, raw):
    global _cache_bytes
    if key in _cache:
        _cache_bytes -= len(_cache.pop(key))
    _cache[key] = raw
    _cache_bytes += len(raw)
    while _cache_bytes > _CACHE_MAX_BYTES and _cache:
        _, value = _cache.popitem(last=False)
        _cache_bytes -= len(value)


async def seal(questions):
    safe = [
        {
            k: v
            for k, v in q.items()
            if k not in ["response", "outcome", "marks", "marked"]
        }
        for q in questions
    ]
    raw = json.dumps(
        safe, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    key = hashlib.sha256(raw).hexdigest()
    await db.tejas_packs.update_one(
        {"_id": key},
        {
            "$setOnInsert": {
                "schema": 1,
                "payload": zlib.compress(raw, 6),
                "sha256": key,
                "count": len(safe),
                "bytes": len(raw),
                "created_at": now(),
            }
        },
        upsert=True,
    )
    remember(key, raw)
    return key


async def unpack(key):
    raw = _cache.get(key)
    if raw is None:
        p = await db.tejas_packs.find_one({"_id": key})
        if not p:
            raise RuntimeError(
                "Frozen content pack is missing; do not substitute new content."
            )
        raw = zlib.decompress(p["payload"])
        if hashlib.sha256(raw).hexdigest() != key:
            raise RuntimeError("Frozen content integrity check failed.")
        remember(key, raw)
    else:
        _cache.move_to_end(key)
    return json.loads(raw)


async def hydrate(a):
    if a and "questions" not in a and a.get("pack_id"):
        a["questions"] = await unpack(a["pack_id"])
    return a


async def insert_attempt(a):
    from .db import attempts

    a["pack_id"] = await seal(a["questions"])
    a["count"] = len(a["questions"])
    record = {k: v for k, v in a.items() if k not in ["questions", "_id"]}
    await attempts.insert_one(record)
