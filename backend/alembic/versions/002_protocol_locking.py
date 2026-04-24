"""protocol locking: is_archived for versions, tags for protocols

Revision ID: 002
Revises: 001
Create Date: 2026-04-24
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tags column to protocols (IF NOT EXISTS — safe to re-run)
    op.execute(
        "ALTER TABLE protocols ADD COLUMN IF NOT EXISTS tags JSON NOT NULL DEFAULT '[]'::json"
    )
    # Add is_archived to protocol_versions — marks superseded versions
    op.execute(
        "ALTER TABLE protocol_versions ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE protocol_versions DROP COLUMN IF EXISTS is_archived")
    op.execute("ALTER TABLE protocols DROP COLUMN IF EXISTS tags")
