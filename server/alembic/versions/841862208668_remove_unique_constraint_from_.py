"""remove unique constraint from investment product isin

Revision ID: 841862208668
Revises: f01b6cdf4bce
Create Date: 2026-08-09 16:26:32.306620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '841862208668'
down_revision: Union[str, Sequence[str], None] = 'f01b6cdf4bce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
