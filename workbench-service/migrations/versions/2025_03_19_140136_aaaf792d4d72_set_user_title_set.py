"""set user_title_set

Revision ID: aaaf792d4d72
Revises: a106de176394
Create Date: 2025-03-19 14:01:36.127350

"""

from typing import Sequence, Union

import sqlmodel as sm
from alembic import op
from semantic_workbench_service import db

# revision identifiers, used by Alembic.
revision: str = "aaaf792d4d72"
down_revision: Union[str, None] = "a106de176394"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Add the __user_title_set key to the meta_data of all conversations to prevent
    # auto-retitling for existing conversations
    for conversation_id, meta_data in bind.execute(
        sm.select(db.Conversation.conversation_id, db.Conversation.meta_data)
    ).yield_per(1):
        meta_data = meta_data or {}
        meta_data["__user_title_set"] = True

        bind.execute(
            sm.update(db.Conversation)
            .where(sm.col(db.Conversation.conversation_id) == conversation_id)
            .values(meta_data=meta_data)
        )


def downgrade() -> None:
    bind = op.get_bind()

    # Drop the __user_title_set key
    for conversation_id, meta_data in bind.execute(
        sm.select(db.Conversation.conversation_id, db.Conversation.meta_data)
    ).yield_per(1):
        meta_data = meta_data or {}
        if not meta_data.pop("__user_title_set", None):
            continue

        bind.execute(
            sm.update(db.Conversation)
            .where(sm.col(db.Conversation.conversation_id) == conversation_id)
            .values(meta_data=meta_data)
        )
