# Arclat — AI Agent Latency Optimizer

## What is Arclat
Arclat audits your AI agent pipeline, finds exactly where you're losing time, and tells you how to fix it — in minutes, not weeks. You submit your agent's logs (JSON format) and Arclat detects latency bottlenecks, ranks them by impact, and provides specific fix recommendations with before/after code examples.

## Tech Stack
* **Backend:** Python 3.11, FastAPI, Celery, Redis, SQLAlchemy 2.0
* **Frontend:** Next.js 14, Tailwind CSS, TypeScript
* **Database:** PostgreSQL (via Supabase)

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url> arclat
   cd arclat
   ```

2. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your local or Supabase credentials if necessary
   ```

3. **Start backend, database, and redis via Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Run Database Migrations (Run inside backend or against the exposed DB port):**
   ```bash
   alembic upgrade head
   ```

5. **Start frontend application:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Running Tests
To test the custom latency bottleneck detectors:
```bash
cd backend
pytest tests/
```

## Built By
Stravon
