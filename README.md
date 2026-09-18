# jedzonko

Monorepo: Quasar frontend, Django backend, MariaDB database.

- `backend/` — Django 5.2 / Python 3.14 / Django REST Framework
- `frontend/` — Quasar 2 (Vite, TypeScript, Pinia)
- `infra/` — Docker Compose configuration for MariaDB and the application services

## Configuration

Copy `.env.example` to `.env` and fill in the values. `.env` is never committed.

## Local development (WSL2 Ubuntu)

```bash
# database
docker compose --env-file ../.env -f infra/docker-compose.yml up -d database

# backend
cd backend
python3.14 -m venv .venv && .venv/bin/pip install ".[dev]"
set -a && . ../.env && set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 0.0.0.0:8000

# frontend (proxies /api and /media to the backend)
cd frontend
npm install
npm run dev
```

## Verification

```bash
# backend
cd backend
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/isort . && .venv/bin/black --check . && .venv/bin/mypy .
.venv/bin/pytest

# frontend
cd frontend
npm run lint:check && npm run typecheck && npm run build
```

## Accounts and permissions

There is no public registration. An administrator creates users in Django admin
(`/admin/`) and grants promotion access with the `promotions.view_promotions`
permission. New users have no promotion access. The backend permission is the
single source of truth; the Quasar UI only hides navigation.

## Backend layering

Each feature owns `domain/`, `application/`, `infrastructure/` and
`presentation/`, with dependencies pointing inwards. `<feature>/composition.py`
is the feature's composition root: it is the only place that wires
infrastructure adapters into application use cases, and it is the only module
another feature may import to reuse that feature's behaviour.
