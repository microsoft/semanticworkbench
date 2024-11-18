"""double-check debugs

Revision ID: 245baf258e11
Revises: 5149c7fb5a32
Create Date: 2024-11-05 01:51:24.835708

"""

from typing import Sequence, Union

import sqlmodel as sm
from alembic import op
from semantic_workbench_service import db

# revision identifiers, used by Alembic.
revision: str = "245baf258e11"
down_revision: Union[str, None] = "5149c7fb5a32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    pass
