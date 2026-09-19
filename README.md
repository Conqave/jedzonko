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

## Household deletion and purge

Deleting a household is recoverable for 7 days
(`households/domain/retention.py: HOUSEHOLD_RETENTION_PERIOD`). Members see
their deleted households at `GET /api/households/deleted/` and restore one with
`POST /api/households/{id}/restore/` while the window lasts. Afterwards the
household and all its data are purged permanently.

The purge runs as a daily host cron job, because the existing Compose stack has
no scheduler and a one-line crontab entry is cheaper than adding one:

```bash
sudo install -m 0644 infra/cron/jedzonko-purge /etc/cron.d/jedzonko-purge
```

It runs at 03:15 every day and cron mails the command output (how many
households were purged, and which). Run it manually with:

```bash
cd infra
docker compose exec -T backend python manage.py purge_deleted_households --dry-run
docker compose exec -T backend python manage.py purge_deleted_households
```

`--dry-run` reports what would be purged and changes nothing.

## Backend layering

Each feature owns `domain/`, `application/`, `infrastructure/` and
`presentation/`, with dependencies pointing inwards. `<feature>/composition.py`
is the feature's composition root: it is the only place that wires
infrastructure adapters into application use cases, and it is the only module
another feature may import to reuse that feature's behaviour.

`backend/shared/` is a plain Python package, not a Django app and not a staging
area. Code belongs there only when at least two independent features need the
same responsibility and none of them is its natural owner. It currently holds
measurement units and quantity conversion (`shared/measurement.py`,
`shared/measurement_units.py`), needed by `households`, `inventory`, `recipes`
and `shopping`, and product/offer name normalization (`shared/text.py`), needed
by `recipes`, `households` and `promotions`. `shared` may not import any
feature.
