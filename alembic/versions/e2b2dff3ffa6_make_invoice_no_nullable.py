"""make invoice_no nullable

Revision ID: e2b2dff3ffa6
Revises: fc8acee66e49
Create Date: 2025-12-06 11:06:07.579660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2b2dff3ffa6'
down_revision: Union[str, Sequence[str], None] = 'fc8acee66e49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column('invoice', 'invoice_no',
                    existing_type=sa.String(length=30),
                    nullable=True)


def downgrade():
    op.alter_column('invoice', 'invoice_no',
                    existing_type=sa.String(length=30),
                    nullable=False)
