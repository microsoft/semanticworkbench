"""conversationmessagedebug

Revision ID: 5149c7fb5a32
Revises: 039bec8edc33
Create Date: 2024-11-04 20:40:29.252951

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel as sm
from alembic import op
from semantic_workbench_service import db

# revision identifiers, used by Alembic.
revision: str = "5149c7fb5a32"
down_revision: Union[str, None] = "039bec8edc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversationmessagedebug",
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["conversationmessage.message_id"],
            name="fk_conversationmessagedebug_message_id_conversationmessage",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("message_id"),
    )

    bind = op.get_bind()
    max_sequence = bind.execute(sm.select(sm.func.max(db.ConversationMessage.sequence))).scalar()
    if max_sequence is not None:
        step = 100
        for sequence_start in range(1, max_sequence + 1, step):
            sequence_end_exclusive = sequence_start + step

            results = bind.execute(
                sm.select(db.ConversationMessage.message_id, db.ConversationMessage.meta_data).where(
                    db.ConversationMessage.sequence >= sequence_start,
                    db.ConversationMessage.sequence < sequence_end_exclusive,
                )
            ).fetchall()

            for message_id, meta_data in results:
                debug = meta_data.pop("debug", None)
                if not debug:
                    continue

                bind.execute(
                    sm.insert(db.ConversationMessageDebug).values(
                        message_id=message_id,
                        data=debug,
                    )
                )

                bind.execute(
                    sm.update(db.ConversationMessage)
                    .where(db.ConversationMessage.message_id == message_id)
                    .values(meta_data=meta_data)
                )


def downgrade() -> None:
    bind = op.get_bind()

    max_sequence = bind.execute(sm.select(sm.func.max(db.ConversationMessage.sequence))).scalar()
    if max_sequence is not None:
        step = 100
        for sequence_start in range(1, max_sequence + 1, step):
            sequence_end_exclusive = sequence_start + step
            results = bind.execute(
                sm.select(
                    db.ConversationMessageDebug.message_id,
                    db.ConversationMessageDebug.data,
                    db.ConversationMessage.meta_data,
                )
                .join(db.ConversationMessage)
                .where(
                    db.ConversationMessage.sequence >= sequence_start,
                    db.ConversationMessage.sequence < sequence_end_exclusive,
                )
            ).fetchall()

            for message_id, debug_data, meta_data in results:
                meta_data["debug"] = debug_data
                bind.execute(
                    sm.update(db.ConversationMessage)
                    .where(db.ConversationMessage.message_id == message_id)
                    .values(meta_data=meta_data)
                )

    op.drop_table("conversationmessagedebug")
