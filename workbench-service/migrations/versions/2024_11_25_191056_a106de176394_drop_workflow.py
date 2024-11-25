"""drop workflow

Revision ID: a106de176394
Revises: 245baf258e11
Create Date: 2024-11-25 19:10:56.835186

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a106de176394"
down_revision: Union[str, None] = "245baf258e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("workflowuserparticipant")
    op.drop_table("workflowrun")
    op.drop_table("workflowdefinition")

    with op.batch_alter_table("assistantparticipant") as batch_op:
        batch_op.add_column(sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False))

    with op.batch_alter_table("userparticipant") as batch_op:
        batch_op.add_column(sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False))


def downgrade() -> None:
    op.drop_column("userparticipant", "metadata")
    op.drop_column("assistantparticipant", "metadata")
    op.create_table(
        "workflowdefinition",
        sa.Column("workflow_definition_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("workflow_definition_id", name="workflowdefinition_pkey"),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "workflowuserparticipant",
        sa.Column("workflow_definition_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("image", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("service_user", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("active_participant", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_definition_id"],
            ["workflowdefinition.workflow_definition_id"],
            name="fk_workflowuserparticipant_workflowdefinition",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("workflow_definition_id", "user_id", name="workflowuserparticipant_pkey"),
    )
    op.create_table(
        "workflowrun",
        sa.Column("workflow_run_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("workflow_definition_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["workflow_definition_id"],
            ["workflowdefinition.workflow_definition_id"],
            name="fk_workflowrun_workflowdefinition",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("workflow_run_id", name="workflowrun_pkey"),
    )
