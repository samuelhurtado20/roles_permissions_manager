"""Semantic cache chat schema: create chat_records table with pgvector support

Revision ID: 0002_semantic_cache_chat_schema
Revises: 0001_initial_schema
Create Date: 2026-10-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = '0002_semantic_cache_chat_schema'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Create chat_records table with pgvector extension
    op.create_table(
        'chat_records',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('embedding', pg.VECTOR(dim=1536), nullable=False),  # pgvector extension column
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),  # Nullable, populated on cache hits
        sa.Column('source_type', sa.Enum('CACHE', 'OPENAI_API', name='chat_record_source_type'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create index for per-user similarity search on (user_id, embedding)
    op.execute("CREATE INDEX idx_chat_records_user_embedding ON chat_records USING ivfflat (embedding vector_l2_ops) WITH (lists = 100)")

    # Create composite index for frequently queried user history
    op.create_index('idx_chat_records_user_created', 'chat_records', ['user_id', sa.text('created_at DESC')])

    # Add pgvector extension if not already present
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade():
    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")

    # Drop indices
    op.drop_index('idx_chat_records_user_embedding', table_name='chat_records')
    op.drop_index('idx_chat_records_user_created', table_name='chat_records')

    # Drop chat_records table
    op.drop_table('chat_records')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS chat_record_source_type")