"""index message_type

Revision ID: 039bec8edc33
Revises: b29524775484
Create Date: 2024-10-30 23:15:36.240812

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "039bec8edc33"
down_revision: Union[str, None] = "b29524775484"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_conversationmessage_message_type"), "conversationmessage", ["message_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_conversationmessage_message_type"), table_name="conversationmessage")
