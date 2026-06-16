"""
SQLite-based local usage tracker. Works offline.
Syncs to the remote API every 10 audits.
"""
import sqlite3
import datetime
import os
import threading
from pathlib import Path

import httpx

_DB_PATH = Path.home() / ".arclat" / "usage.db"
_REMOTE = os.getenv("ARCLAT_API_URL", "https://arclat-production.up.railway.app")
_lock = threading.Lock()

FREE_LIMIT = 20


def _conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            api_key TEXT NOT NULL,
            month   TEXT NOT NULL,
            count   INTEGER DEFAULT 0,
            plan    TEXT DEFAULT 'free',
            PRIMARY KEY (api_key, month)
        )
    """)
    conn.commit()
    return conn


def _month() -> str:
    return datetime.date.today().strftime("%Y-%m")


def _sync_remote(api_key: str, month: str, count: int) -> None:
    try:
        httpx.post(
            f"{_REMOTE}/auth/usage/sync",
            json={"api_key": api_key, "month": month, "count": count},
            timeout=5,
        )
    except Exception:
        pass  # sync is best-effort


def validate_and_check(api_key: str) -> tuple[bool, str]:
    """Returns (allowed, reason). Fetches plan from remote on first use."""
    if not api_key or not api_key.startswith("arc_"):
        return False, "Invalid API key format. Get your key at https://arclat.vercel.app"

    month = _month()
    with _lock:
        conn = _conn()
        row = conn.execute(
            "SELECT count, plan FROM usage WHERE api_key=? AND month=?",
            (api_key, month),
        ).fetchone()

        if row is None:
            # First use this month — fetch plan from remote
            try:
                resp = httpx.post(
                    f"{_REMOTE}/auth/login",
                    json={"api_key": api_key},
                    timeout=5,
                )
                plan = resp.json().get("plan", "free") if resp.is_success else "free"
            except Exception:
                plan = "free"
            conn.execute(
                "INSERT OR IGNORE INTO usage (api_key, month, count, plan) VALUES (?,?,0,?)",
                (api_key, month, plan),
            )
            conn.commit()
            row = (0, plan)

        count, plan = row

    if plan == "free" and count >= FREE_LIMIT:
        return False, (
            f"Free plan limit reached ({FREE_LIMIT} audits/month). "
            "Upgrade at https://arclat.vercel.app"
        )
    return True, ""


def increment(api_key: str) -> int:
    month = _month()
    with _lock:
        conn = _conn()
        conn.execute(
            "INSERT INTO usage (api_key, month, count) VALUES (?,?,1) "
            "ON CONFLICT(api_key, month) DO UPDATE SET count=count+1",
            (api_key, month),
        )
        conn.commit()
        new_count = conn.execute(
            "SELECT count FROM usage WHERE api_key=? AND month=?", (api_key, month)
        ).fetchone()[0]

    _sync_remote(api_key, month, new_count)

    return new_count
