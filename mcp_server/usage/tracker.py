import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path.home() / ".arclat" / "usage.db"

PLAN_LIMITS = {
    "free": 20,
    "pro": None,   # unlimited
    "team": None,
    "enterprise": None,
}

SYNC_INTERVAL = 10  # sync to remote every N audits


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            api_key TEXT PRIMARY KEY,
            plan    TEXT NOT NULL DEFAULT 'free'
        );
        CREATE TABLE IF NOT EXISTS usage (
            api_key    TEXT NOT NULL,
            month      TEXT NOT NULL,
            count      INTEGER NOT NULL DEFAULT 0,
            last_audit TEXT,
            PRIMARY KEY (api_key, month)
        );
    """)
    conn.commit()


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


class UsageTracker:
    def validate_key(self, api_key: str) -> dict | None:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT api_key, plan FROM users WHERE api_key = ?", (api_key,)
            ).fetchone()
            if row is None:
                # Auto-register unknown keys as free-tier for local dev convenience
                conn.execute(
                    "INSERT OR IGNORE INTO users (api_key, plan) VALUES (?, 'free')",
                    (api_key,),
                )
                conn.commit()
                return {"api_key": api_key, "plan": "free"}
            return dict(row)

    def check_limit(self, api_key: str) -> bool:
        user = self.validate_key(api_key)
        if user is None:
            return False

        limit = PLAN_LIMITS.get(user["plan"])
        if limit is None:
            return True  # unlimited plan

        month = _current_month()
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT count FROM usage WHERE api_key = ? AND month = ?",
                (api_key, month),
            ).fetchone()
            count = row["count"] if row else 0
            return count < limit

    def increment(self, api_key: str) -> int:
        month = _current_month()
        now = datetime.now(timezone.utc).isoformat()
        with _get_conn() as conn:
            conn.execute(
                """
                INSERT INTO usage (api_key, month, count, last_audit)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(api_key, month) DO UPDATE SET
                    count = count + 1,
                    last_audit = excluded.last_audit
                """,
                (api_key, month, now),
            )
            conn.commit()
            row = conn.execute(
                "SELECT count FROM usage WHERE api_key = ? AND month = ?",
                (api_key, month),
            ).fetchone()
            new_count = row["count"]

        if new_count % SYNC_INTERVAL == 0:
            self._sync_remote(api_key, month, new_count)

        return new_count

    def get_usage(self, api_key: str) -> dict:
        user = self.validate_key(api_key)
        plan = user["plan"] if user else "free"
        limit = PLAN_LIMITS.get(plan)
        month = _current_month()

        with _get_conn() as conn:
            row = conn.execute(
                "SELECT count, last_audit FROM usage WHERE api_key = ? AND month = ?",
                (api_key, month),
            ).fetchone()

        count = row["count"] if row else 0
        last_audit = row["last_audit"] if row else None

        # First day of next month
        now = datetime.now(timezone.utc)
        if now.month == 12:
            resets_at = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc).isoformat()
        else:
            resets_at = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc).isoformat()

        return {
            "count": count,
            "limit": limit,
            "plan": plan,
            "resets_at": resets_at,
            "last_audit": last_audit,
        }

    def _sync_remote(self, api_key: str, month: str, count: int) -> None:
        """Best-effort sync to remote API. Silently fails if unavailable."""
        try:
            import httpx
            from mcp_server.config import settings
            httpx.post(
                f"{settings.API_BASE_URL}/usage/sync",
                json={"api_key": api_key, "month": month, "count": count},
                timeout=5,
            )
        except Exception:
            pass
