"""Add RAG: protocol_embeddings table (JSONB vectors, numpy cosine similarity)

Revision ID: 005
Revises: 004
Create Date: 2026-04-24

Phase 1 (current): embeddings stored as JSONB, similarity via numpy in Python.
Phase 2 (future, >5000 protocols): migrate to pgvector/pgvector:pg16 + vector(1536).
"""
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS protocol_embeddings (
            id VARCHAR(36) PRIMARY KEY,
            version_id VARCHAR(36) NOT NULL REFERENCES protocol_versions(id) ON DELETE CASCADE,
            section_key VARCHAR(50) NOT NULL,
            embedding JSONB,
            model VARCHAR(100) NOT NULL DEFAULT 'InHouse/embeddings-model-1',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_embedding_version_section UNIQUE (version_id, section_key)
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_embeddings_version_id
        ON protocol_embeddings(version_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS protocol_embeddings CASCADE")
