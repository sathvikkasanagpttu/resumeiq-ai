"""pgvector and embedding index upgrade

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-10-07 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Enable pgvector extension in PostgreSQL
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Alter embedding column type to vector(768) if needed and create cosine HNSW index
        op.execute("ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(768) USING embedding::text::vector(768)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_hnsw ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)")

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_knowledge_chunks_embedding_hnsw")
        op.execute("ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE json USING embedding::text::json")
