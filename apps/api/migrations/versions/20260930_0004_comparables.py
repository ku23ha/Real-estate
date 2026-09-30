"""Add RET-030 comparable source facts linked to evidence.

Revision ID: 20260930_0004
Revises: 20260930_0003
"""

from alembic import op
import sqlalchemy as sa


revision = "20260930_0004"
down_revision = "20260930_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comparables",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("deal_id", sa.Uuid(), sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), sa.ForeignKey("evidence.id"), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("reported_price", sa.Numeric(), nullable=False),
        sa.Column("currency_code", sa.Text(), nullable=False),
        sa.Column("property_type", sa.Text(), nullable=False),
        sa.Column("area_value", sa.Numeric(), nullable=False),
        sa.Column("area_unit", sa.Text(), nullable=False),
        sa.Column("location_label", sa.Text(), nullable=False),
        sa.Column("project_name", sa.Text(), nullable=True),
        sa.Column("developer_name", sa.Text(), nullable=True),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("reported_price > 0", name="ck_comparables_price_positive"),
        sa.CheckConstraint("area_value > 0", name="ck_comparables_area_positive"),
        sa.CheckConstraint("length(trim(currency_code)) = 3", name="ck_comparables_currency_code_length"),
        sa.UniqueConstraint("deal_id", "fingerprint", name="uq_comparables_deal_fingerprint"),
        sa.UniqueConstraint("evidence_id", name="uq_comparables_evidence_id"),
    )
    op.create_index(
        "ix_comparables_deal_transaction_date",
        "comparables",
        ["deal_id", "transaction_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_comparables_deal_transaction_date", table_name="comparables")
    op.drop_table("comparables")
