import os, hashlib
from datetime import datetime, timezone, timedelta
import bcrypt, jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, EmailStr, field_validator
from starlette.concurrency import run_in_threadpool
from .db import db, users, sessions, uid, now, get

router = APIRouter(prefix="/api/auth", tags=["Accounts"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=64)
    name: str = Field(default="Student", min_length=1, max_length=80)
    exam: str = "JEE Main"
    consent: bool = False

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode()) > 72:
            raise ValueError("Use a password of at most 72 UTF-8 bytes.")
        return value


def view(u):
    return {k: u[k] for k in ["id", "name", "email", "role", "exam"] if k in u}


def hashpw(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def verify(p, h):
    return bcrypt.checkpw(p.encode(), h.encode())


def token(u, sid, kind, seconds):
    return jwt.encode(
        {"sub": u["id"], "sid": sid, "type": kind, "exp": int(now()) + seconds},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )


def cookies(response, u, sid):
    for kind, duration in [("access", 900), ("refresh", 604800)]:
        response.set_cookie(
            kind + "_token",
            token(u, sid, kind, duration),
            max_age=duration,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
        )


async def new_session(u, response):
    sid = uid()
    await sessions.insert_one(
        {
            "id": sid,
            "user_id": u["id"],
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        }
    )
    cookies(response, u, sid)
    return view(u)


async def current(request: Request):
    tok = request.cookies.get("access_token")
    try:
        p = jwt.decode(tok, os.environ["JWT_SECRET"], algorithms=["HS256"])
        if p["type"] != "access":
            raise ValueError()
        sess = await sessions.find_one(
            {
                "id": p["sid"],
                "user_id": p["sub"],
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            }
        )
        if not sess:
            raise ValueError()
        u = await users.find_one({"id": p["sub"]}, {"_id": 0, "password_hash": 0})
        if not u:
            raise ValueError()
        return u
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise HTTPException(401, "Sign in to continue. Your saved work is retained.")


async def staff(u=Depends(current)):
    if u["role"] not in ["owner", "reviewer"]:
        raise HTTPException(
            403, "Content Studio is restricted to authorized reviewers."
        )
    return u


async def owner(u=Depends(staff)):
    if u["role"] != "owner":
        raise HTTPException(
            403, "Only the owner can publish or manage reviewer access."
        )
    return u


@router.post("/register")
async def register(data: Credentials, response: Response):
    if not data.consent:
        raise HTTPException(
            400, "Please acknowledge the privacy notice to create an account."
        )
    if data.exam not in ["JEE Main", "BITSAT"]:
        raise HTTPException(400, "Choose JEE Main or BITSAT.")
    u = {
        "id": uid(),
        "email": str(data.email).lower(),
        "name": data.name.strip(),
        "exam": data.exam,
        "role": "student",
        "password_hash": await run_in_threadpool(hashpw, data.password),
        "created_at": now(),
        "consent_at": now(),
    }
    from pymongo.errors import DuplicateKeyError

    try:
        await users.insert_one(u)
    except DuplicateKeyError:
        raise HTTPException(
            409,
            "An account cannot be created with these details. Try signing in instead.",
        )
    return await new_session(u, response)


@router.post("/login")
async def login(data: Credentials, request: Request, response: Response):
    email = str(data.email).lower()
    key = hashlib.sha256((request.client.host + ":" + email).encode()).hexdigest()
    limit = await db.tejas_login_limits.find_one({"_id": key})
    if (
        limit
        and limit.get("count", 0) >= 5
        and limit["expires_at"].replace(tzinfo=timezone.utc)
        > datetime.now(timezone.utc)
    ):
        raise HTTPException(429, "Too many sign-in attempts. Please wait 15 minutes.")
    u = await users.find_one({"email": email})
    if not u or not await run_in_threadpool(verify, data.password, u["password_hash"]):
        await db.tejas_login_limits.update_one(
            {"_id": key},
            {
                "$inc": {"count": 1},
                "$set": {
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15)
                },
            },
            upsert=True,
        )
        raise HTTPException(401, "Email or password is incorrect.")
    await db.tejas_login_limits.delete_one({"_id": key})
    return await new_session(u, response)


@router.get("/me")
async def me(u=Depends(current)):
    return view(u)


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    try:
        p = jwt.decode(
            request.cookies.get("refresh_token"),
            os.environ["JWT_SECRET"],
            algorithms=["HS256"],
        )
        if p["type"] != "refresh":
            raise ValueError()
        if not await sessions.find_one(
            {
                "id": p["sid"],
                "user_id": p["sub"],
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            }
        ):
            raise ValueError()
        u = await get(users, p["sub"])
        cookies(response, u, p["sid"])
        return view(u)
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise HTTPException(401, "Your session has ended. Sign in again.")


@router.post("/logout")
async def logout(request: Request, response: Response):
    for name in ["access_token", "refresh_token"]:
        try:
            p = jwt.decode(
                request.cookies.get(name),
                os.environ["JWT_SECRET"],
                algorithms=["HS256"],
            )
            await sessions.delete_one({"id": p["sid"]})
        except Exception:
            pass
        response.delete_cookie(
            name, path="/", secure=True, httponly=True, samesite="lax"
        )
    return {"ok": True}


@router.patch("/preferences")
async def preferences(data: dict, u=Depends(current)):
    exam = data.get("exam")
    if exam not in ["JEE Main", "BITSAT"]:
        raise HTTPException(400, "Choose a supported exam.")
    await users.update_one({"id": u["id"]}, {"$set": {"exam": exam}})
    return {"exam": exam}


async def seed_owner():
    email = os.environ["ADMIN_EMAIL"].lower()
    if not await users.find_one({"email": email}):
        await users.insert_one(
            {
                "id": uid(),
                "email": email,
                "name": "Tejas Owner",
                "role": "owner",
                "exam": "JEE Main",
                "password_hash": await run_in_threadpool(
                    hashpw, os.environ["ADMIN_PASSWORD"]
                ),
                "created_at": now(),
            }
        )
