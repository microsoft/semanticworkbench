import pytest
import semantic_workbench_service
from alembic import command
from alembic.config import Config
from semantic_workbench_service import db
from semantic_workbench_service.config import DBSettings


@pytest.fixture
async def bootstrapped_db_settings(db_settings: DBSettings) -> DBSettings:
    async with db.create_engine(db_settings) as engine:
        await db.bootstrap_db(engine, settings=db_settings)

    return db_settings


@pytest.fixture
def alembic_config(bootstrapped_db_settings: DBSettings, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setattr(semantic_workbench_service.settings, "db", bootstrapped_db_settings)
    return Config(bootstrapped_db_settings.alembic_config_path)


def test_migration_cycle(alembic_config: Config) -> None:
    """Test that all migrations can downgrade and upgrade without error."""

    # check that there are no schema differences from head
    command.check(alembic_config)

    # downgrade to base
    command.downgrade(alembic_config, "base")

    # and upgrade back to head
    command.upgrade(alembic_config, "head")

    # check that the current revision is head
    command.check(
        alembic_config,
    )
