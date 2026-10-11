from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from .auth import owner
from .db import users, audit

router = APIRouter(prefix="/api/studio", tags=["Reviewer authorization"])


class Access(BaseModel):
    email: EmailStr
    role: str


@router.post("/reviewers")
async def update_access(data: Access, u=Depends(owner)):
    if data.role not in ["student", "reviewer"]:
        raise HTTPException(400, "Choose reviewer or student access.")
    target = await users.find_one({"email": str(data.email).lower()})
    if not target:
        raise HTTPException(404, "Ask this reviewer to register an account first.")
    if target["role"] == "owner":
        raise HTTPException(400, "Owner privileges cannot be changed here.")
    await users.update_one({"id": target["id"]}, {"$set": {"role": data.role}})
    await audit(u["id"], "Reviewer access updated", target["id"], data.role)
    return {"ok": True}
