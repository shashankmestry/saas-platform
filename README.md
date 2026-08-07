# Open Source SaaS Platform

## Overview

Production-ready open-source SaaS platform foundation. The backend currently
provides FastAPI bootstrapping, Supabase PostgreSQL, JWT authentication,
Just-In-Time platform user provisioning, and organization foundation
(create/list with owner membership).

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
# fill DATABASE_URL, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SECRET_KEY
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

1. **Project Settings → API Keys**
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL` / `SUPABASE_URL`
   - Publishable key → `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_PUBLISHABLE_KEY`
   - Secret key (server-only) → `SUPABASE_SECRET_KEY` in `backend/.env`
     (never use `NEXT_PUBLIC_*` for the secret)
2. **Authentication → URL Configuration**
   - Site URL: `http://localhost:3000`
   - Redirect URLs: `http://localhost:3000/auth/callback`
3. **Authentication → Providers → Email**
   - Enable Confirm email for verification before first login
4. **Storage**
   - Create a **private** bucket named `organization-assets`
   - Optional: set a 2 MB file size limit and restrict MIME types to
     `image/jpeg`, `image/png`, `image/webp`
   - Do not make the bucket public; logos are served via short-lived signed URLs

Full frontend auth details: [frontend/README.md](frontend/README.md).

## Current APIs

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| `GET` | `/` | No | Service info |
| `GET` | `/api/v1/health` | No | Health check |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Current platform user (JIT) |
| `GET` | `/api/v1/organizations` | Bearer JWT | Organizations for the current user |
| `POST` | `/api/v1/organizations` | Bearer JWT | Create organization + owner membership |
| `GET` | `/api/v1/organizations/{id}/profile` | Bearer JWT | Organization profile (`organization.view`) |
| `PATCH` | `/api/v1/organizations/{id}/profile` | Bearer JWT | Update organization profile (`organization.manage`) |
| `GET` | `/api/v1/organizations/{id}/plan` | Bearer JWT | Organization plan & entitlements (`organization.view`) |
| `GET` | `/api/v1/organizations/{id}/subscription` | Bearer JWT | Organization subscription (`organization.view`) |
| `POST` | `/api/v1/organizations/{id}/logo/upload` | Bearer JWT | Request logo upload authorization (`organization.manage`) |
| `POST` | `/api/v1/organizations/{id}/logo/confirm` | Bearer JWT | Confirm logo upload (`organization.manage`) |
| `DELETE` | `/api/v1/organizations/{id}/logo` | Bearer JWT | Remove organization logo (`organization.manage`) |
| `GET` | `/api/v1/organizations/{id}/members` | Bearer JWT | List members (`member.view`) |
| `PATCH` | `/api/v1/organizations/{id}/members/{membership_id}` | Bearer JWT | Update member role (`member.role.update`) |
| `DELETE` | `/api/v1/organizations/{id}/members/{membership_id}` | Bearer JWT | Remove member (`member.remove`) |
| `POST` | `/api/v1/organizations/{id}/leave` | Bearer JWT | Leave organization |
| `POST` | `/api/v1/organizations/{id}/ownership/transfer` | Bearer JWT | Transfer ownership |
| `GET` | `/api/v1/organizations/{id}/invitations` | Bearer JWT | List pending invitations (`invitation.view`) |
| `POST` | `/api/v1/organizations/{id}/invitations` | Bearer JWT | Invite member (`member.invite`) |
| `DELETE` | `/api/v1/organizations/{id}/invitations/{id}` | Bearer JWT | Revoke invitation (`invitation.revoke`) |
| `POST` | `/api/v1/invitations/accept` | Bearer JWT | Accept invitation |

See [docs/API.md](docs/API.md) for full details.

Interactive docs while the server is running:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

This project is licensed under the MIT License. See `LICENSE` for details.
