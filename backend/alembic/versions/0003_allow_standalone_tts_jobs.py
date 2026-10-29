"""allow standalone text-to-speech jobs

Revision ID: 0003_allow_standalone_tts_jobs
Revises: 0002_add_translation_job_fields
Create Date: 2026-10-15 00:00:00.000000
"""

from alembic import op


revision = "0003_allow_standalone_tts_jobs"
down_revision = "0002_add_translation_job_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("translation_jobs", "video_id", nullable=True)


def downgrade():
    op.alter_column("translation_jobs", "video_id", nullable=False)