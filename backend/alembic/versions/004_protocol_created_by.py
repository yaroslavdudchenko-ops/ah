"""Add created_by to protocols table

Revision ID: 004
Revises: 003
Create Date: 2026-04-24
"""
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE protocols ADD COLUMN IF NOT EXISTS created_by VARCHAR(100)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE protocols DROP COLUMN IF EXISTS created_by")
