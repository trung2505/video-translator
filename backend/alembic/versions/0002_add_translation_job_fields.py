"""add translation job fields

Revision ID: 0002_add_translation_job_fields
Revises: 0001_initial
Create Date: 2026-09-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_add_translation_job_fields'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Add job_type with default 'video' for existing rows
    op.add_column('translation_jobs', sa.Column('job_type', sa.String(length=50), nullable=False, server_default='video'))
    # Add input/output file references (nullable)
    op.add_column('translation_jobs', sa.Column('input_file_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('translation_jobs', sa.Column('output_file_id', postgresql.UUID(as_uuid=True), nullable=True))
    # Add parameters column as Text (JSON candidate)
    op.add_column('translation_jobs', sa.Column('parameters', sa.Text(), nullable=True))

    # Create indexes for lookup
    op.create_index('ix_translation_jobs_job_type', 'translation_jobs', ['job_type'])
    op.create_index('ix_translation_jobs_input_file_id', 'translation_jobs', ['input_file_id'])

    # Add foreign key constraints if files table exists
    with op.get_context().autocommit_block():
        op.create_foreign_key('fk_translation_jobs_input_file_id_files', 'translation_jobs', 'files', ['input_file_id'], ['id'])
        op.create_foreign_key('fk_translation_jobs_output_file_id_files', 'translation_jobs', 'files', ['output_file_id'], ['id'])


def downgrade():
    # Drop FKs
    op.drop_constraint('fk_translation_jobs_input_file_id_files', 'translation_jobs', type_='foreignkey')
    op.drop_constraint('fk_translation_jobs_output_file_id_files', 'translation_jobs', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_translation_jobs_input_file_id', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_job_type', table_name='translation_jobs')

    # Drop columns
    op.drop_column('translation_jobs', 'parameters')
    op.drop_column('translation_jobs', 'output_file_id')
    op.drop_column('translation_jobs', 'input_file_id')
    op.drop_column('translation_jobs', 'job_type')
