"""Add RET-010 reference domain entities.

Revision ID: 20260930_0002
Revises: 20260930_0001
"""

from alembic import op
import sqlalchemy as sa


revision = "20260930_0002"
down_revision = "20260930_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_table(
        "developers",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_table(
        "locations",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("parent_location_id", sa.Uuid(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_locations_parent_location_id", "locations", ["parent_location_id"])
    op.create_table(
        "micro_markets",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("location_id", sa.Uuid(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_micro_markets_location_id", "micro_markets", ["location_id"])
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("developer_id", sa.Uuid(), sa.ForeignKey("developers.id"), nullable=True),
        sa.Column("location_id", sa.Uuid(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_projects_developer_id", "projects", ["developer_id"])
    op.create_index("ix_projects_location_id", "projects", ["location_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_location_id", table_name="projects")
    op.drop_index("ix_projects_developer_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_micro_markets_location_id", table_name="micro_markets")
    op.drop_table("micro_markets")
    op.drop_index("ix_locations_parent_location_id", table_name="locations")
    op.drop_table("locations")
    op.drop_table("developers")
    op.drop_table("users")
    op.drop_table("organizations")
