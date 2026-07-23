import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from postgrest.exceptions import APIError
from app.dependencies import anon_client, admin_client, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / response schemas ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""
    company: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UsageSyncRequest(BaseModel):
    api_key: str
    month: str   # e.g. "2026-06"
    count: int


# ── Helpers ─────────────────────────────────────────────────────────────────

def _generate_api_key() -> str:
    # Relay-branded keys; legacy arc_ keys remain valid everywhere.
    return "rly_" + secrets.token_urlsafe(24)


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    sb_admin = admin_client()

    # 1. Create Supabase auth user via admin client (synchronous, immediately committed)
    try:
        auth_resp = sb_admin.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "email_confirm": True,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if auth_resp.user is None:
        raise HTTPException(status_code=400, detail="Registration failed.")

    user_id = auth_resp.user.id
    api_key = _generate_api_key()

    # 2. Insert into public users table
    try:
        sb_admin.table("users").insert({
            "id": user_id,
            "email": body.email,
            "name": body.name or None,
            "company": body.company or None,
            "plan": "free",
            "api_key": api_key,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user record: {e}")

    return {
        "message": "Registered successfully. Check your email to confirm your account.",
        "api_key": api_key,
    }


@router.post("/login")
def login(body: LoginRequest):
    sb_anon = anon_client()
    sb_admin = admin_client()

    # 1. Sign in with Supabase Auth
    try:
        auth_resp = sb_anon.auth.sign_in_with_password({"email": body.email, "password": body.password})
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if auth_resp.user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = auth_resp.user.id

    # 2. Fetch api_key from users table, backfill if row is missing (orphaned auth accounts)
    try:
        result = sb_admin.table("users").select("api_key, plan").eq("id", user_id).single().execute()
    except APIError:
        api_key = _generate_api_key()
        sb_admin.table("users").insert({
            "id": user_id,
            "email": body.email,
            "plan": "free",
            "api_key": api_key,
        }).execute()
        result = sb_admin.table("users").select("api_key, plan").eq("id", user_id).single().execute()

    return {
        "api_key": result.data["api_key"],
        "plan": result.data["plan"],
        "access_token": auth_resp.session.access_token,
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    sb_admin = admin_client()
    user_id = current_user["id"]

    # Fetch user row
    user_result = sb_admin.table("users").select("email, name, company, plan, api_key, created_at").eq("id", user_id).single().execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch current month usage
    month = _current_month()
    usage_result = sb_admin.table("usage").select("audit_count, last_audit_at").eq("user_id", user_id).eq("month", month).execute()
    usage_row = usage_result.data[0] if usage_result.data else {"audit_count": 0, "last_audit_at": None}

    plan_limits = {"free": 20, "pro": None, "team": None, "enterprise": None}
    limit = plan_limits.get(user_result.data["plan"])

    return {
        **user_result.data,
        "usage": {
            "count": usage_row["audit_count"],
            "limit": limit,
            "month": month,
            "last_audit_at": usage_row["last_audit_at"],
        },
    }


@router.post("/usage/sync")
def usage_sync(body: UsageSyncRequest):
    """Called by the MCP server every 10 audits to sync local SQLite count to Supabase."""
    sb_admin = admin_client()

    # Look up user_id from api_key
    try:
        user_result = sb_admin.table("users").select("id").eq("api_key", body.api_key).single().execute()
    except APIError:
        raise HTTPException(status_code=404, detail="Unknown api_key")

    user_id = user_result.data["id"]

    # Upsert usage row — take the higher of the two counts to avoid overwriting newer data
    existing = sb_admin.table("usage").select("audit_count").eq("user_id", user_id).eq("month", body.month).execute()
    current_count = existing.data[0]["audit_count"] if existing.data else 0
    final_count = max(current_count, body.count)

    sb_admin.table("usage").upsert({
        "user_id": user_id,
        "month": body.month,
        "audit_count": final_count,
        "last_audit_at": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="user_id,month").execute()

    return {"synced": True, "month": body.month, "count": final_count}
