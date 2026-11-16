"""remove legacy aadhaar profile values

Revision ID: b7e4f1a2c9d3
Revises: a51cf575109b
Create Date: 2026-11-16 11:00:00.000000

Aadhaar numbers are collected only by the official portal. Rows written
before A1 are deleted rather than retained under a read filter. The deletion
is irreversible; a downgrade does not restore the values.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7e4f1a2c9d3'
down_revision: Union[str, Sequence[str], None] = 'a51cf575109b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM profile_values WHERE field_key = 'aadhaar_number'")


def downgrade() -> None:
    # Data deleted by this migration cannot be reconstructed.
    pass
