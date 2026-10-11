"""Bounded, source-free catalogue projection. Never retrieve keys for discovery."""

from .db import sets

PROJECT = {
    "_id": 0,
    "id": 1,
    "title": 1,
    "exam": 1,
    "year": 1,
    "status": 1,
    "rules": 1,
    "version": 1,
    "source": 1,
    "attribution": 1,
    "created_at": 1,
    "audience": 1,
    "allowed_emails": 1,
    "expires": 1,
    "questions.number": 1,
    "questions.type": 1,
    "questions.subject": 1,
    "questions.approved": 1,
}


async def page(query, page=1, size=20):
    return (
        await sets.find(query, PROJECT)
        .sort([("created_at", -1), ("id", 1)])
        .skip((max(1, min(page, 10000)) - 1) * size)
        .limit(size)
        .to_list(size)
    )
