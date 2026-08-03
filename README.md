# Open Source SaaS Platform

## Overview

Production-ready open-source SaaS platform foundation. The backend currently
provides FastAPI bootstrapping, Supabase PostgreSQL, JWT authentication, and
Just-In-Time platform user provisioning.

## Technology Stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui
- Backend: FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2
- Database / Auth: Supabase PostgreSQL + Supabase Auth (JWT)
- Documentation: Markdown-based docs
- Local infrastructure: Docker Compose

## Project Structure

```text
.
|-- .github/
|   `-- workflows/
|-- backend/
|-- docs/
|   |-- API.md
|   |-- DEVELOPMENT.md
|   `-- ROADMAP.md
|-- frontend/
|-- .editorconfig
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- LICENSE
`-- README.md
```

## Setup

Backend setup:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# fill DATABASE_URL, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend setup:

```bash
cd frontend
cp .env.example .env.local
# fill NEXT_PUBLIC_APP_URL, NEXT_PUBLIC_API_URL,
# NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
npm install
npm run dev
```

### Supabase dashboard configuration

In the Supabase project used by local development:

1. **Project Settings → API**
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL` / `SUPABASE_URL`
   - Publishable key → `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_PUBLISHABLE_KEY`
2. **Authentication → URL Configuration**
   - Site URL: `http://localhost:3000`
   - Redirect URLs: `http://localhost:3000/auth/callback`
3. **Authentication → Providers → Email**
   - Enable Confirm email for verification before first login

Full frontend auth details: [frontend/README.md](frontend/README.md).

## Current APIs

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| `GET` | `/` | No | Service info |
| `GET` | `/api/v1/health` | No | Health check |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Current platform user (JIT) |

See [docs/API.md](docs/API.md) for full details.

Interactive docs while the server is running:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

This project is licensed under the MIT License. See `LICENSE` for details.
