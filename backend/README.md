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
- `http://localhost:8000/api/v1/auth/me` — returns JWT identity (`id`, `email`, `role`)

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
|   |   `-- users/
|   |       |-- dependencies.py
|   |       |-- exceptions.py
|   |       |-- models.py
|   |       |-- repository.py
|   |       |-- router.py
|   |       |-- schemas.py
|   |       `-- service.py
|   `-- shared/
|       `-- responses.py
|-- alembic/
|   |-- env.py
|   `-- versions/
|-- alembic.ini
|-- requirements/
|-- tests/
|-- .env.example
|-- pyproject.toml
`-- README.md
```
