"""delete knowlege-transfer-assistants

Revision ID: 503c739152f3
Revises: b2f86e981885
Create Date: 2025-06-18 17:43:28.113154

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "503c739152f3"
down_revision: Union[str, None] = "b2f86e981885"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM assistant
        WHERE assistant_service_id = 'project-assistant.made-exploration'
        AND template_id = 'knowledge_transfer'
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
