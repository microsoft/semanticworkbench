"""delete context transfer assistants

Revision ID: b2f86e981885
Revises: 3763629295ad
Create Date: 2025-05-19 16:36:13.739217

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2f86e981885"
down_revision: Union[str, None] = "3763629295ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM assistant
        WHERE assistant_service_id = 'project-assistant.made-exploration'
        AND template_id = 'context_transfer'
        """
    )
    op.execute(
        """
        UPDATE assistantparticipant
        SET active_participant = false
        WHERE assistant_id NOT IN (
            SELECT assistant_id
            FROM assistant
        )
        """
    )


def downgrade() -> None:
    pass
