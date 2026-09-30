"""Add RET-020 evidence and provenance records.

Revision ID: 20260930_0003
Revises: 20260930_0002
"""

from alembic import op
import sqlalchemy as sa


revision = "20260930_0003"
down_revision = "20260930_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("rights_status", sa.Text(), nullable=False),
        sa.Column("rights_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_evidence_sources_name_not_blank"),
        sa.CheckConstraint("length(trim(source_type)) > 0", name="ck_evidence_sources_type_not_blank"),
        sa.CheckConstraint("length(trim(rights_status)) > 0", name="ck_evidence_sources_rights_not_blank"),
    )
    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("deal_id", sa.Uuid(), sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("evidence_sources.id"), nullable=False),
        sa.Column("evidence_type", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_content", sa.JSON(), nullable=False),
        sa.Column("normalized_content", sa.JSON(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("length(trim(evidence_type)) > 0", name="ck_evidence_type_not_blank"),
    )
    op.create_index("ix_evidence_deal_created", "evidence", ["deal_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_evidence_deal_created", table_name="evidence")
    op.drop_table("evidence")
    op.drop_table("evidence_sources")
