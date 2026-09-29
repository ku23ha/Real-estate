"""Create persistent Deal and Property tables.

Revision ID: 20260930_0001
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "20260930_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deals",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="draft", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_deals_name_not_blank"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "properties",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("deal_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("asset_type", sa.Text(), nullable=True),
        sa.Column("area_value", sa.Numeric(), nullable=True),
        sa.Column("area_unit", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
        sa.CheckConstraint(
            "(area_value IS NULL AND area_unit IS NULL) OR "
            "(area_value IS NOT NULL AND area_unit IS NOT NULL)",
            name="ck_properties_area_value_unit_pair",
        ),
        sa.CheckConstraint("area_value IS NULL OR area_value > 0", name="ck_properties_area_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deal_id", name="uq_properties_deal_id"),
    )


def downgrade() -> None:
    op.drop_table("properties")
    op.drop_table("deals")
