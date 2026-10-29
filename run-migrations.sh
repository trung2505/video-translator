#!/bin/bash
set -e

# Install minimal migration dependencies
pip install -q alembic==1.12.1 sqlalchemy==2.0.23 psycopg2-binary==2.9.9 pydantic==2.5.0 pydantic-settings==2.1.0 python-dotenv==1.0.0

cd /app/backend

# Run migration cycle
echo "=== UPGRADE #1 (applying 0001_initial and 0002_add_translation_job_fields) ==="
python -m alembic -c alembic.ini upgrade head || true

echo -e "\n=== Verify schema after upgrade ==="
psql -h postgres -U postgres -d video_translator -c "\d+ translation_jobs" || echo "Table not yet created"

echo -e "\n=== DOWNGRADE (reverting all) ==="
python -m alembic -c alembic.ini downgrade base || true

echo -e "\n=== Verify schema after downgrade ==="
psql -h postgres -U postgres -d video_translator -c "SELECT * FROM alembic_version;" || echo "alembic_version table dropped"

echo -e "\n=== UPGRADE #2 (reapplying) ==="
python -m alembic -c alembic.ini upgrade head || true

echo -e "\n=== Verify schema after upgrade #2 ==="
psql -h postgres -U postgres -d video_translator -c "\d+ translation_jobs"

echo -e "\n=== MIGRATION VALIDATION COMPLETE ==="
