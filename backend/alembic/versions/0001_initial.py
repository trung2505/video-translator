"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-06-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # files
    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # videos
    op.create_table(
        'videos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('original_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('processed_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subtitle_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_videos_user_id', 'videos', ['user_id'])
    op.create_index('ix_videos_status', 'videos', ['status'])
    op.create_index('ix_videos_created_at', 'videos', ['created_at'])

    # translation_jobs
    op.create_table(
        'translation_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_translation_jobs_video_id', 'translation_jobs', ['video_id'])
    op.create_index('ix_translation_jobs_task_id', 'translation_jobs', ['task_id'])

    # segments
    op.create_table(
        'segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start', sa.Float(), nullable=False),
        sa.Column('end', sa.Float(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
    )

    # subtitles
    op.create_table(
        'subtitles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('srt_path', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('subtitles')
    op.drop_table('segments')
    op.drop_index('ix_translation_jobs_task_id', table_name='translation_jobs')
    op.drop_index('ix_translation_jobs_video_id', table_name='translation_jobs')
    op.drop_table('translation_jobs')
    op.drop_index('ix_videos_created_at', table_name='videos')
    op.drop_index('ix_videos_status', table_name='videos')
    op.drop_index('ix_videos_user_id', table_name='videos')
    op.drop_table('videos')
    op.drop_table('files')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
