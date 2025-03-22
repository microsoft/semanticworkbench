"""add template_id

Revision ID: 3763629295ad
Revises: aaaf792d4d72
Create Date: 2025-03-21 15:32:50.919136

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3763629295ad"
down_revision: Union[str, None] = "aaaf792d4d72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("assistant") as batch_op:
        batch_op.add_column(sa.Column("template_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.execute("update assistant set template_id = ' default' where template_id is null")
    with op.batch_alter_table("assistant") as batch_op:
        batch_op.alter_column("template_id", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("assistant") as batch_op:
        batch_op.drop_column("template_id")
