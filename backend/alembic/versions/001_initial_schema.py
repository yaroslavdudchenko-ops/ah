"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phase", sa.String(10), nullable=False),
        sa.Column("design_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("section_prompts", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "protocols",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("drug_name", sa.String(200), nullable=False),
        sa.Column("inn", sa.String(200), nullable=False),
        sa.Column("phase", sa.String(10), nullable=False),
        sa.Column("therapeutic_area", sa.String(200), nullable=False),
        sa.Column("indication", sa.Text, nullable=False),
        sa.Column("population", sa.Text, nullable=False),
        sa.Column("primary_endpoint", sa.Text, nullable=False),
        sa.Column("secondary_endpoints", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("duration_weeks", sa.Integer, nullable=False),
        sa.Column("dosing", sa.Text, nullable=False),
        sa.Column("inclusion_criteria", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("exclusion_criteria", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_protocols_phase", "protocols", ["phase"])
    op.create_index("ix_protocols_status", "protocols", ["status"])

    op.create_table(
        "protocol_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("protocol_id", sa.String(36), sa.ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("content", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("compliance_score", sa.Integer, nullable=True),
        sa.Column("generated_by", sa.String(100), nullable=False, server_default="InHouse/Qwen3.5-122B"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_protocol_versions_protocol_id", "protocol_versions", ["protocol_id"])

    op.create_table(
        "open_issues",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("protocol_id", sa.String(36), sa.ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section", sa.String(100), nullable=False),
        sa.Column("issue_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("suggestion", sa.Text, nullable=True),
        sa.Column("resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_open_issues_protocol_id", "open_issues", ["protocol_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("performed_by", sa.String(100), nullable=False, server_default="system"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"])

    # Seed default templates
    op.execute("""
        INSERT INTO templates (id, name, phase, design_type, description, section_prompts) VALUES
        ('tpl-phase-i-001', 'Phase I — Open-Label FIH', 'I', 'open-label',
         'Первое исследование на человеке (FIH), открытое, эскалация дозы', '{}'),
        ('tpl-phase-ii-001', 'Phase II — Single-Arm', 'II', 'open-label',
         'Однорукавное исследование эффективности Phase II', '{}'),
        ('tpl-phase-iii-001', 'Phase III — RCT Placebo-Controlled', 'III', 'randomized',
         'Рандомизированное двойное слепое плацебо-контролируемое исследование Phase III', '{}')
    """)


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("open_issues")
    op.drop_table("protocol_versions")
    op.drop_table("protocols")
    op.drop_table("templates")
