import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCredentials(BaseModel):
    email: str
    password: str


class UsageSyncPayload(BaseModel):
    api_key: str
    month: str
    count: int


@router.post("/register")
async def register(credentials: UserCredentials):
    api_key = "arc_" + secrets.token_urlsafe(24)
    # TODO: persist to Supabase users table
    return {"message": "Registered successfully", "api_key": api_key}


@router.post("/login")
async def login(credentials: UserCredentials):
    # TODO: verify via Supabase Auth and return stored api_key
    return {"message": "Login successful", "api_key": "arc_placeholder"}


@router.get("/me")
async def me():
    # TODO: return user info + usage from Supabase
    return {"email": "user@example.com", "plan": "free", "usage": {"count": 0, "limit": 20}}


@router.post("/usage/sync")
async def usage_sync(payload: UsageSyncPayload):
    # TODO: upsert into Supabase usage table
    return {"synced": True, "api_key": payload.api_key, "month": payload.month, "count": payload.count}
