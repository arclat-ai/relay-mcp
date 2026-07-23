# Running Relay

## What's in this repo

| Part | What it does | Required? |
|------|-------------|-----------|
| `mcp_server/` | The MCP server — core product | Yes |
| `backend/` | FastAPI — auth + API key issuance only | Yes (for key registration) |
| `frontend/` | Next.js — landing page + register/login | Optional |

---

## 1. MCP Server (the core product)

### Install locally for development

```bash
# From repo root
pip install -e .
```

This installs the `relay-mcp` command via `pyproject.toml`.

### Add to Claude Code

Edit `~/.claude/claude_code_config.json`:

```json
{
  "mcpServers": {
    "relay": {
      "command": "relay-mcp",
      "env": {
        "RELAY_API_KEY": "your_key_here"
      }
    }
  }
}
```

For production (PyPI install):
```json
{
  "mcpServers": {
    "relay": {
      "command": "uvx",
      "args": ["relay-mcp"],
      "env": {
        "RELAY_API_KEY": "your_key_here"
      }
    }
  }
}
```

Restart Claude Code, then say: `"Audit this codebase for latency issues"`

### MCP tools available

- `audit_codebase(directory, api_key)` — scan a Python project, get ranked findings
- `get_findings(severity?, finding_type?)` — filter results from last audit
- `apply_fix(file_path, finding_id, dry_run=true)` — patch a file (dry run by default)

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RELAY_API_KEY` | — | Your API key (set in MCP config) |
| `RELAY_API_URL` | `https://api.arclat.com` | Backend URL for usage sync |

Usage data is stored locally at `~/.relay/usage.db` (SQLite) and synced to the backend every 10 audits.

---

## 2. Backend (FastAPI — auth + billing)

### Requirements

- Python 3.11+
- A Supabase project (free tier is fine)

### First-time: create the database tables

1. Open your Supabase project → **SQL Editor → New query**
2. Paste and run the contents of `supabase_schema.sql` (repo root)

That creates the `users` and `usage` tables with RLS policies.

### Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Environment variables

Copy `.env.example` to `.env` and fill in:

```
SUPABASE_URL=...
SUPABASE_KEY=...
DATABASE_URL=postgresql+asyncpg://...
CORS_ORIGINS=["http://localhost:3000"]
```

### Run

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account, returns `api_key` |
| POST | `/auth/login` | Get `api_key` for existing user |
| GET | `/auth/me` | Current user info + usage |
| POST | `/auth/usage/sync` | Called by MCP server to sync usage |

---

## 3. Frontend (Next.js — optional)

### Requirements

- Node.js 18+

### Setup

```bash
cd frontend
npm install
```

### Environment variables

Create `frontend/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Run

```bash
cd frontend
npm run dev
```

App at `http://localhost:3000`.

### Pages

| Path | Description |
|------|-------------|
| `/` | Landing page |
| `/auth/register` | Create account + get API key |
| `/auth/login` | Login |
| `/dashboard` | Usage stats + API key display |

---

## Running everything together

```bash
# Terminal 1 — backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend (optional)
cd frontend && npm run dev
```

The MCP server runs as a subprocess managed by Claude Code — you don't start it manually.

---

## Publishing to PyPI (for `uvx relay-mcp`)

```bash
pip install build twine
python -m build
twine upload dist/*
```

Package name: `relay-mcp` (defined in `pyproject.toml`).
