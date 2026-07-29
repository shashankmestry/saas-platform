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

The API will be available at:

- `http://localhost:8000/`
- `http://localhost:8000/api/v1/health`

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
|   |   |-- lifespan.py
|   |   `-- logging.py
|   `-- shared/
|       `-- responses.py
|-- requirements/
|-- tests/
|-- .env.example
|-- pyproject.toml
`-- README.md
```
