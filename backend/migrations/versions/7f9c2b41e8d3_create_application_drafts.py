"""create application drafts

Revision ID: 7f9c2b41e8d3
Revises: 4b35bc655de5
Create Date: 2026-11-12 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7f9c2b41e8d3"
down_revision: str | Sequence[str] | None = "4b35bc655de5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_drafts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("service_slug", sa.String(length=80), nullable=False),
        sa.Column("service_name", sa.String(length=200), nullable=False),
        sa.Column("pack_version", sa.String(length=20), nullable=False),
        sa.Column("template_snapshot", sa.JSON(), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("document_links", sa.JSON(), nullable=False),
        sa.Column("declaration_confirmed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_drafts_user_id"),
        "application_drafts",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_application_drafts_user_id"), table_name="application_drafts"
    )
    op.drop_table("application_drafts")
