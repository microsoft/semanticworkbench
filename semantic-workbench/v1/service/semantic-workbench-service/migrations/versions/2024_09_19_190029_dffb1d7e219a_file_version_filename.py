"""upgrades file version storage filename

Revision ID: dffb1d7e219a
Revises: 69dcda481c14
Create Date: 2024-09-19 19:00:29.233114

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from semantic_workbench_service import db
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlmodel import select

# revision identifiers, used by Alembic.
revision: str = "dffb1d7e219a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


async def upgrade_file_versions(conn: AsyncConnection) -> None:
    file_version_details = []
    for row in await conn.execute(
        select(db.File.file_id, db.File.filename, db.FileVersion.version).join(db.FileVersion)
    ):
        file_version_details.append((row[0], row[1], row[2]))

    for file_id, filename, version in file_version_details:
        await conn.execute(
            sa.update(db.FileVersion)
            .where(db.FileVersion.file_id == file_id)
            .where(db.FileVersion.version == version)
            .values(storage_filename=f"{file_id.hex}:{filename}:{str(version).zfill(7)}")
        )


def upgrade() -> None:
    op.add_column("fileversion", sa.Column("storage_filename", sqlmodel.AutoString(), nullable=True))
    op.execute("UPDATE fileversion SET storage_filename = ''")
    op.run_async(upgrade_file_versions)
    with op.batch_alter_table("fileversion") as batch_op:
        batch_op.alter_column("storage_filename", nullable=False)


def downgrade() -> None:
    op.drop_column("fileversion", "storage_filename")
