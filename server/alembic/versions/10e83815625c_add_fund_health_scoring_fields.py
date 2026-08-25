"""add fund health scoring fields

Revision ID: 10e83815625c
Revises: 841862208668
Create Date: 2026-08-10 17:53:13.094634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10e83815625c'
down_revision: Union[str, Sequence[str], None] = '841862208668'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
