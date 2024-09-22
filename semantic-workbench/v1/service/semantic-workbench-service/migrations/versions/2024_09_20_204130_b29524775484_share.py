"""share

Revision ID: b29524775484
Revises: 69dcda481c14
Create Date: 2024-09-17 20:41:30.747858

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "b29524775484"
down_revision: Union[str, None] = "dffb1d7e219a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversationshare",
        sa.Column("conversation_share_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("created_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("conversation_permission", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_redeemable", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.conversation_id"],
            name="fk_file_conversation_id_conversation",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.user_id"],
        ),
        sa.PrimaryKeyConstraint("conversation_share_id"),
    )
    op.create_table(
        "conversationshareredemption",
        sa.Column("conversation_share_redemption_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_share_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_permission", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("new_participant", sa.Boolean(), nullable=False),
        sa.Column("redeemed_by_user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_share_id"],
            ["conversationshare.conversation_share_id"],
            name="fk_conversationshareredemption_conversation_share_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["redeemed_by_user_id"],
            ["user.user_id"],
            name="fk_conversationshareredemption_user_id_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("conversation_share_redemption_id"),
    )
    op.add_column("assistant", sa.Column("imported_from_assistant_id", sa.Uuid(), nullable=True))
    op.add_column("conversation", sa.Column("imported_from_conversation_id", sa.Uuid(), nullable=True))
    op.add_column(
        "userparticipant", sa.Column("conversation_permission", sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )
    op.execute("UPDATE userparticipant SET conversation_permission = 'read_write'")
    with op.batch_alter_table("userparticipant") as batch_op:
        batch_op.alter_column("conversation_permission", nullable=False)

    inspector = inspect(op.get_bind())
    uq_constraints = inspector.get_unique_constraints("fileversion")
    if any("uq_fileversion_file_id_version" == uq_constraint["name"] for uq_constraint in uq_constraints):
        with op.batch_alter_table("fileversion") as batch_op:
            batch_op.drop_constraint("uq_fileversion_file_id_version", type_="unique")


def downgrade() -> None:
    op.drop_column("userparticipant", "conversation_permission")
    op.drop_column("conversation", "imported_from_conversation_id")
    op.drop_column("assistant", "imported_from_assistant_id")
    op.drop_table("conversationshareredemption")
    op.drop_table("conversationshare")
