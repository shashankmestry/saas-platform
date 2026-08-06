# Backend

Minimal, production-ready FastAPI foundation for the SaaS platform.

## Run API

From the `backend/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Environment configuration:

- `DATABASE_URL` — Supabase PostgreSQL connection string for SQLAlchemy
- `SUPABASE_URL` / `SUPABASE_PUBLISHABLE_KEY` — JWT verification via cached JWKS
  (tokens are validated locally; Supabase Auth is not called on every request)

The API will be available at:

- `http://localhost:8000/`
- `http://localhost:8000/api/v1/health`
- `http://localhost:8000/api/v1/auth/me` — returns the platform user (JIT on first login)
- `http://localhost:8000/api/v1/organizations` — list/create organizations
- `http://localhost:8000/docs` — Swagger UI

## API

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| `GET` | `/` | No | Service info (`name`, `version`, `status`) |
| `GET` | `/api/v1/health` | No | Health check (`{"status":"healthy"}`) |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Current platform user (JIT provisioning) |
| `GET` | `/api/v1/organizations` | Bearer JWT | Organizations for the current user |
| `POST` | `/api/v1/organizations` | Bearer JWT | Create organization + owner membership |
| `GET` | `/api/v1/organizations/{id}/profile` | Bearer JWT | Organization profile (`organization.view`) |
| `PATCH` | `/api/v1/organizations/{id}/profile` | Bearer JWT | Update organization profile (`organization.manage`) |
| `GET` | `/api/v1/organizations/{id}/plan` | Bearer JWT | Organization plan & entitlements (`organization.view`) |
| `POST` | `/api/v1/organizations/{id}/logo/upload` | Bearer JWT | Request logo upload authorization (`organization.manage`) |
| `POST` | `/api/v1/organizations/{id}/logo/confirm` | Bearer JWT | Confirm logo upload (`organization.manage`) |
| `DELETE` | `/api/v1/organizations/{id}/logo` | Bearer JWT | Remove organization logo (`organization.manage`) |
| `GET` | `/api/v1/organizations/{id}/members` | Bearer JWT | List members (`member.view`) |
| `GET` | `/api/v1/organizations/{id}/invitations` | Bearer JWT | List pending invitations (`invitation.view`) |
| `POST` | `/api/v1/organizations/{id}/invitations` | Bearer JWT | Invite member (`member.invite`) |
| `DELETE` | `/api/v1/organizations/{id}/invitations/{id}` | Bearer JWT | Revoke invitation (`invitation.revoke`) |
| `POST` | `/api/v1/invitations/accept` | Bearer JWT | Accept invitation |

Full request/response details: [docs/API.md](../docs/API.md)

### Database migrations

```bash
alembic upgrade head
```

## Structure

```text
backend/
|-- app/
|   |-- api/
|   |   `-- v1/
|   |       |-- api.py
|   |       `-- endpoints/
|   |           |-- health.py
|   |           `-- root.py
|   |-- core/
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- lifespan.py
|   |   |-- logging.py
|   |   `-- security.py
|   |-- db/
|   |   `-- base.py
|   |-- modules/
|   |   |-- auth/
|   |   |   |-- dependencies.py
|   |   |   |-- exceptions.py
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   `-- service.py
|   |   |-- memberships/
|   |   |   |-- dependencies.py
|   |   |   |-- exceptions.py
|   |   |   |-- models.py
|   |   |   |-- repository.py
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   |-- service.py
|   |   |   `-- tokens.py
|   |   |-- organizations/
|   |   |   |-- dependencies.py
|   |   |   |-- exceptions.py
|   |   |   |-- models.py
|   |   |   |-- repository.py
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   `-- service.py
|   |   `-- users/
|   |       |-- dependencies.py
|   |       |-- exceptions.py
|   |       |-- models.py
|   |       |-- repository.py
|   |       |-- schemas.py
|   |       `-- service.py
|   `-- shared/
|       |-- email.py
|       `-- responses.py
|-- alembic/
|   |-- env.py
|   `-- versions/
|       |-- 0001_create_users.py
|       |-- 0002_create_organizations.py
|       `-- 0003_create_organization_invitations.py
|-- alembic.ini
|-- requirements/
|-- tests/
|-- .env.example
|-- pyproject.toml
`-- README.md
```
