#!/usr/bin/env sh
set -e

echo "Waiting for Postgres..."
until pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres}; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Running alembic upgrade head"
cd /app
if [ -f alembic.ini ]; then
  alembic upgrade head
  exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo "Alembic upgrade failed with exit code $exit_code"
    exit $exit_code
  fi
else
  echo "alembic.ini not found in /app"
  exit 1
fi

echo "DB migration finished"
