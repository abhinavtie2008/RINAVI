"""create application cases

Revision ID: a51cf575109b
Revises: 7f9c2b41e8d3
Create Date: 2026-11-13 21:35:47.091427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a51cf575109b'
down_revision: Union[str, Sequence[str], None] = '7f9c2b41e8d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("draft_id", sa.Uuid(), nullable=True),
        sa.Column("service_slug", sa.String(length=80), nullable=False),
        sa.Column("service_name", sa.String(length=200), nullable=False),
        sa.Column("pack_version", sa.String(length=20), nullable=False),
        sa.Column("packet_snapshot", sa.JSON(), nullable=False),
        sa.Column("packet_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reference_number", sa.String(length=120), nullable=True),
        sa.Column("acknowledgement_number", sa.String(length=120), nullable=True),
        sa.Column("deadline_at", sa.Date(), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["draft_id"], ["application_drafts.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("draft_id"),
    )
    op.create_index(
        op.f("ix_application_cases_user_id"),
        "application_cases",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "case_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"], ["application_cases.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_case_events_case_id"), "case_events", ["case_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_case_events_case_id"), table_name="case_events")
    op.drop_table("case_events")
    op.drop_index(
        op.f("ix_application_cases_user_id"), table_name="application_cases"
    )
    op.drop_table("application_cases")
