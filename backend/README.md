# Database & Migrations

This document explains how to initialize the database and use Alembic migrations for the backend.

Prerequisites
- PostgreSQL running and accessible via `DATABASE_URL` environment variable.
- `alembic` installed in the backend environment (see `requirements.txt`).

Quick start (local)

1. Copy environment example

```bash
cp .env.example .env
```

2. Run database migrations

```bash
cd backend
m ake upgrade
# or
alembic upgrade head
```

Docker (using docker-compose)

1. Copy `.env.example` to `.env` at repo root.
2. Bring up the stack

```bash
cd infra
docker compose up -d --build
```

The compose setup runs `/app/scripts/init-db.sh` inside the backend container which waits for Postgres and runs `alembic upgrade head`.

Migration workflow

- Create an empty revision:

```bash
cd backend
make revision MESSAGE="add new table"
```

- Apply migrations

```bash
make upgrade
```

Troubleshooting

- If `alembic upgrade head` fails inside the container, exec into backend container and inspect logs and error message:

```bash
docker compose exec backend sh
alembic upgrade head
```

- Common issues:
  - Missing `DATABASE_URL` in environment — ensure `.env` provided to compose.
  - Missing Python dependencies inside container — rebuild image `docker compose build backend`.
