"""remove unique constraint from investment product isin

Revision ID: f01b6cdf4bce
Revises: 21f4ef1272ad
Create Date: 2026-08-09 16:25:37.899113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f01b6cdf4bce'
down_revision: Union[str, Sequence[str], None] = '21f4ef1272ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
