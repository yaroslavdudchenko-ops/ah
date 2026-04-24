"""protocol locking: is_archived for protocol_versions

Revision ID: 003
Revises: 002
Create Date: 2026-04-24
"""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Mark superseded versions when a new full generation is created
    op.execute(
        "ALTER TABLE protocol_versions ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE protocol_versions DROP COLUMN IF EXISTS is_archived")
